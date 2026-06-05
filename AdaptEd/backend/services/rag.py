"""
RAG-сервис: семантическое сопоставление текста задачи с темами/учебником.

Идея:
1) Эталоны (темы или куски учебника) превращаем в векторы-эмбеддинги и храним в БД.
2) Для нового вопроса считаем его вектор и ищем ближайший эталон по косинусной близости.
3) Возвращаем тему ближайшего эталона как ярлык + оценку близости.

Эмбеддинги берём через OpenAI-совместимый эндпоинт NeuroAPI/ProxyAPI
(тем же ключом, что и чат). Векторное хранилище — обычная таблица в PostgreSQL,
сравнение делаем на numpy (для прототипа этого достаточно, pgvector не нужен).
"""
from typing import Any, Dict, List, Optional, Tuple
import os
import re
import requests
import numpy as np

from utils.db import has_db, get_db

# Сколько фрагментов отправлять в /embeddings за один запрос (целый учебник — сотни кусков).
EMBED_BATCH_SIZE = 32

# Начала строк-задач (не заголовки параграфов).
_TASK_LINE_PREFIXES = (
    "решите",
    "найдите",
    "докажите",
    "вычислите",
    "постройте",
    "укажите",
    "сколько",
    "какова",
    "какой",
    "какие",
    "какую",
    "какое",
    "каким",
    "при каких",
    "известно",
    "даны",
    "дано",
    "бросают",
    "монету",
    "игральный",
    "стрелок",
    "рабочий",
    "турист",
    "велосипедист",
    "подбрасывая",
    "наугад",
    "вероятность",
    "катер",
    "лодка",
    "теплоход",
    "дмитрий",
    "глеб",
    "французский",
    "м.",
    "мцнмо",
)


# Тема по умолчанию, если ничего не нашли.
DEFAULT_TOPIC = "Общая математика"

# Базовая школьная таксономия тем для математики 9 класса.
# Текст справа помогает эмбеддингу "понять" тему (ключевые формулировки).
DEFAULT_MATH_TAXONOMY: List[Dict[str, str]] = [
    {"topic": "Линейные уравнения", "text": "Линейное уравнение первой степени вида ax+b=0, где x в первой степени без квадрата. Примеры: 2x+3=7; 5x-4=11; 3(x-2)=9. Перенос слагаемых, один корень."},
    {"topic": "Квадратные уравнения", "text": "Квадратное уравнение второй степени вида ax^2+bx+c=0, x в квадрате (x^2, x²). Примеры: x^2-5x+6=0; 2x^2+3x-2=0; x^2-9=0. Дискриминант D=b^2-4ac, теорема Виета, два корня."},
    {"topic": "Дробно-рациональные уравнения", "text": "Уравнение с переменной в знаменателе дроби, например (x+1)/(x-2)=3 или 1/x + 1/(x-1)=2. Область допустимых значений, общий знаменатель."},
    {"topic": "Уравнения с модулем", "text": "Уравнение с модулем (абсолютной величиной): |x-3|=5, |2x+1|=7. Раскрытие модуля по двум случаям, часто два корня."},
    {"topic": "Уравнения с корнем", "text": "Иррациональное уравнение с квадратным корнем: √(x+1)=3, sqrt(2x-1)=5. Возведение обеих частей в квадрат, проверка посторонних корней."},
    {"topic": "Неравенства", "text": "Неравенство со знаками <, >, ≤, ≥. Линейные и квадратные неравенства: 2x+1<5; x^2-4>0. Метод интервалов, ответ как промежуток, например 1<x<1.5."},
    {"topic": "Системы уравнений", "text": "Система из нескольких уравнений с несколькими неизвестными, например { x+y=10; x-y=2 }. Метод подстановки и сложения."},
    {"topic": "Проценты и пропорции", "text": "Текстовая задача на проценты, скидки, наценки и пропорции: найти сколько процентов, на сколько подорожал товар, прямая и обратная пропорция."},
    {"topic": "Степени и выражения", "text": "Упрощение и вычисление алгебраического выражения, свойства степеней: a^m·a^n=a^(m+n). Например упростить выражение или найти значение при данном x."},
    {"topic": "Функции и графики", "text": "Линейная функция y=kx+b и квадратичная y=ax^2+bx+c, график, нули функции, координаты вершины параболы, область значений."},
    {"topic": "Прогрессии", "text": "Арифметическая и геометрическая прогрессии: найти n-й член или сумму первых n членов, разность d, знаменатель q."},
    {"topic": "Геометрия: треугольники", "text": "Геометрическая задача про треугольник: теорема Пифагора, площадь, периметр, признаки подобия и равенства треугольников, углы."},
]


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    """Делит каждую строку на её длину (L2-норму), чтобы скалярное произведение = косинус."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # защита от деления на ноль
    return matrix / norms


class RagService:
    def __init__(self):
        self.api_key = os.getenv("PROXYAPI_KEY", "")
        chat_url = os.getenv("PROXYAPI_URL", "https://neuroapi.host/v1/chat/completions")
        # Эндпоинт эмбеддингов выводим из URL чата (можно переопределить переменной).
        self.embeddings_url = os.getenv(
            "PROXYAPI_EMBEDDINGS_URL",
            chat_url.replace("/chat/completions", "/embeddings"),
        )
        self.embeddings_model = os.getenv("PROXYAPI_EMBEDDINGS_MODEL", "text-embedding-3-small")
        # Кэш эталонов в памяти, чтобы не читать БД на каждый запрос.
        self._cache: Optional[List[Dict[str, Any]]] = None
        # Предпосчитанная нормализованная матрица эмбеддингов (numpy) + метаданные строк.
        self._matrix: Optional[np.ndarray] = None
        self._meta: Optional[List[Dict[str, Any]]] = None

    def _invalidate(self) -> None:
        """Сбрасывает все кэши после изменения индекса (вставка/удаление)."""
        self._cache = None
        self._matrix = None
        self._meta = None

    # ---------- Эмбеддинги ----------

    def embeddings_available(self) -> bool:
        return bool(self.api_key and self.embeddings_url)

    def _embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Один HTTP-запрос эмбеддингов для пачки строк."""
        if not texts:
            return []
        try:
            resp = requests.post(
                self.embeddings_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.embeddings_model, "input": texts},
                timeout=120,
            )
            if resp.status_code != 200:
                print(f"[RAG] embeddings HTTP {resp.status_code}: {resp.text[:300]}")
                return None
            data = resp.json()
            items = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
            vectors = [item.get("embedding", []) for item in items]
            if len(vectors) != len(texts):
                print(f"[RAG] embeddings count mismatch: got {len(vectors)}, expected {len(texts)}")
                return None
            return vectors
        except Exception as e:
            print(f"[RAG] embeddings error: {e}")
            return None

    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Считает эмбеддинги для списка строк пачками. None — если провайдер недоступен."""
        if not self.embeddings_available() or not texts:
            return None
        all_vectors: List[List[float]] = []
        for start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[start : start + EMBED_BATCH_SIZE]
            vectors = self._embed_batch(batch)
            if vectors is None:
                return None
            all_vectors.extend(vectors)
        return all_vectors

    def embed_query(self, text: str) -> Optional[List[float]]:
        vectors = self.embed_texts([text])
        if not vectors:
            return None
        return vectors[0]

    # ---------- Индексирование ----------

    def _chunk_text(self, text: str, max_chars: int = 700) -> List[str]:
        """Грубое разбиение текста учебника на куски по абзацам/длине."""
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
        chunks: List[str] = []
        buffer = ""
        for paragraph in paragraphs:
            if len(buffer) + len(paragraph) + 1 <= max_chars:
                buffer = f"{buffer}\n{paragraph}".strip()
            else:
                if buffer:
                    chunks.append(buffer)
                # Если один абзац длиннее лимита — режем по длине.
                while len(paragraph) > max_chars:
                    chunks.append(paragraph[:max_chars])
                    paragraph = paragraph[max_chars:]
                buffer = paragraph
        if buffer:
            chunks.append(buffer)
        return chunks or ([text.strip()] if text and text.strip() else [])

    def _normalize_textbook_text(self, text: str) -> str:
        """Подготавливает текст PDF: переносы перед заголовками, если они «прилипли» к абзацу."""
        text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"([^\n])(§\s*\d+)", r"\1\n\2", text)
        text = re.sub(r"([^\n])((?:Глава|ГЛАВА)\s+\d+)", r"\1\n\2", text, flags=re.IGNORECASE)
        text = re.sub(r"([^\n])(Параграф\s+\d+)", r"\1\n\2", text, flags=re.IGNORECASE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _clean_heading_title(self, title: str) -> str:
        """Убирает оглавление, кавычки и хвосты из названия главы/§."""
        title = (title or "").strip().strip("«»\"'")
        # Оглавление: «тема . . . . . 55» или «тема.....55»
        title = re.sub(r"(\s*\.\s*){3,}.*$", "", title)
        title = re.sub(r"\.{2,}.*$", "", title)
        title = re.sub(r"\s+\d{1,3}\s*$", "", title)
        title = re.sub(r"\s+", " ", title)
        return title[:200]

    def _looks_like_section_title(self, title: str) -> bool:
        """Отсекает задачи, ответы и мусор PDF — оставляет название параграфа."""
        title = self._clean_heading_title(title)
        if len(title) < 4 or len(title) > 120:
            return False
        if title[0].islower():
            return False
        low = title.lower()
        if any(low.startswith(p) for p in _TASK_LINE_PREFIXES):
            return False
        if re.search(r"[\+\=\∫√≤≥]", title) and re.search(r"\d", title):
            return False
        if re.search(r"\d+\s*решений", low):
            return False
        if len(re.findall(r"\b\d{3,}\b", title)) >= 1:
            return False
        if len(re.findall(r"\d+\.", title)) >= 2:
            return False
        if re.search(r"\.{3,}", title):
            return False
        if title.rstrip().endswith("-"):
            return False
        if not re.search(r"[а-яёА-ЯЁ]{4,}", title):
            return False
        letters = [c for c in title if c.isalpha()]
        if not letters:
            return False
        vowels = sum(1 for c in letters if c.lower() in "аеёиоуыэюяaeiou")
        if vowels < max(2, len(letters) // 6):
            return False
        if re.fullmatch(r"[А-ЯЁA-Z\s]+", title) and " " not in title.strip():
            return False
        return True

    def _looks_like_chapter_title(self, title: str) -> bool:
        title = self._clean_heading_title(title)
        if len(title) < 3:
            return False
        if re.search(r"\.{3,}", title):
            return False
        if re.fullmatch(r"\d{1,3}", title):
            return False
        return bool(re.search(r"[а-яёА-ЯЁ]{3,}", title))

    def _parse_heading_line(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Распознаёт заголовок учебника: только Глава/Часть и §/Параграф.
        Номера задач (711., 1001.) и строки ответов не считаются темами.
        """
        line = line.strip()
        if not line or len(line) > 200:
            return None

        m = re.match(
            r"^(?:Глава|ГЛАВА|Chapter)\s+(\d+|[IVXLC]+)\s*[.:]?\s*(.+)$",
            line,
            re.IGNORECASE,
        )
        if m:
            title = self._clean_heading_title(m.group(2))
            if self._looks_like_chapter_title(title):
                return ("chapter", f"Глава {m.group(1)}. {title}")

        m = re.match(r"^(?:Часть|ЧАСТЬ)\s+(\d+)\s*[.:]?\s*(.+)$", line, re.IGNORECASE)
        if m:
            title = self._clean_heading_title(m.group(2))
            if self._looks_like_chapter_title(title):
                return ("chapter", f"Часть {m.group(1)}. {title}")

        m = re.match(r"^§\s*(\d+)\s*[.:]?\s*(.+)$", line)
        if m:
            title = self._clean_heading_title(m.group(2))
            if self._looks_like_section_title(title):
                return ("section", f"§{m.group(1)}. {title}")

        m = re.match(r"^Параграф\s+(\d+)\s*[.:]?\s*(.+)$", line, re.IGNORECASE)
        if m:
            title = self._clean_heading_title(m.group(2))
            if self._looks_like_section_title(title):
                return ("section", f"Параграф {m.group(1)}. {title}")

        return None

    def _structured_sections(self, full_text: str) -> List[Dict[str, Any]]:
        """
        Режет учебник по структуре: глава (parent_topic) → параграф/§ (topic).
        Темы берутся из заголовков книги, без LLM и без базовой таксономии.
        """
        text = self._normalize_textbook_text(full_text)
        lines = text.split("\n")

        current_chapter: Optional[str] = None
        current_section: Optional[str] = None
        body_lines: List[str] = []
        pieces: List[Dict[str, Any]] = []

        def flush_body() -> None:
            nonlocal body_lines
            body = "\n".join(body_lines).strip()
            if not body:
                body_lines = []
                return
            topic = current_section or current_chapter or "Материал учебника"
            parent = current_chapter if current_section else None
            for chunk in self._chunk_text(body):
                pieces.append({"topic": topic[:255], "parent_topic": parent, "text": chunk})
            body_lines = []

        for line in lines:
            heading = self._parse_heading_line(line)
            if heading:
                level, title = heading
                flush_body()
                if level == "chapter":
                    current_chapter = title[:255]
                else:
                    current_section = title[:255]
                continue
            if line.strip():
                body_lines.append(line)

        flush_body()

        if not pieces:
            for chunk in self._chunk_text(text):
                pieces.append(
                    {"topic": "Материал учебника", "parent_topic": None, "text": chunk}
                )
        return pieces

    def add_reference(self, topic: str, text: str, source: str = "taxonomy") -> bool:
        """Добавляет один эталон (тема + текст) с эмбеддингом в БД."""
        if not has_db():
            return False
        vector = self.embed_query(text)
        if not vector:
            return False
        sess = get_db()
        if sess is None:
            return False
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            row = RagChunk(topic=topic, text=text, source=source, embedding=vector)
            sess.add(row)
            sess.commit()
            self._invalidate()
            return True
        except Exception as e:
            print(f"[RAG] add_reference error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return False
        finally:
            sess.close()

    def ingest_taxonomy(self, items: Optional[List[Dict[str, str]]] = None) -> int:
        """Загружает список тем (по умолчанию — школьную математику) одним батчем."""
        if not has_db():
            return 0
        items = items or DEFAULT_MATH_TAXONOMY
        texts = [f"{it['topic']}. {it.get('text', '')}".strip() for it in items]
        vectors = self.embed_texts(texts)
        if not vectors or len(vectors) != len(items):
            return 0
        sess = get_db()
        if sess is None:
            return 0
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            # Идемпотентность: убираем прежнюю таксономию, чтобы повторный засев не плодил дубли.
            sess.query(RagChunk).filter(RagChunk.source == "taxonomy").delete(synchronize_session=False)
            count = 0
            for it, vec in zip(items, vectors):
                sess.add(RagChunk(topic=it["topic"], text=it.get("text", it["topic"]), source="taxonomy", embedding=vec))
                count += 1
            sess.commit()
            self._invalidate()
            return count
        except Exception as e:
            print(f"[RAG] ingest_taxonomy error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return 0
        finally:
            sess.close()

    def ingest_textbook(
        self, title: str, full_text: str, topic_hint: Optional[str] = None
    ) -> Tuple[int, Optional[str]]:
        """
        Режет учебник на куски, считает эмбеддинги и сохраняет.

        Тема фрагмента:
        - если задан topic_hint — одна тема на весь файл (ручное переопределение);
        - иначе темы берутся из структуры учебника (глава → параграф/§), без LLM.

        Возвращает (число фрагментов, текст ошибки или None).
        """
        if not has_db():
            return 0, "База данных недоступна"

        if topic_hint:
            pieces = [
                {"topic": topic_hint[:255], "parent_topic": None, "text": c}
                for c in self._chunk_text(full_text)
            ]
        else:
            pieces = self._structured_sections(full_text)

        if not pieces:
            return 0, "Текст пустой или слишком короткий для нарезки на фрагменты"

        texts = [p["text"] for p in pieces]
        vectors = self.embed_texts(texts)
        if not vectors or len(vectors) != len(texts):
            return 0, (
                f"Не удалось получить эмбеддинги для {len(texts)} фрагментов "
                f"(проверьте PROXYAPI_KEY и лимиты API)"
            )

        sess = get_db()
        if sess is None:
            return 0, "Не удалось открыть сессию БД"
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            count = 0
            for piece, vec in zip(pieces, vectors):
                if not vec:
                    return count, f"Пустой вектор на фрагменте #{count + 1}"
                sess.add(
                    RagChunk(
                        topic=piece["topic"],
                        parent_topic=piece.get("parent_topic"),
                        text=piece["text"],
                        source=title,
                        embedding=vec,
                    )
                )
                count += 1
            sess.commit()
            self._invalidate()
            return count, None
        except Exception as e:
            print(f"[RAG] ingest_textbook error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return 0, f"Ошибка сохранения в БД: {e}"
        finally:
            sess.close()

    def topic_breakdown(self, source: str) -> List[Dict[str, Any]]:
        """Сколько фрагментов по каждой теме внутри источника (для отчёта в UI)."""
        counts: Dict[str, Dict[str, Any]] = {}
        for ch in self._load_chunks():
            if ch.get("source") == source:
                t = ch.get("topic") or "—"
                if t not in counts:
                    counts[t] = {"topic": t, "parent_topic": ch.get("parent_topic"), "chunks": 0}
                counts[t]["chunks"] += 1
        return sorted(counts.values(), key=lambda x: x["chunks"], reverse=True)

    # ---------- Поиск / классификация ----------

    def _load_chunks(self) -> List[Dict[str, Any]]:
        """Загружает все эталоны из БД в память (с кэшем)."""
        if self._cache is not None:
            return self._cache
        if not has_db():
            self._cache = []
            return self._cache
        sess = get_db()
        if sess is None:
            self._cache = []
            return self._cache
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            rows = sess.query(RagChunk).all()
            self._cache = [
                {
                    "topic": r.topic,
                    "parent_topic": getattr(r, "parent_topic", None),
                    "text": r.text,
                    "source": r.source,
                    "embedding": r.embedding or [],
                }
                for r in rows
            ]
            return self._cache
        except Exception as e:
            print(f"[RAG] load_chunks error: {e}")
            self._cache = []
            return self._cache
        finally:
            sess.close()

    def _ensure_index(self):
        """
        Строит (один раз и кэширует) нормализованную матрицу эмбеддингов и
        параллельный список метаданных. Возвращает (matrix, meta).
        Матрица имеет форму (N, D): N фрагментов, D=размерность эмбеддинга.
        """
        if self._matrix is not None and self._meta is not None:
            return self._matrix, self._meta
        chunks = self._load_chunks()
        rows: List[List[float]] = []
        meta: List[Dict[str, Any]] = []
        dim = max((len(c.get("embedding") or []) for c in chunks), default=0)
        for c in chunks:
            emb = c.get("embedding") or []
            if dim > 0 and len(emb) == dim:  # пропускаем битые/пустые векторы
                rows.append(emb)
                meta.append(c)
        if rows:
            self._matrix = _normalize_rows(np.asarray(rows, dtype=np.float32))
        else:
            self._matrix = np.zeros((0, 0), dtype=np.float32)
        self._meta = meta
        return self._matrix, self._meta

    def count(self) -> int:
        return len(self._load_chunks())

    def list_sources(self) -> List[Dict[str, Any]]:
        """Список источников в индексе с числом фрагментов (для управления базой)."""
        counts: Dict[str, int] = {}
        for ch in self._load_chunks():
            src = ch.get("source") or "—"
            counts[src] = counts.get(src, 0) + 1
        return [{"source": s, "chunks": n} for s, n in sorted(counts.items())]

    def list_topics(self) -> List[Dict[str, Any]]:
        """Плоский список тем (параграфов) с числом фрагментов и источниками."""
        counts: Dict[str, Dict[str, Any]] = {}
        for ch in self._load_chunks():
            t = ch.get("topic") or "—"
            if t not in counts:
                counts[t] = {
                    "topic": t,
                    "parent_topic": ch.get("parent_topic"),
                    "chunks": 0,
                    "sources": set(),
                }
            counts[t]["chunks"] += 1
            counts[t]["sources"].add(ch.get("source") or "—")
        return [
            {
                "topic": v["topic"],
                "parent_topic": v["parent_topic"],
                "chunks": v["chunks"],
                "sources": sorted(v["sources"]),
            }
            for v in sorted(counts.values(), key=lambda x: x["chunks"], reverse=True)
        ]

    def list_topic_groups(self) -> List[Dict[str, Any]]:
        """Темы, сгруппированные по главам (parent_topic) для UI."""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in self.list_topics():
            parent = item.get("parent_topic") or "Без главы"
            groups.setdefault(parent, []).append(
                {
                    "topic": item["topic"],
                    "chunks": item["chunks"],
                    "sources": item.get("sources") or [],
                }
            )
        return [
            {"parent_topic": parent, "topics": topics}
            for parent, topics in sorted(
                groups.items(),
                key=lambda x: sum(t["chunks"] for t in x[1]),
                reverse=True,
            )
        ]

    def delete_topic(self, topic: str, source: Optional[str] = None) -> int:
        """Удаляет все фрагменты темы (опционально — только в пределах одного источника)."""
        if not has_db() or not topic:
            return 0
        sess = get_db()
        if sess is None:
            return 0
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            query = sess.query(RagChunk).filter(RagChunk.topic == topic)
            if source:
                query = query.filter(RagChunk.source == source)
            deleted = query.delete(synchronize_session=False)
            sess.commit()
            self._invalidate()
            return int(deleted or 0)
        except Exception as e:
            print(f"[RAG] delete_topic error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return 0
        finally:
            sess.close()

    def delete_source(self, source: str) -> int:
        """Удаляет все фрагменты одного источника (например, перед перезаливкой учебника)."""
        if not has_db() or not source:
            return 0
        sess = get_db()
        if sess is None:
            return 0
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            deleted = sess.query(RagChunk).filter(RagChunk.source == source).delete(synchronize_session=False)
            sess.commit()
            self._invalidate()
            return int(deleted or 0)
        except Exception as e:
            print(f"[RAG] delete_source error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return 0
        finally:
            sess.close()

    def clear_all(self) -> int:
        """Полностью очищает индекс (все источники и темы)."""
        if not has_db():
            return 0
        sess = get_db()
        if sess is None:
            return 0
        try:
            from models.rag_chunk import RagChunk  # type: ignore

            deleted = sess.query(RagChunk).delete(synchronize_session=False)
            sess.commit()
            self._invalidate()
            return int(deleted or 0)
        except Exception as e:
            print(f"[RAG] clear_all error: {e}")
            try:
                sess.rollback()
            except Exception:
                pass
            return 0
        finally:
            sess.close()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Возвращает top_k ближайших эталонов с оценкой similarity.
        Косинус считается одним матрично-векторным произведением на numpy:
        similarities = M @ q, где M и q уже L2-нормированы (значит, скаляр = косинус).
        """
        matrix, meta = self._ensure_index()
        if matrix.shape[0] == 0:
            return []
        q_vec = self.embed_query(query)
        if not q_vec:
            return []
        q = np.asarray(q_vec, dtype=np.float32)
        if q.shape[0] != matrix.shape[1]:  # размерности не совпали
            return []
        norm = np.linalg.norm(q)
        if norm == 0:
            return []
        q = q / norm
        sims = matrix @ q  # (N, D) @ (D,) -> (N,): по косинусу с каждым фрагментом

        k = min(top_k, len(meta))
        # argpartition находит top-k без полной сортировки (быстрее на больших N),
        # затем сортируем только эти k по убыванию.
        top_idx = np.argpartition(-sims, k - 1)[:k]
        top_idx = top_idx[np.argsort(-sims[top_idx])]

        results = []
        for i in top_idx:
            ch = meta[int(i)]
            results.append({
                "topic": ch["topic"],
                "parent_topic": ch.get("parent_topic"),
                "text": ch["text"],
                "source": ch["source"],
                "score": round(float(sims[int(i)]), 4),
            })
        return results

    def search_textbook(self, query: str, top_k: int = 3, min_score: float = 0.25) -> List[Dict[str, Any]]:
        """
        Поиск по фрагментам загруженного учебника (исключаем служебную таксономию).
        Используется для подсказок: подмешиваем релевантный кусок учебника.
        """
        results = [r for r in self.search(query, top_k=max(top_k, 5)) if r.get("source") != "taxonomy"]
        results = [r for r in results if r.get("score", 0.0) >= min_score]
        return results[:top_k]

    def classify_topic(self, question: str, min_score: float = 0.30) -> Optional[Dict[str, Any]]:
        """
        Определяет тему вопроса через ближайший эталон.
        Возвращает None, если индекс пуст, эмбеддинги недоступны или близость низкая.
        """
        results = self.search(question, top_k=1)
        if not results:
            return None
        best = results[0]
        if best["score"] < min_score:
            return None
        return best


_rag_service: Optional[RagService] = None


def get_rag_service() -> RagService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RagService()
    return _rag_service

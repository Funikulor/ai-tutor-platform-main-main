from typing import Any, Dict, List, Optional
import os
import json
import time
import re
from datetime import datetime, timezone

try:
	from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # type: ignore
	external_available = True
except Exception:
	external_available = False

from utils.persistent_storage import persistent_storage
from utils.batched_saver import get_personality_batcher
from utils.personalization_store import (
	load_personality_profiles,
	save_personality_profile,
)
import requests
from utils.db import has_db, get_db
from models.personality_profile import PersonalityProfile, PersonalityTrait, CommunicationStyle

# Текст для ученика/учителя: без секретов, имён переменных и окружений (это только в логах backend).
ASSISTANT_UNAVAILABLE_USER_MESSAGE = (
	"Извините, сейчас ответ ассистента временно недоступен. "
	"Попробуйте позже или сообщите учителю или администратору платформы, если ошибка повторяется."
)


def assistant_response_means_llm_down(text: Optional[str]) -> bool:
	"""Провайдер не вернул ответ; наш публичный fallback (для 503 и валидации в роутерах)."""
	if not text:
		return False
	low = (text or "").lower()
	if "ответ ассистента временно недоступен" in low:
		return True
	# Совместимость со старым текстом ошибки до правки UX
	return "модель временно недоступна" in low


class AssistantService:
	"""Обёртка ассистента: онлайн (Proxy/OpenAI-compatible HTTP, Hugging Face Inference), локально — только при ASSISTANT_PROVIDER=local."""

	def __init__(self, model_name: str = None):
		self.hf_model = os.getenv("HF_MODEL", model_name or "microsoft/DialoGPT-medium")
		self.hf_token = os.getenv("HF_API_TOKEN", "")
		self.proxyapi_key = os.getenv("PROXYAPI_KEY", "")
		# OpenAI Chat Completions-совместимый POST (ProxyAPI, NeuroAPI и др.)
		self.proxyapi_url = os.getenv("PROXYAPI_URL", "https://api.proxyapi.ru/openai/v1/chat/completions")
		self.proxyapi_model = os.getenv("PROXYAPI_MODEL", "gpt-4o")  # gpt-4o (рекомендуется), gpt-4o-mini и т.д.

		explicit = (os.getenv("ASSISTANT_PROVIDER") or "").strip().lower()
		if explicit == "neuroapi":
			explicit = "proxyapi"
		elif explicit == "openai":
			print(
				"[AssistantService] ASSISTANT_PROVIDER=openai игнорируется как официальный OpenAI SDK: "
				"используется только OpenAI-compatible HTTP (PROXYAPI_KEY)."
			)
			explicit = "proxyapi"
		if explicit in ("proxyapi", "hf_api", "local"):
			self.provider = explicit
			self._provider_source = "env"
		else:
			self._provider_source = "auto"
			# Онлайн в приоритете: сначала прокси, иначе Hugging Face; без ключей — канал proxyapi (ответ будет недоступен до настройки)
			if self.proxyapi_key:
				self.provider = "proxyapi"
			elif self.hf_token:
				self.provider = "hf_api"
			else:
				self.provider = "proxyapi"

		self._pipe = None
		self._tokenizer = None
		self._model = None
		self._documents: List[Dict] = self._load_documents()
		self._personality_profiles: Dict[str, PersonalityProfile] = {}
		self._load_personality_profiles()  # Загружаем профили при инициализации
		
		ps = getattr(self, "_provider_source", "env")
		print(f"[AssistantService] Провайдер: {self.provider}" + (f" ({ps})" if ps else ""))
		print(f"[AssistantService] PROXYAPI URL: {self.proxyapi_url}")
		print(f"[AssistantService] PROXYAPI модель: {self.proxyapi_model}")
		print(f"[AssistantService] PROXYAPI ключ: {'установлен' if self.proxyapi_key else 'не установлен'}")
		print(f"[AssistantService] Hugging Face модель: {self.hf_model}; HF_API_TOKEN: {'установлен' if self.hf_token else 'не установлен'}")
	
	def _load_personality_profiles(self):
		"""Загружает профили личности из БД (с fallback)."""
		try:
			profiles_data = load_personality_profiles()
			for user_id, profile_data in profiles_data.items():
				try:
					profile = PersonalityProfile(**profile_data)
					self._personality_profiles[user_id] = profile
					print(f"[AssistantService] Загружен профиль личности для {user_id}")
				except Exception as e:
					print(f"[AssistantService] Ошибка загрузки профиля личности {user_id}: {e}")
			print(f"[AssistantService] Загружено {len(self._personality_profiles)} профилей личности")
		except Exception as e:
			print(f"[AssistantService] Ошибка загрузки профилей личности: {e}")
	
	def _save_personality_profile(self, user_id: str, force: bool = False):
		"""
		Сохраняет профиль личности в persistent_storage через батчинг
		
		Args:
			user_id: ID пользователя
			force: Если True, сохраняет немедленно (для критичных обновлений)
		"""
		try:
			if user_id in self._personality_profiles:
				profile = self._personality_profiles[user_id]
				profile_dict = profile.dict()
				profile_dict['last_updated'] = datetime.now().isoformat()
				
				# Используем батчинг для сохранения
				batcher = get_personality_batcher()
				if force:
					# Принудительное сохранение
					batcher.flush(user_id)
					# Также сохраняем напрямую для гарантии
					save_personality_profile(user_id, profile_dict)
				else:
					# Планируем сохранение через батчер
					batcher.schedule_save(user_id, profile_dict)
		except Exception as e:
			print(f"[AssistantService] Ошибка сохранения профиля личности {user_id}: {e}")
	
	def flush_all_profiles(self):
		"""Принудительно сохраняет все профили личности (используется при завершении)"""
		batcher = get_personality_batcher()
		batcher.flush_all()

	def _load_documents(self) -> List[Dict]:
		if has_db():
			sess = get_db()
			if sess is not None:
				try:
					# Lazy import Document only when DB is present
					from models.document import Document  # type: ignore
					from sqlalchemy.exc import OperationalError, ProgrammingError
					try:
						rows = sess.query(Document).limit(1000).all()
						return [{"title": r.title, "content": r.content} for r in rows]
					except (OperationalError, ProgrammingError) as e:
						# Таблицы еще не созданы, используем fallback
						print(f"[Assistant] Таблицы БД еще не созданы, используем fallback хранилище: {e}")
						sess.close()
				except Exception as e:
					print(f"[Assistant] Ошибка загрузки документов из БД: {e}")
					if sess:
						sess.close()
		docs = persistent_storage.get("documents", [])
		return docs if isinstance(docs, list) else []

	def _save_documents(self):
		if has_db():
			return  # DB is source of truth when present
		persistent_storage.set("documents", self._documents)

	def _humanize_model_text(self, text: str) -> str:
		"""Нормализует ответ модели в простой читаемый текст без markdown/latex шума."""
		if not text:
			return text
		s = str(text).strip()
		# Убираем markdown code fences и заголовки
		s = re.sub(r"```(?:\w+)?", "", s)
		s = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", s)
		# Убираем markdown-разметку, сохраняя контент
		s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
		s = re.sub(r"__([^_]+)__", r"\1", s)
		s = re.sub(r"`([^`]+)`", r"\1", s)
		# LaTeX-ограждения и частые конструкции
		s = s.replace("\\(", "").replace("\\)", "").replace("\\[", "").replace("\\]", "")
		s = s.replace("$$", "").replace("$", "")
		s = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", s)
		s = re.sub(r"\\sqrt\{([^}]+)\}", r"sqrt(\1)", s)
		s = re.sub(r"\\[a-zA-Z]+", "", s)  # остаточные latex-команды
		# Приводим маркеры списков к простому виду
		s = re.sub(r"(?m)^\s*[-*]\s+", "- ", s)
		# Чистим лишние пробелы
		s = re.sub(r"[ \t]+", " ", s)
		s = re.sub(r"\n{3,}", "\n\n", s).strip()
		# Если ответ оборван без пунктуации, обрезаем до последнего завершенного предложения
		if s and s[-1] not in ".!?":
			last_stop = max(s.rfind("."), s.rfind("!"), s.rfind("?"))
			if last_stop > int(len(s) * 0.45):
				s = s[: last_stop + 1].strip()
			elif len(s) > 0:
				s = s.rstrip(",:;-/") + "."
		return s

	def _ensure_pipe(self):
		if self.provider == "local" and self._pipe is None and external_available:
			try:
				# Используем более легкую модель для чата
				model_name = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")
				self._pipe = pipeline("text-generation", model=model_name)
			except Exception:
				try:
					# Fallback на tiny модель
					self._tokenizer = AutoTokenizer.from_pretrained("sshleifer/tiny-gpt2")
					self._model = AutoModelForCausalLM.from_pretrained("sshleifer/tiny-gpt2")
				except Exception:
					self._pipe = None

	def _prompt_for_hf_api(self, prompt: str, messages: Optional[List[Dict[str, str]]]) -> str:
		if messages:
			lines = []
			for msg in messages:
				role = msg.get("role", "user")
				content = (msg.get("content") or "").strip()
				if not content:
					continue
				if role in ("user", "assistant", "system"):
					lines.append(f"{role}: {content}")
			if lines:
				return "\n".join(lines) + "\nassistant:"
		return prompt or ""

	def _generate_proxyapi(self, prompt: str, messages: Optional[List[Dict[str, str]]] = None, max_new_tokens: int = 512) -> Optional[str]:
		"""
		Генерация через PROXYAPI (совместим с OpenAI форматом)
		
		PROXYAPI предоставляет доступ к различным AI моделям через единый API
		"""
		# Детальная проверка настроек
		if not self.proxyapi_key:
			print(f"[PROXYAPI] ❌ PROXYAPI ключ не установлен")
			print(f"[PROXYAPI] Проверьте переменную PROXYAPI_KEY в Railway Variables")
			return None
		
		if not self.proxyapi_url:
			print(f"[PROXYAPI] ❌ PROXYAPI URL не установлен")
			print(f"[PROXYAPI] Проверьте переменную PROXYAPI_URL в Railway Variables")
			return None
		
		print(f"[PROXYAPI] ✅ Настройки проверены:")
		print(f"[PROXYAPI]   URL: {self.proxyapi_url}")
		print(f"[PROXYAPI]   Модель: {self.proxyapi_model}")
		print(f"[PROXYAPI]   Ключ: {'установлен (длина: ' + str(len(self.proxyapi_key)) + ')' if self.proxyapi_key else 'не установлен'}")
		
		# Формируем сообщения для PROXYAPI (совместим с OpenAI форматом)
		proxyapi_messages = []
		if messages:
			# Конвертируем формат сообщений для PROXYAPI
			for msg in messages:
				role = msg.get("role", "user")
				content = msg.get("content", "")
				if role in ["user", "assistant", "system"]:
					proxyapi_messages.append({"role": role, "content": content})
		else:
			# Если нет истории, используем prompt как user сообщение
			proxyapi_messages = [{"role": "user", "content": prompt}]
		
		# Retry логика для обработки rate limits
		max_retries = 3
		base_delay = 1  # секунда
		
		for attempt in range(max_retries):
			try:
				print(f"[PROXYAPI] 📤 Отправка запроса (попытка {attempt + 1}/{max_retries})")
				print(f"[PROXYAPI]   URL: {self.proxyapi_url}")
				print(f"[PROXYAPI]   Модель: {self.proxyapi_model}")
				print(f"[PROXYAPI]   Сообщений: {len(proxyapi_messages)}")
				
				headers = {
					"Authorization": f"Bearer {self.proxyapi_key}",
					"Content-Type": "application/json"
				}
				
				payload = {
					"model": self.proxyapi_model,
					"messages": proxyapi_messages,
					"temperature": 0.7,
					"max_tokens": max_new_tokens
				}
				
				print(f"[PROXYAPI]   Payload: model={self.proxyapi_model}, messages={len(proxyapi_messages)}, max_tokens={max_new_tokens}")
				
				response = requests.post(
					self.proxyapi_url,
					headers=headers,
					json=payload,
					timeout=60
				)
				
				print(f"[PROXYAPI] 📥 Получен ответ: HTTP {response.status_code}")
				
				if response.status_code == 200:
					data = response.json()
					if data and "choices" in data and len(data["choices"]) > 0:
						content = data["choices"][0].get("message", {}).get("content", "")
						result = content.strip() if content else None
						
						if result:
							print(f"[PROXYAPI] Успешно получен ответ (длина: {len(result)})")
							return result
						else:
							print(f"[PROXYAPI] Пустой ответ от модели")
					else:
						print(f"[PROXYAPI] Неожиданный формат ответа: {data}")
				else:
					error_msg = response.text
					print(f"[PROXYAPI] Ошибка HTTP {response.status_code}: {error_msg}")
					
					# Обработка rate limits
					if response.status_code == 429:
						wait_time = base_delay * (2 ** attempt)
						print(f"[PROXYAPI] Rate limit превышен. Ожидание {wait_time:.1f} секунд перед повтором...")
						if attempt < max_retries - 1:
							time.sleep(wait_time)
							continue
						else:
							print(f"[PROXYAPI] Rate limit превышен после {max_retries} попыток")
							return "Извините, превышен лимит запросов к PROXYAPI. Пожалуйста, подождите немного и попробуйте снова."
					
					# Обработка ошибок аутентификации
					elif response.status_code in [401, 403]:
						print("[PROXYAPI] Ошибка аутентификации (401/403). Проверьте PROXYAPI_KEY в Variables/backend .env.")
						return ASSISTANT_UNAVAILABLE_USER_MESSAGE
					
					# Другие ошибки
					else:
						if attempt < max_retries - 1:
							wait_time = base_delay * (2 ** attempt)
							time.sleep(wait_time)
							continue
						else:
							return None
						
			except requests.exceptions.Timeout:
				wait_time = base_delay * (2 ** attempt)
				print(f"[PROXYAPI] Timeout. Повтор через {wait_time:.1f} секунд...")
				if attempt < max_retries - 1:
					time.sleep(wait_time)
					continue
				else:
					print(f"[PROXYAPI] Timeout после {max_retries} попыток")
					return None
					
			except requests.exceptions.ConnectionError as e:
				wait_time = base_delay * (2 ** attempt)
				print(f"[PROXYAPI] Ошибка подключения. Повтор через {wait_time:.1f} секунд...")
				if attempt < max_retries - 1:
					time.sleep(wait_time)
					continue
				else:
					print(f"[PROXYAPI] Ошибка подключения после {max_retries} попыток: {e}")
					return None
					
			except Exception as e:
				error_type = type(e).__name__
				print(f"[PROXYAPI] Ошибка: {error_type}: {e}")
				if attempt < max_retries - 1:
					wait_time = base_delay * (2 ** attempt)
					time.sleep(wait_time)
				else:
					return None
		
		return None

	def _generate_hf_api(self, prompt: str, max_new_tokens: int = 256) -> Optional[str]:
		"""Генерация через Hugging Face API"""
		# Пробуем с токеном, если нет - используем публичный API
		url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
		headers = {}
		if self.hf_token:
			headers["Authorization"] = f"Bearer {self.hf_token}"
		
		payload = {
			"inputs": prompt,
			"parameters": {
				"max_new_tokens": max_new_tokens,
				"temperature": 0.7,
				"do_sample": True,
				"return_full_text": False
			}
		}
		try:
			resp = requests.post(url, headers=headers, json=payload, timeout=60)
			if resp.status_code == 200:
				data = resp.json()
				if isinstance(data, list) and data and isinstance(data[0], dict):
					text = data[0].get("generated_text", "")
					# Убираем исходный промпт если он есть
					if text.startswith(prompt):
						text = text[len(prompt):].strip()
					return text or data[0].get("summary_text") or str(data[0])
				if isinstance(data, dict):
					text = data.get("generated_text", "")
					if text.startswith(prompt):
						text = text[len(prompt):].strip()
					return text or data.get("summary_text") or str(data)
				return str(data)
			elif resp.status_code == 503:
				# Модель загружается, ждем
				return None
			return None
		except Exception as e:
			return None

	def _generate(
		self,
		prompt: str,
		max_new_tokens: int = 256,
		messages: Optional[List[Dict[str, str]]] = None,
		sanitize_output: bool = True,
	) -> str:
		def _maybe_sanitize(text: str) -> str:
			return self._humanize_model_text(text) if sanitize_output else text

		# Приоритет: онлайн (OpenAI-compatible HTTP), затем Hugging Face Inference. Локально — только если ASSISTANT_PROVIDER=local.
		if self.provider != "local":
			if self.proxyapi_key:
				proxy_text = self._generate_proxyapi(prompt, messages, max_new_tokens)
				if proxy_text:
					return _maybe_sanitize(proxy_text)
				print("[AssistantService] PROXYAPI не вернул ответ; пробуем Hugging Face Inference API...")
			hf_prompt = self._prompt_for_hf_api(prompt, messages)
			api_text = self._generate_hf_api(hf_prompt, max_new_tokens)
			if api_text:
				return _maybe_sanitize(api_text)

		self._ensure_pipe()
		if self._pipe is not None:
			try:
				local_prompt = self._prompt_for_hf_api(prompt, messages) if messages else (prompt or "")
				result = self._pipe(local_prompt, max_new_tokens=max_new_tokens)
				if isinstance(result, list) and result:
					text = result[0].get("generated_text") or result[0].get("summary_text") or ""
					return _maybe_sanitize(text if isinstance(text, str) else str(text))
			except Exception:
				pass

		proxy_ok = bool(self.proxyapi_key)
		hf_tok_ok = bool(self.hf_token)
		print(
			"[AssistantService] LLM: все провайдеры вернули пустой ответ. Для оператора платформы: "
			f"provider={self.provider!r}; PROXYAPI_KEY={'задан' if proxy_ok else 'нет'}; "
			f"HF_API_TOKEN={'задан' if hf_tok_ok else 'нет'} (ASSISTANT_PROVIDER=proxyapi|hf_api|local; "
			"без значения — автопо ключам)."
		)

		return _maybe_sanitize(ASSISTANT_UNAVAILABLE_USER_MESSAGE)

	def _hw_due_display(self, due: Any) -> str:
		if due is None:
			return "без дедлайна"
		if hasattr(due, "strftime"):
			try:
				return due.strftime("%Y-%m-%d")
			except Exception:
				return str(due)
		s = str(due).strip()
		if len(s) >= 10 and s[4:5] == "-" and s[7:8] == "-":
			return s[:10]
		return s[:48] if s else "без дедлайна"

	def _get_homeworks_context(self, user_id: str) -> str:
		"""Активные ДЗ ученика: Postgres + fallback persistent_storage (как в GET /homeworks)."""
		uid = str(user_id)
		lines: List[str] = []
		seen_ids = set()
		active_statuses = ("new", "in_progress", "submitted")
		today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
		header = (
			f"Сегодняшняя дата по UTC: {today_utc}. "
			"Сравнивай дедлайны с этой датой, если ученик спрашивает про «сегодня».\n"
		)

		if has_db():
			sess = get_db()
			if sess is not None:
				try:
					from models.homework import Homework  # type: ignore
					rows = (
						sess.query(Homework)
						.filter(Homework.assigned_to == uid)
						.filter(Homework.status.in_(active_statuses))
						.order_by(Homework.due_date.asc().nulls_last())
						.limit(12)
						.all()
					)
					for hw in rows:
						title = hw.title or "Задание"
						status = hw.status or "new"
						due_s = self._hw_due_display(hw.due_date)
						lines.append(f"- {title} (статус: {status}, дедлайн: {due_s})")
						if hw.id is not None:
							seen_ids.add(hw.id)
				except Exception:
					pass
				finally:
					try:
						sess.close()
					except Exception:
						pass

		try:
			for hw in persistent_storage.get("homeworks", []) or []:
				if str(hw.get("assigned_to", "")) != uid:
					continue
				st = hw.get("status") or "new"
				if st not in active_statuses:
					continue
				hid = hw.get("id")
				if hid is not None and hid in seen_ids:
					continue
				title = hw.get("title") or "Задание"
				due_s = self._hw_due_display(hw.get("due_date"))
				lines.append(f"- {title} (статус: {st}, дедлайн: {due_s})")
				if hid is not None:
					seen_ids.add(hid)
		except Exception:
			pass

		if not lines:
			return (
				header
				+ "Активные домашние задания по данным платформы: список пуст (ученику не назначено незавершённых ДЗ или это не ученическая учётная запись). "
				"На вопросы «есть ли ДЗ» отвечай: по системе сейчас ничего не числится — не выдумывай задания.\n"
			)

		return header + "Активные домашние задания:\n" + "\n".join(lines[:15])

	def _get_library_course_context(self, context: Optional[Dict[str, Any]]) -> str:
		"""Текст урока и контрольного вопроса мини-курса из библиотеки (как в JSON курса)."""
		if not context:
			return ""
		cid = context.get("library_course_id")
		if not cid:
			return ""
		idx = context.get("library_lesson_index", 0)
		try:
			idx = int(idx)
		except (TypeError, ValueError):
			idx = 0
		try:
			from routes.materials import _load_courses_raw  # noqa: WPS433

			raw_courses = _load_courses_raw()
		except Exception:
			return ""
		course = next((c for c in raw_courses if str(c.get("id")) == str(cid)), None)
		if not course:
			return ""
		lessons = course.get("lessons") or []
		if lessons:
			idx = max(0, min(idx, len(lessons) - 1))
		else:
			idx = 0
		lesson = lessons[idx] if lessons else None

		lines: List[str] = [
			"[Мини-курс библиотеки платформы — про содержание шага и контрольные вопросы отвечай СТРОГО по этому блоку. "
			"Не выдумывай другие формулировки вопросов и не подменяй текст проверки.]",
			f"Курс: {course.get('title', '')}",
			f"Описание: {course.get('description', '')}",
			f"Предмет: {course.get('subject', '')}. Тема курса: {course.get('topic', '')}.",
			f"Открыт шаг {idx + 1} из {len(lessons) if lessons else 0}.",
		]
		if lesson:
			lines.append(f"Заголовок шага: {lesson.get('title', '')}")
			content = (lesson.get("content") or "").strip()
			if len(content) > 14000:
				content = content[:14000] + "\n…[фрагмент урока сокращён для чата]"
			if content:
				lines.append("Текст урока (как в курсе):\n" + content)
			ch = lesson.get("checkpoint") or {}
			cpt = ch.get("type") or "single_choice"
			lines.append(f"Контроль после шага — тип: {cpt}")
			q = (ch.get("question") or "").strip()
			if q:
				lines.append(f"Вопрос (дословно): {q}")
			if cpt == "single_choice":
				opts = ch.get("options") or []
				for i, opt in enumerate(opts):
					lines.append(f"  Вариант {i}: {opt}")
				ci = ch.get("correct_index")
				if ci is not None:
					lines.append(
						f"  [Справка для ассистента] Верный индекс варианта: {ci}. "
						"Не называй его ученику, пока он не попросил ответ явно или не решил сам; веди подсказками."
					)
			elif cpt == "numeric":
				ca = ch.get("correct_answer")
				if ca is not None:
					lines.append(
						f"  [Справка для ассистента] Верный ответ: {ca}. "
						"Не озвучивай сразу; помогай вычислить шагами."
					)
			elif cpt == "short_text":
				acc = ch.get("acceptable_answers") or []
				if acc:
					lines.append(
						f"  [Справка для ассистента] Допустимые ответы: {acc}. "
						"Не зачитывай список ученику; подсказывай логику."
					)

		return "\n".join(lines)

	def _get_test_context(self, context: Optional[Dict[str, Any]]) -> str:
		"""Подмешивает в чат полный контекст конкретного теста/отправки."""
		if not context or not has_db():
			return ""
		sess = get_db()
		if sess is None:
			return ""
		try:
			from models.homework import Homework, HomeworkSubmission  # type: ignore
			from models.test import Test, TestSubmission  # type: ignore

			test_id = context.get("test_id")
			homework_id = context.get("homework_id")
			test_submission_id = context.get("test_submission_id")
			question_id = context.get("question_id")

			if homework_id and not test_submission_id:
				homework = sess.get(Homework, homework_id)
				if homework is not None and not test_id:
					test_id = getattr(homework, "test_id", None)
				linked = (
					sess.query(HomeworkSubmission)
					.filter(HomeworkSubmission.homework_id == homework_id)
					.order_by(HomeworkSubmission.created_at.desc())
					.first()
				)
				if linked and getattr(linked, "test_submission_id", None):
					test_submission_id = linked.test_submission_id

			test_submission = sess.get(TestSubmission, test_submission_id) if test_submission_id else None
			if test_submission is not None and not test_id:
				test_id = test_submission.test_id
			test = sess.get(Test, test_id) if test_id else None

			if test is None:
				return ""

			lines = [
				f"\nКонтекст текущего теста: {test.title}",
				f"Тема: {test.topic or 'не указана'}",
			]
			questions = sorted(list(getattr(test, "questions", []) or []), key=lambda q: q.id or 0)
			for question in questions:
				if question_id and question.id != question_id:
					continue
				lines.append(f"- Вопрос #{question.id}: {question.question}")
				options = question.options or []
				if options:
					for idx, option in enumerate(options):
						lines.append(f"  {idx + 1}. {option}")
				if question.explanation:
					lines.append(f"  Объяснение учителя: {question.explanation}")

			if test_submission is not None:
				lines.append(
					f"Результат ученика: {test_submission.correct_count or 0} из {test_submission.total_questions or 0}, "
					f"{test_submission.score or 0}%."
				)
				for item in (test_submission.question_results or []):
					if question_id and item.get("question_id") != question_id:
						continue
					lines.append(
						f"- Ответ ученика на вопрос #{item.get('question_id')}: "
						f"{item.get('student_answer')} | верно: {'да' if item.get('is_correct') else 'нет'}"
					)
					if item.get("student_explanation"):
						lines.append(f"  Как ученик решал: {item.get('student_explanation')}")
					if item.get("correct_answer_text"):
						lines.append(f"  Правильный ответ: {item.get('correct_answer_text')}")
					if item.get("question_explanation"):
						lines.append(f"  Почему так: {item.get('question_explanation')}")

			return "\n".join(lines)
		except Exception:
			return ""
		finally:
			try:
				sess.close()
			except Exception:
				pass

	def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, 
	         user_id: Optional[str] = None, student_weaknesses: Optional[List[str]] = None,
	         user_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
		"""Чат с учетом личности и слабых мест ученика"""
		# Получаем профиль личности если есть user_id
		personality_context = ""
		if user_id:
			profile = self.get_personality_profile(user_id)
			if profile:
				# Добавляем информацию о слабых местах
				weaknesses_text = ""
				if student_weaknesses:
					weaknesses_text = f"\nСлабые места ученика: {', '.join(student_weaknesses)}. Учитывай это в ответах."
				
				# Добавляем информацию о стиле общения
				comm_style = profile.communication_style
				style_text = f"Стиль общения: {'формальный' if comm_style.formality > 0.5 else 'неформальный'}, "
				style_text += f"{'подробный' if comm_style.verbosity > 0.5 else 'краткий'}"
				interests_text = ""
				if profile.interests:
					interests_text = f"\nИнтересы ученика: {', '.join(profile.interests[:5])}."
				
				personality_context = f"\n[Контекст ученика: {style_text}.{weaknesses_text}{interests_text}]\n"
		
		# Контекст по ДЗ
		homeworks_ctx = ""
		if user_id:
			homeworks_ctx = self._get_homeworks_context(user_id)
		test_ctx = self._get_test_context(context)
		library_course_ctx = self._get_library_course_context(context)

		# Имя ученика (если есть)
		name_text = f"\nИмя ученика: {user_name}." if user_name else ""

		# Формируем системный промпт
		base_system = system_prompt or (
			"Ты дружелюбный образовательный ассистент. Помогай ученику учиться, объясняй понятно и поддерживай. "
			"Если задаешь ученику вопрос, на который трудно ответить одним точным значением, предложи 3-5 коротких вариантов ответа на выбор."
		)
		base_system = base_system + name_text
		
		# OpenAI Chat Completions-совместимый HTTP (ProxyAPI / NeuroAPI): список сообщений с system.
		if self.proxyapi_key and self.provider != "local":
			# Добавляем системное сообщение в начало
			formatted_messages = [{"role": "system", "content": f"{base_system}{personality_context}"}]
			# Добавляем последние сообщения из истории
			formatted_messages.extend(messages[-10:])  # Последние 10 сообщений для контекста
			# Контекст по ДЗ
			if homeworks_ctx:
				formatted_messages.append({"role": "system", "content": homeworks_ctx})
			if test_ctx:
				formatted_messages.append({
					"role": "system",
					"content": test_ctx + "\nЕсли ученик просит помочь, опирайся только на этот тестовый контекст и объясняй по шагам.",
				})
			if library_course_ctx:
				formatted_messages.append({
					"role": "system",
					"content": library_course_ctx
					+ "\nЕсли спрашивают про контроль после шага — формулировку вопроса и варианты бери только из блока выше. "
					"Помогай учиться вместе с курсом: поясняй идеи урока, не подменяй проверку выдуманными задачами.",
				})
			return self._generate("", max_new_tokens=1024, messages=formatted_messages)
		else:
			# Для других провайдеров используем старый формат
			history = "\n".join([f"{m.get('role','user')}: {m.get('content','')}" for m in messages[-5:]])
			lib_extra = ""
			if library_course_ctx:
				lib_extra = "\n" + library_course_ctx + "\n(Отвечай по мини-курсу только из этого контекста.)\n"
			prompt = f"{base_system}{personality_context}\n{homeworks_ctx}\n{test_ctx}{lib_extra}\n{history}\nassistant:"
			return self._generate(prompt, max_new_tokens=1024)

	def hint(self, task_text: str, student_level: Optional[str] = None) -> str:
		policy = (
			"Ты образовательный ассистент. Дай короткую подсказку, НЕ раскрывай ответ полностью, "
			"направь шагами. Спроси наводящий вопрос, предложи следующий шаг."
		)
		level = f" Уровень ученика: {student_level}." if student_level else ""
		ctx_docs = self.retrieve_context(task_text)
		ctx = "\n\n".join([f"[Источник: {d.get('title','doc')}]\n{d.get('content','')[:800]}" for d in ctx_docs])
		prompt = f"{policy}{level}\nКонтекст (можно использовать, нельзя раскрывать ответ):\n{ctx}\n\nЗадача: {task_text}\nПодсказка:"
		return self._generate(prompt, max_new_tokens=120)

	def motivational_message(self, topic: str, student_name: Optional[str] = None, deadline: Optional[str] = None) -> str:
		name = f", {student_name}" if student_name else ""
		dl = f" Дедлайн: {deadline}." if deadline else ""
		prompt = (
			"Сгенерируй очень короткое дружелюбное сообщение-приветствие и мотивацию (1-2 предложения) "
			"для задания по теме: " + topic + name + ". " + dl +
			" Тон доброжелательный, поддерживающий, без раскрытия ответов."
		)
		return self._generate(prompt, max_new_tokens=80)

	def add_document(self, title: str, content: str):
		if has_db():
			sess = get_db()
			if sess is not None:
				try:
					from models.document import Document  # type: ignore
					row = Document(title=title, content=content)
					sess.add(row)
					sess.commit()
					return
				finally:
					sess.close()
		self._documents.append({"title": title, "content": content})
		self._save_documents()

	def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
		q = (query or "").lower()
		if has_db():
			sess = get_db()
			if sess is not None and q:
				try:
					from models.document import Document  # type: ignore
					rows = sess.query(Document).filter(Document.content.ilike(f"%{query}%")).limit(50).all()
					scored = []
					for r in rows:
						text = r.content or ""
						score = text.lower().count(q)
						scored.append((score, {"title": r.title, "content": text}))
					scored.sort(key=lambda x: x[0], reverse=True)
					return [d for s, d in scored[:top_k] if s > 0]
				finally:
					sess.close()
		# fallback to in-memory/json
		scored = []
		for doc in self._documents:
			text = doc.get("content", "")
			score = (text.lower().count(q) if q else 0)
			scored.append((score, doc))
		scored.sort(key=lambda x: x[0], reverse=True)
		return [d for s, d in scored[:top_k] if s > 0]
	
	def get_personality_profile(self, user_id: str) -> Optional[PersonalityProfile]:
		"""Получить профиль личности ученика"""
		if user_id not in self._personality_profiles:
			self._personality_profiles[user_id] = PersonalityProfile(user_id=user_id)
			# Сохраняем новый профиль
			self._save_personality_profile(user_id)
		return self._personality_profiles.get(user_id)
	
	def update_personality_from_chat(self, user_id: str, messages: List[Dict[str, str]]):
		"""Обновляет профиль личности на основе диалога"""
		profile = self.get_personality_profile(user_id)
		if not profile:
			return
		
		# Добавляем сообщения в историю
		for msg in messages[-10:]:  # Последние 10 сообщений
			if msg.get("role") == "user":
				profile.chat_history.append({
					"role": "user",
					"content": msg.get("content", ""),
					"timestamp": str(datetime.now())
				})
				profile.total_messages += 1
		
		# Анализируем диалог для выявления черт личности
		# Используем простую эвристику или можно использовать LLM для анализа
		all_text = " ".join([m.get("content", "") for m in profile.chat_history[-20:]])
		all_text_lower = all_text.lower()
		
		# Определяем стиль общения
		question_count = all_text.count("?")
		profile.communication_style.question_frequency = min(question_count / max(len(profile.chat_history), 1), 1.0)
		
		# Определяем формальность (по наличию формальных слов)
		formal_words = ["пожалуйста", "спасибо", "благодарю", "извините", "прошу", "будьте добры"]
		informal_words = ["привет", "пока", "ок", "давай", "эй", "слушай"]
		formal_count = sum(1 for word in formal_words if word in all_text_lower)
		informal_count = sum(1 for word in informal_words if word in all_text_lower)
		if formal_count + informal_count > 0:
			profile.communication_style.formality = formal_count / (formal_count + informal_count)
		else:
			profile.communication_style.formality = 0.5
		
		# Определяем многословность
		avg_length = sum(len(m.get("content", "")) for m in profile.chat_history[-10:]) / max(len(profile.chat_history[-10:]), 1)
		profile.communication_style.verbosity = min(avg_length / 100, 1.0)
		
		# Определяем эмоциональный тон
		positive_words = ["отлично", "классно", "нравится", "интересно", "понял", "спасибо", "рад", "хорошо"]
		negative_words = ["плохо", "не понимаю", "сложно", "трудно", "не получается", "не могу", "устал"]
		positive_count = sum(1 for word in positive_words if word in all_text_lower)
		negative_count = sum(1 for word in negative_words if word in all_text_lower)
		if positive_count > negative_count * 2:
			profile.communication_style.emotional_tone = "positive"
		elif negative_count > positive_count * 2:
			profile.communication_style.emotional_tone = "negative"
		elif negative_count > 0:
			profile.communication_style.emotional_tone = "frustrated"
		else:
			profile.communication_style.emotional_tone = "neutral"
		
		# Выявляем черты личности на основе поведения
		self._update_personality_traits(profile, all_text_lower)
		self._update_interests(profile, all_text_lower)
		
		# Выявляем упоминания слабых мест
		weakness_keywords = ["не понимаю", "сложно", "трудно", "не получается", "не знаю", "забыл", "не помню"]
		for keyword in weakness_keywords:
			if keyword in all_text.lower():
				# Извлекаем контекст
				for msg in profile.chat_history[-5:]:
					if keyword in msg.get("content", "").lower():
						# Пытаемся извлечь тему
						content = msg.get("content", "")
						if "математик" in content.lower() or "алгебр" in content.lower():
							if "математика" not in profile.mentioned_weaknesses:
								profile.mentioned_weaknesses.append("математика")
						elif "русск" in content.lower() or "язык" in content.lower():
							if "русский язык" not in profile.mentioned_weaknesses:
								profile.mentioned_weaknesses.append("русский язык")
		
		profile.last_updated = datetime.now()
		self._personality_profiles[user_id] = profile
		# Сохраняем профиль после обновления
		self._save_personality_profile(user_id)

	def _update_interests(self, profile: PersonalityProfile, text: str):
		"""Пытается выделить интересы ученика из формулировок в диалоге."""
		interest_keywords = {
			"игры": ["игр", "minecraft", "роблокс", "roblox", "genshin", "steam", "playstation"],
			"спорт": ["спорт", "футбол", "баскетбол", "волейбол", "трениров", "бег", "танцы"],
			"музыка": ["музык", "песн", "гитара", "пианино", "вокал", "рэп"],
			"рисование": ["рисую", "рисован", "скетч", "иллюстрац", "аниме"],
			"программирование": ["программ", "код", "python", "javascript", "робот", "unity"],
			"чтение": ["читаю", "книг", "роман", "манга", "комикс"],
			"кино": ["фильм", "сериал", "кино", "мультфильм"],
		}
		for interest, keywords in interest_keywords.items():
			if any(keyword in text for keyword in keywords) and interest not in profile.interests:
				profile.interests.append(interest)
		if len(profile.interests) > 10:
			profile.interests = profile.interests[:10]
	
	def _update_personality_traits(self, profile: PersonalityProfile, text: str):
		"""Обновляет черты личности на основе анализа текста"""
		# Любознательность - много вопросов, интерес к новому
		curiosity_indicators = ["почему", "как", "что", "интересно", "хочу узнать", "расскажи", "объясни"]
		curiosity_score = min(sum(1 for word in curiosity_indicators if word in text) / 10, 1.0)
		if "curiosity" not in profile.traits:
			profile.traits["curiosity"] = PersonalityTrait(trait_name="curiosity", score=curiosity_score)
		else:
			# Усредняем с предыдущим значением
			profile.traits["curiosity"].score = (profile.traits["curiosity"].score + curiosity_score) / 2
		
		# Настойчивость - продолжает задавать вопросы, не сдается
		persistence_indicators = ["еще", "снова", "попробую", "продолжу", "не сдаюсь", "еще раз"]
		persistence_score = min(sum(1 for word in persistence_indicators if word in text) / 5, 1.0)
		if "persistence" not in profile.traits:
			profile.traits["persistence"] = PersonalityTrait(trait_name="persistence", score=persistence_score)
		else:
			profile.traits["persistence"].score = (profile.traits["persistence"].score + persistence_score) / 2
		
		# Уверенность - использует уверенные формулировки
		confidence_indicators = ["знаю", "уверен", "точно", "понял", "легко", "справлюсь", "могу"]
		confidence_score = min(sum(1 for word in confidence_indicators if word in text) / 7, 1.0)
		if "confidence" not in profile.traits:
			profile.traits["confidence"] = PersonalityTrait(trait_name="confidence", score=confidence_score)
		else:
			profile.traits["confidence"].score = (profile.traits["confidence"].score + confidence_score) / 2
		
		# Креативность - нестандартные вопросы, творческий подход
		creativity_indicators = ["может быть", "а если", "интересно", "необычно", "по-другому", "идея"]
		creativity_score = min(sum(1 for word in creativity_indicators if word in text) / 6, 1.0)
		if "creativity" not in profile.traits:
			profile.traits["creativity"] = PersonalityTrait(trait_name="creativity", score=creativity_score)
		else:
			profile.traits["creativity"].score = (profile.traits["creativity"].score + creativity_score) / 2
	
	def analyze_personality_traits(self, user_id: str) -> Dict[str, float]:
		"""Анализирует черты личности через LLM"""
		profile = self.get_personality_profile(user_id)
		if not profile or len(profile.chat_history) < 3:
			return {}
		
		# Формируем промпт для анализа
		recent_chat = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in profile.chat_history[-10:]])
		prompt = f"""Проанализируй диалог ученика и определи черты его личности. Оцени каждую черту от 0 до 1:
- curiosity (любознательность)
- persistence (настойчивость)
- confidence (уверенность)
- creativity (креативность)
- analytical_thinking (аналитическое мышление)

Диалог:
{recent_chat}

Верни только JSON с оценками, например: {{"curiosity": 0.8, "persistence": 0.6, ...}}"""
		
		try:
			result = self._generate(prompt, max_new_tokens=200)
			# Пытаемся извлечь JSON
			if "{" in result and "}" in result:
				json_str = result[result.index("{"):result.rindex("}")+1]
				traits = json.loads(json_str)
				# Обновляем профиль
				for trait_name, score in traits.items():
					if trait_name not in profile.traits:
						profile.traits[trait_name] = PersonalityTrait(trait_name=trait_name, score=float(score))
					else:
						profile.traits[trait_name].score = (profile.traits[trait_name].score + float(score)) / 2
				return traits
		except Exception:
			pass
		
		return {}


# Создаем экземпляр после загрузки .env (будет пересоздан в app.py)
assistant_service = None

def get_assistant_service():
	"""Получить или создать экземпляр AssistantService"""
	global assistant_service
	if assistant_service is None:
		assistant_service = AssistantService()
	return assistant_service

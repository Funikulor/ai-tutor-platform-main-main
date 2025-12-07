from typing import List, Dict, Optional
import os
import json
from datetime import datetime

try:
	from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # type: ignore
	external_available = True
except Exception:
	external_available = False

from utils.persistent_storage import persistent_storage
import requests
from utils.db import has_db, get_db
from models.personality_profile import PersonalityProfile, PersonalityTrait, CommunicationStyle


class AssistantService:
	"""AI Assistant wrapper with provider selection: hf_api or local pipeline."""

	def __init__(self, model_name: str = None):
		self.provider = os.getenv("ASSISTANT_PROVIDER", "ollama")  # ollama | hf_api | local
		self.hf_model = os.getenv("HF_MODEL", model_name or "microsoft/DialoGPT-medium")
		self.hf_token = os.getenv("HF_API_TOKEN", "")
		self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
		self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")  # llama3.2, mistral, qwen2.5, etc.
		self._pipe = None
		self._tokenizer = None
		self._model = None
		self._documents: List[Dict] = self._load_documents()
		self._personality_profiles: Dict[str, PersonalityProfile] = {}
		
		# Логируем настройки при инициализации
		print(f"[AssistantService] Провайдер: {self.provider}")
		print(f"[AssistantService] Ollama URL: {self.ollama_url}")
		print(f"[AssistantService] Ollama модель: {self.ollama_model}")

	def _load_documents(self) -> List[Dict]:
		if has_db():
			sess = get_db()
			if sess is not None:
				try:
					# Lazy import Document only when DB is present
					from models.document import Document  # type: ignore
					rows = sess.query(Document).limit(1000).all()
					return [{"title": r.title, "content": r.content} for r in rows]
				finally:
					sess.close()
		docs = persistent_storage.get("documents", [])
		return docs if isinstance(docs, list) else []

	def _save_documents(self):
		if has_db():
			return  # DB is source of truth when present
		persistent_storage.set("documents", self._documents)

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

	def _generate_ollama(self, prompt: str, messages: Optional[List[Dict[str, str]]] = None, max_new_tokens: int = 512) -> Optional[str]:
		"""Генерация через Ollama API (локальная нейросеть)"""
		url = f"{self.ollama_url}/api/chat"
		
		# Формируем сообщения для Ollama
		ollama_messages = []
		if messages:
			# Конвертируем формат сообщений для Ollama
			for msg in messages:
				role = msg.get("role", "user")
				content = msg.get("content", "")
				if role in ["user", "assistant", "system"]:
					ollama_messages.append({"role": role, "content": content})
		else:
			# Если нет истории, используем prompt как user сообщение
			ollama_messages = [{"role": "user", "content": prompt}]
		
		payload = {
			"model": self.ollama_model,
			"messages": ollama_messages,
			"stream": False,
			"options": {
				"temperature": 0.7,
				"num_predict": max_new_tokens,
			}
		}
		
		try:
			print(f"[Ollama] Подключение к {url}, модель: {self.ollama_model}")
			# Отключаем прокси для локальных запросов
			resp = requests.post(url, json=payload, timeout=120, proxies={"http": None, "https": None})
			print(f"[Ollama] Статус ответа: {resp.status_code}")
			
			if resp.status_code == 200:
				data = resp.json()
				message = data.get("message", {})
				content = message.get("content", "")
				result = content.strip() if content else None
				if result:
					print(f"[Ollama] Успешно получен ответ (длина: {len(result)})")
				else:
					print(f"[Ollama] Пустой ответ от модели")
				return result
			else:
				print(f"[Ollama] Ошибка HTTP {resp.status_code}: {resp.text}")
				return None
		except requests.exceptions.ConnectionError as e:
			# Ollama не запущен
			print(f"[Ollama] Ошибка подключения: {e}")
			return None
		except Exception as e:
			print(f"[Ollama] Ошибка: {type(e).__name__}: {e}")
			import traceback
			traceback.print_exc()
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

	def _generate(self, prompt: str, max_new_tokens: int = 256, messages: Optional[List[Dict[str, str]]] = None) -> str:
		# Пробуем Ollama первым (локальная нейросеть)
		ollama_text = None
		if self.provider == "ollama":
			ollama_text = self._generate_ollama(prompt, messages, max_new_tokens)
			if ollama_text:
				return ollama_text
			# Fallback на другие провайдеры если Ollama недоступна
			print("Ollama недоступна, пробуем другие провайдеры...")
		
		if self.provider == "hf_api" or (self.provider == "ollama" and not ollama_text):
			api_text = self._generate_hf_api(prompt, max_new_tokens)
			if api_text:
				return api_text
		
		# Fallback на локальный pipeline
		self._ensure_pipe()
		if self._pipe is not None:
			try:
				result = self._pipe(prompt, max_new_tokens=max_new_tokens)
				if isinstance(result, list) and result:
					text = result[0].get("generated_text") or result[0].get("summary_text") or ""
					return text if isinstance(text, str) else str(text)
			except Exception:
				pass
		
		return "Извините, модель временно недоступна. Убедитесь, что Ollama запущена (ollama serve) или проверьте настройки провайдера."

	def _get_homeworks_context(self, user_id: str) -> str:
		"""Краткий контекст по активным ДЗ ученика (из БД, если доступно)."""
		if not has_db():
			return ""
		sess = get_db()
		if sess is None:
			return ""
		try:
			from models.homework import Homework  # type: ignore
			rows = (
				sess.query(Homework)
				.filter(Homework.assigned_to == user_id)
				.filter(Homework.status.in_(["new", "in_progress", "submitted"]))
				.order_by(Homework.due_date.asc().nulls_last())
				.limit(5)
				.all()
			)
			if not rows:
				return ""
			lines = []
			for hw in rows:
				title = hw.title or "Задание"
				status = hw.status or "new"
				due = hw.due_date.strftime("%Y-%m-%d") if hw.due_date else "без дедлайна"
				lines.append(f"- {title} (статус: {status}, дедлайн: {due})")
			return "\nАктивные домашние задания:\n" + "\n".join(lines)
		except Exception:
			return ""
		finally:
			try:
				sess.close()
			except Exception:
				pass

	def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, 
	         user_id: Optional[str] = None, student_weaknesses: Optional[List[str]] = None,
	         user_name: Optional[str] = None) -> str:
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
				
				personality_context = f"\n[Контекст ученика: {style_text}.{weaknesses_text}]\n"
		
		# Контекст по ДЗ
		homeworks_ctx = ""
		if user_id:
			homeworks_ctx = self._get_homeworks_context(user_id)

		# Имя ученика (если есть)
		name_text = f"\nИмя ученика: {user_name}." if user_name else ""

		# Формируем системный промпт
		base_system = system_prompt or "Ты дружелюбный образовательный ассистент. Помогай ученику учиться, объясняй понятно и поддерживай."
		base_system = base_system + name_text
		
		# Для Ollama используем формат с системным сообщением
		if self.provider == "ollama":
			# Добавляем системное сообщение в начало
			formatted_messages = [{"role": "system", "content": f"{base_system}{personality_context}"}]
			# Добавляем последние сообщения из истории
			formatted_messages.extend(messages[-10:])  # Последние 10 сообщений для контекста
			# Контекст по ДЗ
			if homeworks_ctx:
				formatted_messages.append({"role": "system", "content": homeworks_ctx})
			return self._generate("", max_new_tokens=2048, messages=formatted_messages)
		else:
			# Для других провайдеров используем старый формат
			history = "\n".join([f"{m.get('role','user')}: {m.get('content','')}" for m in messages[-5:]])
			prompt = f"{base_system}{personality_context}\n{homeworks_ctx}\n{history}\nassistant:"
			return self._generate(prompt, max_new_tokens=2048)

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
		
		# Определяем стиль общения
		question_count = all_text.count("?")
		profile.communication_style.question_frequency = min(question_count / max(len(profile.chat_history), 1), 1.0)
		
		# Определяем формальность (по наличию формальных слов)
		formal_words = ["пожалуйста", "спасибо", "благодарю", "извините"]
		has_formal = any(word in all_text.lower() for word in formal_words)
		profile.communication_style.formality = 0.7 if has_formal else 0.3
		
		# Определяем многословность
		avg_length = sum(len(m.get("content", "")) for m in profile.chat_history[-10:]) / max(len(profile.chat_history[-10:]), 1)
		profile.communication_style.verbosity = min(avg_length / 100, 1.0)
		
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

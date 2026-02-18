from typing import List, Dict, Optional
import os
import json
import time
from datetime import datetime

try:
	from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM  # type: ignore
	external_available = True
except Exception:
	external_available = False

try:
	from openai import OpenAI, RateLimitError, APIError, APIConnectionError  # type: ignore
	openai_available = True
except Exception:
	openai_available = False
	RateLimitError = None
	APIError = None
	APIConnectionError = None

# PROXYAPI использует requests (уже импортирован)

from utils.persistent_storage import persistent_storage
from utils.batched_saver import get_personality_batcher
import requests
from utils.db import has_db, get_db
from models.personality_profile import PersonalityProfile, PersonalityTrait, CommunicationStyle


class AssistantService:
	"""AI Assistant wrapper with provider selection: hf_api or local pipeline."""

	def __init__(self, model_name: str = None):
		self.provider = os.getenv("ASSISTANT_PROVIDER", "openai")  # openai | proxyapi | hf_api | local
		self.hf_model = os.getenv("HF_MODEL", model_name or "microsoft/DialoGPT-medium")
		self.hf_token = os.getenv("HF_API_TOKEN", "")
		self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
		self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # gpt-4o-mini (рекомендуется), gpt-3.5-turbo, gpt-4o, etc.
		self.proxyapi_key = os.getenv("PROXYAPI_KEY", "")
		self.proxyapi_url = os.getenv("PROXYAPI_URL", "https://api.proxyapi.ru/openai/v1/chat/completions")  # URL для PROXYAPI
		self.proxyapi_model = os.getenv("PROXYAPI_MODEL", "gpt-4o-mini")  # Модель для PROXYAPI
		self._openai_client = None
		if openai_available and self.openai_api_key:
			try:
				self._openai_client = OpenAI(api_key=self.openai_api_key)
			except Exception as e:
				print(f"[AssistantService] Ошибка инициализации OpenAI клиента: {e}")
		self._pipe = None
		self._tokenizer = None
		self._model = None
		self._documents: List[Dict] = self._load_documents()
		self._personality_profiles: Dict[str, PersonalityProfile] = {}
		self._load_personality_profiles()  # Загружаем профили при инициализации
		
		# Логируем настройки при инициализации
		print(f"[AssistantService] Провайдер: {self.provider}")
		print(f"[AssistantService] OpenAI модель: {self.openai_model}")
		print(f"[AssistantService] OpenAI API ключ: {'установлен' if self.openai_api_key else 'не установлен'}")
		print(f"[AssistantService] PROXYAPI URL: {self.proxyapi_url}")
		print(f"[AssistantService] PROXYAPI модель: {self.proxyapi_model}")
		print(f"[AssistantService] PROXYAPI ключ: {'установлен' if self.proxyapi_key else 'не установлен'}")
	
	def _load_personality_profiles(self):
		"""Загружает профили личности из persistent_storage"""
		try:
			profiles_data = persistent_storage.get("personality_profiles", {})
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
					profiles_data = persistent_storage.get("personality_profiles", {})
					profiles_data[user_id] = profile_dict
					persistent_storage.set("personality_profiles", profiles_data)
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

	def _generate_openai(self, prompt: str, messages: Optional[List[Dict[str, str]]] = None, max_new_tokens: int = 512) -> Optional[str]:
		"""
		Генерация через OpenAI API с обработкой rate limits
		
		Лимиты для gpt-4o-mini (рекомендуется):
		- 60,000 TPM (токенов в минуту)
		- 3 RPM (запросов в минуту)
		- 200 RPD (запросов в день)
		- 200,000 TPD (токенов в день)
		"""
		if not openai_available or not self._openai_client:
			print(f"[OpenAI] OpenAI клиент недоступен")
			return None
		
		# Формируем сообщения для OpenAI
		openai_messages = []
		if messages:
			# Конвертируем формат сообщений для OpenAI
			for msg in messages:
				role = msg.get("role", "user")
				content = msg.get("content", "")
				if role in ["user", "assistant", "system"]:
					openai_messages.append({"role": role, "content": content})
		else:
			# Если нет истории, используем prompt как user сообщение
			openai_messages = [{"role": "user", "content": prompt}]
		
		# Retry логика для обработки rate limits
		max_retries = 3
		base_delay = 1  # секунда
		
		for attempt in range(max_retries):
			try:
				print(f"[OpenAI] Отправка запроса, модель: {self.openai_model} (попытка {attempt + 1}/{max_retries})")
				response = self._openai_client.chat.completions.create(
					model=self.openai_model,
					messages=openai_messages,
					temperature=0.7,
					max_tokens=max_new_tokens,
				)
				
				if response and response.choices:
					content = response.choices[0].message.content
					result = content.strip() if content else None
					if result:
						print(f"[OpenAI] Успешно получен ответ (длина: {len(result)})")
					else:
						print(f"[OpenAI] Пустой ответ от модели")
					return result
				else:
					print(f"[OpenAI] Пустой ответ от API")
					return None
					
			except RateLimitError as e:
				# Обработка rate limit ошибок
				retry_after = getattr(e, 'retry_after', None)
				if retry_after:
					wait_time = float(retry_after)
				else:
					# Exponential backoff: 1s, 2s, 4s
					wait_time = base_delay * (2 ** attempt)
				
				if attempt < max_retries - 1:
					print(f"[OpenAI] Rate limit превышен. Ожидание {wait_time:.1f} секунд перед повтором...")
					time.sleep(wait_time)
				else:
					print(f"[OpenAI] Rate limit превышен после {max_retries} попыток. Лимиты: 3 RPM, 60,000 TPM для gpt-4o-mini")
					return "Извините, превышен лимит запросов к OpenAI API. Пожалуйста, подождите немного и попробуйте снова. Лимиты: 3 запроса в минуту, 60,000 токенов в минуту."
					
			except APIConnectionError as e:
				# Ошибки подключения
				if attempt < max_retries - 1:
					wait_time = base_delay * (2 ** attempt)
					print(f"[OpenAI] Ошибка подключения. Повтор через {wait_time:.1f} секунд...")
					time.sleep(wait_time)
				else:
					print(f"[OpenAI] Ошибка подключения после {max_retries} попыток: {e}")
					return None
					
			except APIError as e:
				# Другие ошибки API
				error_code = getattr(e, 'code', None)
				if error_code == 'insufficient_quota':
					print(f"[OpenAI] Недостаточно средств на счету. Проверьте баланс на https://platform.openai.com/account/usage")
					return "Извините, недостаточно средств на счету OpenAI. Пожалуйста, пополните баланс."
				else:
					print(f"[OpenAI] Ошибка API: {type(e).__name__}: {e}")
					if attempt < max_retries - 1:
						wait_time = base_delay * (2 ** attempt)
						time.sleep(wait_time)
					else:
						return None
						
			except Exception as e:
				print(f"[OpenAI] Неожиданная ошибка: {type(e).__name__}: {e}")
				import traceback
				traceback.print_exc()
				return None
		
		return None

	def _generate_proxyapi(self, prompt: str, messages: Optional[List[Dict[str, str]]] = None, max_new_tokens: int = 512) -> Optional[str]:
		"""
		Генерация через PROXYAPI (совместим с OpenAI форматом)
		
		PROXYAPI предоставляет доступ к различным AI моделям через единый API
		"""
		if not self.proxyapi_key:
			print(f"[PROXYAPI] PROXYAPI ключ не установлен")
			return None
		
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
				print(f"[PROXYAPI] Отправка запроса, модель: {self.proxyapi_model} (попытка {attempt + 1}/{max_retries})")
				
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
				
				response = requests.post(
					self.proxyapi_url,
					headers=headers,
					json=payload,
					timeout=60
				)
				
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
						print(f"[PROXYAPI] Ошибка аутентификации. Проверьте PROXYAPI_KEY")
						return "Извините, ошибка аутентификации PROXYAPI. Проверьте настройки API ключа."
					
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

	def _generate(self, prompt: str, max_new_tokens: int = 256, messages: Optional[List[Dict[str, str]]] = None) -> str:
		# Пробуем PROXYAPI первым, если выбран
		proxyapi_text = None
		if self.provider == "proxyapi":
			proxyapi_text = self._generate_proxyapi(prompt, messages, max_new_tokens)
			if proxyapi_text:
				return proxyapi_text
			# Fallback на другие провайдеры если PROXYAPI недоступна
			print("PROXYAPI недоступна, пробуем другие провайдеры...")
		
		# Пробуем OpenAI
		openai_text = None
		if self.provider == "openai":
			openai_text = self._generate_openai(prompt, messages, max_new_tokens)
			if openai_text:
				return openai_text
			# Fallback на другие провайдеры если OpenAI недоступна
			print("OpenAI недоступна, пробуем другие провайдеры...")
		
		# Fallback на PROXYAPI, если OpenAI была выбрана но не работает
		if self.provider == "openai" and not openai_text and self.proxyapi_key:
			proxyapi_text = self._generate_proxyapi(prompt, messages, max_new_tokens)
			if proxyapi_text:
				return proxyapi_text
		
		# Fallback на OpenAI, если PROXYAPI была выбрана но не работает
		if self.provider == "proxyapi" and not proxyapi_text and openai_available and self.openai_api_key:
			openai_text = self._generate_openai(prompt, messages, max_new_tokens)
			if openai_text:
				return openai_text
		
		if self.provider == "hf_api" or ((self.provider == "openai" or self.provider == "proxyapi") and not openai_text and not proxyapi_text):
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
		
		return "Извините, модель временно недоступна. Убедитесь, что API ключ установлен в .env файле (OPENAI_API_KEY или PROXYAPI_KEY) или проверьте настройки провайдера."

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
		
		# Для OpenAI используем формат с системным сообщением
		if self.provider == "openai":
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

from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import json

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.test import Test, TestQuestion, TestSubmission
from utils.db import get_db, has_db
from services.assistant import get_assistant_service

router = APIRouter()


class ManualQuestion(BaseModel):
	question: str
	options: List[str]
	correct_index: int
	explanation: Optional[str] = None


class ManualTestCreate(BaseModel):
	title: str
	topic: Optional[str] = None
	difficulty: Optional[str] = None
	creator_id: Optional[str] = None
	questions: List[ManualQuestion]


class ManualTestUpdate(BaseModel):
	title: Optional[str] = None
	topic: Optional[str] = None
	difficulty: Optional[str] = None
	questions: Optional[List[ManualQuestion]] = None


class GeneratedTestRequest(BaseModel):
	topic: Optional[str] = None
	difficulty: Optional[str] = "medium"
	question_count: Optional[int] = 5
	creator_id: Optional[str] = None


class TestSubmitRequest(BaseModel):
	user_id: str
	answers: List[int]  # индексы ответов по порядку вопросов


def _assistant():
	return get_assistant_service()


def _serialize_test(test: Test, include_questions: bool = False) -> Dict[str, Any]:
	data = {
		"id": test.id,
		"title": test.title,
		"topic": test.topic,
		"difficulty": test.difficulty,
		"source": test.source,
		"creator_id": test.creator_id,
		"created_at": test.created_at.isoformat() if test.created_at else None,
	}
	if include_questions:
		data["questions"] = []
		for q in test.questions:
			# Определяем тип вопроса автоматически если не указан
			q_type = getattr(q, 'question_type', None)
			if not q_type:
				opts = q.options or []
				if len(opts) > 1:
					q_type = "single"  # По умолчанию single, можно улучшить логику для multiple
				elif len(opts) == 1:
					# Пытаемся определить text или numeric
					try:
						float(opts[0])
						q_type = "numeric"
					except (ValueError, TypeError):
						q_type = "text"
				else:
					q_type = "single"
			
			data["questions"].append({
				"id": q.id,
				"question": q.question,
				"options": q.options,
				"correct_index": q.correct_index,
				"question_type": q_type,
				"explanation": q.explanation,
			})
	return data


@router.post("/tests/manual", response_model=Dict[str, Any])
async def create_manual_test(payload: ManualTestCreate, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	if not payload.questions:
		raise HTTPException(status_code=400, detail="Questions are required")

	test = Test(
		title=payload.title,
		topic=payload.topic,
		difficulty=payload.difficulty,
		source="manual",
		creator_id=payload.creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for q in payload.questions:
		if q.correct_index < 0 or q.correct_index >= len(q.options):
			raise HTTPException(status_code=400, detail="correct_index is out of range")
		db.add(
			TestQuestion(
				test_id=test.id,
				question=q.question,
				options=q.options,
				correct_index=q.correct_index,
				explanation=q.explanation,
			)
		)

	db.commit()
	db.refresh(test)
	return {"test": _serialize_test(test, include_questions=True)}


@router.post("/tests/generate", response_model=Dict[str, Any])
async def generate_test(request: Request, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	
	try:
		payload = await request.json()
	except Exception as e:
		print(f"[Tests] Ошибка парсинга JSON: {e}")
		raise HTTPException(status_code=400, detail=f"Некорректный формат JSON запроса: {str(e)}")

	if payload is None:
		raise HTTPException(status_code=400, detail="Укажите тему для генерации теста (topic)")

	if not isinstance(payload, dict):
		raise HTTPException(status_code=400, detail="Некорректный формат запроса")

	topic = (payload.get("topic") or "").strip()
	difficulty = payload.get("difficulty") or "medium"
	question_count = payload.get("question_count") or 5
	creator_id = payload.get("creator_id")
	user_id = payload.get("user_id")  # Для адаптивной генерации
	subject = payload.get("subject", "Математика")
	grade = payload.get("grade", "9")
	include_explanations = payload.get("include_explanations", True)

	if not topic:
		raise HTTPException(status_code=400, detail="Укажите тему для генерации теста (topic)")

	assist = _assistant()
	
	# Получаем профиль ученика для адаптивной генерации
	student_context = ""
	weak_topics = []
	interests = []
	
	if user_id:
		try:
			from agents.orchestrator import AgentOrchestrator
			orchestrator = AgentOrchestrator()
			profile = orchestrator.profiler.get_profile(user_id)
			personality_profile = assist.get_personality_profile(user_id)
			
			if profile:
				# Собираем слабые темы
				for topic_name, mastery in profile.topic_mastery.items():
					if mastery < 0.5:
						weak_topics.append(f"{topic_name} (мастерство: {mastery:.0%})")
				
				# Добавляем частые ошибки
				if profile.error_frequency:
					top_errors = sorted(profile.error_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
					for err_tag, count in top_errors:
						weak_topics.append(f"{str(err_tag.value)} (ошибок: {count})")
			
			if personality_profile:
				interests = personality_profile.interests or []
			
			if weak_topics:
				student_context += f"\nСлабые места ученика: {', '.join(weak_topics[:5])}. Сфокусируй вопросы на этих темах для улучшения понимания."
			
			if interests:
				student_context += f"\nИнтересы ученика: {', '.join(interests[:3])}. Используй примеры из этих областей в вопросах (например, если ученик любит футбол, используй задачи про футбол)."
		except Exception as e:
			print(f"[Tests] Ошибка получения профиля ученика: {e}")
	
	print(f"[Tests] generate start topic='{topic}' diff='{difficulty}' count={question_count} creator={creator_id} user_id={user_id} adaptive={bool(user_id)}")
	
	# Формируем примеры вопросов в зависимости от предмета
	example_questions = ""
	if "математик" in subject.lower() or "алгебр" in subject.lower() or "геометр" in subject.lower():
		example_questions = '''
ПРИМЕР РЕАЛЬНОГО ВОПРОСА ПО МАТЕМАТИКЕ:
{{
  "type": "single",
  "question": "Чему равна производная функции f(x) = 3x² + 5x - 2?",
  "options": ["6x + 5", "3x + 5", "6x² + 5", "3x² + 5x"],
  "correct_index": 0,
  "explanation": "Производная функции f(x) = 3x² + 5x - 2 находится по правилу дифференцирования: производная от x² равна 2x, поэтому производная от 3x² равна 6x. Производная от 5x равна 5. Производная от константы -2 равна 0. Итого: f'(x) = 6x + 5"
}}
'''
	elif "физик" in subject.lower():
		example_questions = '''
ПРИМЕР РЕАЛЬНОГО ВОПРОСА ПО ФИЗИКЕ:
{{
  "type": "single",
  "question": "С какой силой действует Земля на тело массой 2 кг? (g = 10 м/с²)",
  "options": ["20 Н", "10 Н", "5 Н", "2 Н"],
  "correct_index": 0,
  "explanation": "Сила тяжести вычисляется по формуле F = mg, где m - масса тела, g - ускорение свободного падения. F = 2 кг × 10 м/с² = 20 Н"
}}
'''
	elif "хими" in subject.lower():
		example_questions = '''
ПРИМЕР РЕАЛЬНОГО ВОПРОСА ПО ХИМИИ:
{{
  "type": "single",
  "question": "Какая валентность у атома кислорода в молекуле воды H₂O?",
  "options": ["II", "I", "III", "IV"],
  "correct_index": 0,
  "explanation": "В молекуле воды H₂O атом кислорода связан с двумя атомами водорода, каждый из которых имеет валентность I. Следовательно, валентность кислорода равна II"
}}
'''
	else:
		example_questions = '''
ПРИМЕР РЕАЛЬНОГО ВОПРОСА:
{{
  "type": "single",
  "question": "Конкретный вопрос, проверяющий знание темы '{topic}'",
  "options": ["Правильный конкретный ответ", "Неправильный ответ с типичной ошибкой", "Неправильный ответ", "Неправильный ответ"],
  "correct_index": 0,
  "explanation": "Подробное объяснение с конкретными фактами и обоснованием правильного ответа"
}}
'''
	
	# Формируем промпт с учетом адаптивности
	prompt = f"""Ты - опытный учитель {subject.lower()} для {grade} класса. Твоя задача - создать РЕАЛЬНЫЙ тест с КОНКРЕТНЫМИ вопросами по теме "{topic}".

ЗАПРЕЩЕНО:
❌ Использовать фразы "Пример вопроса", "Пример по теме"
❌ Создавать варианты ответов типа "Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"
❌ Писать объяснения типа "Правильный ответ - первый вариант"
❌ Создавать общие, абстрактные вопросы без конкретики

ОБЯЗАТЕЛЬНО:
✅ Каждый вопрос должен быть КОНКРЕТНЫМ и проверять РЕАЛЬНЫЕ знания по теме "{topic}"
✅ Варианты ответов должны содержать РЕАЛЬНЫЕ ответы, формулы, числа, факты
✅ Объяснения должны быть ПОДРОБНЫМИ с формулами, примерами, обоснованием
✅ Вопросы должны быть РАЗНООБРАЗНЫМИ по типам и сложности

ПАРАМЕТРЫ:
- Предмет: {subject}
- Класс: {grade}
- Тема: {topic}
- Сложность: {difficulty}
- Количество вопросов: {question_count}
{student_context}

{example_questions}

ТИПЫ ВОПРОСОВ:
1. "single" - один правильный ответ из 4 вариантов (большинство вопросов)
2. "multiple" - несколько правильных ответов
3. "numeric" - числовой ответ (для задач)
4. "text" - текстовый ответ (для развернутых вопросов)

ФОРМАТ ОТВЕТА (строго JSON, без дополнительного текста до и после):
{{
  "title": "Тест по теме: {topic}",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "type": "single",
      "question": "КОНКРЕТНЫЙ вопрос по теме {topic} с конкретными данными, формулами или фактами",
      "options": ["Правильный конкретный ответ", "Неправильный ответ (типичная ошибка)", "Неправильный ответ", "Неправильный ответ"],
      "correct_index": 0,
      "explanation": "ПОДРОБНОЕ объяснение с формулами, примерами, пошаговым решением или обоснованием"
    }}
  ]
}}

ВАЖНО: Создай ровно {question_count} РЕАЛЬНЫХ вопросов по теме "{topic}". Каждый вопрос должен быть уникальным и проверять конкретные знания. НЕ создавай примеры или заглушки!"""
	
	try:
		# Формируем system message для более четких инструкций
		system_message = f"""Ты - опытный учитель {subject.lower()} для {grade} класса. Твоя задача - создавать РЕАЛЬНЫЕ вопросы для тестов.

КРИТИЧЕСКИ ВАЖНО:
- НИКОГДА не начинай вопрос со слов "Пример вопроса" или "Пример по теме"
- НИКОГДА не используй фразы типа "Пример вопроса по теме..."
- Каждый вопрос должен быть КОНКРЕТНЫМ с формулами, числами или фактами
- Варианты ответов должны быть РЕАЛЬНЫМИ ответами, а не "Вариант 1", "Вариант 2"
- Объяснения должны быть ПОДРОБНЫМИ с обоснованием

Примеры ПЛОХИХ вопросов (НЕ ДЕЛАЙ ТАК):
❌ "Пример вопроса по теме Интегралы?"
❌ Варианты: "Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"

Примеры ХОРОШИХ вопросов (ДЕЛАЙ ТАК):
✅ "Чему равен интеграл ∫(2x + 3)dx?"
✅ Варианты: "x² + 3x + C", "x² + 3x", "2x² + 3x + C", "x + 3"
"""
		
		# Используем messages для передачи system message в Ollama
		messages = [
			{"role": "system", "content": system_message},
			{"role": "user", "content": prompt}
		]
		
		print(f"[Tests] Отправляем промпт в AI (длина: {len(prompt)} символов)")
		print(f"[Tests] System message (первые 300 символов): {system_message[:300]}...")
		raw = assist._generate(prompt, max_new_tokens=4000, messages=messages)
		print(f"[Tests] Получен ответ от AI, длина: {len(raw)} символов")
		print(f"[Tests] Ответ AI (первые 1000 символов):\n{raw[:1000]}")
		if len(raw) > 1000:
			print(f"[Tests] ... (еще {len(raw) - 1000} символов)")
	except Exception as e:
		print(f"[Tests] Ошибка генерации через AI: {e}")
		raise HTTPException(status_code=500, detail=f"Ошибка генерации через AI: {str(e)}. Убедитесь, что Ollama запущена или проверьте настройки провайдера.")

	if not raw or len(raw.strip()) == 0:
		raise HTTPException(status_code=500, detail="AI не вернул ответ. Проверьте настройки Ollama или другого провайдера.")

	# Пытаемся вытащить JSON
	json_match = re.search(r"\{.*\}", raw, re.DOTALL)
	if not json_match:
		print(f"[Tests] JSON not found in raw response. First 500 chars: {raw[:500]}")
		raise HTTPException(status_code=500, detail="Не удалось найти JSON в ответе AI. Попробуйте еще раз или проверьте настройки AI.")
	try:
		json_str = json_match.group()
		print(f"[Tests] Извлечен JSON, длина: {len(json_str)} символов")
		data = json.loads(json_str)
		print(f"[Tests] JSON успешно распарсен, найдено ключей: {list(data.keys())}")
	except json.JSONDecodeError as e:
		print(f"[Tests] JSON parse error: {e}")
		print(f"[Tests] JSON snippet (первые 500 символов): {json_match.group()[:500]}")
		print(f"[Tests] JSON snippet (последние 500 символов): {json_match.group()[-500:]}")
		raise HTTPException(status_code=500, detail=f"Ошибка парсинга JSON от AI: {str(e)}. Попробуйте еще раз.")
	except Exception as e:
		print(f"[Tests] Unexpected error parsing JSON: {e}")
		raise HTTPException(status_code=500, detail=f"Неожиданная ошибка при обработке ответа AI: {str(e)}")

	questions = data.get("questions") or []
	print(f"[Tests] Найдено вопросов в JSON: {len(questions)}")
	if not questions:
		print("[Tests] ERROR: No questions in generated test")
		print(f"[Tests] Данные из JSON: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
		raise HTTPException(status_code=500, detail="No questions in generated test")
	
	# Валидация: проверяем, что вопросы не являются примерами/заглушками
	example_keywords = ["пример вопроса", "пример по теме", "example question", "sample question"]
	placeholder_keywords = ["правильный ответ - первый", "правильный ответ - второй", "правильный ответ - третий", 
	                       "правильный ответ - первый вариант", "правильный ответ - второй вариант"]
	placeholder_options = ["вариант 1", "вариант 2", "вариант 3", "вариант 4", 
	                      "option 1", "option 2", "option 3", "option 4",
	                      "вариант1", "вариант2", "вариант3", "вариант4"]
	
	invalid_questions = []
	valid_questions = []
	
	for i, q in enumerate(questions):
		question_text = (q.get("question") or "").strip()
		explanation = (q.get("explanation") or "").strip()
		
		# Пропускаем пустые вопросы
		if not question_text:
			invalid_questions.append(f"Вопрос {i+1}: пустой текст вопроса")
			continue
		
		# Проверяем, не является ли вопрос примером
		question_lower = question_text.lower()
		if any(keyword in question_lower for keyword in example_keywords):
			invalid_questions.append(f"Вопрос {i+1}: содержит фразу 'пример вопроса' или 'пример по теме'")
			continue
		
		# Проверяем, не начинается ли вопрос со слова "Пример"
		if question_lower.startswith("пример"):
			invalid_questions.append(f"Вопрос {i+1}: начинается со слова 'Пример' - это заглушка")
			continue
		
		# Проверяем варианты ответов для single/multiple
		if q.get("type") in ["single", "multiple"]:
			options = q.get("options") or []
			if len(options) < 2:
				invalid_questions.append(f"Вопрос {i+1}: недостаточно вариантов ответа (нужно минимум 2, получено {len(options)})")
				continue
			
			# Проверяем, что варианты не являются просто "Вариант 1", "Вариант 2" и т.д.
			option_texts = [str(opt).strip().lower() for opt in options if opt]
			
			# Если все варианты - это просто "Вариант N", это заглушка
			all_are_placeholders = all(opt in placeholder_options for opt in option_texts)
			if all_are_placeholders:
				invalid_questions.append(f"Вопрос {i+1}: все варианты ответов являются заглушками ('Вариант 1', 'Вариант 2' и т.д.)")
				print(f"[Tests] Вопрос {i+1} варианты: {option_texts}")
				continue
			
			# Проверяем, что варианты достаточно разные (не все одинаковые)
			if len(set(option_texts)) < 2:
				invalid_questions.append(f"Вопрос {i+1}: варианты ответов слишком похожи или одинаковые")
				continue
			
			# Проверяем, что варианты не слишком короткие (меньше 3 символов - подозрительно)
			short_options = [opt for opt in option_texts if len(opt) < 3]
			if len(short_options) >= len(option_texts) * 0.5:  # Больше половины слишком короткие
				invalid_questions.append(f"Вопрос {i+1}: слишком много коротких вариантов ответа (возможно заглушки)")
				continue
		
		# Проверяем объяснение на заглушки
		if include_explanations:
			if not explanation or len(explanation.strip()) < 10:
				invalid_questions.append(f"Вопрос {i+1}: отсутствует или слишком короткое объяснение (минимум 10 символов)")
				continue
			
			explanation_lower = explanation.lower()
			if any(keyword in explanation_lower for keyword in placeholder_keywords):
				invalid_questions.append(f"Вопрос {i+1}: объяснение содержит фразу-заглушку типа 'Правильный ответ - первый вариант'")
				print(f"[Tests] Вопрос {i+1} объяснение: {explanation[:100]}")
				continue
		
		# Вопрос прошел валидацию
		valid_questions.append(q)
		print(f"[Tests] Вопрос {i+1} прошел валидацию: {question_text[:50]}...")
	
	# Если слишком много невалидных вопросов, выдаем ошибку
	invalid_ratio = len(invalid_questions) / len(questions) if questions else 1.0
	if invalid_ratio > 0.3:  # Больше 30% вопросов - заглушки
		error_msg = f"AI сгенерировал слишком много вопросов-заглушек ({len(invalid_questions)} из {len(questions)}). Это означает, что AI не понял инструкцию или модель работает некорректно. Попробуйте перегенерировать тест или проверьте настройки AI (Ollama должна быть запущена)."
		print(f"[Tests] ERROR: {error_msg}")
		print(f"[Tests] Проблемные вопросы: {invalid_questions}")
		print(f"[Tests] Полный ответ AI (первые 1000 символов): {raw[:1000]}")
		raise HTTPException(status_code=500, detail=error_msg)
	
	if invalid_questions:
		print(f"[Tests] WARNING: Обнаружены некоторые вопросы-заглушки: {invalid_questions}")
		print(f"[Tests] Используем {len(valid_questions)} валидных вопросов из {len(questions)}")
		questions = valid_questions  # Используем только валидные вопросы
		
		if not questions:
			raise HTTPException(status_code=500, detail="Все сгенерированные вопросы оказались заглушками. Попробуйте перегенерировать тест или проверьте настройки AI.")

	title = data.get("title") or f"Тест: {topic}"
	topic = data.get("topic") or topic
	diff = data.get("difficulty") or difficulty
	print(f"[Tests] parsed title='{title}' topic='{topic}' diff='{diff}' questions={len(questions)}")

	test = Test(
		title=title,
		topic=topic,
		difficulty=diff,
		source="ai",
		creator_id=creator_id,
		created_at=datetime.utcnow(),
	)
	db.add(test)
	db.flush()

	for q in questions:
		q_type = q.get("type", "single")
		opts = q.get("options") or []
		
		# Для разных типов вопросов обрабатываем по-разному
		if q_type in ["single", "multiple"]:
			if not opts or len(opts) < 2:
				# Если нет вариантов, пропускаем или создаем дефолтные
				continue
			correct_index = q.get("correct_index")
			if correct_index is None:
				correct_index = q.get("correct_answer", 0)
			# Для multiple choice может быть массив
			if q_type == "multiple" and isinstance(correct_index, list):
				# Берем первый правильный индекс для хранения
				correct_index = correct_index[0] if correct_index else 0
			if not isinstance(correct_index, int):
				correct_index = 0
			if correct_index < 0 or correct_index >= len(opts):
				correct_index = 0
		else:
			# Для text и numeric - сохраняем правильный ответ в options[0] как строку
			correct_answer = q.get("correct_answer", "")
			opts = [str(correct_answer)] if correct_answer else [""]
			correct_index = 0
		
		db.add(
			TestQuestion(
				test_id=test.id,
				question=q.get("question", ""),
				options=opts,
				correct_index=correct_index,
				question_type=q_type,
				explanation=q.get("explanation") if include_explanations else None,
			)
		)

	try:
		db.commit()
	except Exception as e:
		db.rollback()
		print(f"[Tests] Database commit error: {e}")
		raise HTTPException(status_code=500, detail=f"Ошибка сохранения теста в базу данных: {str(e)}")
	
	try:
		db.refresh(test)
	except Exception as e:
		print(f"[Tests] Database refresh error: {e}")
		# Продолжаем, даже если refresh не удался - у нас есть test.id
	
	print(f"[Tests] saved test id={test.id} title={title} questions={len(questions)} topic={topic}")
	
	try:
		serialized = _serialize_test(test, include_questions=True)
		if not serialized or not isinstance(serialized, dict):
			raise ValueError("_serialize_test returned invalid data")
		if "id" not in serialized:
			raise ValueError("_serialize_test returned data without id")
		print(f"[Tests] serialized test: id={serialized.get('id')}, questions_count={len(serialized.get('questions', []))}")
		return {"test": serialized}
	except Exception as e:
		print(f"[Tests] Serialization error: {e}")
		raise HTTPException(status_code=500, detail=f"Ошибка сериализации теста: {str(e)}")


@router.get("/tests", response_model=List[Dict[str, Any]])
async def list_tests(topic: Optional[str] = None, creator_id: Optional[str] = None, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	stmt = select(Test)
	if topic:
		stmt = stmt.where(Test.topic == topic)
	if creator_id:
		stmt = stmt.where(Test.creator_id == creator_id)
	rows = db.execute(stmt).scalars().all()
	return [_serialize_test(t, include_questions=False) for t in rows]


@router.get("/tests/{test_id}", response_model=Dict[str, Any])
async def get_test(test_id: int, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	return _serialize_test(test, include_questions=True)


@router.put("/tests/{test_id}", response_model=Dict[str, Any])
async def update_test(test_id: int, payload: ManualTestUpdate, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	if payload.title is not None:
		test.title = payload.title
	if payload.topic is not None:
		test.topic = payload.topic
	if payload.difficulty is not None:
		test.difficulty = payload.difficulty

	# Если переданы вопросы — перезаписываем
	if payload.questions is not None:
		# удалить старые
		for q in list(test.questions):
			db.delete(q)
		db.flush()
		for q in payload.questions:
			if q.correct_index < 0 or q.correct_index >= len(q.options):
				raise HTTPException(status_code=400, detail="correct_index is out of range")
			db.add(
				TestQuestion(
					test_id=test.id,
					question=q.question,
					options=q.options,
					correct_index=q.correct_index,
					explanation=q.explanation,
				)
			)

	db.commit()
	db.refresh(test)
	return _serialize_test(test, include_questions=True)


@router.delete("/tests/{test_id}", response_model=Dict[str, Any])
async def delete_test(test_id: int, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	db.delete(test)
	db.commit()
	return {"ok": True}


@router.post("/tests/{test_id}/submit", response_model=Dict[str, Any])
async def submit_test(test_id: int, payload: TestSubmitRequest, db: Session = Depends(get_db)):
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	test = db.get(Test, test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")

	questions = test.questions
	if len(payload.answers) != len(questions):
		raise HTTPException(status_code=400, detail="Answers count mismatch")

	correct = 0
	for ans, q in zip(payload.answers, questions):
		if ans == q.correct_index:
			correct += 1
	score_pct = int(round(100 * correct / max(1, len(questions))))

	feedback = None
	try:
		assist = _assistant()
		qtext = "\n".join([f"Вопрос: {q.question}\nТвой ответ: {a}, правильный: {q.correct_index}" for q, a in zip(questions, payload.answers)])
		prompt = f"Оцени результаты теста. Правильных ответов: {correct} из {len(questions)} ({score_pct}%). Дай 2-3 рекомендации кратко. \n{qtext}"
		feedback = assist._generate(prompt, max_new_tokens=200)
	except Exception:
		feedback = None

	sub = TestSubmission(
		test_id=test_id,
		user_id=payload.user_id,
		answers=payload.answers,
		score=score_pct,
		feedback=feedback,
		created_at=datetime.utcnow(),
	)
	db.add(sub)
	db.commit()
	db.refresh(sub)

	return {
		"score": score_pct,
		"correct": correct,
		"total": len(questions),
		"feedback": feedback,
		"submission_id": sub.id,
	}


class TestAssignRequest(BaseModel):
	test_id: int
	student_ids: List[str]
	due_date: Optional[str] = None


@router.post("/tests/assign", response_model=Dict[str, Any])
async def assign_test_as_homework(payload: TestAssignRequest, db: Session = Depends(get_db)):
	"""
	Назначить тест ученикам как домашнее задание
	"""
	if not has_db() or db is None:
		raise HTTPException(status_code=503, detail="Database is not configured")
	
	test = db.get(Test, payload.test_id)
	if not test:
		raise HTTPException(status_code=404, detail="Test not found")
	
	from models.homework import Homework
	from datetime import datetime as dt
	
	created_homeworks = []
	due_date_obj = None
	if payload.due_date:
		try:
			due_date_obj = dt.fromisoformat(payload.due_date.replace('Z', '+00:00'))
		except Exception:
			try:
				due_date_obj = dt.strptime(payload.due_date, '%Y-%m-%d')
			except Exception:
				pass
	
	for student_id in payload.student_ids:
		homework = Homework(
			title=f"Тест: {test.title}",
			description=f"Выполните тест по теме: {test.topic or 'без темы'}",
			subject=test.topic or "Общее",
			due_date=due_date_obj,
			status="new",
			assigned_to=student_id,
			created_by=test.creator_id,
			test_id=test.id,
			created_at=dt.utcnow(),
		)
		db.add(homework)
		created_homeworks.append({
			"id": homework.id,
			"title": homework.title,
			"assigned_to": student_id,
			"due_date": homework.due_date.isoformat() if homework.due_date else None,
		})
	
	db.commit()
	
	return {
		"success": True,
		"test_id": test.id,
		"test_title": test.title,
		"homeworks": created_homeworks,
		"assigned_count": len(created_homeworks),
	}



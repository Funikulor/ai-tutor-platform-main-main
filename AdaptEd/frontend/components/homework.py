"""
Компонент для сдачи домашних заданий
"""
import streamlit as st
import requests
from typing import Dict, Any


def _client():
	session = requests.Session()
	session.trust_env = False
	return session


def show_homework_submission():
	"""Интерфейс сдачи домашнего задания"""
	st.header("📝 Сдача домашнего задания")
	
	user_id = st.session_state.get("user_id", "")
	
	if not user_id:
		st.warning("⚠️ Необходимо войти в систему")
		return
	
	# Форма для сдачи задания
	with st.form("homework_submission"):
		st.subheader("Информация о задании")
		
		homework_id = st.text_input("ID задания (опционально)")
		topic = st.selectbox("Тема", ["Математика", "Русский язык", "Алгебра", "Геометрия", "Другое"])
		question = st.text_area("Текст задания", height=100, placeholder="Введите текст задания...")
		
		st.subheader("Ваше решение")
		answer = st.text_input("Ответ (число или текст)")
		solution_description = st.text_area(
			"Подробное описание решения",
			height=200,
			placeholder="Опишите, как вы решали это задание. Какие шаги вы предприняли? Где возникли трудности?"
		)
		
		submitted = st.form_submit_button("📤 Сдать задание", use_container_width=True)
		
		if submitted:
			if not question or not solution_description:
				st.error("⚠️ Заполните все обязательные поля")
			else:
				with st.spinner("Анализирую ваше решение..."):
					try:
						resp = _client().post(
							"http://127.0.0.1:8000/homework/submit",
							json={
								"user_id": user_id,
								"homework_id": homework_id if homework_id else None,
								"question": question,
								"answer": answer if answer else None,
								"solution_description": solution_description,
								"topic": topic
							},
							timeout=60
						)
						
						if resp.status_code == 200:
							data = resp.json()
							st.success("✅ Задание успешно сдано!")
							
							# Показываем анализ
							st.subheader("📊 Анализ вашего решения")
							analysis = data.get("analysis", "Анализ недоступен")
							st.write(analysis)
							
							# Рекомендации
							recommendations = data.get("recommendations")
							if recommendations:
								st.info(f"💡 {recommendations}")
							
							# Предложение посмотреть статистику
							if st.button("📈 Посмотреть мою статистику"):
								st.session_state.current_page = "statistics"
								st.rerun()
						else:
							st.error(f"Ошибка: {resp.status_code}")
					except requests.exceptions.Timeout:
						st.error("⏱️ Превышено время ожидания. Попробуйте еще раз.")
					except Exception as e:
						st.error(f"Ошибка: {e}")


def show_test_interface():
	"""Интерфейс для прохождения тестов"""
	st.header("📋 Тесты")
	
	user_id = st.session_state.get("user_id", "")
	
	if not user_id:
		st.warning("⚠️ Необходимо войти в систему")
		return
	
	# Генерация нового теста
	with st.expander("🎲 Создать новый тест"):
		with st.form("generate_test"):
			topic = st.selectbox("Тема теста", ["Математика", "Русский язык", "Алгебра", "Геометрия"])
			difficulty = st.selectbox("Сложность", ["easy", "medium", "hard"])
			question_count = st.slider("Количество вопросов", 3, 10, 5)
			
			generate = st.form_submit_button("Создать тест")
			
			if generate:
				with st.spinner("Генерирую персонализированный тест..."):
					try:
						resp = _client().post(
							"http://127.0.0.1:8000/tests/generate",
							json={
								"user_id": user_id,
								"topic": topic,
								"difficulty": difficulty,
								"question_count": question_count
							},
							timeout=60
						)
						
						if resp.status_code == 200:
							test_data = resp.json()
							st.session_state.current_test = test_data
							st.success("✅ Тест создан!")
							st.rerun()
						else:
							st.error(f"Ошибка создания теста: {resp.status_code}")
					except Exception as e:
						st.error(f"Ошибка: {e}")
	
	# Прохождение теста
	if "current_test" in st.session_state:
		test_data = st.session_state.current_test
		st.subheader(f"Тест: {test_data.get('topic', 'Без темы')}")
		
		questions = test_data.get("questions", [])
		user_answers = {}
		
		if "test_answers" not in st.session_state:
			st.session_state.test_answers = {}
		
		for i, q in enumerate(questions):
			st.write(f"**Вопрос {i+1}:** {q.get('question', '')}")
			options = q.get("options", [])
			
			# Радио-кнопки для выбора ответа
			selected = st.radio(
				"Выберите ответ:",
				options,
				key=f"test_q_{i}",
				index=st.session_state.test_answers.get(i, None)
			)
			
			if selected:
				st.session_state.test_answers[i] = options.index(selected)
			
			st.divider()
		
		col1, col2 = st.columns(2)
		with col1:
			if st.button("✅ Завершить тест", use_container_width=True):
				# Отправляем ответы
				answers = {i: st.session_state.test_answers.get(i) for i in range(len(questions))}
				
				with st.spinner("Проверяю результаты..."):
					try:
						resp = _client().post(
							"http://127.0.0.1:8000/tests/submit",
							json={
								"user_id": user_id,
								"test_id": test_data.get("test_id"),
								"answers": answers
							}
						)
						
						if resp.status_code == 200:
							result = resp.json()
							st.success("✅ Тест завершен!")
							
							# Показываем результаты
							score = result.get("score", 0)
							st.metric("Результат", f"{score}%")
							
							analysis = result.get("analysis", "")
							if analysis:
								st.write("**Анализ:**", analysis)
							
							# Очищаем тест
							del st.session_state.current_test
							del st.session_state.test_answers
							st.rerun()
					except Exception as e:
						st.error(f"Ошибка: {e}")
		
		with col2:
			if st.button("❌ Отменить тест", use_container_width=True):
				del st.session_state.current_test
				del st.session_state.test_answers
				st.rerun()


def show_statistics():
	"""Показывает статистику и слабые места ученика"""
	st.header("📊 Статистика и анализ")
	
	user_id = st.session_state.get("user_id", "")
	
	if not user_id:
		st.warning("⚠️ Необходимо войти в систему")
		return
	
	try:
		resp = _client().get(f"http://127.0.0.1:8000/statistics/{user_id}")
		
		if resp.status_code == 200:
			data = resp.json()
			
			# Основная статистика
			stats = data.get("statistics", {})
			col1, col2, col3, col4 = st.columns(4)
			
			with col1:
				st.metric("📊 Точность", f"{stats.get('accuracy_rate', 0):.1f}%")
			with col2:
				st.metric("✅ Заданий", stats.get('total_tasks', 0))
			with col3:
				st.metric("⭐ Уровень", stats.get('level', 1))
			with col4:
				st.metric("🏆 Очки", stats.get('points', 0))
			
			# Слабые места
			weaknesses = data.get("weaknesses", [])
			if weaknesses:
				st.subheader("⚠️ Выявленные слабые места")
				for w in weaknesses:
					with st.expander(f"🔴 {w.get('name', 'Неизвестно')}"):
						st.write(w.get('description', ''))
						st.write(f"**Тип:** {w.get('type', '')}")
			
			# Сильные стороны
			strengths = data.get("strengths", [])
			if strengths:
				st.subheader("✅ Сильные стороны")
				for s in strengths:
					st.success(f"✨ {s}")
			
			# Профиль личности
			personality = data.get("personality")
			if personality:
				with st.expander("👤 Профиль личности"):
					comm_style = personality.get("communication_style", {})
					st.write(f"**Стиль общения:** {'Формальный' if comm_style.get('formality', 0) > 0.5 else 'Неформальный'}")
					st.write(f"**Многословность:** {'Подробный' if comm_style.get('verbosity', 0) > 0.5 else 'Краткий'}")
					
					traits = personality.get("traits", {})
					if traits:
						st.write("**Черты личности:**")
						for trait, score in traits.items():
							st.progress(score, text=f"{trait}: {score:.1%}")
		else:
			st.error("Ошибка загрузки статистики")
	except Exception as e:
		st.error(f"Ошибка: {e}")




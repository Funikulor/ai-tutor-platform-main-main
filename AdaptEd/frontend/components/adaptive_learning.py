"""
Компонент адаптивного обучения с ИИ-агентами
"""
import streamlit as st
import requests


def generate_personalized_tasks(user_id: str, topic: str = "general", count: int = 3):
    """
    Генерирует персонализированные задания для ученика
    """
    try:
        session = requests.Session()
        session.trust_env = False  # Отключаем прокси
        
        response = session.post(
            "http://127.0.0.1:8000/agents/generate-tasks",
            json={
                "user_id": user_id,
                "topic": topic,
                "count": count
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('tasks', [])
        else:
            st.error(f"Ошибка генерации заданий: {response.status_code}")
            return []
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return []


def submit_task_with_ai_analysis(user_id: str, task_id: int, question: str, 
                                 user_answer: int, correct_answer: int):
    """
    Отправляет задание с анализом через ИИ
    """
    try:
        session = requests.Session()
        session.trust_env = False  # Отключаем прокси
        
        response = session.post(
            "http://127.0.0.1:8000/agents/submit-task",
            json={
                "user_id": user_id,
                "task_id": task_id,
                "question": question,
                "user_answer": user_answer,
                "correct_answer": correct_answer
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None


def request_hint(task_text: str, student_level: str = "") -> str:
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            "http://127.0.0.1:8000/assistant/chat",
            json={
                "messages": [{"role": "user", "content": "Подскажи по задаче"}],
                "mode": "hint",
                "context": {"task": task_text, "level": student_level},
            },
        )
        if resp.status_code == 200:
            return resp.json().get("message", "")
        return "Не удалось получить подсказку"
    except Exception as e:
        return f"Ошибка: {e}"


def show_adaptive_tasks(user_id: str):
    """
    Показывает адаптивные задания
    """
    st.header("🎯 Адаптивное обучение")
    
    # Выбор темы
    topic = st.selectbox(
        "Выберите тему:",
        ["general", "addition", "subtraction", "multiplication", "division", "mixed"],
        format_func=lambda x: {
            "general": "Общие задания",
            "addition": "Сложение",
            "subtraction": "Вычитание", 
            "multiplication": "Умножение",
            "division": "Деление",
            "mixed": "Смешанные операции"
        }[x]
    )
    
    if st.button("Сгенерировать персонализированные задания"):
        with st.spinner("ИИ генерирует задания специально для вас..."):
            tasks = generate_personalized_tasks(user_id, topic, count=3)
        
        if tasks:
            st.success(f"Сгенерировано {len(tasks)} заданий!")
            
            for idx, task in enumerate(tasks):
                with st.expander(f"Задание {idx + 1}: {task['question']}"):
                    st.write(f"**Сложность:** {task.get('difficulty', 'intermediate')}")
                    st.write(f"**Категория:** {task.get('category', 'general')}")
                    
                    # Подсказка
                    hint_area_key = f"hint_area_{task['id']}"
                    if st.button("💡 Подсказка", key=f"hint_btn_{task['id']}"):
                        hint_text = request_hint(task_text=task['question'])
                        st.session_state[hint_area_key] = hint_text
                    if hint_area_key in st.session_state and st.session_state[hint_area_key]:
                        st.info(f"💡 Подсказка: {st.session_state[hint_area_key]}")
                    
                    user_answer = st.number_input(
                        "Ваш ответ:",
                        key=f"answer_{task['id']}",
                        value=0,
                        step=1
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Отправить ответ", key=f"submit_{task['id']}"):
                            result = submit_task_with_ai_analysis(
                                user_id=user_id,
                                task_id=task['id'],
                                question=task['question'],
                                user_answer=user_answer,
                                correct_answer=task['correct_answer']
                            )
                            
                            if result:
                                if result.get('is_correct'):
                                    st.success("✅ Правильно! Отлично!")
                                else:
                                    st.error("❌ Неправильно")
                                
                                # Показываем сообщение от наставника
                                mentor_msg = result.get('mentor_message', {})
                                if mentor_msg.get('message'):
                                    st.info(f"💬 {mentor_msg['message']}")
                                
                                # Показываем анализ ошибки
                                error_analysis = result.get('error_analysis')
                                if error_analysis and not result.get('is_correct'):
                                    with st.expander("📊 Анализ ошибки"):
                                        st.write(f"**Тип ошибки:** {error_analysis.get('error_type', 'unknown')}")
                                        st.write(f"**Объяснение:** {error_analysis.get('justification', '')}")
                                        st.write(f"**Рекомендация:** {error_analysis.get('suggested_remediation', '')}")
                                
                                # Сохраняем результат в сессии
                                if 'task_results' not in st.session_state:
                                    st.session_state.task_results = []
                                st.session_state.task_results.append({
                                    'task_id': task['id'],
                                    'question': task['question'],
                                    'user_answer': user_answer,
                                    'correct_answer': task['correct_answer'],
                                    'is_correct': result.get('is_correct'),
                                    'mentor_message': mentor_msg.get('message', ''),
                                    'error_analysis': error_analysis
                                })
                                
                                st.success("📤 Ответ отправлен и сохранен!")
                    
                    with col2:
                        if st.button(f"Показать ответ", key=f"show_{task['id']}"):
                            st.write(f"Правильный ответ: **{task['correct_answer']}**")
        else:
            st.warning("Не удалось сгенерировать задания")
    
    # Показываем историю ответов
    if 'task_results' in st.session_state and st.session_state.task_results:
        st.subheader("📋 История ваших ответов")
        for i, result in enumerate(st.session_state.task_results[-5:]):  # Последние 5
            status = "✅" if result['is_correct'] else "❌"
            st.write(f"{status} **{result['question']}** → Ваш ответ: {result['user_answer']}, Правильный: {result['correct_answer']}")
            if result['mentor_message']:
                st.caption(f"💬 {result['mentor_message']}")


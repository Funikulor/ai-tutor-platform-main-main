"""
Интерфейс учителя с назначением заданий и аналитикой
"""
import streamlit as st
import requests
from components.student_selector import show_student_selector, show_student_multiselect
import pandas as pd


def show_teacher_dashboard():
    """
    Показывает дашборд учителя
    """
    st.header("👨‍🏫 Панель учителя")
    
    # Получение отчета
    report_type = st.selectbox(
        "Тип отчета:",
        ["summary", "detailed", "struggling"]
    )
    
    if st.button("Обновить отчет"):
        try:
            session = requests.Session()
            session.trust_env = False  # Отключаем прокси
            
            response = session.get(
                f"http://127.0.0.1:8000/agents/teacher-report",
                params={"report_type": report_type}
            )
            
            if response.status_code == 200:
                report = response.json()
                display_teacher_report(report, report_type)
            else:
                st.error(f"Ошибка загрузки отчета: {response.status_code}")
        
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")


def display_teacher_report(report: dict, report_type: str):
    """
    Отображает отчет учителя
    """
    if 'error' in report:
        st.warning(f"Нет данных: {report['error']}")
        return
    
    if report_type == "summary":
        show_summary_report(report)
    elif report_type == "detailed":
        show_detailed_report(report)
    elif report_type == "struggling":
        show_struggling_students(report)


def show_summary_report(report: dict):
    """
    Показывает сводный отчет
    """
    stats = report.get('class_statistics', {})
    
    st.subheader("📊 Статистика класса")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего учеников", stats.get('total_students', 0))
    
    with col2:
        st.metric("Выполнено заданий", stats.get('total_tasks_completed', 0))
    
    with col3:
        st.metric("Средняя точность", f"{stats.get('average_accuracy', 0):.1f}%")
    
    # Распределение уровней
    level_dist = stats.get('level_distribution', {})
    if level_dist:
        st.subheader("📈 Распределение по уровням")
        level_df = pd.DataFrame([
            {"Уровень": f"Level {k}", "Количество": v}
            for k, v in level_dist.items()
        ])
        st.bar_chart(level_df.set_index('Уровень'))
    
    # Типичные вызовы
    common_challenges = report.get('common_challenges', {})
    if common_challenges:
        st.subheader("⚠️ Частые ошибки в классе")
        challenge_df = pd.DataFrame([
            {"Тип ошибки": k, "Количество": v}
            for k, v in common_challenges.items()
        ])
        st.bar_chart(challenge_df.set_index('Тип ошибки'))
    
    # Рекомендации
    recommendations = report.get('recommendations', [])
    if recommendations:
        st.subheader("💡 Рекомендации")
        for rec in recommendations:
            priority_color = "🔥" if rec.get('priority') == 'high' else "📌"
            st.write(f"{priority_color} **{rec.get('topic')}**")
            st.write(f"   → {rec.get('action')}")


def show_detailed_report(report: dict):
    """
    Показывает детальный отчет
    """
    # Показываем сводку
    show_summary_report(report)
    
    # Индивидуальные профили
    individual_profiles = report.get('individual_profiles', [])
    if individual_profiles:
        st.subheader("👥 Индивидуальные профили")
        
        # Таблица профилей
        profile_data = []
        for profile in individual_profiles:
            profile_data.append({
                "ID": profile['user_id'],
                "Точность": f"{profile['accuracy_rate']:.1f}%",
                "Заданий": profile['total_tasks'],
                "Уровень": profile['level'],
                "Очки": profile['points'],
                "Достижений": len(profile['achievements'])
            })
        
        df = pd.DataFrame(profile_data)
        st.dataframe(df, use_container_width=True)


def show_struggling_students(report: dict):
    """
    Показывает отстающих учеников
    """
    struggling_count = report.get('struggling_count', 0)
    st.subheader(f"⚠️ Отстающие ученики: {struggling_count}")
    
    students = report.get('students', [])
    if students:
        for student in students:
            with st.expander(f"Ученик {student['user_id']} - Точность: {student['accuracy_rate']:.1f}%"):
                st.write("**Типичные ошибки:**")
                for error_type, count in student.get('most_common_errors', {}).items():
                    st.write(f"• {error_type}: {count} раз")
                
                st.write("**Рекомендации:**")
                for rec in student.get('recommendations', []):
                    st.write(f"• {rec}")
    
    # Предложения по вмешательству
    interventions = report.get('intervention_suggestions', [])
    if interventions:
        st.subheader("🎯 Предложения по поддержке")
        for intervention in interventions:
            st.write(f"**{intervention.get('type', 'support')}:**")
            st.write(f"   {intervention.get('description', '')}")


def assign_tasks_to_student():
    """
    Функция назначения заданий ученику
    """
    st.subheader("📝 Назначение заданий")
    
    # Выбор ученика через селектор
    student_id = show_student_selector("Выберите ученика:", "assign_student")
    
    if not student_id:
        st.warning("Выберите ученика из списка")
        return
    
    topic = st.selectbox(
        "Тема:",
        ["addition", "subtraction", "multiplication", "division", "mixed"],
        format_func=lambda x: {
            "addition": "Сложение",
            "subtraction": "Вычитание",
            "multiplication": "Умножение",
            "division": "Деление",
            "mixed": "Смешанные операции"
        }[x]
    )
    
    # Список доступных задач
    try:
        session = requests.Session()
        session.trust_env = False  # Отключаем прокси
        
        response = session.get(f"http://127.0.0.1:8000/tasks")
        if response.status_code == 200:
            all_tasks = response.json()
            
            topic_tasks = [t for t in all_tasks if topic in t.get('category', '').lower()]
            
            selected_tasks = st.multiselect(
                "Выберите задания:",
                options=[f"ID: {t['id']} - {t['question']}" for t in topic_tasks],
                key="task_selector"
            )
            
            with st.expander("📚 Загрузить учебный материал (текст)"):
                doc_title = st.text_input("Название материала:", key="doc_title")
                doc_text = st.text_area("Текст учебника/материала:", key="doc_text", height=150)
                if st.button("Загрузить в ассистента", key="upload_doc_btn"):
                    if doc_title and doc_text.strip():
                        try:
                            up_resp = session.post(
                                "http://127.0.0.1:8000/assistant/documents/upload",
                                json={"title": doc_title, "content": doc_text}
                            )
                            if up_resp.status_code == 200:
                                st.success("Материал загружен и будет учитываться ассистентом")
                            else:
                                st.error("Не удалось загрузить материал")
                        except Exception as e:
                            st.error(f"Ошибка загрузки: {e}")
                    else:
                        st.warning("Заполните название и текст")
            
            deadline = st.text_input("Дедлайн (необязательно):", placeholder="например, 2025-11-10")
            
            if st.button("Назначить задания"):
                # Извлекаем ID задач
                task_ids = []
                for sel in selected_tasks:
                    task_id = int(sel.split(' - ')[0].split(': ')[1])
                    task_ids.append(task_id)
                
                try:
                    # 1) Отправляем назначение
                    session = requests.Session()
                    session.trust_env = False
                    assign_resp = session.post(
                        "http://127.0.0.1:8000/agents/assign-tasks",
                        json={
                            "user_id": student_id,
                            "topic": topic,
                            "task_ids": task_ids
                        }
                    )
                    
                    if assign_resp.status_code == 200:
                        st.success(f"Задания назначены выбранному ученику!")
                        
                        # 2) Запрашиваем короткое мотивационное сообщение
                        try:
                            mot_resp = session.post(
                                "http://127.0.0.1:8000/assistant/motivation",
                                json={
                                    "topic": topic,
                                    "student_name": student_id,
                                    "deadline": deadline or None,
                                }
                            )
                            if mot_resp.status_code == 200:
                                st.info(f"💬 Сообщение для ученика: {mot_resp.json().get('message', '')}")
                            else:
                                st.caption("Не удалось сгенерировать мотивационное сообщение")
                        except Exception:
                            st.caption("Не удалось сгенерировать мотивационное сообщение")
                    else:
                        st.error("Ошибка назначения заданий")
                
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
    
    except Exception as e:
        st.error(f"Ошибка загрузки заданий: {str(e)}")


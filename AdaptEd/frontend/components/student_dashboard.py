"""
Компонент дашборда ученика с мотивацией и прогрессом
"""
import streamlit as st
import requests

def show_student_dashboard(user_id: str):
    """
    Отображает личный кабинет ученика
    """
    try:
        session = requests.Session()
        session.trust_env = False  # Отключаем прокси
        
        response = session.get(f"http://127.0.0.1:8000/agents/dashboard/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            profile = data.get('profile', {})
            
            st.header("🎓 Личный кабинет")
            
            # Основная статистика
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Точность", f"{profile.get('accuracy_rate', 0):.1f}%")
            
            with col2:
                st.metric("✅ Заданий выполнено", profile.get('total_tasks_completed', 0))
            
            with col3:
                st.metric("⭐ Уровень", profile.get('level', 1))
            
            with col4:
                st.metric("🏆 Очки", profile.get('points', 0))
            
            # Система мотивации
            st.subheader("🏅 Достижения")
            achievements = profile.get('achievements', [])
            if achievements:
                for achievement in achievements:
                    st.success(f"✅ {achievement}")
            else:
                st.info("Продолжай учиться, чтобы получить достижения!")
            
            # Сообщение от наставника
            mentor_message = data.get('mentor_message', {})
            if mentor_message.get('message'):
                st.subheader("💬 Сообщение от наставника")
                message_type = mentor_message.get('tone', 'neutral')
                
                if message_type == 'celebratory':
                    st.success(f"✨ {mentor_message['message']}")
                elif message_type == 'encouraging':
                    st.info(f"💙 {mentor_message['message']}")
                else:
                    st.write(f"{mentor_message['message']}")
                
                # Предложения помощи
                suggestions = mentor_message.get('suggestions', [])
                if suggestions:
                    st.subheader("💡 Рекомендации")
                    for suggestion in suggestions[:3]:
                        st.write(f"• **{suggestion.get('title')}**: {suggestion.get('description')}")
            
            # Анализ ошибок
            error_patterns = data.get('error_patterns', {})
            if error_patterns:
                st.subheader("📈 Типичные ошибки")
                import pandas as pd
                
                error_df = pd.DataFrame([
                    {"Тип ошибки": k, "Количество": v}
                    for k, v in error_patterns.items()
                ])
                st.bar_chart(error_df.set_index('Тип ошибки'))
            
            # Недавние задания
            recent_tasks = data.get('recent_tasks', [])
            if recent_tasks:
                st.subheader("📝 Последние задания")
                
                # Показываем последние 5 задач
                for task in recent_tasks[-5:]:
                    status = "✅" if task.get('is_correct') else "❌"
                    st.write(f"{status} {task.get('question')} (Ответ: {task.get('user_answer')})")
            
        else:
            st.error("Ошибка загрузки данных")
    
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Не удалось подключиться к серверу. Убедитесь, что backend запущен.")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")


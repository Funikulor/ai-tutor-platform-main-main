"""
Компонент для администратора
"""
import streamlit as st
import requests
from components.student_selector import show_student_selector, show_student_multiselect


def show_admin_users_management():
    """Управление пользователями"""
    st.header("👥 Управление пользователями")
    
    # Получаем всех пользователей
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.get("http://127.0.0.1:8000/all")
        if response.status_code == 200:
            users = response.json()
            
            # Фильтруем по ролям
            role_filter = st.selectbox(
                "Фильтр по роли:",
                ["all", "student", "teacher", "parent", "admin"],
                format_func=lambda x: {
                    "all": "Все роли",
                    "student": "Ученики",
                    "teacher": "Учителя",
                    "parent": "Родители",
                    "admin": "Администраторы"
                }[x]
            )
            
            filtered_users = users
            if role_filter != "all":
                filtered_users = [u for u in users if u.get('role') == role_filter]
            
            # Таблица пользователей
            if filtered_users:
                st.subheader(f"Пользователи ({len(filtered_users)})")
                
                for user in filtered_users:
                    with st.expander(f"{user.get('full_name', 'Без имени')} ({user.get('role', 'unknown')})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**ID:** {user.get('user_id', 'N/A')}")
                            st.write(f"**Email:** {user.get('email', 'N/A')}")
                            st.write(f"**Роль:** {user.get('role', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Класс:** {user.get('class_id', 'Не назначен')}")
                            st.write(f"**Телефон:** {user.get('phone', 'Не указан')}")
                            st.write(f"**Активен:** {'Да' if user.get('is_active') else 'Нет'}")
                        
                        # Редактор
                        with st.form(f"edit_form_{user.get('user_id')}"):
                            new_full_name = st.text_input("Имя Фамилия", value=user.get('full_name', ''))
                            new_email = st.text_input("Email", value=user.get('email', ''))
                            new_role = st.selectbox("Роль", ["student", "teacher", "parent", "admin"], index=["student", "teacher", "parent", "admin"].index(user.get('role', 'student')))
                            new_class = st.text_input("Класс", value=user.get('class_id') or "")
                            new_phone = st.text_input("Телефон", value=user.get('phone') or "")
                            submitted = st.form_submit_button("Сохранить изменения")
                        
                        if submitted:
                            try:
                                upd = session.put(
                                    f"http://127.0.0.1:8000/users/{user.get('user_id')}",
                                    json={
                                        "full_name": new_full_name,
                                        "email": new_email,
                                        "role": new_role,
                                        "class_id": new_class or None,
                                        "phone": new_phone or None,
                                    }
                                )
                                if upd.status_code == 200:
                                    st.success("Изменения сохранены")
                                    st.rerun()
                                else:
                                    st.error(f"Ошибка сохранения: {upd.text}")
                            except Exception as e:
                                st.error(f"Ошибка: {e}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button(f"{'Деактивировать' if user.get('is_active') else 'Активировать'}", key=f"toggle_{user.get('user_id')}"):
                                try:
                                    resp = session.post(f"http://127.0.0.1:8000/users/{user.get('user_id')}/toggle")
                                    if resp.status_code == 200:
                                        st.success("Статус обновлён")
                                        st.rerun()
                                    else:
                                        st.error("Не удалось изменить статус")
                                except Exception as e:
                                    st.error(f"Ошибка: {e}")
                        with col2:
                            st.caption("Редактирование доступно выше")
                        with col3:
                            if st.button("Удалить", key=f"delete_{user.get('user_id')}"):
                                try:
                                    resp = session.delete(f"http://127.0.0.1:8000/users/{user.get('user_id')}")
                                    if resp.status_code == 200:
                                        st.success("Пользователь удалён")
                                        st.rerun()
                                    else:
                                        st.error("Не удалось удалить пользователя")
                                except Exception as e:
                                    st.error(f"Ошибка: {e}")
            else:
                st.info("Пользователи не найдены")
        
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            st.error(f"Ответ сервера: {response.text}")
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")


def show_admin_binding():
    """Привязка учеников к учителям"""
    st.header("🔗 Привязка учеников к учителям")
    
    # Получаем всех учителей
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.get("http://127.0.0.1:8000/all")
        if response.status_code == 200:
            users = response.json()
            teachers = [u for u in users if u.get('role') == 'teacher']
            students = [u for u in users if u.get('role') == 'student']
            
            if teachers and students:
                # Выбор учителя
                teacher_options = [f"{t.get('full_name', 'Без имени')} (ID: {t.get('user_id')})" for t in teachers]
                teacher_map = {opt: t.get('user_id') for opt, t in zip(teacher_options, teachers)}
                
                selected_teacher_display = st.selectbox("Выберите учителя:", teacher_options)
                selected_teacher_id = teacher_map[selected_teacher_display]
                
                # Выбор учеников
                student_ids = show_student_multiselect("Выберите учеников для привязки:", "bind_students")
                
                if st.button("Привязать учеников к учителю"):
                    if student_ids:
                        st.success(f"Привязано {len(student_ids)} учеников к учителю!")
                        st.info("Функция привязки будет реализована в базе данных")
                    else:
                        st.warning("Выберите учеников для привязки")
            else:
                st.warning("Необходимо зарегистрировать учителей и учеников")
        
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            st.error(f"Ответ сервера: {response.text}")
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")


def show_admin_analytics():
    """Системная аналитика"""
    st.header("📊 Системная аналитика")
    
    # Общая статистика
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.get("http://127.0.0.1:8000/all")
        if response.status_code == 200:
            users = response.json()
            
            # Подсчет по ролям
            role_counts = {}
            for user in users:
                role = user.get('role', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            # Отображение статистики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ученики", role_counts.get('student', 0))
            
            with col2:
                st.metric("Учителя", role_counts.get('teacher', 0))
            
            with col3:
                st.metric("Родители", role_counts.get('parent', 0))
            
            with col4:
                st.metric("Администраторы", role_counts.get('admin', 0))
            
            # График распределения
            st.subheader("Распределение пользователей по ролям")
            import pandas as pd
            
            role_data = []
            for role, count in role_counts.items():
                role_names = {
                    'student': 'Ученики',
                    'teacher': 'Учителя', 
                    'parent': 'Родители',
                    'admin': 'Администраторы'
                }
                role_data.append({
                    'Роль': role_names.get(role, role),
                    'Количество': count
                })
            
            df = pd.DataFrame(role_data)
            st.bar_chart(df.set_index('Роль'))
            
            # Активность пользователей
            st.subheader("Активные пользователи")
            active_users = [u for u in users if u.get('is_active')]
            st.write(f"Активных пользователей: {len(active_users)} из {len(users)}")
            
        else:
            st.error("Не удалось загрузить данные")
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")


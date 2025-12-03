"""
AdaptEd - AI-Powered Adaptive Learning Platform
С версией с многоагентной архитектурой и авторизацией
"""
import streamlit as st
import requests
from components.auth import init_session, show_login_page, show_register_page, logout
from components.student_dashboard import show_student_dashboard
from components.teacher_interface import show_teacher_dashboard, assign_tasks_to_student
from components.admin_interface import show_admin_users_management, show_admin_binding, show_admin_analytics
from components.assistant import assistant_chat_ui
from components.homework import show_homework_submission, show_test_interface, show_statistics

# Отключаем прокси для локальных запросов
session = requests.Session()
session.trust_env = False

# Инициализация сессии
init_session()

# Streamlit frontend setup
def main():
    st.set_page_config(
        page_title="AdaptEd - AI-Powered Adaptive Learning",
        page_icon="🎓",
        layout="wide"
    )
    
    # Проверка авторизации
    if not st.session_state.is_authenticated:
        # Страница входа или регистрации
        if 'page' not in st.session_state:
            st.session_state.page = "login"
        
        if st.session_state.page == "login":
            show_login_page()
        elif st.session_state.page == "register":
            show_register_page()
        return
    
    # Если пользователь авторизован
    user_info = st.session_state.user
    role = st.session_state.role
    
    st.title("🎓 AdaptEd - AI-Powered Adaptive Learning Platform")
    st.markdown("*Персонализированное обучение с ИИ-агентами*")
    
    # Информация о пользователе в сайдбаре
    st.sidebar.title(f"👤 {user_info.get('full_name', 'Пользователь')}")
    st.sidebar.write(f"**Роль:** {role.title()}")
    st.sidebar.write(f"**ID:** {st.session_state.user_id}")
    
    if st.sidebar.button("🚪 Выход"):
        logout()
        st.rerun()
    
    # Боковое меню в зависимости от роли
    if role == "student":
        menu_items = [
            "🏠 Главная",
            "👤 Личный кабинет",
            "🤖 Помощник",
            "📝 Домашние задания",
            "📋 Тесты",
            "📊 Статистика"
        ]
    elif role == "teacher":
        menu_items = [
            "🏠 Главная",
            "📊 Панель учителя",
            "⚙️ Назначение заданий",
            "👥 Ученики"
        ]
    elif role == "parent":
        menu_items = [
            "🏠 Главная",
            "👨‍👩‍👧 Мои дети",
            "📈 Прогресс",
            "💬 Взаимодействие"
        ]
    else:
        menu_items = [
            "🏠 Главная"
        ]
    
    # Навигация через кнопки-ссылки
    st.sidebar.markdown("### 📚 Навигация")
    
    if role == "student":
        if st.sidebar.button("🏠 Главная", key="nav_home"):
            st.session_state.current_page = "home"
        if st.sidebar.button("👤 Личный кабинет", key="nav_dashboard"):
            st.session_state.current_page = "dashboard"
        if st.sidebar.button("🤖 Помощник", key="nav_assistant"):
            st.session_state.current_page = "assistant"
        if st.sidebar.button("📝 Домашние задания", key="nav_homework"):
            st.session_state.current_page = "homework"
        if st.sidebar.button("📋 Тесты", key="nav_tests"):
            st.session_state.current_page = "tests"
        if st.sidebar.button("📊 Статистика", key="nav_statistics"):
            st.session_state.current_page = "statistics"
    
    elif role == "teacher":
        if st.sidebar.button("🏠 Главная", key="nav_home"):
            st.session_state.current_page = "home"
        if st.sidebar.button("📊 Панель учителя", key="nav_teacher"):
            st.session_state.current_page = "teacher"
        if st.sidebar.button("⚙️ Назначение заданий", key="nav_assign"):
            st.session_state.current_page = "assign"
        if st.sidebar.button("👥 Ученики", key="nav_students"):
            st.session_state.current_page = "students"
    
    elif role == "parent":
        if st.sidebar.button("🏠 Главная", key="nav_home"):
            st.session_state.current_page = "home"
        if st.sidebar.button("👨‍👩‍👧 Мои дети", key="nav_children"):
            st.session_state.current_page = "children"
        if st.sidebar.button("📈 Прогресс", key="nav_progress"):
            st.session_state.current_page = "progress"
        if st.sidebar.button("💬 Взаимодействие", key="nav_chat"):
            st.session_state.current_page = "chat"
    
    elif role == "admin":
        if st.sidebar.button("🏠 Главная", key="nav_home"):
            st.session_state.current_page = "home"
        if st.sidebar.button("👥 Управление пользователями", key="nav_users"):
            st.session_state.current_page = "users"
        if st.sidebar.button("🔗 Привязка учеников", key="nav_bind"):
            st.session_state.current_page = "bind"
        if st.sidebar.button("📊 Системная аналитика", key="nav_analytics"):
            st.session_state.current_page = "analytics"
    
    # Определяем текущую страницу
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    page = st.session_state.current_page
    
    # Главная страница
    if page == "home":
        st.header(f"Добро пожаловать, {user_info.get('full_name', 'Пользователь')}!")
        
        if role == "student":
            st.markdown(
                """
                ### 🎓 Вы ученик!
                
                Используйте следующие возможности:
                - **Личный кабинет** - просмотрите свой прогресс, баллы и достижения
                - **Помощник** - общайтесь с ИИ и получайте подсказки
                - **Мои задания** - просмотрите назначенные задания
                """
            )
        elif role == "teacher":
            st.markdown(
                """
                ### 👨‍🏫 Вы учитель!
                
                Используйте следующие возможности:
                - **Панель учителя** - аналитика и отчеты по классу
                - **Назначение заданий** - дайте задания ученикам
                - **Ученики** - просмотр индивидуальных профилей
                """
            )
        elif role == "parent":
            st.markdown(
                """
                ### 👨‍👩‍👧 Вы родитель!
                
                Используйте следующие возможности:
                - **Мои дети** - управление профилями детей
                - **Прогресс** - отслеживание успеваемости
                - **Взаимодействие** - связь с учителями
                """
            )
        
        elif role == "admin":
            st.markdown(
                """
                ### 👨‍💼 Вы администратор!
                
                Используйте следующие возможности:
                - **Управление пользователями** - просмотр и управление всеми пользователями
                - **Привязка учеников** - привязка учеников к учителям
                - **Системная аналитика** - общая статистика системы
                """
            )
    
    # Меню для ученика
    elif role == "student":
        if page == "dashboard":
            show_student_dashboard(st.session_state.user_id)
        
        elif page == "assistant":
            assistant_chat_ui()
        
        elif page == "homework":
            show_homework_submission()
        
        elif page == "tests":
            show_test_interface()
        
        elif page == "statistics":
            show_statistics()
        
        elif page == "tasks":
            st.header("📝 Мои задания")
            st.info("Здесь будут отображаться назначенные вам задания")
    
    # Меню для учителя
    elif role == "teacher":
        if page == "teacher":
            show_teacher_dashboard()
        
        elif page == "assign":
            assign_tasks_to_student()
        
        elif page == "students":
            st.header("👥 Ученики класса")
            st.info("Здесь будет список учеников класса")
    
    # Меню для родителя
    elif role == "parent":
        if page == "children":
            st.header("👨‍👩‍👧 Мои дети")
            st.info("Здесь будет список ваших детей")
        
        elif page == "progress":
            st.header("📈 Прогресс детей")
            st.info("Здесь будет информация о прогрессе")
        
        elif page == "chat":
            st.header("💬 Взаимодействие с учителями")
            st.info("Здесь будет общение с учителями")
    
    # Меню для админа
    elif role == "admin":
        if page == "users":
            show_admin_users_management()
        
        elif page == "bind":
            show_admin_binding()
        
        elif page == "analytics":
            show_admin_analytics()


if __name__ == "__main__":
    main()

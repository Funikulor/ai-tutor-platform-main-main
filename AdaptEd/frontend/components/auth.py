"""
Компоненты авторизации и регистрации
"""
import streamlit as st
import requests
from typing import Optional, Dict


def init_session():
    """Инициализация сессии"""
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False


def register(email: str, password: str, full_name: str, role: str, 
             class_id: Optional[str] = None, phone: Optional[str] = None) -> Optional[Dict]:
    """
    Регистрация пользователя
    
    roles: student, teacher, parent
    """
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.post(
            "http://127.0.0.1:8000/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
                "class_id": class_id,
                "phone": phone
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка регистрации: {response.text}")
            return None
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None


def login(email: str, password: str) -> Optional[Dict]:
    """
    Вход пользователя
    """
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.post(
            "http://127.0.0.1:8000/auth/login",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            st.error(f"Неверный email или пароль")
            return None
    
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
        return None


def get_current_user(token: str) -> Optional[Dict]:
    """Получение информации о текущем пользователе"""
    try:
        session = requests.Session()
        session.trust_env = False
        
        headers = {"Authorization": f"Bearer {token}"}
        response = session.get(
            "http://127.0.0.1:8000/auth/me",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    except Exception as e:
        return None


def logout():
    """Выход пользователя"""
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.is_authenticated = False


def show_login_page():
    """Отображает страницу входа"""
    st.header("🔐 Вход в систему")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Уже зарегистрированы?")
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email:", key="login_email")
            password = st.text_input("Пароль:", type="password", key="login_password")
            submitted = st.form_submit_button("Войти")
        if submitted:
            result = login(email, password)
            if result:
                st.session_state.token = result["access_token"]
                st.session_state.user_id = result["user_id"]
                st.session_state.role = result["role"]
                st.session_state.is_authenticated = True
                # Получаем полную информацию о пользователе
                user_info = get_current_user(result["access_token"])
                if user_info:
                    st.session_state.user = user_info
                st.rerun()
    
    with col2:
        st.subheader("Новый пользователь?")
        st.write("Создайте аккаунт")
        
        if st.button("Зарегистрироваться", key="go_to_register"):
            st.session_state.page = "register"
            st.rerun()


def show_register_page():
    """Отображает страницу регистрации"""
    st.header("📝 Регистрация")
    
    st.info("Выберите свою роль и заполните форму")
    
    role = st.selectbox(
        "Выберите роль:",
        ["student", "teacher", "parent"],
        format_func=lambda x: {
            "student": "👨‍🎓 Ученик",
            "teacher": "👨‍🏫 Учитель",
            "parent": "👨‍👩‍👧 Родитель"
        }[x]
    )
    
    # Обязательные поля
    first_name = st.text_input("Имя:")
    surname = st.text_input("Фамилия:")
    email = st.text_input("Email:")
    password = st.text_input("Пароль:", type="password")
    
    # Дополнительные поля
    col1, col2 = st.columns(2)
    
    with col1:
        phone = st.text_input("Телефон (необязательно):")
    
    with col2:
        if role == "student":
            class_id = st.text_input("Класс:")
        else:
            class_id = None
    
    if st.button("Зарегистрироваться", key="register_btn"):
        # Проверяем, что все обязательные поля заполнены
        required_fields = [first_name, surname, email, password]
        if not all(required_fields) or not all(field.strip() for field in required_fields if field):
            st.error("Заполните все обязательные поля")
        else:
            full_name = f"{first_name} {surname}"
            result = register(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                class_id=class_id if role == "student" else None,
                phone=phone
            )
            
            if result:
                st.session_state.page = "login"
                st.rerun()
    
    if st.button("Назад к входу", key="back_to_login"):
        st.session_state.page = "login"
        st.rerun()


"""
Компонент для выбора учеников
"""
import streamlit as st
import requests
from typing import List, Dict


def get_all_students() -> List[Dict]:
    """Получает список всех учеников"""
    try:
        session = requests.Session()
        session.trust_env = False
        
        response = session.get("http://127.0.0.1:8000/users/all")
        if response.status_code == 200:
            users = response.json()
            # Фильтруем только учеников
            students = [user for user in users if user.get('role') == 'student']
            return students
        else:
            st.error(f"Ошибка сервера: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Ошибка загрузки учеников: {str(e)}")
        return []


def show_student_selector(label: str = "Выберите ученика:", key: str = "student_selector") -> str:
    """
    Показывает селектор учеников
    
    Returns:
        user_id выбранного ученика или None
    """
    students = get_all_students()
    
    if not students:
        st.warning("Ученики не найдены")
        return None
    
    # Создаем список для отображения
    student_options = []
    student_map = {}
    
    for student in students:
        display_name = f"{student.get('full_name', 'Без имени')} (ID: {student.get('user_id', 'N/A')})"
        student_options.append(display_name)
        student_map[display_name] = student.get('user_id')
    
    # Селектор без возможности редактирования
    selected_display = st.selectbox(
        label,
        options=student_options,
        key=key,
        disabled=False  # Можно выбрать, но нельзя редактировать
    )
    
    if selected_display:
        return student_map[selected_display]
    
    return None


def show_student_multiselect(label: str = "Выберите учеников:", key: str = "student_multiselect") -> List[str]:
    """
    Показывает мультиселектор учеников
    
    Returns:
        список user_id выбранных учеников
    """
    students = get_all_students()
    
    if not students:
        st.warning("Ученики не найдены")
        return []
    
    # Создаем список для отображения
    student_options = []
    student_map = {}
    
    for student in students:
        display_name = f"{student.get('full_name', 'Без имени')} (ID: {student.get('user_id', 'N/A')})"
        student_options.append(display_name)
        student_map[display_name] = student.get('user_id')
    
    # Мультиселектор
    selected_displays = st.multiselect(
        label,
        options=student_options,
        key=key,
        default=[]
    )
    
    selected_ids = []
    for display in selected_displays:
        if display in student_map:
            selected_ids.append(student_map[display])
    
    return selected_ids


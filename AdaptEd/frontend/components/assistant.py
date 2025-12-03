"""
Компонент ассистента с чатом, анимированным аватаром и подсказками
"""
import streamlit as st
import requests
from typing import List, Dict
import time


def _client():
	session = requests.Session()
	session.trust_env = False
	return session


def _render_animated_avatar():
	"""Рендерит анимированный аватар чата"""
	# Используем HTML/CSS для анимации
	avatar_html = """
	<div style="text-align: center; margin: 20px 0;">
		<div id="avatar-container" style="display: inline-block;">
			<svg width="120" height="120" viewBox="0 0 120 120">
				<!-- Голова -->
				<circle cx="60" cy="50" r="35" fill="#FFD700" stroke="#FFA500" stroke-width="2"/>
				<!-- Глаза -->
				<circle cx="50" cy="45" r="5" fill="#000" id="eye-left">
					<animate attributeName="cy" values="45;47;45" dur="2s" repeatCount="indefinite"/>
				</circle>
				<circle cx="70" cy="45" r="5" fill="#000" id="eye-right">
					<animate attributeName="cy" values="45;47;45" dur="2s" repeatCount="indefinite"/>
				</circle>
				<!-- Улыбка -->
				<path d="M 40 60 Q 60 70 80 60" stroke="#000" stroke-width="3" fill="none" id="smile">
					<animate attributeName="d" values="M 40 60 Q 60 70 80 60;M 40 62 Q 60 72 80 62;M 40 60 Q 60 70 80 60" dur="3s" repeatCount="indefinite"/>
				</path>
				<!-- Тело -->
				<rect x="40" y="85" width="40" height="30" rx="10" fill="#4A90E2" stroke="#2E5C8A" stroke-width="2"/>
			</svg>
		</div>
		<p style="margin-top: 10px; font-weight: bold; color: #4A90E2;">🤖 ИИ-Помощник</p>
	</div>
	"""
	st.markdown(avatar_html, unsafe_allow_html=True)


def assistant_chat_ui():
	"""Интерфейс чата с анимированным аватаром"""
	user_id = st.session_state.get("user_id", "")
	
	st.header("💬 Чат с ИИ-Помощником")
	
	# Анимированный аватар
	col1, col2, col3 = st.columns([1, 2, 1])
	with col2:
		_render_animated_avatar()
	
	if "assistant_history" not in st.session_state:
		st.session_state.assistant_history = []  # list of {role, content}
	
	# Отображение истории чата
	chat_container = st.container()
	with chat_container:
		for i, msg in enumerate(st.session_state.assistant_history):
			if msg["role"] == "user":
				with st.chat_message("user"):
					st.write(msg['content'])
			else:
				with st.chat_message("assistant"):
					st.write(msg['content'])
	
	# Показываем информацию о личности если есть
	if st.session_state.assistant_history and user_id:
		with st.expander("📊 Информация о вашем профиле"):
			try:
				resp = _client().get(f"http://127.0.0.1:8000/statistics/{user_id}")
				if resp.status_code == 200:
					data = resp.json()
					weaknesses = data.get("weaknesses", [])
					if weaknesses:
						st.write("**Выявленные слабые места:**")
						for w in weaknesses[:3]:
							st.write(f"• {w.get('description', w.get('name', ''))}")
			except:
				pass
	
	# Ввод сообщения
	user_message = st.chat_input("Напишите ваш вопрос...")
	
	if user_message:
		# Добавляем сообщение пользователя
		st.session_state.assistant_history.append({"role": "user", "content": user_message})
		
		# Показываем индикатор загрузки
		with st.spinner("ИИ думает..."):
			try:
				resp = _client().post(
					"http://127.0.0.1:8000/assistant/chat",
					json={
						"messages": st.session_state.assistant_history,
						"mode": "general",
						"user_id": user_id if user_id else None,
					},
					timeout=60
				)
				if resp.status_code == 200:
					data = resp.json()
					answer = data.get("message", "(нет ответа)")
					st.session_state.assistant_history.append({"role": "assistant", "content": answer})
					
					# Показываем инсайты о личности если есть
					personality_insights = data.get("personality_insights")
					if personality_insights:
						with st.expander("💡 Инсайты о вашем стиле общения"):
							comm_style = personality_insights.get("communication_style", {})
							st.write(f"**Стиль:** {'Формальный' if comm_style.get('formality', 0) > 0.5 else 'Неформальный'}, "
							         f"{'Подробный' if comm_style.get('verbosity', 0) > 0.5 else 'Краткий'}")
					
					st.rerun()
				else:
					st.error(f"Ошибка ассистента: {resp.status_code}")
			except requests.exceptions.Timeout:
				st.error("⏱️ Превышено время ожидания. Попробуйте еще раз.")
			except Exception as e:
				st.error(f"Ошибка: {e}")


def request_hint(task_text: str, student_level: str = "") -> str:
	try:
		resp = _client().post(
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

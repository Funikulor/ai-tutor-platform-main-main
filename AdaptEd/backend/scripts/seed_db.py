#!/usr/bin/env python3
"""
Скрипт заполнения БД тестовыми учениками и учителями.
Запуск из корня backend: python -m scripts.seed_db
Выводит список email и паролей в консоль и в файл seed_credentials.txt
"""
import os
import sys

# Добавляем родительскую директорию в path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

# Загружаем .env до импорта app/db
env_path = os.path.join(backend_dir, '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

# Для локального сидирования без Postgres можно задать USE_SQLITE=1 в .env
if os.getenv("USE_SQLITE", "").strip() == "1":
    sqlite_path = os.path.join(backend_dir, "adapted.db")
    os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path}"
    print(f"[Seed] Используем SQLite: {sqlite_path}")

from utils.db import init_db, has_db, get_db
from utils.auth_service import auth_service
from models.auth import UserRole

# Случайные данные для учеников
STUDENT_NAMES = [
    "Иванов Алексей", "Петрова Мария", "Сидоров Дмитрий", "Козлова Анна",
    "Новиков Иван", "Морозова Елена", "Волков Павел", "Соколова Ольга",
    "Лебедев Сергей", "Кузнецова Татьяна", "Попов Николай", "Васильева Ирина",
    "Федоров Андрей", "Михайлова Наталья", "Андреев Александр", "Егорова Светлана",
]
PARENT_NAMES = [
    "Иванов Иван Петрович", "Петрова Ольга Сергеевна", "Сидоров Петр Иванович",
    "Козлова Елена Викторовна", "Новиков Дмитрий Александрович", "Морозова Анна Дмитриевна",
    "Волков Сергей Николаевич", "Соколова Мария Павловна", "Лебедев Андрей Иванович",
    "Кузнецова Татьяна Сергеевна", "Попов Николай Владимирович", "Васильева Ирина Андреевна",
    "Федоров Александр Петрович", "Михайлова Наталья Олеговна", "Андреев Павел Сергеевич",
    "Егорова Светлана Дмитриевна",
]
PHONES = [
    "+7 916 111-22-33", "+7 926 222-33-44", "+7 903 333-44-55", "+7 905 444-55-66",
    "+7 495 555-66-77", "+7 499 666-77-88", "+7 916 777-88-99", "+7 926 888-99-00",
    "+7 903 999-00-11", "+7 905 100-11-22", "+7 495 200-22-33", "+7 499 300-33-44",
    "+7 916 400-44-55", "+7 926 500-55-66", "+7 903 600-66-77", "+7 905 700-77-88",
]
CLASSES = ["10А", "10Б", "11А", "9А", "9Б"]

# Учителя
TEACHER_NAMES = [
    "Смирнова Елена Викторовна", "Кузнецов Михаил Сергеевич", "Павлова Анна Александровна",
    "Семенов Игорь Николаевич", "Голубева Ольга Дмитриевна",
]

def random_password():
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def main():
    init_db()
    if not has_db():
        print("БД недоступна. Проверьте DATABASE_URL и наличие SQLAlchemy.")
        return

    credentials = []
    base_student = 100  # чтобы не пересекаться с существующими
    base_teacher = 50

    # Ученики
    for i, name in enumerate(STUDENT_NAMES):
        email = f"student{base_student + i + 1}@adapted.local"
        password = random_password()
        class_id = CLASSES[i % len(CLASSES)]
        parent_fio = PARENT_NAMES[i % len(PARENT_NAMES)]
        parent_phone = PHONES[i % len(PHONES)]
        user = auth_service.register_user(
            email=email,
            password=password,
            full_name=name,
            role=UserRole.STUDENT,
            class_id=class_id,
            phone=PHONES[(i + 1) % len(PHONES)],
            parent_fio=parent_fio,
            parent_phone=parent_phone,
        )
        if user:
            credentials.append(("Ученик", name, email, password, class_id, f"{parent_fio}, {parent_phone}"))
            print(f"  Ученик: {email} / {password}  (класс {class_id})")

    # Учителя
    for i, name in enumerate(TEACHER_NAMES):
        email = f"teacher{base_teacher + i + 1}@adapted.local"
        password = random_password()
        user = auth_service.register_user(
            email=email,
            password=password,
            full_name=name,
            role=UserRole.TEACHER,
            class_id=None,
            phone=PHONES[(i + 5) % len(PHONES)],
        )
        if user:
            credentials.append(("Учитель", name, email, password, "-", "-"))
            print(f"  Учитель: {email} / {password}")

    # Сохраняем в файл
    out_path = os.path.join(backend_dir, "seed_credentials.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("AdaptEd — тестовые учётные записи (email / пароль)\n")
        f.write("=" * 60 + "\n\n")
        for role, name, email, password, cls, parent in credentials:
            f.write(f"{role}: {name}\n  Email: {email}\n  Пароль: {password}\n  Класс: {cls}\n  Родитель: {parent}\n\n")
    print(f"\nСписок сохранён в: {out_path}")
    return credentials

if __name__ == "__main__":
    print("Заполнение БД тестовыми пользователями...\n")
    main()

"""
Скрипт для проверки установленных зависимостей
"""
import sys
import io

# Устанавливаем UTF-8 для вывода
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

required_packages = {
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'pydantic': 'pydantic',
    'python-multipart': 'multipart',
    'python-dotenv': 'dotenv',
}

missing = []

for package_name, import_name in required_packages.items():
    try:
        __import__(import_name)
        print(f"[OK] {package_name} установлен")
    except ImportError:
        print(f"[FAIL] {package_name} НЕ установлен")
        missing.append(package_name)

if missing:
    print(f"\n[WARNING] Отсутствуют пакеты: {', '.join(missing)}")
    print("Установите их командой: pip install " + " ".join(missing))
    sys.exit(1)
else:
    print("\n[SUCCESS] Все зависимости установлены!")
    sys.exit(0)


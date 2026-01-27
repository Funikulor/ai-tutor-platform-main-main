"""
Скрипт для проверки доступности сервера
"""
import requests
import time
import sys

def check_server(url="http://127.0.0.1:8000", timeout=5, max_retries=10):
    """Проверяет доступность сервера"""
    print(f"Проверка доступности сервера: {url}")
    print(f"Таймаут: {timeout} сек, Максимум попыток: {max_retries}\n")
    
    for i in range(max_retries):
        try:
            print(f"Попытка {i+1}/{max_retries}...")
            response = requests.get(f"{url}/", timeout=timeout)
            if response.status_code == 200:
                print(f"[SUCCESS] Сервер доступен!")
                print(f"Ответ: {response.json()}")
                return True
            else:
                print(f"[WARNING] Сервер ответил с кодом {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[INFO] Сервер еще не запущен, ждем...")
            time.sleep(2)
        except requests.exceptions.Timeout:
            print(f"[ERROR] Превышено время ожидания ответа")
        except Exception as e:
            print(f"[ERROR] Ошибка: {e}")
            time.sleep(2)
    
    print(f"\n[ERROR] Сервер недоступен после {max_retries} попыток")
    print("\nПроверьте:")
    print("1. Запущен ли сервер: npm run dev")
    print("2. Правильный ли порт (8000)")
    print("3. Нет ли ошибок в логах сервера")
    return False

if __name__ == "__main__":
    success = check_server()
    sys.exit(0 if success else 1)




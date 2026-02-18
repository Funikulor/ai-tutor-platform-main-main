import sqlite3

conn = sqlite3.connect('adapted.db')
cur = conn.cursor()

# Получаем список таблиц
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]

print("Таблицы в SQLite:")
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    count = cur.fetchone()[0]
    print(f"  {table}: {count} записей")

conn.close()


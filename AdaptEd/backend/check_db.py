import sqlite3, os
path = "adapted.db"
print("exists", os.path.exists(path))
con = sqlite3.connect(path)
cur = con.cursor()
print("tables:", cur.execute("select name from sqlite_master where type='table'").fetchall())
print("tests count:", cur.execute("select count(*) from tests").fetchone())
print("questions count:", cur.execute("select count(*) from test_questions").fetchone())
print("last tests:", cur.execute("select id,title,topic,difficulty,creator_id from tests order by id desc limit 5").fetchall())

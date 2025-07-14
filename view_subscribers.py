import sqlite3

conn = sqlite3.connect("subscribers.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM subscribers")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()

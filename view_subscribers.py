import sqlite3

conn = sqlite3.connect("subscribers.db")
cursor = conn.cursor()

cursor.execute("SELECT name, email, city, office, unsubscribed FROM subscribers")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()

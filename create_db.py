import sqlite3

def create_database():
    conn = sqlite3.connect("subscribers.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        city TEXT NOT NULL,
        office TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()
    print("✅ Database created.")

if __name__ == "__main__":
    create_database()

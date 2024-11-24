import sqlite3

class Database:
    def __init__(self, db_name):
        """Bazani ulash va kerakli jadvalni yaratish."""
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """Tadbirlar uchun jadval yaratish."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            date_time TEXT NOT NULL
        )
        """)
        self.connection.commit()

    def add_event(self, user_id, name, date_time):
        """Yangi tadbir qo'shish."""
        self.cursor.execute(
            "INSERT INTO events (user_id, name, date_time) VALUES (?, ?, ?)",
            (user_id, name, date_time.strftime("%Y-%m-%d %H:%M"))
        )
        self.connection.commit()

    def get_user_events(self, user_id):
        """Foydalanuvchining barcha tadbirlarini olish."""
        self.cursor.execute(
            "SELECT id, name, date_time FROM events WHERE user_id = ? ORDER BY date_time ASC",
            (user_id,)
        )
        return self.cursor.fetchall()

    def delete_event(self, event_id):
        """Tadbirni o'chirish."""
        self.cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.connection.commit()

    def delete_all_events(self, user_id):
        """Foydalanuvchining barcha tadbirlarini o'chirish."""
        self.cursor.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
        self.connection.commit()

    def close(self):
        """Bazani yopish."""
        self.connection.close()

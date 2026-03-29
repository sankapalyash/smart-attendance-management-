import sqlite3

DATABASE = "database/database.db"


# ---------------- GET DATABASE CONNECTION ---------------- #

def get_connection():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# ---------------- INITIALIZE DATABASE ---------------- #

def init_db():

    conn = get_connection()
    cursor = conn.cursor()


    # -------- ADMIN TABLE -------- #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)


    # -------- TEACHERS TABLE -------- #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)


    # -------- STUDENTS TABLE -------- #

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT,
        name TEXT,
        username TEXT,
        password TEXT,
        mobile TEXT,
        email TEXT
    )
    """)


    # -------- DEFAULT ADMIN -------- #

    cursor.execute("SELECT * FROM admin")

    admin = cursor.fetchone()

    if not admin:

        cursor.execute(
            "INSERT INTO admin (username,password) VALUES (?,?)",
            ("admin", "admin123")
        )


    conn.commit()
    conn.close()
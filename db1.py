import sqlite3
conn=sqlite3.connect("exprac.db")
cursor=conn.cursor()
cursor.execute("""
            CREATE TABLE IF NOT EXISTS exprac
             ( id INTEGER PRIMARY KEY AUTOINCREMENT,
               title TEXT,
               amount REAL,
               category TEXT,
               user_id INTEGER,
               created_at TEXT)
""")
cursor.execute("""
              CREATE TABLE IF NOT EXISTS users
               ( id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE,
               password TEXT,
               name TEXT,
               email TEXT,
               dob TEXT,
               contact TEXT,
               profile_photo TEXT
               )
""")
try:
  cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
except:
  pass
try:
  cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
except:
  pass
try:
  cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
except:
  pass
try:
  cursor.execute("ALTER TABLE users ADD COLUMN contact TEXT")
except:
  pass
try:
  cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
except:
  pass
conn.commit()
conn.close()
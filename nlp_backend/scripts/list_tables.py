import sqlite3

db = sqlite3.connect('app.db')
c = db.cursor()

c.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = c.fetchall()

print("All tables in app.db:")
for t in tables:
    print(f"  - {t[0]}")

db.close()

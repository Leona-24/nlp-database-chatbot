
import sqlite3
import os

db_path = os.path.join('nlp_backend', 'data', 'app.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Add role column if not exists
try:
    c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'buyer'")
except sqlite3.OperationalError:
    print("Role column already exists")

# 2. Update existing and add missing users for the demo
users_data = [
    (5, 'blessy', 'chennai', 'seller'),
    (8, 'Karthik', 'Madurai', 'seller'),
    (10, 'Anu', 'Bangalore', 'seller'),
    (11, 'Priya', 'Mumbai', 'buyer')
]

for uid, name, city, role in users_data:
    c.execute("INSERT OR REPLACE INTO users (id, name, city, role) VALUES (?, ?, ?, ?)", (uid, name, city, role))

conn.commit()
conn.close()
print("✅ Database updated with roles!")

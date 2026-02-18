import sqlite3

db = sqlite3.connect('app.db')
c = db.cursor()

# 1. Ensure 'users' table has a 'name' and 'city' column (not just username)
# This is for the frontend demo data
try:
    c.execute("ALTER TABLE users ADD COLUMN name TEXT")
except: pass # already exists
try:
    c.execute("ALTER TABLE users ADD COLUMN city TEXT")
except: pass # already exists

# 2. Clear and add demo users to 'users' table
c.execute("DELETE FROM users WHERE id IN (5, 8)")
# Note: we keep the password_hash columns empty or null for these demo records
c.execute("INSERT INTO users (id, username, name, city) VALUES (5, 'blessy_user', 'blessy', 'chennai')")
c.execute("INSERT INTO users (id, username, name, city) VALUES (8, 'karthik_user', 'Karthik', 'Madurai')")

# 3. Re-create user_products with a FOREIGN KEY
c.execute("DROP TABLE IF EXISTS user_products")
c.execute("""
    CREATE TABLE user_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        no_of_items INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
""")

# 4. Add product data
c.execute("INSERT INTO user_products (user_id, product, no_of_items) VALUES (5, 'Pen', 10)")
c.execute("INSERT INTO user_products (user_id, product, no_of_items) VALUES (8, 'Pencil', 20)")

db.commit()
db.close()
print("Database updated: 'users' table enriched and 'user_products' linked via FK.")

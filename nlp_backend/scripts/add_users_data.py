import sqlite3

db = sqlite3.connect('app.db')
c = db.cursor()

# Create users_info table (separate from auth users table)
c.execute('''CREATE TABLE IF NOT EXISTS users_info (
    id INTEGER PRIMARY KEY, 
    name TEXT, 
    city TEXT
)''')

# Clear and add users
c.execute('DELETE FROM users_info')
c.execute('INSERT INTO users_info VALUES (5, "blessy", "chennai")')
c.execute('INSERT INTO users_info VALUES (8, "Karthik", "Madurai")')

db.commit()

print("=== USERS_INFO ===")
c.execute('SELECT * FROM users_info')
for row in c.fetchall():
    print(row)

print("\n=== USER_PRODUCTS ===")
c.execute('SELECT * FROM user_products')
for row in c.fetchall():
    print(row)

print("\n=== JOINED DATA (users who bought products) ===")
c.execute('''SELECT u.name, u.city, p.product, p.no_of_items 
             FROM user_products p 
             JOIN users_info u ON p.user_id = u.id''')
for row in c.fetchall():
    print(row)

print("\n=== TEST QUERY: Number of people who bought Pen ===")
c.execute('''SELECT COUNT(*) 
             FROM user_products 
             WHERE LOWER(product) = 'pen' ''')
print(f"Count: {c.fetchone()[0]}")

db.close()
print("\n✅ Complete!")

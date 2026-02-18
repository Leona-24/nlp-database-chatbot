import sqlite3

# Connect to database
db = sqlite3.connect('app.db')
cursor = db.cursor()

# Show all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== ALL TABLES ===")
for table in tables:
    print(f"- {table[0]}")
    
# Create user_products table with proper structure
print("\n=== Creating user_products table ===")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_products (
        user_id INTEGER,
        product TEXT,
        no_of_items INTEGER
    )
""")

# Clear any existing data
cursor.execute("DELETE FROM user_products")

# Add sample data matching the screenshots
print("Adding sample data...")
cursor.execute("INSERT INTO user_products (user_id, product, no_of_items) VALUES (5, 'Pen', 10)")
cursor.execute("INSERT INTO user_products (user_id, product, no_of_items) VALUES (8, 'Pencil', 20)")

db.commit()

# Verify the data
print("\n=== USER_PRODUCTS TABLE ===")
cursor.execute("SELECT * FROM user_products")
for row in cursor.fetchall():
    print(row)

# Test the exact match query
print("\n=== TEST: Count people who bought 'Pen' (exact match) ===")
cursor.execute("SELECT COUNT(*) FROM user_products WHERE LOWER(product) = 'pen'")
count = cursor.fetchone()[0]
print(f"Count: {count}")

print("\n=== TEST: Count people who bought 'Pencil' (exact match) ===")  
cursor.execute("SELECT COUNT(*) FROM user_products WHERE LOWER(product) = 'pencil'")
count = cursor.fetchone()[0]
print(f"Count: {count}")

print("\n✅ Setup complete!")
db.close()

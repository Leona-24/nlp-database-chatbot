"""
Add sample product data to demonstrate the precision fix
This creates user_products table with pen and pencil data
"""
from sqlalchemy import create_engine, text

# Connect to the database
engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})

with engine.connect() as conn:
    # Create user_products table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_products (
            user_id INTEGER,
            product TEXT,
            no_of_items INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """))
    
    # Create users table if it doesn't exist
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city TEXT
        )
    """))
    
    # Check if data already exists
    result = conn.execute(text("SELECT COUNT(*) as cnt FROM users WHERE id IN (5, 8)")).first()
    
    if result[0] == 0:
        print("Adding sample users and product data...")
        
        # Add users
        conn.execute(text("INSERT OR REPLACE INTO users (id, name, city) VALUES (5, 'blessy', 'chennai')"))
        conn.execute(text("INSERT OR REPLACE INTO users (id, name, city) VALUES (8, 'Karthik', 'Madurai')"))
        
        # Add product purchases
        conn.execute(text("INSERT INTO user_products (user_id, product, no_of_items) VALUES (5, 'Pen', 10)"))
        conn.execute(text("INSERT INTO user_products (user_id, product, no_of_items) VALUES (8, 'Pencil', 20)"))
        
        conn.commit()
        print("✅ Sample data added successfully!")
    else:
        print("Data already exists")
    
    # Show the data
    print("\n=== USERS ===")
    result = conn.execute(text("SELECT * FROM users WHERE id IN (5, 8)"))
    for row in result:
        print(dict(row._mapping))
    
    print("\n=== USER PRODUCTS ===")
    result = conn.execute(text("SELECT * FROM user_products"))
    for row in result:
        print(dict(row._mapping))
    
    print("\n=== TEST QUERY: Who bought Pen ===")
    result = conn.execute(text("""
        SELECT users.name, users.city, user_products.product, user_products.no_of_items
        FROM user_products 
        JOIN users ON user_products.user_id = users.id 
        WHERE LOWER(user_products.product) = 'pen'
    """))
    for row in result:
        print(dict(row._mapping))

print("\n✅ Database setup complete!")

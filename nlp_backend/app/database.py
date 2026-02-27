import os
from sqlalchemy import create_engine, text, inspect
import pandas as pd
from typing import List, Dict, Any, Optional

# Base directory for the database files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Global engines
engine = None  # Dynamic engine for user queries
auth_db_path = os.path.join(DATA_DIR, "auth.db")
auth_engine = create_engine(f"sqlite:///{auth_db_path}", connect_args={"check_same_thread": False})

def get_engine():
    global engine
    if engine is None:
        # Default fallback to local SQLite for demo queries
        app_db_path = os.path.join(DATA_DIR, "app.db")
        engine = create_engine(f"sqlite:///{app_db_path}", connect_args={"check_same_thread": False})
    return engine

def get_auth_engine():
    return auth_engine

def connect_db(config: Dict[str, Any]):
    """
    Connects to a database dynamically based on config.
    Config expects: type, host, port, database, username, password
    """
    global engine
    
    db_type = config.get("type", "sqlite")
    
    try:
        if db_type == "sqlite":
             # For sqlite, we might just use a local file or memory
             db_path = config.get("database", "data/app.db")
             connection_string = f"sqlite:///./{db_path}"
             new_engine = create_engine(connection_string, connect_args={"check_same_thread": False})
             
        elif db_type == "postgresql":
            # postgresql://user:password@host:port/dbname
            user = config.get("username")
            password = config.get("password")
            host = config.get("host")
            port = config.get("port", "5432")
            dbname = config.get("database")
            
            connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
            new_engine = create_engine(connection_string)
            
        elif db_type == "mysql":
            # mysql+pymysql://user:password@host:port/dbname
            user = config.get("username")
            password = config.get("password")
            host = config.get("host")
            port = config.get("port", "3306")
            dbname = config.get("database")
            
            connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
            new_engine = create_engine(connection_string)
            
        else:
            return {"error": f"Unsupported database type: {db_type}"}

        # Test connection
        with new_engine.connect() as conn:
            pass
            
        # If successful, update global engine
        engine = new_engine
        return {"message": "Connected successfully", "type": db_type}
        
    except Exception as e:
        return {"error": str(e)}

def get_schema() -> List[Dict[str, Any]]:
    """
    Returns the schema of the connected database.
    Format: [{name: 'table_name', columns: [{name: 'col', type: 'TYPE', ...}]}]
    """
    try:
        current_engine = get_engine()
        # Fresh inspector every time to detect dynamically added tables
        inspector = inspect(current_engine)
        schema = []
        
        table_names = inspector.get_table_names()
        for table in table_names:
            columns = []
            for col in inspector.get_columns(table):
                columns.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "primary_key": col.get("primary_key", False)
                })
            
            # Try to get foreign keys
            try:
                fks = inspector.get_foreign_keys(table)
                for fk in fks:
                    # Enrich column info if it's a foreign key
                    for col_name in fk["constrained_columns"]:
                        for col_data in columns:
                            if col_data["name"] == col_name:
                                col_data["foreign_key"] = f"{fk['referred_table']}.{fk['referred_columns'][0]}"
            except Exception:
                pass # Some DBs might fail here
                
            schema.append({
                "name": table,
                "columns": columns
            })
            
        return schema
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return []

def init_db():
    """Initializes the sample database with mock data."""
    current_engine = get_engine()
    if "app.db" in str(current_engine.url):
        with current_engine.connect() as conn:
            with conn.begin():
                # Create Sample Tables
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        department TEXT,
                        gpa REAL
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT,
                        city TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER,
                        total_amount REAL,
                        order_date DATE,
                        FOREIGN KEY(customer_id) REFERENCES customers(id)
                    )
                """))

                # Check if data exists, if not seed it
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM students")).scalar()
                    if result == 0:
                        print("Seeding sample database...")
                        conn.execute(text("INSERT INTO students (name, department, gpa) VALUES ('Alice', 'CS', 3.8)"))
                        conn.execute(text("INSERT INTO students (name, department, gpa) VALUES ('Bob', 'Arts', 3.5)"))
                        conn.execute(text("INSERT INTO students (name, department, gpa) VALUES ('Charlie', 'Physics', 3.9)"))
                        
                        conn.execute(text("INSERT INTO customers (name, email, city) VALUES ('John Doe', 'john@example.com', 'New York')"))
                        conn.execute(text("INSERT INTO customers (name, email, city) VALUES ('Jane Smith', 'jane@example.com', 'Chennai')"))
                        
                        conn.execute(text("INSERT INTO orders (customer_id, total_amount, order_date) VALUES (1, 150.00, '2023-01-10')"))
                        conn.execute(text("INSERT INTO orders (customer_id, total_amount, order_date) VALUES (2, 85.50, '2023-02-15')"))
                except Exception as e:
                    print(f"Seed failed: {e}")

def init_auth_db():
    """Initializes the authentication database."""
    engine = get_auth_engine()
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Migration: Add email column if not exists
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN email TEXT"))
            except Exception:
                pass # Already exists or other error

def execute_query(sql_query: str) -> Dict[str, Any]:
    """Executes a raw SQL query and returns results as a list of dicts. SECURITY: Only SELECT queries allowed."""
    current_engine = get_engine()
    print(f"Executing SQL: {sql_query}")
    try:
        # 🔒 COMPREHENSIVE SECURITY CHECK - Block ALL data modification operations
        sql_upper = sql_query.upper().strip()
        
        # List of ALL forbidden SQL operations
        forbidden_operations = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
            "CREATE", "REPLACE", "MERGE", "GRANT", "REVOKE",
            "EXEC", "EXECUTE", "CALL", "PRAGMA", "ATTACH", "DETACH"
        ]
        
        # Check for any forbidden keywords
        for operation in forbidden_operations:
            if operation in sql_upper:
                return {"error": f"🚫 BLOCKED: '{operation}' operations are not allowed. Only SELECT queries permitted for data safety."}
            
        with current_engine.connect() as conn:
            # Check if query is valid selection
            clean_query = sql_query.strip()
            
            # If it's an error message from our NLP engine (starts with --)
            if clean_query.startswith("--"):
                 return {"error": f"I was unable to build a valid query: {clean_query.replace('--', '').strip()}"}

            if not clean_query:
                 return {"error": "No query was generated. Please try rephrasing your question."}

            # Must be a SELECT query
            if not clean_query.upper().startswith("SELECT"):
                 return {"error": "🚫 SECURITY: Only SELECT queries are supported. No data modifications allowed."}

            import time
            start_time = time.time()
            result = conn.execute(text(sql_query))
            # Get column names
            columns = result.keys()
            # Fetch all rows (frontend handles pagination)
            rows = result.fetchall()
            data = [dict(zip(columns, row)) for row in rows]
            execution_time = round(time.time() - start_time, 3)
            return {"columns": list(columns), "data": data, "execution_time": execution_time}
            
    except Exception as e:
        return {"error": str(e)}

def get_user(identifier: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by username OR email from the auth database."""
    current_engine = get_auth_engine()
    try:
        with current_engine.connect() as conn:
            # Use mappings() to get dict-like access for compatibility across SQLAlchemy versions
            query = text("SELECT id, username, password_hash, email FROM users WHERE username = :i OR email = :i")
            result = conn.execute(query, {"i": identifier}).mappings().first()
            
            if result:
                return dict(result)
            return None
    except Exception as e:
        print(f"Auth Retrieve Error: {e}")
        return None

def create_user(username: str, email: str, password_hash: str) -> bool:
    """Creates a new user in the auth database."""
    current_engine = get_auth_engine()
    try:
        with current_engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, email, password_hash) VALUES (:u, :e, :p)"), 
                {"u": username, "e": email, "p": password_hash}
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Auth Creation Error: {e}")
        return False

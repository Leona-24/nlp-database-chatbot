import sqlite3
import os

db_path = "nlp_backend/data/industrial.db"
os.makedirs("nlp_backend/data", exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Machines
cursor.execute("""
CREATE TABLE machines (
    machine_id INTEGER PRIMARY KEY,
    machine_name TEXT NOT NULL,
    location TEXT,
    last_service_date DATE
)
""")

# 2. Products
cursor.execute("""
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_type TEXT NOT NULL,
    base_price REAL
)
""")

# 3. Production
cursor.execute("""
CREATE TABLE production (
    production_id INTEGER PRIMARY KEY AUTOINCREMENT,
    production_date DATE,
    product_id INTEGER,
    machine_id INTEGER,
    shift TEXT,
    units_produced INTEGER,
    defects INTEGER,
    production_time_hours REAL,
    FOREIGN KEY(product_id) REFERENCES products(product_id),
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
)
""")

# 4. Environment Conditions
cursor.execute("""
CREATE TABLE environment_conditions (
    production_id INTEGER,
    avg_temperature_c REAL,
    avg_humidity_percent REAL,
    FOREIGN KEY(production_id) REFERENCES production(production_id)
)
""")

# 5. Production Costs
cursor.execute("""
CREATE TABLE production_costs (
    production_id INTEGER,
    material_cost REAL,
    energy_kwh REAL,
    labour_hours REAL,
    FOREIGN KEY(production_id) REFERENCES production(production_id)
)
""")

# 6. Quality Checks
cursor.execute("""
CREATE TABLE quality_checks (
    production_id INTEGER,
    failed_checks INTEGER,
    scrap_rate REAL,
    rework_hours REAL,
    FOREIGN KEY(production_id) REFERENCES production(production_id)
)
""")

# Seed some data
cursor.execute("INSERT INTO machines (machine_name, location) VALUES ('Machine-A', 'Floor-1'), ('Machine-B', 'Floor-2')")
cursor.execute("INSERT INTO products (product_type, base_price) VALUES ('Automotive', 500.0), ('Aerospace', 2500.0)")
cursor.execute("INSERT INTO production (production_date, product_id, machine_id, shift, units_produced, defects) VALUES ('2023-10-01', 1, 1, 'Morning', 100, 2)")
cursor.execute("INSERT INTO production (production_date, product_id, machine_id, shift, units_produced, defects) VALUES ('2023-10-01', 2, 2, 'Night', 50, 1)")
cursor.execute("INSERT INTO environment_conditions (production_id, avg_temperature_c) VALUES (1, 24.5), (2, 22.0)")
cursor.execute("INSERT INTO production_costs (production_id, energy_kwh) VALUES (1, 150.0), (2, 280.0)")
cursor.execute("INSERT INTO quality_checks (production_id, failed_checks) VALUES (1, 0), (2, 3)")

conn.commit()
conn.close()

print(f"✅ Industrial Database created at {db_path}")

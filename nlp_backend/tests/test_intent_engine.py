"""
Comprehensive test suite for the improved NLP intent-understanding engine.
Tests typo tolerance, intent detection, schema awareness, and SQL generation.
"""
import json
import sys

# Import the engine
from nlp_service import nlp_engine

# Load schema
with open("full_schema.json", "r") as f:
    schema = json.load(f)

# Define test cases: (input, expected_intent_keywords_in_sql)
test_cases = [
    # === EXACT MATCHES FROM USER EXAMPLES ===
    ("hw many usrs are there", "COUNT(*)", "Typo: count users"),
    ("show all user", "SELECT *", "List users"),
    ("giv me total product", "COUNT(*)", "Count products"),
    ("lst all prodcts", "SELECT *", "List products"),
    
    # === COUNT INTENT ===
    ("how many students are there", "COUNT(*)", "Count students"),
    ("how many customers", "COUNT(*)", "Count customers"),
    ("number of orders", "COUNT(*)", "Count orders"),
    ("count all students", "COUNT(*)", "Count students explicit"),
    
    # === LIST INTENT ===
    ("show all students", "SELECT * FROM students", "List students"),
    ("show all customers", "SELECT * FROM customers", "List customers"),
    ("list all orders", "SELECT * FROM orders", "List orders"),
    ("display all students", "SELECT *", "Display students"),
    
    # === FILTER BY VALUE ===
    ("show students from CS department", "department", "Filter by dept"),
    ("show customers from Chennai", "city", "Filter by city"),
    ("students with gpa greater than 3.5", "gpa >", "GPA filter"),
    
    # === COLUMN SELECTION ===
    ("show student names", "name", "Select name column"),
    ("show customer emails", "email", "Select email column"),
    
    # === JOIN QUERIES ===
    ("show customers and their orders", "JOIN", "Join customers+orders"),
    
    # === AGGREGATION ===
    ("total amount of orders", "SUM", "Sum orders"),
    ("average gpa of students", "AVG", "Average GPA"),
    
    # === SORTING / LIMITING ===
    ("top 5 students", "LIMIT 5", "Top 5 limit"),
    
    # === META QUERIES ===
    ("show all tables", "sqlite_master", "List tables"),
    ("list tables in database", "sqlite_master", "List tables variant"),

    # === TYPO RESILIENCE ===
    ("shw all studnts", "students", "Typo: students"),
    ("custmers from mumbai", "city", "Typo: customers + city"),
]

print("=" * 70)
print("NLP ENGINE TEST SUITE")
print("=" * 70)

passed = 0
failed = 0

for query, expected_keyword, description in test_cases:
    result = nlp_engine.generate_sql(query, schema)
    sql = result["sql"]
    
    if expected_keyword.upper() in sql.upper():
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    print(f"\n{status} | {description}")
    print(f"  Input:    \"{query}\"")
    print(f"  SQL:      {sql}")
    print(f"  Expected: {expected_keyword}")

print("\n" + "=" * 70)
print(f"RESULTS: {passed}/{passed+failed} passed ({failed} failed)")
print("=" * 70)

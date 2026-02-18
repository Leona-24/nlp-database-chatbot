import json, sys, io

old_stdout = sys.stdout
sys.stdout = io.StringIO()

from nlp_service import nlp_engine
schema = json.load(open("full_schema.json"))

test_cases = [
    ("hw many usrs are there", "COUNT(*)"),
    ("show all user", "SELECT *"),
    ("giv me total product", "COUNT(*)"),
    ("lst all prodcts", "SELECT *"),
    ("how many students are there", "COUNT(*)"),
    ("how many customers", "COUNT(*)"),
    ("number of orders", "COUNT(*)"),
    ("count all students", "COUNT(*)"),
    ("show all students", "SELECT * FROM students"),
    ("show all customers", "SELECT * FROM customers"),
    ("list all orders", "SELECT * FROM orders"),
    ("display all students", "SELECT *"),
    ("show students from CS department", "department"),
    ("show customers from Chennai", "city"),
    ("students with gpa greater than 3.5", "gpa >"),
    ("show student names", "name"),
    ("show customer emails", "email"),
    ("show customers and their orders", "JOIN"),
    ("total amount of orders", "SUM"),
    ("average gpa of students", "AVG"),
    ("top 5 students", "LIMIT 5"),
    ("show all tables", "sqlite_master"),
    ("list tables in database", "sqlite_master"),
    ("shw all studnts", "students"),
    ("custmers from mumbai", "city"),
]

results = []
for q, exp in test_cases:
    r = nlp_engine.generate_sql(q, schema)
    sql = r["sql"]
    ok = exp.upper() in sql.upper()
    results.append((ok, q, sql, exp))

sys.stdout = old_stdout

passed = sum(1 for ok, _, _, _ in results if ok)
failed = sum(1 for ok, _, _, _ in results if not ok)

for ok, q, sql, exp in results:
    tag = "OK" if ok else "XX"
    print(f"{tag}: {q}")
    if not ok:
        print(f"   SQL: {sql}")
        print(f"   Want: {exp}")

print(f"\nResults: {passed}/{len(results)} passed, {failed} failed")

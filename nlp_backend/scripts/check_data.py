from database import execute_query
import json

print("--- STUDENTS ---")
print(json.dumps(execute_query("SELECT * FROM students"), indent=2))

print("\n--- USERS ---")
print(json.dumps(execute_query("SELECT * FROM users"), indent=2))

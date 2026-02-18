"""
Test the exact query: "tell me number of person brought pen"
"""
import sys
sys.path.append('.')

from nlp_service import nlp_engine
from database import get_schema

# Get current schema
schema = get_schema()

print("=== CURRENT DATABASE SCHEMA ===")
for table in schema:
    print(f"\nTable: {table['name']}")
    for col in table['columns']:
        print(f"  - {col['name']} ({col['type']})")

print("\n" + "="*80)
print("TESTING YOUR EXACT QUERY")
print("="*80)

# Your exact query
query = "tell me number of person brought pen"
print(f"\nInput: '{query}'")

result = nlp_engine.generate_sql(query, schema)

print(f"\nGenerated SQL:\n{result['sql']}")
print(f"\nThought: {result['thought']}")
print(f"Confidence: {result['confidence']}")
print(f"Model: {result['model']}")

# Now actually execute it
print("\n" + "="*80)
print("EXECUTING THE QUERY")
print("="*80)

from database import execute_query
execution_result = execute_query(result['sql'])

if 'error' in execution_result:
    print(f"Error: {execution_result['error']}")
else:
    print(f"Results: {execution_result['data']}")
    print(f"Number of rows: {len(execution_result['data'])}")

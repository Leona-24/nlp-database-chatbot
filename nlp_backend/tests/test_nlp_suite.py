"""
Comprehensive Test for Demo Queries
"""
import sys
sys.path.append('.')

from nlp_service import nlp_engine
from database import get_schema

# Get current schema
schema = get_schema()

test_queries = [
    "Show only names of users",
    "Show users from Chennai",
    "Show all users who bought Pencil",
    "Show products with more than 5 items",
    "Show users and their products",
    "How many users are there?",
    "Show top 3 users"
]

print("=== NLP ENGINE TEST SUITE ===")
for query in test_queries:
    print(f"\nQuery: {query}")
    result = nlp_engine.generate_sql(query, schema)
    print(f"SQL: {result['sql']}")
    print(f"Thought: {result['thought']}\n")

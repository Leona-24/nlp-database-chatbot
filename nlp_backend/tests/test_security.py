"""
Security Test Suite for NLP Service
Tests the multi-layer security validation
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from nlp_service import nlp_engine

# Sample schema for testing
TEST_SCHEMA = [
    {
        "name": "users",
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"},
            {"name": "email", "type": "TEXT"}
        ]
    },
    {
        "name": "orders",
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "user_id", "type": "INTEGER"},
            {"name": "total", "type": "REAL"}
        ]
    }
]

def test_security():
    print("=" * 70)
    print("🔒 SECURITY TEST SUITE - Read-Only Database Protection")
    print("=" * 70)
    
    # Test cases
    test_cases = [
        # ✅ Valid SELECT queries (should pass)
        ("Show me all users", "✅ VALID"),
        ("List all orders", "✅ VALID"),
        ("How many users are there?", "✅ VALID"),
        
        # ❌ Data modification attempts (should be blocked)
        ("Delete all users", "❌ BLOCKED"),
        ("Update user email to test@example.com", "❌ BLOCKED"),
        ("Insert a new user named John", "❌ BLOCKED"),
        ("Drop the users table", "❌ BLOCKED"),
        ("Create a new table called products", "❌ BLOCKED"),
        ("Truncate the orders table", "❌ BLOCKED"),
    ]
    
    print("\n📝 Running security tests...\n")
    
    for query, expected in test_cases:
        print(f"Query: '{query}'")
        print(f"Expected: {expected}")
        
        result = nlp_engine.generate_sql(query, TEST_SCHEMA)
        
        # Check if blocked
        if result["sql"] == "-- BLOCKED" or "BLOCKED" in result["thought"]:
            print(f"Result: ❌ BLOCKED")
            print(f"Reason: {result['thought']}")
            status = "❌ BLOCKED"
        else:
            print(f"Result: ✅ ALLOWED")
            print(f"SQL: {result['sql']}")
            status = "✅ VALID"
        
        # Verify expected behavior
        if expected in status:
            print("✓ Test PASSED ✓")
        else:
            print("✗ Test FAILED ✗")
        
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("🎉 Security test suite complete!")
    print("=" * 70)

if __name__ == "__main__":
    test_security()

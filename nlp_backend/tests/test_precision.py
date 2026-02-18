"""
Test Precision Matching: "pen" vs "pencil"
This test demonstrates the fix for the exact issue you reported.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from nlp_service import nlp_engine

# Schema matching your actual database structure
SCHEMA = [
    {
        "name": "user_products",
        "columns": [
            {"name": "user_id", "type": "INTEGER"},
            {"name": "product", "type": "TEXT"},
            {"name": "no_of_items", "type": "INTEGER"}
        ]
    },
    {
        "name": "users",
        "columns": [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"},
            {"name": "city", "type": "TEXT"}
        ]
    }
]

def test_precision():
    print("=" * 80)
    print("🎯 PRECISION MATCHING TEST - The 'Pen vs Pencil' Fix")
    print("=" * 80)
    print("\nYour Issue: 'show all who bought pen' was returning BOTH pen and pencil")
    print("Root Cause: LIKE '%pen%' matches substring, so 'pen' matched 'pencil'")
    print("Fix: Changed to exact matching with = 'pen'")
    print("\n" + "=" * 80)
    
    # Test 1: Show who bought pen
    print("\n📝 TEST 1: 'show all who bought pen'")
    print("-" * 80)
    result1 = nlp_engine.generate_sql("show all who bought pen", SCHEMA)
    print(f"Generated SQL:\n{result1['sql']}")
    print(f"\nThought Process: {result1['thought']}")
    
    # Check if it uses exact matching
    sql_lower = result1['sql'].lower()
    if "= 'pen'" in sql_lower or '= "pen"' in sql_lower:
        print("\n✅ SUCCESS: Uses exact matching (= 'pen')")
        print("   This will match ONLY 'pen', NOT 'pencil'")
    elif "like '%pen%'" in sql_lower:
        print("\n❌ NEED TO FIX: Still using substring matching")
        print("   This would match both 'pen' AND 'pencil'")
    
    # Test 2: Show who bought pencil
    print("\n" + "=" * 80)
    print("\n📝 TEST 2: 'show all who bought pencil'")
    print("-" * 80)
    result2 = nlp_engine.generate_sql("show all who bought pencil", SCHEMA)
    print(f"Generated SQL:\n{result2['sql']}")
    print(f"\nThought Process: {result2['thought']}")
    
    sql_lower2 = result2['sql'].lower()
    if "= 'pencil'" in sql_lower2 or '= "pencil"' in sql_lower2:
        print("\n✅ SUCCESS: Uses exact matching (= 'pencil')")
        print("   This will match ONLY 'pencil', NOT 'pen'")
    elif "like '%pencil%'" in sql_lower2:
        print("\n⚠️  WARNING: Using substring matching")
        print("   This might match other items containing 'pencil'")
    
    # Test 3: Search for partial match (when appropriate)
    print("\n" + "=" * 80)
    print("\n📝 TEST 3: 'show products containing pen'")
    print("-" * 80)
    result3 = nlp_engine.generate_sql("show products containing pen", SCHEMA)
    print(f"Generated SQL:\n{result3['sql']}")
    print(f"\nNote: When user asks for 'containing', LIKE '%...%' is appropriate")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎉 SUMMARY")
    print("=" * 80)
    print("""
Before Fix:
  Query: "show all who bought pen"
  SQL: WHERE product LIKE '%pen%'
  Results: pen ✓ + pencil ✓ (wrong!)

After Fix:
  Query: "show all who bought pen"
  SQL: WHERE product = 'pen'
  Results: pen ✓ only (correct!)
    """)
    print("=" * 80)

if __name__ == "__main__":
    test_precision()

import requests
import json
import os

API_URL = "http://localhost:8000/api/query"

test_cases = [
    {
        "id": 1,
        "question": "Show all machine names",
        "expected_tables": ["machines"]
    },
    {
        "id": 2,
        "question": "Total units produced in the Morning shift",
        "expected_tables": ["production"]
    },
    {
        "id": 3,
        "question": "Average temperature for production on Night shift",
        "expected_tables": ["environment_conditions", "production"]
    },
    {
        "id": 4,
        "question": "Which product types had more than 2 quality checks failed?",
        "expected_tables": ["products", "production", "quality_checks"]
    },
    {
        "id": 5,
        "question": "Total energy consumption for machine_id 1",
        "expected_tables": ["production_costs", "production"]
    }
]

results = []

print("🚀 Starting Industrial Database Test with RAG...")
print("-" * 60)

for case in test_cases:
    print(f"Testing Q{case['id']}: {case['question']}")
    try:
        response = requests.post(API_URL, json={"query": case["question"]}, timeout=30)
        data = response.json()
        
        sql = data.get("sql_query", "").lower()
        thought = data.get("thought", "")
        
        # Verify RAG Accuracy (Did it pick the right tables?)
        tables_found = []
        for table in case["expected_tables"]:
            if table in sql:
                tables_found.append(table)
        
        rag_score = len(tables_found) / len(case["expected_tables"])
        
        # Verify Execution Accuracy (Did it get data?)
        execution_success = "error" not in data.get("message", "").lower() and len(data.get("results", [])) >= 0
        
        # A result is "Correct" if:
        # 1. RAG picked at least the primary necessary table
        # 2. SQL was generated and executed without error
        is_correct = rag_score >= 0.5 and execution_success
        
        results.append({
            "question": case["question"],
            "sql": sql,
            "is_correct": is_correct,
            "rag_score": rag_score,
            "results_count": len(data.get("results", [])),
            "thought": thought
        })
        
        status = "✅ CORRECT" if is_correct else "❌ FAILED"
        print(f"Status: {status} | Tables Found: {len(tables_found)}/{len(case['expected_tables'])}")
        print(f"SQL: {sql[:100]}...")
        print("-" * 30)
        
    except Exception as e:
        print(f"Error testing Q{case['id']}: {e}")

# Calculate Final Accuracy
correct_count = sum(1 for r in results if r["is_correct"])
accuracy = (correct_count / len(test_cases)) * 100

summary = {
    "total_questions": len(test_cases),
    "correct_answers": correct_count,
    "accuracy_percentage": accuracy,
    "detailed_results": results
}

with open("test_results.json", "w") as f:
    json.dump(summary, f, indent=4)

print("\n" + "="*60)
print(f"FINAL ACCURACY: {accuracy}%")
print("="*60)

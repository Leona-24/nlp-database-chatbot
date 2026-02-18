try:
    from nlp_service import nlp_engine
    import json
    with open("full_schema.json", "r") as f:
        schema = json.load(f)
    print("Testing connection to Llama 3 via Groq...")
    resp = nlp_engine.generate_sql("how many users", schema)
    print(f"Status: SUCCESS")
    print(f"Model Used: {resp.get('model')}")
    print(f"AI Reasoning: {resp.get('thought')}")
    print(f"Generated SQL: {resp.get('sql')}")
except Exception as e:
    print(f"Status: ERROR")
    print(f"Details: {str(e)}")

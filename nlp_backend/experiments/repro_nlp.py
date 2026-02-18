
from nlp_service import NLPEngine
import json

engine = NLPEngine()
with open('full_schema.json', 'r') as f:
    schema = json.load(f)

# Test 7: Singular Table request
query7 = "list out all the table name"
result7 = engine.generate_sql(query7, schema)
print(f"Test 7: {query7}")
print(json.dumps(result7, indent=2))

with open('repro_output.txt', 'w') as f:
    f.write(json.dumps(result7, indent=2))

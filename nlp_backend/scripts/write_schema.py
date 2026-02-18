from database import get_schema
import json
with open('full_schema.json', 'w') as f:
    json.dump(get_schema(), f, indent=2)
print("Schema written to full_schema.json")

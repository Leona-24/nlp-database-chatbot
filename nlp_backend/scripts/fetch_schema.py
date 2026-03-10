import urllib.request
import json
with urllib.request.urlopen("http://127.0.0.1:8000/api/schema") as url:
    data = json.loads(url.read().decode())
    with open('current_schema.json', 'w') as f:
        json.dump(data, f, indent=4)

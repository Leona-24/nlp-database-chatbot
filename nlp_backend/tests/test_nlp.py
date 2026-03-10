import sys
import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/api/query'
headers = {'Content-Type': 'application/json'}
data = json.dumps({'query': 'Show machine-wise OEE for this month'})

try:
    req = urllib.request.Request(url, data=data.encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print("SQL:")
        print(result.get('sql_query', ''))
        print("THOUGHT:")
        print(result.get('thought', ''))
except urllib.error.URLError as e:
    print(f"Error: {e}")

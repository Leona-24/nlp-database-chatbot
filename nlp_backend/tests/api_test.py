import urllib.request, json, sys

API_URL = "http://127.0.0.1:8000/api/query"

queries = [
    "hw many usrs are there",
    "show all user",
    "giv me total product",
    "lst all prodcts",
    "show all students",
    "show customers from Chennai",
    "total amount of orders",
]

for q in queries:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps({"query": q}).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        sql = data.get("sql_query", "N/A")
        count = len(data.get("results", []))
        msg = data.get("message", "")
        print(f"Q: {q}")
        print(f"  SQL: {sql}")
        print(f"  Results: {count} rows | {msg}")
        print()
    except Exception as e:
        print(f"Q: {q} => ERROR: {e}")
        print()

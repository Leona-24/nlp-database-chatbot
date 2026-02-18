from database import get_engine
from sqlalchemy import inspect
import json

engine = get_engine()
inspector = inspect(engine)

schema_dump = {}
for table in inspector.get_table_names():
    cols = []
    for col in inspector.get_columns(table):
        cols.append({
            "name": col["name"],
            "type": str(col["type"])
        })
    schema_dump[table] = cols

print(json.dumps(schema_dump, indent=2))

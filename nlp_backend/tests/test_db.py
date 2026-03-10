import sys
import os
sys.path.append(os.path.abspath('nlp_backend'))
from app.database import get_engine, get_schema
import pandas as pd
engine = get_engine()
with engine.connect() as conn:
    print(pd.read_sql('SELECT name FROM sqlite_master WHERE type="table"', conn))

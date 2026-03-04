import sys
sys.path.insert(0, ".")

# Simulate the data exactly as returned by execute_query
columns = ["product_type", "total_downtime"]
data = [
    {"product_type": "Appliances",  "total_downtime": 757.18},
    {"product_type": "Automotive",  "total_downtime": 774.80},
    {"product_type": "Electronics", "total_downtime": 699.79},
    {"product_type": "Furniture",   "total_downtime": 725.39},
    {"product_type": "Textiles",    "total_downtime": 782.59},
]

print("=== Testing visualization_service ===")
try:
    from app.visualization_service import generate_chart, _detect_columns, _is_numeric_col
    import pandas as pd

    df = pd.DataFrame(data)
    print(f"DataFrame:\n{df}")
    print(f"dtypes: {df.dtypes.to_dict()}")

    for col in df.columns:
        print(f"  _is_numeric_col({col!r}) = {_is_numeric_col(df[col])}")

    label_col, numeric_cols = _detect_columns(df)
    print(f"  label_col={label_col!r}, numeric_cols={numeric_cols}")

    result = generate_chart(columns=columns, data=data, query="total downtime by product type")
    if result:
        print(f"\nSUCCESS! chart_image length = {len(result)} chars")
    else:
        print("\nFAILED: generate_chart returned None")

except Exception as e:
    import traceback
    print(f"EXCEPTION: {e}")
    traceback.print_exc()


import pandas as pd
import os

file_path = "5 Years Profit and Loss_WithTrend.xlsx"

if os.path.exists(file_path):
    print(f"Scanning {file_path} for text blocks...")
    try:
        df = pd.read_excel(file_path, sheet_name=None, header=None) # Read all sheets
        for sheet_name, sheet_df in df.items():
            print(f"--- Sheet: {sheet_name} ---")
            # Iterate through all cells
            for idx, row in sheet_df.iterrows():
                for col_idx, value in enumerate(row):
                    if isinstance(value, str) and len(value) > 100:
                        print(f"Found large text at Row {idx}, Col {col_idx}:")
                        print(f"Content: {value[:200]}...")
                        print("-" * 20)
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File not found.")

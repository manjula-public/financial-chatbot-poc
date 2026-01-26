import pandas as pd
import os

file_path = "UK/5 Years Profit and Loss_WithTrend.xlsx"
full_path = os.path.join(os.getcwd(), file_path)

print(f"Analyzing file: {full_path}")

try:
    # Read the excel file, skipping potential header rows to find the main table
    # Based on previous analysis of the other file, data might start around row 5-6
    df = pd.read_excel(full_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)
    
    # Locate the row with "Gross Sales" to define the header structure
    header_row_idx = -1
    for idx, row in df.iterrows():
        # Check first few columns for "Gross Sales"
        if row.astype(str).str.contains("Gross Sales", case=False, na=False).any():
            header_row_idx = idx
            break
            
    if (header_row_idx != -1):
        print(f"Header likely at row: {header_row_idx}")
        # Reload with header
        df = pd.read_excel(full_path, sheet_name='5 YEARS_Annual Profit and Loss', header=header_row_idx)
        print(df.head(20).to_markdown())
        print("\n--- Column Names ---")
        print(df.columns.tolist())
    else:
        print("Could not locate 'Gross Sales' row. Printing first 20 rows raw.")
        print(df.head(20).to_markdown())

except Exception as e:
    print(f"Error reading file: {e}")

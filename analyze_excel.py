import pandas as pd
import os

files = [
    "5 Years Profit and Loss_WithTrend.xlsx",
    "UK/5 Years Profit and Loss_WithTrend.xlsx"
]

def analyze_file(file_path):
    full_path = os.path.join(os.getcwd(), file_path)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    print(f"\nAnalyzing file: {file_path}")
    try:
        # Load without header
        df = pd.read_excel(full_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)
        
        # Find first row with at least 3 non-null values
        start_row = -1
        for idx, row in df.iterrows():
            if row.count() >= 3:
                start_row = idx
                break
        
        if start_row != -1:
            print(f"Potential header found at row {start_row}")
            print(df.iloc[start_row:start_row+5].to_markdown())
        else:
            print("No significant data found.")
            
    except Exception as e:
        print(f"Error: {e}")

for f in files:
    analyze_file(f)

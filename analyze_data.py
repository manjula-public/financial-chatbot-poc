import pandas as pd
import io

def clean_and_parse_data(file_or_path):
    """
    Reads the Excel file (or file-like object) and extracting the P&L data.
    Assumes the structure where 'Gross Sales' creates the header row.
    """
    try:
        # Load the dataframe
        # If it's a file path
        if isinstance(file_or_path, str):
            df = pd.read_excel(file_or_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)
        else:
            # If it's a file upload object
            df = pd.read_excel(file_or_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)

        # Find header row
        header_row_idx = -1
        for idx, row in df.iterrows():
            if row.astype(str).str.contains("Gross Sales", case=False, na=False).any():
                header_row_idx = idx
                break
        
        if header_row_idx == -1:
            return None, "Could not find 'Gross Sales' row to identify headers."

        # Reload with correct header
        if isinstance(file_or_path, str):
            df = pd.read_excel(file_or_path, sheet_name='5 YEARS_Annual Profit and Loss', header=header_row_idx)
        else:
            # Need to seek 0 if it was read before? 
            # pandas read_excel usually handles bytes well, but safer to re-read from source if possible
            # For stream, might need to reset pointer if passed twice, but here we just re-parse the existing df?
            # Actually easier to just slice the initial DF since we already loaded it without headers
             # Make the found row the columns
            new_header = df.iloc[header_row_idx]
            df = df[header_row_idx + 1:] 
            df.columns = new_header
            
        # Clean up columns
        # We expect columns like 'Accounts', '2024', '2025' etc. 
        # But headers might be messy like "Unnamed: 1". 
        # The user wants specific columns in B column mainly.
        
        # Let's standardize column names if possible or just return raw specific subset
        # Drop completely empty rows
        df = df.dropna(how='all')
        
        # Reset index
        df.reset_index(drop=True, inplace=True)
        
        return df, None

    except Exception as e:
        return None, str(e)

def get_empty_template():
    """Returns a DataFrame with the standard expense categories for manual entry."""
    categories = [
        "Gross Sales",
        "Less Sales Discounts (enter as negative)",
        "Less Sales Returns (enter as negative)",
        "Cost of Goods Sold",
        "Marketing & Advertising",
        "Salaries & Wages",
        "Payroll Benefits & Taxes",
        "Travel & Entertainment",
        "Web Hosting and maintenance",
        "Stationary",
        "Rent",
        "Utilities",
        "Office Supplies",
        "Professional Fees",
        "Insurance",
        "Depreciation",
        "Interest Expense",
        "Other Operating Expenses1",
        "Other Operating Expenses2",
        "Other Operating Expenses3",
        "Other Operating Expenses4",
        "Other Operating Expenses5"
    ]
    return pd.DataFrame({"Category": categories, "2024": [0.0]*len(categories), "2025": [0.0]*len(categories)})

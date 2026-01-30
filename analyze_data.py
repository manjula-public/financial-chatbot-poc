import pandas as pd
import io

def clean_and_parse_data(file_or_path):
    """
    Reads the Excel file and extracts P&L data.
    Attempts to intelligently find the header row containing Years and 'Category'.
    """
    try:
        # Load the dataframe without header initially to scan
        if isinstance(file_or_path, str):
            df_raw = pd.read_excel(file_or_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)
        else:
            df_raw = pd.read_excel(file_or_path, sheet_name='5 YEARS_Annual Profit and Loss', header=None)

        # Strategy 1: Look for "Category" or "Account" explicitly
        header_row_idx = -1
        for idx, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower()
            if row_str.str.contains("category").any() or row_str.str.contains("account").any():
                header_row_idx = idx
                break
        
        # Strategy 2: If not found, look for "Gross Sales" (Data row) and take row above it
        if header_row_idx == -1:
            for idx, row in df_raw.iterrows():
                if row.astype(str).str.contains("Gross Sales", case=False, na=False).any():
                    # If Gross Sales is found, the header is likely the row above
                    if idx > 0:
                        header_row_idx = idx - 1
                    else:
                        header_row_idx = idx # Fallback, though unlikely
                    break

        if header_row_idx == -1:
            return None, "Could not identify header row (checked for 'Category', 'Account', or row above 'Gross Sales')."

        # Apply Header
        new_header = df_raw.iloc[header_row_idx]
        df = df_raw[header_row_idx + 1:].copy() 
        df.columns = new_header
        
        # Rename first column to 'Category' to be safe
        # (The header in Excel might be 'Category' or empty or something else)
        if len(df.columns) > 0:
            cols = list(df.columns)
            cols[0] = 'Category'
            df.columns = cols
            
        # Clean up Category values just in case
        if 'Category' in df.columns:
             df['Category'] = df['Category'].astype(str).str.strip()
            
        # Drop empty rows
        df = df.dropna(how='all')
        
        # Clean up Year Columns (convert float to int/str)
        # Some imports make 2024 as 2024.0
        new_cols = []
        for c in df.columns:
            try:
                # If it's a number like 2024.0, make it '2024'
                val = float(c)
                if val.is_integer() and val > 1900 and val < 2100:
                    new_cols.append(str(int(val)))
                else:
                     new_cols.append(str(c).strip())
            except:
                new_cols.append(str(c).strip())
        df.columns = new_cols

        df.reset_index(drop=True, inplace=True)
        
        return df, None

    except Exception as e:
        return None, f"Parsing Error: {str(e)}"

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

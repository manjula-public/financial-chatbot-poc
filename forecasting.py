
import pandas as pd
import numpy as np

def generate_forecast(df_input, start_year, end_year):
    """
    Takes a dataframe with 'Category', '2024', '2025' columns.
    Forecasts up to end_year based on the trend between 2024 and 2025.
    """
    # Create a copy to avoid mutating original
    df = df_input.copy()
    
    # Ensure numeric
    base_years = [2024, 2025]
    for y in base_years:
        col_name = str(y)
        if col_name in df.columns:
             df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
    
    # Calculate Growth Rate or Absolute Diff
    # User said: "predict based on year 2024 and 2025"
    # Linear projection: Diff = val_2025 - val_2024. Next year = val_prev + Diff.
    
    years_to_predict = range(2026, int(end_year) + 1)
    
    current_cols = [str(y) for y in base_years if str(y) in df.columns]
    if len(current_cols) < 2:
        return df # Can't forecast
        
    for year in years_to_predict:
        prev_year = str(year - 1)
        prev_prev_year = str(year - 2)
        
        # Calculate for each row
        new_values = []
        for _, row in df.iterrows():
            try:
                val_last = float(row[prev_year])
                val_prev = float(row[prev_prev_year])
                
                # Simple Linear Trend
                diff = val_last - val_prev
                prediction = val_last + diff
                new_values.append(prediction)
            except:
                new_values.append(0.0)
        
        df[str(year)] = new_values

    return df

def calculate_summary_metrics(df):
    """
    Calculates derived metrics like Gross Profit, Total Expenses, Net Income 
    if the rows are identifiable.
    """
    # Normalize categories for matching
    df['Category_Clean'] = df['Category'].astype(str).str.lower().str.strip()
    
    years = [c for c in df.columns if c not in ['Category', 'Category_Clean']]
    
    summary = {}
    
    # Helper to sum based on keyword
    def sum_by_keyword(keyword, exclude=None):
        mask = df['Category_Clean'].str.contains(keyword, na=False)
        if exclude:
            mask = mask & ~df['Category_Clean'].str.contains(exclude, na=False)
        return df[mask][years].sum()
    
    # For the POC, we iterate year by year
    results = pd.DataFrame(index=years, columns=["Gross Profit", "Total Expenses", "Net Profit"])
    
    for y in years:
        # Get scalar values for the year
        # Note: This is a robust guess. In a real app, we'd ID specific rows by ID.
        col_data = df.set_index('Category')[y]
        
        # extract specific known keys safely
        def get_val(key):
            try:
                # Basic fuzzy matching
                matches = col_data[col_data.index.str.contains(key, case=False, na=False)]
                if len(matches) > 0:
                    return float(matches.values[0])
                else: 
                     return 0.0
            except:
                return 0.0

        g_sales = get_val("Gross Sales")
        discounts = get_val("Discounts")
        returns = get_val("Returns")
        cost_goods = get_val("Cost of Goods Sold")
        
        net_sales = g_sales + discounts + returns
        g_profit = net_sales - cost_goods
        
        # Expenses
        expense_keys = [
            "Marketing", "Salaries", "Payroll", "Travel", "Hosting", "Stationary", 
            "Rent", "Utilities", "Office", "Professional", "Insurance", 
            "Depreciation", "Interest", "Other Operating"
        ]
        total_exp = 0
        for k in expense_keys:
             total_exp += df[df['Category_Clean'].str.contains(k.lower(), na=False)][y].sum()
             
        net_profit = g_profit - total_exp
        
        results.loc[y, "Gross Profit"] = g_profit
        results.loc[y, "Total Expenses"] = total_exp
        results.loc[y, "Net Profit"] = net_profit
        
    return results

def calculate_executive_summary(df):
    """
    Generates a high-level summary table matching the requested format:
    Revenue: Net Sales, Direct Cost, Gross Margin, Gross Margin %
    Expenses: Operating Expenses, Interest, Taxes, EBIT
    """
    df = df.copy()
    if 'Category_Clean' not in df.columns:
         df['Category_Clean'] = df['Category'].astype(str).str.lower().str.strip()

    years = [c for c in df.columns if c not in ['Category', 'Category_Clean']]
    
    # Initialize result structure
    # Rows we want
    rows = [
        "Net Sales",
        "Direct Cost",
        "Gross Margin (Profit)",
        "Gross Margin %",
        "Operating Expenses",
        "Interest",
        "Taxes",
        "EBIT (Earnings before Interest and Taxes)"
    ]
    
    summary_df = pd.DataFrame(index=rows, columns=years)
    
    for y in years:
        col_data = df.set_index('Category')[y]
        
        def get_val(key_list):
            total = 0.0
            for key in key_list:
                matches = df[df['Category_Clean'].str.contains(key.lower(), na=False)][y]
                total += matches.sum()
            return float(total)
            
        def get_val_exact(key_fragment):
             matches = df[df['Category_Clean'].str.contains(key_fragment.lower(), na=False)][y]
             return float(matches.sum())

        # 1. Revenue
        # Net Sales = Gross Sales - Discounts (if neg) - Returns. Assuming they are in the sheet.
        # Simple Sum of "Gross Sales", "Discounts", "Returns" rows
        net_sales = get_val_exact("Gross Sales") + get_val_exact("Sales Discount") + get_val_exact("Sales Returns")
        
        # Direct Cost = Cost of Goods Sold
        direct_cost = get_val_exact("Cost of Goods Sold")
        
        # Gross Margin
        gross_margin = net_sales - direct_cost # Assuming COGS is positive. If negative in sheet, add it.
        # User sheet usually has COGS as positive number to be subtracted. 
        # But let's check: Net Sales 81k, Direct Cost 6.7k => GM 74.3k. So 81 - 6.7. Correct.
        
        if net_sales != 0:
            gm_percent = (gross_margin / net_sales) * 100
        else:
            gm_percent = 0.0
            
        # 2. Expenses
        # Operating Expenses: All expenses EXCEPT Interest and Taxes
        # We can sum known categories
        opex_keys = [
             "Marketing", "Salaries", "Payroll", "Travel", "Hosting", "Stationary", 
            "Rent", "Utilities", "Office", "Professional", "Insurance", 
            "Depreciation", "Other Operating", "Amortization", "Bad Debt"
        ]
        # Exclude Interest, Tax
        operating_expenses = get_val(opex_keys)
        
        # Interest
        interest = get_val_exact("Interest Expense")
        
        # Taxes
        taxes = get_val_exact("Income Tax") # or just "Taxes"
        
        # EBIT
        # Formula: Gross Margin - Operating Expenses
        # Wait, usually EBIT = Net Income + Interest + Taxes? 
        # Or Revenue - COGS - Opex. Yes.
        ebit = gross_margin - operating_expenses
        
        # Populate
        summary_df.loc["Net Sales", y] = net_sales
        summary_df.loc["Direct Cost", y] = direct_cost
        summary_df.loc["Gross Margin (Profit)", y] = gross_margin
        summary_df.loc["Gross Margin %", y] = gm_percent
        summary_df.loc["Operating Expenses", y] = operating_expenses
        summary_df.loc["Interest", y] = interest
        summary_df.loc["Taxes", y] = taxes
        summary_df.loc["EBIT (Earnings before Interest and Taxes)", y] = ebit
        
    return summary_df

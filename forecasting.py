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
    # OR Percentage Growth: Growth = (val_2025 / val_2024) - 1. Next year = val_prev * (1 + Growth).
    # Linear is safer for negative numbers/zeros. Percentage explodes on small numbers.
    # Let's stick to Linear difference for simplicity unless user specifies otherwise, 
    # BUT for sales, percentage make more sense.
    # Hybrid approach: If both positive, use CAGR/Percentage. If mixed/zero, use Absolute.
    # For this POC, let's use a simplified Linear Trend (Line equation).
    
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

    # Calculate Summaries (Gross Profit, Net Income) if they don't exist
    # This might be complex if we only have raw rows.
    # We can rely on the dataframe already having them OR calculate them top-down if we know the structure.
    # For now, just returning the raw forecast of line items.
    
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

    # Gross Sales
    gross_sales = sum_by_keyword("gross sales")
    
    # COGS
    cogs = sum_by_keyword("cost of goods sold")
    
    # Gross Profit = Sales - COGS (assuming COGS is positive value in sheet, subtracted logically)
    # The sheet has "Less..." so we need to be careful with signs.
    # User said: "Less Sales Discounts (enter as negative)" -> so we sum them?
    # Let's assume standard logic: 
    # Net Sales = Gross Sales + Discounts + Returns (if entered as negative)
    # Gross Profit = Net Sales - COGS
    
    # For the POC, we iterate year by year
    results = pd.DataFrame(index=years, columns=["Gross Profit", "Total Expenses", "Net Profit"])
    
    for y in years:
        # Get scalar values for the year
        # Note: This is a robust guess. In a real app, we'd ID specific rows by ID.
        col_data = df.set_index('Category')[y]
        
        # extract specific known keys safely
        def get_val(key):
            try:
                return float(col_data[col_data.index.str.contains(key, case=False, na=False)].values[0])
            except:
                return 0.0

        g_sales = get_val("Gross Sales")
        discounts = get_val("Discounts")
        returns = get_val("Returns")
        cost_goods = get_val("Cost of Goods Sold")
        
        net_sales = g_sales + discounts + returns
        g_profit = net_sales - cost_goods
        
        # Sum all expenses (everything else)
        # Exclude Sales, COGS, and the derived rows themselves
        expense_mask = ~df['Category_Clean'].str.contains("gross|sales|goods sold|profit|income|expense", regex=True, case=False)
        # ^ This regex is tricky. Better to just sum the known expense lines if possible.
        # Let's sum everything BELOW "Gross Profit" implies specific structure.
        # Simpler: Total Revenue - Net Profit check? No.
        
        # Let's just create a simple Total Expenses by summing specific expense fields from requirements
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

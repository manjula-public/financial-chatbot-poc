
import pandas as pd
import numpy as np

def generate_forecast(df_input, start_year, end_year):
    """
    Takes a dataframe with 'Category' and Year columns.
    Dynamically identifies the latest available data years and forecasts
    up to end_year based on the trend of the last 2 available years.
    """
    # Create a copy to avoid mutating original
    df = df_input.copy()
    
    # Identify existing years in columns (assuming integer-like column names)
    existing_years = []
    for col in df.columns:
        if str(col).isdigit():
            existing_years.append(int(col))
    
    existing_years.sort()
    
    # Ensure numeric for updated columns
    for y in existing_years:
        col_name = str(y)
        df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
    
    # We need at least 2 years to calculate a trend
    if len(existing_years) < 2:
        return df 
        
    last_actual_year = existing_years[-1]
    
    # If the requested end_year is not beyond our actual data, nothing to do
    if end_year <= last_actual_year:
        return df

    years_to_predict = range(last_actual_year + 1, int(end_year) + 1)
    
    # Base for trend: Last 2 years
    base_year_last = str(existing_years[-1])
    base_year_prev = str(existing_years[-2])
    
    for year in years_to_predict:
        # We use a moving trend or fixed trend? 
        # User implies linear projection.
        # Let's use the trend from the *Most Recent Actuals* and apply it forward?
        # Or should we propagate the trend (i.e. if 2026 is predicted, use 2026-2025 for 2027?)
        # Simple linear projection from last actuals is often safer (Constant Growth)
        # But if we want "Compound" growth, we use previous year.
        # Let's stick to the previous logic: New Year = Previous Year + Diff.
        # But Diff should be calculated from the BASE or dynamically?
        # Original code: diff = row[prev_year] - row[prev_prev_year]
        # This implies "Momentum". If 2025 grew by 100 vs 2024, then 2026 grows by 100 vs 2025.
        
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

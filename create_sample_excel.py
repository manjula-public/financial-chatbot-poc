
import pandas as pd

# Define the data structure matching the application's expectation
# The parser looks for a row containing "Gross Sales" to detect the header.
# We will create a few initial rows before the header to mimic a real report.

data = {
    "Category": [
        "Gross Sales",
        "Less Sales Discounts",
        "Less Sales Returns",
        "Cost of Goods Sold",
        "Gross Profit", # Calculated line (often in reports)
        "Operating Expenses",
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
        "Total Operating Expenses",
        "EBIT",
        "Interest Expense",
        "Income Tax",
        "Net Profit"
    ],
    "2024": [
        100000, # Gross Sales
        -2000,  # Discounts
        -1000,  # Returns
        30000,  # COGS
        67000,  # Gross Profit (100k - 2k - 1k - 30k)
        0,      # Header Row buffer
        5000,   # Marketing
        25000,  # Salaries
        5000,   # Benefits
        2000,   # Travel
        500,    # Hosting
        200,    # Stationary
        12000,  # Rent
        2000,   # Utilities
        1000,   # Office
        1500,   # Professional
        1200,   # Insurance
        1000,   # Depreciation
        56400,  # Total Opex (Sum of above)
        10600,  # EBIT (67000 - 56400)
        500,    # Interest
        2000,   # Tax
        8100    # Net Profit
    ],
    "2025": [
        120000, # Gross Sales (20% growth)
        -2200,
        -1100,
        36000,
        80700,
        0,
        6000,   # Marketing (Increased)
        28000,  # Salaries (Increased)
        5500,
        2500,
        600,
        250,
        12500,  # Rent (Small increase)
        2200,
        1100,
        1000,   # Professional (Decreased)
        1300,
        1000,
        61950,  # Total Opex
        18750,  # EBIT
        450,    # Interest (Decreased)
        3500,   # Tax
        14800   # Net Profit
    ]
}

df = pd.DataFrame(data)

# Create a writer object
file_name = "sample_financial_data.xlsx"
sheet_name = "5 YEARS_Annual Profit and Loss"

try:
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        # Write generic info in first few rows
        start_row = 5
        
        # Write the dataframe headers and data
        df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)
        
        # Access the worksheet to add some "Report Header" text above
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        
        worksheet['A1'] = "Financial Performance Report"
        worksheet['A2'] = "Company: Demo Corp"
        worksheet['A3'] = "Currency: USD"

    print(f"Successfully created '{file_name}' with sheet '{sheet_name}'.")
    
except Exception as e:
    print(f"Error creating file: {e}")

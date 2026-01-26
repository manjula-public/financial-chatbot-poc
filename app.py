import streamlit as st
import pandas as pd
import json
import os
from analyze_data import clean_and_parse_data, get_empty_template
from forecasting import generate_forecast, calculate_summary_metrics, calculate_executive_summary
import plotly.graph_objects as go
import plotly.express as px

# --- Setup Page ---
st.set_page_config(page_title="Financial Chatbot POC", layout="wide")

# --- Session State Initialization ---
if 'data_source' not in st.session_state:
    st.session_state.data_source = None # dataframe

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'manual_data' not in st.session_state:
    st.session_state.manual_data = get_empty_template()

# --- Saving/Loading Persistence ---
SESSION_FILE = "session_data.json"

def save_session():
    data_to_save = {
        "chat_history": st.session_state.chat_history
        # Saving dataframe requires serialization, doing it simply here
    }
    # For dataframe, let's verify if we need to save it to disk for this POC
    # Ideally yes, but let's stick to in-memory for the session unless user clicks "Save"
    with open(SESSION_FILE, 'w') as f:
        json.dump(data_to_save, f)
    st.toast("Session Saved Successfully!")

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            st.session_state.chat_history = data.get("chat_history", [])
        st.toast("Session Loaded!")

# --- Sidebar: Settings ---
with st.sidebar:
    st.title("Settings")
    
    st.subheader("LLM Configuration")
    llm_provider = st.selectbox("Select Provider", ["Google Gemini", "OpenAI", "Local (Ollama)"])
    
    api_key = ""
    if llm_provider != "Local (Ollama)":
        api_key = st.text_input(f"Enter {llm_provider} API Key", type="password")
        os.environ["OPENAI_API_KEY"] = api_key # Temp set for LangChain
    
    st.divider()
    
    st.subheader("Forecast Settings")
    start_year = st.number_input("Start Year", value=2024, step=1)
    end_year = st.number_input("End Year (Forecast Limit)", value=2028, step=1)
    
    st.divider()
    st.subheader("Persistence")
    if st.button("Save Session"):
        save_session()
    if st.button("Load Session"):
        load_session()

# --- Main Interface ---
st.title("💰 Financial Forecasting & Chatbot")

# Tabs for Mode
tab1, tab2, tab3 = st.tabs(["1. Data Input", "2. Analysis & Forecast", "3. Chat Assistant"])

# --- Tab 1: Data Input ---
with tab1:
    st.header("Upload or Enter Data")
    
    input_method = st.radio("Choose Method", ["Excel Upload", "Manual Entry"])
    
    if input_method == "Excel Upload":
        uploaded_file = st.file_uploader("Upload Profit & Loss Excel", type=["xlsx", "xls"])
        if uploaded_file:
            df, error = clean_and_parse_data(uploaded_file)
            if error:
                st.error(f"Error parsing file: {error}")
            else:
                st.success("File uploaded successfully!")
                st.session_state.data_source = df
                st.dataframe(df.head())
                
    elif input_method == "Manual Entry":
        st.info("Enter values for 2024 and 2025. Future years will be forecasted.")
        
        # Editable Grid
        edited_df = st.data_editor(st.session_state.manual_data, num_rows="dynamic", use_container_width=True)
        
        if st.button("Generate Forecast from Grid"):
            st.session_state.manual_data = edited_df
            st.session_state.data_source = edited_df
            st.success("Data loaded for processing!")

# --- Shared Logic: Ensure Data Exists ---
from forecasting import generate_forecast, calculate_summary_metrics, calculate_executive_summary
import plotly.graph_objects as go
import plotly.express as px

# ... (rest of imports)

# ... (inside Shared Logic)
if st.session_state.data_source is not None:
    # Generate Forecast automatically
    forecast_df = generate_forecast(st.session_state.data_source, start_year, end_year)
    summary_df = calculate_summary_metrics(forecast_df)
    exec_summary_df = calculate_executive_summary(forecast_df)
    
    # --- Tab 2: Analysis ---
    with tab2:
        st.header("Financial Analysis & Forecast")
        
        # --- 1. Executive Summary Table ---
        st.subheader("Summary Analysis")
        st.markdown("Detailed breakdown of Revenue, Expenses, and Profitability.")
        
        # Formatting for display
        display_df = exec_summary_df.copy()
        # Format numbers as currency string for display if desired, or let Streamlit handle it
        # Let's use Streamlit's column config for better interactivity
        st.dataframe(
            display_df.style.format("{:,.2f}"),
            use_container_width=True
        )

        st.divider()
        st.subheader("Visual Insights")
        
        # --- 2. Advanced Charts ---
        col_charts_1, col_charts_2 = st.columns(2)
        
        with col_charts_1:
            # Chart A: Trend Analysis (Area Chart)
            # Net Sales vs Total Expenses vs Net Profit
            st.caption("📈 **5-Year Financial Trend**")
            
            # Prepare data for Plotly Express
            trend_data = summary_df.reset_index().rename(columns={"index": "Year"})
            # Melt for multiple lines
            trend_melt = trend_data.melt(id_vars=["Year"], value_vars=["Gross Profit", "Total Expenses", "Net Profit"], var_name="Metric", value_name="Amount")
            
            fig_trend = px.area(trend_melt, x="Year", y="Amount", color="Metric", 
                                color_discrete_map={"Gross Profit": "#2ecc71", "Total Expenses": "#e74c3c", "Net Profit": "#3498db"})
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_charts_2:
             # Chart B: Expense Breakdown (Donut)
             # Get the last forecasted year for the snapshot
             last_year = str(end_year)
             st.caption(f"🍩 **Expense Breakdown ({last_year})**")
             
             # Extract expense rows from original DF for the last year
             # Filter for explicit expense categories
             expense_keys = ["Marketing", "Salaries", "Rent", "Utilities", "Office", "Professional", "Insurance", "Interest", "Taxes"]
             
             # Create a mini dataframe for the pie chart
             pie_data = []
             if 'Category' in forecast_df.columns:
                 for _, row in forecast_df.iterrows():
                     cat = str(row['Category'])
                     if any(k.lower() in cat.lower() for k in expense_keys):
                         val = float(row[last_year]) if last_year in forecast_df.columns else 0
                         if val > 0:
                             pie_data.append({"Category": cat, "Amount": val})
             
             df_pie = pd.DataFrame(pie_data)
             if not df_pie.empty:
                 fig_pie = px.pie(df_pie, values="Amount", names="Category", hole=0.4)
                 fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                 st.plotly_chart(fig_pie, use_container_width=True)
             else:
                 st.info("No detailed expense data found for breakdown.")

        # Chart C: Waterfall (Profit Flow) for Base Year (2024 or Start Year)
        st.divider()
        st.subheader(f"Profitability Waterfall ({start_year})")
        
        try:
            val_sales = exec_summary_df.loc["Net Sales", str(start_year)]
            val_cogs = -abs(exec_summary_df.loc["Direct Cost", str(start_year)]) # COGS is a reduction
            val_opex = -abs(exec_summary_df.loc["Operating Expenses", str(start_year)])
            val_tax_int = -abs(exec_summary_df.loc["Interest", str(start_year)] + exec_summary_df.loc["Taxes", str(start_year)])
            val_net = exec_summary_df.loc["EBIT (Earnings before Interest and Taxes)", str(start_year)] # Approx
            # Actually, let's do: Sales -> COGS -> Gross Profit -> Opex -> EBIT
            
            fig_waterfall = go.Figure(go.Waterfall(
                name = "20", orientation = "v",
                measure = ["relative", "relative", "total", "relative", "total"],
                x = ["Net Sales", "Direct Cost", "Gross Margin", "Opex", "EBIT"],
                textposition = "outside",
                text = [f"{val_sales/1000:.1f}k", f"{val_cogs/1000:.1f}k", f"{val_sales+val_cogs:.1f}", f"{val_opex/1000:.1f}k", f"{(val_sales+val_cogs+val_opex)/1000:.1f}k"],
                y = [val_sales, val_cogs, 0, val_opex, 0],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            # The 'total' measure computes automatically based on previous values? No, Waterfall is tricky.
            # Simpler setup:
            fig_waterfall = go.Figure(go.Waterfall(
                orientation = "v",
                measure = ["absolute", "relative", "total", "relative", "relative", "total"],
                x = ["Net Sales", "Direct Cost", "Gross Margin", "Opex", "Interest/Tax", "Net Result"],
                y = [val_sales, val_cogs, 0, val_opex, val_tax_int, 0],
                connector = {"line":{"color":"rgb(63, 63, 63)"}},
            ))
            
            fig_waterfall.update_layout(title = "Profit Flow Waterfall", showlegend = True)
            st.plotly_chart(fig_waterfall, use_container_width=True)
        except Exception as e:
            st.error(f"Could not generate Waterfall: {e}")


    # --- Tab 3: Chatbot ---
    with tab3:
        st.header("Financial Assistant")
        
        # Chat History Container
        chat_container = st.container()
        
        # Input
        user_input = st.chat_input("Ask something about the data (e.g., 'Why did expenses go up in 2026?')")
        
        # specific prompt for summary
        if st.button("📝 Generate Detailed Summary Analysis"):
             user_input = "Please provide a detailed Executive Summary Analysis of the financial trends, including Revenue, Expenses, and Net Profit projections."
        
        if user_input:
            # 1. User Message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            # 2. AI Response Logic
            response = "I need an API Key to answer intelligently!"
            if api_key or llm_provider == "Local (Ollama)":
                try:
                    from langchain_core.messages import HumanMessage, SystemMessage
                    from langchain_core.prompts import ChatPromptTemplate
                    
                    # Construct Context
                    # Convert dataframe to string/markdown for context
                    context_data = forecast_df.to_markdown()
                    system_prompt = f"""
                    You are a highly skilled financial analyst assistant (CFO level).
                    
                    Your Goal: Analyze the following P&L data and answer the user's question.
                    
                    Data Context:
                    {context_data}
                    
                    Instructions:
                    1. If the user asks for a "Summary Analysis" or "Overview":
                       - Provide a structured Executive Summary.
                       - Highlight Key Trends (Revenue Growth, Expense changes).
                       - Identify Risks or Anomalies.
                       - Provide a specific "Net Profit" analysis.
                    2. Be professional, concise, and use Markdown (bolding, lists) for readability.
                    3. If the data contains forecasts (future years), explicitly mention they are projections.
                    """
                    
                    # Call LLM
                    if llm_provider == "OpenAI":
                        from langchain_openai import ChatOpenAI
                        llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key)
                        res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_input)])
                        response = res.content
                    elif llm_provider == "Local (Ollama)":
                         from langchain_community.chat_models import ChatOllama
                         try:
                             llm = ChatOllama(model="llama2") 
                             res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_input)])
                             response = res.content
                         except Exception as ol_err:
                             if "No connection made" in str(ol_err) or "10061" in str(ol_err):
                                 response = "⚠️ **Ollama is not running.**\nPlease download it from [ollama.com](https://ollama.com) and run `ollama serve` in a terminal, or switch to OpenAI/Gemini in the sidebar."
                             else:
                                 raise ol_err
                    elif llm_provider == "Google Gemini":
                         from langchain_google_genai import ChatGoogleGenerativeAI
                         # API Key should be set in os.environ["GOOGLE_API_KEY"] usually, 
                         # but we can pass it if the library supports it or set env var earlier.
                         os.environ["GOOGLE_API_KEY"] = api_key
                         llm = ChatGoogleGenerativeAI(model="gemini-pro")
                         res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_input)])
                         response = res.content
                         
                except Exception as e:
                    response = f"AI Error: {str(e)}"
            
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Render History
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
else:
    with tab2:
        st.info("Please load data in Tab 1 first.")
    with tab3:
         st.info("Please load data in Tab 1 first.")

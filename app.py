import streamlit as st
import pandas as pd
import json
import os
from analyze_data import clean_and_parse_data, get_empty_template
from forecasting import generate_forecast, calculate_summary_metrics
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
if st.session_state.data_source is not None:
    # Generate Forecast automatically
    forecast_df = generate_forecast(st.session_state.data_source, start_year, end_year)
    summary_df = calculate_summary_metrics(forecast_df)
    
    # --- Tab 2: Analysis ---
    with tab2:
        st.header("Financial Analysis & Forecast")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Forecasted P&L Statement")
            st.dataframe(forecast_df, use_container_width=True)
            
        with col2:
            st.subheader("Key Metrics Trend")
            
            # Simple Line Chart for Net Profit
            if "Net Profit" in summary_df.columns:
                fig = px.line(summary_df, x=summary_df.index, y="Net Profit", title="Net Profit Trend", markers=True)
                st.plotly_chart(fig, use_container_width=True)
        
        # Expense Breakdown Bar Chart (for base year vs last forecast)
        st.subheader("Expense & Revenue Breakdown")
        
        # Prepare data for Plotly
        # We need to reshape slightly for a good stacked bar or grouped bar
        # Let's plot Gross Profit vs Total Expenses
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=summary_df.index, y=summary_df['Gross Profit'], name='Gross Profit'))
        fig_bar.add_trace(go.Bar(x=summary_df.index, y=summary_df['Total Expenses'], name='Total Expenses'))
        fig_bar.update_layout(barmode='group', title="Gross Profit vs Expenses")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Tab 3: Chatbot ---
    with tab3:
        st.header("Financial Assistant")
        
        # Chat History Container
        chat_container = st.container()
        
        # Input
        user_input = st.chat_input("Ask something about the data (e.g., 'Why did expenses go up in 2026?')")
        
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
                    You are a financial analyst assistant. 
                    Analyze the following P&L data and answer the user's question.
                    
                    Data:\n{context_data}
                    
                    Provide concise, professional insights. Use bullet points/markdown.
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

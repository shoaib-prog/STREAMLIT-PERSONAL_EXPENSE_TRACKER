import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from datetime import date
import os
import io
from io import BytesIO
import base64
import plotly.express as px

# ✅ Set page configuration
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)
# --- Sidebar Dark Mode Toggle ---
st.sidebar.markdown("🌓 **Theme Settings**")
dark_mode = st.sidebar.toggle("Dark Mode", value=False)

# --- Define Light and Dark CSS ---
light_theme = """
    .stApp {
        background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #fff0e0;
        border-right: 2px solid #ffb078;
    }
    div[data-testid="metric-container"] {
        background-color: #fff4e6;
        border-left: 5px solid #ffa94d;
    }
"""

dark_theme = """
    .stApp {
        background: #1e1e1e;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #2d2d2d;
        color: white;
        border-right: 1px solid #444;
    }
    div[data-testid="metric-container"] {
        background-color: #2b2b2b;
        border-left: 5px solid #ffb078;
        color: white;
    }
"""

# --- Apply selected theme ---
selected_theme = dark_theme if dark_mode else light_theme
st.markdown(f"<style>{selected_theme}</style>", unsafe_allow_html=True)


# --- Custom Styling ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(120deg, #f6d365 0%, #fda085 100%);
        font-family: 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] {
        background-color: #fff0e0;
        border-right: 2px solid #ffb078;
        padding: 1rem;
    }
    .main-header {
        background: linear-gradient(90deg, #ff8a00, #e52e71);
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        margin-bottom: 30px;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
    }
    button[kind="primary"] {
        background-color: #ff7a59 !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        padding: 0.5em 1em;
    }
    div[data-testid="metric-container"] {
        background-color: #fff4e6;
        border-left: 5px solid #ffa94d;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<h1 style='color:green;'>💰 Personal Expense Tracker</h1>", unsafe_allow_html=True)
st.write("Track your daily expenses easily and visually.")

# --- CSV File Path ---
csv_file = "expenses.csv"

# --- Load or Create CSV File ---
if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])
else:
    df = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])
    df.to_csv(csv_file, index=False)

# --- Expense Form ---
with st.form("expense_form"):
    col1, col2 = st.columns(2)
    date_input = col1.date_input("📅 Date", date.today())
    category = col2.selectbox("🧾 Category", ["Food", "Transport", "Rent", "Shopping", "EMI", "Utilities", "Education", "Medical", "Other"])
    amount = st.number_input("💵 Amount", min_value=0.0, step=0.01)
    note = st.text_input("📝 Note (Optional)")
    submitted = st.form_submit_button("➕ Add Expense")

    if submitted:
        new_data = {"Date": str(date_input), "Category": category, "Amount": amount, "Note": note}
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(csv_file, index=False)
        st.success("✅ Expense added successfully!")

# --- Reload updated data ---
if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
    try:
        expenses = pd.read_csv(csv_file)

        # --- Sidebar Filters ---
        st.sidebar.header("📂 Filters")

        if not expenses.empty:
            min_date = pd.to_datetime(expenses["Date"]).min().date()
            max_date = pd.to_datetime(expenses["Date"]).max().date()

            date_range = st.sidebar.date_input("Filter by Date Range", value=(min_date, max_date))

            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
                expenses["Date"] = pd.to_datetime(expenses["Date"])
                expenses = expenses[
                    (expenses["Date"] >= pd.to_datetime(start_date)) &
                    (expenses["Date"] <= pd.to_datetime(end_date))
                ]

            category_filter = st.sidebar.multiselect("Filter by Category", options=expenses["Category"].unique())
            if category_filter:
                expenses = expenses[expenses["Category"].isin(category_filter)]

            # --- Display Filtered Table ---
            st.subheader("📋 Filtered Expense Data")
            st.dataframe(expenses)

            if not expenses.empty:
                # --- Export to Excel ---
                st.markdown("### 📤 Export Data")
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    expenses.to_excel(writer, index=False, sheet_name='Expenses')

                st.download_button(
                    label="⬇️ Download as Excel",
                    data=buffer.getvalue(),
                    file_name="filtered_expenses.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # --- Total ---
                total = expenses["Amount"].sum()
                st.metric("💰 Total Spent", f"₹ {total:.2f}")

                # --- Monthly Summary ---
                st.markdown("### 📆 Monthly Summary")
                expenses["Month"] = expenses["Date"].dt.to_period("M").astype(str)
                monthly_total = expenses.groupby("Month")["Amount"].sum()
                st.bar_chart(monthly_total)

                # --- Bar Chart ---
                st.subheader("📊 Expense by Category")
                category_sum = expenses.groupby("Category")["Amount"].sum().reset_index()
                fig_bar = px.bar(
                   category_sum,
                   x="Category",
                   y="Amount",
                   color="Category",
                   title="Expenses by Category",
                   template="plotly_dark",
                   text="Amount"
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

                # --- Pie Chart ---
                st.subheader("🧁 Expense Distribution")
                fig_pie = px.pie(
                      category_sum,
                      names="Category",
                      values="Amount",
                      title="Expense Distribution by Category",
                      template="seaborn",
                      hole=0.4
                )
                fig_pie.update_traces(textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

                # --- Summary Insights ---
                st.markdown("### 📈 Summary Insights")
                st.write(f"🧾 Total Expenses: ₹{expenses['Amount'].sum():.2f}")
                st.write(f"📅 Average Daily Spend: ₹{expenses.groupby('Date')['Amount'].sum().mean():.2f}")
                st.write(f"🔝 Highest Spending Category: {expenses.groupby('Category')['Amount'].sum().idxmax()}")
                st.write(f"🕒 Recent Entry: {expenses.sort_values('Date', ascending=False).iloc[0].to_dict()}")

                # --- Additional Excel Download Link ---
                towrite = io.BytesIO()
                downloaded_file = expenses.copy()
                downloaded_file.to_excel(towrite, index=False, sheet_name='Expenses')
                towrite.seek(0)
                b64 = base64.b64encode(towrite.read()).decode()
                link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="expenses.xlsx">📥 Download Full Excel</a>'
                st.markdown(link, unsafe_allow_html=True)

        else:
            st.info("No expenses available to display. Start adding above.")
    except pd.errors.EmptyDataError:
        st.info("Expenses file is currently empty. Add your first expense above.")
else:
    st.info("No expense data found. Add an entry to begin.")

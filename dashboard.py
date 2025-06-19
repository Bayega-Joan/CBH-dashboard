import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Clipboard Health Shift Analysis Dashboard")

# Load Excel files from local paths
view_metrics_file = "data/claim_view_analysis.xlsx"
claim_percent_file = "data/claim_percentage.xlsx"
profitability_file = "data/shift_profitability_analysis.xlsx"
worker_group_file = "data/worker_grouping_analysis.xlsx"

# Helper function to load sheet
@st.cache_data
def load_excel_sheet(uploaded_file, sheet_name):
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        if sheet_name in xls.sheet_names:
            return xls.parse(sheet_name)
    return pd.DataFrame()

st.sidebar.header("View Options")

tabs = st.tabs(["Claim View Metrics", "Claim % by Rate", "Profitability", "Worker Grouping"])

# ---------------- Claim View Metrics ------------------
with tabs[0]:
    if view_metrics_file:
        sheets = ["Overall_Worker_Stats", "Overall_Shift_Stats", "AM_Worker_Stats", "PM_Worker_Stats", "Overnight_Worker_Stats"]
        for sheet in sheets:
            df = load_excel_sheet(view_metrics_file, sheet)
            if not df.empty:
                st.subheader(sheet.replace("_", " "))
                st.dataframe(df)
                if "claim_to_view_ratio" in df.columns:
                    st.plotly_chart(px.histogram(df, x="claim_to_view_ratio", nbins=20, title=f"{sheet} - Claim to View Ratio"))

# ---------------- Claim Percentage ------------------
with tabs[1]:
    if claim_percent_file:
        all_rate_df = load_excel_sheet(claim_percent_file, "All_Rate_Slot_Combos")
        pivot_df = load_excel_sheet(claim_percent_file, "Pivot_Rate_vs_Slot")
        top_df = load_excel_sheet(claim_percent_file, "Top_10_Percent")

        st.subheader("Claim % by Rounded Rate and Slot")
        if not all_rate_df.empty:
            st.dataframe(all_rate_df)
            st.plotly_chart(px.bar(all_rate_df, x="rounded_rate", y="claim_percentage", color="slot", barmode="group", title="Claim % by Rate & Slot"))

        if not top_df.empty:
            st.subheader("Top 10% Rate/Slot by Claim %")
            st.dataframe(top_df)

        if not pivot_df.empty:
            st.subheader("Pivot Table")
            st.dataframe(pivot_df)

# ---------------- Profitability ------------------
with tabs[2]:
    if profitability_file:
        profit_by_slot = load_excel_sheet(profitability_file, "Profit_By_Shift_Type")
        profit_by_rate = load_excel_sheet(profitability_file, "Profit_By_PayRate")

        if not profit_by_slot.empty:
            st.subheader("Profit by Shift Type")
            st.dataframe(profit_by_slot)
            st.plotly_chart(px.bar(profit_by_slot, x="slot", y="total_profit", title="Total Profit by Shift Type"))

        if not profit_by_rate.empty:
            st.subheader("Profit by Pay Rate")
            st.dataframe(profit_by_rate)
            st.plotly_chart(px.line(profit_by_rate, x="rounded_rate", y="total_profit", title="Profit by Rounded Pay Rate"))

# ---------------- Worker Grouping ------------------
with tabs[3]:
    if worker_group_file:
        xls = pd.ExcelFile(worker_group_file)
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            st.subheader(f"Worker Group: {sheet}")
            st.dataframe(df)

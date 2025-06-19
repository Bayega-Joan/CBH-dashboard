import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Clipboard Health Shift Analysis Dashboard")

#Excel files
view_metrics_file = "data/claim_view_analysis.xlsx"
claim_percent_file = "data/claim_percentage.xlsx"
profitability_file = "data/shift_profitability_analysis.xlsx"
worker_group_file = "data/worker_grouping_analysis.xlsx"

#Helper function to load sheet
@st.cache_data
def load_excel_sheet(uploaded_file, sheet_name):
    if uploaded_file is not None:
        xls = pd.ExcelFile(uploaded_file)
        if sheet_name in xls.sheet_names:
            return xls.parse(sheet_name)
    return pd.DataFrame()

st.sidebar.header("View Options")

tabs = st.tabs(["Claim to View Metrics", "Claim % by pay_rate", "Profitability", "Worker Grouping"])

# ---------------- Claim View Metrics ------------------
with tabs[0]:
    if view_metrics_file:
        df_summary = load_excel_sheet(view_metrics_file, "Claim_to_View_Stats")
        if not df_summary.empty:
            st.subheader("Claim to View Summary Metrics by Shift Period")
            st.dataframe(df_summary)

            # Bar chart for claim-to-view ratio
            st.plotly_chart(
                px.bar(
                    df_summary,
                    x="Shift Period",
                    y="Claim-to-View Ratio(Worker)",
                    title="Claim-to-View Ratio by Shift Period"
                )
            )

            # Line chart for views before claim by workers
            st.plotly_chart(
                px.line(
                    df_summary,
                    x="Shift Period",
                    y="Views Before Claim (Worker)",
                    title="Average Views before picking a shift"
                )
            )

            # Line chart for views before claim by shift
            st.plotly_chart(
                px.line(
                    df_summary,
                    x="Shift Period",
                    y="Views Before Claim (Shift)",
                    title="Average Views Before Claim (Shift)"
                )
            )


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
            st.subheader("Top 10% Rates (threshold of 50 offers applied)")
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

        worker_counts = {}
        worker_group_dfs = {}

        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            worker_group_dfs[sheet] = df  
            unique_workers = df['worker_id'].nunique()
            worker_counts[sheet] = unique_workers

        if worker_counts:
            summary_df = pd.DataFrame({
                "Shift Type": list(worker_counts.keys()),
                "Total Workers": list(worker_counts.values())
            })

            st.subheader("Total Workers by Shift Group")
            st.plotly_chart(
                px.bar(
                    summary_df,
                    x="Shift Type",
                    y="Total Workers",
                    title="Distribution of Workers by Dominant Shift Type Chosen",
                    text="Total Workers"
                )
            )

        for sheet, df in worker_group_dfs.items():
            st.subheader(f"Worker Group: {sheet}")
            st.dataframe(df)



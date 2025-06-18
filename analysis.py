import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import math

# ------------------------------------------------------------------------------
# 1.1 On average, how many shifts does a worker view before picking up a shift?
# 1.2 On average, how many views does a shift get before being claimed?
# ------------------------------------------------------------------------------

def calculate_claim_view_metrics(df: pd.DataFrame, output_excel: str = "claim_view_analysis.xlsx", output_txt: str = "claim_view_summary.txt"):
    df.columns = df.columns.str.strip().str.lower()

    time_cols = ['shift_start_at', 'shift_created_at', 'offer_viewed_at', 'claimed_at', 'canceled_at', 'deleted_at']
    for col in time_cols:
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df['slot'] = df['slot'].str.strip().str.upper()

    #Classyfing shift periods depending on assigned slots
    def classify_period_from_slot(slot):
        if slot == 'NOC':
            return 'Overnight'
        elif slot in ['AM', 'MORNING']:
            return 'AM'
        elif slot in ['PM', 'AFTERNOON', 'EVENING']:
            return 'PM'
        else:
            return 'Unknown'

    df['shift_period'] = df['slot'].apply(classify_period_from_slot)

    summary_lines = []

    #Claim to view stats for workers: conversion rate
    def analyze_group(sub_df, label):
        views = sub_df.groupby('worker_id').size()
        claims = sub_df[sub_df['claimed_at'].notnull()].groupby('worker_id').size()

        stats = pd.DataFrame({
            'views': views,
            'claims': claims
        })
        stats['claims'] = stats['claims'].fillna(0)
        stats['claim_to_view_ratio'] = stats['claims'] / stats['views']

        valid = stats[stats['views'] > 0]
        avg_ratio = valid['claim_to_view_ratio'].mean()
        avg_views_per_claim = 1 / avg_ratio if avg_ratio > 0 else float('inf')

        summary_lines.append(f"=== {label.upper()} ===")
        summary_lines.append(f"Average claim-to-view ratio: {avg_ratio:.4f}")
        summary_lines.append(f"Average views before a claim: {avg_views_per_claim:.2f}\n")

        return stats.reset_index().head(100), avg_ratio, avg_views_per_claim
    
    #Claim to view stats for shifts: booking rate
    def analyze_shift_view_counts(sub_df, label):
        claimed_shifts = sub_df[sub_df['claimed_at'].notnull()]
        views_per_shift = sub_df.groupby('shift_id').size()
        shift_claimed_flag = claimed_shifts[['shift_id']].drop_duplicates()

        claimed_views = views_per_shift[views_per_shift.index.isin(shift_claimed_flag['shift_id'])]
        avg_views_per_shift_claim = claimed_views.mean()

        summary_lines.append(f"=== {label.upper()} SHIFT VIEW STATS ===")
        summary_lines.append(f"Average number of views before a shift is claimed: {avg_views_per_shift_claim:.2f}\n")

        return claimed_views.reset_index(name='views_before_claim').head(100)

    with pd.ExcelWriter(output_excel) as writer:
        #Overall worker stats
        sample_all, _, _ = analyze_group(df, 'Overall')
        sample_all.to_excel(writer, sheet_name='Overall_Worker_Stats', index=False)

        #Overall shift stats
        shift_sample_overall = analyze_shift_view_counts(df, 'Overall')
        shift_sample_overall.to_excel(writer, sheet_name='Overall_Shift_Stats', index=False)

        #Per shift period analysis
        for period in ['AM', 'PM', 'Overnight']:
            subset = df[df['shift_period'] == period]

            sample_worker, _, _ = analyze_group(subset, period)
            sample_worker.to_excel(writer, sheet_name=f'{period}_Worker_Stats', index=False)

            shift_sample = analyze_shift_view_counts(subset, period)
            shift_sample.to_excel(writer, sheet_name=f'{period}_Shift_Stats', index=False)

    #Save summary to TXT file
    with open(output_txt, 'w') as f:
        for line in summary_lines:
            f.write(line + '\n')

    print(f"\nSummary saved to: {output_txt}")
    print(f"Results saved to: {output_excel}")

#Load data and run the Claim-view analysis
df = pd.read_excel("problem.xlsx", engine="openpyxl")
calculate_claim_view_metrics(df)

# ------------------------------------------------------------------------------
# 2. At which pay_rate are claims made the most?
# ------------------------------------------------------------------------------

def analyze_claim_percentage_by_rate_and_slot(df: pd.DataFrame, output_excel: str = "claim_percentage.xlsx", rate_col: str = "pay_rate"):
    
    df.columns = df.columns.str.strip().str.lower()
    df['rounded_rate'] = df[rate_col].round(0).astype(int)
    df['slot'] = df['slot'].str.strip().str.upper()
    df['is_claimed'] = df['claimed_at'].notnull()

    grouped = df.groupby(['rounded_rate', 'slot']).agg(
        total_offers=('worker_id', 'count'),
        total_claims=('is_claimed', 'sum')
    ).reset_index()
    grouped['claim_percentage'] = (grouped['total_claims'] / grouped['total_offers']) * 100

    threshold = 50
    grouped_filtered = grouped[grouped['total_offers'] >= threshold]

    grouped_sorted = grouped_filtered.sort_values('claim_percentage', ascending=False)
    top_n = math.ceil(len(grouped_sorted) * 0.10)
    top_pairs = grouped_sorted.head(top_n)[['rounded_rate', 'slot']]
    top_grouped = pd.merge(grouped, top_pairs, on=['rounded_rate', 'slot'], how='inner')

    #Pivot table for visual overview
    pivot = grouped.pivot(index='rounded_rate', columns='slot', values='claim_percentage').fillna(0).round(2)

    #Overall summary by rounded_rate 
    overall = df.groupby('rounded_rate').agg(
        total_offers=('worker_id', 'count'),
        total_claims=('is_claimed', 'sum')
    ).reset_index()
    overall['claim_percentage'] = (overall['total_claims'] / overall['total_offers']) * 100

    #Save to Excel
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        grouped.to_excel(writer, sheet_name="All_Rate_Slot_Combos", index=False)
        top_grouped.to_excel(writer, sheet_name="Top_10_Percent", index=False)
        pivot.to_excel(writer, sheet_name="Pivot_Rate_vs_Slot", index=True)
        overall.to_excel(writer, sheet_name="Overall_By_Rate", index=False)

    print(f"Workbook saved to '{output_excel}'.")

# ------------------------------------------------------------------------------
# 3. What has been the most profitable pay_rate and shift slot
# ------------------------------------------------------------------------------

def analyze_shift_profitability(df: pd.DataFrame, output_excel: str = "shift_profitability_analysis.xlsx", output_txt: str = "shift_profitability_summary.txt"):
    
    df.columns = df.columns.str.strip().str.lower()
    claimed = df[df['claimed_at'].notnull()].copy()
    claimed['slot'] = claimed['slot'].str.strip().str.upper()
    claimed['rounded_rate'] = claimed['pay_rate'].round(0).astype(int)
    claimed['profit'] = (claimed['charge_rate'] - claimed['pay_rate']) * claimed['duration']

    #Group by shift slot
    profit_by_slot = claimed.groupby('slot').agg(
        total_profit=('profit', 'sum'),
        average_profit_per_shift=('profit', 'mean'),
        number_of_claims=('worker_id', 'count')
    ).reset_index()

    #Group by rounded pay rate
    profit_by_rate = claimed.groupby('rounded_rate').agg(
        total_profit=('profit', 'sum'),
        number_of_claims=('worker_id', 'count'),
        average_profit_per_shift=('profit', 'mean')
    ).reset_index().sort_values('total_profit', ascending=False)

    most_profitable_slot = profit_by_slot.sort_values('total_profit', ascending=False).iloc[0]
    most_profitable_rate = profit_by_rate.iloc[0]

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        claimed[['shift_id', 'slot', 'pay_rate', 'charge_rate', 'duration', 'profit', 'rounded_rate']].to_excel(writer, sheet_name="Claimed_Offers_Profit", index=False)
        profit_by_slot.to_excel(writer, sheet_name="Profit_By_Shift_Type", index=False)
        profit_by_rate.to_excel(writer, sheet_name="Profit_By_PayRate", index=False)

    with open(output_txt, 'w') as f:
        f.write(f"Profitability Summary\n")
        f.write(f"Most profitable shift type: {most_profitable_slot['slot']} (${most_profitable_slot['total_profit']:.2f} total profit)\n")
        f.write(f"Most profitable pay rate: ${most_profitable_rate['rounded_rate']} (${most_profitable_rate['total_profit']:.2f} total profit)\n")

    print(f" Profitability analysis saved to '{output_excel}' and summary saved to '{output_txt}'")

# ------------------------------------------------------------------------------
# 4. How are the workers distributed by the different shift slots?
# ------------------------------------------------------------------------------

def group_workers_by_shift_period(df: pd.DataFrame, output_excel: str = "worker_grouping_analysis.xlsx", output_txt: str = "worker_grouping_summary.txt"):
    
    df.columns = df.columns.str.strip().str.lower()
    df['slot'] = df['slot'].str.strip().str.upper()
    df['shift_period'] = df['slot']

    claimed = df[df['claimed_at'].notnull()]
    worker_period_counts = claimed.groupby(['worker_id', 'shift_period']).size().unstack(fill_value=0)
    worker_period_counts['dominant_period'] = worker_period_counts.idxmax(axis=1)

    df = df.merge(worker_period_counts['dominant_period'], on='worker_id', how='left')
    df.rename(columns={'dominant_period': 'worker_group'}, inplace=True)

    claimed_with_group = df[df['claimed_at'].notnull()]
    groups = claimed_with_group['worker_group'].dropna().unique()

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        for group in groups:
            group_df = claimed_with_group[claimed_with_group['worker_group'] == group]
            group_df.to_excel(writer, sheet_name=str(group)[:31], index=False)

    group_counts = claimed_with_group.groupby('worker_group')['worker_id'].nunique()

    with open(output_txt, 'w') as f:
        f.write("Worker Group Counts (Claimed Shifts Only):\n")
        for group, count in group_counts.items():
            f.write(f"{group}: {count} workers\n")

    print(f"Worker group file saved to '{output_excel}'")
    print(f"Worker group summary saved to '{output_txt}'")

# ------------------------------------------------------------------------------
#   Data Load and Analyis
# ------------------------------------------------------------------------------
df = pd.read_excel("problem.xlsx", engine="openpyxl")
calculate_claim_view_metrics(df)
analyze_claim_percentage_by_rate_and_slot(df)
analyze_shift_profitability(df)
group_workers_by_shift_period(df)

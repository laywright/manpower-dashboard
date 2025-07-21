import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Load data
uploaded_file = st.file_uploader("Upload the Excel file", type="xlsx")
if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Manhours")
    df.columns = df.columns.str.strip()
    bus_columns = [col for col in df.columns if col.startswith('Bus')]

    # ---------- 1. MANHOURS PER BUS ----------
    df['Total_Per_Process'] = df[bus_columns].sum(axis=1)
    total_hours_per_bus = df[bus_columns].sum()
    buses = total_hours_per_bus.index.str.replace('Bus ', '')
    df_bus_total = pd.DataFrame({'Bus': buses, 'Manhours': total_hours_per_bus.values})

    st.subheader("1. Total Manhours per Bus")
    fig1 = px.bar(df_bus_total, x='Bus', y='Manhours', title='Manhours per Bus')
    st.plotly_chart(fig1)

    avg_manhours = df_bus_total['Manhours'].mean()
    top5_buses = df_bus_total.sort_values(by='Manhours', ascending=False).head(5)
    st.markdown(f"**Average manhours per bus:** {avg_manhours:.1f} hours")
    st.markdown("**Top 5 buses with highest manhours:**")
    st.dataframe(top5_buses)

    # ---------- 2. AVERAGE TIME PER PROCESS ----------
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    avg_process_df = df[['Process', 'Station', 'Avg_Time_Per_Process']].copy()
    avg_process_df = avg_process_df.sort_values(by='Avg_Time_Per_Process', ascending=False)
    fig2 = px.bar(avg_process_df, x='Process', y='Avg_Time_Per_Process', color='Station',
                 title='Average Time Taken per Process', height=600)
    st.subheader("2. Average Time per Process")
    st.plotly_chart(fig2)

    overall_avg = avg_process_df['Avg_Time_Per_Process'].mean()
    st.markdown(f"**Overall average process time:** {overall_avg:.1f} hours")
    st.markdown("**Top 7 bottleneck processes:**")
    st.dataframe(avg_process_df.head(7))

    # ---------- 3. OUTLIER DETECTION ----------
    z_scores = (df[bus_columns] - df[bus_columns].mean(axis=1).values[:, None]) / df[bus_columns].std(axis=1).values[:, None]
    outliers_df = df[['Process', 'Station']].copy()
    for bus in bus_columns:
        outliers_df[bus] = z_scores[bus] > 2

    outlier_long = outliers_df.melt(id_vars=['Process', 'Station'], var_name='Bus', value_name='Is_Outlier')
    outlier_long = outlier_long[outlier_long['Is_Outlier']]

    st.subheader("3. Outlier Detection")
    st.markdown(f"**Total outlier occurrences:** {len(outlier_long)}")
    st.dataframe(outlier_long[['Station', 'Process', 'Bus']])

    # ---------- 4. CYCLE TIME ----------
    cycle_times_df = pd.DataFrame({
        'Bus': buses,
        'Cycle Time (hours)': df[bus_columns].sum().values
    })
    fig3 = px.line(cycle_times_df, x='Bus', y='Cycle Time (hours)', markers=True,
                   title='Cycle Time per Bus')
    st.subheader("4. Cycle Time Analysis")
    st.plotly_chart(fig3)

    avg_cycle = cycle_times_df['Cycle Time (hours)'].mean()
    st.markdown(f"**Average cycle time per bus:** {avg_cycle:.1f} hours")
    st.markdown("**Top 3 buses with longest cycle times:**")
    st.dataframe(cycle_times_df.sort_values(by='Cycle Time (hours)', ascending=False).head(3))

    # ---------- 5. RESOURCE ALLOCATION GAPS ----------
    df['Time_per_person'] = df['Total_Per_Process'] / df['Number of people']
    gap_df = df[['Station', 'Process', 'Number of people', 'Total_Per_Process', 'Time_per_person']]
    gap_df = gap_df.sort_values(by='Time_per_person', ascending=False)

    fig4 = px.bar(gap_df.head(10), x='Process', y='Time_per_person', color='Station',
                 title='Top 10 Resource Allocation Gaps')
    st.subheader("5. Resource Allocation Gaps")
    st.plotly_chart(fig4)

    st.markdown("**Top 5 processes with highest time per person:**")
    st.dataframe(gap_df.head(5))

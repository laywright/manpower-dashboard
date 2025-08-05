import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

st.set_page_config(page_title="🚌 BasiGo Manpower Dashboard", layout="wide")
st.title("🚌 BasiGo Manpower Dashboard")

uploaded_file = st.file_uploader("📤 Upload the Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="Manhours")

    # Identify relevant bus columns
    bus_columns = [col for col in df.columns if str(col).startswith("Bus")]

    st.subheader("📊 Total Manhours per Bus")
    total_hours = df[bus_columns].sum()
    buses = total_hours.index.str.extract(r'(Bus\s*\d+)')[0]
    df_manhours = pd.DataFrame({'Bus': buses, 'Hours': total_hours.values})
    df_manhours = df_manhours.sort_values(by='Hours', ascending=False)

    fig1 = px.bar(df_manhours, x='Bus', y='Hours', title="<b>Total Manhours per Bus</b>",
                  labels={'Bus': 'Bus Number', 'Hours': 'Total Hours'}, color_discrete_sequence=['green'])
    fig1.update_layout(hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    avg_manhours = df_manhours['Hours'].mean()
    st.markdown(f"**📊 The average total manhours per bus is:** `{avg_manhours:.1f}` hours.")
    st.markdown("**🚨 Top 5 buses with the highest labor demand:**")
    for _, row in df_manhours.head(5).iterrows():
        st.markdown(f"• **{row['Bus']}** — `{row['Hours']:.1f}` hours")

    # Process Time Analysis
    st.subheader("⏱️ Average Time Taken per Process")
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    avg_process_df = df[['Station', 'Process', 'Avg_Time_Per_Process']].sort_values(by='Avg_Time_Per_Process', ascending=False)
    fig2 = px.bar(avg_process_df, x='Process', y='Avg_Time_Per_Process', color='Avg_Time_Per_Process',
                  title='⏱️ Average Time Taken per Process Across All Buses',
                  labels={'Avg_Time_Per_Process': 'Average Time (hours)'}, color_continuous_scale='Cividis')
    fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified", coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

    overall_avg = avg_process_df['Avg_Time_Per_Process'].mean()
    st.markdown(f"**📊 The overall average process time across all buses is:** `{overall_avg:.1f}` hours.")
    st.markdown("**🚨 Top 7 Time Bottlenecks:**")
    for _, row in avg_process_df.head(7).iterrows():
        st.markdown(f"• **{row['Process']}**: `{row['Avg_Time_Per_Process']:.1f}` hours")

    # KPI comparison table
    st.subheader("📐 Process Time vs KPI Targets")
    kpi_data = {
        'Station': ['Chassis', 'Body', 'Metal Finishing', 'Paint', 'Trim', 'EOL'],
        'KPI_Hours': [8, 80, 24, 24, 56, 16]
    }
    kpi_df = pd.DataFrame(kpi_data)
    process_kpi_df = df.groupby('Station')['Avg_Time_Per_Process'].mean().reset_index()
    kpi_comparison_df = pd.merge(kpi_df, process_kpi_df, on='Station')
    kpi_comparison_df['% Deviation'] = ((kpi_comparison_df['Avg_Time_Per_Process'] - kpi_comparison_df['KPI_Hours']) / kpi_comparison_df['KPI_Hours']) * 100
    kpi_comparison_df = kpi_comparison_df.rename(columns={'Avg_Time_Per_Process': 'Current Avg Hours'})
    st.dataframe(kpi_comparison_df.style.format({"Current Avg Hours": "{:.1f}", "KPI_Hours": "{:.1f}", "% Deviation": "{:+.1f}%"}))

    # Outlier Detection
    st.subheader("🚨 Outlier Processes")
    df['Variance'] = df[bus_columns].var(axis=1)
    top_var_df = df.nlargest(7, 'Variance')[['Station', 'Process']].drop_duplicates()
    df_long_outliers = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                               var_name='Bus', value_name='Hours')
    df_long_outliers = df_long_outliers.merge(top_var_df, on=['Station', 'Process'])
    df_long_outliers['Avg Hours per Process'] = df_long_outliers.groupby('Process')['Hours'].transform('mean')
    df_long_outliers['Z_Score'] = df_long_outliers.groupby('Process')['Hours'].transform(
        lambda x: (x - x.mean()) / x.std(ddof=0))
    outliers_table_df = df_long_outliers[df_long_outliers['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)

    if outliers_table_df.empty:
        st.info("✅ No significant outliers found.")
    else:
        st.dataframe(outliers_table_df[['Bus', 'Station', 'Process', 'Hours', 'Avg Hours per Process']])

    # Cycle Time
    st.subheader("🔁 Cycle Time vs Target")
    cycle_kpis = pd.DataFrame({
        'Station': ['Chassis', 'Body', 'Metal Finishing', 'Paint', 'Trim', 'EOL'],
        'Target Cycle Time (hrs)': [8, 80, 24, 24, 56, 16]
    })
    actual_cycle_time = df.groupby('Station')[bus_columns].sum().mean(axis=1).reset_index()
    actual_cycle_time.columns = ['Station', 'Actual Cycle Time (hrs)']
    cycle_comparison = pd.merge(cycle_kpis, actual_cycle_time, on='Station')
    cycle_comparison['Deviation %'] = ((cycle_comparison['Actual Cycle Time (hrs)'] - cycle_comparison['Target Cycle Time (hrs)']) / cycle_comparison['Target Cycle Time (hrs)']) * 100
    st.dataframe(cycle_comparison.style.format({"Target Cycle Time (hrs)": "{:.1f}", "Actual Cycle Time (hrs)": "{:.1f}", "Deviation %": "{:+.1f}%"}))

    # Human Resource Allocation Gaps
    st.subheader("👷 Human Resource Allocation Gaps")
    df['Total_Hours'] = df[bus_columns].sum(axis=1)
    resource_gap_df = df.groupby('Station')['Total_Hours'].sum().reset_index()
    resource_gap_df = resource_gap_df.sort_values(by='Total_Hours', ascending=False)
    fig5 = px.bar(resource_gap_df, x='Station', y='Total_Hours', title='👷 Total Manhours by Station',
                 labels={'Total_Hours': 'Manhours'}, color='Total_Hours', color_continuous_scale='sunset')
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("**🚨Processes with highest Human resource allocation gaps:**")
    for _, row in resource_gap_df.head(5).iterrows():
        st.markdown(f"• **{row['Station']}** — `{row['Total_Hours']:.1f}` hours")

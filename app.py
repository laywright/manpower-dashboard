import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

st.set_page_config(
    page_title="BasiGo Manpower Dashboard",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌 BasiGo Manpower Dashboard")

uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

if uploaded_file is not None:
    # Load and clean data
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')
    df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())

    # Ensure numeric conversion
    df['Number of people'] = pd.to_numeric(df.get('Number of people', pd.Series(dtype=float)), errors='coerce')

    # Get only bus columns and exclude Bus21 to Bus24
    bus_columns = [col for col in df.columns if str(col).startswith('Bus') and col not in ['Bus 21', 'Bus 22', 'Bus 23', 'Bus 24']]

    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Manhours per person'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    buses = bus_columns
    total_hours = df[bus_columns].multiply(df['Number of people'], axis=0).sum()
    total_df = pd.DataFrame({'Bus': buses, 'Manhours': total_hours.values})
    avg_manhours = total_df['Manhours'].mean()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Summary", "Process time analysis", "Human resource allocation gaps"])

    # -------------------- TAB 1 --------------------
    with tab1:
        st.subheader("Total manhours summary")
        st.metric("Average total manhours per bus", f"{avg_manhours:.1f} hrs")

        selected_bus = st.selectbox("View Manhours for specific bus", buses)
        st.write(f"**{selected_bus} Manhours:** {total_hours[selected_bus]:.1f} hrs")

        fig1 = px.bar(total_df, x='Bus', y='Manhours', title="Total manhours per bus",
                      labels={'Bus': 'Bus', 'Manhours': 'Total Manhours'},
                      color_discrete_sequence=['green'], text='Manhours')
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        top5 = total_df.sort_values(by='Manhours', ascending=False).head(5)
        st.markdown("**🚨 Top 5 buses with highest manhours:**")
        for _, row in top5.iterrows():
            st.markdown(f"• {row['Bus']}: {row['Manhours']:.1f} manhours")

        st.download_button("📥  Download total manhours CSV", total_df.to_csv(index=False).encode(),
                           file_name="total_manhours.csv", mime='text/csv')

        # -------------------- KPI Comparison --------------------
        st.subheader("📊 KPI vs Actual Process Time by Station")

        # Define KPIs
        station_kpis = {
            'Chassis': 8,
            'Body': 80,
            'Metal Finish': 24,
            'Paint': 24,
            'Trim': 56,
            'EOL': 16
        }
        manhour_kpi = 1400

        # Melt bus columns to long format
        df_long_kpi = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                              var_name='Bus', value_name='Manhours')

        # Calculate total time per station across all buses
        station_totals = df_long_kpi.groupby('Station')['Manhours'].sum()
        num_buses = len(bus_columns)
        station_avg_times = (station_totals / num_buses).to_dict()

        # Build comparison table
        comparison_data = []
        for station, kpi_time in station_kpis.items():
            actual_time = station_avg_times.get(station, np.nan)
            percent_used = (actual_time / kpi_time * 100) if pd.notna(actual_time) else np.nan
            comparison_data.append({
                'Station': station,
                'KPI Time (hrs)': kpi_time,
                'Actual Avg Time (hrs)': round(actual_time, 2) if pd.notna(actual_time) else 'N/A',
                '% of KPI Used': f"{round(percent_used, 1)}%" if pd.notna(percent_used) else 'N/A'
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df)

        # Manhour KPI comparison
        st.markdown("**🧮 Total Manhours KPI Comparison**")
        st.metric("KPI Target", f"{manhour_kpi} hrs")
        st.metric("Actual Avg Total Manhours", f"{avg_manhours:.1f} hrs")
        st.metric("% of KPI Used", f"{(avg_manhours / manhour_kpi * 100):.1f}%")

    # -------------------- TAB 2 --------------------
    with tab2:
        st.subheader("Average time per process (Overall)")
        process_avg_df = df[['Process', 'Avg_Time_Per_Process']].dropna()
        process_avg_df = process_avg_df[process_avg_df['Process'].str.strip() != '']
        process_avg_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig2 = px.bar(process_avg_df, x='Process', y='Avg_Time_Per_Process',
                      title='Average Time per Process Across All Buses',
                      labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                      color_discrete_sequence=['green'], text='Avg_Time_Per_Process')
        fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified", width=1200, height=600)
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**🚨 Top 7 longest processes:**")
        for _, row in process_avg_df.head(7).iterrows():
            st.markdown(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hrs")

        if 'Station' in df.columns:
            station_options = df['Station'].dropna().unique().tolist()
            if station_options:
                selected_station = st.selectbox("Select Station for Average Process Time", station_options, key='station_avg')
                station_avg_df = df[df['Station'] == selected_station][['Process', 'Avg_Time_Per_Process']]
                station_avg_df = station_avg_df.dropna().sort_values(by='Avg_Time_Per_Process', ascending=False)

                fig_station = px.bar(station_avg_df, x='Process', y='Avg_Time_Per_Process',
                                     title=f'Average Time per Process in {selected_station} Station',
                                     labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                                     color_discrete_sequence=['green'], text='Avg_Time_Per_Process')
                fig_station.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
                st.plotly_chart(fig_station, use_container_width=True)

        # Outlier Detection Table
        st.subheader("🚨 Outlier Processes")

        top_var_df = df.nlargest(7, 'Variance')[['Station', 'Process']].drop_duplicates()
        df_long_outliers = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                                   var_name='Bus', value_name='Hours')
        outliers_merged = df_long_outliers.merge(top_var_df, on=['Station', 'Process'])
        outliers_merged['Average Hours per Process'] = outliers_merged.groupby('Process')['Hours'].transform('mean')
        outliers_merged['Z_Score'] = outliers_merged.groupby('Process')['Hours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_table_df = outliers_merged[outliers_merged['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)

        if outliers_table_df.empty:
            st.info("✅ No significant outliers found in the top 7 high-variance processes.")
        else:
            st.dataframe(outliers_table_df[['Bus', 'Station', 'Process', 'Hours', 'Average Hours per Process']])

    # -------------------- TAB 3 --------------------
    with tab3:
        st.subheader("Human resource allocation gaps")

        gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']].copy()
        gap_df = gap_df.dropna(subset=['Process'])
        gap_df = gap_df[gap_df['Process'].str.strip() != '']
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

        station_colors = {
            'Trim': 'red',
            'Logistics': 'blue',
            'Chassis': 'purple',
            'Body': 'orange',
            'Metal Finish': 'teal

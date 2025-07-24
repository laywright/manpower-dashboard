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
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')
    df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())
    df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')
    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]

    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Manhours per person'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    buses = bus_columns
    total_hours = df[bus_columns].multiply(df['Number of people'], axis=0).sum()
    total_df = pd.DataFrame({'Bus': buses, 'Manhours': total_hours.values})
    avg_manhours = total_df['Manhours'].mean()

    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Process time analysis", "Human resource allocation gaps", "📥 Downloads"])

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
        st.markdown("**🚨 Top 5 buses with highest manhours :**")
        for _, row in top5.iterrows():
            st.markdown(f"• {row['Bus']}: {row['Manhours']:.1f} manhours")

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

        st.markdown("**🚨 Top 7 time bottlenecks:**")
        for _, row in process_avg_df.head(7).iterrows():
            st.markdown(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hrs")

        # Station-based breakdown toggle
        station_options = df['Station'].dropna().unique().tolist()
        selected_station = st.selectbox("Select Station for Average Process Time", station_options, key='station_avg')
        station_avg_df = df[df['Station'] == selected_station][['Process', 'Avg_Time_Per_Process']]
        station_avg_df = station_avg_df.dropna().sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig_station = px.bar(station_avg_df, x='Process', y='Avg_Time_Per_Process',
                            title=f'Average Time per Process in {selected_station} Station',
                            labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                            color_discrete_sequence=['green'], text='Avg_Time_Per_Process')
        fig_station.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
        st.plotly_chart(fig_station, use_container_width=True)

        # Outlier table integration
        st.subheader("🚨 Outlier Processes (High Variance)")
        top_var_df = df.nlargest(7, 'Variance')[['Station', 'Process']].drop_duplicates()
        df_long_outliers = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                                   var_name='Bus', value_name='Manhours')
        outliers_merged = df_long_outliers.merge(top_var_df, on=['Station', 'Process'])
        outliers_merged['Avg_Manhours_Process'] = outliers_merged.groupby('Process')['Manhours'].transform('mean')
        outliers_merged['Z_Score'] = outliers_merged.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_table_df = outliers_merged[outliers_merged['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)

        if outliers_table_df.empty:
            st.info("No significant outliers found.")
        else:
            st.dataframe(outliers_table_df[['Bus', 'Station', 'Process', 'Manhours', 'Avg_Manhours_Process']])

    with tab3:
        st.subheader("Human resource allocation gaps")
        gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']]
        gap_df = gap_df.dropna(subset=['Process'])
        gap_df = gap_df[gap_df['Process'].str.strip() != '']

        station_gap = st.selectbox("Choose Station to Analyze HR Gaps", station_options, key='station_gap')
        filtered_gap_df = gap_df[gap_df['Station'] == station_gap].sort_values(by='Manhours per person', ascending=False)

        # Display insights table
        st.subheader(f"🚨 HR Allocation Gaps in {station_gap} Station")
        st.dataframe(filtered_gap_df[['Station', 'Process', 'Manhours per person', 'Number of people']])

        # Chart visualization
        fig4 = px.bar(filtered_gap_df, x='Process', y='Manhours per person', color='Station',
                      title=f'HR Allocation Gaps in {station_gap}',
                      labels={'Manhours per person': 'Manhours/Person'},
                      text='Manhours per person',
                      color_discrete_sequence=['green'])
        fig4.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
        st.plotly_chart(fig4, use_container_width=True)

    with tab4:
        st.subheader("📥 Downloads")
        st.download_button("Download total manhours CSV", total_df.to_csv(index=False).encode(), file_name="total_manhours.csv", mime='text/csv')
        st.download_button("Download process averages CSV", process_avg_df.to_csv(index=False).encode(), file_name="process_avg.csv", mime='text/csv')
        if not outliers_table_df.empty:
            st.download_button("Download Outlier Table CSV", outliers_table_df.to_csv(index=False).encode(), file_name="outlier_table.csv", mime='text/csv')
        st.download_button(f"Download HR Gaps CSV ({station_gap})", filtered_gap_df.to_csv(index=False).encode(), file_name=f"{station_gap.lower()}_hr_gaps.csv", mime='text/csv')

else:
    st.info("Please upload a valid Excel file to proceed.")

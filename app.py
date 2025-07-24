import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
from scipy import stats

st.set_page_config(
    page_title="BasiGo Manpower Dashboard",
    page_icon="🚌",
    layout="wide"
)

# -----------------------------
# Upload Excel File
# -----------------------------

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

    # -----------------------------
    # Tabs Layout
    # -----------------------------
    tab1, tab2, tab3 = st.tabs(["Summary", "Process time analysis", "Human resource allocation gaps"])

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

        st.download_button("📥 Download total manhours CSV", total_df.to_csv(index=False).encode(),
                           file_name="total_manhours.csv", mime='text/csv')

    with tab2:
        st.subheader("Average time per process")

        stations = df['Station'].dropna().unique()
        selected_station = st.selectbox("Select a station", stations)
        station_df = df[df['Station'] == selected_station]

        station_avg_df = station_df[['Process', 'Avg_Time_Per_Process']].dropna()
        station_avg_df = station_avg_df[station_avg_df['Process'].str.strip() != '']
        station_avg_df = station_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig_station = px.bar(station_avg_df, x='Process', y='Avg_Time_Per_Process',
                     title=f'Average Time per Process - {selected_station}',
                     labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                     color_discrete_sequence=['green'], text='Avg_Time_Per_Process')
        fig_station.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified",
                           coloraxis_showscale=False, width=1200, height=600)
        st.plotly_chart(fig_station, use_container_width=True)

        st.download_button("📥 Download process averages CSV", station_avg_df.to_csv(index=False).encode(),
                           file_name=f"process_avg_{selected_station}.csv", mime='text/csv')

        st.markdown("**🚨 Top 7 time bottlenecks:**")
        for _, row in station_avg_df.head(7).iterrows():
            st.markdown(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hrs")

        # Outlier Table (instead of separate tab)
        st.markdown("### 🚨 Outliers Table")
        df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                          var_name='Bus', value_name='Manhours')
        df_long = df_long.merge(df[['Station', 'Process', 'Avg_Time_Per_Process']], on=['Station', 'Process'])
        df_long['Z_Score'] = df_long.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_df = df_long[df_long['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)[
            ['Bus', 'Station', 'Process', 'Manhours', 'Avg_Time_Per_Process']]

        if outliers_df.empty:
            st.info("No strong outliers detected.")
        else:
            st.dataframe(outliers_df)

        st.download_button("📥 Download Outliers CSV", outliers_df.to_csv(index=False).encode(),
                           file_name="outliers.csv", mime='text/csv')

    with tab3:
        st.subheader("Human resource allocation gaps")

        hr_station = st.selectbox("Select a station for HR insights", stations, key='hr_station')
        gap_df = df[df['Station'] == hr_station][['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']]
        gap_df = gap_df.dropna(subset=['Process'])
        gap_df = gap_df[gap_df['Process'].str.strip() != '']
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

        station_colors = {
            'Trim': 'red',
            'Logistics': 'blue',
            'Chassis': 'purple',
            'Body': 'orange',
            'Metal Finish': 'teal',
            'Paint': 'pink',
            'EOL': 'gray'
        }

        fig4 = px.bar(gap_df, x='Process', y='Manhours per person', color='Station',
                      title=f'HR Allocation Gaps - {hr_station}',
                      labels={'Manhours per person': 'Manhours/Person'},
                      text='Manhours per person',
                      color_discrete_map=station_colors)
        fig4.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
        st.plotly_chart(fig4, use_container_width=True)

        st.dataframe(gap_df[['Station', 'Process', 'Manhours per person', 'Number of people']])

        st.download_button("📥 Download HR gaps CSV", gap_df.to_csv(index=False).encode(),
                           file_name=f"hr_gaps_{hr_station}.csv", mime='text/csv')

        st.markdown("**🚨 Top Human resource allocation gaps:**")
        for _, row in gap_df.head(7).iterrows():
            st.markdown(f"• {row['Process']} ({row['Station']}): {row['Manhours per person']:.2f} hrs/person, {row['Number of people']} people")
else:
    st.info("Please upload a valid Excel file to proceed.")

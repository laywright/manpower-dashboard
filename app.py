import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
from scipy import stats

st.set_page_config(page_title="🚌 BasiGo Manpower Dashboard", layout="wide")
st.title("🚌 BasiGo Manpower Dashboard")

# -----------------------------
# Upload Excel File
# -----------------------------
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

    tab1, tab2, tab3 = st.tabs(["📊 Summary", "⏱️ Process Time Analysis", "👷 HR Allocation Gaps"])

    with tab1:
        st.subheader("📊 Total Manhours Summary")
        st.metric("Average Total Manhours per Bus", f"{avg_manhours:.1f} hrs")

        selected_bus = st.selectbox("🔍 View Manhours for Specific Bus", buses)
        st.write(f"**{selected_bus} Manhours:** {total_hours[selected_bus]:.1f} hrs")

        fig1 = px.bar(total_df, x='Bus', y='Manhours', title="Total Manhours per Bus",
                     labels={'Bus': 'Bus', 'Manhours': 'Total Manhours'},
                     color_discrete_sequence=['green'], text='Manhours')
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        top5 = total_df.sort_values(by='Manhours', ascending=False).head(5)
        st.markdown("**🚨 Top 5 Buses with Highest Labor Demand:**")
        for _, row in top5.iterrows():
            st.markdown(f"• {row['Bus']}: {row['Manhours']:.1f} manhours")

        st.download_button("📥 Download Total Manhours CSV", total_df.to_csv(index=False).encode(),
                           file_name="total_manhours.csv", mime='text/csv')

    with tab2:
        st.subheader("⏱️ Average Time per Process by Station")
        stations = ['Chassis', 'Body', 'Metal Finish', 'Paint', 'Trim', 'EOL']
        station_choice = st.selectbox("🏭 Select Station", stations, key='station_toggle')
        station_df = df[df['Station'] == station_choice]

        process_avg_df = station_df[['Process', 'Avg_Time_Per_Process']].dropna()
        process_avg_df = process_avg_df[process_avg_df['Process'].str.strip() != '']
        process_avg_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig2 = px.bar(process_avg_df, x='Process', y='Avg_Time_Per_Process',
                     title=f'Average Time per Process - {station_choice}',
                     labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                     color_discrete_sequence=['green'], text='Avg_Time_Per_Process')
        fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified",
                           width=1200, height=600)
        st.plotly_chart(fig2, use_container_width=True)

        st.download_button("📥 Download Process Averages CSV", process_avg_df.to_csv(index=False).encode(),
                           file_name="process_avg.csv", mime='text/csv')

        bus_choice = st.selectbox("🚌 Select Bus for Process Time View", buses, key='bus_choice2')
        process_bus_df = station_df[['Process'] + [bus_choice]].dropna()
        fig2b = px.bar(process_bus_df, x='Process', y=bus_choice,
                       title=f"Time Taken per Process - {bus_choice} ({station_choice})",
                       labels={bus_choice: 'Manhours'},
                       color_discrete_sequence=['green'], text=bus_choice)
        fig2b.update_layout(xaxis_tickangle=-45, width=1200, height=600)
        st.plotly_chart(fig2b, use_container_width=True)

        # Outliers table
        st.markdown("### 🚨 Process Outliers (Z-Score > 2)")
        top7_var = df.nlargest(7, 'Variance')[['Station', 'Process']]
        df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                          var_name='Bus', value_name='Manhours')
        filtered = df_long.merge(top7_var, on=['Station', 'Process'])
        filtered['Z_Score'] = filtered.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_df = filtered[filtered['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)

        if outliers_df.empty:
            st.info("No strong outliers detected.")
        else:
            outlier_table = outliers_df[['Bus', 'Station', 'Process', 'Manhours']]
            st.dataframe(outlier_table, use_container_width=True)

    with tab3:
        st.subheader("👷 Human Resource Allocation Gaps")
        station_filter = st.selectbox("🏭 Select Station", stations, key='hr_station')
        gap_df = df[df['Station'] == station_filter][['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']]
        gap_df = gap_df.dropna(subset=['Process'])
        gap_df = gap_df[gap_df['Process'].str.strip() != '']
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

        color_map = {
            'Trim': 'red',
            'Logistics': 'blue',
            'Chassis': 'purple',
            'Body': 'orange',
            'Metal Finish': 'teal'
        }
        color_value = color_map.get(station_filter, 'gray')

        fig4 = px.bar(gap_df, x='Process', y='Manhours per person',
                      title=f'HR Allocation Gaps - {station_filter}',
                      labels={'Manhours per person': 'Manhours/Person'},
                      text='Manhours per person',
                      color_discrete_sequence=[color_value])
        fig4.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
        st.plotly_chart(fig4, use_container_width=True)

        insights_table = gap_df[['Station', 'Process', 'Manhours per person', 'Number of people']].head(7)
        st.markdown("### 🚨 Top 7 Processes with Highest HR Gaps")
        st.dataframe(insights_table, use_container_width=True)
else:
    st.info("👆 Please upload a valid Excel file to proceed.")

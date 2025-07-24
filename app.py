import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io
from scipy import stats

st.set_page_config(page_title="Bus Manhours Dashboard", layout="wide")

# -----------------------------
# Upload Excel File
# -----------------------------
# 📥 File upload
uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')
if file:
    df = pd.read_excel(file, sheet_name='Manhours')

    # -----------------------------
    # Data Cleaning
    # -----------------------------
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
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "⏱️ Process Time Analysis", "🚨 Outliers", "👷 HR Allocation Gaps"])

    with tab1:
        st.subheader("📊 Total Manhours Summary")
        st.metric("Average Total Manhours per Bus", f"{avg_manhours:.1f} hrs")

        selected_bus = st.selectbox("🔍 View Manhours for Specific Bus", buses)
        st.write(f"**{selected_bus} Manhours:** {total_hours[selected_bus]:.1f} hrs")

        # Bar chart for total manhours
        fig1 = px.bar(total_df, x='Bus', y='Manhours', title="Total Manhours per Bus",
                     labels={'Bus': 'Bus', 'Manhours': 'Total Manhours'},
                     color_discrete_sequence=['green'], text='Manhours')
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)

        top5 = total_df.sort_values(by='Manhours', ascending=False).head(5)
        st.markdown("**🚨 Top 5 Buses with Highest Labor Demand:**")
        for _, row in top5.iterrows():
            st.markdown(f"• {row['Bus']}: {row['Manhours']:.1f} manhours")

        # Download option
        st.download_button("📥 Download Total Manhours CSV", total_df.to_csv(index=False).encode(),
                           file_name="total_manhours.csv", mime='text/csv')

    with tab2:
        st.subheader("⏱️ Average Time per Process")
        process_avg_df = df[['Process', 'Avg_Time_Per_Process']].dropna()
        process_avg_df = process_avg_df[process_avg_df['Process'].str.strip() != '']
        process_avg_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

        fig2 = px.bar(process_avg_df, x='Process', y='Avg_Time_Per_Process',
                     title='Average Time per Process Across All Buses',
                     labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'},
                     color='Avg_Time_Per_Process', color_continuous_scale='Cividis', text='Avg_Time_Per_Process')
        fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified",
                           coloraxis_showscale=False, width=1200, height=600)
        st.plotly_chart(fig2, use_container_width=True)

        st.download_button("📥 Download Process Averages CSV", process_avg_df.to_csv(index=False).encode(),
                           file_name="process_avg.csv", mime='text/csv')

        st.markdown("**🚨 Top 7 Time Bottlenecks:**")
        for _, row in process_avg_df.head(7).iterrows():
            st.markdown(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hrs")

        bus_choice = st.selectbox("🚌 Select Bus for Process Time View", buses, key='bus_choice2')
        process_bus_df = df[['Process'] + [bus_choice]].dropna()
        fig2b = px.bar(process_bus_df, x='Process', y=bus_choice,
                       title=f"Time Taken per Process - {bus_choice}",
                       labels={bus_choice: 'Manhours'},
                       color=bus_choice, color_continuous_scale='Viridis', text=bus_choice)
        fig2b.update_layout(xaxis_tickangle=-45, width=1200, height=600)
        st.plotly_chart(fig2b, use_container_width=True)

    with tab3:
        st.subheader("🚨 Outliers in Time Taken per Process")
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
            for _, row in outliers_df.iterrows():
                st.markdown(f"• {row['Bus']} on {row['Process']} ({row['Station']}): {row['Manhours']} hrs [Z-Score: {row['Z_Score']:.2f}]")

        st.download_button("📥 Download Outliers CSV", outliers_df.to_csv(index=False).encode(),
                           file_name="outliers.csv", mime='text/csv')

    with tab4:
        st.subheader("👷 Human Resource Allocation Gaps")
        gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']]
        gap_df = gap_df.dropna(subset=['Process'])
        gap_df = gap_df[gap_df['Process'].str.strip() != '']
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

        fig4 = px.bar(gap_df, x='Process', y='Manhours per person', color='Station',
                      title='HR Allocation Gaps by Process',
                      labels={'Manhours per person': 'Manhours/Person'},
                      category_orders={"Process": gap_df['Process'].tolist()}, text='Manhours per person')
        fig4.update_layout(xaxis_tickangle=-45, width=1200, height=600, hovermode="x unified")
        st.plotly_chart(fig4, use_container_width=True)

        st.download_button("📥 Download HR Gaps CSV", gap_df.to_csv(index=False).encode(),
                           file_name="hr_gaps.csv", mime='text/csv')

        st.markdown("**🚨 Top 7 Processes with Highest HR Allocation Gaps:**")
        for _, row in gap_df.head(7).iterrows():
            st.markdown(f"• {row['Process']} ({row['Station']}): {row['Manhours per person']:.2f} hrs/person, {row['Number of people']} people")
else:
    st.info("👆 Please upload a valid Excel file to proceed.")

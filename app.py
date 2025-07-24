import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Bus Process Dashboard", layout="wide")

# -------------------------
# Sidebar - File Upload
# -------------------------
st.sidebar.title("📁 Upload Data")
file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

# -------------------------
# Load Excel Data
# -------------------------
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df = pd.read_excel(xls, sheet_name='Manhours')
    df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())
    df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')
    return df

if file:
    df = load_data(file)

    # -------------------------
    # Preprocessing
    # -------------------------
    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Total_Process_Time'] = df[bus_columns].sum(axis=1)
    df['Avg_Cycle_Time_Per_Process'] = df['Total_Process_Time'] / len(bus_columns)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Gap_Score'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    df = df.dropna(subset=['Process'])
    df = df[df['Process'].str.strip() != '']

    # -------------------------
    # Tabs
    # -------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Summary KPIs", "📊 Process Trends", "🚨 Outliers", "📉 Resource Gaps"])

    with tab1:
        st.header("🔍 Summary KPIs")
        col1, col2, col3 = st.columns(3)
        total_manhours = df[bus_columns].multiply(df['Number of people'], axis=0).sum().sum()
        avg_process_time = df['Avg_Time_Per_Process'].mean()
        max_gap = df['Gap_Score'].max()
        col1.metric("Total Manhours", f"{total_manhours:.0f} hrs")
        col2.metric("Avg Process Time", f"{avg_process_time:.2f} hrs")
        col3.metric("Max Manhour Gap", f"{max_gap:.2f} hrs/person")

        fig1 = px.bar(df, x='Process', y='Avg_Time_Per_Process',
                      title="⏱️ Avg Time per Process",
                      color='Avg_Time_Per_Process',
                      color_continuous_scale='Cividis',
                      labels={'Avg_Time_Per_Process': 'Average Time (hrs)'})
        fig1.update_traces(text=df['Avg_Time_Per_Process'].round(1), textposition='outside')
        fig1.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig1, use_container_width=True)

        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Table as CSV", data=csv_data, file_name="processed_manhours.csv", mime='text/csv')

    with tab2:
        st.header("📊 Detailed Process Trends")
        selected_bus = st.selectbox("Select a Bus:", bus_columns)
        trend_df = df[['Station', 'Process', selected_bus]]
        fig2 = px.bar(trend_df, x='Process', y=selected_bus, title=f"Manhours for {selected_bus}", labels={selected_bus: "Hours"}, color='Station')
        fig2.update_traces(text=trend_df[selected_bus].round(1), textposition='outside')
        fig2.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.header("🚨 Outlier Detection")
        df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns, var_name='Bus', value_name='Manhours')
        top7_var_processes = df.nlargest(7, 'Variance')[['Station', 'Process']]
        filtered_long = df_long.merge(top7_var_processes, on=['Station', 'Process'])
        filtered_long['Z_Score'] = filtered_long.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_df = filtered_long[filtered_long['Z_Score'] > 2]

        fig3 = px.scatter(outliers_df, x='Process', y='Manhours', color='Bus', title='Outlier Buses per Process', hover_data=['Station'])
        fig3.update_traces(marker=dict(size=12))
        st.plotly_chart(fig3, use_container_width=True)

        if not outliers_df.empty:
            st.dataframe(outliers_df[['Process', 'Station', 'Bus', 'Manhours', 'Z_Score']])
            csv_outliers = outliers_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Outliers", data=csv_outliers, file_name="outliers.csv", mime='text/csv')
        else:
            st.info("✅ No strong outliers found.")

        # Annotated heatmap
        st.subheader("Annotated Heatmap of Top 7 Variable Processes")
        heatmap_data = filtered_long.pivot(index='Bus', columns='Process', values='Manhours')
        fig, ax = plt.subplots(figsize=(14, 8))
        sns.heatmap(heatmap_data, cmap='YlGnBu', linewidths=0.5, linecolor='gray', annot=True, fmt=".1f", ax=ax)
        ax.set_title('⏱️ Time Spent on Each Process per Bus (Top 7 Variable Processes) – Hours')
        ax.set_xlabel('Process')
        ax.set_ylabel('Bus')
        st.pyplot(fig)

    with tab4:
        st.header("📉 Resource Allocation Gaps")
        gap_df = df[['Station', 'Process', 'Gap_Score', 'Number of people']].sort_values(by='Gap_Score', ascending=False)
        fig4 = px.bar(gap_df.head(15), x='Process', y='Gap_Score', color='Station',
                      title="Top Resource Allocation Gaps",
                      labels={'Gap_Score': 'Manhours per Person'})
        fig4.update_traces(text=gap_df.head(15)['Gap_Score'].round(1), textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(gap_df.head(15))
        csv_gap = gap_df.head(15).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Gaps Table", data=csv_gap, file_name="resource_gaps.csv", mime='text/csv')

else:
    st.info("📂 Please upload an Excel file to begin analysis.")

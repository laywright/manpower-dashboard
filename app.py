import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Bus Process Dashboard", layout="wide")

# -------------------------
# Sidebar - File Upload & Filters
# -------------------------
st.sidebar.title("📁 Upload Data")
file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

st.sidebar.markdown("---")

# -------------------------
# Cache loading function
# -------------------------
@st.cache_data
def load_data(file):
    xls = pd.ExcelFile(file)
    df = pd.read_excel(xls, sheet_name='Manhours')
    df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())
    df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')
    return df

# -------------------------
# Main Section
# -------------------------
if file:
    df = load_data(file)

    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Total_Process_Time'] = df[bus_columns].sum(axis=1)
    df['Avg_Cycle_Time_Per_Process'] = df['Total_Process_Time'] / len(bus_columns)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Gap_Score'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    # Clean blanks
    df = df.dropna(subset=['Process'])
    df = df[df['Process'].str.strip() != '']

    # Tabs for navigation
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
                      title="⏱️ Avg Time per Process", color='Avg_Time_Per_Process',
                      color_continuous_scale='Cividis')
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.header("📊 Detailed Process Trends")
        selected_bus = st.selectbox("Select a Bus:", bus_columns)
        trend_df = df[['Station', 'Process', selected_bus]]
        fig2 = px.bar(trend_df, x='Process', y=selected_bus, title=f"Manhours for {selected_bus}",
                      labels={selected_bus: "Manhours"}, color='Station')
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.header("🚨 Outlier Detection")

        df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                          var_name='Bus', value_name='Manhours')

        top7_var_processes = df.nlargest(7, 'Variance')[['Station', 'Process']]
        filtered_long = df_long.merge(top7_var_processes, on=['Station', 'Process'])

        filtered_long['Z_Score'] = filtered_long.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0))
        outliers_df = filtered_long[filtered_long['Z_Score'] > 2]

        fig3 = px.scatter(outliers_df, x='Process', y='Manhours', color='Bus',
                          title='Outlier Buses per Process', hover_data=['Station'])
        st.plotly_chart(fig3, use_container_width=True)

        if not outliers_df.empty:
            st.dataframe(outliers_df[['Process', 'Station', 'Bus', 'Manhours', 'Z_Score']])
        else:
            st.info("✅ No strong outliers found.")

    with tab4:
        st.header("📉 Resource Allocation Gaps")
        gap_df = df[['Station', 'Process', 'Gap_Score', 'Number of people']].sort_values(by='Gap_Score', ascending=False)
        fig4 = px.bar(gap_df.head(15), x='Process', y='Gap_Score', color='Station',
                      title="Top Resource Allocation Gaps", labels={'Gap_Score': 'Manhours per Person'})
        st.plotly_chart(fig4, use_container_width=True)

        st.dataframe(gap_df.head(15))

else:
    st.info("📂 Please upload an Excel file to begin analysis.")

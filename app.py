import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="🚍 Bus Process Dashboard", layout="wide")

# -------------------------
# Sidebar - File Upload
# -------------------------
st.sidebar.title("📁 Upload Data")
file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
st.sidebar.markdown("---")

# -------------------------
# Data Loading
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
    df = df.dropna(subset=['Process'])
    df = df[df['Process'].str.strip() != '']

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Manhour Summary", "🔍 Bus View", "🚨 High Usage Alert", "📉 Resource Gaps", "📈 Total per Bus"
    ])

    with tab1:
        st.header("📊 Overall Summary")
        col1, col2, col3 = st.columns(3)

        total_manhours = df[bus_columns].multiply(df['Number of people'], axis=0).sum().sum()
        avg_process_time = df['Avg_Time_Per_Process'].mean()
        max_gap = df['Gap_Score'].max()

        col1.metric("🔢 Total Manhours", f"{total_manhours:.0f} hrs")
        col2.metric("⏱️ Avg Process Time", f"{avg_process_time:.2f} hrs")
        col3.metric("📉 Max Gap Score", f"{max_gap:.2f} hrs/person")

        fig1 = px.bar(df, x='Process', y='Avg_Time_Per_Process',
                      title="⏱️ Average Time per Process",
                      color='Station', labels={'Avg_Time_Per_Process': 'Avg Time (hrs)'})
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.header("🔍 View Manhours by Bus")
        selected_bus = st.selectbox("Select Bus Number:", bus_columns)
        bus_df = df[['Station', 'Process', selected_bus]]
        fig2 = px.bar(bus_df, x='Process', y=selected_bus,
                      title=f"Manhours for {selected_bus}",
                      color='Station', labels={selected_bus: 'Manhours'})
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.header("🚨 Buses with Unusually High Time per Process")

        # Melt to long format
        df_long = df.melt(id_vars=['Process'], value_vars=bus_columns,
                          var_name='Bus Index', value_name='Manhours')

        # Detect high usage using threshold
        process_stats = df_long.groupby('Process')['Manhours'].agg(['mean', 'std']).reset_index()
        process_stats['Threshold'] = process_stats['mean'] + 1.5 * process_stats['std']

        df_merged = df_long.merge(process_stats[['Process', 'Threshold']], on='Process')
        df_merged['Is_High'] = df_merged['Manhours'] > df_merged['Threshold']
        high_usage = df_merged[df_merged['Is_High']]

        fig3 = px.scatter(high_usage, x='Process', y='Manhours', color='Bus Index',
                          title="🚨 High Manhour Alerts", labels={'Manhours': 'Hours'})
        st.plotly_chart(fig3, use_container_width=True)

        if not high_usage.empty:
            st.subheader("⚠️ Alerts Summary")
            for _, row in high_usage.iterrows():
                st.markdown(f"• **{row['Bus Index']}** spent unusually high time on **{row['Process']}**")
        else:
            st.success("✅ No significant outliers detected.")

    with tab4:
        st.header("📉 Resource Allocation Gaps")

        gap_df = df[['Station', 'Process', 'Gap_Score', 'Number of people']]
        gap_df = gap_df.sort_values(by='Gap_Score', ascending=False)

        fig4 = px.bar(gap_df.head(15), x='Process', y='Gap_Score', color='Station',
                      title="Top Resource Allocation Gaps",
                      labels={'Gap_Score': 'Manhour per Person'})
        st.plotly_chart(fig4, use_container_width=True)

        st.subheader("🧮 Top 5 Gap Insights")
        for _, row in gap_df.head(5).iterrows():
            st.markdown(f"• **{row['Process']}** ({row['Station']}): {row['Gap_Score']:.2f} hrs/person "
                        f"with {row['Number of people']} assigned")

    with tab5:
        st.header("📈 Total Manhours per Bus")
        total_by_bus = df[bus_columns].sum().sort_values(ascending=False)
        bus_df = pd.DataFrame({'Bus': total_by_bus.index, 'Total Hours': total_by_bus.values})

        fig5 = px.bar(bus_df, x='Bus', y='Total Hours',
                      title="🚌 Total Manhours per Bus", color='Total Hours',
                      color_continuous_scale='Turbo')
        st.plotly_chart(fig5, use_container_width=True)
        st.dataframe(bus_df)

else:
    st.info("📂 Please upload an Excel file to start the dashboard.")

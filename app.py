import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Bus Process Time Dashboard", layout="wide")

# --- Sidebar for File Upload ---
st.sidebar.title("📂 Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Upload MP1_CL_BS_MF_Time_Log.xlsx", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Analysis')
    df.dropna(how='all', inplace=True)
    df.rename(columns={df.columns[0]: 'Bus'}, inplace=True)

    st.title("🚌 Bus Process Time Analysis Dashboard")

    # --- Overview Metrics ---
    st.subheader("📊 Overview Metrics")
    process_data = df.drop(columns='Bus')
    avg_times = process_data.mean().sort_values(ascending=False)
    std_per_process = process_data.std().sort_values(ascending=False)
    total_man_hours = process_data.sum(axis=1)
    df['Total Man-Hours'] = total_man_hours

    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Buses", df.shape[0])
    col2.metric("Number of Processes", process_data.shape[1])
    col3.metric("Avg Total Man-Hours", f"{total_man_hours.mean():.2f} hrs")

    # --- Bar Chart: Avg Time Per Process ---
    st.subheader("⏱️ Average Time Spent per Process (in Hours)")
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    avg_times.plot(kind='bar', color='skyblue', ax=ax1)
    ax1.set_title('Average Time Spent per Process')
    ax1.set_ylabel('Hours')
    ax1.grid(axis='y')
    st.pyplot(fig1)

    # --- Bar Chart: Total Man-Hours per Bus ---
    st.subheader("🕒 Total Man-Hours per Bus")
    df_sorted = df[['Bus', 'Total Man-Hours']].sort_values(by='Bus')
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.bar(df_sorted['Bus'].astype(str), df_sorted['Total Man-Hours'], color='orange')
    ax2.set_title('Total Man-Hours per Bus')
    ax2.set_xlabel('Bus Number')
    ax2.set_ylabel('Hours')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(axis='y')
    st.pyplot(fig2)

    # --- Boxplot: Process Variation ---
    st.subheader("📦 Variation in Process Times (Boxplot)")
    fig3, ax3 = plt.subplots(figsize=(14, 6))
    sns.boxplot(data=process_data, orient='h', palette='Set2', ax=ax3)
    ax3.set_title('Variation in Process Times Across Buses')
    ax3.set_xlabel('Hours')
    ax3.set_ylabel('Process')
    ax3.grid(axis='x')
    st.pyplot(fig3)

    # --- Heatmap: Per-Bus Process Time ---
    st.subheader("🌡️ Heatmap - Time Spent per Process per Bus")
    fig4, ax4 = plt.subplots(figsize=(14, 8))
    sns.heatmap(process_data, cmap='YlGnBu', linewidths=0.5, linecolor='gray',
                annot=True, fmt=".1f", yticklabels=df['Bus'], ax=ax4)
    ax4.set_title('Time Spent on Each Process per Bus')
    ax4.set_xlabel('Process')
    ax4.set_ylabel('Bus')
    st.pyplot(fig4)

    # --- Outlier Detection ---
    st.subheader("🚨 Outlier Detection")
    thresholds = process_data.mean() + 1.5 * process_data.std()
    outliers = (process_data > thresholds).stack()
    high_usage = outliers[outliers].reset_index()
    high_usage.columns = ['Bus Index', 'Process', 'Flag']
    high_usage['Bus'] = df['Bus'].iloc[high_usage['Bus Index']].values

    if not high_usage.empty:
        for _, row in high_usage.iterrows():
            st.warning(f"• Bus **{row['Bus']}** spent unusually high time on '**{row['Process']}**'")
    else:
        st.success("✅ No significant outliers detected in process time.")

    # --- Raw Data Section ---
    with st.expander("🧾 View Raw Data"):
        st.dataframe(df)

else:
    st.info("Upload your Excel file from the sidebar to begin analysis.")

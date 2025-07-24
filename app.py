import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# ------------------------- #
# Page Configuration
# ------------------------- #
st.set_page_config(page_title="Bus Manhour Dashboard", layout="wide")

# ------------------------- #
# Authentication & Sheet Access
# ------------------------- #
@st.cache_resource

def load_data():
    # Load data from Google Sheets
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1bsYcEO8ncUxOiw6uxFIVqBIA903DM7Tfl4AWjWStjqQ")
    worksheet = sh.worksheet("Manhours")
    df = get_as_dataframe(worksheet, evaluate_formulas=True)
    return df.dropna(how='all')

df = load_data()
df.columns = df.columns.str.strip()
df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')

bus_columns = [col for col in df.columns if str(col).startswith("Bus")]
buses = [col for col in bus_columns if df[col].notna().sum() > 0]

# ------------------------- #
# Tabs Structure
# ------------------------- #
tabs = st.tabs([
    "📊 Summary",
    "🔍 Bus Selection",
    "🚌 Total Hours per Bus",
    "⏱️ Process Averages",
    "🔎 Time per Process (Bus)",
    "🚨 Outlier Detection",
    "📉 HR Gaps"
])

# 1. Summary
with tabs[0]:
    st.header("📊 Overall Summary")
    total_hours = df[bus_columns].multiply(df['Number of people'], axis=0).sum()
    overall_avg_process_time = df[bus_columns].mean(axis=1).mean()
    st.metric("✅ Total Manhours Across All Buses", f"{total_hours.sum():,.0f} hours")
    st.metric("📌 Overall Avg. Time per Process", f"{overall_avg_process_time:.1f} hours")

# 2. Bus Selection View
with tabs[1]:
    st.header("🔍 View Manhours for Selected Bus")
    selected_bus = st.selectbox("Choose Bus Number", buses)
    if selected_bus:
        st.subheader(f"Manhours for {selected_bus}")
        bus_df = df[['Station', 'Process', selected_bus]].dropna()
        st.dataframe(bus_df.rename(columns={selected_bus: "Hours"}))

# 3. Total Hours per Bus Chart
with tabs[2]:
    st.header("🚌 Total Manhours per Bus")
    total_hours_df = pd.DataFrame({"Bus": buses, "Manhours": total_hours[buses]})
    fig1 = px.bar(total_hours_df, x="Bus", y="Manhours", color_discrete_sequence=['green'],
                 title="<b>Total Manhours per Bus</b>")
    st.plotly_chart(fig1, use_container_width=True)

    avg_total = total_hours_df['Manhours'].mean()
    st.info(f"📊 The average total manhours per bus is **{avg_total:.1f}** hours.")

    st.markdown("**🚨 Top 5 Buses by Manhours:**")
    top5 = total_hours_df.sort_values(by='Manhours', ascending=False).head(5)
    for _, row in top5.iterrows():
        st.write(f"• {row['Bus']} — {row['Manhours']:.1f} hours")

# 4. Average Time per Process
with tabs[3]:
    st.header("⏱️ Avg Time per Process")
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    process_avg_df = df[['Process', 'Avg_Time_Per_Process']].dropna()
    process_avg_df = process_avg_df[process_avg_df['Process'].str.strip() != '']
    process_avg_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

    fig2 = px.bar(process_avg_df, x='Process', y='Avg_Time_Per_Process',
                 color='Avg_Time_Per_Process',
                 color_continuous_scale='Cividis',
                 title='⏱️ Average Time Taken per Process')
    fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45,
                      coloraxis_showscale=False, width=1200, height=600)
    st.plotly_chart(fig2, use_container_width=True)

    overall_avg = process_avg_df['Avg_Time_Per_Process'].mean()
    st.info(f"📊 Overall average process time: **{overall_avg:.1f} hours**")

    st.markdown("**🚨 Top 7 Time Bottlenecks:**")
    for _, row in process_avg_df.head(7).iterrows():
        st.write(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hours")

# 5. Time Taken per Process on Selected Bus
with tabs[4]:
    st.header("🔎 Time per Process on a Selected Bus")
    bus_option = st.selectbox("Select Bus", buses, key="bus_select_process")
    if bus_option:
        temp = df[['Process', bus_option]].dropna()
        st.dataframe(temp.rename(columns={bus_option: "Hours"}))

# 6. Outlier Detection
with tabs[5]:
    st.header("🚨 Outlier Detection (Top 7 Variance Processes)")
    df['Variance'] = df[bus_columns].var(axis=1)
    top7_var = df.nlargest(7, 'Variance')[['Station', 'Process']]

    df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                      var_name='Bus', value_name='Manhours')
    filtered = df_long.merge(top7_var, on=['Station', 'Process'])
    filtered['Z_Score'] = filtered.groupby('Process')['Manhours'].transform(
        lambda x: (x - x.mean()) / x.std(ddof=0))
    outliers_df = filtered[filtered['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)

    if outliers_df.empty:
        st.success("✅ No strong outliers detected in the top 7 variance-heavy processes.")
    else:
        for _, row in outliers_df.iterrows():
            st.write(f"• {row['Bus']} on {row['Process']} ({row['Station']}): {row['Manhours']} hrs [Z = {row['Z_Score']:.2f}]")

# 7. HR Gaps
with tabs[6]:
    st.header("📉 Human Resource Allocation Gaps")
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Manhours per person'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)

    gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']].dropna()
    gap_df = gap_df[gap_df['Process'].str.strip() != '']
    gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

    fig3 = px.bar(gap_df, x='Process', y='Manhours per person', color='Station',
                 title='🔍 Human Resource Allocation Gaps by Process',
                 labels={'Manhours per person': 'Manhour per Person'},
                 category_orders={"Process": gap_df['Process'].tolist()})
    fig3.update_layout(xaxis_tickangle=-45, width=1200, height=600)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**🚨 Top 7 Gaps:**")
    for _, row in gap_df.head(7).iterrows():
        st.write(f"• {row['Process']} ({row['Station']}): {row['Manhours per person']:.2f} hours/person with {int(row['Number of people'])} people")

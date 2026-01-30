import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ================= ⚙️ PAGE CONFIG =================
st.set_page_config(
    page_title="🚌 BasiGo Manpower Dashboard",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌🔥 **BasiGo Manpower Dashboard** 🔥🚌")
st.caption("⏱️ Manhours • 👷 Workforce Allocation • 🚨 Process Bottlenecks")

uploaded_file = st.file_uploader(
    "📤 **Upload Production Tracker Excel File**",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("📎 Please upload a valid Excel file to continue 👆")
    st.stop()

# ================= 📂 LOAD BUS SHEETS =================
xls = pd.ExcelFile(uploaded_file)

bus_sheets = [
    s for s in xls.sheet_names
    if s.startswith(("PV1A Bus", "PV1B Bus", "PV2 Bus"))
]

st.success(f"✅ Loaded **{len(bus_sheets)} buses** 🚌")

bus_data = {}

for sheet in bus_sheets:
    df = pd.read_excel(xls, sheet_name=sheet)
    df = df.dropna(how="all").rename(columns=lambda x: str(x).strip())

    df['Number of people'] = pd.to_numeric(
        df.get('Number of people', pd.Series(dtype=float)),
        errors='coerce'
    )

    bus_data[sheet] = df

# ================= 🧮 TOTAL MANHOURS =================
bus_manhours = []

for bus, df in bus_data.items():
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    time_cols = numeric_cols.drop(['Number of people'], errors='ignore')

    total_hours = (
        df[time_cols]
        .multiply(df['Number of people'], axis=0)
        .sum()
        .sum()
    )

    bus_manhours.append({
        "🚌 Bus": bus,
        "⏱️ Manhours": total_hours
    })

total_df = pd.DataFrame(bus_manhours)
avg_manhours = total_df['⏱️ Manhours'].mean()

# ================= 🧩 COMBINED DATA =================
combined_df = pd.concat(
    [df.assign(Bus=bus) for bus, df in bus_data.items()],
    ignore_index=True
)

# ================= 📑 TABS =================
tab1, tab2, tab3 = st.tabs([
    "📊 **Summary**",
    "⏱️ **Process Time Analysis**",
    "👷 **HR Allocation Gaps**"
])

# =====================================================
# 📊 TAB 1 — SUMMARY
# =====================================================
with tab1:
    st.subheader("📊 **Total Manhours Overview**")

    st.metric(
        "📈 Average Manhours per Bus",
        f"{avg_manhours:.1f} hrs ⏱️"
    )

    selected_bus = st.selectbox(
        "🚌 **Select a Bus to Inspect**",
        total_df['🚌 Bus']
    )

    selected_value = total_df.loc[
        total_df['🚌 Bus'] == selected_bus, '⏱️ Manhours'
    ].values[0]

    st.markdown(
        f"### 🟢 **{selected_bus}** → ⏱️ **{selected_value:.1f} hrs**"
    )

    fig1 = px.bar(
        total_df,
        x='🚌 Bus',
        y='⏱️ Manhours',
        text='⏱️ Manhours',
        title="🚌 Total Manhours per Bus"
    )
    fig1.update_layout(
        hovermode="x unified",
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("### 🚨 **Top 5 Highest Manhour Buses**")
    for _, row in total_df.sort_values(
        by='⏱️ Manhours', ascending=False
    ).head(5).iterrows():
        st.markdown(
            f"• 🚨🚌 **{row['🚌 Bus']}** — ⏱️ {row['⏱️ Manhours']:.1f} hrs"
        )

    st.download_button(
        "📥 Download Manhours CSV 📊",
        total_df.to_csv(index=False).encode(),
        file_name="total_manhours.csv",
        mime="text/csv"
    )

# =====================================================
# ⏱️ TAB 2 — PROCESS TIME ANALYSIS
# =====================================================
with tab2:
    st.subheader("⏱️ **Average Process Time Analysis**")

    process_df = combined_df[['Station', 'Process', 'Avg_Time_Per_Process']].dropna()
    process_df = process_df[process_df['Process'].str.strip() != ""]

    process_avg = (
        process_df
        .groupby(['Station', 'Process'], as_index=False)
        .mean()
        .sort_values(by='Avg_Time_Per_Process', ascending=False)
    )

    process_avg['🚨 Status'] = process_avg['Avg_Time_Per_Process'].apply(
        lambda x: "🚨⚠️ OVER 8 HRS" if x > 8 else "✅ OK"
    )

    fig2 = px.bar(
        process_avg,
        x='Process',
        y='Avg_Time_Per_Process',
        color='Station',
        text='🚨 Status',
        title="⏱️ Average Process Time Across All Buses"
    )

    fig2.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🚨🔥 **Processes Exceeding 8 Hours**")
    slow = process_avg[process_avg['Avg_Time_Per_Process'] > 8]

    if slow.empty:
        st.success("🎉✅ No process exceeds 8 hours — great job!")
    else:
        for _, row in slow.iterrows():
            st.markdown(
                f"• 🚨🔥 **{row['Process']}** "
                f"({row['Station']}) → ⏱️ {row['Avg_Time_Per_Process']:.1f} hrs"
            )

# =====================================================
# 👷 TAB 3 — HR ALLOCATION GAPS
# =====================================================
with tab3:
    st.subheader("👷 **Human Resource Allocation Gaps**")

    gap_df = combined_df[[
        'Station',
        'Process',
        'Avg_Manhours',
        'Number of people',
        'Manhours per person'
    ]].dropna(subset=['Process'])

    gap_df = gap_df[gap_df['Process'].str.strip() != ""]
    gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)

    gap_df['🚨 Load Status'] = gap_df['Manhours per person'].apply(
        lambda x: "🚨🔥 OVERLOADED" if x > 8 else "✅ BALANCED"
    )

    fig3 = px.bar(
        gap_df,
        x='Process',
        y='Manhours per person',
        color='Station',
        text='🚨 Load Status',
        title="👷 Manhours per Person by Process"
    )

    fig3.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 🚨👷 **Top 7 HR Allocation Gaps**")
    top_gaps = gap_df.head(7)[[
        'Station',
        'Process',
        'Manhours per person',
        'Number of people'
    ]]

    st.dataframe(
        top_gaps.style.format({
            'Manhours per person': '{:.2f}',
            'Number of people': '{:.0f}'
        })
    )

    st.download_button(
        "📥 Download HR Gap CSV 👷",
        gap_df.to_csv(index=False).encode(),
        file_name="hr_allocation_gaps.csv",
        mime="text/csv"
    )

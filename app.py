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

st.title("🚌🔥 BasiGo Manpower Dashboard 🔥🚌")
st.caption("👷 Manpower • ⏱️ Manhours • 🚨 Bottlenecks")

uploaded_file = st.file_uploader("📤 Upload Production Tracker Excel File", type=["xlsx"])

if uploaded_file is None:
    st.info("📎 Please upload the Excel file to continue 👆")
    st.stop()

# ================= 📂 LOAD BUS SHEETS =================
xls = pd.ExcelFile(uploaded_file)

bus_sheets = [
    s for s in xls.sheet_names
    if s.startswith(("PV1A Bus", "PV1B Bus", "PV2 Bus"))
]

st.success(f"✅ Loaded {len(bus_sheets)} bus sheets 🚌")

all_data = []

for sheet in bus_sheets:
    df = pd.read_excel(xls, sheet_name=sheet)

    # 🧹 Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # 🎯 Keep only valid columns
    expected_cols = [
        "Vin No", "Station", "Date",
        "Activities", "Manpower", "Manhours"
    ]

    missing = set(expected_cols) - set(df.columns)
    if missing:
        st.warning(f"⚠️ Sheet **{sheet}** missing columns: {missing}")
        continue

    df = df[expected_cols]
    df["Bus"] = sheet

    # 🔢 Numeric safety
    df["Manpower"] = pd.to_numeric(df["Manpower"], errors="coerce")
    df["Manhours"] = pd.to_numeric(df["Manhours"], errors="coerce")

    # 🚨 Flag long activities
    df["🚨 Status"] = df["Manhours"].apply(
        lambda x: "🚨 OVER 8 HRS" if x > 8 else "✅ OK"
    )

    all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)

# ================= 📑 TABS =================
tab1, tab2, tab3 = st.tabs([
    "📊 Summary",
    "⏱️ Activity Analysis",
    "👷 Manpower Analysis"
])

# =====================================================
# 📊 TAB 1 — SUMMARY
# =====================================================
with tab1:
    st.subheader("📊 Manhours Summary by Bus 🚌")

    bus_summary = (
        combined_df
        .groupby("Bus", as_index=False)["Manhours"]
        .sum()
        .sort_values("Manhours", ascending=False)
    )

    avg_mh = bus_summary["Manhours"].mean()

    st.metric(
        "📈 Average Manhours per Bus",
        f"{avg_mh:.1f} hrs ⏱️"
    )

    fig1 = px.bar(
        bus_summary,
        x="Bus",
        y="Manhours",
        text="Manhours",
        title="🚌 Total Manhours per Bus"
    )
    fig1.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig1, use_container_width=True)

# =====================================================
# ⏱️ TAB 2 — ACTIVITY ANALYSIS
# =====================================================
with tab2:
    st.subheader("⏱️ Activity Manhours Analysis 🚨")

    activity_summary = (
        combined_df
        .groupby(["Station", "Activities"], as_index=False)["Manhours"]
        .sum()
        .sort_values("Manhours", ascending=False)
    )

    activity_summary["🚨 Status"] = activity_summary["Manhours"].apply(
        lambda x: "🚨 OVER 8 HRS" if x > 8 else "✅ OK"
    )

    fig2 = px.bar(
        activity_summary,
        x="Activities",
        y="Manhours",
        color="Station",
        text="🚨 Status",
        title="⏱️ Total Manhours per Activity"
    )
    fig2.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### 🚨 Activities Exceeding 8 Manhours")
    slow = activity_summary[activity_summary["Manhours"] > 8]

    if slow.empty:
        st.success("🎉 No activity exceeds 8 manhours!")
    else:
        for _, r in slow.iterrows():
            st.markdown(
                f"• 🚨 **{r['Activities']}** "
                f"({r['Station']}) — ⏱️ {r['Manhours']:.1f} hrs"
            )

# =====================================================
# 👷 TAB 3 — MANPOWER ANALYSIS
# =====================================================
with tab3:
    st.subheader("👷 Manpower vs Manhours 🚨")

    manpower_summary = (
        combined_df
        .groupby(["Station", "Activities"], as_index=False)
        .agg({
            "Manpower": "mean",
            "Manhours": "sum"
        })
        .sort_values("Manhours", ascending=False)
    )

    manpower_summary["🚨 Load"] = manpower_summary["Manhours"].apply(
        lambda x: "🚨 HIGH LOAD" if x > 8 else "✅ OK"
    )

    fig3 = px.bar(
        manpower_summary,
        x="Activities",
        y="Manhours",
        color="Station",
        text="🚨 Load",
        title="👷 Manpower Load per Activity"
    )
    fig3.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 🚨 Top 7 Highest Load Activities")
    st.dataframe(
        manpower_summary.head(7)[[
            "Station", "Activities", "Manpower", "Manhours", "🚨 Load"
        ]]
    )

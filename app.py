import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Bus Manhour Dashboard", layout="wide")
st.title("🚌 Bus Manufacturing Manhour Dashboard")

# Upload Excel file
uploaded_file = st.file_uploader("Upload the 'MP1 Weekly Plan for manipulation.xlsx' file", type="xlsx")
if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')

    # Identify bus columns
    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]

    # -------------------------
    # 1. TOTAL MANHOURS PER BUS
    # -------------------------
    total_hours = df[bus_columns].sum()
    buses = total_hours.index.str.replace('Bus ', '').str.strip()
    manhour_df = pd.DataFrame({'Bus': buses, 'Manhours': total_hours.values})

    st.subheader("📊 Total Manhours per Bus")
    fig1 = px.bar(
        manhour_df,
        x='Bus',
        y='Manhours',
        title="<b>Total Manhours per Bus</b>",
        labels={'Bus': 'Bus Number', 'Manhours': 'Total Manhours'},
        color_discrete_sequence=['green']
    )
    fig1.update_layout(hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    avg_manhours = manhour_df['Manhours'].mean()
    top5 = manhour_df.sort_values(by='Manhours', ascending=False).head(5)

    st.markdown(f"**\n📊 The average total manhours per bus is {avg_manhours:.1f} hours.**")
    st.markdown("**🚨 Top 5 buses with the highest labor demand:**")
    for _, row in top5.iterrows():
        bus_number = row['Bus']
        st.markdown(f"  • **Bus {bus_number} — {row['Manhours']:.1f} manhours**")

    # -------------------------
    # 2. AVERAGE TIME PER PROCESS
    # -------------------------
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    process_avg_df = df[['Process', 'Avg_Time_Per_Process']].copy()
    process_avg_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)

    st.subheader("⏱️ Average Time Taken per Process Across All Buses")
    fig2 = px.bar(
        process_avg_df,
        x='Process',
        y='Avg_Time_Per_Process',
        title='⏱️ Average Time Taken per Process Across All Buses',
        labels={'Avg_Time_Per_Process': 'Average Time (hours)'},
        color='Avg_Time_Per_Process',
        color_continuous_scale='Cividis'
    )
    fig2.update_layout(
        yaxis_range=[0, 30],
        xaxis_tickangle=-45,
        hovermode="x unified",
        coloraxis_showscale=False,
        width=1200,
        height=600
    )
    st.plotly_chart(fig2, use_container_width=True)

    overall_avg_process_time = process_avg_df['Avg_Time_Per_Process'].mean()
    top7_bottlenecks = process_avg_df.head(7)

    st.markdown(f"**\n📊 The overall average process time across all buses is {overall_avg_process_time:.1f} hours.**")
    st.markdown("**🚨 Top 7 Time Bottlenecks (Processes with highest average manhours):**")
    for _, row in top7_bottlenecks.iterrows():
        st.markdown(f"  • **{row['Process']}: {row['Avg_Time_Per_Process']:.1f} hours**")

    # -------------------------
    # 3. OUTLIER DETECTION
    # -------------------------
    st.subheader("🔍 Outlier Detection per Process")

    df_z = df.copy()
    z_scores = ((df_z[bus_columns] - df_z[bus_columns].mean(axis=1).values[:, None]) /
                df_z[bus_columns].std(axis=1).values[:, None])

    high_var_processes = df[bus_columns].std(axis=1).sort_values(ascending=False).head(7).index

    for idx in high_var_processes:
        process_name = df.loc[idx, 'Process']
        process_data = df.loc[idx, bus_columns]
        process_z = z_scores.loc[idx, :]

        outliers = process_z[process_z > 2]
        process_df = pd.DataFrame({
            'Bus': [b.replace('Bus ', '') for b in process_data.index],
            'Time (hrs)': process_data.values,
            'Z-Score': process_z.values
        })

        fig = px.bar(
            process_df,
            x='Bus',
            y='Time (hrs)',
            color='Z-Score',
            title=f"🚨 Outlier Detection for Process: {process_name}",
            color_continuous_scale='Reds'
        )
        fig.update_layout(yaxis_title="Time (hrs)", xaxis_title="Bus")
        st.plotly_chart(fig, use_container_width=True)

        if not outliers.empty:
            st.markdown(f"**Outliers detected in '{process_name}' (Z > 2):**")
            for bus, score in outliers.items():
                st.markdown(f"  • **{bus}** — Z-score: **{score:.2f}**")
        else:
            st.markdown(f"✅ No significant outliers detected for '{process_name}' (Z ≤ 2).")
else:
    st.info("⬆️ Please upload the Excel file to begin analysis.")

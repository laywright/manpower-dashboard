import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="🚌 Bus Process Insight Dashboard", layout="wide")

# 📥 File upload
uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, sheet_name='Manhours')
    
    # 🔍 Cleanup
    df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())
    df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')
    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]
    
    # 🧮 Manhours calculation
    buses = bus_columns
    total_hours = df[buses].multiply(df['Number of people'], axis=0).sum()
    total_df = pd.DataFrame({'Bus': buses, 'Manhours': total_hours.values})
    avg_manhours = total_df['Manhours'].mean()
    
    # ⏱️ Process time calculations
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    process_avg_df = df[['Process', 'Avg_Time_Per_Process']].dropna()
    process_avg_df = process_avg_df[process_avg_df['Process'].str.strip() != '']
    overall_avg_time = process_avg_df['Avg_Time_Per_Process'].mean()

    # 📊 Layout starts
    st.title("🧮 Operational Insight Dashboard")
    
    # ✅ Summary Panel
    st.subheader("🔢 Summary")
    st.metric("📊 Average Manhours per Bus", f"{avg_manhours:.1f} hrs")
    st.metric("⏱️ Average Process Time Across Buses", f"{overall_avg_time:.1f} hrs")

    # 🧭 Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Manhours Summary",
        "⏱️ Process Bottlenecks",
        "🛠️ Process Time Per Bus",
        "🚨 Outlier Detection",
        "📊 Resource Allocation Gaps",
        "📤 Downloads"
    ])

    # ✨ Tab 1: Manhours Summary
    with tab1:
        selected_bus = st.selectbox("Choose a Bus to View Manhours", buses)
        if selected_bus:
            selected_total = df[selected_bus].multiply(df['Number of people'], axis=0).sum()
            st.write(f"**Total manhours for {selected_bus}:** {selected_total:.1f} hours")
        
        fig1 = px.bar(total_df, x='Bus', y='Manhours',
                      title="📊 Total Manhours per Bus",
                      labels={'Bus': 'Bus Number', 'Manhours': 'Total Manhours'},
                      color_discrete_sequence=['green'])
        fig1.update_layout(hovermode="x unified")
        st.plotly_chart(fig1, use_container_width=True)
        
        top5 = total_df.sort_values(by='Manhours', ascending=False).head(5)
        st.markdown(f"**Average total manhours per bus:** {avg_manhours:.1f} hrs")
        st.markdown("🚨 **Top 5 Buses with Highest Labor Demand:**")
        for _, row in top5.iterrows():
            st.write(f"• {row['Bus']}: {row['Manhours']:.1f} hrs")

    # ✨ Tab 2: Process Bottlenecks
    with tab2:
        sorted_df = process_avg_df.sort_values(by='Avg_Time_Per_Process', ascending=False)
        fig2 = px.bar(sorted_df, x='Process', y='Avg_Time_Per_Process',
                      title="⏱️ Average Time per Process (All Buses)",
                      labels={'Avg_Time_Per_Process': 'Average Time (hrs)'},
                      color='Avg_Time_Per_Process', color_continuous_scale='Cividis')
        fig2.update_layout(yaxis_range=[0, 30], xaxis_tickangle=-45, hovermode="x unified",
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)
        
        bottlenecks = sorted_df.head(7)
        st.markdown(f"📊 **Overall average process time:** {overall_avg_time:.1f} hrs")
        st.markdown("🚨 **Top 7 Time Bottlenecks:**")
        for _, row in bottlenecks.iterrows():
            st.write(f"• {row['Process']}: {row['Avg_Time_Per_Process']:.1f} hrs")

    # ✨ Tab 3: Process Time by Bus
    with tab3:
        selected_bus_proc = st.selectbox("Choose a Bus to View Process Times", buses)
        if selected_bus_proc:
            proc_df = df[['Process', selected_bus_proc]].dropna()
            proc_df = proc_df[proc_df['Process'].str.strip() != '']
            fig3 = px.bar(proc_df, x='Process', y=selected_bus_proc,
                          title=f"🔎 Process Time for {selected_bus_proc}",
                          labels={selected_bus_proc: "Manhours"},
                          color=selected_bus_proc, color_continuous_scale='Blues')
            fig3.update_layout(xaxis_tickangle=-45, hovermode="x unified",
                               coloraxis_showscale=False)
            st.plotly_chart(fig3, use_container_width=True)

    # ✨ Tab 4: Outliers by Z-Score
    with tab4:
        df['Variance'] = df[bus_columns].var(axis=1)
        top_var = df.nlargest(7, 'Variance')[['Station', 'Process']]
        df_long = df.melt(id_vars=['Station', 'Process'], value_vars=bus_columns,
                          var_name='Bus', value_name='Manhours')
        filtered_long = df_long.merge(top_var, on=['Station', 'Process'])
        filtered_long['Z_Score'] = filtered_long.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        )
        outliers_df = filtered_long[filtered_long['Z_Score'] > 2].sort_values(by='Z_Score', ascending=False)
        st.subheader("🚨 Outliers in High Variance Processes")
        if outliers_df.empty:
            st.info("No strong outliers detected.")
        else:
            for _, row in outliers_df.iterrows():
                st.write(f"• {row['Bus']} on {row['Process']} ({row['Station']}): {row['Manhours']} hrs (Z = {row['Z_Score']:.2f})")

    # ✨ Tab 5: Resource Allocation Gaps
    with tab5:
        df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
        df['Manhours per person'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)
        gap_df = df[['Station', 'Process', 'Avg_Manhours', 'Number of people', 'Manhours per person']].dropna()
        gap_df = gap_df[gap_df['Process'].str.strip() != '']
        gap_df = gap_df.sort_values(by='Manhours per person', ascending=False)
        
        fig4 = px.bar(gap_df, x='Process', y='Manhours per person', color='Station',
                      title="📊 Human Resource Allocation Gaps",
                      labels={'Manhours per person': 'Manhours/Person'},
                      category_orders={"Process": gap_df['Process'].tolist()})
        fig4.update_layout(hovermode="x unified", xaxis_tickangle=-45)
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("🚨 **Top 7 Processes with Highest Resource Gaps:**")
        for _, row in gap_df.head(7).iterrows():
            st.write(f"• {row['Process']} ({row['Station']}): {row['Manhours per person']:.2f} hrs/person "
                     f"with {row['Number of people']} people assigned")

    # ✨ Tab 6: CSV Downloads
    with tab6:
        st.subheader("📤 Downloadable Data")
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button("Download Total Manhours CSV", convert_df(total_df), "total_manhours.csv", "text/csv")
        st.download_button("Download Process Averages CSV", convert_df(process_avg_df), "process_avg.csv", "text/csv")
        st.download_button("Download Resource Gap CSV", convert_df(gap_df), "resource_gaps.csv", "text/csv")
        if not outliers_df.empty:
            st.download_button("Download Z-Score Outliers CSV", convert_df(outliers_df), "outliers.csv", "text/csv")

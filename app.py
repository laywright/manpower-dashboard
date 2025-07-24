import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(
    page_title="Bus Process Dashboard",
    layout="wide",
    page_icon="🚌"
)

# -------------------------
# Sidebar - File Upload & Filters
# -------------------------
st.sidebar.title("📁 Upload Data & Filters")
file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"], help="Upload an Excel file with a 'Manhours' sheet")

if file:
    # -------------------------
    # Cache loading function with error handling
    # -------------------------
    @st.cache_data(ttl=3600, max_entries=5)
    def load_data(file):
        try:
            xls = pd.ExcelFile(file)
            df = pd.read_excel(xls, sheet_name='Manhours')
            df = df.dropna(how='all').rename(columns=lambda x: str(x).strip())
            df['Number of people'] = pd.to_numeric(df['Number of people'], errors='coerce')
            
            # Clean blanks
            df = df.dropna(subset=['Process'])
            df = df[df['Process'].str.strip() != '']
            
            return df
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")
            st.stop()

    df = load_data(file)
    
    # -------------------------
    # Sidebar Filters
    # -------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filters")
    
    # Station filter
    all_stations = df['Station'].unique()
    station_filter = st.sidebar.multiselect(
        "Filter by Station",
        options=all_stations,
        default=all_stations
    )
    
    # Process filter
    all_processes = df['Process'].unique()
    process_filter = st.sidebar.multiselect(
        "Filter by Process",
        options=all_processes,
        default=all_processes
    )
    
    # Apply filters
    df = df[df['Station'].isin(station_filter)]
    df = df[df['Process'].isin(process_filter)]
    
    # -------------------------
    # Data Calculations
    # -------------------------
    bus_columns = [col for col in df.columns if str(col).startswith('Bus')]
    
    # Calculate metrics
    df['Avg_Time_Per_Process'] = df[bus_columns].mean(axis=1)
    df['Total_Process_Time'] = df[bus_columns].sum(axis=1)
    df['Avg_Cycle_Time_Per_Process'] = df['Total_Process_Time'] / len(bus_columns)
    df['Variance'] = df[bus_columns].var(axis=1)
    df['Avg_Manhours'] = df[bus_columns].mean(axis=1)
    df['Gap_Score'] = df['Avg_Manhours'] / df['Number of people'].replace(0, pd.NA)
    
    # -------------------------
    # Main Section - Tabs
    # -------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Summary KPIs", "📊 Process Trends", "🚨 Outliers", "📉 Resource Gaps"])
    
    with tab1:
        st.header("🔍 Summary KPIs")
        
        # Compact view toggle
        compact_view = st.checkbox("Compact View", key="compact_view")
        
        if compact_view:
            col1, col2 = st.columns(2)
        else:
            col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        total_manhours = df[bus_columns].multiply(df['Number of people'], axis=0).sum().sum()
        avg_process_time = df['Avg_Time_Per_Process'].mean()
        max_gap = df['Gap_Score'].max()
        process_count = df['Process'].nunique()
        
        col1.metric("Total Manhours", f"{total_manhours:,.0f} hrs")
        col2.metric("Avg Process Time", f"{avg_process_time:.2f} hrs")
        
        if not compact_view:
            col3.metric("Max Manhour Gap", f"{max_gap:.2f} hrs/person")
            col4.metric("Unique Processes", process_count)
        
        # Charts
        fig1 = px.bar(
            df, 
            x='Process', 
            y='Avg_Time_Per_Process', 
            title="⏱️ Avg Time per Process", 
            color='Avg_Time_Per_Process', 
            color_continuous_scale='Cividis',
            hover_data=['Station']
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Heatmap
        st.subheader("Bus Correlation Matrix")
        fig_heat = px.imshow(
            df[bus_columns].corr(),
            title="Bus Correlation Matrix",
            color_continuous_scale='Viridis',
            labels=dict(color="Correlation")
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    
    with tab2:
        st.header("📊 Detailed Process Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_bus = st.selectbox("Select a Bus:", bus_columns)
        
        with col2:
            sort_option = st.selectbox("Sort by:", 
                                     ['Process', 'Station', 'Manhours'], 
                                     index=0)
        
        trend_df = df[['Station', 'Process', selected_bus]].sort_values(by=sort_option)
        trend_df = trend_df.rename(columns={selected_bus: "Manhours"})
        
        fig2 = px.bar(
            trend_df, 
            x='Process', 
            y='Manhours', 
            title=f"Manhours for {selected_bus}", 
            color='Station',
            hover_data=['Station']
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Show raw data
        if st.checkbox("Show raw data", key="trend_raw_data"):
            st.dataframe(trend_df)
    
    with tab3:
        st.header("🚨 Outlier Detection")
        
        df_long = df.melt(
            id_vars=['Station', 'Process'], 
            value_vars=bus_columns, 
            var_name='Bus', 
            value_name='Manhours'
        )
        
        top7_var_processes = df.nlargest(7, 'Variance')[['Station', 'Process']]
        filtered_long = df_long.merge(top7_var_processes, on=['Station', 'Process'])
        
        filtered_long['Z_Score'] = filtered_long.groupby('Process')['Manhours'].transform(
            lambda x: (x - x.mean()) / x.std(ddof=0)
        
        outliers_df = filtered_long[abs(filtered_long['Z_Score']) > 2]
        
        if not outliers_df.empty:
            fig3 = px.scatter(
                outliers_df, 
                x='Process', 
                y='Manhours', 
                color='Bus', 
                title='Outlier Buses per Process', 
                hover_data=['Station', 'Z_Score'],
                size='Z_Score'
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            st.subheader("Outlier Details")
            st.dataframe(
                outliers_df[['Process', 'Station', 'Bus', 'Manhours', 'Z_Score']]
                .sort_values('Z_Score', ascending=False)
                .style.background_gradient(subset=['Z_Score'], cmap='Reds')
            )
        else:
            st.success("✅ No strong outliers found (Z-Score > 2).")
    
    with tab4:
        st.header("📉 Resource Allocation Gaps")
        
        gap_df = df[['Station', 'Process', 'Gap_Score', 'Number of people']] \
            .sort_values(by='Gap_Score', ascending=False) \
            .dropna(subset=['Gap_Score'])
        
        fig4 = px.bar(
            gap_df.head(15), 
            x='Process', 
            y='Gap_Score', 
            color='Station', 
            title="Top Resource Allocation Gaps", 
            labels={'Gap_Score': 'Manhours per Person'},
            hover_data=['Number of people']
        )
        st.plotly_chart(fig4, use_container_width=True)
        
        st.subheader("Top 15 Processes by Resource Gap")
        st.dataframe(
            gap_df.head(15).style.background_gradient(
                subset=['Gap_Score'], 
                cmap='OrRd'
            )
        )
        
        # Export functionality
        st.markdown("---")
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Analysis to Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Analysis', index=False)
                    gap_df.to_excel(writer, sheet_name='Resource_Gaps', index=False)
                
                st.download_button(
                    label="Download Excel",
                    data=output.getvalue(),
                    file_name='bus_analysis.xlsx',
                    mime='application/vnd.ms-excel'
                )
        
        with col2:
            if st.button("Export Outliers to CSV"):
                csv = outliers_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name='bus_outliers.csv',
                    mime='text/csv'
                )
else:
    st.info("📂 Please upload an Excel file to begin analysis.")
    st.image("https://via.placeholder.com/800x400?text=Upload+Excel+File+to+Start", use_column_width=True)

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown("🚌 **Bus Process Dashboard** | 📅 Updated: " + pd.Timestamp.now().strftime("%Y-%m-%d"))

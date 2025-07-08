import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from matplotlib import cm

# Set page config
st.set_page_config(
    page_title="Bus Maintenance Process Analysis",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stSelectbox>div>div>select {
        background-color: #e8f5e9;
    }
    .stSlider>div>div>div>div {
        background-color: #4CAF50;
    }
    .reportview-container .markdown-text-container {
        font-family: monospace;
    }
    .sidebar .sidebar-content {
        background-color: #e8f5e9;
    }
    </style>
    """, unsafe_allow_html=True)

# App title
st.title('🚌 Bus Maintenance Process Analysis')
st.markdown("""
This dashboard analyzes the time spent on various maintenance processes across different buses.
Use the controls in the sidebar to filter and explore the data.
""")

# File upload
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Load data
        @st.cache_data
        def load_data(file):
            df = pd.read_excel(file, sheet_name='Analysis')
            df.dropna(how='all', inplace=True)
            df.rename(columns={df.columns[0]: 'Bus'}, inplace=True)
            return df
        
        df = load_data(uploaded_file)
        
        # Sidebar filters
        st.sidebar.header("Filters")
        selected_buses = st.sidebar.multiselect(
            "Select Buses to Display",
            options=df['Bus'].unique(),
            default=df['Bus'].unique()
        )
        
        # Filter data based on selection
        filtered_df = df[df['Bus'].isin(selected_buses)]
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "⏱️ Process Times", 
            "🚌 Bus Analysis", 
            "🔍 Deep Dive"
        ])
        
        with tab1:
            st.header("Overview Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Data Preview")
                st.dataframe(filtered_df.head(), use_container_width=True)
                
            with col2:
                st.subheader("Summary Statistics")
                st.dataframe(filtered_df.describe(), use_container_width=True)
            
            st.subheader("Total Man-Hours per Bus")
            df['Total Man-Hours'] = df.drop(columns='Bus').sum(axis=1)
            df_sorted = df[['Bus', 'Total Man-Hours']].sort_values(by='Bus')
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(df_sorted['Bus'].astype(str), df_sorted['Total Man-Hours'], color='skyblue')
            ax.set_title('Total Man-Hours per Bus')
            ax.set_xlabel('Bus Number')
            ax.set_ylabel('Total Man-Hours')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y')
            st.pyplot(fig)
            
        with tab2:
            st.header("Process Time Analysis")
            
            avg_times = filtered_df.drop(columns='Bus').mean().sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Average Time per Process")
                fig, ax = plt.subplots(figsize=(10, 6))
                avg_times.plot(kind='bar', color='skyblue', ax=ax)
                ax.set_title('Average Time Spent per Process (in Hours)')
                ax.set_ylabel('Average Hours')
                ax.tick_params(axis='x', rotation=90)
                ax.grid(axis='y')
                st.pyplot(fig)
                
            with col2:
                st.subheader("Process Time Variability")
                std_per_process = filtered_df.drop(columns='Bus').std().sort_values(ascending=False)
                st.dataframe(std_per_process.rename("Standard Deviation"), use_container_width=True)
                st.caption("Higher values indicate more inconsistency in process times")
            
            st.subheader("Process Time Distribution")
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.boxplot(data=filtered_df.drop(columns='Bus'), orient='h', palette='Set2', ax=ax)
            ax.set_title('Variation in Process Times Across Buses (Boxplot)')
            ax.set_xlabel('Hours')
            ax.set_ylabel('Process')
            ax.grid(axis='x')
            st.pyplot(fig)
            
        with tab3:
            st.header("Bus-Specific Analysis")
            
            selected_bus = st.selectbox(
                "Select a Bus to Analyze",
                options=filtered_df['Bus'].unique()
            )
            
            bus_data = filtered_df[filtered_df['Bus'] == selected_bus].drop(columns='Bus').T
            bus_data.columns = ['Hours']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Process Times for Bus {selected_bus}")
                fig, ax = plt.subplots(figsize=(8, 8))
                bus_data.plot(kind='pie', y='Hours', autopct='%1.1f%%', ax=ax, legend=False)
                ax.set_ylabel('')
                st.pyplot(fig)
                
            with col2:
                st.subheader(f"Time Breakdown for Bus {selected_bus}")
                st.dataframe(bus_data.sort_values('Hours', ascending=False), use_container_width=True)
                
                # Compare to average
                avg_data = filtered_df.drop(columns='Bus').mean()
                comparison = pd.DataFrame({
                    'Bus Time': bus_data['Hours'],
                    'Average Time': avg_data
                })
                comparison['Difference'] = comparison['Bus Time'] - comparison['Average Time']
                st.write("Comparison to Average:")
                st.dataframe(comparison, use_container_width=True)
                
        with tab4:
            st.header("Deep Dive Analysis")
            
            st.subheader("Heatmap of Process Times")
            fig, ax = plt.subplots(figsize=(14, 8))
            sns.heatmap(
                filtered_df.set_index('Bus'), 
                cmap='YlGnBu', 
                linewidths=0.5, 
                linecolor='gray', 
                annot=True, 
                fmt=".1f",
                ax=ax
            )
            ax.set_title('Time Spent on Each Process per Bus (Hours)')
            ax.set_xlabel('Process')
            ax.set_ylabel('Bus')
            st.pyplot(fig)
            
            # Outlier detection
            st.subheader("Outlier Detection")
            process_data = filtered_df.drop(columns='Bus')
            thresholds = process_data.mean() + 1.5 * process_data.std()
            outliers = (process_data > thresholds).stack()
            high_usage = outliers[outliers].reset_index()
            high_usage.columns = ['Bus Index', 'Process', 'Flag']
            high_usage['Bus'] = filtered_df['Bus'].iloc[high_usage['Bus Index']].values
            
            if not high_usage.empty:
                st.warning("🚨 Buses with Unusually High Time on Certain Processes:")
                for _, row in high_usage.iterrows():
                    st.write(f"- Bus {row['Bus']} spent unusually high time on '{row['Process']}'")
                    
                # Show outliers in a table
                st.dataframe(
                    high_usage[['Bus', 'Process']].rename(columns={
                        'Bus': 'Bus Number',
                        'Process': 'Process with High Time'
                    }),
                    use_container_width=True
                )
            else:
                st.success("✅ No significant outliers detected in process time.")
                
            # Correlation analysis
            st.subheader("Process Time Correlations")
            fig, ax = plt.subplots(figsize=(10, 8))
            sns.heatmap(
                process_data.corr(),
                annot=True,
                cmap='coolwarm',
                center=0,
                ax=ax
            )
            ax.set_title('Correlation Between Processes')
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("ℹ️ Please upload an Excel file to begin analysis.")
    st.markdown("""
    ### Expected File Format:
    - First column should contain Bus identifiers
    - Subsequent columns should contain time values for different processes
    - Sheet name should be 'Analysis' or you'll need to modify the code
    """)

# Add some space at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)

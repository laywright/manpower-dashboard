import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import time

# Set page config
st.set_page_config(
    page_title="Process Time Analytics",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #e9ecef;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 0.3rem;
    }
    .metric-card {
        background-color: white;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .stDataFrame {
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

def load_data(uploaded_file):
    """Load and preprocess the data"""
    try:
        if uploaded_file is not None:
            df = pd.read_excel(uploaded_file, sheet_name='Analysis')
            
            # Data cleaning
            df.dropna(how='all', inplace=True)
            df.rename(columns={df.columns[0]: 'Bus'}, inplace=True)
            
            # Calculate additional metrics
            process_columns = [col for col in df.columns if col != 'Bus']
            df['Total'] = df[process_columns].sum(axis=1)
            return df
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

@st.cache_data
def process_data(df):
    """Cache data processing operations"""
    return df

def overview_page(df):
    """Dashboard overview page with key metrics"""
    st.title("⏱️ Process Time Analytics Dashboard")
    
    if df is not None:
        # Summary Statistics at the top
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Buses Analyzed", len(df))
        with col2:
            st.metric("Total Processes Tracked", len(df.columns) - 2)  # Exclude Bus and Total
        with col3:
            st.metric("Total Hours Recorded", f"{df['Total'].sum():,.1f}")
        
        st.markdown("---")
        
        # Overview Statistics
        st.subheader("Overview Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
        with col2:
            st.markdown("#### Descriptive Statistics")
            st.dataframe(df.describe(), use_container_width=True)
        
        # Detailed Man-Hours by Bus (Dropdown)
        st.markdown("---")
        st.subheader("Detailed Hours by Bus")
        
        selected_bus = st.selectbox(
            "Select Bus to View Detailed Hours",
            options=df['Bus'].unique()
        )
        
        if selected_bus:
            bus_data = df[df['Bus'] == selected_bus].drop(columns=['Bus', 'Total'])
            bus_data = bus_data.T.reset_index()
            bus_data.columns = ['Process', 'Hours']
            
            st.dataframe(
                bus_data.sort_values('Hours', ascending=False),
                hide_index=True,
                use_container_width=True
            )
            
            # Visualization of selected bus
            fig = px.bar(
                bus_data.sort_values('Hours', ascending=True),
                x='Hours',
                y='Process',
                orientation='h',
                title=f"Process Hours for Bus {selected_bus}",
                labels={'Hours': 'Hours', 'Process': 'Process'},
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

def time_analysis_page(df):
    """Detailed time analysis visualizations"""
    st.title("🕒 Time Distribution Analysis")
    
    if df is not None:
        # Process selection
        processes = [col for col in df.columns if col not in ['Bus', 'Total']]
        selected_processes = st.multiselect(
            "Select Processes to Analyze",
            options=processes,
            default=processes[:3]
        )
        
        if selected_processes:
            tab1, tab2, tab3 = st.tabs([
                "Average Time", 
                "Variability", 
                "Heatmap"
            ])
            
            with tab1:
                st.subheader("Average Time per Process")
                avg_times = df[selected_processes].mean().sort_values(ascending=False)
                
                fig = px.bar(
                    avg_times,
                    x=avg_times.values,
                    y=avg_times.index,
                    orientation='h',
                    color=avg_times.values,
                    color_continuous_scale='Blues',
                    labels={'x': 'Average Hours', 'y': 'Process'},
                    height=500
                )
                fig.update_layout(
                    title="Average Time Spent per Process (in Hours)",
                    xaxis_title="Average Hours",
                    yaxis_title="Process",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show data table
                st.dataframe(
                    avg_times.reset_index().rename(columns={'index': 'Process', 0: 'Average Hours'}),
                    hide_index=True,
                    use_container_width=True
                )
            
            with tab2:
                st.subheader("Process Time Variability")
                
                # Boxplot
                fig = px.box(
                    df[selected_processes],
                    orientation='h',
                    points="all",
                    height=500
                )
                fig.update_layout(
                    title="Variation in Process Times Across Buses",
                    xaxis_title="Hours",
                    yaxis_title="Process"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Standard deviation
                st.subheader("Standard Deviation per Process")
                std_dev = df[selected_processes].std().sort_values(ascending=False)
                st.dataframe(
                    std_dev.reset_index().rename(columns={'index': 'Process', 0: 'Std Dev'}),
                    hide_index=True,
                    use_container_width=True
                )
            
            with tab3:
                st.subheader("Time Spent Heatmap")
                
                # Create heatmap
                fig = px.imshow(
                    df[selected_processes],
                    x=selected_processes,
                    y=df['Bus'],
                    color_continuous_scale='YlGnBu',
                    labels=dict(x="Process", y="Bus", color="Hours"),
                    aspect="auto"
                )
                fig.update_layout(
                    title="Time Spent on Each Process per Bus (Hours)",
                    xaxis_title="Process",
                    yaxis_title="Bus"
                )
                st.plotly_chart(fig, use_container_width=True)

def outlier_analysis_page(df):
    """Identify and analyze outliers in the data"""
    st.title("🚨 Outlier Detection")
    
    if df is not None:
        st.markdown("""
        This section identifies buses that spent unusually high time on specific processes.
        Outliers are calculated as values exceeding 1.5 times the interquartile range (IQR).
        """)
        
        processes = [col for col in df.columns if col not in ['Bus', 'Total']]
        selected_process = st.selectbox(
            "Select Process for Outlier Analysis",
            options=processes
        )
        
        if selected_process:
            # Calculate thresholds
            q1 = df[selected_process].quantile(0.25)
            q3 = df[selected_process].quantile(0.75)
            iqr = q3 - q1
            upper_threshold = q3 + 1.5 * iqr
            
            # Identify outliers
            outliers = df[df[selected_process] > upper_threshold]
            
            if not outliers.empty:
                st.warning(f"Found {len(outliers)} outliers for {selected_process}")
                
                # Show outlier details
                st.subheader("Outlier Details")
                st.dataframe(
                    outliers[['Bus', selected_process]].sort_values(
                        by=selected_process, ascending=False
                    ),
                    use_container_width=True
                )
                
                # Visualization
                fig = px.scatter(
                    df,
                    x='Bus',
                    y=selected_process,
                    color=selected_process,
                    color_continuous_scale='Reds',
                    labels={'Bus': 'Bus Number', selected_process: 'Hours'},
                    height=500
                )
                fig.add_hline(
                    y=upper_threshold,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Outlier Threshold",
                    annotation_position="top right"
                )
                fig.update_layout(
                    title=f"Outlier Detection for {selected_process}",
                    xaxis_title="Bus Number",
                    yaxis_title="Hours"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success(f"No outliers detected for {selected_process}")

# Main app logic
def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Time Analysis", "Outlier Detection"]
    )
    
    # File uploader in main content area
    st.sidebar.title("Data Upload")
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
    
    # Load and process data
    raw_data = load_data(uploaded_file)
    df = process_data(raw_data) if raw_data is not None else None
    
    # Display selected page
    if page == "Overview":
        overview_page(df)
    elif page == "Time Analysis":
        time_analysis_page(df)
    elif page == "Outlier Detection":
        outlier_analysis_page(df)

if __name__ == "__main__":
    main()

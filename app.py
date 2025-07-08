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
            df['Total Man-Hours'] = df.drop(columns='Bus').sum(axis=1)
            return df
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

@st.cache_data
def process_data(df):
    """Cache data processing operations"""
    # Any heavy data processing would go here
    return df

def overview_page(df):
    """Dashboard overview page with key metrics"""
    st.title("⏱️ Process Time Analytics Dashboard")
    st.markdown("""
    This dashboard provides comprehensive analysis of process times across different buses. 
    Use the sidebar to navigate between different analytical views.
    """)
    
    if df is not None:
        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Buses Analyzed", len(df))
        with col2:
            st.metric("Total Processes Tracked", len(df.columns) - 2)  # Exclude Bus and Total
        with col3:
            st.metric("Total Man-Hours Recorded", f"{df['Total Man-Hours'].sum():,.1f}")
        
        # Data Preview
        st.subheader("Data Preview")
        st.dataframe(df.head(), use_container_width=True)
        
        # Summary Statistics
        st.subheader("Summary Statistics")
        st.dataframe(df.describe(), use_container_width=True)

def time_analysis_page(df):
    """Detailed time analysis visualizations"""
    st.title("🕒 Time Distribution Analysis")
    
    if df is not None:
        # Process selection
        processes = df.columns[1:-1]  # Exclude Bus and Total
        selected_processes = st.multiselect(
            "Select Processes to Analyze",
            options=processes,
            default=processes[:3]
        )
        
        if selected_processes:
            tab1, tab2, tab3, tab4 = st.tabs([
                "Average Time", 
                "Total per Bus", 
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
                st.subheader("Total Man-Hours per Bus")
                df_sorted = df[['Bus'] + selected_processes].sort_values(by='Bus')
                df_sorted['Total'] = df_sorted[selected_processes].sum(axis=1)
                
                # Interactive bar chart
                fig = px.bar(
                    df_sorted,
                    x='Bus',
                    y='Total',
                    color='Total',
                    color_continuous_scale='Viridis',
                    labels={'Bus': 'Bus Number', 'Total': 'Total Man-Hours'},
                    height=500
                )
                fig.update_layout(
                    title="Total Man-Hours per Bus",
                    xaxis_title="Bus Number",
                    yaxis_title="Total Man-Hours"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show data table
                st.dataframe(
                    df_sorted[['Bus', 'Total']],
                    hide_index=True,
                    use_container_width=True
                )
            
            with tab3:
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
            
            with tab4:
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
        
        processes = df.columns[1:-1]  # Exclude Bus and Total
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

def report_page(df):
    """Generate and download reports"""
    st.title("📊 Generate Report")
    
    if df is not None:
        st.markdown("""
        Generate a comprehensive report of the analysis with selected visualizations.
        """)
        
        # Report options
        col1, col2 = st.columns(2)
        with col1:
            include_avg = st.checkbox("Include Average Time Chart", True)
            include_total = st.checkbox("Include Total per Bus Chart", True)
        with col2:
            include_variability = st.checkbox("Include Variability Analysis", True)
            include_outliers = st.checkbox("Include Outlier Analysis", True)
        
        # Generate report
        if st.button("Generate Report"):
            with st.spinner("Generating report..."):
                time.sleep(2)  # Simulate processing time
                
                report_content = f"""
                <html>
                    <head>
                        <title>Process Time Analysis Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 2rem; }}
                            h1 {{ color: #2c3e50; }}
                            .chart {{ margin-bottom: 2rem; }}
                            table {{ border-collapse: collapse; width: 100%; margin-bottom: 1rem; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <h1>Process Time Analysis Report</h1>
                        <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        
                        <h2>Dataset Overview</h2>
                        <p>Total buses analyzed: {len(df)}</p>
                        <p>Total processes tracked: {len(df.columns) - 2}</p>
                        <p>Total man-hours recorded: {df['Total Man-Hours'].sum():,.1f}</p>
                """
                
                if include_avg:
                    avg_times = df.drop(columns=['Bus', 'Total Man-Hours']).mean().sort_values(ascending=False)
                    report_content += f"""
                    <h2>Average Time per Process</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{avg_time_chart_to_base64(avg_times)}" width="800">
                    </div>
                    """
                
                if include_total:
                    df_sorted = df[['Bus', 'Total Man-Hours']].sort_values(by='Bus')
                    report_content += f"""
                    <h2>Total Man-Hours per Bus</h2>
                    <div class="chart">
                        <img src="data:image/png;base64,{total_time_chart_to_base64(df_sorted)}" width="800">
                    </div>
                    """
                
                report_content += """
                    </body>
                </html>
                """
                
                # Create download link
                st.success("Report generated successfully!")
                st.download_button(
                    label="Download Report (HTML)",
                    data=report_content,
                    file_name="process_time_analysis_report.html",
                    mime="text/html"
                )

def avg_time_chart_to_base64(avg_times):
    """Helper function to convert avg time chart to base64"""
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_times.plot(kind='barh', color='skyblue', ax=ax)
    ax.set_title('Average Time per Process')
    ax.set_xlabel('Hours')
    ax.grid(axis='x')
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def total_time_chart_to_base64(df_sorted):
    """Helper function to convert total time chart to base64"""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df_sorted['Bus'].astype(str), df_sorted['Total Man-Hours'], color='skyblue')
    ax.set_title('Total Man-Hours per Bus')
    ax.set_xlabel('Bus Number')
    ax.set_ylabel('Total Man-Hours')
    plt.xticks(rotation=45)
    ax.grid(axis='y')
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# Main app logic
def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Time Analysis", "Outlier Detection", "Generate Report"]
    )
    
    # Theme selector
    st.sidebar.markdown("---")
    theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("""
        <style>
            .main {
                background-color: #1a1a1a;
                color: white;
            }
            .sidebar .sidebar-content {
                background-color: #2d2d2d;
            }
            .metric-card {
                background-color: #2d2d2d;
                color: white;
            }
            h1, h2, h3, h4, h5, h6 {
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
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
    elif page == "Generate Report":
        report_page(df)

if __name__ == "__main__":
    main()

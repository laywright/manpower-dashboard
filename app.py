import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import cm
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Manufacturing Process Analysis",
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
    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# App title
st.title('🚌 Body Process Analysis')
st.markdown("""
This dashboard analyzes the time spent on processes across different buses.
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
        
        # Calculate total man-hours
        filtered_df['Total Man-Hours'] = filtered_df.drop(columns='Bus').sum(axis=1)
        df_sorted = filtered_df[['Bus', 'Total Man-Hours']].sort_values(by='Bus')
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview", 
            "⏱️ Process Times", 
            "🚌 Bus Analysis", 
            "🔍 Deep Dive"
        ])
        
        with tab1:
            st.header("Overview Dashboard")
            
            # Metrics Row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Total Buses", len(filtered_df))
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col2:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Average Hours", f"{filtered_df['Total Man-Hours'].mean():.1f}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col3:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                st.metric("Total Hours", f"{filtered_df['Total Man-Hours'].sum():.1f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Interactive Bus Hours Selector
            st.subheader("Bus Hours Explorer")
            
            # Toggle to show all buses
            show_all = st.toggle("Show All Buses", value=False)
            
            if show_all:
                bus_hours = df_sorted
            else:
                bus_hours = df_sorted.head(5)
                st.caption(f"Showing first 5 of {len(df_sorted)} buses")
            
            # Plotly interactive bar chart
            fig = px.bar(
                bus_hours,
                x='Bus',
                y='Total Man-Hours',
                color='Total Man-Hours',
                color_continuous_scale='Blues',
                labels={'Bus': 'Bus Number', 'Total Man-Hours': 'Total Hours'},
                height=500
            )
            fig.update_layout(
                title="Total Hours per Bus",
                xaxis_title="Bus Number",
                yaxis_title="Total Hours",
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(
                bus_hours.set_index('Bus').style.background_gradient(cmap='Blues'),
                use_container_width=True
            )
            
        with tab2:
            st.header("Process Time Analysis")
            
            avg_times = filtered_df.drop(columns=['Bus', 'Total Man-Hours']).mean().sort_values(ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Average Time per Process")
                fig = px.bar(
                    avg_times,
                    x=avg_times.values,
                    y=avg_times.index,
                    orientation='h',
                    color=avg_times.values,
                    color_continuous_scale='Teal',
                    labels={'x': 'Average Hours', 'y': 'Process'},
                    height=500
                )
                fig.update_layout(
                    title="Average Time Spent per Process (Hours)",
                    xaxis_title="Average Hours",
                    yaxis_title="Process",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader("Process Time Variability")
                std_per_process = filtered_df.drop(columns=['Bus', 'Total Man-Hours']).std().sort_values(ascending=False)
                
                fig = px.bar(
                    std_per_process,
                    x=std_per_process.values,
                    y=std_per_process.index,
                    orientation='h',
                    color=std_per_process.values,
                    color_continuous_scale='Oranges',
                    labels={'x': 'Standard Deviation', 'y': 'Process'},
                    height=500
                )
                fig.update_layout(
                    title="Process Time Variability",
                    xaxis_title="Standard Deviation",
                    yaxis_title="Process",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Process Time Distribution")
            fig = px.box(
                filtered_df.drop(columns=['Bus', 'Total Man-Hours']),
                orientation='h',
                points="all",
                height=600
            )
            fig.update_layout(
                title="Distribution of Process Times Across Buses",
                xaxis_title="Hours",
                yaxis_title="Process"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            st.header("Bus-Specific Analysis")
            
            selected_bus = st.selectbox(
                "Select a Bus to Analyze",
                options=filtered_df['Bus'].unique()
            )
            
            bus_data = filtered_df[filtered_df['Bus'] == selected_bus].drop(columns=['Bus', 'Total Man-Hours']).T
            bus_data.columns = ['Hours']
            bus_data = bus_data.sort_values('Hours', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Process Distribution for Bus {selected_bus}")
                fig = px.pie(
                    bus_data,
                    values='Hours',
                    names=bus_data.index,
                    hole=0.3,
                    height=500,
                    color_discrete_sequence=px.colors.sequential.Teal_r
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    title=f"Time Distribution for Bus {selected_bus}",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.subheader(f"Time Breakdown for Bus {selected_bus}")
                
                # Horizontal bar chart
                fig = px.bar(
                    bus_data.reset_index(),
                    x='Hours',
                    y='index',
                    orientation='h',
                    color='Hours',
                    color_continuous_scale='Teal',
                    labels={'index': 'Process', 'Hours': 'Hours'},
                    height=500
                )
                fig.update_layout(
                    title=f"Process Hours for Bus {selected_bus}",
                    xaxis_title="Hours",
                    yaxis_title="Process",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Compare to average
                avg_data = filtered_df.drop(columns=['Bus', 'Total Man-Hours']).mean()
                comparison = pd.DataFrame({
                    'Process': bus_data.index,
                    'Bus Hours': bus_data['Hours'],
                    'Average Hours': avg_data
                })
                comparison['Difference'] = comparison['Bus Hours'] - comparison['Average Hours']
                
                st.dataframe(
                    comparison.style.background_gradient(
                        cmap='RdBu', 
                        subset=['Difference'],
                        vmin=-comparison['Difference'].abs().max(),
                        vmax=comparison['Difference'].abs().max()
                    ),
                    use_container_width=True
                )
                
        with tab4:
            st.header("Deep Dive Analysis")
            
            st.subheader("Heatmap of Process Times")
            fig = px.imshow(
                filtered_df.set_index('Bus').drop(columns='Total Man-Hours'),
                color_continuous_scale='YlGnBu',
                labels=dict(x="Process", y="Bus", color="Hours"),
                aspect="auto",
                height=600
            )
            fig.update_layout(
                title="Time Spent on Each Process per Bus (Hours)",
                xaxis_title="Process",
                yaxis_title="Bus"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Outlier detection
            st.subheader("Outlier Detection")
            process_data = filtered_df.drop(columns=['Bus', 'Total Man-Hours'])
            thresholds = process_data.mean() + 1.5 * process_data.std()
            outliers = (process_data > thresholds).stack()
            high_usage = outliers[outliers].reset_index()
            high_usage.columns = ['Bus Index', 'Process', 'Flag']
            high_usage['Bus'] = filtered_df['Bus'].iloc[high_usage['Bus Index']].values
            
            if not high_usage.empty:
                st.warning("🚨 Buses with Unusually High Time on Certain Processes:")
                
                # Interactive scatter plot
                fig = px.scatter(
                    high_usage,
                    x='Bus',
                    y='Process',
                    size=[10]*len(high_usage),
                    color='Process',
                    hover_name='Bus',
                    height=500
                )
                fig.update_layout(
                    title="Outlier Processes by Bus",
                    xaxis_title="Bus",
                    yaxis_title="Process"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Outlier table
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
            fig = px.imshow(
                process_data.corr(),
                color_continuous_scale='RdBu',
                zmin=-1,
                zmax=1,
                height=600
            )
            fig.update_layout(
                title="Correlation Between Processes",
                xaxis_title="Process",
                yaxis_title="Process"
            )
            st.plotly_chart(fig, use_container_width=True)
            
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

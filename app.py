import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .metric-box {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .chart-container {
        border-radius: 10px;
        padding: 15px;
        background-color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# App title
st.title('🚌 Manufacturing Process Analysis')
st.markdown("Analyze time spent on manufacturing processes across different buses")

# File upload
uploaded_file = st.sidebar.file_uploader("📁 Upload Excel File", type=["xlsx"])

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
        st.sidebar.header("🔍 Filters")
        selected_buses = st.sidebar.multiselect(
            "Select Buses",
            options=df['Bus'].unique(),
            default=df['Bus'].unique()
        )
        
        # Filter data
        filtered_df = df[df['Bus'].isin(selected_buses)]
        filtered_df['Total Hours'] = filtered_df.drop(columns='Bus').sum(axis=1)
        df_sorted = filtered_df[['Bus', 'Total Hours']].sort_values(by='Bus')
        
        # Main tabs
        tab1, tab2 = st.tabs(["📊 Overview", "🚌 Bus Analysis"])
        
        with tab1:
            st.header("Total Hours Analysis")
            
            # Toggle for bus selection
            col1, col2 = st.columns([3,1])
            with col1:
                show_all = st.toggle("Show All Buses", value=False, key="toggle_all")
            
            with col2:
                sort_order = st.selectbox("Sort Order", ["Ascending", "Descending"], index=1)
            
            # Sort data based on selection
            df_sorted = df_sorted.sort_values(
                by='Total Hours', 
                ascending=(sort_order == "Ascending")
            )
            
            # Show selected buses
            bus_hours = df_sorted if show_all else df_sorted.head(10)
            
            # Create interactive chart
            with st.container():
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                fig = px.bar(
                    bus_hours,
                    x='Bus',
                    y='Total Hours',
                    color='Total Hours',
                    color_continuous_scale='teal',
                    labels={'Bus': 'Bus Number', 'Total Hours': 'Total Hours'},
                    height=500
                )
                fig.update_layout(
                    title="Total Hours per Bus",
                    xaxis_title="Bus Number",
                    yaxis_title="Total Hours",
                    hovermode="x unified",
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Data table with hours
            with st.expander("View Detailed Data"):
                st.dataframe(
                    bus_hours.set_index('Bus').style.background_gradient(
                        cmap='Blues', 
                        subset=['Total Hours']
                    ),
                    use_container_width=True
                )
        
        with tab2:
            st.header("Bus-Specific Analysis")
            
            # Bus selection
            selected_bus = st.selectbox(
                "Select Bus",
                options=filtered_df['Bus'].unique(),
                key="bus_select"
            )
            
            # Get bus data
            bus_data = filtered_df[filtered_df['Bus'] == selected_bus].drop(columns=['Bus', 'Total Hours']).T
            bus_data.columns = ['Hours']
            bus_data = bus_data.sort_values('Hours', ascending=False)
            
            # Create two columns for charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # Sunburst chart for process breakdown
                fig = px.sunburst(
                    bus_data.reset_index(),
                    path=['index'],
                    values='Hours',
                    color='Hours',
                    color_continuous_scale='teal',
                    height=500,
                    title=f"Process Breakdown for Bus {selected_bus}"
                )
                fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                # Horizontal bar chart
                fig = px.bar(
                    bus_data.reset_index(),
                    x='Hours',
                    y='index',
                    orientation='h',
                    color='Hours',
                    color_continuous_scale='teal',
                    labels={'index': 'Process', 'Hours': 'Hours'},
                    height=500,
                    title=f"Process Hours for Bus {selected_bus}"
                )
                fig.update_layout(
                    xaxis_title="Hours",
                    yaxis_title="Process",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Comparison with average
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader(f"Comparison with Average Hours")
            
            avg_data = filtered_df.drop(columns=['Bus', 'Total Hours']).mean()
            comparison = pd.DataFrame({
                'Process': bus_data.index,
                'Bus Hours': bus_data['Hours'],
                'Average Hours': avg_data
            })
            comparison['Difference'] = comparison['Bus Hours'] - comparison['Average Hours']
            
            # Create comparison chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comparison['Process'],
                y=comparison['Bus Hours'],
                name='Bus Hours',
                marker_color='#4CAF50'
            ))
            fig.add_trace(go.Bar(
                x=comparison['Process'],
                y=comparison['Average Hours'],
                name='Average Hours',
                marker_color='#9E9E9E'
            ))
            fig.update_layout(
                barmode='group',
                height=500,
                xaxis_title="Process",
                yaxis_title="Hours",
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show comparison table
            with st.expander("View Detailed Comparison"):
                st.dataframe(
                    comparison.style.background_gradient(
                        cmap='RdBu', 
                        subset=['Difference'],
                        vmin=-comparison['Difference'].abs().max(),
                        vmax=comparison['Difference'].abs().max()
                    ),
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("ℹ️ Please upload an Excel file to begin analysis.")
    st.markdown("""
    ### Expected File Format:
    - First column: Bus identifiers
    - Subsequent columns: Time values for different processes
    - Sheet name: 'Analysis'
    """)

# Add some space at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)

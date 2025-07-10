import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
st.markdown("This dashboard analyzes the time spent on processes across different buses.")

# File upload
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Load data
        @st.cache_data
        def load_data(file):
            df = pd.read_excel(file, sheet_name='Analysis')
            return df

        df = load_data(uploaded_file)
        df.dropna(how='all', inplace=True)
        df.rename(columns={df.columns[0]: 'Bus'}, inplace=True)

        with st.expander("Preview Uploaded Data"):
            st.dataframe(df.head(10), use_container_width=True)

        # Sidebar filters
        st.sidebar.header("Filters")
        selected_buses = st.sidebar.multiselect(
            "Select Buses to Display",
            options=df['Bus'].unique(),
            default=df['Bus'].unique()
        )

        filtered_df = df[df['Bus'].isin(selected_buses)].copy()
        filtered_df['Total Man-Hours'] = filtered_df.drop(columns='Bus').sum(axis=1)
        df_sorted = filtered_df[['Bus', 'Total Man-Hours']].sort_values(by='Bus')

        # Allow download
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        st.sidebar.download_button(
            "Download Filtered Data",
            convert_df_to_csv(filtered_df),
            "filtered_data.csv",
            "text/csv"
        )

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "⏱️ Process Times", "🚌 Bus Analysis", "🔍 Deep Dive"])

        with tab1:
            st.header("Overview Dashboard")

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

            st.subheader("Bus Hours Explorer")
            show_all = st.toggle("Show All Buses", value=False)
            bus_hours = df_sorted if show_all else df_sorted.head(5)

            fig = px.bar(
                bus_hours,
                x='Bus',
                y='Total Man-Hours',
                color='Total Man-Hours',
                color_continuous_scale='Blues',
                height=500
            )
            fig.update_layout(title="Total Hours per Bus", xaxis_title="Bus", yaxis_title="Hours")
            st.plotly_chart(fig, use_container_width=True)

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
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Process Time Variability")
                stds = filtered_df.drop(columns=['Bus', 'Total Man-Hours']).std().sort_values(ascending=False)
                fig = px.bar(
                    stds,
                    x=stds.values,
                    y=stds.index,
                    orientation='h',
                    color=stds.values,
                    color_continuous_scale='Oranges',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Process Time Distribution")
            fig = px.box(
                filtered_df.drop(columns=['Bus', 'Total Man-Hours']),
                orientation='h',
                points="all",
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.header("Bus-Specific Analysis")
            selected_bus = st.selectbox("Select a Bus to Analyze", options=filtered_df['Bus'].unique())

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
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader(f"Time Breakdown for Bus {selected_bus}")
                fig = px.bar(
                    bus_data.reset_index(),
                    x='Hours',
                    y='index',
                    orientation='h',
                    color='Hours',
                    color_continuous_scale='Teal',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)

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
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Outlier Detection")
            process_data = filtered_df.drop(columns=['Bus', 'Total Man-Hours'])
            thresholds = process_data.mean() + 1.5 * process_data.std()
            outliers = (process_data > thresholds).stack()
            high_usage = outliers[outliers].reset_index()
            high_usage.columns = ['Bus Index', 'Process', 'Flag']
            high_usage['Bus'] = filtered_df['Bus'].iloc[high_usage['Bus Index']].values

            if not high_usage.empty:
                st.warning("🚨 Buses with Unusually High Time on Certain Processes:")
                fig = px.scatter(
                    high_usage,
                    x='Bus',
                    y='Process',
                    size=[10]*len(high_usage),
                    color='Process',
                    hover_name='Bus',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(high_usage[['Bus', 'Process']].rename(columns={
                    'Bus': 'Bus Number', 'Process': 'Process with High Time'
                }), use_container_width=True)
            else:
                st.success("✅ No significant outliers detected.")

            st.subheader("Process Time Correlations")
            corr = process_data.corr()
            fig = px.imshow(corr, color_continuous_scale='RdBu', zmin=-1, zmax=1, height=600)
            st.plotly_chart(fig, use_container_width=True)

            # Show top correlated pairs
            st.subheader("Top Process Correlation Pairs")
            strong_pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
            top_pairs = strong_pairs.unstack().dropna().abs().sort_values(ascending=False).head(5)
            st.table(top_pairs.reset_index().rename(columns={
                'level_0': 'Process A',
                'level_1': 'Process B',
                0: 'Correlation'
            }))

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("ℹ️ Please upload an Excel file to begin analysis.")
    st.markdown("""
    ### Expected File Format:
    - First column should contain Bus identifiers
    - Other columns should contain time values for processes
    - Sheet name should be 'Analysis'
    """)

# Space at bottom
st.markdown("<br><br>", unsafe_allow_html=True)

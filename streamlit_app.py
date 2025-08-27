# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(
    page_title="📶 Simple RSSI Heatmap Tracker",
    page_icon="📶",
    layout="wide"
)

# Initialize session state
if 'data_points' not in st.session_state:
    st.session_state.data_points = []
if 'is_tracking' not in st.session_state:
    st.session_state.is_tracking = False
if 'start_position' not in st.session_state:
    st.session_state.start_position = None

def add_data_point(x, y, rssi):
    """Add a new data point to the session"""
    quality = get_rssi_quality(rssi)
    point = {
        'x': x,
        'y': y, 
        'rssi': rssi,
        'quality': quality,
        'timestamp': datetime.now()
    }
    st.session_state.data_points.append(point)

def get_rssi_quality(rssi):
    """Convert RSSI to quality description"""
    if rssi >= -60:
        return 'Excellent'
    elif rssi >= -70:
        return 'Good'
    elif rssi >= -80:
        return 'Fair'
    elif rssi >= -90:
        return 'Poor'
    else:
        return 'Critical'

def get_rssi_color(rssi):
    """Get color for RSSI value"""
    if rssi >= -60:
        return 'green'
    elif rssi >= -70:
        return 'lightgreen'
    elif rssi >= -80:
        return 'yellow'
    elif rssi >= -90:
        return 'orange'
    else:
        return 'red'

def create_heatmap():
    """Create interactive heatmap using Plotly"""
    if not st.session_state.data_points:
        return None
    
    df = pd.DataFrame(st.session_state.data_points)
    
    fig = go.Figure()
    
    # Add scatter points with color based on RSSI
    fig.add_trace(go.Scatter(
        x=df['x'],
        y=df['y'],
        mode='markers+lines',
        marker=dict(
            size=15,
            color=df['rssi'],
            colorscale=[[0, 'red'], [0.25, 'orange'], [0.5, 'yellow'], 
                       [0.75, 'lightgreen'], [1, 'green']],
            cmin=-100,
            cmax=-40,
            colorbar=dict(
                title="RSSI (dBm)",
                titleside="right"
            ),
            line=dict(width=2, color='white')
        ),
        text=[f'RSSI: {rssi} dBm<br>Position: ({x}, {y})<br>Quality: {quality}' 
              for x, y, rssi, quality in zip(df['x'], df['y'], df['rssi'], df['quality'])],
        hovertemplate='%{text}<extra></extra>',
        name='Measurements',
        line=dict(color='blue', width=2, dash='dash')
    ))
    
    # Add start position
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(size=20, color='blue', symbol='star'),
        name='Start Position',
        hovertemplate='Start Position (0,0)<extra></extra>'
    ))
    
    fig.update_layout(
        title='WiFi Signal Strength Heatmap',
        xaxis_title='X Position (meters)',
        yaxis_title='Y Position (meters)',
        hovermode='closest',
        showlegend=True,
        height=500,
        template='plotly_white'
    )
    
    return fig

def calculate_stats():
    """Calculate statistics from data points"""
    if not st.session_state.data_points:
        return {}
    
    df = pd.DataFrame(st.session_state.data_points)
    rssi_values = df['rssi'].values
    
    stats = {
        'total_points': len(df),
        'avg_rssi': np.mean(rssi_values),
        'min_rssi': np.min(rssi_values),
        'max_rssi': np.max(rssi_values),
        'excellent': len(df[df['rssi'] >= -60]),
        'good': len(df[(df['rssi'] >= -70) & (df['rssi'] < -60)]),
        'fair': len(df[(df['rssi'] >= -80) & (df['rssi'] < -70)]),
        'poor': len(df[(df['rssi'] >= -90) & (df['rssi'] < -80)]),
        'critical': len(df[df['rssi'] < -90]),
        'agv_suitable': len(df[df['rssi'] >= -70]),
        'coverage_percent': (len(df[df['rssi'] >= -70]) / len(df)) * 100 if len(df) > 0 else 0
    }
    
    return stats

# Header
st.title("📶 Simple RSSI Heatmap Tracker")
st.markdown("**Walk around your warehouse and automatically generate WiFi heatmap for AGV/AMR implementation**")

# Create columns for layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("🎮 Controls")
    
    # Manual data entry
    st.subheader("📍 Add Measurement")
    with st.form("add_measurement"):
        x_pos = st.number_input("X Position (meters)", value=0.0, step=1.0)
        y_pos = st.number_input("Y Position (meters)", value=0.0, step=1.0)
        rssi_val = st.number_input("RSSI (dBm)", value=-70, min_value=-120, max_value=-20)
        
        if st.form_submit_button("➕ Add Point"):
            add_data_point(x_pos, y_pos, rssi_val)
            st.success(f"Added point at ({x_pos}, {y_pos}) with {rssi_val} dBm")
            st.rerun()
    
    # Quick add buttons
    st.subheader("🚀 Quick Actions")
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("🎲 Demo Data"):
            # Add sample data for demonstration
            demo_points = [
                (0, 0, -55), (5, 3, -62), (10, -2, -68), (15, 4, -75),
                (-5, 8, -58), (8, 10, -72), (12, -5, -78), (-8, -3, -65),
                (20, 8, -82), (-12, 12, -70), (18, -8, -85), (-15, -10, -88)
            ]
            for x, y, rssi in demo_points:
                add_data_point(x, y, rssi)
            st.success("Demo data added!")
            st.rerun()
    
    with col_b:
        if st.button("🗑️ Clear All"):
            st.session_state.data_points = []
            st.success("All data cleared!")
            st.rerun()
    
    # File upload
    st.subheader("📤 Import/Export")
    uploaded_file = st.file_uploader("Upload CSV data", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if all(col in df.columns for col in ['x', 'y', 'rssi']):
                st.session_state.data_points = []
                for _, row in df.iterrows():
                    add_data_point(row['x'], row['y'], row['rssi'])
                st.success(f"Imported {len(df)} data points!")
                st.rerun()
            else:
                st.error("CSV must have columns: x, y, rssi")
        except Exception as e:
            st.error(f"Error importing file: {e}")

with col2:
    st.header("🗺️ Heatmap Visualization")
    
    # Display heatmap
    if st.session_state.data_points:
        fig = create_heatmap()
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👆 Add measurement points to see the heatmap")
        # Show placeholder
        placeholder_fig = go.Figure()
        placeholder_fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(size=20, color='blue', symbol='star'),
            name='Start Here'
        ))
        placeholder_fig.update_layout(
            title='Your Heatmap Will Appear Here',
            xaxis_title='X Position (meters)',
            yaxis_title='Y Position (meters)',
            height=400,
            template='plotly_white'
        )
        st.plotly_chart(placeholder_fig, use_container_width=True)

# Statistics Dashboard
if st.session_state.data_points:
    st.header("📊 Coverage Analysis")
    
    stats = calculate_stats()
    
    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Points", stats['total_points'])
    with col2:
        st.metric("Avg RSSI", f"{stats['avg_rssi']:.0f} dBm")
    with col3:
        st.metric("Min RSSI", f"{stats['min_rssi']:.0f} dBm")
    with col4:
        st.metric("Max RSSI", f"{stats['max_rssi']:.0f} dBm")
    with col5:
        st.metric("AGV Ready", f"{stats['coverage_percent']:.0f}%")
    
    # Quality breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Signal Quality Breakdown")
        quality_data = {
            'Quality': ['Excellent', 'Good', 'Fair', 'Poor', 'Critical'],
            'Count': [stats['excellent'], stats['good'], stats['fair'], stats['poor'], stats['critical']],
            'RSSI Range': ['≥ -60 dBm', '-70 to -60 dBm', '-80 to -70 dBm', '-90 to -80 dBm', '< -90 dBm']
        }
        quality_df = pd.DataFrame(quality_data)
        
        fig_bar = px.bar(
            quality_df, 
            x='Quality', 
            y='Count',
            color='Quality',
            color_discrete_map={
                'Excellent': 'green',
                'Good': 'lightgreen', 
                'Fair': 'yellow',
                'Poor': 'orange',
                'Critical': 'red'
            },
            title="Data Points by Signal Quality"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        st.subheader("🏭 AGV/AMR Readiness Assessment")
        
        if stats['coverage_percent'] >= 95:
            st.success("✅ **READY FOR DEPLOYMENT**")
            st.write("Excellent WiFi coverage for AGV/AMR operations")
        elif stats['coverage_percent'] >= 80:
            st.warning("⚠️ **NEEDS IMPROVEMENT**")
            st.write("Some areas require better WiFi coverage")
        else:
            st.error("❌ **NOT READY**")
            st.write("Significant WiFi improvements needed")
        
        st.write("**Requirements for AGV/AMR:**")
        st.write("- Minimum -70 dBm signal strength")
        st.write("- 95% coverage in operational areas")
        st.write("- No dead zones on critical paths")
        
        st.write("**Current Status:**")
        st.write(f"- Coverage: {stats['coverage_percent']:.1f}%")
        st.write(f"- Suitable points: {stats['agv_suitable']}/{stats['total_points']}")
        st.write(f"- Problem areas: {stats['poor'] + stats['critical']} points")

    # Download section
    st.subheader("💾 Export Results")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Download CSV Data"):
            df = pd.DataFrame(st.session_state.data_points)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"rssi_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Download Report"):
            report = f"""
RSSI HEATMAP SURVEY REPORT
=========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Data Points: {stats['total_points']}

SIGNAL STRENGTH ANALYSIS:
- Average RSSI: {stats['avg_rssi']:.0f} dBm
- Minimum RSSI: {stats['min_rssi']:.0f} dBm
- Maximum RSSI: {stats['max_rssi']:.0f} dBm
- AGV Suitable Coverage: {stats['coverage_percent']:.1f}%

QUALITY BREAKDOWN:
- Excellent (≥-60 dBm): {stats['excellent']} points
- Good (-70 to -60 dBm): {stats['good']} points  
- Fair (-80 to -70 dBm): {stats['fair']} points
- Poor (-90 to -80 dBm): {stats['poor']} points
- Critical (<-90 dBm): {stats['critical']} points

AGV/AMR READINESS: {"READY" if stats['coverage_percent'] >= 95 else "NEEDS WORK" if stats['coverage_percent'] >= 80 else "NOT READY"}
"""
            st.download_button(
                label="Download Report",
                data=report,
                file_name=f"rssi_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

# Instructions
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### 🚀 Quick Start Guide
    
    1. **Add Measurements**: Use the form on the left to add RSSI measurements at different positions
    2. **Try Demo Data**: Click "Demo Data" to see how the heatmap works
    3. **View Results**: Watch the heatmap update automatically as you add points
    4. **Analyze Coverage**: Check the statistics to see if your warehouse is AGV-ready
    5. **Export Data**: Download CSV data or a detailed report
    
    ### 📱 For Real Warehouse Survey:
    
    1. **Download a WiFi analyzer app** on your phone:
       - Android: "WiFi Analyzer" by VREM (free)
       - iPhone: "WiFi Explorer Lite" (limited free version)
    
    2. **Walk through your warehouse** systematically
    3. **Record RSSI values** at key positions (every 5-10 meters)
    4. **Enter the data** into this tool as you go, or collect and upload later
    
    ### 🎯 AGV/AMR Requirements:
    - **Minimum -70 dBm** for reliable operation
    - **95% coverage** across operational areas  
    - **No dead zones** on critical paths
    - **Good handoff** between access points
    
    ### 📊 Signal Quality Guide:
    - **Green (Excellent)**: -60 dBm or better
    - **Light Green (Good)**: -70 to -60 dBm
    - **Yellow (Fair)**: -80 to -70 dBm  
    - **Orange (Poor)**: -90 to -80 dBm
    - **Red (Critical)**: Below -90 dBm
    """)

# Footer
st.markdown("---")
st.markdown("🏭 **Simple RSSI Heatmap Tracker** - Perfect for warehouse WiFi surveys before AGV/AMR deployment")

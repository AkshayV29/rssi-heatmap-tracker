# streamlit_app_simple.py
import streamlit as st
import json
import csv
import io
from datetime import datetime
import math

st.set_page_config(
    page_title="📶 Simple RSSI Heatmap Tracker",
    page_icon="📶",
    layout="wide"
)

# Initialize session state
if 'data_points' not in st.session_state:
    st.session_state.data_points = []

def add_data_point(x, y, rssi):
    """Add a new data point to the session"""
    quality = get_rssi_quality(rssi)
    point = {
        'x': float(x),
        'y': float(y), 
        'rssi': int(rssi),
        'quality': quality,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
        return '#4CAF50'  # Green
    elif rssi >= -70:
        return '#8BC34A'  # Light Green
    elif rssi >= -80:
        return '#FFC107'  # Yellow
    elif rssi >= -90:
        return '#FF9800'  # Orange
    else:
        return '#F44336'  # Red

def calculate_stats():
    """Calculate statistics from data points"""
    if not st.session_state.data_points:
        return {}
    
    rssi_values = [p['rssi'] for p in st.session_state.data_points]
    
    stats = {
        'total_points': len(st.session_state.data_points),
        'avg_rssi': sum(rssi_values) / len(rssi_values),
        'min_rssi': min(rssi_values),
        'max_rssi': max(rssi_values),
        'excellent': len([p for p in st.session_state.data_points if p['rssi'] >= -60]),
        'good': len([p for p in st.session_state.data_points if -70 <= p['rssi'] < -60]),
        'fair': len([p for p in st.session_state.data_points if -80 <= p['rssi'] < -70]),
        'poor': len([p for p in st.session_state.data_points if -90 <= p['rssi'] < -80]),
        'critical': len([p for p in st.session_state.data_points if p['rssi'] < -90]),
        'agv_suitable': len([p for p in st.session_state.data_points if p['rssi'] >= -70]),
    }
    
    stats['coverage_percent'] = (stats['agv_suitable'] / stats['total_points']) * 100 if stats['total_points'] > 0 else 0
    
    return stats

def create_simple_heatmap():
    """Create a simple text-based heatmap representation"""
    if not st.session_state.data_points:
        return "No data points to display"
    
    # Find bounds
    x_values = [p['x'] for p in st.session_state.data_points]
    y_values = [p['y'] for p in st.session_state.data_points]
    
    min_x, max_x = min(x_values), max(x_values)
    min_y, max_y = min(y_values), max(y_values)
    
    # Create a simple grid representation
    grid_size = 20
    grid = {}
    
    for point in st.session_state.data_points:
        # Normalize to grid coordinates
        if max_x > min_x:
            grid_x = int((point['x'] - min_x) / (max_x - min_x) * grid_size)
        else:
            grid_x = grid_size // 2
            
        if max_y > min_y:
            grid_y = int((point['y'] - min_y) / (max_y - min_y) * grid_size)
        else:
            grid_y = grid_size // 2
            
        grid[(grid_x, grid_y)] = point
    
    return grid, min_x, max_x, min_y, max_y

# Header
st.title("📶 Simple RSSI Heatmap Tracker")
st.markdown("**Walk around your warehouse and create WiFi heatmap for AGV/AMR implementation**")

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
            st.session_state.data_points = []  # Clear existing
            for x, y, rssi in demo_points:
                add_data_point(x, y, rssi)
            st.success("Demo data added!")
            st.rerun()
    
    with col_b:
        if st.button("🗑️ Clear All"):
            st.session_state.data_points = []
            st.success("All data cleared!")
            st.rerun()

with col2:
    st.header("🗺️ Heatmap Visualization")
    
    if st.session_state.data_points:
        # Display points in a table format since we're avoiding plotly
        st.subheader("📊 Measurement Points")
        
        # Create a visual representation
        for i, point in enumerate(st.session_state.data_points):
            color = get_rssi_color(point['rssi'])
            
            # Create colored box using HTML
            st.markdown(f"""
            <div style="
                background-color: {color}; 
                padding: 10px; 
                margin: 5px 0; 
                border-radius: 8px; 
                color: white;
                font-weight: bold;
                display: flex;
                justify-content: space-between;
            ">
                <span>Point {i+1}: ({point['x']}m, {point['y']}m)</span>
                <span>{point['rssi']} dBm - {point['quality']}</span>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.info("👆 Add measurement points to see the visualization")
        st.markdown("""
        ### 📱 How to Use:
        1. **Add measurements** using the form on the left
        2. **Try "Demo Data"** to see how it works
        3. **Walk your warehouse** and record RSSI values
        4. **Download results** when done
        """)

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
        
        # Simple bar chart using progress bars
        st.write("**Excellent (≥-60 dBm):**")
        st.progress(stats['excellent'] / stats['total_points'] if stats['total_points'] > 0 else 0)
        st.write(f"{stats['excellent']} points")
        
        st.write("**Good (-70 to -60 dBm):**")
        st.progress(stats['good'] / stats['total_points'] if stats['total_points'] > 0 else 0)
        st.write(f"{stats['good']} points")
        
        st.write("**Fair (-80 to -70 dBm):**")
        st.progress(stats['fair'] / stats['total_points'] if stats['total_points'] > 0 else 0)
        st.write(f"{stats['fair']} points")
        
        st.write("**Poor (-90 to -80 dBm):**")
        st.progress(stats['poor'] / stats['total_points'] if stats['total_points'] > 0 else 0)
        st.write(f"{stats['poor']} points")
        
        st.write("**Critical (<-90 dBm):**")
        st.progress(stats['critical'] / stats['total_points'] if stats['total_points'] > 0 else 0)
        st.write(f"{stats['critical']} points")
    
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
        # Create CSV data
        csv_data = "x,y,rssi,quality,timestamp\n"
        for point in st.session_state.data_points:
            csv_data += f"{point['x']},{point['y']},{point['rssi']},{point['quality']},{point['timestamp']}\n"
        
        st.download_button(
            label="📄 Download CSV Data",
            data=csv_data,
            file_name=f"rssi_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Create report
        report = f"""RSSI HEATMAP SURVEY REPORT
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

DETAILED MEASUREMENTS:
"""
        for i, point in enumerate(st.session_state.data_points):
            report += f"Point {i+1}: ({point['x']}m, {point['y']}m) = {point['rssi']} dBm ({point['quality']})\n"
        
        st.download_button(
            label="📊 Download Report",
            data=report,
            file_name=f"rssi_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

# Instructions
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### 🚀 Quick Start Guide
    
    1. **Add Measurements**: Use the form to add RSSI measurements at different positions
    2. **Try Demo Data**: Click "Demo Data" to see how the tool works
    3. **View Results**: Check the statistics to see if your warehouse is AGV-ready
    4. **Export Data**: Download CSV data or a detailed report
    
    ### 📱 For Real Warehouse Survey:
    
    1. **Download WiFi analyzer app** on your phone:
       - Android: "WiFi Analyzer" by VREM (free)
       - iPhone: "WiFi Explorer Lite" (free but limited)
    
    2. **Walk through warehouse** systematically (every 5-10 meters)
    3. **Record position and RSSI** values in this tool
    4. **Generate professional report** for your AGV implementation team
    
    ### 🎯 Signal Quality Guide:
    - 🟢 **Excellent (≥-60 dBm)**: Perfect for AGVs
    - 🟢 **Good (-70 to -60 dBm)**: Suitable for AGVs  
    - 🟡 **Fair (-80 to -70 dBm)**: May need improvement
    - 🟠 **Poor (-90 to -80 dBm)**: Unsuitable for AGVs
    - 🔴 **Critical (<-90 dBm)**: No reliable connectivity
    """)

# Footer
st.markdown("---")
st.markdown("🏭 **Simple RSSI Heatmap Tracker** - Perfect for warehouse WiFi surveys before AGV/AMR deployment")

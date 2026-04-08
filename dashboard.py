import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess

st.set_page_config(page_title="Attendance System", layout="wide")

# GET REGISTERED STUDENTS
IMAGE_FOLDER = 'Training_images'
registered_names = []

if os.path.exists(IMAGE_FOLDER):
    all_files = os.listdir(IMAGE_FOLDER)
    for f in all_files:
        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Clean name: "Nana_Aishah.jpg" -> "NANA AISHAH"
            name = os.path.splitext(f)[0].replace("_", " ").upper().strip()
            registered_names.append(name)

total_registered = len(registered_names)

# HEADER
st.title("📊 Real-Time Attendance & Absence Tracker")
st.sidebar.title("System Controls")

attendance_file = 'attendance.csv'

if total_registered > 0:
    present_names = []
    
    if os.path.exists(attendance_file) and os.stat(attendance_file).st_size > 0:
        # Load logs and normalize names for comparison
        df = pd.read_csv(attendance_file, names=['Name', 'Timestamp'], header=None)
        df['Name'] = df['Name'].str.upper().str.strip() 
        present_names = df['Name'].unique().tolist()
    else:
        df = pd.DataFrame(columns=['Name', 'Timestamp'])

    # SET MATHEMATICS: ABSENTEE LOGIC
    # People in the folder MINUS people in the CSV
    absent_names = list(set(registered_names) - set(present_names))
    
    unique_present = len(present_names)
    absent_count = len(absent_names)
    attendance_percentage = (unique_present / total_registered) * 100

    # DISPLAY METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("Students Present", f"{unique_present} / {total_registered}")
    col2.metric("Attendance Rate", f"{attendance_percentage:.1f}%")
    # delta_color="inverse" makes the red "Absent" count look like a warning
    col3.metric("Students Absent", absent_count, delta=f"-{absent_count}", delta_color="inverse")

    st.divider()

    # DASHBOARD LAYOUT
    left_col, mid_col, right_col = st.columns([1.5, 1, 1.5])

    with left_col:
        st.subheader("✅ Present Students")
        if unique_present > 0:
            st.dataframe(df.iloc[::-1], use_container_width=True)
        else:
            st.info("No one has checked in yet.")

    with mid_col:
        st.subheader("🎯 Status Pie")
        # --- FIXED VARIABLE NAME HERE ---
        status_df = pd.DataFrame({
            "Status": ["Present", "Absent"],
            "Count": [unique_present, absent_count]
        })
        fig = px.pie(status_df, values='Count', names='Status', 
                     color='Status', 
                     color_discrete_map={'Present':'#00CC96', 'Absent':'#EF553B'},
                     hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("🚨 Absentee List")
        if absent_count > 0:
            # Sorting alphabetically so the list is easy to read
            absent_names.sort()
            for name in absent_names:
                st.error(f"❌ {name}") 
        else:
            st.success("🎉 All students are present!")

else:
    st.warning("⚠️ Please add student photos to 'Training_Images' folder first.")

# 6. LAUNCHER
if st.sidebar.button("🚀 LAUNCH AI SCANNER"):
    # This runs your scanner in a background process
    subprocess.Popen(["python3", "main.py"])
    st.sidebar.success("Scanner launching in a new window...")
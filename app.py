import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="HR Analytics Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ฟังก์ชันโหลดข้อมูล (ซัพพอร์ตทั้งการอัปโหลดไฟล์ และโหลดไฟล์ HR DATA.txt โดยตรง)
@st.cache_data
def load_data(file_source):
    # อ่านไฟล์ TSV (Tab-separated values) หรือ CSV
    try:
        df = pd.read_csv(file_source, sep="\t")
        if len(df.columns) <= 1:
            df = pd.read_csv(file_source, sep=",")
    except Exception:
        df = pd.read_csv(file_source, sep=",")
    
    # ลบช่องว่างส่วนเกินในชื่อคอลัมน์
    df.columns = df.columns.str.strip()
    
    # ทำความสะอาดข้อมูลประเภทข้อความ
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        
    return df

# ส่วนประกอบ Sidebar สำหรับการโหลดข้อมูล
st.sidebar.title("⚙️ ตั้งค่า & ตัวกรอง")
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ HR DATA (txt/csv)", type=["txt", "csv"])

file_path = "HR DATA.txt"

if uploaded_file is not None:
    df = load_data(uploaded_file)
elif os.path.exists(file_path):
    df = load_data(file_path)
else:
    st.error("⚠️ ไม่พบไฟล์ `HR DATA.txt` กรุณาวางไฟล์ในโฟลเดอร์เดียวกันหรืออัปโหลดผ่าน Sidebar")
    st.stop()

# 3. ตัวกรองข้อมูล (Filters) บน Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")

# Filter: แผนก (Department)
dept_col = "Department" if "Department" in df.columns else df.columns[0]
departments = ["ทั้งหมด (All)"] + sorted(list(df[dept_col].dropna().unique()))
selected_dept = st.sidebar.selectbox("แผนก (Department):", departments)

# Filter: สถานะพนักงาน (Employment Status)
status_col = "EmploymentStatus" if "EmploymentStatus" in df.columns else ("Status" if "Status" in df.columns else None)
if status_col:
    statuses = ["ทั้งหมด (All)"] + sorted(list(df[status_col].dropna().unique()))
    selected_status = st.sidebar.selectbox("สถานะพนักงาน (Status):", statuses)
else:
    selected_status = "ทั้งหมด (All)"

# การกรอง Dataframe
filtered_df = df.copy()

if selected_dept != "ทั้งหมด (All)":
    filtered_df = filtered_df[filtered_df[dept_col] == selected_dept]

if status_col and selected_status != "ทั้งหมด (All)":
    filtered_df = filtered_df[filtered_df[status_col] == selected_status]

# 4. ส่วนหัว Dashboard
st.title("👥 HR Analytics Dashboard")
st.markdown("ระบบวิเคราะห์ข้อมูลทรัพยากรบุคคล อัตรากำลังพล ค่าตอบแทน และผลการดำเนินงาน")
st.markdown("---")

# 5. สรุปค่า KPIs (Key Performance Indicators)
total_emp = len(filtered_df)

active_emp = len(filtered_df[filtered_df[status_col] == "Active"]) if status_col else total_emp
term_emp = len(filtered_df[filtered_df[status_col].astype(str).str.contains("Terminated", na=False)]) if status_col else 0
turnover_rate = (term_emp / total_emp * 100) if total_emp > 0 else 0

pay_col = "PayRate" if "PayRate" in df.columns else ("Salary" if "Salary" in df.columns else None)
avg_pay = filtered_df[pay_col].mean() if pay_col and total_emp > 0 else 0

sat_col = "EmpSatisfaction" if "EmpSatisfaction" in df.columns else None
avg_sat = filtered_df[sat_col].mean() if sat_col and total_emp > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="พนักงานทั้งหมด", value=f"{total_emp:,} คน", delta=f"Active: {active_emp}")

with col2:
    st.metric(label="อัตราการลาออก (Turnover Rate)", value=f"{turnover_rate:.1f}%", delta=f"ลาออก {term_emp} คน", delta_color="inverse")

with col3:
    st.metric(label="ค่าตอบแทนเฉลี่ย", value=f"${avg_pay:.2f}")

with col4:
    st.metric(label="ความพึงพอใจเฉลี่ย", value=f"{avg_sat:.2f} / 5" if sat_col else "N/A")

st.markdown("---")

# 6. กราฟแสดงผลวิเคราะห์ (Visualizations)
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 จำนวนพนักงานแยกตามแผนก")
    dept_counts = filtered_df[dept_col].value_counts().reset_index()
    dept_counts.columns = [dept_col, "Count"]
    fig_dept = px.bar(
        dept_counts, x=dept_col, y="Count", 
        color=dept_col, text_auto=True,
        labels={dept_col: "แผนก", "Count": "จำนวน (คน)"}
    )
    fig_dept.update_layout(showlegend=False, xaxis_title="", yaxis_title="จำนวนคน")
    st.plotly_chart(fig_dept, use_container_width=True)

with col_chart2:
    perf_col = "PerformanceScore" if "PerformanceScore" in df.columns else None
    if perf_col:
        st.subheader("🎯 สัดส่วนผลการประเมินการทำงาน")
        perf_counts = filtered_df[perf_col].value_counts().reset_index()
        perf_counts.columns = [perf_col, "Count"]
        fig_perf = px.pie(
            perf_counts, names=perf_col, values="Count", 
            hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_perf, use_container_width=True)

col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    rec_col = "RecruitmentSource" if "RecruitmentSource" in df.columns else None
    if rec_col:
        st.subheader("📢 ช่องทางการรับสมัครพนักงาน")
        rec_counts = filtered_df[rec_col].value_counts().reset_index()
        rec_counts.columns = [rec_col, "Count"]
        fig_rec = px.bar(
            rec_counts, y=rec_col, x="Count", orientation='h',
            color="Count", color_continuous_scale="Viridis", text_auto=True,
            labels={rec_col: "ช่องทาง", "Count": "จำนวน"}
        )
        fig_rec.update_layout(showlegend=False, yaxis_title="", xaxis_title="จำนวนคน")
        st.plotly_chart(fig_rec, use_container_width=True)

with col_chart4:
    term_col = "TermReason" if "TermReason" in df.columns else None
    if term_col:
        st.subheader("⚠️ สาเหตุการออกจากงาน")
        term_df = filtered_df[~filtered_df[term_col].astype(str).str.contains("N/A|still employed", case=False, na=False)]
        if len(term_df) > 0:
            term_counts = term_df[term_col].value_counts().reset_index()
            term_counts.columns = [term_col, "Count"]
            fig_term = px.pie(
                term_counts, names=term_col, values="Count",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_term, use_container_width=True)
        else:
            st.info("ไม่มีข้อมูลการออกจากงานในกลุ่มข้อมูลที่เลือก")

st.markdown("---")

# 7. ตารางข้อมูลรายละเอียดพนักงาน (Data Table)
st.subheader("📋 รายชื่อและรายละเอียดพนักงาน")

search_term = st.text_input("🔎 ค้นหาข้อมูลพนักงาน (ชื่อ, ตำแหน่ง ฯลฯ):")

display_df = filtered_df.copy()
if search_term:
    mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
    display_df = display_df[mask]

st.dataframe(display_df, use_container_width=True)
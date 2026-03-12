import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
from PIL import Image
import google.generativeai as genai

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
# Thay API Key của bạn vào đây
API_KEY = "YOUR_GEMINI_API_KEY"

if API_KEY != "YOUR_GEMINI_API_KEY":
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

DATA_FILE = "aji_master_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"plants": [], "logs": [], "yields": [], "expenses": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Khởi tạo dữ liệu vào Session State (Tránh mất data khi đổi Tab)
if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

# ==========================================
# 2. LOGIC CẢNH BÁO SÂU BỆNH & DINH DƯỠNG
# ==========================================
def get_alerts(temp, humi, plants):
    alerts = []
    # Cảnh báo môi trường dựa trên nhiệt độ & độ ẩm
    if temp > 30 and humi < 65:
        alerts.append("🚨 **BỌ TRĨ:** Thời tiết nóng khô, kiểm tra mặt dưới lá non!")
    if 20 <= temp <= 28 and 70 <= humi <= 85:
        alerts.append("🚨 **RẦY MỀM:** Điều kiện ấm ẩm lý tưởng cho rầy sinh sản!")
    if temp > 28 and humi > 85:
        alerts.append("🚨 **THÁN THƯ:** Nóng ẩm cao, nguy cơ thối trái rụng lá!")
    if temp > 33:
        alerts.append("🌡️ **QUÁ NÓNG:** Cần che lưới lan hoặc phun sương hạ nhiệt.")
    if temp > 32 and humi < 60:
        alerts.append("💧 **THIẾU NƯỚC:** Bốc hơi nhanh, cần tăng cường tưới gốc.")

    # Cảnh báo bón phân theo tuổi từng cây
    for p in plants:
        try:
            d_plant = datetime.strptime(p["date"], "%Y-%m-%d").date()
            age = (date.today() - d_plant).days
            if age in [15, 30, 45, 60, 75]:
                alerts.append(f"🌿 **{p['name']}**: Ngày thứ {age} - Đến kỳ bón phân định kỳ.")
        except: pass
    return alerts

# ==========================================
# 3. GIAO DIỆN CHÍNH (UI)
# ==========================================
st.set_page_config(page_title="Aji Farm Pro AI", page_icon="🌶️", layout="wide")

st.sidebar.title("🌶️ Aji Charapita Pro")
menu = st.sidebar.selectbox("CHỨC NĂNG", 
    ["📊 Tổng quan", "🌱 Quản lý cây", "📷 AI Bác sĩ", "📔 Nhật ký", "🧺 Thu hoạch", "💰 Tài chính", "📁 Báo cáo"])

# --- TAB 1: TỔNG QUAN ---
if menu == "📊 Tổng quan":
    st.header("📊 Tình trạng vườn thực tế")
    c1, c2 = st.columns(2)
    with c1: temp = st.slider("Nhiệt độ hiện tại (°C)", 15, 45, 30)
    with c2: humi = st.slider("Độ ẩm hiện tại (%)", 20, 100, 70)

    st.subheader("🚨 Thông báo & Cảnh báo")
    alerts = get_alerts(temp, humi, data["plants"])
    if alerts:
        for a in alerts: st.warning(a)
    else: st.success("Mọi chỉ số đang ở mức an toàn.")

    st.divider()
    st.subheader("🔮 Dự báo sản lượng")
    if len(data["yields"]) >= 3:
        df_y = pd.DataFrame(data["yields"])
        avg = df_y["amount"].mean()
        # Công thức: Trung bình lứa trước * Số cây * Hệ số tăng trưởng (giả định)
        predict = avg * len(data["plants"]) * 0.8 
        st.info(f"Dự báo sản lượng đợt tới: ~{int(predict)} gram")
    else:
        st.info("Cần thêm dữ liệu thu hoạch (ít nhất 3 lần) để AI dự báo.")

# --- TAB 2: QUẢN LÝ CÂY ---
elif menu == "🌱 Quản lý cây":
    st.header("🌱 Quản lý gốc ớt")
    with st.expander("➕ Thêm cây mới"):
        with st.form("add_p", clear_on_submit=True):
            n = st.text_input("Tên/Mã cây")
            d = st.date_input("Ngày trồng", value=date.today())
            nt = st.text_input("Ghi chú")
            if st.form_submit_button("Lưu vào hệ thống") and n:
                data["plants"].append({"name": n, "date": str(d), "note": nt})
                save_data(data); st.rerun()

    for i, p in enumerate(data["plants"]):
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            col1.write(f"**{p['name']}** - Trồng ngày: {p['date']}")
            if col2.button("❌", key=f"del_{i}"):
                data["plants"].pop(i); save_data(data); st.rerun()

# --- TAB 3: AI BÁC SĨ ---
elif menu == "📷 AI Bác sĩ":
    st.header("📷 Chẩn đoán bằng Thị giác máy tính")
    img_file = st.camera_input("Chụp ảnh lá hoặc ngọn ớt")
    if img_file:
        img = Image.open(img_file); st.image(img, width=400)
        if st.button("🚀 AI Phân tích"):
            if model:
                with st.spinner("Đang soi bệnh..."):
                    prompt = "Phân tích lá ớt Aji Charapita: tình trạng sức khỏe, sâu bệnh gì, thiếu chất gì và cách xử lý hữu cơ."
                    res = model.generate_content([prompt, img])
                    st.success("Kết quả chẩn đoán:"); st.write(res.text)
            else: st.error("Chưa cấu hình API Key!")

# --- TAB 5: THU HOẠCH ---
elif menu == "🧺 Thu hoạch":
    st.header("🧺 Ghi nhận sản lượng")
    with st.form("yield"):
        amt = st.number_input("Khối lượng (gram)", min_value=0)
        if st.form_submit_button("Lưu thu hoạch"):
            data["yields"].append({"date": str(date.today()), "amount": amt})
            save_data(data); st.rerun()
    if data["yields"]:
        df_y = pd.DataFrame(data["yields"])
        st.line_chart(df_y.set_index("date"))

# --- TAB 6: TÀI CHÍNH ---
elif menu == "💰 Tài chính":
    st.header("💰 Quản lý chi phí")
    with st.form("exp"):
        item = st.text_input("Khoản chi"); price = st.number_input("Số tiền", min_value=0)
        if st.form_submit_button("Lưu chi phí"):
            data["expenses"].append({"item": item, "amount": price})
            save_data(data); st.rerun()
    if data["expenses"]:
        df_e = pd.DataFrame(data["expenses"])
        st.bar_chart(df_e.set_index("item"))

# --- TAB 7: BÁO CÁO ---
elif menu == "📁 Báo cáo":
    st.header("📁 Xuất dữ liệu Excel")
    if st.button("Tạo file Báo cáo"):
        with pd.ExcelWriter("Aji_Farm_Report.xlsx") as writer:
            pd.DataFrame(data["plants"]).to_excel(writer, sheet_name="Cay")
            pd.DataFrame(data["yields"]).to_excel(writer, sheet_name="ThuHoach")
            pd.DataFrame(data["expenses"]).to_excel(writer, sheet_name="TaiChinh")
        with open("Aji_Farm_Report.xlsx", "rb") as f:
            st.download_button("📥 Tải xuống Excel", f, file_name="Aji_Farm_Report.xlsx")

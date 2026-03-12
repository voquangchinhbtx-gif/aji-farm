import streamlit as st
import google.generativeai as genai
import os
import pandas as pd
from PIL import Image

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Aji Charapita Farm", page_icon="🌶️", layout="wide")

# --- CẤU HÌNH GEMINI AI ---
# API Key của bạn đã được tích hợp sẵn bên dưới
API_KEY = "AIzaSyCBqUjnG3kJLuwYuZzWX9piIf-eqE29GQs"

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Lỗi kết nối AI: {e}")

# --- QUẢN LÝ DỮ LIỆU NHẬT KÝ ---
DATA_FILE = "nhat_ky_vuon.csv"
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Ngày", "Công việc", "Ghi chú"])
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# --- GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/628/628283.png", width=80)
    st.title("Bảng Điều Khiển")
    menu = st.radio("Chọn chức năng:", ["🏠 Trang chủ", "📝 Nhật ký vườn ớt", "🤖 Chẩn đoán sâu bệnh (AI)"])
    st.divider()
    st.info("Giáo án: Ứng dụng AI trong quản lý nông nghiệp thông minh.")

# --- CHỨC NĂNG 1: TRANG CHỦ ---
if menu == "🏠 Trang chủ":
    st.title("🌶️ Hệ Thống Quản Lý Vườn Ớt Aji Charapita")
    st.subheader("Chào mừng bạn đến với hệ thống quản lý thông minh!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Hệ thống giúp bạn:**
        * Theo dõi quá trình chăm sóc cây hàng ngày.
        * Sử dụng Trí tuệ nhân tạo để phát hiện bệnh sớm.
        * Lưu trữ dữ liệu khoa học phục vụ giảng dạy và thực hành.
        """)
    with col2:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Aji_Charapita.jpg/640px-Aji_Charapita.jpg", caption="Giống ớt đắt nhất thế giới - Aji Charapita")

# --- CHỨC NĂNG 2: NHẬT KÝ VƯỜN ---
elif menu == "📝 Nhật ký vườn ớt":
    st.header("📝 Nhật ký chăm sóc cây")
    
    with st.expander("➕ Thêm ghi chép mới"):
        with st.form("entry_form", clear_on_submit=True):
            date = st.date_input("Ngày thực hiện")
            task = st.text_input("Nội dung công việc (Ví dụ: Bón phân, Tưới nước...)")
            note = st.text_area("Ghi chú chi tiết tình trạng cây")
            submit = st.form_submit_button("Lưu vào hệ thống")
            
            if submit:
                new_data = pd.DataFrame([[date, task, note]], columns=["Ngày", "Công việc", "Ghi chú"])
                df = pd.read_csv(DATA_FILE)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success("Đã cập nhật nhật ký thành công!")

    st.subheader("📋 Lịch sử chăm sóc đã lưu")
    df_display = pd.read_csv(DATA_FILE)
    st.table(df_display)

# --- CHỨC NĂNG 3: CHẨN ĐOÁN AI ---
elif menu == "🤖 Chẩn đoán sâu bệnh (AI)":
    st.header("🤖 Trợ lý AI chẩn đoán sức khỏe cây trồng")
    st.write("Vui lòng tải ảnh lá ớt có dấu hiệu bất thường để AI phân tích.")
    
    uploaded_file = st.file_uploader("Chọn ảnh từ thiết bị hoặc Chụp ảnh...", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        st.image(img, caption="Ảnh đang chờ phân tích", width=400)
        
        if st.button("🚀 Bắt đầu chẩn đoán bằng AI"):
            with st.spinner("AI đang nghiên cứu hình ảnh, vui lòng đợi..."):
                try:
                    # Gửi ảnh cho Gemini AI
                    prompt = "Bạn là một chuyên gia nông nghiệp. Hãy nhìn hình ảnh này, cho biết cây có bị bệnh gì không, tên bệnh là gì và đưa ra lời khuyên khắc phục ngắn gọn bằng tiếng Việt."
                    response = model.generate_content([prompt, img])
                    
                    st.success("Đã có kết quả phân tích!")
                    st.markdown("---")
                    st.markdown("### 🔍 Kết quả từ Trợ lý AI:")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"Lỗi khi xử lý hình ảnh: {e}")

import streamlit as st
import google.generativeai as genai
import os

# --- CẤU HÌNH GEMINI AI ---
API_KEY = "AIzaSyCBqUjnG3kJLuwYuZzWX9piIf-eqE29GQs"

if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Lỗi kết nối AI: {e}")

# --- ĐỌC DỮ LIỆU ---
DATA_FILE = "data.csv"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write("Ngày,Nội dung,Ghi chú\n")

# Các dòng code tiếp theo của bạn...
st.title("Hệ Thống Quản Lý Vườn Ớt Aji Charapita")
st.write("Chào mừng bạn đến với hệ thống quản lý thông minh!")

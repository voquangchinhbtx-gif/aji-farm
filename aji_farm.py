import streamlit as st
import requests
import os
import json
import pandas as pd
from datetime import date, datetime
from streamlit_js_eval import get_geolocation
import google.generativeai as genai
from PIL import Image, ImageOps
import io

# =========================================================
# 1. QUẢN LÝ LƯU TRỮ (MỤC 1 & 14) - FIX LỖI KEYERROR
# =========================================================
st.set_page_config(page_title="Aji Farm v14.0 Masterpiece", layout="wide", page_icon="🌶️")

DATA_FILE = "aji_farm_master.json"

def load_data():
    default = {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Đảm bảo các key luôn tồn tại
                for key in default:
                    if key not in data: data[key] = default[key]
                return data
        except: return default
    return default

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

if "data" not in st.session_state:
    st.session_state.data = load_data()

# =========================================================
# 2. GPS & THỜI TIẾT (MỤC 2 & 3) - FIX LỖI API DESCRIPTION
# =========================================================
WEATHER_API_KEY = "66ad043d6024749fa4bf92f0a6782397"

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        r = requests.get(url, timeout=5).json()
        return r if r.get("main") else None
    except: return None

if "gps" not in st.session_state:
    try: st.session_state.gps = get_geolocation()
    except: st.session_state.gps = None

loc = st.session_state.gps
# Default info phòng trường hợp lỗi API
info = {"city": "Vườn mẫu", "temp": 25, "hum": 80, "wind": 1, "rain": 0, "desc": "N/A"}

if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w:
        info = {
            "city": w.get("name", "Vườn"), 
            "temp": w["main"].get("temp", 25),
            "hum": w["main"].get("humidity", 80), 
            "wind": w.get("wind", {}).get("speed", 0),
            "rain": w.get("rain", {}).get("1h", 0), 
            # 2️⃣ FIX: Lấy description an toàn
            "desc": w.get("weather", [{"description": "N/A"}])[0].get("description", "N/A")
        }

# =========================================================
# 3. DASHBOARD (MỤC 4) & PHÂN TÍCH DỮ LIỆU (MỤC 12)
# =========================================================
st.title("🌶️ Aji Farm Agri-Intelligence v14.0")
plants = st.session_state.data.get("plants", [])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
m2.metric("💧 Độ ẩm", f"{info['hum']}%")
m3.metric("🌬️ Thời tiết", info['desc'].capitalize())
m4.metric("🌿 Quy mô", f"{len(plants)} gốc")

# =========================================================
# 4. DỰ BÁO DỊCH TỄ IPPC (MỤC 5) & TƯỚI TIÊU (MỤC 6)
# =========================================================
st.divider()
c_risk, c_irri = st.columns(2)
with c_risk:
    st.subheader("🔮 Dự báo nguy cơ AI")
    t, h, r = info['temp'], info['hum'], info['rain']
    # Model dự báo chuẩn hóa
    risks = {
        "Thán thư": min((h * 0.6 + r * 40) / 100, 1.0),
        "Phấn trắng": min(((100-h) * 0.5 + (1 if 18<=t<=26 else 0) * 50) / 100, 1.0)
    }
    for pest, val in risks.items():
        st.write(f"**{pest}**")
        st.progress(val)

with c_irri:
    st.subheader("🚿 Irrigation AI (Lịch tưới)")
    # 9️⃣ TIMELINE: Tính ngày tuổi cây (Mục 9)
    p_last = plants[-1] if plants else {"date": str(date.today())}
    try: p_dt = datetime.strptime(p_last.get("date"), "%Y-%m-%d").date()
    except: p_dt = date.today()
    age = (date.today() - p_dt).days
    
    # 6️⃣ TƯỚI TIÊU: Tính ml nước (Mục 6)
    vol = (300 if age < 15 else 600) * (1.5 if t > 32 else 1.0)
    st.info(f"Cây {age} ngày tuổi: Tưới {int(vol)}ml (06:00 & 17:30)")

# =========================================================
# 5. GIS MAP & QUẢN LÝ CÂY CRUD (MỤC 7, 8, 10)
# =========================================================
st.divider()
c_map, c_crud = st.columns([3, 2])

with c_map:
    st.subheader("🗺️ Bản đồ vườn thực tế (GIS)")
    if plants:
        df_m = pd.DataFrame(plants)
        if "lat" in df_m.columns and "lon" in df_m.columns:
            df_m[["lat", "lon"]] = df_m[["lat", "lon"]].apply(pd.to_numeric, errors="coerce")
            st.map(df_m.dropna(subset=["lat", "lon"]), zoom=18)
    else: st.info("Vườn chưa có cây.")

with c_crud:
    st.subheader("📋 Danh sách & Năng suất (Yield)")
    if plants:
        st.dataframe(pd.DataFrame(plants)[["variety", "date"]], height=200)
        # 🔟 NĂNG SUẤT: Dự báo sản lượng (Mục 10)
        st.success(f"Dự kiến thu hoạch: {len(plants)*1.2:.1f} kg")
        if st.button("🗑️ Xóa cây cuối"):
            st.session_state.data["plants"].pop(); save_data(); st.rerun()

# =========================================================
# 6. VISION AI (MỤC 11) - FIX LỖI ẢNH NHỎ & NÉN
# =========================================================
st.divider()
st.subheader("🧠 Chẩn đoán Vision AI")
img_f = st.camera_input("Chụp lá bệnh")
if img_f:
    img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
    # 3️⃣ FIX: Kiểm tra kích thước ảnh
    if img.size[0] < 200 or img.size[1] < 200:
        st.warning("⚠️ Ảnh quá nhỏ hoặc mờ, AI có thể chẩn đoán sai.")
    
    img.thumbnail((800, 800))
    if st.button("🔍 AI Soi Bệnh"):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85) # Tối ưu tốc độ
            res = model.generate_content(["Bệnh gì? Trị thế nào?", {"mime_type": "image/jpeg", "data": buf.getvalue()}])
            ans = getattr(res, "text", "AI không xác định được")[:1500]
            st.success(ans)
            # 1️⃣2️⃣ NHẬT KÝ BỆNH: Lưu log (Mục 12)
            st.session_state.data["disease_logs"].append({"date": str(date.today()), "diagnosis": ans[:200]})
            save_data()
        except: st.error("Lỗi AI Vision!")

# =========================================================
# 7. AI CHAT & FEEDBACK LOOP (MỤC 13)
# =========================================================
st.divider()
st.subheader("🤖 Trợ lý & Đánh giá (Feedback)")
c_chat, c_feed = st.columns(2)

with c_chat:
    chat_in = st.chat_input("Hỏi chuyên gia...")
    if chat_in:
        # Code gọi AI Chat tương tự Vision...
        st.session_state.data["chat_history"].append([chat_in, "AI đang học từ vườn..."])
        save_data(); st.rerun()
    # 1️⃣ FIX: Chat history an toàn
    for q, a in reversed(st.session_state.data.get("chat_history", [])[-3:]):
        with st.chat_message("assistant"): st.write(a)

with c_feed:
    with st.form("feedback"):
        eff = st.select_slider("Hiệu quả AI", ["Tệ", "Ổn", "Tốt"])
        if st.form_submit_button("Lưu Feedback"):
            st.session_state.data["treatment_feedback"].append({"date": str(date.today()), "eff": eff})
            save_data(); st.success("Đã ghi nhớ!")

# =========================================================
# 8. HỆ THỐNG (MỤC 14)
# =========================================================
with st.sidebar:
    st.header("⚙️ Công cụ")
    st.download_button("💾 Backup JSON", json.dumps(st.session_state.data), "aji_backup.json")
    if st.button("📍 Ghim cây (GPS)"):
        if loc:
            st.session_state.data["plants"].append({"variety": "Ớt Aji", "lat": loc["coords"]["latitude"], "lon": loc["coords"]["longitude"], "date": str(date.today())})
            save_data(); st.rerun()
    if st.checkbox("Xác nhận Reset"):
        if st.button("🗑️ Reset Vườn"):
            st.session_state.data = load_data(); save_data(); st.rerun()































































import streamlit as st
import requests
import os
import json
import pandas as pd
from datetime import date, datetime, timedelta
from streamlit_js_eval import get_geolocation
import google.generativeai as genai
from PIL import Image, ImageOps
import io

# =========================================================
# 1. STORAGE & BACKUP (MỤC 1 & 14)
# =========================================================
st.set_page_config(page_title="Aji Farm Ultimate v13.0", layout="wide", page_icon="🌶️")

DATA_FILE = "aji_farm_v13.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "chat_history" in data:
                    data["chat_history"] = [list(i) for i in data["chat_history"]]
                return data
        except: return {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
    return {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

if "data" not in st.session_state:
    st.session_state.data = load_data()

# =========================================================
# 2. GPS & WEATHER (MỤC 2 & 3)
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
info = {"city": "Mặc định", "temp": 25, "hum": 80, "wind": 1, "rain": 0, "desc": "N/A"}

if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w:
        info = {
            "city": w.get("name", "Vườn"), "temp": w["main"]["temp"],
            "hum": w["main"]["humidity"], "wind": w.get("wind", {}).get("speed", 0),
            "rain": w.get("rain", {}).get("1h", 0), "desc": w["weather"][0]["description"]
        }

# =========================================================
# 3. DASHBOARD & DỰ BÁO SINH HỌC IPPC (MỤC 4 & 5)
# =========================================================
st.title("🌶️ Aji Farm Agri-Intelligence v13.0")
plants = st.session_state.data["plants"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
m2.metric("💧 Độ ẩm", f"{info['hum']}%")
m3.metric("🌬️ Gió/Mưa", f"{info['wind']}m/s | {info['rain']}mm")
m4.metric("🌿 Tổng quy mô", f"{len(plants)} gốc")



st.divider()
st.subheader("🔮 Dự báo dịch hại AI (IPPC Model)")
t, h, r = info['temp'], info['hum'], info['rain']
# Normalize risk score (0.0 - 1.0)
risks = {
    "Thán thư (Anthracnose)": min((h * 0.5 + r * 50) / 100, 1.0),
    "Phấn trắng (Mildew)": min(((100 - h) * 0.4 + (1 if 18<=t<=26 else 0) * 60) / 100, 1.0),
    "Sâu hại/Nhện đỏ": min(((1 if t>32 else 0) * 70 + (1 if h<50 else 0) * 30) / 100, 1.0)
}
cols = st.columns(3)
for i, (pest, val) in enumerate(risks.items()):
    with cols[i]:
        st.write(f"**{pest}**")
        st.progress(val)
        st.write("🔴 Nguy hiểm" if val > 0.7 else "🟠 Cảnh báo" if val > 0.4 else "🟢 An toàn")

# =========================================================
# 4. TƯỚI TIÊU & NĂNG SUẤT (MỤC 6 & 10)
# =========================================================
st.divider()
c_wat, c_yld = st.columns(2)
with c_wat:
    st.subheader("🚿 Irrigation AI (Lượng nước)")
    # Tính theo tuổi cây gần nhất
    p_last = plants[-1] if plants else {"date": str(date.today())}
    try: p_dt = datetime.strptime(p_last.get("date"), "%Y-%m-%d").date()
    except: p_dt = date.today()
    age = (date.today() - p_dt).days
    
    base_w = 300 if age < 15 else 600
    w_final = int(base_w * (1.5 if t > 32 else 0.5 if r > 2 else 1.0))
    st.info(f"💧 Cây {age} ngày tuổi: Tưới **{w_final}ml**/gốc. (Sáng 06:00 | Chiều 17:30)")

with c_yld:
    st.subheader("📈 Dự báo sản lượng (Yield)")
    # Yield = Số cây * 1.5kg (charapita) * Hệ số sức khỏe
    yield_est = len(plants) * 1.5 * (0.8 if max(risks.values()) > 0.7 else 1.0)
    st.success(f"Dự kiến thu hoạch: **{yield_est:.1f} kg**")

# =========================================================
# 5. MAP & TIMELINE & CRUD (MỤC 7, 8, 9)
# =========================================================
st.divider()
c_map, c_list = st.columns([3, 2])

with c_map:
    st.subheader("🗺️ Garden GIS Layout (Vị trí thực)")
    if plants:
        df_m = pd.DataFrame(plants)
        if "lat" in df_m.columns and "lon" in df_m.columns:
            df_m[["lat", "lon"]] = df_m[["lat", "lon"]].apply(pd.to_numeric, errors="coerce")
            df_m = df_m.dropna(subset=["lat", "lon"])
            if not df_m.empty: st.map(df_m, zoom=19)
    else: st.info("Vườn chưa có dữ liệu GPS.")

with c_list:
    st.subheader("📋 Quản lý vườn (CRUD)")
    if plants:
        df_p = pd.DataFrame(plants)
        st.dataframe(df_p[["variety", "date"]], use_container_width=True)
        # Nút xóa cây cuối (Demo CRUD)
        if st.button("🗑️ Xóa cây cuối"):
            st.session_state.data["plants"].pop()
            save_data(); st.rerun()
    else: st.write("Chưa có cây.")

# =========================================================
# 6. VISION AI & DISEASE LOGS (MỤC 11 & 12)
# =========================================================


[Image of an integrated pest management flowchart]

st.divider()
st.subheader("🧠 AI Vision - Chẩn đoán & Nhật ký bệnh")
img_f = st.camera_input("Chụp lá bệnh")
if img_f:
    img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
    img.thumbnail((800, 800))
    if st.button("🔍 AI Soi Bệnh"):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
            res = model.generate_content(["Bệnh gì? Cách trị? Ngắn gọn.", {"mime_type": "image/jpeg", "data": buf.getvalue()}])
            ans = getattr(res, "text", "AI không xác định được")[:1500]
            st.success(ans)
            # Lưu nhật ký bệnh (Mục 12)
            st.session_state.data["disease_logs"].append({
                "date": str(date.today()), "plant": p_last.get("variety", "Ớt Aji"), "diagnosis": ans[:200]
            })
            save_data()
        except: st.error("Lỗi AI Vision!")

# =========================================================
# 7. AI CHAT & FEEDBACK (MỤC 13)
# =========================================================
st.divider()
st.subheader("🤖 Trợ lý AI & Phản hồi (Feedback Loop)")
c_chat, c_feed = st.columns([2, 1])

with c_chat:
    chat_in = st.chat_input("Hỏi kinh nghiệm nông nghiệp...")
    if chat_in:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            ctx = "\n".join([f"U:{c[0]}|A:{c[1]}" for c in st.session_state.data["chat_history"][-2:]])
            res = model.generate_content(f"Agri Expert. Context: {ctx}\nQ: {chat_in}")
            ans_c = getattr(res, "text", "Lỗi chat")[:1000]
            st.session_state.data["chat_history"].append([chat_in, ans_c])
            save_data(); st.rerun()
        except: pass
    for q, a in reversed(st.session_state.data["chat_history"][-3:]):
        with st.chat_message("assistant"): st.write(a)

with c_feed:
    st.write("**Đánh giá hiệu quả AI**")
    with st.form("fb"):
        score = st.select_slider("Kết quả điều trị", ["Tệ", "Ổn", "Tốt"])
        if st.form_submit_button("Ghi nhớ"):
            st.session_state.data["treatment_feedback"].append({"date": str(date.today()), "eff": score})
            save_data(); st.success("Đã lưu!")

# =========================================================
# 8. SIDEBAR SYSTEM TOOLS (MỤC 14)
# =========================================================
with st.sidebar:
    st.header("⚙️ Công cụ hệ thống")
    st.download_button("💾 Backup Dữ liệu (JSON)", json.dumps(st.session_state.data, indent=2), "aji_v13.json")
    if st.button("📍 Ghim cây mới (GPS)"):
        if loc:
            st.session_state.data["plants"].append({
                "variety": "Ớt Aji Charapita", "lat": loc["coords"]["latitude"], 
                "lon": loc["coords"]["longitude"], "date": str(date.today())
            })
            save_data(); st.rerun()
    st.divider()
    if st.checkbox("Xác nhận Reset"):
        if st.button("🗑️ Xóa sạch vườn"):
            st.session_state.data = {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
            save_data(); st.rerun()



























































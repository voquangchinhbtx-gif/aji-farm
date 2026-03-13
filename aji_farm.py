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
# 1. STORAGE & SYSTEM (MỤC 1 & 14)
# =========================================================
st.set_page_config(page_title="Aji Farm Pro v24.0", layout="wide", page_icon="🌶️")

DATA_FILE = "aji_farm_original.json"

def load_data():
    default = {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # FIX 1: Ép kiểu list cho chat history để không lỗi Tuple
                if "chat_history" in data:
                    data["chat_history"] = [list(i) for i in data["chat_history"]]
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
# 2. GPS (MỤC 2) & WEATHER (MỤC 3)
# =========================================================
WEATHER_API_KEY = "66ad043d6024749fa4bf92f0a6782397"

if "gps" not in st.session_state:
    try: st.session_state.gps = get_geolocation()
    except: st.session_state.gps = None

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        r = requests.get(url, timeout=5).json()
        return r if r.get("main") else None
    except: return None

loc = st.session_state.gps
info = {"city": "Vườn Mẫu", "temp": 25, "hum": 80, "wind": 1, "rain": 0, "desc": "N/A"}

if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w:
        # FIX 2: Weather description an toàn qua .get()
        info = {
            "city": w.get("name", "Vườn"), 
            "temp": w["main"].get("temp", 25),
            "hum": w["main"].get("humidity", 80), 
            "wind": w.get("wind", {}).get("speed", 0),
            "rain": w.get("rain", {}).get("1h", 0),
            "desc": w.get("weather", [{"description": "N/A"}])[0].get("description", "N/A")
        }

# =========================================================
# 3. DASHBOARD (MỤC 4) & ANALYTICS (MỤC 12)
# =========================================================
st.title("🌶️ Aji Farm Agri-Intelligence v24.0")
plants = st.session_state.data["plants"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
m2.metric("💧 Độ ẩm", f"{info['hum']}%")
m3.metric("🌬️ Gió/Mưa", f"{info['wind']}m/s | {info['rain']}mm")
m4.metric("🌿 Quy mô", f"{len(plants)} gốc")



# 12. Analytics (Bổ sung phần còn thiếu)
with st.expander("📊 12. PHÂN TÍCH DỮ LIỆU & BIỂU ĐỒ (Analytics)"):
    logs = st.session_state.data.get("disease_logs", [])
    if logs:
        df_l = pd.DataFrame(logs)
        st.write("**Trend dịch bệnh theo thời gian:**")
        st.line_chart(df_l["date"].value_counts().sort_index())
    else: st.info("Chưa có dữ liệu nhật ký bệnh để vẽ biểu đồ.")

# =========================================================
# 4. DỰ BÁO IPPC (MỤC 5) & NĂNG SUẤT (MỤC 10)
# =========================================================
st.divider()
st.subheader("🔮 5. DỰ BÁO DỊCH HẠI AI (IPPC MODEL)")
t, h, r = info['temp'], info['hum'], info['rain']

risks = {
    "Thán thư (Anthracnose)": min((h * 0.5 + r * 50) / 100, 1.0),
    "Phấn trắng (Mildew)": min(((100 - h) * 0.4 + (1 if 18<=t<=26 else 0) * 60) / 100, 1.0)
}

c1, c2 = st.columns(2)
with c1:
    st.write("**Nguy cơ Thán thư**")
    st.progress(risks["Thán thư (Anthracnose)"])
with c2:
    st.write("**Nguy cơ Phấn trắng**")
    st.progress(risks["Phấn trắng (Mildew)"])

# 10. Yield Prediction
yield_est = len(plants) * 1.5 * (0.8 if max(risks.values()) > 0.7 else 1.0)
st.success(f"📈 **10. DỰ BÁO NĂNG SUẤT:** Dự kiến thu hoạch **{yield_est:.1f} kg**")

# =========================================================
# 5. TƯỚI TIÊU (MỤC 6) & TIMELINE (MỤC 9)
# =========================================================
st.divider()
st.subheader("🚿 6. IRRIGATION AI & 9. TIMELINE SINH TRƯỞNG")
if plants:
    p_last = plants[-1]
    p_dt = datetime.strptime(p_last.get("date"), "%Y-%m-%d").date()
    age = (date.today() - p_dt).days
    
    # Logic tưới AI
    water = 600 if t > 32 else 400
    st.info(f"🌿 Cây **{p_last.get('variety')}**: {age} ngày tuổi. Lượng nước: **{water}ml/gốc**.")
else: st.info("Vui lòng ghim cây để xem Timeline.")

# =========================================================
# 6. BẢN ĐỒ GIS (MỤC 7) & QUẢN LÝ CÂY (MỤC 8)
# =========================================================

st.divider()
c_map, c_list = st.columns([3, 2])
with c_map:
    st.subheader("🗺️ 7. GARDEN GIS LAYOUT")
    if plants:
        df_m = pd.DataFrame(plants)
        st.map(df_m)
    else: st.info("Chưa có dữ liệu Map.")

with c_list:
    st.subheader("📋 8. QUẢN LÝ DANH SÁCH (CRUD)")
    if plants:
        st.dataframe(pd.DataFrame(plants)[["variety", "date"]], height=200)
        if st.button("🗑️ Xóa cây cuối"):
            st.session_state.data["plants"].pop(); save_data(); st.rerun()

# =========================================================
# 7. VISION AI (MỤC 11) & DISEASE LOGS (MỤC 12)
# =========================================================


[Image of an integrated pest management flowchart]

st.divider()
st.subheader("🧠 11. VISION AI & 12. DISEASE LOGS")
img_f = st.camera_input("Chụp ảnh lá bệnh")
if img_f:
    img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
    # FIX 3: Check kích thước ảnh
    if img.size[0] >= 200:
        img.thumbnail((800, 800))
        if st.button("🔍 AI SOÁT BỆNH"):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("models/gemini-1.5-flash")
                buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
                res = model.generate_content(["Bệnh gì? Cách trị?", {"mime_type": "image/jpeg", "data": buf.getvalue()}])
                ans = getattr(res, "text", "AI không xác định được")
                st.success(ans)
                # Lưu vào mục 12
                st.session_state.data["disease_logs"].append({"date": str(date.today()), "diagnosis": ans[:200]})
                save_data()
            except: st.error("Lỗi Vision AI!")
    else: st.warning("Ảnh quá mờ hoặc nhỏ.")

# =========================================================
# 8. AI CHAT & FEEDBACK (MỤC 13)
# =========================================================
st.divider()
st.subheader("🤖 13. AI CHAT & FEEDBACK LOOP")
c_chat, c_feed = st.columns([2, 1])
with c_chat:
    q = st.chat_input("Hỏi AI...")
    if q:
        st.session_state.data["chat_history"].append([q, "AI đang tổng hợp..."])
        save_data(); st.rerun()
    for chat in reversed(st.session_state.data.get("chat_history", [])[-3:]):
        with st.chat_message("assistant"): st.write(chat[1])

with c_feed:
    with st.form("fb"):
        st.write("Đánh giá hiệu quả AI:")
        eff = st.select_slider("Kết quả", ["Tệ", "Ổn", "Tốt"])
        if st.form_submit_button("Lưu Feedback"):
            st.session_state.data["treatment_feedback"].append({"date": str(date.today()), "eff": eff})
            save_data(); st.success("Đã ghi nhớ!")

# =========================================================
# 9. SIDEBAR (MỤC 2 & 14)
# =========================================================
with st.sidebar:
    st.header("⚙️ 14. HỆ THỐNG")
    st.download_button("💾 Backup JSON", json.dumps(st.session_state.data, indent=2), "aji_farm.json")
    if st.button("📍 2. GHIM CÂY MỚI (GPS)"):
        if loc:
            st.session_state.data["plants"].append({
                "variety": "Ớt Aji Charapita", 
                "lat": loc["coords"]["latitude"], 
                "lon": loc["coords"]["longitude"], 
                "date": str(date.today())
            })
            save_data(); st.rerun()
    st.divider()
    if st.checkbox("Xác nhận Reset"):
        if st.button("🗑️ Xóa sạch vườn"):
            st.session_state.data = {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
            save_data(); st.rerun()



























































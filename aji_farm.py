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
# 1. STORAGE & SYSTEM (MỤC 1 & 14)
# =========================================================
st.set_page_config(page_title="Aji Farm Ultimate v15.0", layout="wide", page_icon="🌶️")

DATA_FILE = "aji_farm_final_v15.json"

def load_data():
    default = {"plants": [], "disease_logs": [], "treatment_feedback": [], "chat_history": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # FIX 2: Chuẩn hóa Chat History từ JSON (List of Lists)
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
# 2. GPS & WEATHER (MỤC 2 & 3 - FIX 2: DESC AN TOÀN)
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
info = {"city": "Vườn Mẫu", "temp": 25, "hum": 80, "wind": 1, "rain": 0, "desc": "N/A"}

if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w:
        info = {
            "city": w.get("name", "Vườn"), "temp": w["main"].get("temp", 25),
            "hum": w["main"].get("humidity", 80), "wind": w.get("wind", {}).get("speed", 0),
            "rain": w.get("rain", {}).get("1h", 0),
            "desc": w.get("weather", [{"description": "N/A"}])[0].get("description", "N/A")
        }

# =========================================================
# 3. DASHBOARD & ANALYTICS (MỤC 4 & 12 - NÂNG CẤP 3)
# =========================================================
st.title("🌶️ Aji Farm Agri-Intelligence v15.0")
plants = st.session_state.data.get("plants", [])

m1, m2, m3, m4 = st.columns(4)
m1.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
m2.metric("💧 Độ ẩm", f"{info['hum']}%")
m3.metric("🌬️ Gió/Mưa", f"{info['wind']}m/s | {info['rain']}mm")
m4.metric("🌿 Quy mô", f"{len(plants)} gốc")



with st.expander("📊 Phân tích dịch tễ vườn (Analytics)"):
    logs = st.session_state.data.get("disease_logs", [])
    if logs:
        df_l = pd.DataFrame(logs)
        # FIX 1: Kiểm tra cột date trước khi vẽ chart
        if "date" in df_l.columns and not df_l.empty:
            st.line_chart(df_l["date"].value_counts().sort_index())
            st.write("**Thống kê bệnh theo loại cây:**")
            if "plant" in df_l.columns: st.bar_chart(df_l["plant"].value_counts())
    else: st.info("Chưa có dữ liệu phân tích.")

# =========================================================
# 4. AI PEST PREDICTION & YIELD (MỤC 5 & 10 - NÂNG CẤP 1)
# =========================================================
st.divider()
st.subheader("🔮 Dự báo dịch hại AI Pro (IPPC Model)")
t, h, r = info['temp'], info['hum'], info['rain']

# FIX 2: Normalize chuẩn 1.0
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

# Năng suất (Mục 10)
yield_est = len(plants) * 1.5 * (0.8 if max(risks.values()) > 0.7 else 1.0)
st.success(f"📈 Sản lượng dự kiến: **{yield_est:.1f} kg** (Charapita Gold)")

# =========================================================
# 5. MAP GIS & IRRIGATION AI (MỤC 6, 7, 8, 9 - NÂNG CẤP 2, 4)
# =========================================================

st.divider()
c_map, c_irri = st.columns([2, 1])

with c_map:
    st.subheader("🗺️ Garden GIS Layout (Phân khu thực tế)")
    if plants:
        df_m = pd.DataFrame(plants)
        # FIX 2: Xử lý tọa độ lỗi
        if "lat" in df_m.columns and "lon" in df_m.columns:
            df_m[["lat", "lon"]] = df_m[["lat", "lon"]].apply(pd.to_numeric, errors="coerce")
            df_m = df_m.dropna(subset=["lat", "lon"])
            if not df_m.empty: st.map(df_m, zoom=19)
    else: st.info("Vườn chưa có dữ liệu GPS.")

with c_irri:
    st.subheader("💧 Irrigation AI & Timeline")
    if plants:
        # Lấy cây cuối để tính timeline (Mục 9)
        p_last = plants[-1]
        try: p_dt = datetime.strptime(p_last.get("date", str(date.today())), "%Y-%m-%d").date()
        except: p_dt = date.today()
        age = (date.today() - p_dt).days
        
        # Nâng cấp 2: Irrigation AI theo tuổi + thời tiết
        base_w = 300 if age < 15 else 600
        w_final = int(base_w * (1.5 if t > 32 else 0.5 if r > 2 else 1.0))
        st.write(f"🌿 **{p_last.get('variety','Cây')}**: {age} ngày tuổi")
        st.metric("Lượng nước cần", f"{w_final} ml/gốc")
        st.write("⏰ Lịch: 06:15 & 17:45")
    else: st.write("Chưa có cây để tính lịch.")

# =========================================================
# 6. VISION AI & LOGS (MỤC 11 & 12 - FIX 1, 3)
# =========================================================


[Image of an integrated pest management flowchart]

st.divider()
st.subheader("🧠 Vision AI - Chẩn đoán bệnh & Nhật ký")
img_f = st.camera_input("Chụp lá bệnh")
if img_f:
    img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
    # FIX 3: Kiểm tra kích thước ảnh
    if img.size[0] >= 200:
        img.thumbnail((800, 800))
        if st.button("🔍 AI Soi Bệnh"):
            try:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                model = genai.GenerativeModel("models/gemini-1.5-flash")
                buf = io.BytesIO(); img.save(buf, format="JPEG", quality=85)
                res = model.generate_content(["Phân tích bệnh & cách trị.", {"mime_type": "image/jpeg", "data": buf.getvalue()}])
                # FIX 3: Xử lý Vision trả về None
                ans = getattr(res, "text", "AI chưa xác định được")[:1500]
                st.success(ans)
                # FIX 1: Scope p_last an toàn cho logs
                p_name = plants[-1].get("variety", "Ớt Aji") if plants else "Cây"
                st.session_state.data["disease_logs"].append({"date": str(date.today()), "plant": p_name, "diagnosis": ans[:200]})
                save_data()
            except: st.error("Lỗi kết nối AI Vision!")
    else: st.warning("Ảnh quá nhỏ, vui lòng chụp lại.")

# =========================================================
# 7. AI CHAT & FEEDBACK LOOP (MỤC 13 - FIX 1, 2)
# =========================================================
st.divider()
st.subheader("🤖 Trợ lý Nông học & Feedback AI")
c_chat, c_feed = st.columns([2, 1])

with c_chat:
    chat_in = st.chat_input("Hỏi kinh nghiệm chăm sóc...")
    if chat_in:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            # FIX 1: Chat history an toàn
            history = st.session_state.data.get("chat_history", [])
            ctx = "\n".join([f"U:{c[0]}|A:{c[1]}" for c in history[-2:]])
            res = model.generate_content(f"Agri Expert AI. Context: {ctx}\nQ: {chat_in}")
            ans_c = getattr(res, "text", "AI bận")[:1000]
            # FIX 2: Chuẩn hóa List cho JSON
            st.session_state.data["chat_history"].append([chat_in, ans_c])
            save_data(); st.rerun()
        except: pass
    # FIX 1: Hiển thị an toàn
    for q, a in reversed(st.session_state.data.get("chat_history", [])[-3:]):
        with st.chat_message("assistant"): st.write(a)

with c_feed:
    with st.form("fb_loop"):
        eff = st.select_slider("Hiệu quả AI", ["Tệ", "Ổn", "Tốt"])
        if st.form_submit_button("Lưu phản hồi"):
            st.session_state.data["treatment_feedback"].append({"date": str(date.today()), "eff": eff})
            save_data(); st.success("AI đã ghi nhớ!")

# =========================================================
# 8. SIDEBAR SYSTEM TOOLS (MỤC 14)
# =========================================================
with st.sidebar:
    st.header("⚙️ Quản trị Hệ thống")
    st.download_button("💾 Backup JSON", json.dumps(st.session_state.data, indent=2), "aji_ultimate_v15.json")
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






























































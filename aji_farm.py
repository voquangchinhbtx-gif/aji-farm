import streamlit as st
import requests
import os
import json
import pandas as pd
from datetime import date
from streamlit_js_eval import get_geolocation
import google.generativeai as genai
from PIL import Image, ImageOps
import io

# =========================================================
# 0. KHỞI TẠO DỮ LIỆU & CẤU HÌNH GIAO DIỆN
# =========================================================
st.set_page_config(page_title="Aji Farm Pro AI", layout="wide", page_icon="🌶️")

DATA_FILE = "farm_data.json"

@st.cache_data
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"plants": [], "disease_logs": [], "treatment_feedback": []}
    return {"plants": [], "disease_logs": [], "treatment_feedback": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
    load_data.clear()

if "data" not in st.session_state:
    st.session_state.data = load_data()

# Khởi tạo bộ nhớ tạm cho UI
for key in ["weather", "current_procedure", "cur_p_ai", "gps"]:
    if key not in st.session_state:
        st.session_state[key] = None

# =========================================================
# 1. CẤU HÌNH AI & GPS & WEATHER
# =========================================================
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-flash")
    except:
        model = None
else:
    model = None

WEATHER_API_KEY = "66ad043d6024749fa4bf92f0a6782397"

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

# Tối ưu lấy GPS (Chỉ gọi 1 lần)
if not st.session_state.gps:
    st.session_state.gps = get_geolocation()

loc = st.session_state.gps
if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w:
        st.session_state["weather"] = {
            "city": w.get("name", "Vườn"), "temp": w["main"]["temp"],
            "hum": w["main"]["humidity"], "wind": w.get("wind", {}).get("speed", 0),
            "desc": w["weather"][0]["description"].capitalize()
        }

info = st.session_state.get("weather", {"city": "Chưa xác định", "temp": 25, "hum": 80, "wind": 1, "desc": "N/A"})

# =========================================================
# 2. DASHBOARD CHÍNH
# =========================================================
st.title("🌶️ Aji Farm Management Pro")
plants = st.session_state.data.get("plants", [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("📍 Vị trí", info['city'])
c2.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
c3.metric("💧 Độ ẩm", f"{info['hum']}%")
c4.metric("🌿 Tổng số cây", len(plants))
st.info(f"Dự báo thời tiết: {info['desc']}")

# =========================================================
# 3. QUẢN LÝ CÂY TRỒNG (CRUD + SEARCH)
# =========================================================
st.divider()
st.subheader("📋 Danh sách vườn")

df_p = pd.DataFrame(plants)

# Kiểm tra an toàn trước khi Search
if not df_p.empty and "variety" in df_p.columns:
    search = st.text_input("🔎 Tìm cây nhanh...", placeholder="Nhập giống cây cần tìm...")
    df_display = df_p[df_p["variety"].str.contains(search, case=False, na=False)] if search else df_p
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("🌵 Vườn chưa có cây nào. Hãy thêm cây ở mục bên dưới.")

with st.expander("🛠 Thao tác quản lý Cây (Thêm/Sửa/Xóa)"):
    tab1, tab2, tab3 = st.tabs(["➕ Thêm mới", "✏️ Chỉnh sửa", "🗑️ Xóa cây"])
    
    with tab1:
        with st.form("add_plant"):
            t = st.selectbox("Phân loại", ["Gia vị", "Rau", "Ăn trái", "Cảnh"])
            v = st.text_input("Giống cây (Variety)")
            l = st.text_input("Vị trí trồng (Location)")
            a = st.number_input("Tuổi cây (năm)", 0, 100, 0)
            if st.form_submit_button("Lưu vào vườn"):
                st.session_state.data["plants"].append({"type": t, "variety": v, "location": l, "age_years": a})
                save_data(); st.rerun()

    if plants:
        p_list_str = [f"{i} | {p.get('variety','Cây')} | {p.get('location','Vườn')}" for i, p in enumerate(plants)]
        
        with tab2:
            target_e = st.selectbox("Chọn cây muốn sửa:", p_list_str, key="edit_sel")
            idx_e = int(target_e.split(" | ")[0])
            p_curr = plants[idx_e]
            
            with st.form("edit_form_full"):
                type_opts = ["Gia vị", "Rau", "Ăn trái", "Cảnh"]
                curr_t = p_curr.get("type", "Rau")
                if curr_t not in type_opts: curr_t = "Rau"
                
                new_t = st.selectbox("Sửa loại", type_opts, index=type_opts.index(curr_t))
                new_v = st.text_input("Sửa giống", p_curr.get('variety'))
                new_l = st.text_input("Sửa vị trí", p_curr.get('location'))
                new_a = st.number_input("Sửa tuổi", 0, 100, int(p_curr.get('age_years', 0)))
                
                if st.form_submit_button("💾 Cập nhật thay đổi"):
                    st.session_state.data["plants"][idx_e] = {"type": new_t, "variety": new_v, "location": new_l, "age_years": new_a}
                    save_data(); st.success("Đã cập nhật!"); st.rerun()

        with tab3:
            target_d = st.selectbox("Chọn cây muốn xóa:", p_list_str, key="del_sel")
            confirm_del = st.checkbox("Tôi chắc chắn muốn xóa cây này")
            if st.button("❌ Xác nhận Xóa", type="primary", disabled=not confirm_del):
                st.session_state.data["plants"].pop(int(target_d.split(" | ")[0]))
                save_data(); st.rerun()

# =========================================================
# 4. HỆ THỐNG DỰ BÁO DỊCH TỄ (SMART FORECAST)
# =========================================================
st.divider()
st.subheader("🔮 Dự báo Dịch tễ (IPPC Model)")
def clamp(x): return max(0.0, min(float(x), 1.0))

if plants:
    p_names = [f"{p['variety']} ({p['location']})" for p in plants]
    sel_p_f = st.selectbox("Dự báo nguy cơ cho cây:", p_names)
    
    T, H, W = info["temp"], info["hum"], info["wind"]
    risks = {
        "Thán thư": clamp((H/100) * (1.3 if 24<=T<=32 else 0.5)),
        "Phấn trắng": clamp(((100-H)/100) * (1.2 if 18<=T<=26 else 0.4)),
        "Sương mai": clamp((H/100) * (1.5 if H>85 and T<24 else 0.3) * (0.8 if W>4 else 1.2)),
        "Vi khuẩn": clamp((H/100) * (1.4 if T>26 else 0.6)),
        "Thối rễ": clamp((H/100) * (1.3 if W<3 else 0.7))
    }
    
    top_d = max(risks, key=risks.get)
    st.metric("⚠️ Nguy cơ cao nhất", top_d, f"{int(risks[top_d]*100)}%", delta_color="inverse")
    
    cols = st.columns(5)
    for i, (name, val) in enumerate(risks.items()):
        with cols[i]:
            st.write(f"**{name}**")
            st.progress(val)
            if val > 0.7: st.error(f"{int(val*100)}%")
            elif val > 0.4: st.warning(f"{int(val*100)}%")
            else: st.success(f"{int(val*100)}%")

# =========================================================
# 5. AI QUY TRÌNH CHĂM SÓC & FEEDBACK
# =========================================================
st.divider()
st.subheader("🧬 AI Lập Quy trình & Học kinh nghiệm")

if plants:
    target_ai = st.selectbox("Cây cần hỗ trợ:", p_names, key="ai_p_select")
    
    @st.cache_data(ttl=600)
    def get_ai_advice(p_name, w_info, history_text):
        if not model: return "Chưa cấu hình Gemini API Key."
        prompt = f"Cây: {p_name}. Thời tiết: {w_info}. Kinh nghiệm cũ: {history_text}. Lập quy trình chăm sóc 7 ngày, ngắn gọn <120 từ, gạch đầu dòng."
        return model.generate_content(prompt).text

    if st.button("🚀 AI Tạo Quy trình chuẩn"):
        history = [h for h in st.session_state.data.get("treatment_feedback", []) if target_ai in h["plant"]][-5:]
        h_text = "\n".join([f"- {h['score']}: {h['user_note']}" for h in history])
        st.session_state["current_procedure"] = get_ai_advice(target_ai, str(info), h_text)
        st.session_state["cur_p_ai"] = target_ai

    if st.session_state.get("current_procedure") and st.session_state.get("cur_p_ai") == target_ai:
        st.markdown(st.session_state["current_procedure"])
        with st.expander("⭐ Đánh giá & Lưu kinh nghiệm cho AI"):
            with st.form("feedback_ai"):
                sc = st.select_slider("Kết quả thực tế", ["Thất bại", "Kém", "Ổn", "Tốt", "Rất tốt"])
                note = st.text_area("Ghi chú thực tế (để AI học)")
                if st.form_submit_button("Lưu vào bộ não AI"):
                    st.session_state.data["treatment_feedback"].append({
                        "date": str(date.today()), "plant": target_ai, "score": sc, "user_note": note
                    })
                    save_data(); st.success("AI đã ghi nhớ!"); st.rerun()

# =========================================================
# 6. AI VISION - CHẨN ĐOÁN BỆNH QUA ẢNH
# =========================================================
st.divider()
st.subheader("🧠 AI Vision - Soi lá bệnh")
img_f = st.camera_input("Chụp lá cây nghi ngờ bị bệnh")

if img_f:
    img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
    img.thumbnail((768, 768))
    st.image(img, caption="Ảnh chẩn đoán")

    if st.button("🔍 Phân tích bằng Gemini Flash"):
        if not model:
            st.error("Chưa có API Key!")
        else:
            with st.spinner("AI đang soi bệnh..."):
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                try:
                    res = model.generate_content([
                        "Bạn là bác sĩ thực vật. Chẩn đoán bệnh trên lá này, nêu nguyên nhân và cách trị. Dưới 120 từ, gạch đầu dòng.",
                        {"mime_type": "image/jpeg", "data": buf.getvalue()}
                    ])
                    st.success(res.text)
                except Exception as e: st.error(f"Lỗi: {e}")

# Hiển thị nhật ký AI học
if st.checkbox("📚 Xem nhật ký kinh nghiệm AI đã học"):
    fbs = st.session_state.data.get("treatment_feedback", [])
    if fbs:
        st.dataframe(pd.DataFrame(fbs).sort_values("date", ascending=False), use_container_width=True)































































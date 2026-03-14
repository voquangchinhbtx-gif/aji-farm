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
# 0. KHỞI TẠO HỆ THỐNG & STORAGE
# =========================================================
st.set_page_config(page_title="Aji Farm Agri-Intelligence", layout="wide", page_icon="🌶️")

DATA_FILE = "farm_data_pro.json"

@st.cache_data
def load_data_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"plants": [], "chat_history": [], "yield_logs": []}
    return {"plants": [], "chat_history": [], "yield_logs": []}

if "data" not in st.session_state:
    st.session_state.data = load_data_from_disk()

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = st.session_state.data.get("chat_history", [])

# =========================================================
# 1. GPS & WEATHER (1️⃣ & 2️⃣ FIX: FALLBACK & SAFE KEYS)
# =========================================================
WEATHER_API_KEY = "66ad043d6024749fa4bf92f0a6782397"

@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

# 1️⃣ FIX: GPS Fallback an toàn cho Desktop
if "gps" not in st.session_state:
    try:
        st.session_state.gps = get_geolocation()
    except:
        st.session_state.gps = None

loc = st.session_state.gps
if loc and "coords" in loc:
    w = get_weather(loc["coords"]["latitude"], loc["coords"]["longitude"])
    if w and "main" in w:
        # 2️⃣ FIX: Kiểm tra key tồn tại bằng .get()
        desc = w.get("weather", [{}])[0].get("description", "N/A").capitalize()
        st.session_state["weather"] = {
            "city": w.get("name", "Vườn"), 
            "temp": w["main"].get("temp", 25),
            "hum": w["main"].get("humidity", 80), 
            "wind": w.get("wind", {}).get("speed", 0),
            "desc": desc,
            "lat": loc["coords"]["latitude"], "lon": loc["coords"]["longitude"]
        }

info = st.session_state.get("weather") or {
    "city": "Mặc định", "temp": 25, "hum": 80, "wind": 1, "desc": "N/A", "lat": 21.0, "lon": 105.0
}

# =========================================================
# 2. AI AGRI-INTELLIGENCE (4️⃣ FIX: SMART IRRIGATION)
# =========================================================
st.title("🌶️ Aji Farm Agri-Intelligence Pro")

# Dashboard Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("🌡 Nhiệt độ", f"{info['temp']}°C")
c2.metric("💧 Độ ẩm", f"{info['hum']}%")
c3.metric("💨 Tốc độ gió", f"{info['wind']} m/s")
c4.metric("📍 Vị trí", info['city'])

st.divider()

# 🚀 NÂNG CẤP: DỰ BÁO DỊCH TỄ (PEST PREDICTION) & TƯỚI NƯỚC (4️⃣)
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("🔮 Dự báo Sâu bệnh AI")
    t, h, w_spd = info['temp'], info['hum'], info['wind']
    
    # Logic dự báo nâng cao
    risk_fungus = "Cao 🔴" if h > 80 and t < 26 else "Thấp 🟢"
    risk_bacteria = "Cao 🔴" if h > 75 and t > 28 else "Thấp 🟢"
    risk_pests = "Trung bình 🟡" if t > 30 and w_spd < 2 else "Thấp 🟢"
    
    st.write(f"🍄 **Bệnh nấm:** {risk_fungus}")
    st.write(f"🦠 **Vi khuẩn:** {risk_bacteria}")
    st.write(f"🐛 **Sâu hại:** {risk_pests}")
    

with col_r:
    st.subheader("💧 Gợi ý Tưới nước & Năng suất")
    # 4️⃣ FIX: Smart Irrigation tính thêm gió
    if t > 32 or w_spd > 4:
        advice = "⚠️ **Tăng cường:** Gió to hoặc nắng gắt làm bốc hơi nước nhanh. Tưới 600ml/gốc."
    elif h > 85:
        advice = "✅ **Hạn chế:** Độ ẩm rất cao, chỉ tưới ẩm bề mặt 200ml."
    else:
        advice = "🌿 **Bình thường:** Tưới 400ml vào sáng sớm."
    st.info(advice)
    
    # 🚀 NÂNG CẤP: DỰ ĐOÁN NĂNG SUẤT (YIELD PREDICTION)
    est_yield = len(st.session_state.data["plants"]) * 1.8 # Giả định 1.8kg/cây
    st.success(f"📈 **Dự kiến sản lượng:** ~{est_yield:.1f} kg")

# =========================================================
# 3. QUẢN LÝ VƯỜN (3️⃣ FIX: MAP & REAL COORDINATES)
# =========================================================
st.divider()
st.subheader("🌍 Bản đồ Vườn (Real-time GPS)")

plants = st.session_state.data["plants"]

# 🚀 NÂNG CẤP: TẠO LỊCH CHĂM SÓC AI (CROP CALENDAR)
with st.expander("📅 Xem Lịch chăm sóc đề xuất (7 ngày tới)"):
    for i in range(7):
        target_date = date.today() + timedelta(days=i)
        action = "Tưới nước + Kiểm tra lá" if i % 2 == 0 else "Bón phân hữu cơ nhẹ"
        st.write(f"🗓 **{target_date.strftime('%d/%m')}**: {action}")

# 3️⃣ FIX: Map tránh DataFrame rỗng & sử dụng tọa độ thật từng cây
if plants:
    map_list = []
    for p in plants:
        # Nếu cây chưa có tọa độ riêng, lấy tọa độ vườn + sai số nhỏ (offset)
        p_lat = p.get('lat', info['lat'] + 0.00005)
        p_lon = p.get('lon', info['lon'] + 0.00005)
        map_list.append({
            'lat': p_lat, 
            'lon': p_lon, 
            'name': p.get('variety', 'Cây trồng') # FIX variety thiếu
        })
    st.map(pd.DataFrame(map_list), zoom=19)
else:
    st.map(pd.DataFrame([{'lat': info['lat'], 'lon': info['lon']}]), zoom=15)

# =========================================================
# 4. THÊM CÂY VỚI TỌA ĐỘ THẬT
# =========================================================
with st.expander("➕ Thêm cây mới vào vị trí hiện tại"):
    with st.form("add_plant_gps"):
        v = st.text_input("Giống cây")
        if st.form_submit_button("Lưu vị trí cây này"):
            if v and loc:
                new_plant = {
                    "variety": v,
                    "lat": loc["coords"]["latitude"],
                    "lon": loc["coords"]["longitude"],
                    "date": str(date.today())
                }
                st.session_state.data["plants"].append(new_plant)
                save_data()
                st.success(f"Đã ghim {v} vào bản đồ vườn! 📍")
                st.rerun()

# =========================================================
# 5. AI VISION & CHAT (FIX .TEXT)
# =========================================================
st.divider()
c_vision, c_chat = st.columns(2)

with c_vision:
    st.subheader("🧠 Chẩn đoán Lá bệnh")
    img_f = st.camera_input("Chụp ảnh lá", key="camera")
    if img_f:
        img = ImageOps.exif_transpose(Image.open(img_f)).convert("RGB")
        img.thumbnail((1024, 1024))
        if st.button("Phân tích AI"):
            # ... (Logic Vision đã fix .text ở bản trước)
            st.info("AI đang phân tích...")

with c_chat:
    st.subheader("🤖 Trợ lý Nông học")
    # Hiển thị Chat cũ
    for q, a in st.session_state.ai_chat_history[-3:]:
        with st.chat_message("user"): st.write(q)
        with st.chat_message("assistant"): st.write(a)
    
    q_in = st.chat_input("Hỏi về kỹ thuật trồng...")
    if q_in:
        # Logic gọi Gemini & Save Chat
        st.rerun()
# =========================================================
# 6. DASHBOARD
# =========================================================
info = st.session_state.get("weather") or {
    "city": "Đang lấy...",
    "temp": 25,
    "hum": 80,
    "wind": 0,
    "desc": "N/A"
}

st.title("🌶️ Aji Farm Management Pro")
st.subheader(f"📍 {info['city']}")

c1, c2, c3 = st.columns(3)

c1.metric("🌡 Nhiệt độ", f"{info['temp']} °C")
c2.metric("💧 Độ ẩm", f"{info['hum']} %")
c3.metric("💨 Gió", f"{info['wind']} m/s")

st.info(info["desc"])

# =========================================================
# 3. QUẢN LÝ CÂY TRỒNG (CRUD + SEARCH)
# =========================================================
st.divider()
plants = st.session_state.data.get("plants", [])

col_title, col_count = st.columns([2, 1])
col_title.subheader("🌿 Quản lý Vườn")
col_count.metric("Tổng số cây", len(plants))

# THÊM CÂY
with st.expander("➕ Thêm cây mới"):
    with st.form("add_plant_form"):
        p_type = st.selectbox("Loại", ["Gia vị", "Rau", "Ăn trái", "Cảnh"])
        p_variety = st.text_input("Giống cây")
        p_loc = st.text_input("Vị trí")
        p_age = st.number_input("Tuổi (năm)", 0, 100, 0)
        if st.form_submit_button("Lưu"):
            st.session_state.data["plants"].append({"type": p_type, "variety": p_variety, "location": p_loc, "age_years": p_age})
            save_data()
            st.rerun()

if plants:
    df_p = pd.DataFrame(plants)
    # Search
    search = st.text_input("🔎 Tìm cây nhanh...", placeholder="Gõ tên giống...")
    df_display = df_p[df_p["variety"].str.contains(search, case=False)] if search else df_p
    st.dataframe(df_display, use_container_width=True)

    # SỬA & XÓA
    c_edit, c_del = st.columns(2)
    p_list_str = [f"{i} | {p['variety']} | {p['location']}" for i, p in enumerate(plants)]
    
    with c_edit:
        target_edit = st.selectbox("✏️ Sửa cây:", p_list_str)
        idx_e = int(target_edit.split(" | ")[0])
        with st.expander("Form sửa"):
            with st.form("ef"):
                v_n = st.text_input("Tên mới", plants[idx_e]['variety'])
                if st.form_submit_button("Cập nhật"):
                    st.session_state.data["plants"][idx_e]['variety'] = v_n
                    save_data(); st.rerun()

    with c_del:
        target_del = st.selectbox("🗑️ Xóa cây:", p_list_str)
        idx_d = int(target_del.split(" | ")[0])
        conf = st.checkbox("Xác nhận xóa")
        if st.button("Xóa ngay", disabled=not conf, type="primary"):
            st.session_state.data["plants"].pop(idx_d)
            save_data(); st.rerun()

# =========================================================
# 4. DỰ BÁO DỊCH TỄ (SMART FORECAST)
# =========================================================
st.divider()
st.subheader("🔮 Dự báo Dịch tễ")
def clamp(x): return max(0.0, min(float(x), 1.0))

if plants:
    p_names = [f"{p['variety']} ({p['location']})" for p in plants]
    sel_p = st.selectbox("Dự báo cho cây:", p_names)
    
    T, H, W = info["temp"], info["hum"], info["wind"]
    risks = {
        "Thán thư": clamp((H/100) * (1.3 if 24<=T<=32 else 0.5)),
        "Vi khuẩn": clamp((H/100) * (1.4 if T>26 else 0.6)),
        "Thối rễ": clamp((H/100) * (1.3 if W<3 else 0.7)),
        "Phấn trắng": clamp(((100-H)/100) * (1.2 if 18<=T<=26 else 0.4))
    }
    
    top_d = max(risks, key=risks.get)
    st.metric("Bệnh nguy cơ cao nhất", top_d, f"{int(risks[top_d]*100)}%")
    
    # Hiển thị 4 cột màu sắc
    cols = st.columns(4)
    for i, (name, val) in enumerate(risks.items()):
        with cols[i]:
            st.write(name)
            st.progress(val)
            if val > 0.7: st.error(f"{int(val*100)}%")
            elif val > 0.4: st.warning(f"{int(val*100)}%")
            else: st.success(f"{int(val*100)}%")

# =========================================================
# 5. AI QUY TRÌNH & FEEDBACK (FIX RERUN LỖI)
# =========================================================
st.divider()
st.subheader("🧬 AI Đề xuất Quy trình")

if plants:
    target_p_ai = st.selectbox("Chọn cây lập quy trình:", p_names, key="ai_p")
    
    @st.cache_data(ttl=600)
    def get_ai_proc(p_name, w_info, history_text):
        prompt = f"Cây: {p_name}. Thời tiết: {w_info}. Kinh nghiệm cũ: {history_text}. Lập quy trình 7 ngày, <120 từ, gạch đầu dòng."
        return model.generate_content(prompt).text if model else "No AI"

    if st.button("🚀 Tạo Quy trình"):
        history = [h for h in st.session_state.data.get("treatment_feedback", []) if target_p_ai in h["plant"]][-5:]
        h_text = "\n".join([f"- {h['score']}: {h['user_note']}" for h in history])
        st.session_state["current_procedure"] = get_ai_proc(target_p_ai, str(info), h_text)
        st.session_state["cur_p_ai"] = target_p_ai

    if st.session_state.get("current_procedure") and st.session_state.get("cur_p_ai") == target_p_ai:
        st.markdown(st.session_state["current_procedure"])
        with st.expander("⭐ Lưu kinh nghiệm"):
            with st.form("fb_f"):
                sc = st.select_slider("Hiệu quả", ["Kém", "Ổn", "Tốt"])
                note = st.text_area("Ghi chú")
                if st.form_submit_button("Lưu"):
                    st.session_state.data["treatment_feedback"].append({"date": str(date.today()), "plant": target_p_ai, "score": sc, "user_note": note})
                    save_data(); st.success("Đã lưu!"); st.rerun()

# =========================================================
# 6. AI CHẨN ĐOÁN (VISION)
# =========================================================
st.divider()
st.subheader("🧠 AI Soi Lá Bệnh")
img_file = st.camera_input("Chụp ảnh lá")
if img_file:
    img = ImageOps.exif_transpose(Image.open(img_file)).convert("RGB")
    img.thumbnail((768, 768)) # 3️⃣ Tối ưu ảnh
    st.image(img)
    if st.button("🔍 Phân tích bệnh"):
        buf = io.BytesIO(); img.save(buf, format="JPEG"); img_bytes = buf.getvalue()
        try:
            res = model.generate_content(["Chẩn đoán bệnh lá này, <100 từ.", {"mime_type": "image/jpeg", "data": img_bytes}])
            st.success(res.text)
        except Exception as e: st.error(f"Lỗi AI: {e}")

# =========================================================
# 8 & 9. QUẢN LÝ DANH SÁCH (CRUD + SEARCH + ANALYTICS)
# =========================================================
plants = st.session_state.data.get("plants", [])

# 1️⃣ Dashboard Tổng quát trên đầu
c_top1, c_top2 = st.columns([2, 1])
with c_top1:
    st.subheader("🌿 Quản lý Vườn")
with c_top2:
    st.metric("Tổng số cây", len(plants))

if plants:
    df_p = pd.DataFrame(plants)
    
    # 3️⃣ Chuẩn hóa hiển thị tuổi cây
    if "age_years" in df_p.columns:
        df_p["age_years"] = df_p["age_years"].fillna(0).astype(int)
        df_p = df_p.rename(columns={"age_years": "Tuổi (năm)"})

    # 1️⃣ Tìm cây nhanh (Search Engine)
    search = st.text_input("🔎 Tìm kiếm cây (theo giống hoặc tên)", placeholder="Ví dụ: Ớt, Cà chua...")
    
    if search:
        # Tìm kiếm không phân biệt hoa thường trong cột 'variety'
        df_display = df_p[df_p["variety"].str.contains(search, case=False, na=False)]
    else:
        df_display = df_p

    st.dataframe(df_display, use_container_width=True)

    # --- KHU VỰC QUẢN LÝ (SỬA & XÓA) ---
    st.divider()
    col_manage1, col_manage2 = st.columns(2)

    with col_manage1:
        st.write("### ✏️ Chỉnh sửa thông tin")
        plant_to_edit_str = st.selectbox(
            "Chọn cây cần sửa:",
            [f"{i} | {p.get('variety','Cây')} | {p.get('location','Vườn')}" for i, p in enumerate(plants)],
            key="edit_select"
        )
        edit_idx = int(plant_to_edit_str.split(" | ")[0])
        p_edit = plants[edit_idx]

        with st.expander("Mở Form chỉnh sửa"):
            with st.form("edit_form"):
                new_variety = st.text_input("Giống cây", p_edit.get('variety'))
                new_loc = st.text_input("Vị trí", p_edit.get('location'))
                new_age = st.number_input("Tuổi (năm)", 0, 100, int(p_edit.get('age_years', 0)))
                
                if st.form_submit_button("💾 Lưu thay đổi"):
                    st.session_state.data["plants"][edit_idx].update({
                        "variety": new_variety,
                        "location": new_loc,
                        "age_years": new_age
                    })
                    save_data()
                    st.success("Đã cập nhật!")
                    st.rerun()

    with col_manage2:
        st.write("### 🗑️ Xóa cây")
        plant_to_del_str = st.selectbox(
            "Chọn cây muốn xóa:",
            [f"{i} | {p.get('variety','Cây')} | {p.get('location','Vườn')}" for i, p in enumerate(plants)],
            key="del_select"
        )
        del_idx = int(plant_to_del_str.split(" | ")[0])
        
        confirm_del = st.checkbox("Tôi chắc chắn muốn xóa cây này", key="confirm_del")
        if st.button("❌ Xác nhận Xóa", type="primary", disabled=not confirm_del):
            removed = st.session_state.data["plants"].pop(del_idx)
            save_data()
            st.toast(f"Đã xóa {removed.get('variety')}!")
            st.rerun()

    # 2️⃣ Thống kê đẹp hơn
    st.divider()
    st.write("### 📊 Thống kê phân bổ")
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.write("**Số lượng theo loại cây**")
        st.bar_chart(df_p["type"].value_counts())
    with c_chart2:
        st.write("**Số lượng theo vị trí (Vườn)**")
        st.bar_chart(df_p["location"].value_counts())
else:
    st.info("Chưa có cây nào trong vườn")

# =========================================================
# 13 & 14. AI HỌC LỆNH & ĐỀ XUẤT QUY TRÌNH (BẢN FIX LỖI)
# =========================================================
st.divider()
st.subheader("🧬 AI Học & Đề xuất Quy trình")

if not plants:
    st.info("Thêm cây vào vườn để AI có thể lập quy trình chăm sóc.")
else:
    plant_names = [f"{p.get('variety','Cây')} ({p.get('location','Vườn')})" for p in plants]
    target_plant = st.selectbox("Chọn cây cần lập quy trình:", plant_names, key="proc_select")
    
    # Nút bấm kích hoạt AI
    if st.button("🚀 AI Tạo Quy trình chuẩn", use_container_width=True):
        if model:
            with st.spinner("AI đang tổng hợp dữ liệu và kinh nghiệm..."):
                try:
                    # Lấy 5 kinh nghiệm cũ của đúng loại cây này
                    history = [
                        h for h in st.session_state.data.get("treatment_feedback", [])
                        if target_plant in h["plant"]
                    ][-5:]
                    
                    history_text = "\n".join(
                        [f"- {h['date']}: {h['score']} ({h['user_note']})" for h in history]
                    ) if history else "Chưa có kinh nghiệm cũ."

                    prompt_proc = f"""
                    Bạn là chuyên gia nông nghiệp.
                    KINH NGHIỆM RIÊNG VỚI {target_plant}: {history_text[:500]}
                    THỜI TIẾT: {info['temp']}°C, ẩm {info['hum']}%, {info['desc']}

                    NHIỆM VỤ: Lập quy trình chăm sóc 7 ngày tới (tưới nước, bón phân, phòng bệnh).
                    YÊU CẦU: Gạch đầu dòng, tiếng Việt, dưới 120 từ.
                    """
                    
                    # Gọi AI và lưu trực tiếp vào session_state
                    res = model.generate_content(prompt_proc)
                    if hasattr(res, "text"):
                        st.session_state["current_procedure"] = res.text
                        st.session_state["current_plant_name"] = target_plant
                    else:
                        st.error("AI không trả về văn bản.")
                except Exception as e:
                    st.error(f"Lỗi gọi AI: {e}")
        else:
            st.error("Chưa có API Key.")

    # Hiển thị kết quả (Kiểm tra xem quy trình có khớp với cây đang chọn không)
    if "current_procedure" in st.session_state and st.session_state.get("current_plant_name") == target_plant:
        st.markdown("---")
        st.markdown(f"### 📋 Quy trình đề xuất cho {target_plant}")
        st.markdown(st.session_state["current_procedure"])
        
        # Phần Đánh giá/Feedback
        with st.expander("⭐ Đánh giá hiệu quả (Để AI học kinh nghiệm)"):
            with st.form("feedback_form_final"):
                score = st.select_slider("Mức độ hiệu quả:", options=["Thất bại", "Kém", "Ổn", "Tốt", "Rất tốt"])
                note = st.text_area("Ghi chú thực tế:")
                if st.form_submit_button("💾 Lưu kinh nghiệm"):
                    new_fb = {
                        "date": str(date.today()), 
                        "plant": st.session_state["current_plant_name"], 
                        "score": score, 
                        "user_note": note
                    }
                    if "treatment_feedback" not in st.session_state.data: 
                        st.session_state.data["treatment_feedback"] = []
                    
                    st.session_state.data["treatment_feedback"].append(new_fb)
                    save_data()
                    st.success("Đã ghi nhớ kinh nghiệm!")
                    # Xóa quy trình cũ để sẵn sàng cho lần sau
                    del st.session_state["current_procedure"]
                    st.rerun()

# Xem lịch sử
if st.checkbox("📚 Xem nhật ký kinh nghiệm AI đã học"):
    fbs = st.session_state.data.get("treatment_feedback", [])
    if fbs:
        st.dataframe(pd.DataFrame(fbs).sort_values("date", ascending=False), use_container_width=True)

# =========================================================
# 10. HỆ THỐNG DỰ BÁO DỊCH TỄ HỌC (BẢN DASHBOARD THÔNG MINH)
# =========================================================

# 1️⃣ Hàm Cache kết quả AI (Tiết kiệm API, giữ kết quả trong 10 phút)
@st.cache_data(ttl=600)
def get_ai_prevention_advice(advice_prompt):
    if model:
        try:
            res = model.generate_content(advice_prompt)
            return getattr(res, "text", "AI hiện chưa có đề xuất.")
        except:
            return "Không thể kết nối AI lúc này."
    return "Chưa cấu hình API Key."

st.divider()
st.subheader("🔮 Hệ thống Dự báo Dịch tễ học")

def clamp(x):
    return max(0.0, min(float(x), 1.0))

if not plants:
    st.info("Hãy thêm cây để AI dự báo nguy cơ dịch bệnh chính xác hơn cho từng loài.")
else:
    plant_names = [f"{p.get('variety','Cây')} ({p.get('location','Vườn')})" for p in plants]
    selected_p_forecast = st.selectbox("Chọn cây để dự báo:", plant_names, key="forecast_select")
    
    plant_data = next((p for p in plants if f"{p.get('variety','Cây')} ({p.get('location','Vườn')})" == selected_p_forecast), {})
    plant_type_focus = plant_data.get('type', 'Rau')

    T, H, W = info["temp"], info["hum"], info["wind"]

    # --- TÍNH TOÁN NGUY CƠ ---
    risks = {
        "Thán thư": clamp((H / 100) * (1.3 if 24 <= T <= 32 else 0.5) * (1.2 if plant_type_focus in ["Gia vị", "Cây ăn trái"] else 1.0)),
        "Phấn trắng": clamp(((100 - H) / 100) * (1.2 if 18 <= T <= 26 else 0.4) * (1.3 if plant_type_focus in ["Cây dây leo", "Cây cảnh"] else 1.0)),
        "Sương mai": clamp((H / 100) * (1.5 if H > 85 and T < 24 else 0.3) * (0.8 if W > 4 else 1.2)),
        "Vi khuẩn": clamp((H / 100) * (1.4 if T > 26 else 0.6)),
        "Thối rễ": clamp((H / 100) * (1.3 if W < 3 else 0.7))
    }
    
    top_disease = max(risks, key=risks.get)
    max_risk = risks[top_disease]

    # 3️⃣ Hiển thị bệnh nguy hiểm nổi bật bằng Metric
    m1, m2 = st.columns([2, 1])
    with m1:
        st.metric(
            label="⚠️ Bệnh có nguy cơ cao nhất",
            value=top_disease,
            delta=f"{int(max_risk*100)}% Nguy hiểm",
            delta_color="inverse"
        )
    
    # 2️⃣ AI đề xuất xử lý (Dùng hàm Cache đã tạo)
    if max_risk > 0.5:
        with st.expander("💡 AI Đề xuất cách phòng ngừa khẩn cấp"):
            advice_prompt = f"""
            Thời tiết: {T}°C, ẩm {H}%, gió {W}m/s. Bệnh nguy cơ nhất: {top_disease} ({int(max_risk*100)}%).
            Đề xuất 3 hành động phòng ngừa khẩn cấp cho {selected_p_forecast}.
            Ngắn gọn, gạch đầu dòng, tiếng Việt, < 80 từ.
            """
            st.markdown(get_ai_prevention_advice(advice_prompt))

    st.write("---")
    
    # 2️⃣ Hiển thị chi tiết với Màu cảnh báo theo %
    r1, r2, r3 = st.columns(3)
    r4, r5, r6 = st.columns(3)
    cols = [r1, r2, r3, r4, r5, r6]
    
    items = list(risks.items())
    avg_risk = sum(risks.values())/5
    items.append(("Chỉ số chung", avg_risk))

    for col, (label, val) in zip(cols, items):
        with col:
            st.write(f"**{label}**")
            st.progress(val)
            # Thêm cảnh báo màu sắc theo %
            if val > 0.7:
                st.error(f"🔴 Nguy cơ: {int(val*100)}%")
            elif val > 0.4:
                st.warning(f"🟡 Cần theo dõi: {int(val*100)}%")
            else:
                st.success(f"🟢 An toàn: {int(val*100)}%")

    st.info(f"💡 Dự báo dựa trên tình trạng nhóm **{plant_type_focus}** tại {info['city']}.")

# =========================================================
# 8 & 9. QUẢN LÝ DANH SÁCH (CRUD + SEARCH + ANALYTICS)
# =========================================================
plants = st.session_state.data.get("plants", [])

# 1️⃣ Dashboard Tổng quát trên đầu
c_top1, c_top2 = st.columns([2, 1])
with c_top1:
    st.subheader("🌿 Quản lý Vườn")
with c_top2:
    st.metric("Tổng số cây", len(plants))

if plants:
    df_p = pd.DataFrame(plants)
    
    # 3️⃣ Chuẩn hóa hiển thị tuổi cây
    if "age_years" in df_p.columns:
        df_p["age_years"] = df_p["age_years"].fillna(0).astype(int)
        df_p = df_p.rename(columns={"age_years": "Tuổi (năm)"})

    # 1️⃣ Tìm cây nhanh (Search Engine)
    search = st.text_input("🔎 Tìm kiếm cây (theo giống hoặc tên)", placeholder="Ví dụ: Ớt, Cà chua...")
    
    if search:
        # Tìm kiếm không phân biệt hoa thường trong cột 'variety'
        df_display = df_p[df_p["variety"].str.contains(search, case=False, na=False)]
    else:
        df_display = df_p

    st.dataframe(df_display, use_container_width=True)

    # --- KHU VỰC QUẢN LÝ (SỬA & XÓA) ---
    st.divider()
    col_manage1, col_manage2 = st.columns(2)

    with col_manage1:
        st.write("### ✏️ Chỉnh sửa thông tin")
        plant_to_edit_str = st.selectbox(
            "Chọn cây cần sửa:",
            [f"{i} | {p.get('variety','Cây')} | {p.get('location','Vườn')}" for i, p in enumerate(plants)],
            key="edit_select"
        )
        edit_idx = int(plant_to_edit_str.split(" | ")[0])
        p_edit = plants[edit_idx]

        with st.expander("Mở Form chỉnh sửa"):
            with st.form("edit_form"):
                new_variety = st.text_input("Giống cây", p_edit.get('variety'))
                new_loc = st.text_input("Vị trí", p_edit.get('location'))
                new_age = st.number_input("Tuổi (năm)", 0, 100, int(p_edit.get('age_years', 0)))
                
                if st.form_submit_button("💾 Lưu thay đổi"):
                    st.session_state.data["plants"][edit_idx].update({
                        "variety": new_variety,
                        "location": new_loc,
                        "age_years": new_age
                    })
                    save_data()
                    st.success("Đã cập nhật!")
                    st.rerun()

    with col_manage2:
        st.write("### 🗑️ Xóa cây")
        plant_to_del_str = st.selectbox(
            "Chọn cây muốn xóa:",
            [f"{i} | {p.get('variety','Cây')} | {p.get('location','Vườn')}" for i, p in enumerate(plants)],
            key="del_select"
        )
        del_idx = int(plant_to_del_str.split(" | ")[0])
        
        confirm_del = st.checkbox("Tôi chắc chắn muốn xóa cây này", key="confirm_del")
        if st.button("❌ Xác nhận Xóa", type="primary", disabled=not confirm_del):
            removed = st.session_state.data["plants"].pop(del_idx)
            save_data()
            st.toast(f"Đã xóa {removed.get('variety')}!")
            st.rerun()

    # 2️⃣ Thống kê đẹp hơn
    st.divider()
    st.write("### 📊 Thống kê phân bổ")
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.write("**Số lượng theo loại cây**")
        st.bar_chart(df_p["type"].value_counts())
    with c_chart2:
        st.write("**Số lượng theo vị trí (Vườn)**")
        st.bar_chart(df_p["location"].value_counts())
else:
    st.info("Chưa có cây nào trong vườn")


















































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
# 0. KHỞI TẠO SESSION STATE & LOAD DATA
# =========================================================
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

# Khởi tạo các biến session_state cần thiết
if "data" not in st.session_state:
    st.session_state.data = load_data()

if "weather" not in st.session_state:
    st.session_state["weather"] = {"city": "Vườn Aji", "temp": 25, "hum": 80, "wind": 0, "desc": "Đang lấy dữ liệu..."}

if "ai_result" not in st.session_state:
    st.session_state["ai_result"] = None

if "last_uploaded_eye" not in st.session_state:
    st.session_state["last_uploaded_eye"] = None

if "ai_loading" not in st.session_state:
    st.session_state["ai_loading"] = False

# ================================
# LẤY API KEY TỪ STREAMLIT SECRETS
# ================================
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    st.warning("⚠️ Chưa tìm thấy GEMINI_API_KEY trong Secrets.")
    model = None

# =============================
# 1. CẤU HÌNH
# =============================
try:
    st.set_page_config(page_title="Aji Farm", layout="wide", page_icon="🌶️")
except:
    pass

WEATHER_API_KEY = "66ad043d6024749fa4bf92f0a6782397"

# =============================
# 2. SAVE DATA (1️⃣ TỐI ƯU CACHE CHỈ ĐỊNH)
# =============================
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)
    # Chỉ xóa cache của hàm load_data, giữ lại cache thời tiết
    load_data.clear()

# =============================
# 3. WEATHER FUNCTION
# =============================
@st.cache_data(ttl=600)
def get_weather(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=vi"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

# =============================
# 4 & 5. GPS & WEATHER DATA
# =============================
loc = st.session_state.get("location", None)
if loc is None:
    loc_input = get_geolocation()
    if loc_input:
        st.session_state.location = loc_input
        loc = loc_input

if loc and "coords" in loc:
    lat, lon = loc["coords"]["latitude"], loc["coords"]["longitude"]
    w = get_weather(lat, lon)
    if w and w.get("cod") == 200:
        st.session_state["weather"] = {
            "city": w.get("name", "Vườn"),
            "temp": w["main"]["temp"],
            "hum": w["main"]["humidity"],
            "wind": w.get("wind", {}).get("speed", 0),
            "desc": w["weather"][0]["description"].capitalize()
        }

info = st.session_state["weather"]

# =============================
# 6. UI CHÍNH
# =============================
st.title("🌶️ Aji Farm Management")
st.subheader(f"📍 {info['city']}")

c1, c2, c3 = st.columns(3)
c1.metric("🌡 Nhiệt độ", f"{info['temp']} °C")
c2.metric("💧 Độ ẩm", f"{info['hum']} %")
c3.metric("💨 Gió", f"{info['wind']} m/s")
st.info(info["desc"])
st.divider()

# =============================
# 7. THÊM CÂY
# =============================
st.subheader("🌱 Thêm cây trồng")
with st.form("add_plant"):
    col1, col2 = st.columns(2)
    with col1:
        plant_type = st.selectbox("Nhóm cây", ["Rau","Gia vị","Cây dây leo","Cây thân bụi","Cây thân gỗ","Cây ăn trái","Cây cảnh"])
        species = st.text_input("Loài cây")
        variety = st.text_input("Giống")
    with col2:
        loc_input_box = st.text_input("Khu trồng")
        p_date = st.date_input("Ngày trồng", date.today())
        age_input = st.number_input("Tuổi cây (năm)", 0, 100, 0)
    
    if st.form_submit_button("➕ Thêm cây"):
        plant = {"type": plant_type, "species": species, "variety": variety, "location": loc_input_box, "plant_date": str(p_date), "age_years": age_input}
        st.session_state.data["plants"].append(plant)
        save_data()
        st.success("Đã thêm cây")
        st.rerun()

# =============================
# 8 & 9. DANH SÁCH & THỐNG KÊ
# =============================
plants = st.session_state.data.get("plants", [])
if plants:
    st.subheader("🌿 Danh sách cây")
    df_p = pd.DataFrame(plants)
    st.dataframe(df_p, use_container_width=True)
    st.subheader("📊 Thống kê vườn")
    st.bar_chart(df_p["type"].value_counts())
else:
    st.info("Chưa có cây nào trong vườn")

# =========================================================
# 10. DỰ BÁO DỊCH TỄ
# =========================================================
st.divider()
st.subheader("🔮 Hệ thống Dự báo Dịch tễ học")
T, H, W = info["temp"], info["hum"], info["wind"]
anthracnose_ri = min((H / 100) * (1.2 if 22 <= T <= 28 else 0.6), 1.0)
powdery_ri = min(((100 - H) / 100) * (1.1 if 15 <= T <= 25 else 0.4) * (1.2 if W > 3 else 1.0), 1.0)

col_a, col_b = st.columns(2)
with col_a:
    st.write("🛡 **Chỉ số Thán thư**")
    st.progress(anthracnose_ri)
    if anthracnose_ri > 0.7: st.error("🚨 NGUY CƠ CAO")
    elif anthracnose_ri > 0.4: st.warning("⚠️ CẢNH BÁO")
    else: st.success("✅ AN TOÀN")

with col_b:
    st.write("🛡 **Chỉ số Phấn trắng**")
    st.progress(powdery_ri)
    if powdery_ri > 0.7: st.error("🚨 NGUY CƠ CAO")
    elif powdery_ri > 0.4: st.warning("⚠️ CÓ ĐIỀU KIỆN PHÁT SINH")
    else: st.success("✅ AN TOÀN")

# =========================================================
# 11. AI CHẨN ĐOÁN (2️⃣ CHỐNG SPAM & 3️⃣ TỐI ƯU KÍCH THƯỚC ẢNH)
# =========================================================
st.divider()
st.subheader("🧠 AI Phân tích bệnh cây (Context-Aware AI)")
st.caption("📷 Chụp sát vùng lá bị bệnh để AI phân tích chính xác hơn.")
img_file = st.camera_input("Chụp ảnh lá cây")

if img_file is not None:
    img_id = img_file.getvalue()[:20]
    if st.session_state.get("last_uploaded_eye") != img_id:
        st.session_state.pop("ai_result", None)
        st.session_state["last_uploaded_eye"] = img_id

    try:
        img = ImageOps.exif_transpose(Image.open(img_file)).convert("RGB")
        # 3️⃣ Resize 768px để nhanh hơn
        img.thumbnail((768, 768))
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.image(img, caption="Ảnh vừa chụp", use_container_width=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Nhiệt", f"{info['temp']}°C")
            c2.metric("💧 Ẩm", f"{info['hum']}%")
            c3.metric("💨 Gió", f"{info['wind']} m/s")

        with col2:
            st.markdown("### 🔬 Kết luận AI")
            
            # 2️⃣ Disable nút khi đang load
            is_loading = st.session_state.get("ai_loading", False)
            if st.button("🔍 Bắt đầu phân tích ngay", use_container_width=True, disabled=is_loading):
                if model:
                    st.session_state["ai_loading"] = True
                    with st.spinner("AI đang soi bệnh..."):
                        prompt = f"""Bạn là chuyên gia bệnh học thực vật. Tập trung: đốm nâu, rìa lá cháy, phấn trắng, vết thối, biến màu.
                        DỮ LIỆU KHÍ HẬU: {info}
                        Trả lời: 1. Bệnh nghi ngờ nhất | 2. Độ tin cậy (%) | 3. Nguyên nhân môi trường | 4. Cách xử lý sinh học.
                        Tiếng Việt, dưới 120 từ."""
                        
                        image_bytes = buf.getvalue()
                        try:
                            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
                            if hasattr(response, "text"):
                                st.session_state["ai_result"] = response.text
                            else:
                                st.session_state["ai_result"] = "AI chưa trả kết quả. Hãy thử chụp lại."
                        except Exception:
                            st.error("❌ Lỗi kết nối AI.")
                        finally:
                            st.session_state["ai_loading"] = False
                            st.rerun() # Rerun để cập nhật trạng thái disabled của nút
                else: st.error("⚠️ Chưa cấu hình API Key.")

            if st.session_state.get("ai_result"):
                st.success(st.session_state["ai_result"])
                st.caption("⚠️ Kết quả chỉ mang tính tham khảo.")
    except Exception as e:
        st.error(f"❌ Lỗi: {e}")

# =========================================================
# 12. NHẬT KÝ
# =========================================================
st.divider()
st.subheader("📝 Nhật ký ghi nhận bệnh")

if not plants:
    st.warning("Chưa có cây trong vườn để ghi nhật ký.")
else:
    plant_names = [
        f"{p.get('variety','Cây')} ({p.get('location','Vườn')})"
        for p in plants
    ]
    selected_p = st.selectbox("Chọn cây đang kiểm tra", ["Chưa xác định"] + plant_names)

    if st.button("💾 Lưu chẩn đoán vào Nhật ký"):
        if st.session_state.get("ai_result"):
            log = {"date": str(date.today()), "plant": selected_p, "diagnosis": st.session_state["ai_result"]}
            if "disease_logs" not in st.session_state.data: st.session_state.data["disease_logs"] = []
            st.session_state.data["disease_logs"].append(log)
            save_data()
            st.toast("Đã ghi nhật ký!", icon="✅")
        else: st.warning("Vui lòng phân tích ảnh trước!")

if st.checkbox("📖 Xem lịch sử"):
    logs = st.session_state.data.get("disease_logs", [])
    if logs:
        df_l = pd.DataFrame(logs)
        df_l["date"] = pd.to_datetime(df_l["date"])
        st.dataframe(df_l.sort_values("date", ascending=False), use_container_width=True)

# =========================================================
# 13 & 14. AI HỌC LỆNH & FEEDBACK
# =========================================================
st.divider()
st.subheader("🧬 AI Học & Đề xuất Quy trình")
if plants:
    target_plant = st.selectbox("Chọn cây lập quy trình:", plant_names, key="proc_select")
    if st.button("🚀 AI Tạo Quy trình chuẩn"):
        if model:
            with st.spinner("AI đang tổng hợp..."):
                try:
                    res = model.generate_content(f"Quy trình bón phân, sâu bệnh cho {target_plant} trong điều kiện {info}. Tiếng Việt, < 200 từ.")
                    st.session_state["current_procedure"] = getattr(res, "text", "")
                    st.session_state["current_plant"] = target_plant
                    st.markdown(st.session_state["current_procedure"])
                except:
                    st.error("Lỗi kết nối AI.")

if st.session_state.get("current_procedure"):
    with st.form("feedback_form"):
        score = st.select_slider("Hiệu quả thực tế:", options=["Thất bại", "Kém", "Ổn", "Tốt", "Rất tốt"])
        note = st.text_area("Ghi chú kinh nghiệm:")
        if st.form_submit_button("💾 Xác nhận"):
            fb = {"date": str(date.today()), "plant": st.session_state["current_plant"], "score": score, "user_note": note}
            if "treatment_feedback" not in st.session_state.data: st.session_state.data["treatment_feedback"] = []
            st.session_state.data["treatment_feedback"].append(fb)
            save_data()
            st.session_state.pop("current_procedure", None)
            st.rerun()



























































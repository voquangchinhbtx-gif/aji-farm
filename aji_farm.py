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

# ================================
# LẤY API KEY TỪ STREAMLIT SECRETS
# ================================
API_KEY = st.secrets.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
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

DATA_FILE = "farm_data.json"
API_KEY = "66ad043d6024749fa4bf92f0a6782397"

# =============================
# 2. LOAD DATA
# =============================

if "data" not in st.session_state:

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            st.session_state.data=json.load(f)

    else:
        st.session_state.data={"plants":[]}

def save_data():

    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)


# =============================
# 3. WEATHER
# =============================

@st.cache_data(ttl=600)
def get_weather(lat,lon):

    try:
        url=f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=vi"

        r=requests.get(url,timeout=10)

        return r.json()

    except:
        return None


# =============================
# 4. GPS
# =============================

if "location" not in st.session_state:
    st.session_state.location=None

if st.session_state.location is None:
    loc=get_geolocation()

    if loc:
        st.session_state.location=loc

loc=st.session_state.location


# =============================
# 5. WEATHER DATA
# =============================

info={
"city":"Vườn Aji",
"temp":25,
"hum":80,
"wind":0,
"desc":"Đang lấy dữ liệu thời tiết"
}

if loc and "coords" in loc:

    lat=loc["coords"]["latitude"]
    lon=loc["coords"]["longitude"]

    w=get_weather(lat,lon)

    if w and w.get("cod")==200:

        info["city"]=w.get("name","Vườn")
        info["temp"]=w["main"]["temp"]
        info["hum"]=w["main"]["humidity"]
        info["wind"]=w.get("wind",{}).get("speed",0)
        info["desc"]=w["weather"][0]["description"].capitalize()


# =============================
# 6. UI
# =============================

st.title("🌶️ Aji Farm Management")

# ===== WEATHER =====

st.subheader(f"📍 {info['city']}")

c1,c2,c3=st.columns(3)

c1.metric("🌡 Nhiệt độ",f"{info['temp']} °C")
c2.metric("💧 Độ ẩm",f"{info['hum']} %")
c3.metric("💨 Gió",f"{info['wind']} m/s")

st.info(info["desc"])

st.divider()


# =============================
# 7. THÊM CÂY
# =============================

st.subheader("🌱 Thêm cây trồng")

with st.form("add_plant"):

    col1,col2=st.columns(2)

    with col1:

        plant_type=st.selectbox(
        "Nhóm cây",
        ["Rau","Gia vị","Cây dây leo","Cây thân bụi","Cây thân gỗ","Cây ăn trái","Cây cảnh"]
        )

        species=st.text_input("Loài cây")

        variety=st.text_input("Giống")

    with col2:

        location=st.text_input("Khu trồng")

        plant_date=st.date_input("Ngày trồng",date.today())

        age=st.number_input("Tuổi cây (năm)",0,100,0)

    submit=st.form_submit_button("➕ Thêm cây")

    if submit:

        plant={

        "type":plant_type,
        "species":species,
        "variety":variety,
        "location":location,
        "plant_date":str(plant_date),
        "age_years":age

        }

        st.session_state.data["plants"].append(plant)

        save_data()

        st.success("Đã thêm cây")

        st.rerun()


# =============================
# 8. DANH SÁCH CÂY
# =============================

st.subheader("🌿 Danh sách cây trong vườn")

plants=st.session_state.data["plants"]

if plants:

    df=pd.DataFrame(plants)

    st.dataframe(df,use_container_width=True)

else:

    st.info("Chưa có cây nào trong vườn")


# =============================
# 9. THỐNG KÊ
# =============================

if plants:

    st.subheader("📊 Thống kê vườn")

    df=pd.DataFrame(plants)

    chart=df["type"].value_counts()

    st.bar_chart(chart)
# =============================
# 10. DỰ BÁO DỊCH TỄ CHUYÊN SÂU
# =============================

st.divider()
st.subheader("🔮 Hệ thống Dự báo Dịch tễ học")

# Lấy dữ liệu môi trường
T = info.get("temp", 25)
H = info.get("hum", 70)
W = info.get("wind", 0)

# =============================
# MÔ HÌNH PHÂN TÍCH
# =============================

# 1️⃣ Thán thư (Anthracnose)
anthracnose_ri = (H / 100) * (1.2 if 22 <= T <= 28 else 0.6)
anthracnose_ri = min(anthracnose_ri, 1.0)

# 2️⃣ Phấn trắng (Powdery Mildew)
powdery_ri = ((100 - H) / 100) * (1.1 if 15 <= T <= 25 else 0.4)

# Gió giúp phát tán bào tử
if W > 3:
    powdery_ri *= 1.2

powdery_ri = min(powdery_ri, 1.0)

# =============================
# HIỂN THỊ
# =============================

col_a, col_b = st.columns(2)

with col_a:

    st.write("🛡 **Chỉ số Thán thư (Anthracnose)**")

    st.progress(anthracnose_ri)

    if anthracnose_ri > 0.7:
        st.error("🚨 NGUY CƠ CAO: Điều kiện lý tưởng cho nấm thán thư bùng phát.")
    elif anthracnose_ri > 0.4:
        st.warning("⚠️ CẢNH BÁO: Môi trường bắt đầu thuận lợi cho nấm.")
    else:
        st.success("✅ AN TOÀN: Khả năng bùng phát thấp.")

with col_b:

    st.write("🛡 **Chỉ số Phấn trắng (Powdery Mildew)**")

    st.progress(powdery_ri)

    if powdery_ri > 0.7:
        st.error("🚨 NGUY CƠ CAO: Thời tiết khô và gió mạnh → nấm dễ phát tán.")
    elif powdery_ri > 0.4:
        st.warning("⚠️ Có điều kiện phát sinh nấm phấn trắng.")
    else:
        st.success("✅ Môi trường hiện khá an toàn.")

# =============================
# CHU KỲ DỊCH TỄ THEO MÙA
# =============================

st.write("---")
st.write("📅 **Dự báo rủi ro theo chu kỳ mùa (Dữ liệu nông nghiệp mở)**")

seasonal_risk = pd.DataFrame({
    "Tháng": list(range(1, 13)),
    "Sâu hại (Bọ trĩ)": [0.8,0.9,0.7,0.4,0.2,0.1,0.2,0.3,0.5,0.6,0.7,0.8],
    "Nấm bệnh (Mưa nhiều)": [0.1,0.2,0.4,0.6,0.8,0.9,0.7,0.8,0.9,0.7,0.4,0.2]
})

st.line_chart(seasonal_risk.set_index("Tháng"))

st.caption(
"ℹ️ Mô hình dự báo dựa trên sự kết hợp giữa dữ liệu thời tiết thực và mô hình dịch tễ cây trồng."
)
import streamlit as st
import pandas as pd
import io
import google.generativeai as genai
from PIL import Image, ImageOps
from datetime import date

# =========================================================
# 11. AI CHẨN ĐOÁN KẾT HỢP DỮ LIỆU MÔI TRƯỜNG
# =========================================================

st.divider()
st.subheader("🧠 AI Phân tích bệnh cây (Context-Aware AI)")

# Lấy dữ liệu môi trường an toàn
info = st.session_state.get("weather", locals().get("info", {}))

# Camera
img_file = st.camera_input("📷 Chụp lá cây nghi ngờ")

# Reset kết quả khi có ảnh mới
if img_file is not None:
    if "last_uploaded_eye" not in st.session_state or st.session_state["last_uploaded_eye"] != img_file.name:
        st.session_state.pop("ai_result", None)
        st.session_state["last_uploaded_eye"] = img_file.name

if img_file is not None:

    try:
        # =============================
        # XỬ LÝ ẢNH
        # =============================
        img = Image.open(img_file)

        img = ImageOps.exif_transpose(img)

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.thumbnail((1024,1024))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        # =============================
        # DỮ LIỆU MÔI TRƯỜNG
        # =============================
        env_context = f"""
        Vị trí: {info.get('city','Vườn')}
        Nhiệt độ: {info.get('temp','?')}°C
        Độ ẩm: {info.get('hum','?')}%
        Gió: {info.get('wind','?')} m/s
        Điều kiện: {info.get('desc','Không rõ')}
        """

        st.markdown("---")

        col1, col2 = st.columns([1,1.2])

        # =============================
        # HIỂN THỊ ẢNH
        # =============================
        with col1:

            st.image(img, caption="Ảnh vừa chụp", use_container_width=True)

            c1,c2,c3 = st.columns(3)
            c1.metric("🌡️ Nhiệt", f"{info.get('temp','?')}°C")
            c2.metric("💧 Ẩm", f"{info.get('hum','?')}%")
            c3.metric("💨 Gió", f"{info.get('wind','?')} m/s")

        # =============================
        # AI PHÂN TÍCH
        # =============================
        with col2:

            st.markdown("### 🔬 Kết luận AI")

            if st.button("🔍 Bắt đầu phân tích ngay", use_container_width=True):

                with st.spinner("AI đang phân tích bệnh cây..."):

                    prompt = f"""
                    Bạn là chuyên gia bệnh học thực vật.
                    Tập trung vào các đốm biến màu, rìa lá cháy,
                    hoặc lớp phấn bám trên bề mặt lá trong ảnh.

                    DỮ LIỆU KHÍ HẬU THỰC TẾ:
                    {env_context}

                    Hãy cho biết:

                    1. Bệnh nghi ngờ nhất
                    2. Độ tin cậy (%)
                    3. Vì sao môi trường này gây bệnh
                    4. Cách xử lý sinh học

                    Trả lời tiếng Việt dưới 120 từ.
                    """

                    response = model.generate_content(
                        [
                            prompt,
                            {"mime_type":"image/jpeg","data":buffer.getvalue()}
                        ]
                    )

                    result = getattr(response,"text","AI không trả dữ liệu.")

                    st.session_state["ai_result"] = result

            # =============================
            # HIỂN THỊ KẾT QUẢ BỀN VỮNG
            # =============================
            if "ai_result" in st.session_state:
                st.success(st.session_state["ai_result"])
            else:
                st.info("Nhấn nút phía trên để AI phân tích hình ảnh và dữ liệu môi trường.")

    except Exception as e:
        st.error(f"❌ Lỗi xử lý ảnh: {e}")

# =========================================================
# 12. NHẬT KÝ VÀ SẮP XẾP DỮ LIỆU (SMART LOGGING)
# =========================================================
st.divider()
st.subheader("📝 Nhật ký ghi nhận bệnh")

# Chống AttributeError cho session_state.data
if "data" not in st.session_state:
    st.session_state["data"] = {"plants": [], "disease_logs": []}

plants = st.session_state.data.get("plants", [])
plant_names = [f"{p.get('variety','Cây')} ({p.get('location','Vườn')})" for p in plants]

selected_p = st.selectbox("Chọn cây đang kiểm tra", ["Chưa xác định"] + plant_names)

if st.button("💾 Lưu chẩn đoán vào Nhật ký", use_container_width=True):
    if "ai_result" in st.session_state:
        log_entry = {
            "date": str(date.today()),
            "plant": selected_p,
            "diagnosis": st.session_state["ai_result"]
        }
        
        if "disease_logs" not in st.session_state.data:
            st.session_state.data["disease_logs"] = []
            
        st.session_state.data["disease_logs"].append(log_entry)
        save_data() # Hàm lưu file JSON của bạn
        st.toast(f"Đã ghi nhận bệnh trạng cho {selected_p}", icon="✅")
    else:
        st.warning("⚠️ Vui lòng chụp ảnh và phân tích trước khi lưu.")

# Hiển thị lịch sử (Sắp xếp thời gian chuẩn)
if st.checkbox("📖 Xem lịch sử bệnh hại (Mới nhất)"):
    logs = st.session_state.data.get("disease_logs", [])
    if logs:
        df_logs = pd.DataFrame(logs)
        # Ép kiểu datetime để sort chuẩn (Chống lỗi sort string)
        df_logs["date"] = pd.to_datetime(df_logs["date"])
        df_logs = df_logs.sort_values("date", ascending=False)
        
        # Format lại ngày để hiển thị kiểu Việt Nam sau khi đã sort
        df_logs["date"] = df_logs["date"].dt.strftime('%d/%m/%Y')
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("Chưa có nhật ký ghi nhận.")
import pandas as pd
import streamlit as st
from datetime import date

# =========================================================
# 13. AI HỌC LỆNH & TỐI ƯU QUY TRÌNH (BẢN THIẾT GIÁP)
# =========================================================
st.divider()
st.subheader("🧬 AI Học & Đề xuất Quy trình chuẩn")

# 1. KIỂM TRA NGỮ CẢNH AN TOÀN
info = st.session_state.get("weather", locals().get("info", {}))
if "data" not in st.session_state:
    st.session_state["data"] = {"plants": [], "disease_logs": [], "treatment_feedback": []}

plants = st.session_state.data.get("plants", [])

if not plants:
    st.info("💡 Hãy thêm cây trồng ở Mục 7 để bắt đầu lộ trình học tập.")
else:
    plant_options = [f"{p.get('variety','Cây')} ({p.get('location','Vườn')})" for p in plants]
    target_plant = st.selectbox("Chọn cây để lập quy trình chuẩn:", plant_options)
    
    p_info = next((p for p in plants if f"{p.get('variety')} ({p.get('location')})" == target_plant), None)
    
    if not p_info:
        st.error("❌ Không tìm thấy dữ liệu cây trồng.")
    else:
        # Chuẩn hóa tuổi cây
        d_start = pd.to_datetime(p_info.get('plant_date', str(date.today())))
        age_days = max(0, (pd.Timestamp.now() - d_start).days)
        
        # Xử lý feedback gọn nhẹ cho Prompt
        user_feedback = st.session_state.data.get("treatment_feedback", [])
        recent_feedback = [
            {"score": f.get("score"), "note": f.get("user_note", "")[:100]} 
            for f in user_feedback[-3:]
        ]

        if st.button("🚀 AI Tạo Quy trình chuẩn", use_container_width=True):
            model = globals().get("model", None)
            if not model:
                st.error("⚠️ AI chưa được cấu hình API Key.")
                st.stop()

            with st.spinner("🧠 AI đang tổng hợp kinh nghiệm địa phương..."):
                try:
                    learning_prompt = f"""
                    Bạn là chuyên gia nông nghiệp chính xác.
                    Dữ liệu cây: {p_info.get('variety')} ({p_info.get('species','Chưa rõ')}), {age_days} ngày tuổi.
                    Địa phương: {info.get('city', 'Chưa xác định')}, {info.get('temp', '?')}°C.
                    Kinh nghiệm thực tế: {recent_feedback if recent_feedback else "Chưa có"}.

                    Nhiệm vụ: Tạo quy trình gồm: 1. Giai đoạn sinh trưởng | 2. Bón phân | 3. Sâu bệnh.
                    Trả lời tiếng Việt, tối đa 200 từ.
                    """

                    response = model.generate_content(learning_prompt)
                    res_text = getattr(response, "text", "").strip()
                    if not res_text:
                        res_text = "AI chưa đưa ra kết quả. Hãy thử lại."
                    
                    # Lưu ngữ cảnh vào session an toàn
                    st.session_state["current_procedure"] = res_text
                    st.session_state["current_plant"] = target_plant
                    
                    st.success(f"### 📋 Quy trình chuẩn cho {p_info.get('variety')}")
                    st.markdown(res_text)
                    
                except Exception as e:
                    st.error(f"❌ Lỗi AI: {e}")

# =========================================================
# 14. VÒNG LẶP PHẢN HỒI (HỌC TỪ THỰC TẾ)
# =========================================================
if "current_procedure" in st.session_state:
    st.divider()
    st.subheader("⭐ Đánh giá & Dạy AI (Feedback)")
    
    with st.form("feedback_loop_form"):
        score = st.select_slider("Mức độ hiệu quả thực tế:", options=["Thất bại", "Kém", "Ổn", "Tốt", "Rất tốt"])
        note = st.text_area("Ghi chú thực tế (vd: loại phân, nồng độ, kết quả):")
        
        if st.form_submit_button("💾 Xác nhận để AI ghi nhớ"):
            new_feedback = {
                "date": str(date.today()),
                "plant": st.session_state.get("current_plant", "Không rõ"),
                "score": score,
                "user_note": note,
                "procedure": st.session_state.get("current_procedure", "")
            }

            # 1. Đảm bảo key tồn tại trước khi append (Góp ý số 1)
            if "treatment_feedback" not in st.session_state.data:
                st.session_state.data["treatment_feedback"] = []
            
            st.session_state.data["treatment_feedback"].append(new_feedback)
            save_data()
            
            st.toast("AI đã nạp thêm kinh nghiệm mới!", icon="🧠")
            
            # 2. Xóa session_state an toàn bằng pop (Góp ý số 2)
            st.session_state.pop("current_procedure", None)
            st.session_state.pop("current_plant", None)
            
            # Rerun để làm sạch giao diện
            st.rerun()

























































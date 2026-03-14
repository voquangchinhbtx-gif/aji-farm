import streamlit as st
import json
import os
import requests
from datetime import date, datetime
import pandas as pd
import google.generativeai as genai
from PIL import Image, ImageOps
import io
import copy
import numpy as np
from streamlit_js_eval import get_geolocation

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Aji Farm AI",
    page_icon="🌶",
    layout="wide"
)

DATA_FILE="aji_farm_db.json"
WEATHER_KEY="66ad043d6024749fa4bf92f0a6782397"

# =====================================================
# LOAD AI GEMINI
# =====================================================

@st.cache_resource
def load_ai():
    try:
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=GEMINI_KEY)
        return genai.GenerativeModel("gemini-1.5-flash")
    except:
        return None

ai_model = load_ai()

# =====================================================
# DATABASE
# =====================================================

INIT_DATA={
    "plants":[],
    "disease_logs":[],
    "chat":[],
    "inventory":{"fertilizer":100,"pesticide":100}
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return copy.deepcopy(INIT_DATA)

def save():
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)

if "data" not in st.session_state:
    st.session_state.data=load_data()

# =====================================================
# CROP DATABASE
# =====================================================

CROP_DB={
    "aji_charapita":{"name":"Ớt Aji Charapita","water":500,"care":"Nắng mạnh, đất thoát nước tốt"},
    "tomato":{"name":"Cà chua","water":450,"care":"Cần giàn leo, tỉa chồi"},
    "lettuce":{"name":"Xà lách","water":200,"care":"Ưa mát"},
    "durian":{"name":"Sầu riêng","water":2000,"care":"Đất sâu"},
    "mango":{"name":"Xoài","water":1500,"care":"Phòng rầy bông"},
    "basil":{"name":"Húng quế","water":150,"care":"Ngắt hoa kích lá"}
}

# =====================================================
# GPS WEATHER
# =====================================================

@st.cache_data(ttl=600)
def get_weather(lat,lon):
    try:
        url=f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        r=requests.get(url)
        w=r.json()

        return{
            "temp":w["main"]["temp"],
            "hum":w["main"]["humidity"],
            "wind":w["wind"]["speed"]
        }
    except:
        return {"temp":28,"hum":70,"wind":2}

geo=get_geolocation()

if geo:
    w_info=get_weather(geo["coords"]["latitude"],geo["coords"]["longitude"])
else:
    w_info={"temp":28,"hum":70,"wind":2}

# =====================================================
# AI NPK LOCAL (KHÔNG GEMINI)
# =====================================================

def analyze_npk(img):

    arr=np.array(img)

    r=arr[:,:,0].mean()
    g=arr[:,:,1].mean()
    b=arr[:,:,2].mean()

    result=[]

    if g < r*0.9:
        result.append("Thiếu Nitrogen (N) → lá vàng")

    if b > g*0.8:
        result.append("Thiếu Phosphorus (P) → lá sẫm")

    if r > g*1.2:
        result.append("Thiếu Potassium (K) → cháy mép lá")

    if not result:
        result.append("Lá bình thường")

    return result

# =====================================================
# DASHBOARD
# =====================================================

st.title("🌶 AJI FARM AI")

tab1,tab2,tab3=st.tabs([
    "🌤 Tổng quan",
    "🌱 Vườn cây",
    "📷 Bác sĩ AI"
])

# =====================================================
# TAB 1
# =====================================================

with tab1:

    c1,c2,c3=st.columns(3)

    c1.metric("🌡 Nhiệt độ",f"{w_info['temp']}°C")
    c2.metric("💧 Độ ẩm",f"{w_info['hum']}%")
    c3.metric("🌬 Gió",f"{w_info['wind']} m/s")

    risk=min((w_info["hum"]*0.6 + w_info["temp"]*0.3),100)

    st.metric("🦠 Nguy cơ sâu bệnh",f"{int(risk)}%")

    if w_info["hum"]>80 and w_info["temp"]>26:

        st.error("""
Nguy cơ cao:
• Bọ trĩ
• Nấm phấn trắng

Nguyên nhân:
• độ ẩm cao
• lá rậm

Xử lý:
Sinh học: neem oil

Hóa học: Abamectin
""")

# =====================================================
# TAB 2
# =====================================================

with tab2:

    st.subheader("🌱 Thêm cây")

    with st.form("addplant"):

        col1,col2=st.columns(2)

        crop=col1.selectbox(
            "Loại cây",
            list(CROP_DB.keys()),
            format_func=lambda x:CROP_DB[x]["name"]
        )

        plant_date=col2.date_input("Ngày trồng",date.today())

        if st.form_submit_button("➕ Thêm cây"):

            st.session_state.data["plants"].append({
                "crop":crop,
                "date":str(plant_date)
            })

            save()
            st.rerun()

    st.divider()

    st.subheader("🌿 Danh sách cây")

    if st.session_state.data["plants"]:

        df=pd.DataFrame(st.session_state.data["plants"])

        df["Tên"]=df["crop"].map(lambda x:CROP_DB[x]["name"])

        df["date"]=pd.to_datetime(df["date"],errors="coerce")

        df["Tuổi cây"]=(datetime.now()-df["date"]).dt.days

        st.dataframe(df[["Tên","date","Tuổi cây"]])

# =====================================================
# TAB 3
# =====================================================

with tab3:

    st.subheader("📷 AI nhận diện bệnh")

    cam=st.camera_input("Chụp lá cây")

    if cam:

        img=ImageOps.exif_transpose(Image.open(cam)).convert("RGB")

        st.image(img,width=350)

        st.subheader("🌿 Phân tích NPK (AI local)")

        result=analyze_npk(img)

        for r in result:
            st.warning(r)

        if st.button("AI phân tích bệnh"):

            if ai_model:

                with st.spinner("Đang hỏi ý kiến chuyên gia AI..."):

                    buf=io.BytesIO()
                    img.save(buf,format="JPEG")

                    prompt=f"""
Bạn là chuyên gia bệnh cây.

Thông tin môi trường:
Nhiệt độ {w_info['temp']}°C
Độ ẩm {w_info['hum']}%

Dựa vào ảnh hãy:

1. Chẩn đoán bệnh
2. Đánh giá mức độ
3. Đưa hướng xử lý sinh học
4. Đưa hướng xử lý hóa học
"""

                    res=ai_model.generate_content(
                        [prompt,{
                            "mime_type":"image/jpeg",
                            "data":buf.getvalue()
                        }],
                        generation_config={"max_output_tokens":600}
                    )

                    st.success("Kết quả AI")
                    st.write(res.text)

# =====================================================
# AI CHAT
# =====================================================

st.divider()
st.subheader("🤖 Trợ lý nông nghiệp")

for c in st.session_state.data["chat"][-3:]:

    with st.chat_message("user"):
        st.write(c["q"])

    with st.chat_message("assistant"):
        st.write(c["a"])

q=st.chat_input("Hỏi về sâu bệnh, phân bón...")

if q and ai_model:

    with st.spinner("AI đang suy nghĩ..."):

        res=ai_model.generate_content(
            f"Bạn là chuyên gia nông nghiệp. Trả lời dễ hiểu cho nông dân: {q}",
            generation_config={"max_output_tokens":400}
        )

    st.session_state.data["chat"].append({
        "q":q,
        "a":res.text
    })

    save()
    st.rerun()

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.header("⚙ Quản lý vật tư")

    inv=st.session_state.data["inventory"]

    st.write(f"Thuốc BVTV: {inv['pesticide']}%")
    st.write(f"Phân bón: {inv['fertilizer']}%")

    if st.button("Nạp đầy kho"):

        st.session_state.data["inventory"]={
            "fertilizer":100,
            "pesticide":100
        }

        save()
        st.rerun()


















































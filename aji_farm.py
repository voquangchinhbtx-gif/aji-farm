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
from streamlit_js_eval import get_geolocation
import numpy as np   # ⭐ BỔ SUNG

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
# LOAD AI
# =====================================================

@st.cache_resource
def load_ai():
    try:
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=GEMINI_KEY)

        return genai.GenerativeModel("gemini-1.5-flash-latest")

    except:
        return None

ai_model = load_ai()

# =====================================================
# USER LOCATION (GPS)
# =====================================================

geo = get_geolocation()

if geo and "coords" in geo:
    lat = geo["coords"]["latitude"]
    lon = geo["coords"]["longitude"]
else:
    lat = 16.4637
    lon = 107.5909

# =====================================================
# CROP DATABASE
# =====================================================

CROP_DB={
    "aji_charapita":{
        "name":"Ớt Aji Charapita",
        "water":500,
        "care":"Nắng mạnh, đất thoát nước tốt, bón hữu cơ"
    },
    "tomato":{
        "name":"Cà chua",
        "water":450,
        "care":"Cần giàn leo, tỉa chồi nách, phòng nấm sương mai"
    },
    "lettuce":{
        "name":"Xà lách",
        "water":200,
        "care":"Ưa mát, giữ ẩm đất, tránh nắng gắt"
    },
    "durian":{
        "name":"Sầu riêng",
        "water":2000,
        "care":"Đất sâu, thoát nước tốt, bón hữu cơ định kỳ"
    },
    "mango":{
        "name":"Xoài",
        "water":1500,
        "care":"Phòng rầy bông khi ra hoa, tỉa cành"
    },
    "basil":{
        "name":"Húng quế",
        "water":150,
        "care":"Ngắt hoa để kích thích ra lá"
    }
}

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

    st.session_state.data["inventory"]["fertilizer"]=min(
        st.session_state.data["inventory"]["fertilizer"],100
    )

    st.session_state.data["inventory"]["pesticide"]=min(
        st.session_state.data["inventory"]["pesticide"],100
    )

    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)

if "data" not in st.session_state:
    st.session_state.data=load_data()

# =====================================================
# WEATHER (GPS)
# =====================================================

@st.cache_data(ttl=600)
def get_weather(lat,lon):

    try:

        url=f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"

        r=requests.get(url,timeout=5)

        if r.status_code != 200:
            return{
                "temp":28,
                "hum":70,
                "wind":2
            }

        w=r.json()

        return{
            "temp":w["main"]["temp"],
            "hum":w["main"]["humidity"],
            "wind":w["wind"]["speed"]
        }

    except:

        return{
            "temp":28,
            "hum":70,
            "wind":2
        }

w_info=get_weather(lat,lon)

# =====================================================
# ⭐ AI PHÂN TÍCH NPK BẰNG MÀU LÁ (LOCAL)
# =====================================================

def analyze_leaf_npk(image):

    img = np.array(image)

    r = img[:,:,0].mean()
    g = img[:,:,1].mean()
    b = img[:,:,2].mean()

    result = []

    if g < r and g < 120:
        result.append("⚠ Có dấu hiệu thiếu ĐẠM (N) – lá vàng hoặc nhạt")

    if b > r and b > g:
        result.append("⚠ Có thể thiếu LÂN (P) – lá xanh đậm hoặc hơi tím")

    if r > 150 and g < 120:
        result.append("⚠ Có dấu hiệu thiếu KALI (K) – mép lá cháy")

    if not result:
        result.append("✅ Lá có vẻ dinh dưỡng cân đối")

    return result

# =====================================================
# UI TABS
# =====================================================

st.title("🌶 AJI FARM AI")

tab1,tab2,tab3=st.tabs([
"🌤 Tổng quan",
"🌱 Vườn cây",
"🤖 Bác sĩ AI"
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

# =====================================================
# TAB 2
# =====================================================

with tab2:

    st.subheader("🌱 Thêm cây trồng")

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

        st.dataframe(
            df[["Tên","date","Tuổi cây"]],
            use_container_width=True
        )

    else:

        st.info("Chưa có cây nào")

# =====================================================
# TAB 3
# =====================================================

with tab3:

    st.subheader("📷 AI nhận diện bệnh cây")

    cam=st.camera_input("Chụp lá cây")

    if cam:

        img=ImageOps.exif_transpose(Image.open(cam)).convert("RGB")

        st.image(img,width=350)

        if st.button("AI phân tích") and ai_model:

            with st.spinner("🤖 Đang hỏi chuyên gia AI..."):

                try:

                    buf=io.BytesIO()
                    img.save(buf,format="JPEG")

                    prompt = f"""
Bạn là chuyên gia bệnh cây.

Thông tin môi trường hiện tại:
Nhiệt độ: {w_info['temp']}°C
Độ ẩm: {w_info['hum']}%

Dựa vào ảnh cây trồng hãy:
1. Chẩn đoán bệnh
2. Đánh giá mức độ
3. Nguyên nhân
4. Xử lý sinh học
5. Xử lý hóa học
6. Phòng ngừa
"""

                    res=ai_model.generate_content(
                        [prompt,{"mime_type":"image/jpeg","data":buf.getvalue()}]
                    )

                    st.success("Kết quả AI")
                    st.write(res.text)

                except:

                    st.error("AI đang bận, thử lại sau.")

    st.divider()

    # ⭐ PHẦN MỚI

    st.subheader("🌿 Kiểm tra dinh dưỡng NPK (AI local - không tốn token)")

    leaf_file = st.file_uploader(
        "Upload ảnh lá cây để kiểm tra NPK",
        type=["jpg","png","jpeg"]
    )

    if leaf_file:

        leaf_img = Image.open(leaf_file)

        st.image(leaf_img,width=350)

        if st.button("Phân tích NPK"):

            result = analyze_leaf_npk(leaf_img)

            st.success("Kết quả phân tích")

            for r in result:
                st.write(r)

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


















































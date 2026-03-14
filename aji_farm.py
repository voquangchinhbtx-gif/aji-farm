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
        return genai.GenerativeModel("gemini-1.5-flash")
    except:
        return None

ai_model = load_ai()

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
    # CHỈNH SỬA 4: Inventory giới hạn tối đa 100%
    st.session_state.data["inventory"]["fertilizer"] = min(st.session_state.data["inventory"]["fertilizer"], 100)
    st.session_state.data["inventory"]["pesticide"] = min(st.session_state.data["inventory"]["pesticide"], 100)

    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(st.session_state.data,f,ensure_ascii=False,indent=2)

if "data" not in st.session_state:
    st.session_state.data=load_data()

# =====================================================
# WEATHER
# =====================================================

@st.cache_data(ttl=600)
def get_weather():
    try:
        url=f"https://api.openweathermap.org/data/2.5/weather?q=Hue&appid={WEATHER_KEY}&units=metric"
        r=requests.get(url)
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

w_info=get_weather()

# =====================================================
# DASHBOARD
# =====================================================

st.title("🌶 AJI FARM AI")

c1,c2,c3=st.columns(3)

c1.metric("🌡 Nhiệt độ",f"{w_info['temp']}°C")
c2.metric("💧 Độ ẩm",f"{w_info['hum']}%")
c3.metric("🌬 Gió",f"{w_info['wind']} m/s")

risk=min((w_info["hum"]*0.6 + w_info["temp"]*0.3),100)

st.metric("🦠 Nguy cơ sâu bệnh",f"{int(risk)}%")

# =====================================================
# ADD PLANT
# =====================================================

st.divider()
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

# =====================================================
# PLANT LIST
# =====================================================

st.divider()
st.subheader("🌿 Danh sách cây")

if st.session_state.data["plants"]:
    df=pd.DataFrame(st.session_state.data["plants"])
    df["Tên"]=df["crop"].map(lambda x:CROP_DB[x]["name"])
    
    # CHỈNH SỬA 3: Hiển thị thêm cột Chăm sóc lấy từ CROP_DB
    df["Chăm sóc"]=df["crop"].map(lambda x:CROP_DB[x]["care"])

    df["date"]=pd.to_datetime(df["date"],errors="coerce")
    df["Tuổi cây"]=(datetime.now()-df["date"]).dt.days

    st.dataframe(
        df[["Tên","date","Tuổi cây","Chăm sóc"]],
        use_container_width=True
    )

    idx=st.selectbox(
        "Chọn cây",
        range(len(df)),
        format_func=lambda x:df.iloc[x]["Tên"]
    )

    if st.button("Xóa cây"):
        if st.checkbox("Xác nhận xóa lần 1"):
            if st.checkbox("Xác nhận xóa lần 2"):
                st.session_state.data["plants"].pop(idx)
                save()
                st.rerun()
else:
    st.info("Chưa có cây nào")

# =====================================================
# AI CARE
# =====================================================

st.divider()
st.subheader("🤖 AI đề xuất chăm sóc")

if st.session_state.data["plants"]:
    for p in st.session_state.data["plants"]:
        crop=p["crop"]
        crop_info=CROP_DB[crop]
        
        # CHỈNH SỬA 1: Lấy lượng nước 'water' trực tiếp từ Database cây trồng
        water=crop_info["water"]

        if w_info["temp"]>32:
            water+=150

        if w_info["hum"]<60:
            water+=100

        st.info(f"""
🌱 {crop_info['name']}
🚿 Tưới {water} ml/gốc
🌤 Thời tiết: {w_info['temp']}°C / {w_info['hum']}%

Quy trình chăm sóc:
{crop_info['care']}
""")

# =====================================================
# DISEASE WARNING
# =====================================================

st.divider()
st.subheader("⚠ Cảnh báo sâu bệnh")

if w_info["hum"]>80 and w_info["temp"]>26:
    st.error("""
🚨 Nguy cơ cao: Bọ trĩ, Nấm phấn trắng
Nguyên nhân: • độ ẩm cao • lá rậm • thiếu thông thoáng
Xử lý sinh học: • neem oil • bẫy dính vàng
Hóa học: • Abamectin 1.8EC
Phòng ngừa: • tỉa lá gốc • kiểm tra vườn 3 ngày/lần
""")

# =====================================================
# AI CAMERA
# =====================================================

st.divider()
st.subheader("📷 AI nhận diện bệnh cây")

cam=st.camera_input("Chụp lá cây")

if cam:
    img=ImageOps.exif_transpose(Image.open(cam)).convert("RGB")
    st.image(img,width=350)

    if st.button("AI phân tích") and ai_model:
        buf=io.BytesIO()
        img.save(buf,format="JPEG")
        prompt="""Bạn là chuyên gia bệnh cây. Phân tích ảnh và trả lời theo format: Tên cây, Bệnh, Mức độ. Nguyên nhân. Xử lý sinh học. Xử lý hóa học (ghi rõ thuốc + liều). Phòng ngừa tái phát."""
        try:
            res=ai_model.generate_content(
                [prompt,{"mime_type":"image/jpeg","data":buf.getvalue()}],
                generation_config={"max_output_tokens":600}
            )
            st.success("Kết quả AI")
            st.write(res.text)
        except:
            st.error("AI lỗi")

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
    # CHỈNH SỬA 2: Giới hạn phản hồi của AI trong 400 tokens
    res=ai_model.generate_content(
        f"Bạn là chuyên gia nông nghiệp. Trả lời dễ hiểu cho nông dân: {q}",
        generation_config={"max_output_tokens":400}
    )
    st.session_state.data["chat"].append({"q":q, "a":res.text})
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
        st.session_state.data["inventory"]={"fertilizer":100, "pesticide":100}
        save()
        st.rerun()

    st.divider()
    if st.checkbox("Xác nhận reset"):
        if st.button("RESET APP"):
            st.session_state.data=copy.deepcopy(INIT_DATA)
            save()
            st.rerun()


















































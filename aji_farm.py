import streamlit as st
import requests
import os
import json
import pandas as pd
from datetime import date
from streamlit_js_eval import get_geolocation

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






















































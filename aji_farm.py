import streamlit as st
import pandas as pd
import json
import os
import requests
from datetime import datetime, date
from PIL import Image
import google.generativeai as genai

# ==========================================
# 1. CẤU HÌNH
# ==========================================
st.set_page_config(page_title="Aji Farm Pro v4", page_icon="🌶️", layout="wide")

DATA_FILE = "aji_master_data.json"

# ==========================================
# 2. AI CONFIG (BẢO MẬT)
# ==========================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except:
    model = None

# ==========================================
# 3. LOAD DATA
# ==========================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"plants":[],"yields":[],"expenses":[]}

def save_data(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)

if "data" not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# ==========================================
# 4. WEATHER HUẾ
# ==========================================
def get_weather():
    try:
        r = requests.get("https://wttr.in/Kim+Long+Hue?format=%t+%h",timeout=5).text
        t = int(r.split(" ")[0].replace("+","").replace("°C",""))
        h = int(r.split(" ")[1].replace("%",""))
        return t,h
    except:
        return 30,70

# ==========================================
# 5. CẢNH BÁO NÔNG NGHIỆP
# ==========================================
def get_alerts(temp,humi,plants):

    alerts=[]

    if temp>33:
        alerts.append("🌡️ Nắng nóng mạnh — cần che lưới")

    if temp>30 and humi<60:
        alerts.append("🚨 Nguy cơ bọ trĩ cao")

    if temp>28 and humi>85:
        alerts.append("🚨 Nguy cơ nấm bệnh")

    for p in plants:
        try:
            d=datetime.strptime(p["date"],"%Y-%m-%d").date()
            age=(date.today()-d).days

            if age>0 and age%15==0:
                alerts.append(f"🌿 {p['name']} {age} ngày: bón phân hữu cơ")

        except:
            pass

    return alerts

# ==========================================
# 6. SIDEBAR
# ==========================================
st.sidebar.title("🌶️ Aji Farm Pro")

st.sidebar.write("Ngày:",date.today().strftime("%d/%m/%Y"))

menu=st.sidebar.selectbox("Menu",[
"📊 Dashboard",
"🌱 Quản lý cây",
"📷 AI chẩn đoán",
"🧺 Thu hoạch",
"💰 Tài chính"
])

# ==========================================
# 7. DASHBOARD
# ==========================================
if menu=="📊 Dashboard":

    st.header("📊 Trung tâm điều khiển")

    temp,humi=get_weather()

    c1,c2=st.columns(2)

    c1.metric("Nhiệt độ",f"{temp}°C")
    c2.metric("Độ ẩm",f"{humi}%")

    st.divider()

    total_yield=sum(y["amount"] for y in data["yields"])
    total_cost=sum(e["amount"] for e in data["expenses"])

    c3,c4,c5=st.columns(3)

    c3.metric("Số cây",len(data["plants"]))
    c4.metric("Tổng thu hoạch",f"{total_yield} g")
    c5.metric("Chi phí",f"{total_cost:,} đ")

    st.subheader("Cảnh báo hôm nay")

    alerts=get_alerts(temp,humi,data["plants"])

    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.success("Vườn đang ổn định")

# ==========================================
# 8. QUẢN LÝ CÂY
# ==========================================
elif menu=="🌱 Quản lý cây":

    st.header("🌱 Danh sách cây")

    with st.form("add_plant"):

        name=st.text_input("Tên cây / chậu")

        d=st.date_input("Ngày trồng",value=date.today())

        if st.form_submit_button("Thêm cây") and name:

            data["plants"].append({
                "name":name,
                "date":str(d)
            })

            save_data(data)
            st.rerun()

    st.divider()

    for i,p in enumerate(data["plants"]):

        d=datetime.strptime(p["date"],"%Y-%m-%d").date()

        age=(date.today()-d).days

        c1,c2=st.columns([4,1])

        c1.write(f"🌱 {p['name']} — {age} ngày")

        if c2.button("Xóa",key=i):
            data["plants"].pop(i)
            save_data(data)
            st.rerun()

# ==========================================
# 9. AI CHẨN ĐOÁN
# ==========================================
elif menu=="📷 AI chẩn đoán":

    st.header("📷 AI bắt bệnh lá")

    img_file=st.camera_input("Chụp lá")

    if img_file:

        img=Image.open(img_file)

        st.image(img,width=400)

        if st.button("Phân tích"):

            if model:

                with st.spinner("AI đang phân tích..."):

                    try:

                        prompt="""
Bạn là chuyên gia nông nghiệp về ớt Aji Charapita.

Hãy phân tích:
1 bệnh gì
2 thiếu chất gì
3 cách xử lý hữu cơ an toàn
"""

                        res=model.generate_content([prompt,img])

                        st.success("Kết quả")

                        st.write(res.text)

                    except:

                        st.error("AI lỗi")

            else:

                st.error("Chưa cấu hình API")

# ==========================================
# 10. THU HOẠCH
# ==========================================
elif menu=="🧺 Thu hoạch":

    st.header("🧺 Sản lượng")

    with st.form("yield"):

        amt=st.number_input("Gram",min_value=0)

        if st.form_submit_button("Lưu") and amt>0:

            data["yields"].append({
                "date":str(date.today()),
                "amount":amt
            })

            save_data(data)

            st.rerun()

    if data["yields"]:

        df=pd.DataFrame(data["yields"])

        df["date"]=pd.to_datetime(df["date"])

        df=df.sort_values("date")

        st.line_chart(df.set_index("date")["amount"])

# ==========================================
# 11. TÀI CHÍNH
# ==========================================
elif menu=="💰 Tài chính":

    st.header("💰 Chi phí")

    with st.form("exp"):

        item=st.text_input("Vật tư")

        price=st.number_input("Số tiền",min_value=0)

        if st.form_submit_button("Lưu") and item and price>0:

            data["expenses"].append({
                "item":item,
                "amount":price
            })

            save_data(data)

            st.rerun()

    if data["expenses"]:

        df=pd.DataFrame(data["expenses"])

        chart=df.groupby("item")["amount"].sum()

        st.bar_chart(chart)

        st.table(df)


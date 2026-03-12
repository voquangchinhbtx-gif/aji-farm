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
    return {"plants":[], "yields":[], "expenses":[], "supplies":[]}
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
        # Lấy thêm mã thời tiết (weather_code)
        url = "https://api.open-meteo.com/v1/forecast?latitude=16.45&longitude=107.56&current=temperature_2m,relative_humidity_2m,weather_code"
        r = requests.get(url, timeout=5).json()
        
        t = int(round(r['current']['temperature_2m']))
        h = int(r['current']['relative_humidity_2m'])
        w_code = r['current']['weather_code'] # Mã trạng thái thời tiết
        
        return t, h, w_code
    except:
        return 28, 75, 0

# ==========================================
# 5. CẢNH BÁO NÔNG NGHIỆP (Thêm kiểm tra mưa)
# ==========================================
def get_alerts(temp, humi, w_code, plants):
    alerts = []

    # Kiểm tra mã mưa (Các mã từ 51 đến 99 là có mưa)
    if w_code >= 51:
        alerts.append("🌧️ **TRỜI ĐANG MƯA:** Kiểm tra thoát nước gốc, tránh để ớt úng rễ!")
        alerts.append("🚨 **NẤM BỆNH:** Sau mưa cần kiểm tra nấm trắng trên lá!")

    if temp > 33:
        alerts.append("🌡️ Nắng nóng mạnh — cần che lưới")
    
    if temp > 30 and humi < 60:
        alerts.append("🚨 Nguy cơ bọ trĩ cao")

    if temp > 28 and humi > 85 and w_code < 51: # Độ ẩm cao mà không mưa
        alerts.append("🚨 Nguy cơ nấm bệnh do độ ẩm cao")

    # (Giữ nguyên phần nhắc bón phân cũ bên dưới...)
    for p in plants:
        try:
            d = datetime.strptime(p["date"], "%Y-%m-%d").date()
            age = (date.today() - d).days
            if age > 0 and age % 15 == 0:
                alerts.append(f"🌿 {p['name']} {age} ngày: bón phân hữu cơ")
        except: pass

    return alerts

# ==========================================
# 6. SIDEBAR
# ==========================================
st.sidebar.title("🌶️ Aji Farm Pro")

st.sidebar.write("Ngày:",date.today().strftime("%d/%m/%Y"))

menu=st.sidebar.selectbox("Menu",[
"📊 Dashboard",
"🌱 Quản lý cây",
"📋 Quy trình & Nhắc nhở",    
"📦 Kho vật tư",
"📷 AI chẩn đoán",
"🧺 Thu hoạch",
"💰 Tài chính"
])

# ==========================================
# 7. DASHBOARD
# ==========================================
if menu == "📊 Dashboard":

    st.header("📊 Trung tâm điều khiển")

    # BƯỚC QUAN TRỌNG: Nhận đủ 3 giá trị (thêm w_code)
    temp, humi, w_code = get_weather()

    c1, c2 = st.columns(2)

    c1.metric("Nhiệt độ", f"{temp}°C")
    c2.metric("Độ ẩm", f"{humi}%")

    # Hiển thị biểu tượng thời tiết dựa trên mã w_code
    if w_code >= 51:
        st.info("🌧️ Hiện tại Kim Long đang có mưa")
    elif w_code == 0:
        st.info("☀️ Trời đang nắng đẹp")
    else:
        st.info("☁️ Trời nhiều mây")

    st.divider()

    total_yield = sum(y["amount"] for y in data["yields"])
    total_cost = sum(e["amount"] for e in data["expenses"])

    c3, c4, c5 = st.columns(3)

    c3.metric("Số cây", len(data["plants"]))
    c4.metric("Tổng thu hoạch", f"{total_yield} g")
    c5.metric("Chi phí", f"{total_cost:,} đ")

    st.subheader("Cảnh báo hôm nay")

    # Gửi thêm w_code vào hàm cảnh báo
    alerts = get_alerts(temp, humi, w_code, data["plants"])

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
# ==========================================
# 12. KHO VẬT TƯ (PHÂN & THUỐC)
# ==========================================
elif menu == "📦 Kho vật tư":
    st.header("📦 Quản lý Phân bón & Thuốc")
    
    with st.form("add_supply"):
        col1, col2 = st.columns(2)
        s_name = col1.text_input("Tên phân/thuốc (Vd: Đạm cá, Nano Bạc...)")
        s_qty = col2.text_input("Số lượng còn lại (Vd: 2 lít, 500g...)")
        s_note = st.text_input("Ghi chú công dụng (Vd: Bón lá, trị nấm...)")
        
        if st.form_submit_button("Lưu vào kho") and s_name:
            data["supplies"].append({
                "name": s_name,
                "qty": s_qty,
                "note": s_note
            })
            save_data(data)
            st.rerun()

    st.divider()
    
    if data.get("supplies"):
        for i, s in enumerate(data["supplies"]):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"🧪 **{s['name']}**")
                c1.caption(f"📝 {s['note']}")
                c2.write(f"🔢 Còn lại: {s['qty']}")
                if c3.button("Xóa", key=f"sup_{i}"):
                    data["supplies"].pop(i)
                    save_data(data)
                    st.rerun()
    else:
        st.info("Chưa có loại phân thuốc nào trong kho.")
# ==========================================
# 13. QUY TRÌNH & NHẮC NHỞ (KẾT NỐI KHO VẬT TƯ)
# ==========================================
elif menu == "📋 Quy trình & Nhắc nhở":
    st.header("📋 Quy trình & Kiểm tra vật tư sẵn có")

    tab_guide, tab_task = st.tabs(["📖 Sổ tay & Kiểm kho", "🔔 Nhắc việc của tôi"])

    with tab_guide:
        st.info("💡 Hệ thống đang tự động đối chiếu Quy trình với Kho vật tư tại Kim Long của bạn.")
        
        # Danh sách quy trình chuẩn
        standard_guides = [
            {"Giai đoạn": "🌱 Cây con (1-30 ngày)", "Phân cần dùng": "Dịch chuối", "Lưu ý": "Kích rễ loãng"},
            {"Giai đoạn": "🌿 Phát triển (30-60 ngày)", "Phân cần dùng": "Đạm cá", "Lưu ý": "Xanh lá, vươn cành"},
            {"Giai đoạn": "🌼 Ra hoa (60-90 ngày)", "Phân cần dùng": "Trứng sữa", "Lưu ý": "Chống rụng bông"},
            {"Giai đoạn": "🌶️ Nuôi trái (>90 ngày)", "Phân cần dùng": "Kali", "Lưu ý": "Trái bóng, cay nồng"},
            {"Giai đoạn": "🛡️ Phòng bệnh", "Phân cần dùng": "Nano Bạc", "Lưu ý": "Sử dụng sau mưa dầm"}
        ]

        # Lấy danh sách tên vật tư hiện có trong kho (viết thường để so sánh cho chuẩn)
        supplies_in_stock = []
        if data.get("supplies"):
            supplies_in_stock = [s['name'].lower() for s in data["supplies"]]

        # Hiển thị bảng quy trình kèm trạng thái tồn kho
        final_display = []
        for g in standard_guides:
            # Kiểm tra xem loại phân trong quy trình có khớp với vật tư nào trong kho không
            is_in_stock = any(g["Phân cần dùng"].lower() in s for s in supplies_in_stock)
            status = "✅ Sẵn có" if is_in_stock else "❌ Hết hàng"
            final_display.append({
                "Giai đoạn": g["Giai đoạn"],
                "Loại phân": g["Phân cần dùng"],
                "Trạng thái kho": status,
                "Hướng dẫn": g["Lưu ý"]
            })

        st.table(final_display)

        # Cảnh báo nhanh nếu thiếu vật tư quan trọng sau mưa
        temp, humi, w_code = get_weather()
        if w_code >= 51 and not any("nano" in s for s in supplies_in_stock):
            st.error("🚨 **CẢNH BÁO:** Trời đang mưa nhưng trong Kho không tìm thấy **Nano Bạc**. Bạn nên bổ sung sớm để trị nấm!")

    with tab_task:
        st.subheader("🔔 Gợi ý bón phân từ vật tư trong kho")
        if data["plants"]:
            for p in data["plants"]:
                d_p = datetime.strptime(p["date"], "%Y-%m-%d").date()
                age = (date.today() - d_p).days
                
                # Tìm loại phân tương ứng với số tuổi cây
                target_stage = standard_guides[min(age//30, 3)]
                target_fertilizer = target_stage["Phân cần dùng"]
                
                if age % 15 == 0:
                    if any(target_fertilizer.lower() in s for s in supplies_in_stock):
                        st.success(f"✅ **{p['name']}** ({age} ngày): Hãy lấy **{target_fertilizer}** trong kho ra bón.")
                    else:
                        st.warning(f"⚠️ **{p['name']}** ({age} ngày): Cần bón **{target_fertilizer}** nhưng trong kho đã hết!")

        st.divider()
        # Phần nhắc nhở thủ công giữ nguyên như cũ...
        st.write("(Sử dụng form bên dưới để ghi chú thêm các việc khác)")







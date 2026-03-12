import streamlit as st
import os
import json
from datetime import date
import re
import pandas as pd
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from streamlit_js_eval import get_geolocation

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
# 4. WEATHER HUẾ - PHIÊN BẢN CHỐNG CRASH
# ==========================================
import streamlit as st
import requests
from streamlit_js_eval import get_geolocation
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="Aji Charapita Farm", layout="wide")
API_KEY = "66ad043d6024749fa4bf92f0a6782397"


# --- HÀM LẤY THỜI TIẾT ---
def get_weather_data():

    data = {
        "temp": 25,
        "humi": 80,
        "desc": "Đang cập nhật...",
        "city": "Vườn Kim Long",
        "icon": "🌡️"
    }

    try:
        loc = get_geolocation()

        if loc and "coords" in loc:

            lat = loc["coords"].get("latitude")
            lon = loc["coords"].get("longitude")

            if lat and lon:

                url = (
                    f"https://api.openweathermap.org/data/2.5/weather?"
                    f"lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=vi"
                )

                res = requests.get(url, timeout=5).json()

                if res.get("cod") == 200:

                    data["temp"] = res["main"]["temp"]
                    data["humi"] = res["main"]["humidity"]

                    raw_desc = res["weather"][0]["description"].capitalize()
                    data["city"] = res.get("name", "Vườn Kim Long")

                    desc_l = raw_desc.lower()

                    if "mưa" in desc_l:
                        icon = "🌧️"
                    elif "mây" in desc_l:
                        icon = "☁️"
                    elif "quang" in desc_l or "nắng" in desc_l:
                        icon = "☀️"
                    elif "dông" in desc_l:
                        icon = "⚡"
                    else:
                        icon = "🌡️"

                    data["icon"] = icon
                    data["desc"] = f"{icon} {raw_desc}"

                    st.sidebar.success(f"📍 Vị trí: {data['city']}")

                else:
                    st.sidebar.warning("⚠️ Không lấy được dữ liệu thời tiết.")

        else:
            st.sidebar.info("🔄 Đang chờ quyền truy cập GPS...")

    except Exception:
        st.sidebar.error("⚠️ Lỗi kết nối thời tiết")

    return data


# --- GIAO DIỆN CHÍNH ---
st.title("🌶️ Aji Charapita Farm Management")

weather = get_weather_data()

st.subheader("📊 Trung tâm điều khiển")

c1, c2, c3 = st.columns(3)

# --- Nhiệt độ ---
with c1:

    if weather["temp"] > 32:
        t_delta = "Nóng!"
        delta_color = "inverse"
    else:
        t_delta = "Ổn định"
        delta_color = "normal"

    st.metric("Nhiệt độ", f"{weather['temp']}°C", delta=t_delta, delta_color=delta_color)


# --- Độ ẩm ---
with c2:

    if weather["humi"] > 85:
        h_delta = "Ẩm cao"
    else:
        h_delta = "Bình thường"

    st.metric("Độ ẩm", f"{weather['humi']}%", delta=h_delta)


# --- Thời tiết ---
with c3:

    st.write("**Thời tiết thực tế**")
    st.info(weather["desc"])


st.divider()


# --- PHẦN AI CẢNH BÁO ---
predictions = []   # nơi load dữ liệu AI sau này

reliable_preds = [
    p for p in predictions if p.get("confidence", 0) > 60
] if predictions else []


if reliable_preds:

    st.success("📢 Có cảnh báo quan trọng từ AI!")

    for p in reliable_preds:
        st.write(f"🌿 {p.get('plant','Không rõ')} — {p.get('disease','Không rõ')}")

else:

    st.write("✅ Chưa có cảnh báo bệnh hại nào được ghi nhận.")

# ==========================================
# 5. CẢNH BÁO NÔNG NGHIỆP (Thêm kiểm tra mưa)
# ==========================================
from datetime import datetime, date

def get_alerts(temp, humi, w_code, plants):
    alerts = []

    # Kiểm tra mã mưa (51–99 là mưa)
    if w_code >= 51:
        alerts.append("🌧️ **TRỜI ĐANG MƯA:** Kiểm tra thoát nước gốc, tránh để ớt úng rễ!")
        alerts.append("🚨 **NẤM BỆNH:** Sau mưa cần kiểm tra nấm trắng trên lá!")

    if temp > 33:
        alerts.append("🌡️ Nắng nóng mạnh — cần che lưới")

    if temp > 30 and humi < 60:
        alerts.append("🚨 Nguy cơ bọ trĩ cao")

    if temp > 28 and humi > 85 and w_code < 51:  # Ẩm cao nhưng không mưa
        alerts.append("🚨 Nguy cơ nấm bệnh do độ ẩm cao")

    # Nhắc lịch bón phân theo tuổi cây
    for p in plants:
        try:
            d = datetime.strptime(p["date"], "%Y-%m-%d").date()
            age = (date.today() - d).days

            if age > 0 and age % 15 == 0:
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

    # Hàm lấy thời tiết
    def get_weather():
        lat, lon = 16.46, 107.59
        api_key = "YOUR_OPENWEATHERMAP_API_KEY"

        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
            res = requests.get(url, timeout=5).json()

            if res.get("cod") == 200:
                temp = res["main"]["temp"]
                humi = res["main"]["humidity"]
                w_code = res["weather"][0]["id"]

                return temp, humi, w_code

        except:
            pass

        # fallback
        return 25, 80, 0


    # Lấy dữ liệu thời tiết
    temp, humi, w_code = get_weather()

    c1, c2 = st.columns(2)
    c1.metric("Nhiệt độ", f"{temp}°C")
    c2.metric("Độ ẩm", f"{humi}%")

    # Hiển thị trạng thái thời tiết
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

    alerts = get_alerts(temp, humi, w_code, data["plants"])

    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.success("Vườn đang ổn định")
# ==========================================
# 8. QUẢN LÝ CÂY
# ==========================================
elif menu == "🌱 Quản lý cây":
    st.header("🌱 Danh sách cây")

    # --- 1. Form thêm cây mới ---
    with st.form("add_plant"):
        name = st.text_input("Tên cây / chậu")
        d = st.date_input("Ngày trồng", value=date.today())

        submitted = st.form_submit_button("Thêm cây mới")

        if submitted and name:
            data["plants"].append({
                "name": name,
                "date": str(d)
            })
            save_data(data)
            st.success(f"Đã thêm cây {name}!")
            st.rerun()

    st.divider()

    # --- 2. Hiển thị danh sách cây ---
    if data.get("plants"):
        for i, p in enumerate(data["plants"]):

            # Tính tuổi cây
            d_obj = datetime.strptime(p["date"], "%Y-%m-%d").date()
            age = (date.today() - d_obj).days

            c1, c2 = st.columns([4,1])

            c1.write(f"**{p['name']}** — {age} ngày tuổi")

            if c2.button("Xóa", key=f"del_{i}"):
                data["plants"].pop(i)
                save_data(data)
                st.rerun()

    else:
        st.info("Chưa có cây nào trong danh sách. Hãy thêm cây ở phía trên!")
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
# 10. AI CHẨN ĐOÁN BỆNH (BẢN CẬP NHẬT CUỐI)
# ==========================================
elif menu == "📷 AI chẩn đoán":
    st.header("📸 Chẩn đoán bệnh bằng AI")
    
    img_file = st.camera_input("Chụp ảnh lá hoặc thân cây ớt")
    
    if img_file is not None:
        # 1. Hiển thị ảnh ngay để người dùng yên tâm
        img = Image.open(img_file)
        st.image(img, caption="Ảnh đang phân tích", use_container_width=True)
        
        if st.button("🚀 Bắt đầu phân tích"):
            with st.spinner("Đang gửi ảnh sang hệ thống AI..."):
                try:
                    # 2. Cấu hình Model
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # 3. Phân tích trực tiếp bằng đối tượng Image của PIL
                    prompt = """
                    Bạn là chuyên gia nông nghiệp cho giống ớt Aji Charapita. 
                    Nhìn vào ảnh này, hãy chẩn đoán tình trạng sức khỏe của cây:
                    1. Tên bệnh hoặc loại sâu/nấm (nếu có).
                    2. Cách xử lý hữu cơ (dùng Nano bạc, Neem oil, hoặc cách tự nhiên).
                    Nếu ảnh không rõ, hãy yêu cầu người dùng chụp lại gần lá hơn.
                    """
                    
                    # Gửi ảnh đi (Gemini 1.5 Flash hỗ trợ gửi thẳng đối tượng PIL Image)
                    response = model.generate_content([prompt, img])
                    
                    st.success("🤖 AI Phản hồi:")
                    st.markdown(response.text)
                    
                except Exception as e:
                    # Hiển thị lỗi chi tiết để mình biết đường sửa
                    st.error("❌ Lỗi phân tích!")
                    with st.expander("Chi tiết lỗi cho kỹ thuật"):
                        st.code(str(e))
                    st.info("Hãy thử kiểm tra lại API Key trong mục Secrets của Streamlit nhé.")

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
# 13. DỰ BÁO DỊCH TỄ HỌC NÔNG NGHIỆP
# ==========================================
import streamlit as st
import requests
import pandas as pd  # ✅ Giải quyết thiếu import
from streamlit_js_eval import get_geolocation

# --- CẤU HÌNH BAN ĐẦU ---
API_KEY_WEATHER = "66ad043d6024749fa4bf92f0a6782397"

# Giả lập hoặc khởi tạo biến data để tránh NameError ✅
if 'data' not in locals():
    data = {"disease_map": []} 

if menu == "📋 Quy trình & Nhắc nhở":
    st.header("🔮 Hệ thống Dự báo & Phân tích Dịch tễ")

    # 1. GPS & THỜI TIẾT (Xử lý an toàn)
    loc = get_geolocation(key='gps_risk_analysis') # ✅ Dùng key duy nhất
    
    # Giá trị mặc định
    temp, humidity, desc, city = 25, 80, "Không có dữ liệu", "Vị trí hiện tại"

    if loc and "coords" in loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=metric&lang=vi"
            res = requests.get(url, timeout=5) # ✅ Kiểm tra lỗi mạng
            res.raise_for_status() 
            w_data = res.json()
            
            if w_data.get("cod") == 200:
                temp = w_data['main']['temp']
                humidity = w_data['main']['humidity']
                desc = w_data['weather'][0]['description']
                city = w_data.get("name", "Kim Long")
        except Exception as e:
            st.sidebar.error(f"⚠️ Không thể cập nhật thời tiết: {e}")

    # 2. RISK SCORE THÔNG MINH
    risk_score = 0
    if humidity > 90: risk_score += 2
    elif humidity > 80: risk_score += 1
    if "mưa" in desc.lower(): risk_score += 1
    if temp > 34: risk_score += 1

    # 3. DASHBOARD TỔNG QUAN
    st.subheader(f"📊 Dashboard Vườn: {city}")
    m1, m2, m3 = st.columns(3)
    
    # Hiển thị màu sắc theo mức độ nguy cơ ✅
    risk_color = "normal" 
    if risk_score >= 3: risk_color = "inverse"
    
    m1.metric("Chỉ số nguy cơ", f"{risk_score}/4", delta="NGUY HIỂM" if risk_score >= 3 else "AN TOÀN", delta_color=risk_color)
    m2.metric("Nhiệt độ", f"{temp}°C")
    m3.metric("Độ ẩm", f"{humidity}%")
    
    # Cảnh báo trực quan
    if risk_score >= 3:
        st.error("🚨 **CẢNH BÁO:** Điều kiện cực kỳ thuận lợi cho nấm bệnh (Thán thư, Phấn trắng). Cần phun phòng ngay!")
    elif risk_score == 2:
        st.warning("⚠️ **CHÚ Ý:** Độ ẩm cao. Hãy tăng cường thông thoáng cho vườn ớt.")
    else:
        st.success("✅ **AN TOÀN:** Thời tiết đang ủng hộ vườn ớt Aji Charapita của bạn.")

    # 4. PHÂN TÍCH DỮ LIỆU LỊCH SỬ ✅
    st.divider()
    if data.get("disease_map"):
        df_map = pd.DataFrame(data["disease_map"])
        df_map["date"] = pd.to_datetime(df_map["date"])
        
        tab1, tab2, tab3 = st.tabs(["🗺️ Bản đồ ổ bệnh", "📈 Diễn biến dịch", "📊 Thống kê cây"])
        
        with tab1:
            # Kiểm tra dữ liệu Map trước khi hiển thị ✅
            if not df_map[['lat', 'lon']].dropna().empty:
                st.map(df_map.dropna(subset=["lat", "lon"])[["lat", "lon"]])
            else:
                st.info("Chưa có tọa độ GPS cho các ổ bệnh ghi nhận.")
        
        with tab2:
            st.write("📅 **Số ca bệnh theo ngày**")
            cases_by_day = df_map.groupby(df_map["date"].dt.date).size()
            st.line_chart(cases_by_day)
        
        with tab3:
            c1, c2 = st.columns(2)
            c1.write("🔥 **Loại bệnh**")
            c1.bar_chart(df_map["disease"].value_counts())
            c2.write("🌱 **Cây bị nhiễm**")
            c2.bar_chart(df_map["plant"].value_counts())
    else:
        st.info("ℹ️ Hệ thống chưa ghi nhận lịch sử dịch tễ. Các biểu đồ sẽ xuất hiện khi có dữ liệu bệnh hại.")

# ==========================================
# 14. AI CHẨN ĐOÁN (ROBUST VISION AI)
# ==========================================
elif menu == "📷 AI Chẩn đoán bệnh":

    st.header("🔬 AI Chẩn đoán & Ghi nhận Thực địa")

    loc_ai = get_geolocation()
    lat_ai, lon_ai = (loc_ai['coords']['latitude'], loc_ai['coords']['longitude']) if loc_ai else (0, 0)

    img_file = st.camera_input("📸 Chụp ảnh bộ phận nghi ngờ bệnh")

    if img_file:

        image = Image.open(img_file)
        st.image(image, caption="Ảnh hiện trường", use_column_width=True)

        with st.spinner("🤖 AI đang phân tích đa tầng..."):

            predictions = []
            reliable_preds = []

            try:
                model = genai.GenerativeModel("gemini-1.5-flash")

                prompt = """
Trả về DUY NHẤT JSON list 3 bệnh khả năng cao nhất cho cây trồng trong ảnh:

[
 {"plant":"Tên cây","disease":"Tên bệnh","confidence":80,"organic_guide":"Hướng dẫn hữu cơ","source":"FAO/CABI"}
]

Chỉ dùng giải pháp sinh học/hữu cơ.
"""

                response = model.generate_content([prompt, image])

                # Tách JSON an toàn
                match = re.search(r'\[.*\]', response.text, re.DOTALL)

                if match:
                    predictions = json.loads(match.group())

            except Exception as e:
                st.error("AI phân tích thất bại")

        # Lọc kết quả đáng tin cậy
        reliable_preds = [p for p in predictions if p.get("confidence", 0) > 60]

        if reliable_preds:

            st.success("✅ Tìm thấy bệnh có độ tin cậy cao")

            top = reliable_preds[0]

            st.write(f"🌿 Cây: {top.get('plant','Không rõ')}")
            st.write(f"🦠 Bệnh: {top.get('disease','Không rõ')}")
            st.write(f"📊 Độ tin cậy: {top.get('confidence',0)}%")
            st.write(f"🌱 Giải pháp hữu cơ: {top.get('organic_guide','')}")

            new_case = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "plant": top.get("plant", "Không rõ"),
                "disease": top.get("disease", "Bệnh lạ"),
                "lat": lat_ai,
                "lon": lon_ai
            }

            data["disease_map"].append(new_case)
            save_data(data)

        else:
            st.warning("⚠️ Không có dự đoán đủ tin cậy.")















































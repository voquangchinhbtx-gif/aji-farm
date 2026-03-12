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
from streamlit_js_eval import get_geolocation

# 1. Khởi tạo giá trị dự phòng (Default) để App không bao giờ thiếu biến
temp, humidity, description, city_name = 25, 80, "không rõ", "Vườn Kim Long"

# 2. Lấy tọa độ GPS
loc = get_geolocation()

# 3. Kiểm tra đa tầng: loc tồn tại -> có key 'coords' -> có dữ liệu bên trong
if loc and isinstance(loc, dict) and 'coords' in loc:
    try:
        lat = loc['coords'].get('latitude')
        lon = loc['coords'].get('longitude')
        
        if lat and lon:
# 4. Gọi API thời tiết (Có thêm timeout để tránh treo App)
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=vi"
            response = requests.get(weather_url, timeout=5)
            weather_data = response.json()
            
# Kiểm tra xem API trả về kết quả thành công không (status code 200)
        if weather_data.get("cod") == 200:
                city_name = weather_data.get("name", city_name)
                temp = weather_data['main']['temp']
                humidity = weather_data['main']['humidity']
                description = weather_data['weather'][0]['description']
                st.sidebar.success(f"📍 Đang theo dõi tại: {city_name}")
    except Exception as e:
               st.sidebar.warning("Không thể lấy vị trí GPS, đang dùng vị trí mặc định.")
               temp, humi, w_code = 25, 80, "Mây rải rác"
    else:
                st.sidebar.error("⚠️ Không tìm thấy dữ liệu thời tiết cho tọa độ này.")
    except Exception as e:
# Nếu có bất kỳ lỗi phát sinh nào, App vẫn chạy tiếp với giá trị mặc định
                st.sidebar.info("🔄 Đang cập nhật tọa độ...")
    else:
                st.sidebar.warning("📡 Đang đợi tín hiệu GPS hoặc quyền truy cập vị trí...")

# Sau đoạn này, các biến temp, humidity luôn tồn tại, không lo lỗi ở các mục sau.

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
def get_weather():
    """
    Hàm lấy dữ liệu thời tiết dự phòng hoặc từ GPS.
    Trả về: nhiệt độ, độ ẩm, và mã trạng thái (hoặc mô tả).
    """
# Bạn có thể dùng tọa độ mặc định của Kim Long, Huế
    lat, lon = 16.46, 107.59 
    api_key = "YOUR_OPENWEATHERMAP_API_KEY" # Đảm bảo đã thay key thật
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
        res = requests.get(url, timeout=5).json()
        
if res.get("cod") == 200:
            t = res['main']['temp']
            h = res['main']['humidity']
            w = res['weather'][0]['description']
            return t, h, w
    except:
        pass
    
# Trả về giá trị mặc định nếu API lỗi để App không sập
    return 25, 80, "không rõ"
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
elif menu == "🌱 Quản lý cây":
    st.header("🌱 Danh sách cây")

# --- 1. Form thêm cây mới ---
    with st.form("add_plant"):
        name = st.text_input("Tên cây / chậu")
# Đảm bảo đầu file có: from datetime import date
        d = st.date_input("Ngày trồng", value=date.today())
        
# PHẢI có nút Submit button bên trong Form
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

# --- 2. Hiển thị danh sách cây hiện có ---
# Kiểm tra nếu có dữ liệu plants
if data.get("plants"):
        for i, p in enumerate(data["plants"]):
# Ép kiểu datetime để tính số ngày tuổi
            d_obj = datetime.strptime(p["date"], "%Y-%m-%d").date()
            age = (date.today() - d_obj).days
            
            c1, c2 = st.columns([4, 1])
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
if menu == "📋 Quy trình & Nhắc nhở":
    st.header("🔮 Hệ thống Dự báo & Phân tích Dịch tễ")

    # GPS & THỜI TIẾT CACHED
    loc = get_geolocation()
    lat, lon = (loc['coords']['latitude'], loc['coords']['longitude']) if loc else (16.46, 107.59)
    
    try:
        w_res = get_weather(lat, lon, API_KEY_WEATHER)
        temp, humidity, desc = w_res['main']['temp'], w_res['main']['humidity'], w_res['weather'][0]['description']
        city = w_res.get("name", "Kim Long")
    except:
        temp, humidity, desc, city = 25, 80, "Không có dữ liệu", "Vị trí hiện tại"

    # RISK SCORE THÔNG MINH
    risk_score = 0
    if humidity > 90: risk_score += 2
    elif humidity > 80: risk_score += 1
    if "mưa" in desc.lower(): risk_score += 1
    if temp > 34: risk_score += 1

    # DASHBOARD TỔNG QUAN
    st.subheader(f"📊 Dashboard Vườn: {city}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Chỉ số nguy cơ", f"{risk_score}/4")
    m2.metric("Nhiệt độ", f"{temp}°C")
    m3.metric("Độ ẩm", f"{humidity}%")
    
    # CẢNH BÁO MẠNH THEO RISK SCORE
    if risk_score >= 3:
        st.error("🚨 **Nguy cơ bùng phát dịch bệnh cao** – Cần kiểm tra vườn ngay lập tức.")
    elif risk_score == 2:
        st.warning("⚠️ **Điều kiện thuận lợi** cho bệnh phát sinh. Hãy phun phòng hữu cơ.")
    else:
        st.success("✅ **Điều kiện ổn định.** Tiếp tục duy trì chế độ chăm sóc.")

    # PHÂN TÍCH DỮ LIỆU LỊCH SỬ (HEATMAP & TIME-SERIES)
    if data["disease_map"]:
        df_map = pd.DataFrame(data["disease_map"])
        df_map["date"] = pd.to_datetime(df_map["date"])
        
        st.divider()
        tab1, tab2, tab3 = st.tabs(["🗺️ Bản đồ ổ bệnh", "📈 Diễn biến dịch", "📊 Thống kê cây"])
        
        with tab1:
            # Chuẩn hóa dữ liệu map
            clean_map = df_map.dropna(subset=["lat", "lon"])
            st.map(clean_map[["lat", "lon"]])
        
        with tab2:
            st.write("📅 **Số ca bệnh theo ngày**")
            cases_by_day = df_map.groupby(df_map["date"].dt.date).size()
            st.line_chart(cases_by_day)
        
        with tab3:
            c1, c2 = st.columns(2)
            c1.write("🔥 **Bệnh phổ biến**")
            c1.bar_chart(df_map["disease"].value_counts())
            c2.write("🌱 **Cây bị nhiễm**")
            c2.bar_chart(df_map["plant"].value_counts())

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
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt = """Trả về DUY NHẤT JSON list 3 bệnh khả năng cao nhất cho cây trồng trong ảnh:
                [{"plant":"Tên cây","disease":"Tên bệnh","confidence":80,"organic_guide":"Hướng dẫn hữu cơ","source":"FAO/CABI"}]
                Chỉ dùng giải pháp sinh học/hữu cơ."""
                response = model.generate_content([prompt, image])
                
                # Regex & Try-Except an toàn tuyệt đối
                try:
                    match = re.search(r'\[.*\]', response.text, re.DOTALL)
                    predictions = json.loads(match.group()) if match else []
                except: predictions = []
            except: predictions = []

        if predictions:
            # Lọc Confidence an toàn với .get()
            reliable_preds = [p for p in predictions if p.get("confidence", 0) > 60]
            
if reliable_preds:
    # Dòng 463: Phải thụt vào 4 khoảng trắng so với 'if'
    top = reliable_preds[0]
    
    # Các dòng này cũng phải thụt vào ĐÚNG bằng dòng 'top'
    new_case = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "plant": top.get("plant", "Không rõ"),
        "disease": top.get("disease", "Bệnh lạ"),
        "lat": lat_ai, "lon": lon_ai
    }
    data["disease_map"].append(new_case)
    save_data(data)



































import json
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
# 13. QUY TRÌNH & TỐI ƯU HÓA (BẢN BIẾT NÓI)
# ==========================================
elif menu == "📋 Quy trình & Nhắc nhở":
    st.header("📋 Quy trình & Tối ưu hóa phân bón")

    tab_guide, tab_task = st.tabs(["📖 Sổ tay & Nhật ký", "🔔 Nhắc việc của tôi"])

    with tab_guide:
        st.info("💡 Hệ thống tổng hợp kinh nghiệm từ cộng đồng để đưa ra loại phân bón hiệu quả nhất.")
        
        # 1. Thu thập dữ liệu từ kho cộng đồng
        all_supplies = data.get("supplies", [])
        all_names = [s['name'] for s in all_supplies]

        # 2. Danh mục quy trình - Nơi chứa "Kiến thức thực tế"
        standard_guides = [
            {
                "Giai đoạn": "🌱 Cây con (1-30 ngày)",
                "Từ khóa": ["rễ", "chuối", "humic"],
                "HD": "Pha 5ml/1L nước. Tưới gốc lúc 6h-7h sáng để kích rễ mạnh.",
                "Mặc định": "Dịch chuối"
            },
            {
                "Giai đoạn": "🌿 Phát triển (30-60 ngày)",
                "Từ khóa": ["đạm", "lá", "cá", "tăng trưởng"],
                "HD": "Pha 1:200. Phun mặt dưới lá định kỳ 10 ngày để vươn cành.",
                "Mặc định": "Đạm cá"
            },
            {
                "Giai đoạn": "🌼 Ra hoa (60-90 ngày)",
                "Từ khóa": ["hoa", "bông", "trứng", "sữa", "canxi"],
                "HD": "Phun trực tiếp vào chùm hoa lúc chưa nở. Giúp chống rụng bông.",
                "Mặc định": "Dịch Trứng Sữa"
            },
            {
                "Giai đoạn": "🛡️ Phòng bệnh",
                "Từ khóa": ["nấm", "khuẩn", "nano", "bạc", "trĩ"],
                "HD": "Xịt ngay sau mưa dầm. Ngăn ngừa nấm thán thư Kim Long.",
                "Mặc định": "Nano Bạc"
            }
        ]

        # 3. Logic Phân tích & Hiển thị
        refined_data = []
        for g in standard_guides:
            # Tìm loại phân phổ biến nhất dựa trên dữ liệu cộng đồng (all_names)
            matching_items = [n for n in all_names if any(k in n.lower() for k in g["Từ khóa"])]
            
            # Loại phân hiệu quả nhất dựa trên số đông người dùng
            most_common = max(set(matching_items), key=matching_items.count) if matching_items else g["Mặc định"]
            
            # Kiểm tra trạng thái kho cá nhân của bạn
            my_stock = "✅ Đã có" if matching_items else "❌ Cần mua"

            refined_data.append({
                "Giai đoạn": g["Giai đoạn"],
                "Hướng dẫn kỹ thuật (Cụ thể)": g["HD"],
                "Loại phân tối ưu (Số đông tin dùng)": most_common,
                "Trạng thái kho": my_stock
            })

        # Hiển thị bảng phân tích
        st.table(refined_data)

        # 4. Phần thực hiện bón (Nhật ký)
        st.divider()
        st.subheader("🚀 Xác nhận bón phân / Phun thuốc")
        if all_supplies:
            with st.form("action_v4"):
                c1, c2 = st.columns(2)
                p_choice = c1.selectbox("Bón cho cây", ["Tất cả vườn"] + [p['name'] for p in data.get('plants', [])])
                s_choice = c2.selectbox("Loại phân thực tế sử dụng", all_names)
                if st.form_submit_button("Ghi nhận thực hiện"):
                    if "care_history" not in data: data["care_history"] = []
                    data["care_history"].append({"plant": p_choice, "supply": s_choice, "date": str(date.today())})
                    save_data(data)
                    st.success(f"Đã lưu: {p_choice} bón {s_choice}")
                    st.rerun()













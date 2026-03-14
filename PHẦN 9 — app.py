# ==========================================
# AJI FARM AI - MAIN APPLICATION
# ==========================================

import streamlit as st
from streamlit_js_eval import get_geolocation

from config import APP_NAME
from database import load_data
from dashboard import show_dashboard
from garden_manager import show_garden_manager
from gemini_ai import load_gemini, diagnose_plant
from npk_ai import recommend_npk

from PIL import Image


# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌶",
    layout="wide"
)


# ==========================================
# LOAD DATABASE
# ==========================================

data = load_data()


# ==========================================
# SIDEBAR MENU
# ==========================================

st.sidebar.title("🌶 Aji Farm AI")

menu = st.sidebar.radio(

    "Chọn chức năng",

    [

        "🏠 Tổng quan",
        "🌱 Quản lý vườn",
        "🦠 AI chẩn đoán bệnh",
        "🌿 Tư vấn phân bón"

    ]

)


# ==========================================
# GET LOCATION
# ==========================================

geo = get_geolocation()

if geo and "coords" in geo:

    lat = geo["coords"]["latitude"]

    lon = geo["coords"]["longitude"]

else:

    lat = 16.47
    lon = 107.58


# ==========================================
# MENU: DASHBOARD
# ==========================================

if menu == "🏠 Tổng quan":

    show_dashboard(data, lat, lon)


# ==========================================
# MENU: GARDEN MANAGER
# ==========================================

elif menu == "🌱 Quản lý vườn":

    show_garden_manager(data)


# ==========================================
# MENU: AI DIAGNOSIS
# ==========================================

elif menu == "🦠 AI chẩn đoán bệnh":

    st.title("🦠 AI Bác sĩ cây trồng")

    api_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    if api_key:

        model = load_gemini(api_key)

        crop = st.text_input(
            "Tên cây"
        )

        image = st.file_uploader(
            "Tải ảnh lá cây",
            type=["jpg", "png"]
        )

        if image and crop:

            img = Image.open(image)

            st.image(img, width=300)

            if st.button("🔍 Phân tích"):

                with st.spinner("AI đang phân tích..."):

                    result = diagnose_plant(

                        model,
                        img,
                        crop,
                        {
                            "temp": 30,
                            "humidity": 75
                        }

                    )

                    st.markdown(result)


# ==========================================
# MENU: NPK ADVISOR
# ==========================================

elif menu == "🌿 Tư vấn phân bón":

    st.title("🌿 AI tư vấn phân bón")

    crop = st.text_input("Tên cây")

    stage = st.selectbox(

        "Giai đoạn",

        [

            "Cây con",
            "Sinh trưởng",
            "Ra hoa",
            "Đậu trái"

        ]

    )

    if st.button("📊 Phân tích"):

        result = recommend_npk(

            crop,
            stage

        )

        st.success(result)

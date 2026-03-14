# ==========================================
# AJI FARM AI - GARDEN MANAGER
# ==========================================

import streamlit as st
import pandas as pd
from datetime import datetime, date

from database import (
    add_plant,
    get_plants,
    delete_plant,
    save_data
)

from crop_database import (
    get_crop_list,
    get_crop_name,
    get_crop_water_need
)


# ==========================================
# CALCULATE PLANT AGE
# ==========================================

def calculate_age(plant_date):

    try:

        d = datetime.strptime(plant_date, "%Y-%m-%d").date()

        today = date.today()

        age = (today - d).days

        return age

    except:

        return 0


# ==========================================
# ADD PLANT FORM
# ==========================================

def add_plant_form(data):

    st.subheader("🌱 Thêm cây mới")

    crops = get_crop_list()

    crop_names = [c["name"] for c in crops]

    crop_select = st.selectbox(
        "Chọn loại cây",
        crop_names
    )

    plant_date = st.date_input(
        "Ngày trồng",
        value=date.today()
    )

    note = st.text_input(
        "Ghi chú"
    )

    if st.button("➕ Thêm cây"):

        crop_id = None

        for c in crops:

            if c["name"] == crop_select:

                crop_id = c["id"]

        plant = {

            "crop": crop_id,

            "date": plant_date.strftime("%Y-%m-%d"),

            "note": note

        }

        add_plant(data, plant)

        save_data(data)

        st.success("Đã thêm cây.")


# ==========================================
# PLANT LIST
# ==========================================

def plant_list(data):

    plants = get_plants(data)

    if not plants:

        st.info("Chưa có cây.")

        return

    rows = []

    for i, p in enumerate(plants):

        crop_name = get_crop_name(p["crop"])

        age = calculate_age(p["date"])

        water = get_crop_water_need(p["crop"])

        rows.append({

            "ID": i,

            "Tên cây": crop_name,

            "Ngày trồng": p["date"],

            "Tuổi (ngày)": age,

            "Nhu cầu nước": water,

            "Ghi chú": p.get("note", "")
        })

    df = pd.DataFrame(rows)

    st.subheader("📋 Danh sách cây")

    st.dataframe(df, use_container_width=True)


# ==========================================
# DELETE PLANT
# ==========================================

def delete_plant_panel(data):

    plants = get_plants(data)

    if not plants:

        return

    st.subheader("🗑 Xóa cây")

    options = []

    for i, p in enumerate(plants):

        name = get_crop_name(p["crop"])

        options.append(f"{i} - {name}")

    selected = st.selectbox(
        "Chọn cây cần xóa",
        options
    )

    if st.button("❌ Xóa"):

        plant_id = int(selected.split(" - ")[0])

        delete_plant(data, plant_id)

        save_data(data)

        st.success("Đã xóa cây.")


# ==========================================
# CARE ADVICE
# ==========================================

def care_advice(data):

    plants = get_plants(data)

    if not plants:

        return

    st.subheader("🌿 Gợi ý chăm sóc")

    for p in plants:

        name = get_crop_name(p["crop"])

        age = calculate_age(p["date"])

        water = get_crop_water_need(p["crop"])

        st.markdown(f"""
**{name}**

- Tuổi: {age} ngày
- Nhu cầu nước: {water}
""")

        if age < 7:

            st.info("Cây còn non, cần tưới nhẹ mỗi ngày.")

        elif age < 30:

            st.info("Giai đoạn sinh trưởng mạnh, cần bổ sung phân.")

        else:

            st.info("Chuẩn bị giai đoạn ra hoa hoặc thu hoạch.")


# ==========================================
# MAIN UI
# ==========================================

def show_garden_manager(data):

    st.title("🌱 Quản lý vườn")

    tab1, tab2, tab3 = st.tabs([
        "Thêm cây",
        "Danh sách",
        "Chăm sóc"
    ])

    with tab1:

        add_plant_form(data)

    with tab2:

        plant_list(data)

        delete_plant_panel(data)

    with tab3:

        care_advice(data)

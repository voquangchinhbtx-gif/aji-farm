# ==========================================
# AJI FARM AI - DASHBOARD UI
# ==========================================

import streamlit as st
import pandas as pd
from datetime import datetime

from database import get_plants
from weather_system import (
    fetch_weather,
    calculate_disease_risk,
    get_weather_warnings,
    farm_environment_analysis
)

from crop_database import get_crop_name


# ==========================================
# DASHBOARD HEADER
# ==========================================

def dashboard_header(lat, lon):

    st.title("🌶 Aji Farm AI")

    st.markdown(
        f"📍 Vị trí vườn: `{lat} , {lon}`"
    )

    st.caption(
        f"Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}"
    )


# ==========================================
# WEATHER METRICS
# ==========================================

def weather_metrics(weather):

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🌡 Nhiệt độ",
        f"{weather['temp']}°C"
    )

    col2.metric(
        "💧 Độ ẩm",
        f"{weather['humidity']}%"
    )

    col3.metric(
        "🌬 Gió",
        f"{weather['wind']} m/s"
    )

    risk, level = calculate_disease_risk(
        weather["temp"],
        weather["humidity"]
    )

    col4.metric(
        "🦠 Nguy cơ bệnh",
        f"{risk}% ({level})"
    )


# ==========================================
# WEATHER WARNINGS
# ==========================================

def weather_warning_panel(weather):

    warnings = get_weather_warnings(weather)

    if warnings:

        st.subheader("⚠ Cảnh báo thời tiết")

        for w in warnings:

            st.warning(w)


# ==========================================
# FARM ANALYSIS PANEL
# ==========================================

def environment_analysis_panel(weather):

    analysis = farm_environment_analysis(weather)

    if analysis:

        st.subheader("🔎 Phân tích môi trường")

        for a in analysis:

            st.info(a)


# ==========================================
# FARM STATISTICS
# ==========================================

def farm_statistics(data):

    plants = get_plants(data)

    st.subheader("🌱 Thống kê vườn")

    total = len(plants)

    st.metric("Tổng số cây", total)

    if total == 0:

        st.info("Chưa có cây trong hệ thống.")

        return

    crop_names = []

    for p in plants:

        crop_names.append(
            get_crop_name(p["crop"])
        )

    df = pd.DataFrame({
        "Crop": crop_names
    })

    counts = df["Crop"].value_counts()

    st.bar_chart(counts)


# ==========================================
# FARM LIST TABLE
# ==========================================

def farm_table(data):

    plants = get_plants(data)

    if not plants:

        return

    rows = []

    for p in plants:

        rows.append({

            "Tên cây": get_crop_name(p["crop"]),

            "Ngày trồng": p["date"]
        })

    df = pd.DataFrame(rows)

    st.subheader("📋 Danh sách cây")

    st.dataframe(df, use_container_width=True)


# ==========================================
# DAILY TASK PANEL
# ==========================================

def daily_tasks(weather):

    st.subheader("📅 Công việc hôm nay")

    temp = weather["temp"]

    humidity = weather["humidity"]

    st.checkbox(
        "💧 Tưới nước",
        value=temp > 25
    )

    st.checkbox(
        "🌿 Bón phân lá",
        value=temp < 30
    )

    st.checkbox(
        "🦠 Kiểm tra sâu bệnh",
        value=humidity > 70
    )

    st.checkbox(
        "🧹 Dọn cỏ quanh gốc"
    )


# ==========================================
# MAIN DASHBOARD FUNCTION
# ==========================================

def show_dashboard(data, lat, lon):

    dashboard_header(lat, lon)

    weather = fetch_weather(lat, lon)

    st.divider()

    weather_metrics(weather)

    st.divider()

    weather_warning_panel(weather)

    environment_analysis_panel(weather)

    st.divider()

    farm_statistics(data)

    farm_table(data)

    st.divider()

    daily_tasks(weather)

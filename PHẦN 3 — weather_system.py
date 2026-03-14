# ==========================================
# AJI FARM AI - WEATHER + GPS SYSTEM
# ==========================================

import requests
from datetime import datetime

from config import (
    OPENWEATHER_API_KEY,
    DEFAULT_LAT,
    DEFAULT_LON,
    TEMP_WARNING,
    HUMIDITY_WARNING,
    HOT_TEMP,
    WATER_INCREASE_RATIO
)

# ==========================================
# GET WEATHER FROM API
# ==========================================

def fetch_weather(lat, lon):

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    )

    try:

        r = requests.get(url, timeout=5)

        data = r.json()

        weather = {

            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "time": datetime.now().strftime("%H:%M %d/%m/%Y")
        }

        return weather

    except:

        return {

            "temp": 28,
            "humidity": 70,
            "wind": 2,
            "condition": "Unknown",
            "description": "offline",
            "time": datetime.now().strftime("%H:%M %d/%m/%Y")
        }


# ==========================================
# DEFAULT WEATHER (KHI KHÔNG CÓ GPS)
# ==========================================

def get_default_weather():

    return fetch_weather(DEFAULT_LAT, DEFAULT_LON)


# ==========================================
# DISEASE RISK CALCULATION
# ==========================================

def calculate_disease_risk(temp, humidity):

    risk = humidity * 0.6 + temp * 0.3

    if risk > 100:
        risk = 100

    if risk < 30:
        level = "Thấp"

    elif risk < 60:
        level = "Trung bình"

    elif risk < 80:
        level = "Cao"

    else:
        level = "Rất cao"

    return int(risk), level


# ==========================================
# WEATHER WARNINGS
# ==========================================

def get_weather_warnings(weather):

    warnings = []

    temp = weather["temp"]
    humidity = weather["humidity"]

    if temp > TEMP_WARNING:

        warnings.append(
            "Nhiệt độ quá cao, cây dễ mất nước."
        )

    if humidity > HUMIDITY_WARNING:

        warnings.append(
            "Độ ẩm cao, nguy cơ nấm bệnh."
        )

    if weather["wind"] > 10:

        warnings.append(
            "Gió mạnh, nên kiểm tra giàn cây."
        )

    return warnings


# ==========================================
# IRRIGATION ESTIMATION
# ==========================================

def estimate_water_need(base_water, temp):

    water = base_water

    if temp > HOT_TEMP:

        water = base_water * WATER_INCREASE_RATIO

    return int(water)


# ==========================================
# WEATHER SUMMARY
# ==========================================

def generate_weather_summary(weather):

    temp = weather["temp"]
    humidity = weather["humidity"]

    summary = f"""
Nhiệt độ: {temp}°C
Độ ẩm: {humidity}%
Gió: {weather['wind']} m/s
Thời tiết: {weather['description']}
"""

    return summary


# ==========================================
# DAILY FARM ANALYSIS
# ==========================================

def farm_environment_analysis(weather):

    temp = weather["temp"]
    humidity = weather["humidity"]

    analysis = []

    if temp < 15:

        analysis.append(
            "Trời lạnh, cây sinh trưởng chậm."
        )

    if 20 <= temp <= 30:

        analysis.append(
            "Điều kiện nhiệt độ tốt cho cây phát triển."
        )

    if temp > 35:

        analysis.append(
            "Cần che nắng hoặc tưới mát cho cây."
        )

    if humidity > 80:

        analysis.append(
            "Nên kiểm tra nấm bệnh trên lá."
        )

    if humidity < 40:

        analysis.append(
            "Không khí khô, nên tăng tưới."
        )

    return analysis
    # ==========================================
# WEATHER SUMMARY FOR AI
# ==========================================

def generate_weather_summary(weather):

    if not weather:
        return "Không có dữ liệu thời tiết."

    temp = weather.get("temp", "?")
    humidity = weather.get("humidity", "?")
    wind = weather.get("wind", "?")

    summary = f"""
Nhiệt độ: {temp}°C
Độ ẩm: {humidity}%
Gió: {wind} m/s
"""

    return summary

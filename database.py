# ==========================================
# AJI FARM AI - DATABASE SYSTEM
# ==========================================

import json
import os
import copy
from datetime import datetime

from config import DATA_FILE


# ==========================================
# DATA SCHEMA (CẤU TRÚC DATABASE)
# ==========================================

INIT_DATA = {

    # Danh sách cây trồng
    "plants": [],

    # Nhật ký bệnh
    "disease_logs": [],

    # Nhật ký tưới nước
    "irrigation_logs": [],

    # Nhật ký bón phân
    "fertilizer_logs": [],

    # Kho vật tư
    "inventory": {
        "fertilizer": 100,
        "pesticide": 100
    },

    # AI chat history
    "chat_history": []
}


# ==========================================
# LOAD DATABASE
# ==========================================

def load_data():

    if os.path.exists(DATA_FILE):

        try:

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data

        except:

            return copy.deepcopy(INIT_DATA)

    else:

        return copy.deepcopy(INIT_DATA)


# ==========================================
# SAVE DATABASE
# ==========================================

def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# RESET DATABASE
# ==========================================

def reset_database():

    data = copy.deepcopy(INIT_DATA)

    save_data(data)

    return data


# ==========================================
# PLANT MANAGEMENT
# ==========================================

def add_plant(data, crop_id, plant_date):

    plant = {

        "crop": crop_id,

        "date": str(plant_date),

        "created_at": datetime.now().isoformat()
    }

    data["plants"].append(plant)

    return data


def delete_plant(data, index):

    if index < len(data["plants"]):

        data["plants"].pop(index)

    return data


def get_plants(data):

    return data["plants"]


# ==========================================
# DISEASE LOG SYSTEM
# ==========================================

def add_disease_log(data, crop, note):

    log = {

        "date": str(datetime.now().date()),

        "crop": crop,

        "note": note
    }

    data["disease_logs"].append(log)

    return data


def get_disease_logs(data):

    return data["disease_logs"]


# ==========================================
# IRRIGATION LOG SYSTEM
# ==========================================

def add_irrigation_log(data, crop, water_amount):

    log = {

        "date": str(datetime.now().date()),

        "crop": crop,

        "water_ml": water_amount
    }

    data["irrigation_logs"].append(log)

    return data


def get_irrigation_logs(data):

    return data["irrigation_logs"]


# ==========================================
# FERTILIZER LOG SYSTEM
# ==========================================

def add_fertilizer_log(data, crop, fertilizer_type, amount):

    log = {

        "date": str(datetime.now().date()),

        "crop": crop,

        "type": fertilizer_type,

        "amount": amount
    }

    data["fertilizer_logs"].append(log)

    return data


def get_fertilizer_logs(data):

    return data["fertilizer_logs"]


# ==========================================
# INVENTORY MANAGEMENT
# ==========================================

def update_inventory(data, item, amount):

    if item in data["inventory"]:

        data["inventory"][item] += amount

    else:

        data["inventory"][item] = amount

    return data


def get_inventory(data):

    return data["inventory"]


# ==========================================
# CHAT HISTORY
# ==========================================

def add_chat(data, user_msg, ai_msg):

    chat = {

        "time": datetime.now().isoformat(),

        "user": user_msg,

        "ai": ai_msg
    }

    data["chat_history"].append(chat)

    return data


def get_chat_history(data):

    return data["chat_history"]

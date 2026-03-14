# ==========================================
# AJI FARM AI - CROP DATABASE
# ==========================================

# Database kiến thức cây trồng
# Mỗi cây gồm:
# name
# water_need (ml/ngày)
# sunlight
# soil
# care
# growth_days
# fertilizer_schedule


CROP_DB = {

    # ======================================
    # ỚT
    # ======================================

    "aji_charapita": {

        "name": "Ớt Aji Charapita",

        "water_need": 500,

        "sunlight": "Nắng mạnh",

        "soil": "Đất tơi xốp thoát nước tốt",

        "care": "Không để úng, bấm ngọn khi cây 30cm",

        "growth_days": 120,

        "fertilizer_schedule": [
            "7 ngày: phân hữu cơ",
            "20 ngày: NPK nhẹ",
            "40 ngày: Kali cao"
        ]
    },

    "chili": {

        "name": "Ớt thường",

        "water_need": 450,

        "sunlight": "Nắng mạnh",

        "soil": "Đất thịt nhẹ",

        "care": "Bón phân định kỳ 15 ngày",

        "growth_days": 100,

        "fertilizer_schedule": [
            "10 ngày: phân chuồng",
            "25 ngày: NPK",
            "50 ngày: Kali"
        ]
    },

    # ======================================
    # RAU
    # ======================================

    "lettuce": {

        "name": "Xà lách",

        "water_need": 200,

        "sunlight": "Nắng nhẹ",

        "soil": "Đất giàu hữu cơ",

        "care": "Giữ ẩm đất thường xuyên",

        "growth_days": 35,

        "fertilizer_schedule": [
            "7 ngày: phân hữu cơ",
            "15 ngày: NPK loãng"
        ]
    },

    "basil": {

        "name": "Húng quế",

        "water_need": 150,

        "sunlight": "Nắng trung bình",

        "soil": "Đất tơi xốp",

        "care": "Ngắt hoa để kích lá",

        "growth_days": 60,

        "fertilizer_schedule": [
            "10 ngày: phân hữu cơ",
            "20 ngày: NPK nhẹ"
        ]
    },

    "spinach": {

        "name": "Rau bina",

        "water_need": 180,

        "sunlight": "Nắng nhẹ",

        "soil": "Đất giàu mùn",

        "care": "Không để đất khô",

        "growth_days": 40,

        "fertilizer_schedule": [
            "7 ngày: phân hữu cơ"
        ]
    },

    # ======================================
    # CÂY ĂN TRÁI
    # ======================================

    "mango": {

        "name": "Xoài",

        "water_need": 1500,

        "sunlight": "Nắng mạnh",

        "soil": "Đất sâu",

        "care": "Tỉa cành sau thu hoạch",

        "growth_days": 365,

        "fertilizer_schedule": [
            "Đầu mùa mưa: phân hữu cơ",
            "Ra hoa: NPK",
            "Nuôi trái: Kali"
        ]
    },

    "durian": {

        "name": "Sầu riêng",

        "water_need": 2000,

        "sunlight": "Nắng mạnh",

        "soil": "Đất sâu thoát nước",

        "care": "Không để úng nước",

        "growth_days": 365,

        "fertilizer_schedule": [
            "Đầu mùa mưa: phân chuồng",
            "Ra hoa: NPK",
            "Nuôi trái: Kali cao"
        ]
    },

    "banana": {

        "name": "Chuối",

        "water_need": 1800,

        "sunlight": "Nắng mạnh",

        "soil": "Đất giàu hữu cơ",

        "care": "Tỉa chồi phụ",

        "growth_days": 300,

        "fertilizer_schedule": [
            "30 ngày: phân chuồng",
            "60 ngày: NPK",
            "Ra buồng: Kali"
        ]
    },

    # ======================================
    # CÂY PHỔ BIẾN
    # ======================================

    "tomato": {

        "name": "Cà chua",

        "water_need": 400,

        "sunlight": "Nắng mạnh",

        "soil": "Đất tơi xốp",

        "care": "Làm giàn leo",

        "growth_days": 90,

        "fertilizer_schedule": [
            "10 ngày: phân hữu cơ",
            "25 ngày: NPK",
            "Ra hoa: Kali"
        ]
    },

    "cucumber": {

        "name": "Dưa leo",

        "water_need": 350,

        "sunlight": "Nắng mạnh",

        "soil": "Đất giàu mùn",

        "care": "Làm giàn",

        "growth_days": 70,

        "fertilizer_schedule": [
            "10 ngày: phân chuồng",
            "20 ngày: NPK"
        ]
    }

}
# ==========================================
# AJI FARM AI - NPK LEAF ANALYSIS
# ==========================================

import numpy as np
from PIL import Image

from config import (
    N_THRESHOLD,
    P_THRESHOLD,
    K_THRESHOLD
)

# ==========================================
# LOAD IMAGE
# ==========================================

def load_image(image_file):

    img = Image.open(image_file).convert("RGB")

    return img


# ==========================================
# CONVERT IMAGE TO NUMPY
# ==========================================

def image_to_array(img):

    arr = np.array(img)

    return arr


# ==========================================
# CALCULATE RGB AVERAGE
# ==========================================

def calculate_rgb_mean(arr):

    r = arr[:, :, 0].mean()

    g = arr[:, :, 1].mean()

    b = arr[:, :, 2].mean()

    return r, g, b


# ==========================================
# GREEN INDEX
# ==========================================

def calculate_green_index(r, g, b):

    total = r + g + b

    if total == 0:
        return 0

    green_index = g / total

    return green_index


# ==========================================
# LEAF HEALTH SCORE
# ==========================================

def calculate_health_score(green_index):

    score = green_index * 100

    if score > 100:
        score = 100

    return int(score)


# ==========================================
# NITROGEN DEFICIENCY
# ==========================================

def detect_n_deficiency(r, g):

    if g < r * N_THRESHOLD:

        return True

    return False


# ==========================================
# PHOSPHORUS DEFICIENCY
# ==========================================

def detect_p_deficiency(g, b):

    if b > g * P_THRESHOLD:

        return True

    return False


# ==========================================
# POTASSIUM DEFICIENCY
# ==========================================

def detect_k_deficiency(r, g):

    if r > g * K_THRESHOLD:

        return True

    return False


# ==========================================
# LEAF COLOR CLASSIFICATION
# ==========================================

def classify_leaf_color(r, g, b):

    if g > r and g > b:

        return "Xanh khỏe"

    if r > g and r > b:

        return "Ngả vàng / thiếu dinh dưỡng"

    if b > r and b > g:

        return "Tím / thiếu lân"

    return "Không xác định"


# ==========================================
# DISEASE COLOR DETECTION
# ==========================================

def detect_disease_color(r, g, b):

    warnings = []

    if r > 180 and g < 100:

        warnings.append("Có dấu hiệu cháy lá")

    if b > 160:

        warnings.append("Có thể nhiễm nấm")

    if g < 80:

        warnings.append("Lá suy yếu")

    return warnings


# ==========================================
# MAIN ANALYSIS FUNCTION
# ==========================================

def analyze_leaf(image_file):

    img = load_image(image_file)

    arr = image_to_array(img)

    r, g, b = calculate_rgb_mean(arr)

    green_index = calculate_green_index(r, g, b)

    health_score = calculate_health_score(green_index)

    result = {

        "rgb": {

            "r": round(r, 2),
            "g": round(g, 2),
            "b": round(b, 2)
        },

        "green_index": round(green_index, 3),

        "health_score": health_score,

        "leaf_color": classify_leaf_color(r, g, b),

        "deficiencies": [],

        "warnings": []
    }

    if detect_n_deficiency(r, g):

        result["deficiencies"].append("Thiếu Đạm (N)")

    if detect_p_deficiency(g, b):

        result["deficiencies"].append("Thiếu Lân (P)")

    if detect_k_deficiency(r, g):

        result["deficiencies"].append("Thiếu Kali (K)")

    disease_warnings = detect_disease_color(r, g, b)

    result["warnings"].extend(disease_warnings)

    if not result["deficiencies"]:

        result["deficiencies"].append("Không phát hiện thiếu NPK")

    return result

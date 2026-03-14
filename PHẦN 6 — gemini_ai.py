# ==========================================
# AJI FARM AI - GEMINI PLANT DOCTOR
# ==========================================

import google.generativeai as genai
import io
from PIL import Image

from config import GEMINI_MODEL
from weather_system import generate_weather_summary
from crop_database import get_crop_info


# ==========================================
# LOAD GEMINI MODEL
# ==========================================

def load_gemini(api_key):

    try:

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(GEMINI_MODEL)

        return model

    except:

        return None


# ==========================================
# CONVERT IMAGE TO BYTES
# ==========================================

def image_to_bytes(img):

    buffer = io.BytesIO()

    img.save(buffer, format="JPEG")

    return buffer.getvalue()


# ==========================================
# BUILD AI PROMPT
# ==========================================

def build_prompt(crop_id, weather):

    crop_info = get_crop_info(crop_id)

    crop_name = crop_info["name"]

    weather_text = generate_weather_summary(weather)

    prompt = f"""
Bạn là chuyên gia nông nghiệp.

Thông tin cây:
{crop_name}

Điều kiện môi trường:
{weather_text}

Hãy phân tích ảnh lá cây và trả lời:

1. Cây có bệnh gì không?
2. Nếu có, bệnh gì?
3. Mức độ nghiêm trọng
4. Cách xử lý
5. Ưu tiên giải pháp sinh học
6. Nếu cần mới dùng thuốc hóa học

Trả lời rõ ràng theo từng mục.
"""

    return prompt


# ==========================================
# AI DISEASE DIAGNOSIS
# ==========================================

def diagnose_plant(model, image, crop_id, weather):

    try:

        img_bytes = image_to_bytes(image)

        prompt = build_prompt(crop_id, weather)

        response = model.generate_content([

            prompt,

            {
                "mime_type": "image/jpeg",
                "data": img_bytes
            }

        ])

        return response.text

    except Exception as e:

        return f"Lỗi AI: {e}"


# ==========================================
# QUICK DISEASE CHECK (TEXT ONLY)
# ==========================================

def quick_diagnosis(model, description):

    prompt = f"""
Triệu chứng cây trồng:

{description}

Hãy cho biết:

- khả năng bệnh
- cách xử lý nhanh
"""

    try:

        response = model.generate_content(prompt)

        return response.text

    except:

        return "Không thể phân tích."


# ==========================================
# FERTILIZER ADVISOR
# ==========================================

def fertilizer_advisor(model, crop_id, growth_stage):

    crop = get_crop_info(crop_id)

    prompt = f"""
Cây trồng: {crop['name']}

Giai đoạn: {growth_stage}

Hãy tư vấn:

- loại phân nên dùng
- liều lượng
- cách bón
"""

    try:

        response = model.generate_content(prompt)

        return response.text

    except:

        return "Không thể tư vấn phân bón."


# ==========================================
# FARM CONSULTANT CHAT
# ==========================================

def farm_chat(model, question):

    prompt = f"""
Bạn là chuyên gia nông nghiệp.

Hãy trả lời câu hỏi sau:

{question}
"""

    try:

        response = model.generate_content(prompt)

        return response.text

    except:

        return "AI không phản hồi."

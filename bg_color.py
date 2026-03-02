# bg_color.py
import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError
from config import is_dev_mode

load_dotenv()
DEV_MODE = is_dev_mode()

# 🎨 建議：其實背景顏色根本可以 rule-based（超穩）
EMOTION_COLOR_MAP = {
    "joy": "#FFD166, #FFB703, #FB8500",
    "sadness": "#4D96FF, #3A86FF, #4361EE",
    "anger": "#EF476F, #D62828, #9D0208",
    "anxiety": "#8E7DBE, #6A4C93, #5E60CE",
    "love": "#FF99C8, #F15BB5, #F72585",
    "calm": "#90DBF4, #A9DEF9, #E4C1F9",
    "neutral": "#CCCCCC, #999999, #666666",
}

DEFAULT_GRADIENT = "#CCCCCC, #999999, #666666"


def generate_color(emotion=None):
    emotion_key = (emotion or "neutral").lower()

    # ✅ DEV MODE：完全不打 OpenAI
    if DEV_MODE:
        return EMOTION_COLOR_MAP.get(emotion_key, DEFAULT_GRADIENT)

    # 如果你其實不想再用 LLM，這裡可以直接 return rule-based
    # return EMOTION_COLOR_MAP.get(emotion_key, DEFAULT_GRADIENT)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return EMOTION_COLOR_MAP.get(emotion_key, DEFAULT_GRADIENT)

    client = OpenAI(api_key=openai_api_key)

    prompt = f"""
You generate aesthetic HEX color gradients.

Emotion: "{emotion}"

RULES:
- Return EXACTLY 3 HEX color codes
- Format: "#RRGGBB, #RRGGBB, #RRGGBB"
- No explanations.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You generate aesthetic HEX color gradients."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )

        colors = (response.choices[0].message.content or "").strip()

        # 🔒 基本格式檢查（避免模型亂回）
        if colors.count("#") == 3 and "," in colors:
            return colors

        return EMOTION_COLOR_MAP.get(emotion_key, DEFAULT_GRADIENT)

    except (RateLimitError, APIError, Exception) as e:
        print("[WARN] generate_color fallback:", repr(e))
        return EMOTION_COLOR_MAP.get(emotion_key, DEFAULT_GRADIENT)
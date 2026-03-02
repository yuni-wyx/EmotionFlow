# classifier.py
import json
import os
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from config import is_dev_mode

load_dotenv()
DEV_MODE = is_dev_mode()

# Load emotion taxonomy
with open("emotions.json", "r", encoding="utf-8") as f:
    emotion_categories = json.load(f)

emotion_list = []
for emotions in emotion_categories.values():
    emotion_list.extend(emotions)

def get_emotion_category(emotion_label: str) -> str:
    # output 可能會包含 emoji / 多餘空白，這裡先做簡單 normalize
    label = (emotion_label or "").strip()
    for category, emotions in emotion_categories.items():
        if label in emotions:
            return category
    return "Unknown"

def classify_emotion_gemini(user_input: str):
    # ✅ DEV MODE：完全不打 OpenAI
    if DEV_MODE:
        mock_emotion = "anxiety 😟"
        return {
            "ok": True,
            "emotion": mock_emotion,
            "category": get_emotion_category(mock_emotion),
            "source": "mock",
        }

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {
            "ok": False,
            "error_type": "config",
            "message": "Missing OPENAI_API_KEY.",
        }

    client = OpenAI(api_key=openai_api_key)

    system_prompt = f"""
You are an emotion classification assistant. Based on the text input, return
the most likely emotion from this list:

{emotion_list}

Rules:
- Reply with only ONE emotion label from the list + ONE emoji.
- No extra words.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            temperature=0.2,
        )

        output = (response.choices[0].message.content or "").strip()
        category = get_emotion_category(output)

        return {
            "ok": True,
            "emotion": output,
            "category": category,
            "source": "openai",
        }

    except RateLimitError as e:
        print(f"[ERROR] OpenAI rate limit: {repr(e)}")
        return {
            "ok": False,
            "error_type": "quota",
            "message": "OpenAI quota/rate limit exceeded. Please try again later.",
        }

    except APIError as e:
        print(f"[ERROR] OpenAI API error: {repr(e)}")
        return {
            "ok": False,
            "error_type": "api",
            "message": "OpenAI API error occurred. Please try again later.",
        }

    except Exception as e:
        print(f"[ERROR] Unexpected error: {repr(e)}")
        return {
            "ok": False,
            "error_type": "unknown",
            "message": "Unexpected server error occurred.",
        }
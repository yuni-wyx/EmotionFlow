# responder.py
import os
import time
import random
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError
from config import is_dev_mode

load_dotenv()
DEV_MODE = is_dev_mode()

def generate_response_gemini(user_input, emotion=None, max_retries=3):
    # ✅ DEV MODE: 不打 API，直接回固定 mock
    if DEV_MODE:
        if emotion:
            return f"I hear you — feeling {emotion} can be really heavy. I’m here with you."
        return "I hear you — that sounds really heavy. I’m here with you."

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return "I’m here with you — I can’t access my response system right now."

    client = OpenAI(api_key=openai_api_key)

    system_prompt = """
    You are an empathetic AI counselor.
    Your job is to respond with emotional warmth, support, validation,
    and encouragement. Your tone should be calm, caring, and human-like.

    Always reply in **1 or 2 sentences only**, no more.
    Do NOT give advice unless asked. Focus on empathy first.
    """

    user_prompt = f'User says: "{user_input}"'
    if emotion:
        user_prompt = f'The user is feeling: "{emotion}".\n' + user_prompt

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.6,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            sleep_s = min(8, 0.5 * (2 ** attempt)) + random.uniform(0, 0.25)
            print("[WARN] OpenAI rate limit:", repr(e))
            time.sleep(sleep_s)

        except APIError as e:
            print("[ERROR] OpenAI API error:", repr(e))
            break

        except Exception as e:
            print("[ERROR] Unexpected error in generate_response_gemini:", repr(e))
            break

    return "I’m here with you. Please try again in a moment."
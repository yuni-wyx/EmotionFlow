# rlhf_flow.py
import os
import json
import re
import uuid
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from config import is_dev_mode
from bg_color import generate_color

load_dotenv()
DEV_MODE = is_dev_mode()

def _normalize_emotion(emotion: str) -> str:
    e = (emotion or "neutral").strip().lower()
    return e.split()[0] if e else "neutral"

def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    block = m.group(0).strip()
    try:
        return json.loads(block)
    except Exception:
        # best-effort repair
        try:
            return json.loads(block.replace("'", '"'))
        except Exception:
            return None

def generate_flow_ab(user_input: str) -> dict:
    request_id = uuid.uuid4().hex[:10]

    if not user_input or not user_input.strip():
        return {"ok": False, "error_type": "bad_request", "message": "Empty input.", "request_id": request_id}

    # ✅ DEV_MODE：不打 OpenAI，回固定 A/B
    if DEV_MODE:
        emotion = "anxiety 😟"
        emotion_key = _normalize_emotion(emotion)
        return {
            "ok": True,
            "request_id": request_id,
            "emotion": emotion,
            "category": "negative",
            "color": generate_color(emotion_key),
            "candidates": {
                "A": {
                    "prompt_version": "v1_reflect",
                    "response": "I hear you — that sounds really overwhelming. I’m here with you."
                },
                "B": {
                    "prompt_version": "v2_validate",
                    "response": "That makes so much sense to feel right now. You don’t have to carry it alone."
                }
            },
            "music": {
                "song": "Weightless",
                "artist": "Marconi Union",
                "reason": "A steady, soothing track that can help your body settle."
            },
            "source": "mock"
        }

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {"ok": False, "error_type": "config", "message": "Missing OPENAI_API_KEY.", "request_id": request_id}

    client = OpenAI(api_key=openai_api_key)

    system_prompt = """
You are EmotionFlow. You will:
1) infer the user's emotion
2) generate TWO candidate empathetic responses (A and B) that follow different styles
3) recommend ONE real song

Hard rules:
- Return ONLY valid JSON (no markdown, no extra text)
- Each response must be 1–2 sentences
- No advice unless the user explicitly asks for advice
"""

    user_prompt = f"""
User text: {user_input}

Return JSON with EXACT keys:
{{
  "emotion": "<short label + optional emoji>",
  "category": "<one category word>",
  "candidates": {{
    "A": {{"prompt_version": "v1_reflect", "response": "<1-2 sentences>"}},
    "B": {{"prompt_version": "v2_validate", "response": "<1-2 sentences>"}}
  }},
  "music": {{
    "song": "<real song>",
    "artist": "<real artist>",
    "reason": "<1-2 sentences>"
  }}
}}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )

        raw = (resp.choices[0].message.content or "").strip()
        data = _extract_json(raw)

        if not data:
            # parse fallback (still returns A/B)
            emotion = "neutral"
            emotion_key = "neutral"
            return {
                "ok": True,
                "request_id": request_id,
                "emotion": emotion,
                "category": "Unknown",
                "color": generate_color(emotion_key),
                "candidates": {
                    "A": {"prompt_version": "v1_reflect", "response": "I hear you — that sounds like a lot. I’m here with you."},
                    "B": {"prompt_version": "v2_validate", "response": "Your feelings make sense, and you don’t have to face this alone."},
                },
                "music": {
                    "song": "Clair de Lune",
                    "artist": "Claude Debussy",
                    "reason": "A calm, gentle piece to steady your mood."
                },
                "source": "openai_fallback_parse",
            }

        emotion = data.get("emotion", "neutral")
        category = data.get("category", "Unknown")
        candidates = data.get("candidates") or {}
        candA = candidates.get("A") or {}
        candB = candidates.get("B") or {}

        # ensure fields exist
        A = {
            "prompt_version": candA.get("prompt_version", "v1_reflect"),
            "response": (candA.get("response") or "").strip()
        }
        B = {
            "prompt_version": candB.get("prompt_version", "v2_validate"),
            "response": (candB.get("response") or "").strip()
        }

        music = data.get("music") or {}
        song = (music.get("song") or "").strip()
        artist = (music.get("artist") or "").strip()
        reason = (music.get("reason") or "").strip()

        emotion_key = _normalize_emotion(emotion)

        return {
            "ok": True,
            "request_id": request_id,
            "emotion": emotion,
            "category": category,
            "color": generate_color(emotion_key),
            "candidates": {"A": A, "B": B},
            "music": {"song": song, "artist": artist, "reason": reason},
            "source": "openai",
        }

    except RateLimitError as e:
        return {"ok": False, "error_type": "quota", "message": "Quota exceeded or temporarily unavailable.", "detail": str(e), "request_id": request_id}
    except APIError as e:
        return {"ok": False, "error_type": "api", "message": "OpenAI API error.", "detail": str(e), "request_id": request_id}
    except Exception as e:
        return {"ok": False, "error_type": "unknown", "message": "Unexpected server error.", "detail": repr(e), "request_id": request_id}
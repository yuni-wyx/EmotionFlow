# flow.py
import os
import json
import re
import uuid
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from config import is_dev_mode

from classifier import classify_emotion_gemini
from responder import generate_response_gemini
from recommender import generate_music_recommendation
from bg_color import generate_color

load_dotenv()
DEV_MODE = is_dev_mode()


def _normalize_emotion(emotion: str) -> str:
    """
    Normalize emotion label for downstream rule-based functions.
    e.g. "anxiety 😟" -> "anxiety"
    """
    e = (emotion or "neutral").strip().lower()
    if not e:
        return "neutral"
    return e.split()[0]


def _extract_json(text: str) -> dict | None:
    """Try hard to extract a JSON object from model output."""
    if not text:
        return None
    text = text.strip()

    # direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # try find first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None

    block = m.group(0).strip()

    # attempt parse
    try:
        return json.loads(block)
    except Exception:
        pass

    # lightweight "repair": replace single quotes with double quotes (best-effort)
    try:
        repaired = block.replace("'", '"')
        return json.loads(repaired)
    except Exception:
        return None


def generate_flow(user_input: str) -> dict:
    request_id = uuid.uuid4().hex[:10]

    if not user_input or not user_input.strip():
        return {"ok": False, "error_type": "bad_request", "message": "Empty input.", "request_id": request_id}

    # ✅ DEV MODE: no OpenAI calls
    if DEV_MODE:
        emo_res = classify_emotion_gemini(user_input)
        emotion = emo_res.get("emotion", "neutral")
        category = emo_res.get("category", "Unknown")

        reply = generate_response_gemini(user_input, emotion)
        music_text = generate_music_recommendation(user_input, emotion)

        lines = [ln.strip() for ln in (music_text or "").split("\n") if ln.strip()]
        song = lines[0].replace("Song:", "").strip() if len(lines) > 0 else ""
        artist = lines[1].replace("Artist:", "").strip() if len(lines) > 1 else ""
        reason = lines[2].replace("Reason:", "").strip() if len(lines) > 2 else (music_text or "")

        emotion_key = _normalize_emotion(emotion)

        return {
            "ok": True,
            "emotion": emotion,
            "category": category,
            "response": reply,
            "music": {"song": song, "artist": artist, "reason": reason},
            "color": generate_color(emotion_key),
            "source": "mock",
            "request_id": request_id,
        }

    # ✅ PROD: single OpenAI call
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {"ok": False, "error_type": "config", "message": "Missing OPENAI_API_KEY.", "request_id": request_id}

    client = OpenAI(api_key=openai_api_key)

    system_prompt = """
You are EmotionFlow, a supportive assistant that:
1) Classifies the user's emotion
2) Responds empathetically (1–2 sentences, no advice unless asked)
3) Recommends ONE real song as emotional support

Return ONLY valid JSON, no markdown, no extra text.
"""

    user_prompt = f"""
User text: {user_input}

Return JSON with EXACT keys:
{{
  "emotion": "<short label + optional emoji>",
  "category": "<one category word>",
  "response": "<1-2 sentences empathetic reply>",
  "music": {{
    "song": "<real song name>",
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
            temperature=0.4,
        )

        text = (resp.choices[0].message.content or "").strip()
        data = _extract_json(text)

        if not data:
            emotion_key = "neutral"
            return {
                "ok": True,
                "emotion": "neutral",
                "category": "Unknown",
                "response": "I hear you — that sounds like a lot. I’m here with you.",
                "music": {
                    "song": "Clair de Lune",
                    "artist": "Claude Debussy",
                    "reason": "A calm, gentle piece to steady your mood."
                },
                "color": generate_color(emotion_key),
                "source": "openai_fallback_parse",
                "request_id": request_id,
            }

        emotion = data.get("emotion", "neutral")
        category = data.get("category", "Unknown")
        response_text = data.get("response", "I hear you — I’m here with you.")
        music = data.get("music") or {}
        song = music.get("song", "")
        artist = music.get("artist", "")
        reason = music.get("reason", "")

        emotion_key = _normalize_emotion(emotion)

        return {
            "ok": True,
            "emotion": emotion,
            "category": category,
            "response": response_text,
            "music": {"song": song, "artist": artist, "reason": reason},
            "color": generate_color(emotion_key),
            "source": "openai",
            "request_id": request_id,
        }

    except RateLimitError as e:
        # includes "insufficient_quota" cases in practice
        return {
            "ok": False,
            "error_type": "quota",
            "message": "Model quota exceeded or temporarily unavailable.",
            "detail": str(e),
            "request_id": request_id,
        }

    except APIError as e:
        return {
            "ok": False,
            "error_type": "api",
            "message": "OpenAI API error occurred. Please try again later.",
            "detail": str(e),
            "request_id": request_id,
        }

    except Exception as e:
        return {
            "ok": False,
            "error_type": "unknown",
            "message": "Unexpected server error occurred.",
            "detail": repr(e),
            "request_id": request_id,
        }
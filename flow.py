# flow.py
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from config import is_dev_mode

# DEV MODE 下：用現成 functions（它們會 mock，不燒 quota）
from classifier import classify_emotion_gemini
from responder import generate_response_gemini
from recommender import generate_music_recommendation
from bg_color import generate_color

load_dotenv()
DEV_MODE = is_dev_mode()


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
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def generate_flow(user_input: str) -> dict:
    """
    Returns:
      {
        ok: bool,
        emotion: str,
        category: str,
        response: str,
        music: {song, artist, reason},
        color: "#RRGGBB, #RRGGBB, #RRGGBB",
        source: "mock" | "openai",
        error_type?: ...
      }
    """

    # ✅ DEV MODE: no OpenAI calls
    if DEV_MODE:
        emo_res = classify_emotion_gemini(user_input)
        emotion = emo_res.get("emotion", "neutral")
        category = emo_res.get("category", "Unknown")

        reply = generate_response_gemini(user_input, emotion)
        music_text = generate_music_recommendation(user_input, emotion)

        # parse the 3-line format robustly
        lines = [ln.strip() for ln in (music_text or "").split("\n") if ln.strip()]
        song = lines[0].replace("Song:", "").strip() if len(lines) > 0 else ""
        artist = lines[1].replace("Artist:", "").strip() if len(lines) > 1 else ""
        reason = lines[2].replace("Reason:", "").strip() if len(lines) > 2 else (music_text or "")

        return {
            "ok": True,
            "emotion": emotion,
            "category": category,
            "response": reply,
            "music": {"song": song, "artist": artist, "reason": reason},
            "color": generate_color(emotion),
            "source": "mock",
        }

    # ✅ PROD: single OpenAI call
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {"ok": False, "error_type": "config", "message": "Missing OPENAI_API_KEY."}

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
            # fallback: minimal safe output
            return {
                "ok": True,
                "emotion": "neutral",
                "category": "Unknown",
                "response": "I hear you — that sounds like a lot. I’m here with you.",
                "music": {"song": "Clair de Lune", "artist": "Claude Debussy", "reason": "A calm, gentle piece to steady your mood."},
                "color": generate_color("neutral"),
                "source": "openai_fallback_parse",
            }

        emotion = data.get("emotion", "neutral")
        category = data.get("category", "Unknown")
        response_text = data.get("response", "I hear you — I’m here with you.")
        music = data.get("music") or {}
        song = music.get("song", "")
        artist = music.get("artist", "")
        reason = music.get("reason", "")

        return {
            "ok": True,
            "emotion": emotion,
            "category": category,
            "response": response_text,
            "music": {"song": song, "artist": artist, "reason": reason},
            "color": generate_color(emotion),  # rule-based / fallback, not LLM
            "source": "openai",
        }

    except RateLimitError as e:
        return {"ok": False, "error_type": "quota", "message": str(e)}

    except APIError as e:
        return {"ok": False, "error_type": "api", "message": str(e)}

    except Exception as e:
        return {"ok": False, "error_type": "unknown", "message": repr(e)}
# recommender.py
import os
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError
from config import is_dev_mode

load_dotenv()
DEV_MODE = is_dev_mode()

# DEV_MODE 用的固定歌單（穩、好測、不燒錢）
MOCK_RECS = {
    "anxiety": (
        "Song: Weightless\n"
        "Artist: Marconi Union\n"
        "Reason: A steady, soothing track that can help your body settle down."
    ),
    "sadness": (
        "Song: Fix You\n"
        "Artist: Coldplay\n"
        "Reason: Gentle and supportive — it meets sadness with warmth."
    ),
    "anger": (
        "Song: Lose Yourself\n"
        "Artist: Eminem\n"
        "Reason: High energy and cathartic — it helps release tension safely."
    ),
    "joy": (
        "Song: Good as Hell\n"
        "Artist: Lizzo\n"
        "Reason: Bright and empowering — it matches upbeat, confident energy."
    ),
    "neutral": (
        "Song: Clair de Lune\n"
        "Artist: Claude Debussy\n"
        "Reason: Calm and spacious — a soft background for any mood."
    ),
}

DEFAULT_FALLBACK = (
    "Song: River Flows in You\n"
    "Artist: Yiruma\n"
    "Reason: A gentle, calming piece to help you slow down and breathe."
)


def _pick_mock(emotion: str) -> str:
    key = (emotion or "neutral").lower()
    # emotion 可能是 "anxiety 😟" 這種帶 emoji 的，做個簡單清理
    key = key.split()[0] if key else "neutral"
    return MOCK_RECS.get(key, MOCK_RECS["neutral"])


def _looks_like_expected_format(text: str) -> bool:
    t = (text or "").strip()
    return ("Song:" in t) and ("Artist:" in t) and ("Reason:" in t)


def generate_music_recommendation(user_input, emotion):
    """
    Recommend a therapeutic music track based on user's input and emotion.
    Returns EXACT format:
      Song: ...
      Artist: ...
      Reason: ...
    """

    # ✅ DEV MODE：完全不打 OpenAI
    if DEV_MODE:
        return _pick_mock(emotion)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return _pick_mock(emotion)

    client = OpenAI(api_key=openai_api_key)

    system_prompt = """
You are a music therapist AI who recommends songs based on emotional tone.
Your music knowledge spans pop, indie, R&B, classical, and global music.
You choose songs that create emotional resonance, validation, or comfort.

Rules:
- Respond ONLY in the required format.
- Must recommend real songs.
- Keep the explanation short (1–2 sentences).
"""

    user_prompt = f"""
User emotion: {emotion}
User input: "{user_input}"

Please respond exactly in this format:

Song: <song name>
Artist: <artist>
Reason: <short emotional reason>
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        output = (response.choices[0].message.content or "").strip()

        # 🔒 格式不對就 fallback（避免 app.py split 爆炸）
        if not _looks_like_expected_format(output):
            return _pick_mock(emotion)

        return output

    except RateLimitError as e:
        print(f"[ERROR] OpenAI rate limit exceeded in music: {repr(e)}")
        return _pick_mock(emotion)

    except APIError as e:
        print(f"[ERROR] OpenAI API error in music: {repr(e)}")
        return _pick_mock(emotion)

    except Exception as e:
        print(f"[ERROR] Unexpected error in generate_music_recommendation: {repr(e)}")
        return _pick_mock(emotion)
### app.py
from datetime import datetime, timezone
import uuid
import json
import urllib.parse
import os
from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
from classifier import classify_emotion_gemini
from responder import generate_response_gemini
from recommender import generate_music_recommendation
from bg_color import generate_color
from dashboard import create_dashboard
from flow import generate_flow
from secret import get_secret
from config import is_dev_mode
DEV_MODE = is_dev_mode()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only")

try:
    mongo_uri = get_secret("MONGODB_URI")
except Exception as e:
    print(f"[ERROR] Failed to retrieve secret: {e}")
    mongo_uri = None
if not mongo_uri and not DEV_MODE:
    raise RuntimeError("Mongo URI not configured, app will not start.")

mongo_client = MongoClient(mongo_uri) if mongo_uri else None
db = mongo_client["emotion_platform"] if mongo_client is not None else None

collection = db["user_inputs"] if db is not None else None
text_feedback_collection = db["text_feedbacks"] if db is not None else None
music_feedback_collection = db["music_feedbacks"] if db is not None else None

dash_app = create_dashboard(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}
    user_input = (data.get("user_input") or "").strip()
    user_id = data.get("user_id") or session.get("user_id", "anonymous")

    if not user_input:
        return jsonify({"ok": False, "error": "Missing 'user_input'"}), 400

    if collection is not None:
        collection.insert_one({
            "user_id": user_id,
            "text": user_input,
            "timestamp": datetime.now(timezone.utc)
        })
        
    return jsonify({"ok": True}), 200

@app.route("/predict", methods=["POST"])
def predict_emotions():
    data = request.get_json(silent=True) or {}
    user_input = data.get("text")

    if not user_input:
        return jsonify({"ok": False, "error": "Missing 'text' in request body"}), 400

    result = classify_emotion_gemini(user_input)

    # 如果 classify_emotion_gemini 出錯，就根據 error_type 回傳不同狀態碼
    if not result.get("ok", True):
        error_type = result.get("error_type")

        if error_type == "quota":
            status_code = 429  # Too Many Requests / Quota exceeded
        elif error_type == "api":
            status_code = 503  # Service Unavailable
        else:
            status_code = 500  # Unexpected server error

        return jsonify(result), status_code

    return jsonify(result), 200


@app.route("/api/respond", methods=["POST"])
def generate_response():
    data = request.get_json()
    text = data.get("text", "")
    emotion = data.get("emotion") 
    reply = generate_response_gemini(text, emotion)
    return jsonify({"response": reply})

@app.route("/api/flow", methods=["POST"])
def api_flow():
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("user_input") or ""

    result = generate_flow(text)

    if not result.get("ok", True):
        et = result.get("error_type")
        if et == "bad_request":
            return jsonify(result), 400
        if et == "quota":
            return jsonify(result), 429
        if et == "api":
            return jsonify(result), 503
        return jsonify(result), 500

    return jsonify(result), 200

@app.route("/api/music", methods=["POST"])
def recommend_music():
    data = request.json or {}
    user_input = data.get("text", "")
    emotion = data.get("emotion", "neutral")

    if not user_input:
        return jsonify({"ok": False, "error": "Missing 'text'"}), 400

    music = generate_music_recommendation(user_input, emotion)
    lines = [ln.strip() for ln in (music or "").split("\n") if ln.strip()]

    # 🔒 防爆：格式不完整就直接回原文（至少 UI 不會 500）
    if len(lines) < 3:
        return jsonify({"recommendation": (music or "").replace("\n", "<br>")})

    song = lines[0].replace("Song:", "").strip()
    artist = lines[1].replace("Artist:", "").strip()
    reason = lines[2].replace("Reason:", "").strip()

    youtube_url = get_youtube_search_url(song, artist)
    recommendation = (
        f"{song} - {artist}<br>"
        f"{reason}<br>"
        f"🔗 <a href='{youtube_url}' target='_blank'>Watch on YouTube</a>"
    )
    return jsonify({"recommendation": recommendation})

def get_youtube_search_url(song, artist):
    query = urllib.parse.quote(f"{song} {artist}")
    return f"https://www.youtube.com/results?search_query={query}"

@app.route("/api/color", methods=["POST"])
def get_emotion_color():
    data = request.get_json()
    emotion = data.get("emotion", "neutral")
    color = generate_color(emotion)
    return jsonify({"color": color})

@app.route("/anonymous-login", methods=["POST"])
def anonymous_login():
    user_id = str(uuid.uuid4())[:8]
    session["user_id"] = user_id
    session["anonymous"] = True
    return jsonify({"status": "ok", "user_id": user_id})

@app.route("/text_feedback", methods=["POST"])
def text_save_feedback():
    data = request.json or {}

    if text_feedback_collection:
        text_feedback_collection.insert_one({
            "user_id": data.get("user_id", "anonymous"),
            "text_feedback": {
                "text": data.get("text_feedback_text"),
                "response": data.get("text_feedback_response"),
                "emotion": data.get("text_feedback_emotion"),
                "liked": data.get("text_feedback_liked")
            },
            "timestamp": datetime.now(timezone.utc)
        })

    return {"status": "ok"}, 200

@app.route("/music_feedback", methods=["POST"])
def music_save_feedback():
    data = request.json or {}

    if music_feedback_collection:
        music_feedback_collection.insert_one({
            "user_id": data.get("user_id", "anonymous"),
            "music_feedback": {
                "recommendations": data.get("music_recommendations"),
                "emotion": data.get("music_emotion"),
                "liked": data.get("music_liked")
            },
            "timestamp": datetime.now(timezone.utc)
        })

    return {"status": "ok"}, 200

@app.route("/callback")
def callback():
    code = request.args.get('code')
    return f"Authorization code received: {code}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=True)

import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from secret import get_secret

load_dotenv()
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise RuntimeError("MONGODB_URI not set locally.")

client = MongoClient(mongo_uri)
db = client["emotion_platform"]
col = db["preference_pairs"]

out_path = "dpo_dataset.jsonl"

with open(out_path, "w", encoding="utf-8") as f:
    for d in col.find({}):
        text = d.get("text", "").strip()
        emotion = d.get("emotion", "").strip()
        A = (d.get("response_A") or "").strip()
        B = (d.get("response_B") or "").strip()
        chosen = d.get("chosen")

        if not text or not A or not B or chosen not in ("A", "B"):
            continue

        chosen_resp = A if chosen == "A" else B
        rejected_resp = B if chosen == "A" else A

        prompt = f"User: {text}\nEmotion: {emotion}\nAssistant:"

        f.write(json.dumps({
            "prompt": prompt,
            "chosen": chosen_resp,
            "rejected": rejected_resp
        }, ensure_ascii=False) + "\n")

print("Wrote:", out_path)
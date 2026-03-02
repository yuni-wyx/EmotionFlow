import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
mongo_uri = os.getenv("MONGODB_URI")

if not mongo_uri:
    raise RuntimeError("MONGODB_URI not set locally.")

client = MongoClient(mongo_uri)
db = client["emotion_platform"]
col = db["preference_pairs"]

total = col.count_documents({})
winA = col.count_documents({"chosen": "A"})
winB = col.count_documents({"chosen": "B"})

print("Total pairs:", total)
if total > 0:
    print("A win-rate:", winA / total)
    print("B win-rate:", winB / total)

# (optional) breakdown by emotion_key if you add it
pipeline = [
    {"$addFields": {"emotion_key": {"$toLower": {"$arrayElemAt": [{"$split": ["$emotion", " "]}, 0]}}}},
    {"$group": {"_id": {"emotion_key": "$emotion_key", "chosen": "$chosen"}, "n": {"$sum": 1}}},
    {"$sort": {"_id.emotion_key": 1}}
]
print("\nBreakdown:")
for row in col.aggregate(pipeline):
    print(row)
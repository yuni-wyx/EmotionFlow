# 🌊 Emotion Flow

### Real-Time Emotional Support with RLHF and Emotion-Aware Content

🔗 **Live Demo:** [https://emotionflow-40672525442.us-central1.run.app](https://emotionflow-40672525442.us-central1.run.app)  
📄 **Project Type:** ML System + Web Application  
☁️ **Deployment:** Google Cloud Run  

---

## 🧠 Overview

**Emotion Flow** is a production-oriented emotional support web application that combines:

* Emotion classification (DistilBERT-based)
* Empathetic response generation (LLM-based)
* Reinforcement Learning from Human Feedback (RLHF) experimentation
* Mood-aware music recommendation
* Emotion-driven UI color adaptation

The system is designed to simulate a lightweight, real-time emotional companion that responds empathetically while maintaining production stability and cost efficiency.

---

## 🎯 Motivation

Mental distress often requires immediate emotional validation rather than clinical intervention. Emotion Flow explores:

1. Can transformer-based classifiers reliably detect emotional states?
2. Can RLHF improve the empathy and helpfulness of AI responses?
3. Can mood-aware content (music + UI color) enhance user experience?

This project bridges **NLP research**, **human-centered AI**, and **production ML systems**.

---

## 🏗 System Architecture

Emotion Flow uses a **single unified inference endpoint** for efficiency.

```
User Input
    ↓
/api/flow (Single LLM Call in Live Mode)
    ↓
Emotion Classification
Empathetic Response
Music Recommendation
    ↓
Rule-based Color Mapping
    ↓
Frontend UI Update
```

### Key Design Principles

* ✅ Single-call inference (quota-efficient)
* ✅ Graceful fallback modes (Demo / Live)
* ✅ Separation of classification, response, recommendation modules
* ✅ Feedback logging for future preference learning
* ✅ Cloud-native deployment (GCP Cloud Run)

---

## ⚙️ Core Components

### 1️⃣ Emotion Classification

* DistilBERT-based classifier
* Categorizes emotional states such as:

  * Anxiety
  * Sadness
  * Anger
  * Joy
  * Neutral

Evaluated on Reddit mental health datasets.

---

### 2️⃣ Empathetic Response Generation

Uses a large language model (LLM) to:

* Generate 1–2 sentence empathetic replies
* Avoid unsolicited advice
* Focus on emotional validation
* Maintain safe-response behavior

Example:

> “That sounds really overwhelming. I’m here with you, and your feelings make sense.”

---

### 3️⃣ Reinforcement Learning from Human Feedback (RLHF)

The system logs user feedback:

* 👍 Helpful
* 👎 Not Helpful

This enables:

* Preference modeling
* Pairwise comparison experiments
* Future DPO/PPO-style fine-tuning

---

### 4️⃣ Music Recommendation

Emotion-aware music suggestions:

* Real songs
* Short emotional rationale
* YouTube link generation

Example:

```
Fix You – Coldplay
A gentle and supportive track that meets sadness with warmth.
```

---

### 5️⃣ Emotion-Driven UI Color

Background gradient adapts to detected emotion.

Example mappings:

| Emotion | Gradient           |
| ------- | ------------------ |
| Anxiety | Purple-blue        |
| Sadness | Deep blue          |
| Joy     | Warm yellow/orange |
| Anger   | Red tones          |

Color generation is rule-based to reduce inference cost.

---

## 🚀 Deployment

### Cloud Deployment

* Google Cloud Run
* Containerized with Docker
* Public HTTPS endpoint
* Environment-variable based configuration

---

## 🔧 Running Locally

### 1️⃣ Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2️⃣ Demo Mode (No API Keys Required)

```bash
export APP_MODE=demo
python app.py
```

Features:

* No OpenAI required
* No MongoDB required
* Fully interactive demo experience

---

### 3️⃣ Live Mode (LLM Enabled)

```bash
export APP_MODE=live
export OPENAI_API_KEY=your_key
python app.py
```

---

## 📊 API Endpoint

### Unified Endpoint

```
POST /api/flow
```

Request:

```json
{
  "text": "I feel overwhelmed lately."
}
```

Response:

```json
{
  "emotion": "anxiety 😟",
  "category": "negative",
  "response": "That sounds really heavy. I’m here with you.",
  "music": {
    "song": "Weightless",
    "artist": "Marconi Union",
    "reason": "A calming track to help your body settle."
  },
  "color": "#8E7DBE, #6A4C93, #5E60CE"
}
```

---

## 📈 Research Focus

This project explores:

* Emotion classification accuracy
* Empathy quality improvements via RLHF
* User preference modeling
* Multi-modal emotional reinforcement
* Cost-aware LLM system design

---

## 🧪 Experimental Roadmap

Planned extensions:

* DPO-based preference optimization
* Multi-turn emotional memory
* Valence-arousal modeling
* Safety-aware response gating
* Longitudinal emotional trend analysis

---

## 🛡 Safety Considerations

* No clinical advice
* Escalation handling for high-risk phrases
* Controlled response length
* Graceful degradation under API failure

---

## 🧩 Tech Stack

* Python
* Flask
* OpenAI API
* DistilBERT
* MongoDB
* Google Cloud Run
* Docker

---

## 💡 Why This Project Matters

Emotion Flow demonstrates:

* End-to-end ML system design
* Human-centered AI alignment
* Production-grade inference optimization
* Research-to-deployment pipeline
* Practical RLHF experimentation

---

## 👩‍💻 Author

Yuni Wu
MS Data Science — University of Colorado Boulder
ML Systems | Robotics | LLM Alignment | Cloud ML Infrastructure

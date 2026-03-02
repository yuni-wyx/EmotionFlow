# dashboard.py (Recruiter Demo Style)
from collections import Counter
import re
import os
import pandas as pd
import plotly.graph_objs as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from pymongo import MongoClient
from dotenv import load_dotenv

from secret import get_secret
from config import is_dev_mode

load_dotenv()
DEV_MODE = is_dev_mode()

# ---------- THEME ----------
BG = "#0B0F1A"          # deep space
PANEL = "#111827"       # card bg
BORDER = "rgba(0,245,212,0.18)"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"
CYAN = "#00F5D4"
PURPLE = "#9B5DE5"
BLUE = "#4CC9F0"
GRID = "rgba(156,163,175,0.12)"


def _get_mongo_uri() -> str | None:
    if DEV_MODE:
        return os.getenv("MONGODB_URI")
    try:
        return get_secret("MONGODB_URI")
    except Exception:
        return os.getenv("MONGODB_URI")


mongo_uri = _get_mongo_uri()
mongo_client = MongoClient(mongo_uri) if mongo_uri else None
db = mongo_client["emotion_platform"] if mongo_client else None

text_feedback_collection = db["text_feedbacks"] if db is not None else None
music_feedback_collection = db["music_feedbacks"] if db is not None else None
preference_collection = db["preference_pairs"] if db is not None else None


# ---------- DATA ----------
def fetch_text_feedback_data():
    if text_feedback_collection is None:
        return pd.DataFrame(columns=['user_id', 'text', 'response', 'emotion', 'liked', 'timestamp'])

    data = list(text_feedback_collection.find())
    if not data:
        return pd.DataFrame(columns=['user_id', 'text', 'response', 'emotion', 'liked', 'timestamp'])

    processed = [{
        'user_id': d.get('user_id', 'anonymous'),
        'text': d.get('text_feedback', {}).get('text', ''),
        'response': d.get('text_feedback', {}).get('response', ''),
        'emotion': d.get('text_feedback', {}).get('emotion', ''),
        'liked': d.get('text_feedback', {}).get('liked', None),
        'timestamp': d.get('timestamp', None)
    } for d in data]

    return pd.DataFrame(processed)


def fetch_music_feedback_data():
    if music_feedback_collection is None:
        return pd.DataFrame(columns=['user_id', 'recommendations', 'emotion', 'liked', 'timestamp'])

    data = list(music_feedback_collection.find())
    if not data:
        return pd.DataFrame(columns=['user_id', 'recommendations', 'emotion', 'liked', 'timestamp'])

    processed = [{
        'user_id': d.get('user_id', 'anonymous'),
        'recommendations': d.get('music_feedback', {}).get('recommendations', ''),
        'emotion': d.get('music_feedback', {}).get('emotion', ''),
        'liked': d.get('music_feedback', {}).get('liked', None),
        'timestamp': d.get('timestamp', None)
    } for d in data]

    return pd.DataFrame(processed)


def fetch_preference_data():
    if preference_collection is None:
        return pd.DataFrame(columns=[
            "user_id", "text", "emotion", "emotion_key",
            "request_id",
            "prompt_version_A", "prompt_version_B",
            "response_A", "response_B",
            "chosen", "chosen_prompt_version",
            "timestamp"
        ])

    data = list(preference_collection.find())
    if not data:
        return pd.DataFrame(columns=[
            "user_id", "text", "emotion", "emotion_key",
            "request_id",
            "prompt_version_A", "prompt_version_B",
            "response_A", "response_B",
            "chosen", "chosen_prompt_version",
            "timestamp"
        ])

    processed = []
    for d in data:
        emotion_raw = d.get("emotion", "") or ""
        # emotion like "anxiety 😟" -> key "anxiety"
        emotion_key = (emotion_raw.split()[0].lower() if emotion_raw else "neutral")

        chosen = d.get("chosen")
        pvA = d.get("prompt_version_A", "v1_reflect")
        pvB = d.get("prompt_version_B", "v2_validate")
        chosen_pv = pvA if chosen == "A" else (pvB if chosen == "B" else "Unknown")

        processed.append({
            "user_id": d.get("user_id", "anonymous"),
            "text": d.get("text", ""),
            "emotion": emotion_raw,
            "emotion_key": emotion_key,
            "request_id": d.get("request_id"),
            "prompt_version_A": pvA,
            "prompt_version_B": pvB,
            "response_A": d.get("response_A", ""),
            "response_B": d.get("response_B", ""),
            "chosen": chosen,
            "chosen_prompt_version": chosen_pv,
            "timestamp": d.get("timestamp")
        })

    return pd.DataFrame(processed)


def fetch_emotion_distribution_from_text_feedback(df: pd.DataFrame) -> dict:
    if df.empty or "emotion" not in df.columns:
        return {}
    emotions = [
        re.sub(r'[^a-zA-Z\s]', '', str(e)).strip().lower()
        for e in df["emotion"].fillna("").tolist()
    ]
    emotions = [e for e in emotions if e]
    return dict(Counter(emotions))


# ---------- FIG THEME ----------
def apply_console_theme(fig, title: str | None = None):
    if title:
        fig.update_layout(title=title)

    fig.update_layout(
        plot_bgcolor=PANEL,
        paper_bgcolor=BG,
        font=dict(family="JetBrains Mono", color=TEXT),
        title_font=dict(family="Space Grotesk", color=CYAN, size=18),
        xaxis=dict(color=MUTED, gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(color=MUTED, gridcolor=GRID, zerolinecolor=GRID),
        margin=dict(l=28, r=18, t=58, b=28),
        legend=dict(font=dict(family="JetBrains Mono", color=TEXT)),
    )
    return fig


def kpi_card(label: str, value: str, accent: str = CYAN, sub: str | None = None):
    return html.Div(
        [
            html.Div(label, style={"color": MUTED, "fontSize": "12px", "letterSpacing": "1px"}),
            html.Div(value, style={"color": TEXT, "fontSize": "26px", "fontWeight": "700", "lineHeight": "1.1"}),
            html.Div(sub or "", style={"color": accent, "fontSize": "12px", "marginTop": "6px", "fontFamily": "JetBrains Mono"})
        ],
        style={
            "backgroundColor": PANEL,
            "border": f"1px solid {BORDER}",
            "borderRadius": "16px",
            "padding": "16px 16px",
            "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
        }
    )


def create_dashboard(flask_app):
    dash_app = Dash(
        __name__,
        server=flask_app,
        routes_pathname_prefix="/dashboard/",
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap",
        ]
    )
    dash_app.title = "EmotionFlow • RLHF Alignment Console"

    # ---- Fetch data ----
    text_df = fetch_text_feedback_data()
    music_df = fetch_music_feedback_data()
    pref_df = fetch_preference_data()

    # ---- KPIs ----
    total_pairs = int(pref_df.shape[0]) if not pref_df.empty else 0
    a_wins = int((pref_df["chosen"] == "A").sum()) if not pref_df.empty else 0
    b_wins = int((pref_df["chosen"] == "B").sum()) if not pref_df.empty else 0
    win_rate_b = (b_wins / total_pairs) if total_pairs > 0 else 0.0

    text_like = int((text_df["liked"] == True).sum()) if not text_df.empty else 0
    text_dislike = int((text_df["liked"] == False).sum()) if not text_df.empty else 0
    music_like = int((music_df["liked"] == True).sum()) if not music_df.empty else 0
    music_dislike = int((music_df["liked"] == False).sum()) if not music_df.empty else 0

    # ---- Figures ----
    fig_ab = go.Figure(data=[go.Bar(
        x=["A", "B"],
        y=[a_wins, b_wins],
        marker_color=[BLUE, PURPLE]
    )])
    apply_console_theme(fig_ab, "RLHF • A/B Preference Votes")

    pv_counts = pref_df["chosen_prompt_version"].value_counts().to_dict() if not pref_df.empty else {}
    fig_pv = go.Figure(
        data=[go.Bar(x=list(pv_counts.keys()), y=list(pv_counts.values()), marker_color=CYAN)]
        if pv_counts else [go.Bar(x=["v1_reflect", "v2_validate"], y=[0, 0], marker_color=CYAN)]
    )
    apply_console_theme(fig_pv, "RLHF • Winning Prompt Version")

    # Emotion distribution (from text feedback)
    emo_counts = fetch_emotion_distribution_from_text_feedback(text_df)
    fig_emo = go.Figure(
        data=[go.Bar(
            x=list(emo_counts.keys()),
            y=list(emo_counts.values()),
            marker_color=BLUE
        )]
    )
    apply_console_theme(fig_emo, "Signals • Detected Emotion Frequency (from Text Feedback)")

    # Preference by emotion (top 8)
    if pref_df.empty:
        fig_pref_by_emo = go.Figure(data=[go.Bar(x=[], y=[])])
    else:
        top_emotions = pref_df["emotion_key"].value_counts().head(8).index.tolist()
        sub = pref_df[pref_df["emotion_key"].isin(top_emotions)]
        grouped = sub.groupby(["emotion_key", "chosen_prompt_version"]).size().reset_index(name="count")

        fig_pref_by_emo = go.Figure()
        for pv in grouped["chosen_prompt_version"].unique():
            pv_rows = grouped[grouped["chosen_prompt_version"] == pv]
            fig_pref_by_emo.add_trace(go.Bar(
                x=pv_rows["emotion_key"],
                y=pv_rows["count"],
                name=pv
            ))
        fig_pref_by_emo.update_layout(barmode="stack")
    apply_console_theme(fig_pref_by_emo, "RLHF • Preference by Emotion (Top 8)")

    # Feedback summary compact chart (optional)
    fig_feedback = go.Figure(data=[
        go.Bar(x=["Music 👍", "Music 👎"],
               y=[music_like, music_dislike],
               marker_color=[CYAN, PURPLE, BLUE, "rgba(255,255,255,0.35)"])
    ])
    apply_console_theme(fig_feedback, "User Feedback • Quick Summary")

    # ---- Layout ----
    dash_app.layout = dbc.Container([
        # NAVBAR
        dbc.Navbar(
            dbc.Container([
                html.A(
                    "← Back to Chat",
                    href="/",
                    className="btn btn-outline-secondary",
                    style={
                        "borderColor": "#00F5D4",
                        "color": "#00F5D4",
                        "fontFamily": "JetBrains Mono",
                        "textDecoration": "none"
                    }
                ),

                html.Div([
                    html.Div("EMOTIONFLOW", style={
                        "fontSize": "12px",
                        "letterSpacing": "4px",
                        "color": BLUE,
                        "fontFamily": "JetBrains Mono",
                        "marginBottom": "2px"
                    }),
                    html.Div("RLHF ALIGNMENT CONSOLE", style={
                        "fontSize": "22px",
                        "fontWeight": "700",
                        "color": CYAN,
                        "fontFamily": "Space Grotesk"
                    }),
                ], className="ms-3"),

                dbc.Badge(
                    "DEV_MODE" if DEV_MODE else "PROD",
                    style={"backgroundColor": PURPLE, "fontFamily": "JetBrains Mono"},
                    className="ms-auto"
                )
            ]),
            color=BG, dark=True,
            className="mb-4",
            style={"borderRadius": "16px", "border": f"1px solid {BORDER}"}
        ),

        # HERO KPIs
        dbc.Row([
            dbc.Col(kpi_card("TOTAL RLHF PAIRS", str(total_pairs), accent=CYAN, sub="preference_pairs"), md=3),
            dbc.Col(kpi_card("A WINS", str(a_wins), accent=BLUE, sub="prompt A selected"), md=3),
            dbc.Col(kpi_card("B WINS", str(b_wins), accent=PURPLE, sub="prompt B selected"), md=3),
            dbc.Col(kpi_card("B WIN-RATE", f"{win_rate_b*100:.1f}%", accent=CYAN, sub="higher is better (demo)"), md=3),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(kpi_card("MUSIC 👍 / 👎", f"{music_like} / {music_dislike}", accent=BLUE, sub="recommendation feedback"), md=6),
            dbc.Col(kpi_card("UNIQUE EMOTIONS", str(pref_df["emotion_key"].nunique() if not pref_df.empty else 0),
                            accent=CYAN, sub="coverage"), md=6),
        ], className="g-3 mb-4"),

        # MAIN CHARTS
        dbc.Row([
            dbc.Col(
                html.Div([dcc.Graph(figure=fig_ab)], style={
                    "backgroundColor": PANEL, "border": f"1px solid {BORDER}",
                    "borderRadius": "16px", "padding": "10px", "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                }),
                md=6
            ),
            dbc.Col(
                html.Div([dcc.Graph(figure=fig_pv)], style={
                    "backgroundColor": PANEL, "border": f"1px solid {BORDER}",
                    "borderRadius": "16px", "padding": "10px", "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                }),
                md=6
            ),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(
                html.Div([dcc.Graph(figure=fig_pref_by_emo)], style={
                    "backgroundColor": PANEL, "border": f"1px solid {BORDER}",
                    "borderRadius": "16px", "padding": "10px", "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                }),
                md=12
            ),
        ], className="g-3 mb-3"),

        dbc.Row([
            dbc.Col(
                html.Div([dcc.Graph(figure=fig_feedback)], style={
                    "backgroundColor": PANEL, "border": f"1px solid {BORDER}",
                    "borderRadius": "16px", "padding": "10px", "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                }),
                md=6
            ),
            dbc.Col(
                html.Div([dcc.Graph(figure=fig_emo)], style={
                    "backgroundColor": PANEL, "border": f"1px solid {BORDER}",
                    "borderRadius": "16px", "padding": "10px", "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                }),
                md=6
            ),
        ], className="g-3 mb-4"),

        # REWARD SLIDER (DEMO)
        html.Div([
            html.Div("REWARD SIGNAL (DEMO)", style={
                "fontFamily": "JetBrains Mono", "color": MUTED, "letterSpacing": "2px", "fontSize": "12px"
            }),
            html.Div("Simulated reward score", style={
                "fontFamily": "Space Grotesk", "color": CYAN, "fontSize": "18px", "fontWeight": "700",
                "marginTop": "4px"
            }),
            dcc.Slider(
                id='feedback-slider',
                min=0, max=10, step=1, value=5,
                marks={i: str(i) for i in range(11)}
            ),
            html.Div(id='reward-output', style={
                "marginTop": "12px",
                "textAlign": "center",
                "fontFamily": "JetBrains Mono",
                "color": CYAN,
                "fontSize": "18px",
                "fontWeight": "700"
            })
        ], style={
            "backgroundColor": PANEL,
            "border": f"1px solid {BORDER}",
            "borderRadius": "16px",
            "padding": "18px",
            "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
        }),

        html.Div("© EmotionFlow • RLHF demo dashboard", style={
            "color": MUTED, "fontFamily": "JetBrains Mono", "fontSize": "11px",
            "marginTop": "16px", "textAlign": "center", "opacity": 0.7
        })

    ], fluid=True, style={
        "backgroundColor": BG,
        "fontFamily": "Space Grotesk, sans-serif",
        "padding": "26px"
    })

    @dash_app.callback(
        Output('reward-output', 'children'),
        Input('feedback-slider', 'value')
    )
    def _reward_output(v):
        return f"Reward: {v}/10"

    return dash_app
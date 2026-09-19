import streamlit as st
import numpy as np
import joblib
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AQI Predictor Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "history" not in st.session_state:
    st.session_state.history = []

# ── City Data (pollutants pre-defined per city) ───────────────────────────────
CITY_DATA = {
    "🗼 Delhi":       {"PM2.5": 98.0,  "PM10": 215.0, "NO2": 65.0,  "SO2": 18.0, "CO": 2.1,  "O3": 45.0},
    "🌊 Mumbai":      {"PM2.5": 45.0,  "PM10": 95.0,  "NO2": 42.0,  "SO2": 12.0, "CO": 1.2,  "O3": 30.0},
    "🌿 Bangalore":   {"PM2.5": 35.0,  "PM10": 75.0,  "NO2": 38.0,  "SO2": 8.0,  "CO": 0.9,  "O3": 25.0},
    "🌴 Chennai":     {"PM2.5": 40.0,  "PM10": 85.0,  "NO2": 35.0,  "SO2": 10.0, "CO": 1.0,  "O3": 28.0},
    "🏛️ Kolkata":    {"PM2.5": 75.0,  "PM10": 145.0, "NO2": 55.0,  "SO2": 15.0, "CO": 1.8,  "O3": 38.0},
    "💎 Hyderabad":   {"PM2.5": 42.0,  "PM10": 88.0,  "NO2": 40.0,  "SO2": 11.0, "CO": 1.1,  "O3": 27.0},
    "🏔️ Pune":       {"PM2.5": 38.0,  "PM10": 80.0,  "NO2": 36.0,  "SO2": 9.0,  "CO": 1.0,  "O3": 26.0},
    "⚙️ Ahmedabad":  {"PM2.5": 65.0,  "PM10": 130.0, "NO2": 50.0,  "SO2": 14.0, "CO": 1.6,  "O3": 35.0},
    "🌺 Jaipur":      {"PM2.5": 70.0,  "PM10": 140.0, "NO2": 52.0,  "SO2": 13.0, "CO": 1.5,  "O3": 36.0},
    "🕌 Lucknow":     {"PM2.5": 90.0,  "PM10": 180.0, "NO2": 60.0,  "SO2": 17.0, "CO": 1.9,  "O3": 42.0},
    "🏙️ Patna":      {"PM2.5": 110.0, "PM10": 230.0, "NO2": 70.0,  "SO2": 20.0, "CO": 2.5,  "O3": 48.0},
    "🌾 Kanpur":      {"PM2.5": 120.0, "PM10": 250.0, "NO2": 75.0,  "SO2": 22.0, "CO": 2.8,  "O3": 50.0},
    "🌁 Surat":       {"PM2.5": 55.0,  "PM10": 110.0, "NO2": 44.0,  "SO2": 13.0, "CO": 1.3,  "O3": 32.0},
    "🏜️ Jodhpur":    {"PM2.5": 60.0,  "PM10": 125.0, "NO2": 48.0,  "SO2": 13.0, "CO": 1.4,  "O3": 33.0},
    "🌊 Visakhapatnam":{"PM2.5": 38.0, "PM10": 78.0,  "NO2": 36.0,  "SO2": 9.0,  "CO": 0.95, "O3": 26.0},
}

CITY_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Patna": (25.5941, 85.1376),
    "Kanpur": (26.4499, 80.3319),
    "Surat": (21.1702, 72.8311),
    "Jodhpur": (26.2389, 73.0243),
    "Visakhapatnam": (17.6868, 83.2185),
}

# ── AQI Category ─────────────────────────────────────────────────────────────
def aqi_category(val):
    if val <= 50:  return "Good",         "#00c853", "😊"
    if val <= 100: return "Satisfactory",  "#a8d500", "🙂"
    if val <= 200: return "Moderate",     "#ffd600", "😐"
    if val <= 300: return "Poor",         "#ff6d00", "😷"
    if val <= 400: return "Very Poor",    "#d50000", "🤧"
    return              "Severe",         "#7b00a8", "☠️"

HEALTH_ADVICE = {
    "Good":         ["✅ No precautions needed", "✅ Safe for everyone", "✅ Enjoy outdoor activities!"],
    "Satisfactory": ["⚠️ Sensitive groups: limit outdoor effort", "✅ General public safe", "💧 Stay hydrated"],
    "Moderate":     ["⚠️ Avoid prolonged outdoor exertion", "😷 Consider wearing a mask", "🏠 Keep windows slightly closed"],
    "Poor":         ["😷 Wear N95 mask outdoors", "🏠 Limit outdoor time", "💨 Use air purifier indoors"],
    "Very Poor":    ["🚫 Avoid all outdoor activity", "😷 N95 mask mandatory", "🏠 Keep all windows closed", "💨 Air purifier on full"],
    "Severe":       ["🚨 Stay indoors — emergency level", "😷 P100 mask if going out", "🏥 Seek medical help if unwell", "💨 Max air purifier usage"],
}

POLLUTANT_INFO = {
    "PM2.5": {"unit": "µg/m³", "safe": 30,  "emoji": "💨", "desc": "Fine Particles"},
    "PM10":  {"unit": "µg/m³", "safe": 50,  "emoji": "🌫️", "desc": "Coarse Particles"},
    "NO2":   {"unit": "µg/m³", "safe": 40,  "emoji": "🟡", "desc": "Nitrogen Dioxide"},
    "SO2":   {"unit": "µg/m³", "safe": 40,  "emoji": "🔴", "desc": "Sulphur Dioxide"},
    "CO":    {"unit": "mg/m³", "safe": 1.0, "emoji": "⚫", "desc": "Carbon Monoxide"},
    "O3":    {"unit": "µg/m³", "safe": 50,  "emoji": "🔵", "desc": "Ozone"},
}

# ── Plain-language guide for common people ────────────────────────────────────
POLLUTANT_PLAIN = {
    "PM2.5": {
        "plain_name": "Tiny Invisible Dust",
        "emoji": "💨",
        "source": "Car exhaust, factories, crop burning, Diwali crackers",
        "what": "Extremely tiny particles — 30× thinner than a human hair. You breathe them deep into lungs without knowing.",
        "why_bad": "Penetrate lungs & enter bloodstream, raising risk of heart disease, stroke, and lung cancer.",
        "mild": "Slight nose/throat irritation, sneezing",
        "high": "Persistent cough, wheezing, chest tightness",
        "severe": "Asthma attacks, heart complications, hospitalization",
        "safe": "Below 30 µg/m³",
    },
    "PM10": {
        "plain_name": "Visible Dust & Smoke Haze",
        "emoji": "🌫️",
        "source": "Construction sites, unpaved roads, dust storms, crop burning",
        "what": "Slightly larger particles that create the haze you sometimes see in the sky. Includes road dust, pollen, mold.",
        "why_bad": "Trapped in nose/throat; worsens allergies and respiratory conditions.",
        "mild": "Runny nose, sneezing, watery eyes",
        "high": "Sore throat, persistent cough, congestion",
        "severe": "Severe respiratory distress, especially in elderly & children",
        "safe": "Below 50 µg/m³",
    },
    "NO2": {
        "plain_name": "Traffic & Vehicle Exhaust Gas",
        "emoji": "🟡",
        "source": "Car/truck/bus exhaust, power plants, gas stoves",
        "what": "A brownish gas with a sharp smell formed when fuel burns. Very high near busy roads and traffic junctions.",
        "why_bad": "Inflames airways, worsens asthma & bronchitis, weakens lung capacity over time.",
        "mild": "Mild cough, eye & nose irritation",
        "high": "Worsening asthma, difficulty breathing after exertion",
        "severe": "Fluid in lungs, respiratory failure in extreme cases",
        "safe": "Below 40 µg/m³",
    },
    "SO2": {
        "plain_name": "Factory Smoke & Firecracker Gas",
        "emoji": "🔴",
        "source": "Coal power plants, oil refineries, Diwali firecrackers, diesel engines",
        "what": "A pungent invisible gas — the sharp smell you notice near factories or after firecrackers burst.",
        "why_bad": "Burns the lining of your nose, throat & lungs. Forms acid rain in the atmosphere.",
        "mild": "Burning/stinging sensation in nose and throat",
        "high": "Wheezing, chest tightness, shortness of breath",
        "severe": "Acute bronchitis, asthma emergency requiring hospitalization",
        "safe": "Below 40 µg/m³",
    },
    "CO": {
        "plain_name": "The Silent Invisible Gas",
        "emoji": "⚫",
        "source": "Vehicle exhaust, indoor gas/kerosene cooking, running generators, burning charcoal",
        "what": "Completely colorless & odorless — you cannot see, smell, or taste it. Produced whenever anything burns without enough oxygen.",
        "why_bad": "Replaces oxygen in blood, starving organs. Extremely dangerous in closed spaces like rooms or cars.",
        "mild": "Headache, slight dizziness, mild nausea",
        "high": "Severe headache, drowsiness, confusion, vomiting",
        "severe": "Loss of consciousness, organ damage, potentially fatal in enclosed spaces",
        "safe": "Below 1.0 mg/m³",
    },
    "O3": {
        "plain_name": "Afternoon Smog (Ground Ozone)",
        "emoji": "🔵",
        "source": "Vehicle fumes + strong sunlight — peaks on hot sunny afternoons (12–4 PM)",
        "what": "NOT the protective ozone layer above Earth. This forms at ground level from car exhaust + sunlight. Invisible but harmful, worst in summer afternoons.",
        "why_bad": "Irritates lungs like sunburn from inside. Reduces lung function. Worsens asthma significantly.",
        "mild": "Throat irritation, dry cough, mild headache",
        "high": "Chest pain, shortness of breath, worsened asthma",
        "severe": "Permanent lung damage with prolonged exposure",
        "safe": "Below 50 µg/m³",
    },
}

AQI_LEVEL_DETAILS = {
    "Good": {
        "range": "0 – 50", "color_word": "Green",
        "plain": "Air is clean and fresh. Breathe freely — no worries today! 🌿",
        "symptoms": "No symptoms expected for anyone, including sensitive groups.",
        "outdoor": "All outdoor activities freely — jogging, cycling, sports, picnics, morning walks!",
        "best_time": "🌅 Any time is great! Early morning (5–8 AM) air is freshest.",
        "worst_time": "None — excellent all day.",
        "children": "✅ Can play outdoors all day without any restriction.",
        "elderly": "✅ Enjoy full outdoor time comfortably.",
        "asthma": "✅ Asthma & heart patients can go out freely — great day for a walk!",
        "mask": "No mask needed 😊",
        "windows": "Open all windows — let the fresh air in!",
        "tip": "Today is perfect for a morning walk, park picnic, or letting kids play outside all day!",
    },
    "Satisfactory": {
        "range": "51 – 100", "color_word": "Yellow-Green",
        "plain": "Air quality is acceptable. Most people feel perfectly fine. 🙂",
        "symptoms": "Sensitive individuals (asthma, allergies) may feel very mild irritation.",
        "outdoor": "Fine for most people. Avoid intense exercise near busy roads.",
        "best_time": "🌅 Morning (6–9 AM) and late evening (after 9 PM) are cleanest.",
        "worst_time": "⚠️ Rush hours (8–10 AM, 5–8 PM) near busy roads — vehicle fumes peak.",
        "children": "✅ Can play outside. Avoid areas near heavy traffic.",
        "elderly": "✅ Fine outdoors. Avoid strenuous activity near highways.",
        "asthma": "⚠️ Carry your inhaler. Avoid high-traffic zones.",
        "mask": "No mask needed for most people 🙂",
        "windows": "Windows can remain open all day.",
        "tip": "A good day overall! Plan outdoor visits in the morning for the freshest air experience.",
    },
    "Moderate": {
        "range": "101 – 200", "color_word": "Yellow",
        "plain": "Noticeable pollution. Sensitive people feel irritation. General public may experience some discomfort. 😐",
        "symptoms": "Sensitive groups: eye irritation, cough, throat irritation. Others may feel mild breathing discomfort during heavy exercise.",
        "outdoor": "Limit prolonged strenuous activity. Short walks okay; avoid running or heavy sport outdoors.",
        "best_time": "🌅 Very early morning (5–7 AM) is the cleanest window of the day.",
        "worst_time": "⚠️ Afternoons (12–4 PM) when O3 peaks from heat + sunlight. Evening rush hours also bad.",
        "children": "⚠️ Limit outdoor playtime to under 1 hour. Prefer shaded areas away from roads.",
        "elderly": "⚠️ Prefer indoor activities. Short outdoor walks are okay but avoid exertion.",
        "asthma": "⚠️ Significantly limit outdoor time. Take prescribed medications before going out.",
        "mask": "😷 Sensitive groups should wear a surgical or N95 mask outdoors.",
        "windows": "Close windows during afternoon and rush hour periods.",
        "tip": "If you need to go outside, early morning is your best window. Asthma patients should keep inhalers handy.",
    },
    "Poor": {
        "range": "201 – 300", "color_word": "Orange",
        "plain": "Everyone may feel health effects. Stay indoors as much as possible. 😷",
        "symptoms": "Coughing, wheezing, burning eyes, headache, throat irritation for general public. Sensitive groups face serious breathing difficulty.",
        "outdoor": "Avoid ALL unnecessary outdoor activity. Only step out if absolutely essential.",
        "best_time": "🌅 Early morning (5–6 AM) is slightly less polluted — but wear N95 mask even then.",
        "worst_time": "⚠️ All day is concerning. Afternoons and rush hours are worst.",
        "children": "🚫 Keep children strictly indoors. No outdoor play today.",
        "elderly": "🚫 Must stay indoors. Monitor breathing regularly.",
        "asthma": "🚨 STAY INDOORS. Keep nebulizer and emergency medicines ready.",
        "mask": "😷 N95 mask ESSENTIAL for anyone going outdoors.",
        "windows": "Keep all windows tightly closed. Seal gaps if possible.",
        "tip": "Health-alert day. Cancel outdoor plans. Work from home if possible. Keep emergency medicines accessible.",
    },
    "Very Poor": {
        "range": "301 – 400", "color_word": "Red",
        "plain": "Serious health emergency. Everyone is at significant risk outdoors. 🤧",
        "symptoms": "Severe coughing fits, chest pain, shortness of breath, burning eyes, headaches. Can trigger asthma attacks and cardiac events.",
        "outdoor": "DO NOT go outdoors unless it is a medical emergency.",
        "best_time": "❌ There is NO good time to go outside today.",
        "worst_time": "❌ The entire day is dangerous for outdoor activity.",
        "children": "🚫 Must remain indoors 24/7. Schools should ideally close.",
        "elderly": "🚨 Critical risk. Keep oxygen/nebulizer ready. Monitor blood pressure closely.",
        "asthma": "🚨 Medical emergency risk. Stay on max air purifier. Have emergency contact ready.",
        "mask": "😷 N95/P100 mask MANDATORY — even for 5 minutes outside.",
        "windows": "Seal ALL windows and door gaps. Wet towels on gaps. Air purifier on maximum.",
        "tip": "HEALTH EMERGENCY. Postpone all travel. Chest pain or breathing difficulty = seek medical help immediately.",
    },
    "Severe": {
        "range": "400+", "color_word": "Maroon",
        "plain": "🚨 EMERGENCY LEVEL — Comparable to smoking several cigarettes just by being outside briefly.",
        "symptoms": "Severe respiratory distress, intense coughing, nausea, confusion. Brief outdoor exposure equals smoking multiple cigarettes.",
        "outdoor": "ABSOLUTE PROHIBITION — Do not step outside for any non-medical reason.",
        "best_time": "❌ AVOID ALL OUTDOOR ACTIVITY — no safe time exists today.",
        "worst_time": "❌ Entire day is a health emergency.",
        "children": "🚨 Keep in sealed indoor spaces. Avoid cooking smoke, incense, candles even indoors.",
        "elderly": "🚨 LIFE-THREATENING. 24/7 indoor rest, emergency contacts on speed dial.",
        "asthma": "🚨 CALL DOCTOR NOW. Do not wait for symptoms to worsen.",
        "mask": "😷 P100 respirator if stepping outside is unavoidable.",
        "windows": "Maximum sealing. Tape gaps. Multiple air purifiers. Avoid any indoor combustion.",
        "tip": "Declared health emergency level. All outdoor events must be cancelled. Seek medical attention for any breathing difficulty.",
    },
}

# ── Model Load ────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE, "model", "aqi_model.pkl")
IMP_PATH   = os.path.join(BASE, "model", "feature_importances.json")

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_importances():
    if os.path.exists(IMP_PATH):
        with open(IMP_PATH) as f:
            return json.load(f)
    return None

try:
    model       = load_model()
    importances = load_importances()
except Exception as e:
    st.error(f"❌ Model load failed: {e}")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css(dark):
    bg, card, text, border, muted, inp = (
        ("#0d1117","#161b22","#e6edf3","#30363d","#8b949e","#21262d") if dark else
        ("#f0f4f8","#ffffff","#1a202c","#d1d9e0","#718096","#ffffff")
    )
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family:'Inter',sans-serif !important; }}
    .stApp              {{ background:{bg} !important; color:{text} !important; }}
    .stSelectbox > div > div {{
        background:{inp} !important; color:{text} !important;
        border:2px solid {border} !important; border-radius:14px !important;
        font-size:16px !important; padding:4px 8px !important;
    }}
    .stSelectbox label  {{ color:{muted} !important; font-weight:600 !important; font-size:13px !important; }}
    .stButton > button  {{
        background:linear-gradient(135deg,#0072ff,#00c6ff) !important;
        color:white !important; border:none !important; border-radius:12px !important;
        padding:12px 0 !important; font-size:16px !important; font-weight:700 !important;
        width:100% !important; transition:all 0.25s ease !important;
    }}
    .stButton > button:hover {{ transform:translateY(-2px) !important; box-shadow:0 10px 30px rgba(0,114,255,0.4) !important; }}
    .block-container    {{ padding-top:1.8rem !important; padding-bottom:2rem !important; }}
    hr                  {{ border-color:{border} !important; margin:18px 0 !important; }}
    h1,h2,h3            {{ color:{text} !important; font-weight:700 !important; }}
    .stat-card {{
        background:{card}; border:1px solid {border}; border-radius:14px;
        padding:16px 18px; text-align:center;
    }}
    .poll-val   {{ font-size:24px; font-weight:800; }}
    .poll-label {{ font-size:12px; color:{muted}; margin-top:2px; }}
    .stDataFrame {{ border-radius:14px; overflow:hidden; }}
    </style>
    """, unsafe_allow_html=True)

inject_css(st.session_state.dark_mode)

dark       = st.session_state.dark_mode
chart_bg   = "#161b22" if dark else "#ffffff"
chart_font = "#e6edf3" if dark else "#1a202c"
grid_color = "#30363d" if dark else "#e2e8f0"
card_color = "#161b22" if dark else "#ffffff"
border_col = "#30363d" if dark else "#d1d9e0"
muted_col  = "#8b949e" if dark else "#718096"

# ── Charts ────────────────────────────────────────────────────────────────────
def make_gauge(aqi_val, cat, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi_val,
        number={"font": {"size": 56, "color": color, "family": "Inter"}},
        title={"text": f"<b>{cat}</b>", "font": {"size": 22, "color": color}},
        gauge={
            "axis": {"range": [0, 500], "tickwidth": 1, "tickcolor": chart_font,
                     "tickfont": {"color": chart_font}},
            "bar": {"color": color, "thickness": 0.22},
            "bgcolor": chart_bg, "borderwidth": 0,
            "steps": [
                {"range": [0,   50],  "color": "rgba(0,200,83,0.15)"},
                {"range": [50,  100], "color": "rgba(174,234,0,0.15)"},
                {"range": [100, 200], "color": "rgba(255,214,0,0.15)"},
                {"range": [200, 300], "color": "rgba(255,109,0,0.15)"},
                {"range": [300, 400], "color": "rgba(213,0,0,0.15)"},
                {"range": [400, 500], "color": "rgba(106,0,128,0.15)"},
            ],
        },
    ))
    fig.update_layout(paper_bgcolor=chart_bg, font=dict(color=chart_font, family="Inter"),
                      height=300, margin=dict(l=20, r=20, t=20, b=10))
    return fig

def make_radar(vals):
    labels = list(vals.keys())
    maxes  = [500, 600, 400, 200, 50, 300]
    norm   = [round(min(v / m * 100, 100), 1) for v, m in zip(vals.values(), maxes)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=norm + [norm[0]], theta=labels + [labels[0]],
        fill="toself", fillcolor="rgba(0,114,255,0.15)",
        line=dict(color="#0072ff", width=2.5),
        marker=dict(size=7, color="#00c6ff"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=chart_bg,
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=grid_color,
                            tickfont=dict(color=chart_font)),
            angularaxis=dict(gridcolor=grid_color, tickfont=dict(color=chart_font, size=13)),
        ),
        paper_bgcolor=chart_bg, font=dict(color=chart_font, family="Inter"),
        showlegend=False, height=360, margin=dict(l=50, r=50, t=30, b=30),
    )
    return fig

def make_importance(imp_dict):
    items = sorted(imp_dict.items(), key=lambda x: x[1])
    feats, vals = zip(*items)
    colors = ["#4cc9f0","#4361ee","#3a0ca3","#7209b7","#f72585","#0072ff"]
    fig = go.Figure(go.Bar(
        x=list(vals), y=list(feats), orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v*100:.1f}%" for v in vals], textposition="outside",
        textfont=dict(color=chart_font),
    ))
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor=grid_color, tickformat=".0%",
                   tickfont=dict(color=chart_font), range=[0, max(vals)*1.28]),
        yaxis=dict(tickfont=dict(color=chart_font, size=13)),
        paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
        font=dict(color=chart_font, family="Inter"),
        height=320, margin=dict(l=10, r=70, t=20, b=10),
    )
    return fig

def make_bar_pollutants(vals, color):
    """Bar chart comparing each pollutant against its safe limit."""
    labels, measured, safe_vals, pct = [], [], [], []
    for poll, v in vals.items():
        info = POLLUTANT_INFO[poll]
        labels.append(poll)
        measured.append(v)
        safe_vals.append(info["safe"])
        pct.append(round(v / info["safe"] * 100, 1))

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Safe Limit", x=labels, y=safe_vals,
                         marker_color="rgba(100,200,100,0.25)",
                         marker_line=dict(color="rgba(100,200,100,0.8)", width=1.5)))
    
    # Convert hex color to rgba for marker_color to avoid Plotly ValueError
    h = color.lstrip('#')
    rgba_color = f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, 0.8)"
    
    fig.add_trace(go.Bar(name="Measured", x=labels, y=measured,
                         marker_color=rgba_color,
                         marker_line=dict(color=color, width=1.5),
                         text=[f"{v}" for v in measured],
                         textposition="outside", textfont=dict(color=chart_font)))
    fig.update_layout(
        barmode="overlay",
        xaxis=dict(tickfont=dict(color=chart_font, size=13), gridcolor=grid_color),
        yaxis=dict(tickfont=dict(color=chart_font), gridcolor=grid_color),
        paper_bgcolor=chart_bg, plot_bgcolor=chart_bg,
        font=dict(color=chart_font, family="Inter"),
        legend=dict(font=dict(color=chart_font), bgcolor=chart_bg),
        height=320, margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig

import random

def make_city_heatmap(city_name, base_aqi, dark):
    if city_name not in CITY_COORDS:
        city_name = "Delhi"
    lat, lon = CITY_COORDS[city_name]
    
    # Generate dummy zones
    zones = ["North", "South", "East", "West", "Central", "Industrial Area", "Residential", "Commercial", "City Center"]
    
    lats = [lat + random.uniform(-0.08, 0.08) for _ in range(8)] + [lat]
    lons = [lon + random.uniform(-0.08, 0.08) for _ in range(8)] + [lon]
    
    # Dummy AQI, Temp, Humidity
    aqis = [max(10, base_aqi + random.uniform(-50, 80)) for _ in range(9)]
    temps = [random.uniform(25, 38) for _ in range(9)]
    humids = [random.uniform(40, 80) for _ in range(9)]
    
    hover_text = []
    for i in range(9):
        hover_text.append(f"<b>{zones[i]}</b><br>AQI: {int(aqis[i])}<br>Temp: {temps[i]:.1f}°C<br>Humidity: {humids[i]:.0f}%")
        
    fig = go.Figure(go.Densitymapbox(
        lat=lats, lon=lons, z=aqis, radius=40,
        colorscale="RdYlGn_r", zmin=0, zmax=500,
        text=hover_text, hoverinfo="text"
    ))
    
    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter" if dark else "carto-positron",
            center=dict(lat=lat, lon=lon),
            zoom=10
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        paper_bgcolor=chart_bg,
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown("# 🌍 AQI Predictor Pro")
    st.markdown(f'<p style="color:{muted_col}; font-size:14px;">AI-powered · CPCB Standard · Instant Analysis — just select your city!</p>', unsafe_allow_html=True)
with h2:
    st.markdown("<br>", unsafe_allow_html=True)
    dm = st.checkbox("🌙 Dark Mode", value=dark)
    if dm != dark:
        st.session_state.dark_mode = dm
        st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# CITY SELECTOR — the ONLY input the user sees
# ─────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.markdown(f'<h3 style="text-align:center; margin-bottom:6px;">📍 Select Your Location</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center; color:{muted_col}; font-size:14px; margin-bottom:12px;">Choose a city — full AQI analysis loads automatically</p>', unsafe_allow_html=True)
    city = st.selectbox("", list(CITY_DATA.keys()), label_visibility="collapsed")

    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# AUTO PREDICTION (no button needed — runs immediately on city select)
# ─────────────────────────────────────────────────────────────────────────────
d     = CITY_DATA[city]
pm25  = d["PM2.5"]; pm10 = d["PM10"]; no2 = d["NO2"]
so2   = d["SO2"];   co   = d["CO"];   o3  = d["O3"]

inp = np.array([[pm25, pm10, no2, so2, co, o3]])
aqi = float(model.predict(inp)[0])
cat, color, emoji = aqi_category(aqi)

# Save to history (only if city changed since last entry)
last = st.session_state.history[-1] if st.session_state.history else {}
if not last or last.get("City") != city.split(" ",1)[-1]:
    st.session_state.history.append({
        "Time":     datetime.now().strftime("%H:%M:%S"),
        "City":     city.split(" ",1)[-1],
        "PM2.5":    pm25, "PM10": pm10, "NO2": no2,
        "SO2":      so2,  "CO":   co,   "O3":  o3,
        "AQI":      round(aqi, 1),
        "Category": f"{emoji} {cat}",
    })

city_name = city.split(" ", 1)[-1]

# ── Section: City title ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; margin-bottom:10px;">
    <span style="font-size:40px;">{emoji}</span>
    <h2 style="font-size:28px; font-weight:800; margin:4px 0;">{city_name}</h2>
    <span style="
        background:{color}22; border:1.5px solid {color};
        border-radius:20px; padding:4px 18px;
        font-size:14px; font-weight:600; color:{color};
    ">{cat} · AQI {aqi:.1f}</span>
</div>
""", unsafe_allow_html=True)

# ── Row 1: Gauge + Health Card ────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("### 🎯 AQI Gauge")
    st.plotly_chart(make_gauge(round(aqi, 1), cat, color), use_container_width=True)

with col2:
    st.markdown("### 🏥 Health Status")
    tips = HEALTH_ADVICE[cat]
    tips_html = "".join([
        f'<div style="background:{color}14; border-left:3px solid {color}; '
        f'border-radius:8px; padding:10px 14px; margin:6px 0; '
        f'font-size:13px; font-weight:500; color:{chart_font};">{t}</div>'
        for t in tips
    ])
    st.markdown(f"""
    <div style="
        background:{color}12; border:2px solid {color};
        border-radius:18px; padding:20px 20px 14px; margin-top:4px;
    ">
        <div style="text-align:center; font-size:52px; margin-bottom:4px;">{emoji}</div>
        <div style="text-align:center; font-size:24px; font-weight:800; color:{color};">{cat}</div>
        <div style="text-align:center; font-size:40px; font-weight:900; color:{color}; margin:4px 0;">AQI {aqi:.1f}</div>
        <hr style="border-color:{color}33; margin:12px 0;">
        {tips_html}
    </div>
    """, unsafe_allow_html=True)

# ── NEW: Comprehensive Plain-Language Health Advisory ────────────────────────
st.markdown("---")
lvl = AQI_LEVEL_DETAILS[cat]
st.markdown("### 🧑‍⚕️ What This Means for YOU — In Plain Language")
st.markdown(
    f'<p style="color:{muted_col};font-size:14px;margin-top:-8px;">'
    f'Based on current AQI <b>{aqi:.1f}</b> ({cat}) in <b>{city_name}</b> — explained simply, no jargon.</p>',
    unsafe_allow_html=True,
)

# Big plain summary banner
st.markdown(f"""
<div style="background:{color}18;border:2px solid {color}66;border-radius:18px;padding:20px 24px;margin-bottom:14px;">
  <div style="font-size:26px;font-weight:800;color:{color};margin-bottom:6px;">{emoji} {cat} &nbsp;·&nbsp; AQI Range {lvl['range']}</div>
  <div style="font-size:15px;line-height:1.7;color:{chart_font};">{lvl['plain']}</div>
</div>
""", unsafe_allow_html=True)

# 2-column grid: symptoms + outdoor advice
ha1, ha2 = st.columns(2)
with ha1:
    st.markdown(f"""
    <div style="background:{card_color};border:1px solid {border_col};border-radius:14px;padding:16px;height:100%;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">🤒 POSSIBLE SYMPTOMS</div>
      <div style="font-size:14px;color:{chart_font};line-height:1.6;">{lvl['symptoms']}</div>
      <hr style="border-color:{border_col};margin:12px 0;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">😷 MASK RECOMMENDATION</div>
      <div style="font-size:14px;color:{chart_font};">{lvl['mask']}</div>
      <hr style="border-color:{border_col};margin:12px 0;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">🪟 WINDOWS & VENTILATION</div>
      <div style="font-size:14px;color:{chart_font};">{lvl['windows']}</div>
    </div>
    """, unsafe_allow_html=True)

with ha2:
    st.markdown(f"""
    <div style="background:{card_color};border:1px solid {border_col};border-radius:14px;padding:16px;height:100%;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">🏃 OUTDOOR ACTIVITY</div>
      <div style="font-size:14px;color:{chart_font};line-height:1.6;">{lvl['outdoor']}</div>
      <hr style="border-color:{border_col};margin:12px 0;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">✅ BEST TIME TO GO OUTSIDE</div>
      <div style="font-size:14px;color:{chart_font};">{lvl['best_time']}</div>
      <hr style="border-color:{border_col};margin:12px 0;">
      <div style="font-size:13px;font-weight:700;color:{muted_col};letter-spacing:.05em;margin-bottom:8px;">⛔ AVOID GOING OUT DURING</div>
      <div style="font-size:14px;color:{chart_font};">{lvl['worst_time']}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

# 3-column group guidance
hb1, hb2, hb3 = st.columns(3)
group_cards = [
    ("👶 CHILDREN",   lvl["children"]),
    ("👴 ELDERLY",    lvl["elderly"]),
    ("🫁 ASTHMA / HEART PATIENTS", lvl["asthma"]),
]
for col_obj, (title, text) in zip([hb1, hb2, hb3], group_cards):
    with col_obj:
        st.markdown(f"""
        <div style="background:{color}12;border:1.5px solid {color}55;border-radius:14px;padding:14px;">
          <div style="font-size:12px;font-weight:700;color:{color};letter-spacing:.05em;margin-bottom:6px;">{title}</div>
          <div style="font-size:13px;color:{chart_font};line-height:1.55;">{text}</div>
        </div>
        """, unsafe_allow_html=True)

# Pro tip banner
st.markdown(f"""
<div style="background:linear-gradient(135deg,{color}22,{color}08);border-left:4px solid {color};
border-radius:0 12px 12px 0;padding:14px 18px;margin-top:14px;">
  <span style="font-size:13px;font-weight:700;color:{color};">💡 TODAY'S TIP &nbsp;</span>
  <span style="font-size:13px;color:{chart_font};">{lvl['tip']}</span>
</div>
""", unsafe_allow_html=True)

# ── Row 2: Pollutant Value Cards ──────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔬 Pollutant Breakdown (Used for Prediction)")
pc = st.columns(6)
for i, (poll, val) in enumerate(d.items()):
    info  = POLLUTANT_INFO[poll]
    ratio = val / info["safe"]
    p_col = "#00c853" if ratio < 1 else ("#ffd600" if ratio < 2 else "#d50000")
    with pc[i]:
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size:22px;">{info['emoji']}</div>
            <div class="poll-val" style="color:{p_col};">{val}</div>
            <div class="poll-label">{poll}</div>
            <div class="poll-label">{info['unit']}</div>
            <div style="font-size:10px; color:{p_col}; font-weight:600; margin-top:4px;">
                {'✅ Safe' if ratio < 1 else f'⚠️ {ratio:.1f}x limit'}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── NEW: Plain-Language Pollutant Explainer ──────────────────────────────────
st.markdown("---")
st.markdown("### 📖 What Are These Gases? — Simple Explanations for Everyone")
st.markdown(
    f'<p style="color:{muted_col};font-size:14px;margin-top:-8px;">'
    'No science degree needed — here is what each pollutant actually is, where it comes from, and how it affects your body.</p>',
    unsafe_allow_html=True,
)

poll_tabs = st.tabs([f"{POLLUTANT_PLAIN[p]['emoji']} {p}" for p in POLLUTANT_PLAIN])
for tab, (poll, info) in zip(poll_tabs, POLLUTANT_PLAIN.items()):
    cur_val  = d[poll]
    safe_num = POLLUTANT_INFO[poll]["safe"]
    ratio    = cur_val / safe_num
    p_col    = "#00c853" if ratio < 1 else ("#ffd600" if ratio < 2 else "#d50000")
    status   = "✅ Within safe limit" if ratio < 1 else (f"⚠️ {ratio:.1f}× over safe limit" if ratio < 2 else f"🚨 {ratio:.1f}× over safe limit — HIGH")
    with tab:
        r1, r2 = st.columns([3, 2])
        with r1:
            st.markdown(f"""
            <div style="background:{card_color};border:1px solid {border_col};border-radius:14px;padding:18px;">
              <div style="font-size:20px;font-weight:800;color:{chart_font};margin-bottom:4px;">
                {info['emoji']} {poll} &nbsp;<span style="font-size:14px;font-weight:500;color:{muted_col};">{info['plain_name']}</span>
              </div>
              <div style="font-size:13px;font-weight:600;color:{muted_col};margin:10px 0 4px;">🔍 WHAT IS IT?</div>
              <div style="font-size:14px;color:{chart_font};line-height:1.65;">{info['what']}</div>
              <div style="font-size:13px;font-weight:600;color:{muted_col};margin:12px 0 4px;">🏭 WHERE DOES IT COME FROM?</div>
              <div style="font-size:14px;color:{chart_font};">{info['source']}</div>
              <div style="font-size:13px;font-weight:600;color:{muted_col};margin:12px 0 4px;">⚠️ WHY IS IT HARMFUL?</div>
              <div style="font-size:14px;color:{chart_font};line-height:1.65;">{info['why_bad']}</div>
            </div>
            """, unsafe_allow_html=True)
        with r2:
            st.markdown(f"""
            <div style="background:{card_color};border:1px solid {border_col};border-radius:14px;padding:18px;margin-bottom:12px;">
              <div style="font-size:13px;font-weight:700;color:{muted_col};margin-bottom:10px;">📍 CURRENT LEVEL IN {city_name.upper()}</div>
              <div style="font-size:36px;font-weight:900;color:{p_col};">{cur_val} <span style="font-size:14px;font-weight:500;color:{muted_col};">{POLLUTANT_INFO[poll]['unit']}</span></div>
              <div style="font-size:12px;color:{p_col};font-weight:600;margin-top:4px;">{status}</div>
              <div style="font-size:12px;color:{muted_col};margin-top:6px;">Safe limit: {info['safe']}</div>
            </div>
            <div style="background:{card_color};border:1px solid {border_col};border-radius:14px;padding:18px;">
              <div style="font-size:13px;font-weight:700;color:{muted_col};margin-bottom:10px;">🤒 HOW IT FEELS (BY LEVEL)</div>
              <div style="font-size:12px;font-weight:600;color:#00c853;margin-bottom:2px;">🟢 LOW EXPOSURE</div>
              <div style="font-size:13px;color:{chart_font};margin-bottom:8px;">{info['mild']}</div>
              <div style="font-size:12px;font-weight:600;color:#ffd600;margin-bottom:2px;">🟡 HIGH EXPOSURE</div>
              <div style="font-size:13px;color:{chart_font};margin-bottom:8px;">{info['high']}</div>
              <div style="font-size:12px;font-weight:600;color:#d50000;margin-bottom:2px;">🔴 VERY HIGH / PROLONGED</div>
              <div style="font-size:13px;color:{chart_font};">{info['severe']}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Row 3: Radar + Pollutant Bar Chart ───────────────────────────────────────
st.markdown("---")
col3, col4 = st.columns(2)
with col3:
    st.markdown("### 🕸️ Pollutant Radar Chart")
    st.caption("Each pollutant as % of its maximum safe limit")
    st.plotly_chart(make_radar(d), use_container_width=True)

with col4:
    st.markdown("### 📊 Measured vs Safe Limit")
    st.caption("Blue bar = measured · Green overlay = safe limit")
    st.plotly_chart(make_bar_pollutants(d, color), use_container_width=True)

# ── Row 4: Heat Sink Map ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗺️ City Heat Sink Map")
st.caption("Live simulated heat map showing Temperature, Humidity, and Pollution hotspots across the city.")

hm_fig = make_city_heatmap(city_name, aqi, dark)
st.plotly_chart(hm_fig, use_container_width=True)

# ── Row 5: Feature Importance ─────────────────────────────────────────────────
if importances:
    st.markdown("---")
    st.markdown("### 🤖 What Drives AQI? — Feature Importance")
    st.caption("How much each pollutant influences the ML model's AQI prediction")
    st.plotly_chart(make_importance(importances), use_container_width=True)

# ── Prediction History ────────────────────────────────────────────────────────
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📋 City Comparison History")
    df_hist = pd.DataFrame(st.session_state.history)
    st.dataframe(
        df_hist.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
        use_container_width=True,
        hide_index=True,
    )
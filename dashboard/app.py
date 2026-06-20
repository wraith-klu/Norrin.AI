"""
dashboard/app.py
Elite Player Performance Predictor — Premium Streamlit Dashboard.
Tab 1: Real-Time Cricket Predictor (live web scraping + OpenRouter LLM)
Tab 2: Offline ML Models (historical data + scikit-learn ensemble)
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── env loader (no dotenv dependency) ────────────────────────────────────────
def _load_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_env()

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Norrin.AI — Sport Predictor Agent",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Google Fonts + Premium CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── global reset ── */
html, body, [class*="css"], .stMarkdown, .stText,
button, input, select, textarea { 
    font-family: 'Outfit', sans-serif !important; 
    color: #1a1a2e !important;
}

/* ── pure white background ── */
.stApp {
    background: #ffffff !important;
}
.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

/* ── NORRIN.AI hero header ── */
.hero {
    background: linear-gradient(135deg, 
        #16a34a 0%,
        #7c3aed 45%,
        #dc2626 100%
    ) !important;
    border-radius: 28px;
    padding: 52px 56px;
    margin-bottom: 36px;
    border: none;
    box-shadow: 
        0 20px 60px rgba(124, 58, 237, 0.25),
        0 8px 30px rgba(22, 163, 74, 0.15),
        inset 0 1px 1px rgba(255,255,255,0.15);
    position: relative; overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background: 
        radial-gradient(ellipse at 10% 50%, rgba(22, 163, 74, 0.3) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 20%, rgba(220, 38, 38, 0.25) 0%, transparent 45%),
        radial-gradient(ellipse at 50% 100%, rgba(124, 58, 237, 0.4) 0%, transparent 60%);
    pointer-events: none;
}
.hero::after {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 320px; height: 320px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    pointer-events: none;
}
.hero-inner {
    position: relative; z-index: 1;
}
.hero-eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 100px; padding: 6px 18px;
    font-size: 0.75rem; font-weight: 700;
    color: rgba(255,255,255,0.9) !important;
    letter-spacing: 0.12em; text-transform: uppercase;
    margin-bottom: 20px;
}
.hero-title {
    font-size: 3.4rem; font-weight: 900; margin: 0 0 6px;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.03em;
    line-height: 1.05;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff;
}
.hero-title .brand-green { color: #4ade80 !important; -webkit-text-fill-color: #4ade80; }
.hero-title .brand-purple { color: #c4b5fd !important; -webkit-text-fill-color: #c4b5fd; }
.hero-title .brand-red { color: #fca5a5 !important; -webkit-text-fill-color: #fca5a5; }
.hero-subtitle {
    font-size: 0.85rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: rgba(255,255,255,0.65) !important;
    margin-bottom: 16px;
}
.hero-sub {
    font-size: 1.1rem; font-weight: 400;
    color: rgba(255,255,255,0.8) !important;
    max-width: 620px; line-height: 1.65;
}
.hero-badges {
    display: flex; flex-wrap: wrap; gap: 10px;
    margin-top: 28px;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    border-radius: 100px; padding: 8px 18px;
    font-size: 0.8rem; font-weight: 600;
    color: rgba(255,255,255,0.95) !important;
    transition: all 0.2s ease;
}
.hero-badge:hover {
    background: rgba(255,255,255,0.2);
    transform: translateY(-1px);
}
.hero-stats {
    display: flex; gap: 32px; margin-top: 36px;
    padding-top: 28px;
    border-top: 1px solid rgba(255,255,255,0.12);
}
.hero-stat-val {
    font-size: 1.8rem; font-weight: 900;
    color: #ffffff !important; line-height: 1;
    font-family: 'Space Grotesk', sans-serif !important;
}
.hero-stat-lbl {
    font-size: 0.75rem; font-weight: 600;
    color: rgba(255,255,255,0.55) !important;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-top: 4px;
}

/* ── Section header strip ── */
.section-header {
    display: flex; align-items: center; gap: 12px;
    margin: 32px 0 20px;
}
.section-header-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(124,58,237,0.15), transparent);
}
.section-header-title {
    font-size: 0.75rem; font-weight: 800;
    color: #7c3aed !important;
    text-transform: uppercase; letter-spacing: 0.12em;
}

/* ── glass card ── */
.glass-card {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.07);
    border-radius: 20px; padding: 28px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 20px;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.glass-card:hover {
    border-color: rgba(124, 58, 237, 0.18);
    box-shadow: 0 12px 40px rgba(124, 58, 237, 0.08);
    transform: translateY(-2px);
}

/* ── input group card ── */
.input-group-card {
    background: #fafafa;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 18px;
    padding: 22px 24px 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-group-card:hover {
    border-color: rgba(124,58,237,0.2);
    box-shadow: 0 4px 20px rgba(124,58,237,0.06);
}

/* ── squad card ── */
.squad-card {
    background: linear-gradient(135deg, #ffffff 0%, #fbf9ff 100%) !important;
    border: 1px solid rgba(124, 58, 237, 0.12) !important;
    border-left: 5px solid #7c3aed !important;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 4px 24px rgba(124, 58, 237, 0.05), 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 24px;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.squad-card:hover {
    border-color: rgba(124, 58, 237, 0.3) !important;
    box-shadow: 0 12px 40px rgba(124, 58, 237, 0.09) !important;
    transform: translateY(-2px);
}

/* ── manual card ── */
.manual-card {
    background: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.07) !important;
    border-left: 5px solid #64748b !important;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0,0,0,0.03);
    margin-bottom: 24px;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}
.manual-card:hover {
    border-color: rgba(0, 0, 0, 0.12) !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.06) !important;
    transform: translateY(-2px);
}

.card-heading {
    font-size: 0.7rem; font-weight: 800;
    color: #7c3aed !important;
    text-transform: uppercase; letter-spacing: 0.12em;
    padding-bottom: 12px; margin-bottom: 14px;
    border-bottom: 2px solid rgba(124, 58, 237, 0.1);
    display: flex; align-items: center; gap: 8px;
}

/* ── Streamlit input styling overrides ── */
.stTextInput > label, .stSelectbox > label, .stDateInput > label,
.stNumberInput > label, .stSlider > label, .stRadio > label {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #64748b !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 6px !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input, div[data-baseweb="select"] {
    background-color: #ffffff !important;
    border: 1.5px solid rgba(0, 0, 0, 0.1) !important;
    border-radius: 12px !important;
    color: #0f172a !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 10px 16px !important;
    font-size: 0.95rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.stTextInput input:hover, .stNumberInput input:hover, div[data-baseweb="select"]:hover {
    border-color: rgba(124, 58, 237, 0.35) !important;
}
.stTextInput input:focus, .stNumberInput input:focus, div[data-baseweb="select"]:focus-within {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
    background-color: #ffffff !important;
}

/* Fix Streamlit baseweb background issues */
div[data-baseweb="input"] {
    background-color: transparent !important;
    border: none !important;
}
div[data-baseweb="select"] > div {
    background-color: transparent !important;
}
div[data-baseweb="select"] span {
    color: #0f172a !important;
}

/* ── Custom tabs styling ── */
div[data-testid="stTabs"] {
    margin-bottom: 28px !important;
}
div[data-testid="stTabs"] [role="tablist"] {
    background: #f8f9fc !important;
    border-radius: 14px !important;
    padding: 6px !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
    gap: 4px !important;
}
div[data-testid="stTabs"] button[data-testid="stTab"] {
    color: #64748b !important;
    background: transparent !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTabs"] button[data-testid="stTab"][aria-selected="true"] {
    color: #7c3aed !important;
    background: #ffffff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
    font-weight: 700 !important;
}
div[data-testid="stTabs"] button[data-testid="stTab"]:hover:not([aria-selected="true"]) {
    color: #4f46e5 !important;
    background: rgba(255,255,255,0.6) !important;
}

/* ── primary button ── */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #16a34a 0%, #7c3aed 50%, #dc2626 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    padding: 14px 32px !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 35px rgba(124, 58, 237, 0.4) !important;
}
div.stButton > button[kind="primary"]:active {
    transform: translateY(-1px) !important;
}

/* ── step tracker list ── */
.log-container {
    background: #ffffff !important;
    border: 1px solid rgba(124, 58, 237, 0.12) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    margin: 20px 0 !important;
    box-shadow: 0 10px 30px rgba(124, 58, 237, 0.05) !important;
}
.log-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 18px;
    margin-bottom: 10px;
    border-radius: 12px;
    background: transparent;
    border: 1px solid rgba(0, 0, 0, 0.03);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.log-item:last-child { margin-bottom: 0; }
.log-item.done {
    background: rgba(22, 163, 74, 0.03) !important;
    border: 1px solid rgba(22, 163, 74, 0.1) !important;
}
.log-item.active {
    background: rgba(124, 58, 237, 0.04) !important;
    border: 1px solid rgba(124, 58, 237, 0.18) !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.05) !important;
    animation: activeItemPulse 2.5s infinite ease-in-out;
}
@keyframes activeItemPulse {
    0%, 100% { background: rgba(124, 58, 237, 0.04) !important; border-color: rgba(124, 58, 237, 0.18) !important; }
    50% { background: rgba(124, 58, 237, 0.08) !important; border-color: rgba(124, 58, 237, 0.3) !important; }
}

/* Circle Icon Styling */
.log-icon-container {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    flex-shrink: 0;
}
.log-icon-circle {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    color: #ffffff !important;
    font-weight: bold;
    z-index: 2;
    transition: all 0.3s ease;
}
.log-icon-circle.done {
    background: linear-gradient(135deg, #16a34a, #10b981) !important;
    box-shadow: 0 0 8px rgba(22, 163, 74, 0.4);
}
.log-icon-circle.active {
    background: linear-gradient(135deg, #7c3aed, #db2777) !important;
    box-shadow: 0 0 10px rgba(124, 58, 237, 0.5);
    animation: pulseInnerCircle 1.5s infinite alternate;
}
@keyframes pulseInnerCircle {
    0% { transform: scale(1); }
    100% { transform: scale(1.1); }
}

/* Pulsing outer rings for active item */
.log-icon-container.active::before {
    content: "";
    position: absolute;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: #7c3aed;
    border-bottom-color: #db2777;
    animation: spinLoader 1.5s linear infinite;
    z-index: 1;
}
.log-icon-container.active::after {
    content: "";
    position: absolute;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    border: 1px solid rgba(124, 58, 237, 0.3);
    animation: ringPulse 1.8s infinite ease-out;
    z-index: 0;
    opacity: 0;
}
@keyframes ringPulse {
    0% { transform: scale(0.8); opacity: 0.8; }
    100% { transform: scale(1.3); opacity: 0; }
}

@keyframes spinLoader {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.log-text {
    font-size: 0.95rem; font-weight: 500; color: #475569 !important;
}
.log-text.done { color: #1e293b !important; font-weight: 600; }
.log-text.active { color: #0f172a !important; font-weight: 700; }

/* ── stat boxes ── */
.stat-row { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 20px; }
.stat-box {
    flex: 1; min-width: 140px;
    background: #ffffff;
    border-radius: 16px; padding: 20px 22px;
    border: 1px solid rgba(0,0,0,0.07);
    border-top: 4px solid #7c3aed;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.stat-box:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.stat-box.green { border-top-color: #16a34a; }
.stat-box.amber { border-top-color: #d97706; }
.stat-box.red   { border-top-color: #dc2626; }
.stat-lbl {
    font-size: .7rem; font-weight: 800; color: #94a3b8 !important;
    text-transform: uppercase; letter-spacing: .1em;
}
.stat-val {
    font-size: 1.65rem; font-weight: 900; color: #0f172a !important;
    margin-top: 8px; line-height: 1.1;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stat-val.sm { font-size: 1.05rem; padding-top: 8px; font-weight: 700; }

/* ── pill tags ── */
.pill-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 16px; }
.pill {
    padding: 5px 14px; border-radius: 100px; font-size: .8rem; font-weight: 700;
    transition: all 0.2s ease;
}
.pill:hover { transform: scale(1.06); }
.pill-green {
    background: rgba(22, 163, 74, 0.08); color: #15803d !important;
    border: 1px solid rgba(22, 163, 74, 0.2);
}
.pill-red {
    background: rgba(220, 38, 38, 0.08); color: #b91c1c !important;
    border: 1px solid rgba(220, 38, 38, 0.2);
}
.pill-amber {
    background: rgba(217, 119, 6, 0.08); color: #92400e !important;
    border: 1px solid rgba(217, 119, 6, 0.2);
}

/* ── tagline banner ── */
.tagline {
    background: linear-gradient(135deg, rgba(22,163,74,0.05) 0%, rgba(124,58,237,0.05) 50%, rgba(220,38,38,0.04) 100%);
    border: 1px solid rgba(124, 58, 237, 0.12); border-radius: 16px;
    padding: 20px 28px; text-align: center;
    font-size: 1.2rem; font-weight: 600; color: #4338ca !important;
    margin-bottom: 28px; font-style: italic;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
}

/* ── Sliders ── */
div[data-testid="stSlider"] > label {
    color: #64748b !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* ── Radios ── */
div[data-testid="stRadio"] label {
    color: #475569 !important;
    font-weight: 600 !important;
}

/* ── divider ── */
.divider { border: none; border-top: 1px solid rgba(0, 0, 0, 0.06); margin: 28px 0; }

/* ── source chip ── */
.source-chip {
    display: inline-block;
    background: #f8fafc; border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 8px; padding: 4px 12px; font-size: .78rem; color: #475569 !important;
    margin: 4px;
    transition: all 0.2s ease;
}
.source-chip:hover {
    background: #f1f5f9;
    color: #0f172a !important;
}

/* ── Streamlit metric ── */
div[data-testid="metric-container"] {
    background: #ffffff !important;
    border-radius: 16px !important;
    border: 1px solid rgba(0, 0, 0, 0.07) !important;
    border-top: 3px solid #7c3aed !important;
    padding: 18px 20px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04) !important;
    transition: transform 0.2s ease !important;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.08em !important;
}

/* ── Warning/info box overrides ── */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-width: 1px !important;
    border-left-width: 4px !important;
}

/* Fix general texts */
.stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown strong {
    color: #1e293b !important;
}

/* ── Dataframe ── */
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid rgba(0,0,0,0.06) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 3px; }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.5); }
</style>
""", unsafe_allow_html=True)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">🤖 AI-Powered &nbsp;·&nbsp; Live Intelligence &nbsp;·&nbsp; OpenRouter LLM</div>
    <div class="hero-subtitle">Sport Predictor Agent</div>
    <div class="hero-title">
      <span class="brand-green">🏏</span> 
      <span class="brand-purple">Norrin</span><span style="color:#ffffff;-webkit-text-fill-color:#ffffff;">.AI</span>
    </div>
    <div class="hero-sub">
      Real-time analysis &amp; AI-powered predictions for any cricket player — 
      combining live web intelligence with cutting-edge LLM reasoning.
    </div>
    <div class="hero-badges">
      <div class="hero-badge">⚡ Live Web Scraping</div>
      <div class="hero-badge">🧠 LLM Reasoning</div>
      <div class="hero-badge">📊 Ensemble ML Models</div>
      <div class="hero-badge">🔒 Secure API</div>
    </div>
    <div class="hero-stats">
      <div>
        <div class="hero-stat-val">10+</div>
        <div class="hero-stat-lbl">AI Models</div>
      </div>
      <div>
        <div class="hero-stat-val">Live</div>
        <div class="hero-stat-lbl">Web Data</div>
      </div>
      <div>
        <div class="hero-stat-val">3</div>
        <div class="hero-stat-lbl">Free Models</div>
      </div>
      <div>
        <div class="hero-stat-val">∞</div>
        <div class="hero-stat-lbl">Players Supported</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────
tab_rt, tab_ml = st.tabs([
    "⚡  Real-Time Predictor  — Live Web + AI",
    "📊  Offline ML Models  — Historical Database",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — REAL-TIME CRICKET PREDICTOR
# ═══════════════════════════════════════════════════════════════════════════════
with tab_rt:
    st.markdown(
        "🏏 Predict **any real cricket player's** upcoming match performance using "
        "**live web data** from Cricbuzz + AI reasoning via OpenRouter LLM.",
        unsafe_allow_html=False,
    )

    # ── Input section ──────────────────────────────────────────────────
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    # Dropdown to choose prediction mode
    prediction_mode = st.selectbox(
        "Select Prediction Mode",
        options=[
            "📡 Live Cricbuzz Squad Matchup (Recommended)",
            "✍️ Standard Manual Player Entry (Custom Input)"
        ],
        index=0,
        key="prediction_mode_select"
    )

    # Default values to be populated by sections
    player_name: str = ""
    opposition: str = ""
    venue: str = ""
    model_name: str = ""
    selected_player: dict = {}
    match_format: str = "T20"
    squad_data: dict | None = None

    # Mode-specific variables defaults to satisfy type analysis
    player_name_manual: str = ""
    opposition_manual: str = ""
    venue_manual: str = ""
    match_format_manual: str = "T20"
    model_name_manual: str = ""

    match_format_squad: str = "T20"
    model_name_squad: str = ""
    
    # Track prediction triggers
    run_btn_squad = False
    run_btn_manual = False

    if prediction_mode == "📡 Live Cricbuzz Squad Matchup (Recommended)":
        st.markdown('<div class="card-heading">📡 Live Cricbuzz Squad Matchup</div>', unsafe_allow_html=True)
        
        squad_url = st.text_input(
            "Cricbuzz Squad URL",
            value="https://www.cricbuzz.com/cricket-match-squads/129563/eng-vs-nz-2nd-test-new-zealand-tour-of-england-2026",
            placeholder="Paste Cricbuzz match squads URL here",
            key="squad_url_input"
        )
        
        btn_load = st.button("Load Squad Roster", type="secondary", key="squad_load_btn")
        
        if btn_load:
            import importlib
            import sports_predictor.realtime_cricket
            importlib.reload(sports_predictor.realtime_cricket)
            from sports_predictor.realtime_cricket import parse_cricbuzz_squad
            with st.spinner("Fetching and parsing squads..."):
                squad_data = parse_cricbuzz_squad(squad_url)
                if "error" in squad_data:
                    st.error(f"Failed to load squad: {squad_data['error']}")
                else:
                    st.session_state["squad_cache_url"] = squad_url
                    st.session_state["squad_cache_data"] = squad_data
                    st.success("Squad roster successfully loaded!")
                    
        # Load from session cache if URL matches
        squad_data = None
        if "squad_cache_url" in st.session_state and st.session_state["squad_cache_url"] == squad_url:
            squad_data = st.session_state.get("squad_cache_data")
            
        if squad_data:
            st.markdown(
                f'<div style="background: rgba(124, 58, 237, 0.05); border-left: 4px solid #7c3aed; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; color: #1e293b;">'
                f'🏆 <strong>{squad_data["series"]}</strong> at <strong>{squad_data["venue"]}</strong> ({squad_data["team1"]} vs {squad_data["team2"]})'
                f'</div>',
                unsafe_allow_html=True
            )
            
            col_sel_p, col_sel_f, col_sel_m = st.columns([2, 1, 2])
            
            with col_sel_p:
                players_list = []
                player_options_map = {}
                
                # Squad 1 players
                for p in squad_data["squad1"]:
                    label = f"{p['name']} ({squad_data['team1']} - {p['role']} - {p['status']})"
                    players_list.append(label)
                    player_options_map[label] = {
                        "name": p["name"],
                        "role": p["role"],
                        "url": p["href"],
                        "team": squad_data["team1"],
                        "opp_team": squad_data["team2"],
                        "opp_squad": squad_data["squad2"]
                    }
                
                # Squad 2 players
                for p in squad_data["squad2"]:
                    label = f"{p['name']} ({squad_data['team2']} - {p['role']} - {p['status']})"
                    players_list.append(label)
                    player_options_map[label] = {
                        "name": p["name"],
                        "role": p["role"],
                        "url": p["href"],
                        "team": squad_data["team2"],
                        "opp_team": squad_data["team1"],
                        "opp_squad": squad_data["squad1"]
                    }
                
                selected_player_label = st.selectbox("Select Player", options=players_list, key="squad_player_select")
                selected_player = player_options_map.get(selected_player_label, {})
                
            with col_sel_f:
                # Detect format from series/URL
                detected_format = "T20"
                series_lower = squad_data["series"].lower()
                url_lower = squad_url.lower()
                if "test" in series_lower or "test" in url_lower:
                    detected_format = "Test"
                elif "odi" in series_lower or "odi" in url_lower or "one-day" in series_lower or "one day" in series_lower:
                    detected_format = "ODI"
                elif "t20" in series_lower or "t20" in url_lower:
                    detected_format = "T20"
                elif "ipl" in series_lower or "ipl" in url_lower:
                    detected_format = "IPL"
                    
                format_options = ["Test", "ODI", "T20", "IPL", "Other"]
                format_index = format_options.index(detected_format) if detected_format in format_options else 2
                match_format_squad = st.selectbox("Match Format", options=format_options, index=format_index, key="squad_format_select")
                
            with col_sel_m:
                models_config = [
                    {"id": "poolside/laguna-m.1:free", "label": "Poolside: Laguna M.1 (free)", "free": True},
                    {"id": "meta-llama/llama-3.3-70b-instruct:free", "label": "Meta: Llama 3.3 70B Instruct (free)", "free": True},
                    {"id": "nvidia/llama-nemotron-rerank-vl-1b-v2:free", "label": "NVIDIA: Llama Nemotron Rerank VL 1B V2 (free)", "free": True},
                    {"id": "google/gemini-2.5-flash", "label": "Google: Gemini 2.5 Flash", "free": False},
                    {"id": "google/gemini-2.5-pro", "label": "Google: Gemini 2.5 Pro", "free": False},
                    {"id": "openai/gpt-4o-mini", "label": "OpenAI: GPT-4o Mini", "free": False},
                    {"id": "openai/gpt-4o", "label": "OpenAI: GPT-4o", "free": False},
                    {"id": "meta-llama/llama-3.3-70b-instruct", "label": "Meta: Llama 3.3 70B Instruct", "free": False},
                    {"id": "anthropic/claude-3.5-haiku", "label": "Anthropic: Claude 3.5 Haiku", "free": False},
                    {"id": "mistralai/mixtral-8x7b-instruct", "label": "Mistral AI: Mixtral 8x7B Instruct", "free": False},
                ]

                display_options = []
                model_id_map = {}
                for m in models_config:
                    indicator = "✅" if m["free"] else "❌"
                    option_text = f"{indicator} {m['label']}"
                    display_options.append(option_text)
                    model_id_map[option_text] = m["id"]

                selected_option_squad = st.selectbox(
                    "Model Choice",
                    options=display_options,
                    help="Select LLM for analysis reasoning",
                    key="squad_model_select"
                )
                model_name_squad = model_id_map[selected_option_squad]
                
            can_run_squad = bool(api_key) and bool(selected_player)
            if not api_key:
                st.warning("⚠️ **OpenRouter API Key is missing!** Please set `OPENROUTER_API_KEY` in your `.env` file.")
            elif not selected_player:
                st.warning("⚠️ **No player selected.** Please ensure players are loaded in the squad roster.")
                
            run_btn_squad = st.button(
                "🔮  Analyse & Predict Performance (Live Matchup)",
                type="primary",
                disabled=not can_run_squad,
                use_container_width=True,
                key="squad_run_button"
            )
        else:
            st.info("💡 Paste a Cricbuzz Match Squads URL and click 'Load Squad Roster' to select players and opponent rosters instantly.")
            
    elif prediction_mode == "✍️ Standard Manual Player Entry (Custom Input)":
        st.markdown('<div class="card-heading">✍️ Standard Manual Player Entry</div>', unsafe_allow_html=True)
        
        col_player, col_match, col_config = st.columns([2, 2, 2])

        with col_player:
            st.markdown('<div style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">🏏 Player Name</div>', unsafe_allow_html=True)
            player_name_manual = st.text_input(
                "Player Name",
                value="Virat Kohli",
                placeholder="e.g. Jasprit Bumrah",
                label_visibility="collapsed",
                key="manual_player_input"
            )

        with col_match:
            st.markdown('<div style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">🏆 Match Details</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            opposition_manual = c1.text_input("Opposition", value="Pakistan", placeholder="e.g. Australia", key="manual_opp_input")
            venue_manual = c2.text_input("Venue", value="Melbourne Cricket Ground", placeholder="e.g. Eden Gardens", key="manual_venue_input")
            match_format_manual = st.selectbox(
                "Match Format",
                options=["T20", "ODI", "Test", "IPL", "Other"],
                index=0,
                key="manual_format_select",
            )

        with col_config:
            st.markdown('<div style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">🤖 AI Config</div>', unsafe_allow_html=True)
            
            models_config = [
                {"id": "poolside/laguna-m.1:free", "label": "Poolside: Laguna M.1 (free)", "free": True},
                {"id": "meta-llama/llama-3.3-70b-instruct:free", "label": "Meta: Llama 3.3 70B Instruct (free)", "free": True},
                {"id": "nvidia/llama-nemotron-rerank-vl-1b-v2:free", "label": "NVIDIA: Llama Nemotron Rerank VL 1B V2 (free)", "free": True},
                {"id": "google/gemini-2.5-flash", "label": "Google: Gemini 2.5 Flash", "free": False},
                {"id": "google/gemini-2.5-pro", "label": "Google: Gemini 2.5 Pro", "free": False},
                {"id": "openai/gpt-4o-mini", "label": "OpenAI: GPT-4o Mini", "free": False},
                {"id": "openai/gpt-4o", "label": "OpenAI: GPT-4o", "free": False},
                {"id": "meta-llama/llama-3.3-70b-instruct", "label": "Meta: Llama 3.3 70B Instruct", "free": False},
                {"id": "anthropic/claude-3.5-haiku", "label": "Anthropic: Claude 3.5 Haiku", "free": False},
                {"id": "mistralai/mixtral-8x7b-instruct", "label": "Mistral AI: Mixtral 8x7B Instruct", "free": False},
            ]

            display_options = []
            model_id_map = {}
            for m in models_config:
                indicator = "✅" if m["free"] else "❌"
                option_text = f"{indicator} {m['label']}"
                display_options.append(option_text)
                model_id_map[option_text] = m["id"]

            selected_option_manual = st.selectbox(
                "Model",
                options=display_options,
                help="Select LLM for analysis reasoning",
                key="manual_model_select"
            )
            model_name_manual = model_id_map[selected_option_manual]

        can_run_manual = bool(player_name_manual.strip() and opposition_manual.strip() and venue_manual.strip() and api_key)
        if not api_key:
            st.warning("⚠️ **OpenRouter API Key is missing!** Please set `OPENROUTER_API_KEY` in your `.env` file to enable the real-time predictor.")

        run_btn_manual = st.button(
            "🔮  Analyse & Predict Performance (Manual Entry)",
            type="primary",
            disabled=not can_run_manual,
            use_container_width=True,
            key="manual_run_button"
        )

    # ── Execute Prediction ───────────────────────────────────────────────
    run_btn = False
    run_mode = ""

    if run_btn_squad:
        run_btn = True
        run_mode = "squad"
        # Map variables for squad mode
        player_name = selected_player["name"]
        opposition = selected_player["opp_team"]
        venue = (squad_data or {}).get("venue", "")
        match_format = match_format_squad
        model_name = model_name_squad
    elif run_btn_manual:
        run_btn = True
        run_mode = "manual"
        # Map variables for manual mode
        player_name = player_name_manual
        opposition = opposition_manual
        venue = venue_manual
        match_format = match_format_manual
        model_name = model_name_manual

    if run_btn:
        steps: list[str] = []
        progress_box = st.empty()

        def _render_steps(current: str) -> None:
            import re
            steps.append(current)
            html_content = '<div class="log-container">'
            for i, s in enumerate(steps):
                is_last = (i == len(steps) - 1)
                item_class = "active" if is_last else "done"
                text_class = "active" if is_last else "done"
                icon_symbol = "⚡" if is_last else "✓"
                
                # Format markdown bold matches to HTML strong tags
                clean_s = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", s)
                
                html_content += (
                    f'<div class="log-item {item_class}">'
                    f'<div class="log-icon-container {item_class}">'
                    f'<div class="log-icon-circle {item_class}">{icon_symbol}</div>'
                    f'</div>'
                    f'<span class="log-text {text_class}">{clean_s}</span>'
                    f'</div>'
                )
            html_content += '</div>'
            progress_box.markdown(html_content, unsafe_allow_html=True)

        with st.spinner("Gathering live intelligence..."):
            import importlib
            import sports_predictor.realtime_cricket
            importlib.reload(sports_predictor.realtime_cricket)
            if run_mode == "manual":
                from sports_predictor.realtime_cricket import predict_real_player
                result = predict_real_player(
                    player_name=player_name,
                    opposition=opposition,
                    venue=venue,
                    api_key=api_key,
                    match_format=match_format,
                    model_name=model_name,
                    status_callback=_render_steps,
                )
            else:
                from sports_predictor.realtime_cricket import predict_real_player_squad
                result = predict_real_player_squad(
                    player_name=selected_player["name"],
                    player_role=selected_player["role"],
                    player_profile_url=selected_player["url"],
                    opposition_team=selected_player["opp_team"],
                    opponent_squad=selected_player["opp_squad"],
                    match_format=match_format,
                    venue=venue,
                    api_key=api_key,
                    model_name=model_name,
                    status_callback=_render_steps,
                )

        progress_box.empty()

        # ── Error handling ─────────────────────────────────────────────────
        if "error" in result:
            st.error(f"**Prediction failed:** {result['error']}")
            ctx = result.get("scraped_context", {})
            if ctx:
                with st.expander("🔍 Scraped context (for debugging)"):
                    st.json(ctx)
            st.stop()

        # ── Successful result rendering ────────────────────────────────────
        st.success("✅  Prediction complete! Scroll down for full analysis.")

        role = result.get("role", "batsman").lower()
        tagline = result.get("visual_tagline", "")
        reasoning = result.get("reasoning_markdown", "")
        bat = result.get("batsman_prediction") or {}
        bowl = result.get("bowler_prediction") or {}
        ctx = result.get("scraped_context", {})
        profile = ctx.get("profile_data", {})

        # ── Tagline ────────────────────────────────────────────────────────
        if tagline:
            st.markdown(f'<div class="tagline">&#8220; {tagline} &#8221;</div>', unsafe_allow_html=True)

        # ── Player bio strip ───────────────────────────────────────────────
        if profile and "error" not in profile:
            img_url = profile.get("image_url", "")
            img_tag = (
                f'<img src="{img_url}" style="width:80px;height:80px;border-radius:50%;'
                f'object-fit:cover;border:3px solid #7c3aed;" onerror="this.style.display=\'none\'" />'
                if img_url else ""
            )
            name_val = profile.get("name", "")
            country_val = profile.get("country", "")
            role_val = profile.get("role", "")
            bat_style_val = profile.get("bat_style", "")
            bowl_style_val = profile.get("bowl_style", "")
            dob_val = profile.get("dob", "")
            height_val = profile.get("height", "")
            bio_html = (
                f'<div class="glass-card" style="display:flex;gap:20px;align-items:flex-start;">'
                f'{img_tag}'
                f'<div>'
                f'<div style="font-size:1.6rem;font-weight:800;color:#0f172a;">{name_val}</div>'
                f'<div style="color:#475569;font-size:.95rem;margin-top:4px;">'
                f'{country_val} &bull; {role_val} &bull; {bat_style_val} &bull; {bowl_style_val}'
                f'</div>'
                f'<div style="color:#64748b;font-size:.85rem;margin-top:4px;">'
                f'DOB: {dob_val} &bull; {height_val}'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(bio_html, unsafe_allow_html=True)


        # ── Main metrics layout ────────────────────────────────────────────
        col_main, col_right = st.columns([3, 2])

        with col_main:
            # BATSMAN section
            if role in ("batsman", "all-rounder") and bat:
                st.markdown('<div class="card-heading">&#127951; Batsman Prediction Metrics</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="stat-row">
  <div class="stat-box amber">
    <div class="stat-lbl">Runs Range</div>
    <div class="stat-val">{bat.get('predicted_runs_range', 'N/A')}</div>
  </div>
  <div class="stat-box red">
    <div class="stat-lbl">Key Bowler Threat</div>
    <div class="stat-val sm">{bat.get('who_can_get_him_out', 'N/A')}</div>
  </div>
  <div class="stat-box">
    <div class="stat-lbl">Mode of Dismissal</div>
    <div class="stat-val sm">{bat.get('possible_mode_of_dismissal', 'N/A')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

                # Threats
                threats = bat.get("possible_threats", "")
                if threats:
                    st.warning(f"⚠️ **Threat Profile:** {threats}")

                # Bowling type strengths & weaknesses
                st.markdown("**Bowling Types**", unsafe_allow_html=False)
                col_bstr, col_bwk = st.columns(2)
                _none_html = '<em style="color:#64748b">None listed</em>'
                with col_bstr:
                    st.markdown("Strengths against:")
                    pills = "".join(
                        f'<span class="pill pill-green">{x}</span>'
                        for x in bat.get("bowling_strength", [])
                    )
                    st.markdown(f'<div class="pill-row">{pills or _none_html}</div>', unsafe_allow_html=True)
                with col_bwk:
                    st.markdown("Weaknesses against:")
                    pills = "".join(
                        f'<span class="pill pill-red">{x}</span>'
                        for x in bat.get("bowling_weakness", [])
                    )
                    st.markdown(f'<div class="pill-row">{pills or _none_html}</div>', unsafe_allow_html=True)

                # Length strengths & weaknesses
                st.markdown("**Delivery Lengths**", unsafe_allow_html=False)
                col_lstr, col_lwk = st.columns(2)
                with col_lstr:
                    st.markdown("Handles well:")
                    pills = "".join(
                        f'<span class="pill pill-green">{x}</span>'
                        for x in bat.get("length_strength", [])
                    )
                    st.markdown(f'<div class="pill-row">{pills or _none_html}</div>', unsafe_allow_html=True)
                with col_lwk:
                    st.markdown("Struggles with:")
                    pills = "".join(
                        f'<span class="pill pill-red">{x}</span>'
                        for x in bat.get("length_weakness", [])
                    )
                    st.markdown(f'<div class="pill-row">{pills or _none_html}</div>', unsafe_allow_html=True)

            # BOWLER section
            if role in ("bowler", "all-rounder") and bowl:
                if role == "all-rounder":
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                st.markdown('<div class="card-heading">&#127929; Bowler Prediction Metrics</div>', unsafe_allow_html=True)
                st.markdown(f"""
<div class="stat-row">
  <div class="stat-box green">
    <div class="stat-lbl">Wickets Tally</div>
    <div class="stat-val">{bowl.get('predicted_wickets', 'N/A')}</div>
  </div>
  <div class="stat-box amber">
    <div class="stat-lbl">Economy</div>
    <div class="stat-val">{bowl.get('predicted_economy', 'N/A')}</div>
  </div>
  <div class="stat-box">
    <div class="stat-lbl">Strike Rate</div>
    <div class="stat-val">{bowl.get('success_rate', 'N/A')}</div>
  </div>
</div>
""", unsafe_allow_html=True)
                st.info(f"🎯 **Bowling Role:** {bowl.get('role_in_match', 'N/A')}")
                st.markdown(f"🔮 **Deliveries to expect:** {bowl.get('kind_of_ball_will_bowl', 'N/A')}")
                st.markdown(f"📊 **Success vs opposition batters:** {bowl.get('success_rate_vs_batters', 'N/A')}")

        with col_right:
            # Scraped career stats
            st.markdown('<div class="card-heading">📋 Career Stats (Cricbuzz)</div>', unsafe_allow_html=True)

            if profile and "error" not in profile:
                bat_stats = profile.get("batting_summary", {})
                if bat_stats and bat_stats.get("rows"):
                    st.caption("Batting")
                    df_bat = pd.DataFrame(
                        bat_stats["rows"],
                        columns=bat_stats["headers"],
                    )
                    st.dataframe(df_bat, width="stretch", hide_index=True, height=240)

                bowl_stats = profile.get("bowling_summary", {})
                if bowl_stats and bowl_stats.get("rows"):
                    st.caption("Bowling")
                    df_bowl = pd.DataFrame(
                        bowl_stats["rows"],
                        columns=bowl_stats["headers"],
                    )
                    st.dataframe(df_bowl, width="stretch", hide_index=True, height=200)

                # Recent form from scraped data
                rb = profile.get("recent_batting", {})
                if rb and rb.get("rows"):
                    st.caption("Recent Batting (last 5)")
                    df_rb = pd.DataFrame(rb["rows"], columns=rb["headers"])
                    st.dataframe(df_rb, width="stretch", hide_index=True)
            else:
                st.info("No direct Cricbuzz stats available — using web search context.")

        # ── LLM Reasoning ─────────────────────────────────────────────────
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown('<div class="card-heading">&#129504; AI Reasoning & Deep Analysis</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="glass-card">{reasoning}</div>',
            unsafe_allow_html=True,
        )

        # ── Radar chart: bowling type heat-map ────────────────────────────
        if bat and (bat.get("bowling_strength") or bat.get("bowling_weakness")):
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown('<div class="card-heading">&#128202; Bowling Type Vulnerability Map</div>', unsafe_allow_html=True)

            all_types = [
                "Off-spin", "Leg-spin", "Left-arm spinner",
                "Left-arm pacer", "Right-arm pacer", "Medium pace", "Fast pace"
            ]
            strengths_lower = [x.lower() for x in bat.get("bowling_strength", [])]
            weaknesses_lower = [x.lower() for x in bat.get("bowling_weakness", [])]

            scores = []
            for t in all_types:
                t_lower = t.lower()
                if any(w in t_lower or t_lower in w for w in weaknesses_lower):
                    scores.append(1)   # weak
                elif any(s in t_lower or t_lower in s for s in strengths_lower):
                    scores.append(5)   # strong
                else:
                    scores.append(3)   # neutral

            radar_fig = go.Figure(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=all_types + [all_types[0]],
                fill="toself",
                fillcolor="rgba(167,139,250,0.15)",
                line=dict(color="#a78bfa", width=2),
                name="Strength (5) vs Weakness (1)",
            ))
            radar_fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True, range=[0, 5],
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=["Weak", "", "Neutral", "", "Strong"],
                        gridcolor="rgba(0,0,0,0.08)",
                        linecolor="rgba(0,0,0,0.08)",
                    ),
                    angularaxis=dict(gridcolor="rgba(0,0,0,0.08)"),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", family="Outfit"),
                height=420,
                margin=dict(l=60, r=60, t=40, b=40),
                showlegend=False,
            )
            st.plotly_chart(radar_fig, use_container_width=True)

        # ── Length vulnerability bar chart ────────────────────────────────
        if bat and (bat.get("length_strength") or bat.get("length_weakness")):
            all_lengths = ["Good length", "Hard length", "Short (Bouncer)", "Full (Yorker)", "Half volley", "Googly / Wrong 'un", "Slower ball"]
            len_strengths_lower = [x.lower() for x in bat.get("length_strength", [])]
            len_weaknesses_lower = [x.lower() for x in bat.get("length_weakness", [])]

            len_scores, colors_bar = [], []
            for l in all_lengths:
                ll = l.lower()
                if any(w in ll or ll in w for w in len_weaknesses_lower):
                    len_scores.append(-1)
                    colors_bar.append("#ef4444")
                elif any(s in ll or ll in s for s in len_strengths_lower):
                    len_scores.append(1)
                    colors_bar.append("#10b981")
                else:
                    len_scores.append(0)
                    colors_bar.append("#64748b")

            bar_fig = go.Figure(go.Bar(
                x=all_lengths,
                y=len_scores,
                marker_color=colors_bar,
                text=["Strength" if s == 1 else ("Weakness" if s == -1 else "Neutral") for s in len_scores],
                textposition="outside",
            ))
            bar_fig.update_layout(
                title="Delivery Length — Strength vs Weakness",
                yaxis=dict(tickvals=[-1, 0, 1], ticktext=["Weakness", "Neutral", "Strength"], gridcolor="rgba(0,0,0,0.06)"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", family="Outfit"),
                height=340, margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(bar_fig, use_container_width=True)

        # ── Sources accordion ──────────────────────────────────────────────
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        with st.expander("🔗 Data Sources & Search Snippets Used (Transparency)"):
            label_map = {
                "recent_form": "Recent Form",
                "head_to_head": "Head-to-Head Records",
                "pitch_report": "Pitch & Venue Conditions",
                "opposition_bowlers": "Opposition Bowling Attack",
            }
            for key, label in label_map.items():
                items = ctx.get(key, [])
                if not items:
                    continue
                st.markdown(f"**{label}**")
                for item in items:
                    url_link = item.get("url", "#")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    st.markdown(f"- [{title}]({url_link}) — *{snippet}*")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — OFFLINE ML MODELS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ml:
    st.markdown("Predictions powered by an **ensemble ML model** trained on historical match statistics.")

    from sports_predictor.config import MODEL_DIR, SPORTS
    from sports_predictor.data_collection import clean_and_validate, load_or_create_dataset
    from sports_predictor.models import load_model
    from sports_predictor.prediction_service import predict_performance

    df = clean_and_validate(load_or_create_dataset())

    col_sb, col_content = st.columns([1, 3])

    with col_sb:
        st.markdown('<div class="card-heading">Filters</div>', unsafe_allow_html=True)
        sport = st.selectbox("Sport", [s.title() for s in SPORTS]).lower()
        sport_df = df[df["sport"].eq(sport)]
        player_options = sport_df[["player_id", "player_name"]].drop_duplicates()
        player_label = st.selectbox(
            "Player",
            player_options.apply(
                lambda r: f"{r.player_id} - {r.player_name}", axis=1
            ).tolist(),
        )
        player_id = int(player_label.split(" - ")[0])
        match_date_input = st.date_input("Match date", date.today())
        opposition_ml = st.selectbox("Opposition", sorted(sport_df["opposition"].unique()))
        home_away = st.radio("Venue", ["home", "away"], horizontal=True)
        opp_strength = st.slider("Opposition strength", 0.0, 1.0, 0.5, 0.05)
        inj_risk = st.slider("Injury risk", 0.0, 1.0, 0.05, 0.05)
        rest_days = st.number_input("Rest days", 0, 30, 4)

    with col_content:
        result_ml = predict_performance(
            player_id=player_id,
            sport=sport,
            match_date=str(match_date_input),
            opposition=opposition_ml,
            home_away=home_away,
            opposition_strength=opp_strength,
            injury_risk=inj_risk,
            days_rest=rest_days,
        )

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Predicted Performance", f"{result_ml.predicted_performance:.2f}")
        mc2.metric("Confidence Interval", f"{result_ml.confidence_interval[0]:.1f}–{result_ml.confidence_interval[1]:.1f}")
        mc3.metric("Risk Level", result_ml.risk_level)

        history = sport_df[sport_df["player_id"].eq(player_id)].sort_values("match_date")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(
            x=history["match_date"], y=history["performance_metric"],
            name="Actual", line=dict(color="#a78bfa", width=2),
            fill="tozeroy", fillcolor="rgba(167,139,250,0.05)",
        ))
        fig_hist.add_hline(
            y=result_ml.predicted_performance, line_dash="dash",
            line_color="#f472b6", annotation_text="Prediction",
        )
        fig_hist.update_layout(
            height=380, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#1e293b", family="Outfit"),
            xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
            yaxis=dict(title="Performance", gridcolor="rgba(0,0,0,0.05)"),
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        fl, fr = st.columns(2)
        with fl:
            st.markdown("**Feature Importance**")
            model_bundle = load_model(sport)
            fp = MODEL_DIR / sport / "feature_importance.csv"
            if not fp.exists():
                fp = MODEL_DIR / f"{sport}_feature_importance.csv"
            if fp.exists():
                imp_df = pd.read_csv(fp).head(12).sort_values("importance")
            else:
                imp_df = model_bundle.feature_importance.head(12).sort_values("importance")
            fig_imp = go.Figure(go.Bar(
                x=imp_df["importance"], y=imp_df["feature"],
                orientation="h", marker_color="#818cf8",
            ))
            fig_imp.update_layout(
                height=340, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", family="Outfit"),
                xaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0.05)"),
            )
            st.plotly_chart(fig_imp, use_container_width=True)

        with fr:
            st.markdown("**Recent Form**")
            st.dataframe(
                history.tail(10)[
                    ["match_date", "opposition", "is_home", "days_rest",
                     "injury_risk", "performance_metric"]
                ],
                width="stretch",
                hide_index=True,
            )

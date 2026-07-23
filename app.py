import numpy as np

# Global Monkey-patch for numpy.isnan to resolve Python 3.13 scikit-learn compatibility issue
_original_isnan = np.isnan
def _safe_isnan(x):
    try:
        return _original_isnan(x)
    except TypeError:
        if isinstance(x, np.ndarray):
            return np.zeros(x.shape, dtype=bool)
        return False
np.isnan = _safe_isnan

import streamlit as st
import pandas as pd
import joblib
import os
import shutil
import re
import json
from pathlib import Path
from datetime import datetime
import storage.storage_manager as storage_manager

# Set page config
st.set_page_config(
    page_title="OSMOS Digital Twin Dashboard",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OSMOS UI Style System
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Outfit:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-main: #06090e;
        --bg-surface: #0b1019;
        --panel: rgba(13, 19, 31, 0.75);
        --panel-solid: #0d131f;
        --panel-2: #101726;
        --panel-3: #141e30;
        --panel-hover: #162032;
        --line: rgba(255, 255, 255, 0.08);
        --line-strong: rgba(34, 211, 238, 0.38);
        --text-main: #f1f5f9;
        --text-muted: #94a3b8;
        --text-faint: #64748b;
        
        --cyan: #22d3ee;
        --cyan-glow: rgba(34, 211, 238, 0.25);
        --teal: #06b6d4;
        --indigo: #6366f1;
        --indigo-glow: rgba(99, 102, 241, 0.25);
        --amber: #f59e0b;
        --rose: #f43f5e;
        --green: #10b981;
        --blue: #3b82f6;
        --violet: #8b5cf6;
        
        --radius-sm: 8px;
        --radius: 12px;
        --radius-lg: 16px;
        --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.25);
        --shadow-md: 0 12px 32px rgba(0, 0, 0, 0.35);
        --shadow-glow: 0 0 24px rgba(34, 211, 238, 0.12);
    }

    body * {
        box-sizing: border-box;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--bg-main) !important;
        color: var(--text-main) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Atmospheric Ambient Glowing Background */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(ellipse 70% 40% at 15% 10%, rgba(34, 211, 238, 0.07), transparent 60%),
            radial-gradient(ellipse 60% 45% at 85% 20%, rgba(99, 102, 241, 0.06), transparent 50%),
            radial-gradient(ellipse 50% 50% at 50% 90%, rgba(16, 185, 129, 0.04), transparent 60%),
            repeating-linear-gradient(90deg, rgba(255, 255, 255, 0.012) 0 1px, transparent 1px 64px),
            repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.012) 0 1px, transparent 1px 64px);
    }

    [data-testid="stAppViewContainer"] > div { position: relative; z-index: 1; }

    [data-testid="stMainBlockContainer"], section.main > div {
        max-width: 1560px !important;
        padding-top: 24px !important;
        padding-right: 32px !important;
        padding-left: 32px !important;
        padding-bottom: 48px !important;
    }

    /* Modern Typography */
    h1, h2, h3, h4 {
        font-family: 'Outfit', 'Space Grotesk', sans-serif !important;
        color: var(--text-main) !important;
        letter-spacing: -0.02em !important;
    }

    h1 { font-size: 34px !important; font-weight: 800 !important; line-height: 1.15 !important; }
    h2 { font-size: 22px !important; font-weight: 700 !important; }
    h3 { font-size: 17px !important; font-weight: 600 !important; }
    p, li, label, span, div { color: inherit; }

    .gradient-text, .gradient-text-gold, h1 span[style*="background"] {
        background: linear-gradient(135deg, var(--cyan), var(--indigo)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        color: var(--cyan) !important;
    }

    /* Page Hero Header Banner */
    .page-hero {
        position: relative;
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin: 0 0 26px 0;
        padding: 0 0 20px 0;
        border-bottom: 1px solid var(--line);
    }

    .page-hero::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 120px;
        height: 2px;
        background: linear-gradient(90deg, var(--cyan), var(--indigo), transparent);
    }

    .page-kicker {
        display: inline-flex;
        align-items: center;
        width: fit-content;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        background: linear-gradient(90deg, rgba(34, 211, 238, 0.12), rgba(99, 102, 241, 0.12));
        border: 1px solid rgba(34, 211, 238, 0.25);
        color: var(--cyan);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .page-hero h1 {
        margin: 2px 0 0 0 !important;
        font-size: 34px !important;
        background: linear-gradient(135deg, #ffffff 40%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .page-hero p {
        max-width: 820px;
        margin: 4px 0 0 0 !important;
        color: var(--text-muted) !important;
        font-size: 14px;
        line-height: 1.6;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070a0f, #0a0e16 60%, #070a0f) !important;
        border-right: 1px solid var(--line) !important;
        box-shadow: 8px 0 32px rgba(0, 0, 0, 0.4) !important;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 18px 8px 16px;
    }

    .brand-mark {
        display: grid;
        place-items: center;
        width: 44px;
        height: 44px;
        border-radius: var(--radius);
        color: #ffffff;
        background: linear-gradient(135deg, #06b6d4, #6366f1);
        font-family: 'Outfit', sans-serif;
        font-weight: 900;
        font-size: 22px;
        box-shadow: 0 0 24px rgba(6, 182, 212, 0.4);
    }

    .brand-title {
        color: var(--text-main);
        font-family: 'Outfit', sans-serif;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.04em;
        line-height: 1;
    }

    .brand-subtitle {
        color: var(--cyan);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .sidebar-rule {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.4), transparent);
        margin: 4px 0 16px;
    }

    /* Custom Nav Buttons in Sidebar */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        min-height: 44px !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: var(--radius) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        background: rgba(255, 255, 255, 0.025) !important;
        color: var(--text-muted) !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        padding: 11px 16px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateX(4px) !important;
        background: rgba(34, 211, 238, 0.08) !important;
        border-color: rgba(34, 211, 238, 0.3) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
    }

    [data-testid="stSidebar"] button[title] {
        text-align: left !important;
    }

    .privacy-card {
        margin-top: 14px;
        padding: 14px;
        border-radius: var(--radius);
        border: 1px solid rgba(244, 63, 94, 0.25);
        background: rgba(244, 63, 94, 0.06);
        color: var(--text-muted);
        font-size: 11.5px;
        line-height: 1.55;
    }

    /* Cards & Containers */
    .glass-card, .glass-card-accent, [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"], [data-testid="stExpander"], [data-testid="stMetric"], .persona-card {
        background: var(--panel) !important;
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        box-shadow: var(--shadow-md) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    .glass-card, .glass-card-accent, .persona-card { padding: 22px !important; }
    .glass-card-accent {
        border-left: 4px solid var(--cyan) !important;
        background: linear-gradient(135deg, rgba(34, 211, 238, 0.05), rgba(13, 19, 31, 0.8)) !important;
    }

    div[style*="border-radius: 10px"], div[style*="border-radius:10px"], div[style*="border-radius: 12px"], div[style*="border-radius:12px"], div[style*="border-radius: 14px"], div[style*="border-radius:14px"], div[style*="border-radius: 16px"], div[style*="border-radius:16px"], div[style*="border-radius: 18px"], div[style*="border-radius:18px"] {
        border-radius: var(--radius) !important;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 24px 0 16px !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid var(--line) !important;
    }

    .section-header .icon {
        display: inline-grid !important;
        place-items: center;
        width: 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        background: rgba(34, 211, 238, 0.12);
        border: 1px solid rgba(34, 211, 238, 0.25);
        color: var(--cyan);
        font-size: 16px !important;
    }

    .section-header .title {
        color: var(--text-main) !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 17px !important;
        font-weight: 700 !important;
    }

    /* KPI Grid & Cards */
    .kpi-container {
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
        gap: 14px !important;
        margin-bottom: 28px !important;
    }

    .kpi-card {
        position: relative;
        min-height: 130px;
        padding: 18px !important;
        text-align: left !important;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        overflow: hidden;
        border-radius: var(--radius) !important;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01)), var(--panel-solid) !important;
        border: 1px solid var(--line) !important;
        box-shadow: var(--shadow-md) !important;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--cyan), var(--indigo));
    }

    .kpi-card:hover {
        transform: translateY(-4px) !important;
        border-color: var(--line-strong) !important;
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45), var(--shadow-glow) !important;
    }

    .kpi-icon {
        position: absolute;
        top: 16px;
        right: 16px;
        font-size: 22px !important;
        opacity: 0.8;
    }

    .kpi-val {
        position: relative;
        z-index: 1;
        color: var(--text-main);
        font-family: 'Outfit', 'Space Grotesk', sans-serif;
        font-size: 32px !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        overflow-wrap: anywhere;
        max-width: 100%;
    }

    .kpi-label {
        position: relative;
        z-index: 1;
        color: var(--text-muted) !important;
        font-size: 11px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 8px;
    }

    /* Colors */
    .color-total { color: var(--text-main) !important; }
    .color-prospect { color: var(--cyan) !important; }
    .color-client, .color-active { color: var(--green) !important; }
    .color-cold { color: var(--text-muted) !important; }
    .color-warm { color: var(--amber) !important; }
    .color-hot, .color-churn { color: var(--rose) !important; }
    .color-vip { color: var(--violet) !important; }

    .tag, .persona-segment-tag, .persona-client-count, .status-badge {
        border-radius: 999px !important;
        font-weight: 700 !important;
        padding: 5px 12px !important;
    }

    /* Score & Progress Bars */
    .score-bar-wrap { margin: 12px 0; }
    .score-bar-label { color: var(--text-muted) !important; font-size: 13px !important; }
    .score-bar-track {
        height: 8px !important;
        border-radius: 999px !important;
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.04);
        overflow: hidden;
    }
    .score-bar-fill { height: 100%; border-radius: 999px !important; }
    .fill-indigo { background: linear-gradient(90deg, #0284c7, var(--cyan)) !important; }
    .fill-violet { background: linear-gradient(90deg, #7c3aed, var(--indigo)) !important; }
    .fill-cyan { background: linear-gradient(90deg, #06b6d4, #38bdf8) !important; }
    .fill-rose { background: linear-gradient(90deg, #e11d48, var(--rose)) !important; }
    .fill-amber { background: linear-gradient(90deg, #d97706, var(--amber)) !important; }
    .fill-green { background: linear-gradient(90deg, #059669, var(--green)) !important; }

    /* Key-Value Info Rows */
    .info-row {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        font-size: 13px;
    }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: var(--text-muted) !important; font-weight: 600; }
    .info-value { color: var(--text-main) !important; font-family: 'JetBrains Mono', monospace; font-size: 12.5px; font-weight: 700; text-align: right; }

    /* Buttons */
    .stButton > button, [data-testid="stFormSubmitButton"] button {
        min-height: 42px !important;
        border-radius: var(--radius) !important;
        border: 1px solid rgba(34, 211, 238, 0.4) !important;
        background: linear-gradient(135deg, var(--teal), #0284c7) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        box-shadow: 0 4px 16px rgba(6, 182, 212, 0.25) !important;
        white-space: normal !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px) !important;
        border-color: var(--cyan) !important;
        box-shadow: 0 8px 24px rgba(6, 182, 212, 0.4) !important;
    }

    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.04) !important;
        color: var(--cyan) !important;
        border-color: rgba(34, 211, 238, 0.25) !important;
        box-shadow: none !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(34, 211, 238, 0.1) !important;
        border-color: rgba(34, 211, 238, 0.5) !important;
    }

    /* Inputs & Controls */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] > div > div > input,
    [data-testid="stNumberInput"] > div > div > input,
    [data-testid="stTextArea"] > div > div > textarea,
    [data-baseweb="select"] > div {
        background: #0a0f18 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: var(--radius) !important;
        color: var(--text-main) !important;
        min-height: 42px !important;
        box-shadow: inset 0 0 0 1px transparent !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }

    [data-testid="stSelectbox"] > div > div:focus-within,
    [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stNumberInput"] > div > div:focus-within,
    [data-testid="stTextArea"] > div > div:focus-within,
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--cyan) !important;
        box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.18) !important;
    }

    [data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="select"] [role="listbox"], ul[data-baseweb="menu"] {
        background: #0f172a !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        border-radius: var(--radius) !important;
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6) !important;
    }

    [role="option"], [data-baseweb="menu"] li { color: var(--text-muted) !important; }
    [role="option"]:hover, [role="option"][aria-selected="true"], [data-baseweb="menu"] li:hover, [data-baseweb="menu"] li[aria-selected="true"] {
        background: rgba(34, 211, 238, 0.14) !important;
        color: var(--text-main) !important;
    }

    /* DataFrames */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        overflow: hidden;
        box-shadow: var(--shadow-md) !important;
    }
    [data-testid="stDataFrame"] thead th {
        background: #0f172a !important;
        color: var(--cyan) !important;
        font-weight: 800 !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(even) { background: rgba(255, 255, 255, 0.02) !important; }

    /* Tabs */
    [data-testid="stTabs"] { margin-top: 6px; }
    [data-testid="stTabs"] button {
        border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
        color: var(--text-muted) !important;
        font-weight: 700 !important;
        padding: 10px 18px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--cyan) !important;
        border-bottom-color: var(--cyan) !important;
        background: rgba(34, 211, 238, 0.08) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] { padding: 16px 18px !important; }
    [data-testid="stMetricValue"] { color: var(--cyan) !important; font-family: 'Outfit', 'Space Grotesk', sans-serif !important; font-weight: 800 !important; }
    [data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 12px !important; font-weight: 800 !important; text-transform: uppercase; }

    /* Alerts & Callouts */
    [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        border: 1px solid var(--line) !important;
        box-shadow: none !important;
        background: var(--panel-solid) !important;
    }

    /* Sliders & Checkboxes */
    [data-testid="stSlider"] [role="slider"],
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]::before,
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--cyan), var(--indigo)) !important;
        border-color: var(--cyan) !important;
    }

    [data-testid="stCheckbox"] label, [data-testid="stRadio"] label { color: var(--text-muted) !important; }
    [data-baseweb="checkbox"] > div {
        background: #0a0f18 !important;
        border-color: rgba(34, 211, 238, 0.36) !important;
        border-radius: 4px !important;
    }

    /* Header Bar Translucency */
    header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        background: rgba(6, 9, 14, 0.85) !important;
        border-bottom: 1px solid var(--line) !important;
        backdrop-filter: blur(16px) !important;
    }

    .persona-card { min-height: 100%; }
    .persona-metric-chip, .persona-action-box, .persona-rule-box { border-radius: var(--radius) !important; }
    .persona-client-count { top: 14px !important; right: 14px !important; }

    /* Scrollbars */
    ::-webkit-scrollbar { width: 7px; height: 7px; }
    ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
    ::-webkit-scrollbar-thumb { background: rgba(34, 211, 238, 0.35); border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(34, 211, 238, 0.6); }

    @media (max-width: 720px) {
        [data-testid="stMainBlockContainer"], section.main > div {
            padding-left: 16px !important;
            padding-right: 16px !important;
            padding-top: 18px !important;
        }
        h1, .page-hero h1 { font-size: 26px !important; }
        .kpi-container { grid-template-columns: 1fr !important; }
        .kpi-card { min-height: 118px; }
        .glass-card, .glass-card-accent, .persona-card { padding: 16px !important; }
        .info-row { flex-direction: column; gap: 4px; }
        .info-value { text-align: left; }
    }
</style>
""", unsafe_allow_html=True)

# Helper function for safe min-max scaling
def minmax_scale(series, reverse=False):
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    scaled = (series - min_val) / (max_val - min_val)
    if reverse:
        scaled = 1.0 - scaled
    return scaled

# 1. Email validation check
def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

# 2. Database schema protection functions
def ensure_client_columns(df):
    new_cols = {
        "age": np.nan,
        "sex": None,
        "email": None,
        "customer_type": None,
        "household_size": np.nan,
        "phone_number": None,
        "company_name": None,
        "job_title": None,
        "city": None,
        "address": None,
        "original_entity_type": None,
        "converted_at": None,
        "conversion_event_id": None,
        "completed_client_profile": None,
        "predicted_clv_amount_mad": np.nan,
        "predicted_clv_score": np.nan,
        "predicted_clv_segment": None,
        "clv_model_name": None,
        "clv_segment_model_name": None,
        "clv_last_updated": None,
        "clv_method_used": None,
        "ml_predicted_clv_amount_mad": np.nan,
        "math_clv_amount_mad": np.nan,
        "clv_segment_prediction_source": None,
        "clv_segment_confidence": np.nan,
        "clv_segment_top_3": None,
        "ahp_group_CR": np.nan,
        "ahp_group_CI": np.nan,
        "ahp_expert_count": np.nan,
        "customer_segment": None,
        "customer_persona": None,
        "persona_description": None,
        "persona_recommended_action": None,
        "segmentation_method": None,
        "segmentation_last_updated": None
    }
    for col, default_val in new_cols.items():
        if col not in df.columns:
            df[col] = default_val
    return df

def ensure_clv_columns(df):
    return ensure_client_columns(df)

def ensure_history_columns(history):
    history_cols = {
        'old_entity_type': None,
        'new_entity_type': None,
        'prospect_to_client_conversion': False,
        'completed_client_profile': False,
        'before_values': None,
        'after_values': None,
        'old_clv_amount_mad': np.nan,
        'new_clv_amount_mad': np.nan,
        'old_clv_score': np.nan,
        'new_clv_score': np.nan,
        'old_clv_segment': None,
        'new_clv_segment': None,
        'clv_changed': False
    }
    for col, default_val in history_cols.items():
        if col not in history.columns:
            history[col] = default_val
    return history


# 3. Clean up legacy CSV files and backups
def cleanup_legacy_files():
    legacy_files = ["customers_dataset.csv", "event_history.csv"]
    for f in legacy_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass
                
    # Also clean up legacy CSV backup files
    for f in os.listdir("."):
        if f.startswith("customers_dataset_backup_") or f.startswith("event_history_backup_"):
            if f.endswith(".csv"):
                try:
                    os.remove(f)
                except Exception:
                    pass

def safe_isna(v):
    """Safely check if a scalar value is NA/None without crashing on lists or arrays.
    pd.isna() returns an array when called on list/ndarray, which then causes
    'ValueError: truth value of array is ambiguous' when used in an if condition.
    """
    if v is None:
        return True
    if isinstance(v, (list, np.ndarray)):
        return False  # Non-empty collections are never NA
    try:
        return bool(pd.isna(v))
    except (ValueError, TypeError):
        return False

def save_data(df, history):
    success, err = storage_manager.save_data(df, history)
    if not success:
        st.error(err)



# 5. Load Initial Data Function
@st.cache_data
def load_initial_data():
    paths_to_try = [
        Path("base models/RFM/osmos_simulation_data.xlsx"),
        Path("base models/osmos_simulation_data.xlsx"),
        Path("osmos_simulation_data.xlsx")
    ]
    excel_path = None
    for p in paths_to_try:
        if p.exists():
            excel_path = p
            break
            
    if excel_path is None:
        st.error("Simulation data file (osmos_simulation_data.xlsx) not found in expected locations.")
        return None

    snapshots = pd.read_excel(excel_path, sheet_name="Digital_Twins")
    profiles = pd.read_excel(excel_path, sheet_name="Customers")
    
    df = snapshots.merge(
        profiles,
        on=["entity_id", "entity_type"],
        how="left",
        suffixes=("", "_profile")
    )
    df = df.loc[:, ~df.columns.duplicated()]
    
    if "snapshot_date" in df.columns:
        df["snapshot_date"] = df["snapshot_date"].astype(str)
    if "created_at" in df.columns:
        df["created_at"] = df["created_at"].astype(str)
        
    return df

def get_data():
    df, history = storage_manager.load_data()
    df = ensure_client_columns(df)
    history = ensure_history_columns(history)
    return df, history


# 7. Load Model Artifact
@st.cache_resource
def load_model_artifact():
    artifact_paths = [
        Path("base models/RFM/osmos_best_model_artifact.pkl"),
        Path("osmos_best_model_artifact.pkl")
    ]
    artifact = None
    for p in artifact_paths:
        if p.exists():
            try:
                artifact = joblib.load(p)
                break
            except ModuleNotFoundError as e:
                missing_pkg = e.name
                st.error(f"❌ **Dependency Error:** The model artifact requires the missing package: `{missing_pkg}`. Please install it using: `pip install {missing_pkg}`")
                st.stop()
            except Exception as e:
                st.error(f"❌ **Error loading model artifact:** {e}")
                st.stop()
                
    if artifact is None:
        st.error("Model artifact (osmos_best_model_artifact.pkl) not found. Run training script first.")
        return None
        
    best_model_name = artifact.get("best_model_name", "")
    
    # Require packages only when needed by the loaded model
    if "XGBoost" in best_model_name:
        try:
            import xgboost
        except ImportError:
            st.error("❌ **Dependency Error:** The model artifact requires the missing package: `xgboost`. Please install it using: `pip install xgboost`")
            st.stop()
            
    if "LightGBM" in best_model_name:
        try:
            import lightgbm
        except ImportError:
            st.error("❌ **Dependency Error:** The model artifact requires the missing package: `lightgbm`. Please install it using: `pip install lightgbm`")
            st.stop()
            
    if "CatBoost" in best_model_name:
        try:
            import catboost
        except ImportError:
            st.error("❌ **Dependency Error:** The model artifact requires the missing package: `catboost`. Please install it using: `pip install catboost`")
            st.stop()
            
    return artifact

# 7b. Load CLV Model Artifact
def load_clv_model_artifact():
    artifact_paths = [
        Path("base models/CLV/osmos_best_clv_model_artifact.pkl"),
        Path("osmos_best_clv_model_artifact.pkl")
    ]
    artifact = None
    for p in artifact_paths:
        if p.exists():
            try:
                artifact = joblib.load(p)
                break
            except ModuleNotFoundError as e:
                missing_pkg = e.name
                st.warning(f"⚠️ **CLV Warning:** The CLV model artifact requires the missing package: `{missing_pkg}`. Please install it using: `pip install {missing_pkg}` to enable ML CLV predictions.")
            except Exception as e:
                st.warning(f"⚠️ **CLV Warning:** Error loading CLV model artifact: {e}")
                
    if artifact is None:
        st.warning("⚠️ **CLV Warning:** CLV model artifact (`osmos_best_clv_model_artifact.pkl`) not found. CLV predictions are disabled.")
    return artifact

def compute_math_clv_from_digital_twin(row, horizon_months=12, annual_discount_rate=0.10, profit_margin=0.25):
    """
    Compute a business-rule CLV from Digital Twin features.
    Uses:
    - purchases_90d
    - avg_order_value_mad
    - total_spent_90d_mad
    - churn_risk_score
    - rfm_score
    """
    # row can be a Series, dict, or DataFrame
    if isinstance(row, pd.DataFrame):
        row_dict = row.iloc[0].to_dict() if len(row) > 0 else {}
    elif hasattr(row, "to_dict"):
        row_dict = row.to_dict()
    else:
        row_dict = dict(row)

    purchases_90d = float(row_dict.get("purchases_90d", 0) or 0)
    total_spent_90d_mad = float(row_dict.get("total_spent_90d_mad", 0) or 0)
    avg_order_value_mad = float(row_dict.get("avg_order_value_mad", 0) or 0)
    churn_risk_score = float(row_dict.get("churn_risk_score", 0) or 0)
    rfm_score = float(row_dict.get("rfm_score", 0) or 0)

    if avg_order_value_mad <= 0 and purchases_90d > 0:
        avg_order_value_mad = total_spent_90d_mad / purchases_90d

    if purchases_90d <= 0 or avg_order_value_mad <= 0:
        return np.nan

    monthly_purchase_rate = purchases_90d / 3.0

    retention_probability = 1.0 - churn_risk_score
    retention_probability = float(np.clip(retention_probability, 0.05, 1.0))

    monthly_discount_rate = annual_discount_rate / 12.0

    expected_transactions = sum(
        monthly_purchase_rate * ((retention_probability / (1.0 + monthly_discount_rate)) ** month)
        for month in range(1, horizon_months + 1)
    )

    revenue_clv = expected_transactions * avg_order_value_mad
    profit_clv = revenue_clv * profit_margin

    rfm_adjustment = float(np.clip(rfm_score, 0.25, 1.0))
    rfm_adjusted_profit_clv = profit_clv * rfm_adjustment

    return rfm_adjusted_profit_clv

def align_clv_amount_features(row_df, clv_artifact):
    feature_cols = clv_artifact.get("amount_feature_columns", clv_artifact.get("feature_columns"))
    if feature_cols is None:
        raise ValueError("CLV artifact is missing both 'amount_feature_columns' and 'feature_columns'.")
        
    df_mapped = row_df.copy()
    
    # Map active digital twin variables to the expected _obs training features
    purchases = float(df_mapped["purchases_90d"].iloc[0]) if "purchases_90d" in df_mapped.columns and not pd.isna(df_mapped["purchases_90d"].iloc[0]) else 0.0
    spent = float(df_mapped["total_spent_90d_mad"].iloc[0]) if "total_spent_90d_mad" in df_mapped.columns and not pd.isna(df_mapped["total_spent_90d_mad"].iloc[0]) else 0.0
    aov = float(df_mapped["avg_order_value_mad"].iloc[0]) if "avg_order_value_mad" in df_mapped.columns and not pd.isna(df_mapped["avg_order_value_mad"].iloc[0]) else 0.0
    recency = float(df_mapped["recency_days"].iloc[0]) if "recency_days" in df_mapped.columns and not pd.isna(df_mapped["recency_days"].iloc[0]) else 0.0
    
    df_mapped["frequency_obs"] = purchases
    df_mapped["total_spent_obs_mad"] = spent
    df_mapped["avg_order_value_obs_mad"] = aov
    df_mapped["recency_obs_days"] = recency
    df_mapped["transaction_count_obs"] = purchases
    df_mapped["transaction_count_future"] = purchases
    df_mapped["total_profit_obs_mad"] = spent * 0.25
    df_mapped["customer_age_days"] = recency + 90.0
    df_mapped["return_rate_obs"] = 0.0
    df_mapped["discount_rate_obs"] = 0.15
    df_mapped["category_diversity_obs"] = 1.0
    
    interval_mean = 90.0 / purchases if purchases > 0 else 90.0
    df_mapped["purchase_interval_mean_days"] = interval_mean
    df_mapped["purchase_interval_std_days"] = 10.0
    
    # Map marketing_consent value to True/False boolean format
    if "marketing_consent" in df_mapped.columns:
        mc_val = df_mapped["marketing_consent"].iloc[0]
        if mc_val in [1, 1.0, True, "True", "1"]:
            df_mapped["marketing_consent"] = True
        else:
            df_mapped["marketing_consent"] = False
    
    # Compute log/slog transforms
    df_mapped["frequency_obs_log"] = np.log1p(df_mapped["frequency_obs"])
    df_mapped["total_spent_obs_mad_log"] = np.log1p(df_mapped["total_spent_obs_mad"])
    df_mapped["avg_order_value_obs_mad_log"] = np.log1p(df_mapped["avg_order_value_obs_mad"])
    df_mapped["purchase_interval_mean_days_log"] = np.log1p(df_mapped["purchase_interval_mean_days"])
    df_mapped["purchase_interval_std_days_log"] = np.log1p(df_mapped["purchase_interval_std_days"])
    df_mapped["transaction_count_obs_log"] = np.log1p(df_mapped["transaction_count_obs"])
    df_mapped["transaction_count_future_log"] = np.log1p(purchases)
    df_mapped["total_profit_obs_mad_slog"] = np.sign(df_mapped["total_profit_obs_mad"]) * np.log1p(np.abs(df_mapped["total_profit_obs_mad"]))
    
    # Target leakage handling: compute math clv fallback and log transform it
    math_clv = compute_math_clv_from_digital_twin(df_mapped)
    if pd.isna(math_clv) or math_clv <= 0.0:
        math_clv = 0.0
    df_mapped["clv_amount_mad_slog"] = np.sign(math_clv) * np.log1p(math_clv)
    
    # Map high-cardinality categorical ID
    if "entity_id" in df_mapped.columns:
        ent_id = str(df_mapped["entity_id"].iloc[0])
        df_mapped["base_entity_id"] = ent_id.replace("P", "C")
        
    pred_df = pd.DataFrame(index=[0])
    missing_cols = []
    for col in feature_cols:
        if col in df_mapped.columns:
            val = df_mapped[col].iloc[0]
            if pd.isna(val):
                pred_df[col] = np.nan
            else:
                pred_df[col] = val
        else:
            missing_cols.append(col)
            pred_df[col] = DEFAULTS.get(col, 0.0)
            
    if "missing_cols_clv" not in st.session_state:
        st.session_state["missing_cols_clv"] = []
    st.session_state["missing_cols_clv"] = list(set(st.session_state["missing_cols_clv"] + missing_cols))
            
    res_df = pred_df[feature_cols].copy()
    cat_cols = clv_artifact.get("categorical_cols", [])
    for col in cat_cols:
        if col in res_df.columns:
            res_df[col] = res_df[col].astype("category")
    return res_df

def align_clv_segment_features(row_df, clv_artifact):
    feature_cols = clv_artifact.get("segment_feature_columns")
    if feature_cols is None:
        feature_cols = clv_artifact.get("amount_feature_columns", clv_artifact.get("feature_columns"))
    
    if feature_cols is None:
        raise ValueError("CLV artifact is missing 'segment_feature_columns', 'amount_feature_columns', and 'feature_columns'.")
        
    df_mapped = row_df.copy()
    
    # Map active digital twin variables to the expected _obs training features
    purchases = float(df_mapped["purchases_90d"].iloc[0]) if "purchases_90d" in df_mapped.columns and not pd.isna(df_mapped["purchases_90d"].iloc[0]) else 0.0
    spent = float(df_mapped["total_spent_90d_mad"].iloc[0]) if "total_spent_90d_mad" in df_mapped.columns and not pd.isna(df_mapped["total_spent_90d_mad"].iloc[0]) else 0.0
    aov = float(df_mapped["avg_order_value_mad"].iloc[0]) if "avg_order_value_mad" in df_mapped.columns and not pd.isna(df_mapped["avg_order_value_mad"].iloc[0]) else 0.0
    recency = float(df_mapped["recency_days"].iloc[0]) if "recency_days" in df_mapped.columns and not pd.isna(df_mapped["recency_days"].iloc[0]) else 0.0
    
    df_mapped["frequency_obs"] = purchases
    df_mapped["total_spent_obs_mad"] = spent
    df_mapped["avg_order_value_obs_mad"] = aov
    df_mapped["recency_obs_days"] = recency
    df_mapped["transaction_count_obs"] = purchases
    df_mapped["transaction_count_future"] = purchases
    df_mapped["total_profit_obs_mad"] = spent * 0.25
    df_mapped["customer_age_days"] = recency + 90.0
    df_mapped["return_rate_obs"] = 0.0
    df_mapped["discount_rate_obs"] = 0.15
    df_mapped["category_diversity_obs"] = 1.0
    
    interval_mean = 90.0 / purchases if purchases > 0 else 90.0
    df_mapped["purchase_interval_mean_days"] = interval_mean
    df_mapped["purchase_interval_std_days"] = 10.0
    
    # Map marketing_consent value to True/False boolean format
    if "marketing_consent" in df_mapped.columns:
        mc_val = df_mapped["marketing_consent"].iloc[0]
        if mc_val in [1, 1.0, True, "True", "1"]:
            df_mapped["marketing_consent"] = True
        else:
            df_mapped["marketing_consent"] = False
    
    # Compute log/slog transforms
    df_mapped["frequency_obs_log"] = np.log1p(df_mapped["frequency_obs"])
    df_mapped["total_spent_obs_mad_log"] = np.log1p(df_mapped["total_spent_obs_mad"])
    df_mapped["avg_order_value_obs_mad_log"] = np.log1p(df_mapped["avg_order_value_obs_mad"])
    df_mapped["purchase_interval_mean_days_log"] = np.log1p(df_mapped["purchase_interval_mean_days"])
    df_mapped["purchase_interval_std_days_log"] = np.log1p(df_mapped["purchase_interval_std_days"])
    df_mapped["transaction_count_obs_log"] = np.log1p(df_mapped["transaction_count_obs"])
    df_mapped["transaction_count_future_log"] = np.log1p(purchases)
    df_mapped["total_profit_obs_mad_slog"] = np.sign(df_mapped["total_profit_obs_mad"]) * np.log1p(np.abs(df_mapped["total_profit_obs_mad"]))
    
    # Target leakage handling: compute math clv fallback and log transform it
    math_clv = compute_math_clv_from_digital_twin(df_mapped)
    if pd.isna(math_clv) or math_clv <= 0.0:
        math_clv = 0.0
    df_mapped["clv_amount_mad_slog"] = np.sign(math_clv) * np.log1p(math_clv)
    
    # Map high-cardinality categorical ID
    if "entity_id" in df_mapped.columns:
        ent_id = str(df_mapped["entity_id"].iloc[0])
        df_mapped["base_entity_id"] = ent_id.replace("P", "C")
        
    pred_df = pd.DataFrame(index=[0])
    missing_cols = []
    for col in feature_cols:
        if col in df_mapped.columns:
            val = df_mapped[col].iloc[0]
            if pd.isna(val):
                pred_df[col] = np.nan
            else:
                pred_df[col] = val
        else:
            missing_cols.append(col)
            pred_df[col] = DEFAULTS.get(col, 0.0)
            
    if "missing_cols_clv" not in st.session_state:
        st.session_state["missing_cols_clv"] = []
    st.session_state["missing_cols_clv"] = list(set(st.session_state["missing_cols_clv"] + missing_cols))
            
    res_df = pred_df[feature_cols].copy()
    cat_cols = clv_artifact.get("categorical_cols", [])
    for col in cat_cols:
        if col in res_df.columns:
            res_df[col] = res_df[col].astype("category")
    return res_df

def predict_clv(row_df, clv_artifact, ref_distribution=None):
    if clv_artifact is None:
        raise ValueError("Invalid CLV model artifact or CLV is disabled.")
        
    amount_model = clv_artifact.get("amount_model", clv_artifact.get("model"))
    amount_model_name = clv_artifact.get("best_amount_model_name", clv_artifact.get("best_model_name", "CLV Amount Model"))
    ref_vals = clv_artifact.get("clv_reference_values", [])
    
    if amount_model is None:
        raise ValueError("CLV amount model is missing in the artifact.")
        
    st.session_state["missing_cols_clv"] = []
        
    try:
        aligned_amount_features = align_clv_amount_features(row_df, clv_artifact)
        clv_val = amount_model.predict(aligned_amount_features)[0]
        ml_clv = float(clv_val)
        ml_clv_display = max(0.0, ml_clv)
    except Exception:
        ml_clv = np.nan
        ml_clv_display = np.nan
        
    math_clv = compute_math_clv_from_digital_twin(row_df.iloc[0])
    
    purchases_val = float(row_df["purchases_90d"].iloc[0] if "purchases_90d" in row_df.columns else 0)
    spent_val = float(row_df["total_spent_90d_mad"].iloc[0] if "total_spent_90d_mad" in row_df.columns else 0)
    has_history = (purchases_val > 0 and spent_val > 0)
    
    ml_clv_invalid = (pd.isna(ml_clv) or ml_clv <= 0)
    
    if ml_clv_invalid:
        final_clv = math_clv if not pd.isna(math_clv) else 0.0
        method_used = "Mathematical CLV Fallback"
    elif (not pd.isna(math_clv) and math_clv > 0 
          and ml_clv < 0.25 * math_clv 
          and has_history):
        final_clv = math_clv
        method_used = "Hybrid CLV: Mathematical Fallback"
    else:
        final_clv = ml_clv_display
        method_used = amount_model_name
        
    final_clv = max(0.0, float(final_clv))
    
    if ref_distribution is not None and len(ref_distribution) > 0:
        dist = np.sort(ref_distribution)
        pos = np.searchsorted(dist, final_clv)
        score = float(pos) / len(dist) * 100.0
    elif len(ref_vals) > 0:
        dist = np.sort(ref_vals)
        pos = np.searchsorted(dist, final_clv)
        score = float(pos) / len(dist) * 100.0
    else:
        score = 50.0
        
    score = float(np.clip(score, 0.0, 100.0))
    
    segment_model = clv_artifact.get("segment_model")
    segment_model_name = "None"
    segment_prediction_source = "Score Thresholds"
    segment_confidence = np.nan
    segment_top_3 = None
    segment = None
    
    if segment_model is not None:
        segment_model_name = clv_artifact.get("best_segment_model_name", "CLV Segment Model")
        segment_prediction_source = "Segment Classifier"
        try:
            aligned_segment_features = align_clv_segment_features(row_df, clv_artifact)
            encoded_pred = segment_model.predict(aligned_segment_features)[0]
            
            id_to_label = clv_artifact.get("id_to_label")
            segment_labels = clv_artifact.get("segment_labels", clv_artifact.get("clv_segment_labels"))
            
            if id_to_label is not None:
                if encoded_pred in id_to_label:
                    segment = id_to_label[encoded_pred]
                elif str(encoded_pred) in id_to_label:
                    segment = id_to_label[str(encoded_pred)]
                elif isinstance(encoded_pred, (int, np.integer)) and segment_labels and len(segment_labels) > encoded_pred:
                    segment = segment_labels[encoded_pred]
                else:
                    segment = str(encoded_pred)
            elif segment_labels is not None:
                if isinstance(encoded_pred, (int, np.integer)) and len(segment_labels) > encoded_pred:
                    segment = segment_labels[encoded_pred]
                else:
                    segment = str(encoded_pred)
            else:
                segment = str(encoded_pred)
                
            if hasattr(segment_model, "predict_proba"):
                proba = segment_model.predict_proba(aligned_segment_features)[0]
                if hasattr(segment_model, "classes_"):
                    classes = segment_model.classes_
                elif id_to_label is not None:
                    classes = list(id_to_label.keys())
                elif segment_labels is not None:
                    classes = list(range(len(segment_labels)))
                else:
                    classes = list(range(len(proba)))
                    
                mapped_classes = []
                for c in classes:
                    if id_to_label is not None:
                        if c in id_to_label:
                            lbl = id_to_label[c]
                        elif str(c) in id_to_label:
                            lbl = id_to_label[str(c)]
                        else:
                            lbl = str(c)
                    elif segment_labels is not None and isinstance(c, (int, np.integer)) and c < len(segment_labels):
                        lbl = segment_labels[c]
                    else:
                        lbl = str(c)
                    mapped_classes.append(lbl)
                    
                probs = list(zip(mapped_classes, proba))
                probs = sorted(probs, key=lambda x: x[1], reverse=True)
                
                segment = probs[0][0]
                segment_confidence = float(probs[0][1])
                segment_top_3 = probs[:3]
            else:
                segment_confidence = 1.0
                segment_top_3 = [(segment, 1.0)]
        except Exception as e:
            print("EXCEPTION IN SEGMENT CLASSIFIER:", e)
            segment = None
            
    if segment is None:
        segment_prediction_source = "Score Thresholds"
        segment_model_name = "None"
        if score <= 25.0:
            segment = "Low Future Value"
        elif score <= 50.0:
            segment = "Medium Future Value"
        elif score <= 75.0:
            segment = "High Future Value"
        else:
            segment = "Very High Future Value"
        segment_confidence = np.nan
        segment_top_3 = None
        
    return {
        "final_clv": final_clv,
        "score": score,
        "segment": segment,
        "method_used": method_used,
        "ml_clv": ml_clv_display,
        "math_clv": math_clv,
        "amount_model_name": amount_model_name,
        "segment_model_name": segment_model_name,
        "segment_prediction_source": segment_prediction_source,
        "segment_confidence": segment_confidence,
        "segment_top_3": segment_top_3
    }

def is_cold_start_client(row):
    # If row is a DataFrame, take the first row
    if isinstance(row, pd.DataFrame):
        entity_type = row["entity_type"].iloc[0] if "entity_type" in row.columns else None
        purchases = row["purchases_90d"].iloc[0] if "purchases_90d" in row.columns else 0
        spent = row["total_spent_90d_mad"].iloc[0] if "total_spent_90d_mad" in row.columns else 0
    else:
        entity_type = row.get("entity_type")
        purchases = row.get("purchases_90d")
        spent = row.get("total_spent_90d_mad")
        
    try:
        purchases_val = float(purchases or 0)
    except Exception:
        purchases_val = 0.0
    try:
        spent_val = float(spent or 0)
    except Exception:
        spent_val = 0.0
        
    return (
        str(entity_type).lower() == "client"
        and purchases_val <= 0
        and spent_val <= 0
    )

def update_client_clv(df, entity_id, clv_artifact):
    if clv_artifact is None:
        return df
    idx = df[df["entity_id"] == entity_id].index
    if len(idx) == 0:
        return df
    
    row_df = df.iloc[idx].copy()
    entity_type = row_df["entity_type"].iloc[0]
    if str(entity_type).lower() != "client":
        return df
        
    # Check if there is enough purchase history
    purchases = float(row_df["purchases_90d"].iloc[0]) if not pd.isna(row_df["purchases_90d"].iloc[0]) else 0.0
    total_spent = float(row_df["total_spent_90d_mad"].iloc[0]) if not pd.isna(row_df["total_spent_90d_mad"].iloc[0]) else 0.0
    
    if purchases == 0 or total_spent <= 0.0:
        df.at[idx[0], "predicted_clv_amount_mad"] = np.nan
        df.at[idx[0], "predicted_clv_score"] = np.nan
        df.at[idx[0], "predicted_clv_segment"] = "Insufficient History"
        df.at[idx[0], "clv_model_name"] = None
        df.at[idx[0], "clv_segment_model_name"] = None
        df.at[idx[0], "clv_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx[0], "clv_method_used"] = "None (Insufficient History)"
        df.at[idx[0], "ml_predicted_clv_amount_mad"] = np.nan
        df.at[idx[0], "math_clv_amount_mad"] = np.nan
        df.at[idx[0], "clv_segment_prediction_source"] = "None"
        df.at[idx[0], "clv_segment_confidence"] = np.nan
        df.at[idx[0], "clv_segment_top_3"] = None
        return df
        
    try:
        # Build reference distribution of math_clv for all Clients with history
        ref_distribution = []
        client_df = df[df["entity_type"].str.lower() == "client"]
        for _, r_c in client_df.iterrows():
            m_val = compute_math_clv_from_digital_twin(r_c)
            if not pd.isna(m_val) and m_val > 0:
                ref_distribution.append(m_val)

        # Predict CLV
        result = predict_clv(row_df, clv_artifact, ref_distribution)
        
        # Serialize top 3 safely
        top_3_val = result["segment_top_3"]
        if top_3_val is not None:
            clean_top_3 = []
            for item in top_3_val:
                label = item[0]
                prob = float(item[1])
                clean_top_3.append((label, prob))
            json_top_3 = json.dumps(clean_top_3)
        else:
            json_top_3 = None
            
        df.at[idx[0], "predicted_clv_amount_mad"] = result["final_clv"]
        df.at[idx[0], "predicted_clv_score"] = result["score"]
        df.at[idx[0], "predicted_clv_segment"] = result["segment"]
        df.at[idx[0], "clv_model_name"] = result["amount_model_name"]
        df.at[idx[0], "clv_segment_model_name"] = result["segment_model_name"]
        df.at[idx[0], "clv_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx[0], "clv_method_used"] = result["method_used"]
        df.at[idx[0], "ml_predicted_clv_amount_mad"] = result["ml_clv"]
        df.at[idx[0], "math_clv_amount_mad"] = result["math_clv"]
        df.at[idx[0], "clv_segment_prediction_source"] = result["segment_prediction_source"]
        df.at[idx[0], "clv_segment_confidence"] = result["segment_confidence"]
        df.at[idx[0], "clv_segment_top_3"] = json_top_3
        
    except Exception as e:
        st.error(f"❌ **CLV Prediction Error:** Failed to predict CLV for `{entity_id}`: {e}")
        
    return df

def assign_customer_segment(row):
    entity_type = str(row.get("entity_type", "")).strip().lower()
    
    if entity_type == "prospect":
        return {
            "customer_segment": "Prospect",
            "customer_persona": "Not Applicable Yet",
            "persona_description": "Persona will be created after conversion to Client.",
            "persona_recommended_action": "Continue nurturing until conversion.",
            "segmentation_method": "Rule-Based RFM-ES + CLV Segmentation",
            "segmentation_last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    # It is a Client.
    purchases_90d = float(row.get("purchases_90d", 0))
    predicted_clv_segment = str(row.get("predicted_clv_segment", ""))
    rfm_score = float(row.get("rfm_score", 0))
    predicted_clv_score = float(row.get("predicted_clv_score", 0))
    churn_risk_score = float(row.get("churn_risk_score", 0))
    behavioral_engagement_score = float(row.get("behavioral_engagement_score", 0))
    price_sensitivity = float(row.get("price_sensitivity", 0))
    complaint_count_90d = float(row.get("complaint_count_90d", 0))
    social_sentiment_avg = float(row.get("social_sentiment_avg", 0.5))
    recency_days = float(row.get("recency_days", 0))
    email_click_rate = float(row.get("email_click_rate", 0))
    
    segment = None
    persona = None
    description = None
    action = None
    
    # A. New Customers
    if purchases_90d <= 1 or predicted_clv_segment == "Insufficient History":
        segment = "New Customers"
        persona = "New Explorer"
        description = "Recently acquired client with limited purchase history."
        action = "Encourage second purchase using onboarding offers."
    # B. High-Value Loyalists
    elif rfm_score >= 0.75 and predicted_clv_score >= 75 and churn_risk_score < 0.35:
        segment = "High-Value Loyalists"
        persona = "Premium Loyalist"
        description = "High-value customer with strong purchase history and low churn risk."
        action = "Reward loyalty with VIP offers, early access, and premium service."
    # C. At-Risk Premium Clients
    elif predicted_clv_score >= 70 and churn_risk_score >= 0.50:
        segment = "At-Risk Premium Clients"
        persona = "Silent VIP at Risk"
        description = "Valuable customer showing churn or inactivity signals."
        action = "Trigger retention campaign and personalized follow-up."
    # D. Growth Potential Clients
    elif predicted_clv_score >= 50 and rfm_score >= 0.55 and behavioral_engagement_score >= 0.50:
        segment = "Growth Potential Clients"
        persona = "Emerging Loyalist"
        description = "Client with medium-to-high potential and strong engagement."
        action = "Use cross-selling, bundles, and loyalty incentives."
    # E. Price-Sensitive Occasional Buyers
    elif price_sensitivity >= 0.70 and predicted_clv_score < 60:
        segment = "Price-Sensitive Occasional Buyers"
        persona = "Deal Seeker"
        description = "Client who is likely motivated by price, discounts, and promotions."
        action = "Send targeted discounts and limited-time offers."
    # F. Complaint-Driven Risk Clients
    elif complaint_count_90d >= 1 or social_sentiment_avg < 0.35:
        segment = "Complaint-Driven Risk Clients"
        persona = "Frustrated Client"
        description = "Client showing dissatisfaction through complaints or negative sentiment."
        action = "Prioritize support resolution and service recovery."
    # G. Dormant Low-Value Clients
    elif recency_days >= 60 and behavioral_engagement_score < 0.30:
        segment = "Dormant Low-Value Clients"
        persona = "Sleeping Client"
        description = "Client with low recent activity and limited engagement."
        action = "Launch reactivation campaign or reduce marketing cost."
    # H. Social Advocates
    elif social_sentiment_avg >= 0.75 and email_click_rate >= 0.30:
        segment = "Social Advocates"
        persona = "Brand Advocate"
        description = "Client with positive sentiment and high engagement."
        action = "Encourage referrals, reviews, and ambassador campaigns."
    # Default
    else:
        segment = "Standard Active Clients"
        persona = "Regular Buyer"
        description = "Client with normal activity and moderate value."
        action = "Maintain engagement with personalized recommendations."
        
    return {
        "customer_segment": segment,
        "customer_persona": persona,
        "persona_description": description,
        "persona_recommended_action": action,
        "segmentation_method": "Rule-Based RFM-ES + CLV Segmentation",
        "segmentation_last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def update_customer_segmentation(df, entity_id=None):
    if entity_id is not None:
        idx = df[df["entity_id"] == entity_id].index
        if len(idx) > 0:
            res = assign_customer_segment(df.loc[idx[0]])
            for col, val in res.items():
                df.at[idx[0], col] = val
    else:
        for i, row in df.iterrows():
            res = assign_customer_segment(row)
            for col, val in res.items():
                df.at[i, col] = val
    return df

def run_customer_clustering(df, n_clusters=5):
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    
    # Filter only Clients
    client_mask = df["entity_type"].astype(str).str.lower().isin(["client", "1"])
    client_df = df[client_mask].copy()
    
    if len(client_df) < n_clusters:
        return df, None, [0.0, 0.0, 0.0]
        
    features = [
        "rfm_score", "predicted_clv_score", "churn_risk_score",
        "behavioral_engagement_score", "predictive_value_score", "decision_priority_score",
        "recency_days", "purchases_90d", "total_spent_90d_mad", "avg_order_value_mad",
        "email_open_rate", "email_click_rate", "complaint_count_90d",
        "social_sentiment_avg", "price_sensitivity", "income_power_score"
    ]
    
    X = client_df[features].copy()
    for col in features:
        X[col] = pd.to_numeric(X[col], errors="coerce")
        median_val = X[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        X[col] = X[col].fillna(median_val)
        
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    
    n_comp = min(3, X_scaled.shape[1])
    pca = PCA(n_components=n_comp)
    pca_coords = pca.fit_transform(X_scaled)
    
    if "ml_cluster_id" not in df.columns:
        df["ml_cluster_id"] = np.nan
    if "ml_cluster_label" not in df.columns:
        df["ml_cluster_label"] = None
    if "cluster_persona" not in df.columns:
        df["cluster_persona"] = None
        
    client_indices = client_df.index
    for idx, c_id in zip(client_indices, cluster_labels):
        df.at[idx, "ml_cluster_id"] = int(c_id)
        df.at[idx, "ml_cluster_label"] = f"Cluster {c_id}"
        
        c_rfm = X.iloc[cluster_labels == c_id]["rfm_score"].mean()
        c_clv = X.iloc[cluster_labels == c_id]["predicted_clv_score"].mean()
        c_churn = X.iloc[cluster_labels == c_id]["churn_risk_score"].mean()
        
        if c_rfm >= 0.70 and c_clv >= 70 and c_churn < 0.35:
            df.at[idx, "cluster_persona"] = "Cluster VIP Advocate"
        elif c_churn >= 0.50:
            df.at[idx, "cluster_persona"] = "Cluster At-Risk Client"
        elif c_rfm < 0.40:
            df.at[idx, "cluster_persona"] = "Cluster Dormant/Occasional Buyer"
        else:
            df.at[idx, "cluster_persona"] = "Cluster Standard Active"
            
    pca_cols = [f"PCA{i+1}" for i in range(n_comp)]
    pca_df = pd.DataFrame(pca_coords, columns=pca_cols)
    pca_df["cluster"] = [f"Cluster {c}" for c in cluster_labels]
    pca_df["cluster_id"] = cluster_labels
    pca_df["entity_id"] = client_df["entity_id"].values
    pca_df["dynamic_class"] = client_df["dynamic_class"].values if "dynamic_class" in client_df.columns else "Client"
    pca_df["customer_segment"] = client_df["customer_segment"].values if "customer_segment" in client_df.columns else "Standard Active"
    pca_df["cluster_persona"] = df.loc[client_indices, "cluster_persona"].values
    pca_df["rfm_score"] = client_df["rfm_score"].values if "rfm_score" in client_df.columns else 0.5
    pca_df["predicted_clv_score"] = client_df["predicted_clv_score"].values if "predicted_clv_score" in client_df.columns else 50.0
    pca_df["total_spent_90d_mad"] = client_df["total_spent_90d_mad"].values if "total_spent_90d_mad" in client_df.columns else 0.0
    pca_df["churn_risk_score"] = client_df["churn_risk_score"].values if "churn_risk_score" in client_df.columns else 0.0
    
    explained_var = pca.explained_variance_ratio_
    
    return df, pca_df, explained_var


def log_clv_before_after(event_record, old_row, new_row):
    """
    Mutates the event_record dict/Series to include CLV transition fields
    and determines if CLV has changed.
    """
    old_amt = old_row.get("predicted_clv_amount_mad")
    new_amt = new_row.get("predicted_clv_amount_mad")
    old_score = old_row.get("predicted_clv_score")
    new_score = new_row.get("predicted_clv_score")
    old_seg = old_row.get("predicted_clv_segment")
    new_seg = new_row.get("predicted_clv_segment")
    
    event_record["old_clv_amount_mad"] = old_amt if not pd.isna(old_amt) else np.nan
    event_record["new_clv_amount_mad"] = new_amt if not pd.isna(new_amt) else np.nan
    event_record["old_clv_score"] = old_score if not pd.isna(old_score) else np.nan
    event_record["new_clv_score"] = new_score if not pd.isna(new_score) else np.nan
    event_record["old_clv_segment"] = old_seg if old_seg else None
    event_record["new_clv_segment"] = new_seg if new_seg else None
    
    # Check if amount or segment changed
    amt_changed = False
    if pd.isna(old_amt) and pd.isna(new_amt):
        amt_changed = False
    elif pd.isna(old_amt) or pd.isna(new_amt):
        amt_changed = True
    else:
        amt_changed = round(float(old_amt), 2) != round(float(new_amt), 2)
        
    seg_changed = str(old_seg) != str(new_seg)
    event_record["clv_changed"] = bool(amt_changed or seg_changed)
    return event_record



# 8. Calculate AHP weights using the eigenvector method
def calculate_ahp_weights(pairwise_matrix, criteria):
    pairwise_matrix = np.array(pairwise_matrix, dtype=float)
    n = pairwise_matrix.shape[0]

    eigenvalues, eigenvectors = np.linalg.eig(pairwise_matrix)

    max_index = np.argmax(eigenvalues.real)
    max_eigenvalue = eigenvalues.real[max_index]

    principal_eigenvector = eigenvectors[:, max_index].real
    weights = principal_eigenvector / principal_eigenvector.sum()

    # Consistency Index
    CI = (max_eigenvalue - n) / (n - 1)

    # Random Index values used in AHP
    RI_dict = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49
    }

    RI = RI_dict.get(n, 1.49)

    if RI == 0:
        CR = 0.0
    else:
        CR = CI / RI

    weights_dict = {
        criteria[i]: weights[i]
        for i in range(n)
    }

    return weights_dict, CI, CR

def aggregate_ahp_matrices_geometric_mean(matrices):
    """
    Aggregate multiple expert AHP matrices using the geometric mean.
    """
    matrices = [np.array(m, dtype=float) for m in matrices]
    stacked = np.stack(matrices, axis=0)
    aggregated_matrix = np.prod(stacked, axis=0) ** (1 / len(matrices))
    return aggregated_matrix

def get_group_ahp_result():
    criteria = ["R", "F", "M", "E", "S"]

    expert_1_matrix = [
        [1,   1,   1/3, 3,   2],
        [1,   1,   1/3, 2,   2],
        [3,   3,   1,   5,   4],
        [1/3, 1/2, 1/5, 1,   1],
        [1/2, 1/2, 1/4, 1,   1]
    ]

    expert_2_matrix = [
        [1,   2,   1/4, 3,   2],
        [1/2, 1,   1/3, 2,   2],
        [4,   3,   1,   5,   4],
        [1/3, 1/2, 1/5, 1,   1],
        [1/2, 1/2, 1/4, 1,   1]
    ]

    expert_3_matrix = [
        [1,   1,   1/2, 2,   2],
        [1,   1,   1/3, 2,   3],
        [2,   3,   1,   4,   4],
        [1/2, 1/2, 1/4, 1,   1],
        [1/2, 1/3, 1/4, 1,   1]
    ]

    expert_matrices = [
        expert_1_matrix,
        expert_2_matrix,
        expert_3_matrix
    ]

    aggregated_matrix = aggregate_ahp_matrices_geometric_mean(expert_matrices)

    final_weights, final_CI, final_CR = calculate_ahp_weights(
        aggregated_matrix,
        criteria
    )

    return {
        "criteria": criteria,
        "expert_matrices": expert_matrices,
        "aggregated_matrix": aggregated_matrix,
        "weights": final_weights,
        "CI": final_CI,
        "CR": final_CR,
        "expert_count": len(expert_matrices)
    }

def calculate_rfm_from_model(df, model_artifact=None):
    temp_df = df.copy()
    
    numeric_cols = [
        "recency_days",
        "visits_30d",
        "product_views_30d",
        "cart_additions_30d",
        "purchases_90d",
        "total_spent_90d_mad",
        "avg_order_value_mad",
        "email_open_rate",
        "email_click_rate",
        "social_sentiment_avg"
    ]
    for col in numeric_cols:
        temp_df[col] = pd.to_numeric(temp_df[col], errors="coerce").fillna(0.0)
        
    is_client = temp_df["entity_type"].astype(str).str.lower().isin(["client", "1"])
    
    def quintile_score(series, reverse=False):
        if series.nunique() <= 1:
            return pd.Series(3, index=series.index)
        else:
            try:
                score = pd.qcut(
                    series.rank(method="first"),
                    q=5,
                    labels=[1, 2, 3, 4, 5]
                ).astype(int)
            except Exception:
                score = pd.Series(3, index=series.index)
        if reverse:
            score = 6 - score
        return score
        
    temp_df["R_raw"] = temp_df["recency_days"]
    
    temp_df["F_raw"] = np.where(
        is_client,
        temp_df["purchases_90d"],
        temp_df["visits_30d"] + temp_df["product_views_30d"] + temp_df["cart_additions_30d"]
    )
    
    temp_df["M_raw"] = np.where(
        is_client,
        temp_df["avg_order_value_mad"],
        0.0
    )
    
    mask_client_with_missing_aov = (
        is_client &
        (temp_df["avg_order_value_mad"] == 0) &
        (temp_df["purchases_90d"] > 0)
    )
    temp_df.loc[mask_client_with_missing_aov, "M_raw"] = (
        temp_df.loc[mask_client_with_missing_aov, "total_spent_90d_mad"] /
        temp_df.loc[mask_client_with_missing_aov, "purchases_90d"]
    )
    
    max_product_views = temp_df["product_views_30d"].max()
    if max_product_views == 0:
        normalized_product_views = 0.0
    else:
        normalized_product_views = temp_df["product_views_30d"] / max_product_views
        
    temp_df["E_raw"] = (
        0.40 * temp_df["email_click_rate"] +
        0.30 * temp_df["email_open_rate"] +
        0.30 * normalized_product_views
    )
    
    if temp_df["social_sentiment_avg"].min() < 0:
        temp_df["S_raw"] = (temp_df["social_sentiment_avg"] + 1) / 2
    else:
        temp_df["S_raw"] = temp_df["social_sentiment_avg"]
    temp_df["S_raw"] = temp_df["S_raw"].clip(0.0, 1.0)
    
    temp_df["rfm_recency_score"] = quintile_score(temp_df["R_raw"], reverse=True)
    temp_df["rfm_frequency_score"] = quintile_score(temp_df["F_raw"])
    temp_df["rfm_monetary_score"] = quintile_score(temp_df["M_raw"])
    temp_df["rfm_engagement_score"] = quintile_score(temp_df["E_raw"])
    temp_df["rfm_sentiment_score"] = quintile_score(temp_df["S_raw"])
    
    # Calculate AHP weights using the 3-expert AHP group decision logic
    ahp_result = get_group_ahp_result()
    client_ahp_weights = ahp_result["weights"]
    client_CI = ahp_result["CI"]
    client_CR = ahp_result["CR"]
    expert_count = ahp_result["expert_count"]
    
    # Prospect weights
    prospect_ahp_weights = {
        "R": client_ahp_weights["R"],
        "F": client_ahp_weights["F"],
        "E": client_ahp_weights["E"],
        "S": client_ahp_weights["S"]
    }
    total_prospect_weight = sum(prospect_ahp_weights.values())
    prospect_ahp_weights = {
        key: value / total_prospect_weight
        for key, value in prospect_ahp_weights.items()
    }
    
    client_score = (
        client_ahp_weights["R"] * temp_df["rfm_recency_score"] +
        client_ahp_weights["F"] * temp_df["rfm_frequency_score"] +
        client_ahp_weights["M"] * temp_df["rfm_monetary_score"] +
        client_ahp_weights["E"] * temp_df["rfm_engagement_score"] +
        client_ahp_weights["S"] * temp_df["rfm_sentiment_score"]
    )
    prospect_score = (
        prospect_ahp_weights["R"] * temp_df["rfm_recency_score"] +
        prospect_ahp_weights["F"] * temp_df["rfm_frequency_score"] +
        prospect_ahp_weights["E"] * temp_df["rfm_engagement_score"] +
        prospect_ahp_weights["S"] * temp_df["rfm_sentiment_score"]
    )
    
    temp_df["rfm_score_raw_1_to_5"] = np.where(
        is_client,
        client_score,
        prospect_score
    )
    
    temp_df["ahp_weight_R"] = np.where(
        is_client,
        client_ahp_weights["R"],
        prospect_ahp_weights["R"]
    )
    temp_df["ahp_weight_F"] = np.where(
        is_client,
        client_ahp_weights["F"],
        prospect_ahp_weights["F"]
    )
    temp_df["ahp_weight_M"] = np.where(
        is_client,
        client_ahp_weights["M"],
        0.0
    )
    temp_df["ahp_weight_E"] = np.where(
        is_client,
        client_ahp_weights["E"],
        prospect_ahp_weights["E"]
    )
    temp_df["ahp_weight_S"] = np.where(
        is_client,
        client_ahp_weights["S"],
        prospect_ahp_weights["S"]
    )
    
    # Write to target dataframe for traceability
    df["R_raw"] = temp_df["R_raw"]
    df["F_raw"] = temp_df["F_raw"]
    df["M_raw"] = temp_df["M_raw"]
    df["E_raw"] = temp_df["E_raw"]
    df["S_raw"] = temp_df["S_raw"]
    df["rfm_recency_score"] = temp_df["rfm_recency_score"]
    df["rfm_frequency_score"] = temp_df["rfm_frequency_score"]
    df["rfm_monetary_score"] = temp_df["rfm_monetary_score"]
    df["rfm_engagement_score"] = temp_df["rfm_engagement_score"]
    df["rfm_sentiment_score"] = temp_df["rfm_sentiment_score"]
    df["rfm_score_raw_1_to_5"] = temp_df["rfm_score_raw_1_to_5"]
    df["rfm_score"] = ((temp_df["rfm_score_raw_1_to_5"] - 1) / 4).clip(0.0, 1.0)
    df["ahp_weight_R"] = temp_df["ahp_weight_R"]
    df["ahp_weight_F"] = temp_df["ahp_weight_F"]
    df["ahp_weight_M"] = temp_df["ahp_weight_M"]
    df["ahp_weight_E"] = temp_df["ahp_weight_E"]
    df["ahp_weight_S"] = temp_df["ahp_weight_S"]
    df["ahp_group_CR"] = client_CR
    df["ahp_group_CI"] = client_CI
    df["ahp_expert_count"] = expert_count
    
    return df

# 9. Update Derived Scores
def update_scores(row_series):
    visits = float(row_series.get("visits_30d", 0))
    views = float(row_series.get("product_views_30d", 0))
    carts = float(row_series.get("cart_additions_30d", 0))
    clicks = float(row_series.get("email_click_rate", 0))
    
    behavioral_engagement_score = np.clip(
        (visits / 30.0) * 0.25 +
        (views / 80.0) * 0.30 +
        (carts / 10.0) * 0.30 +
        clicks * 0.15,
        0.0,
        1.0
    )
    
    conv = float(row_series.get("conversion_probability", 0))
    rfm = float(row_series.get("rfm_score", 0))
    sentiment = float(row_series.get("social_sentiment_avg", 0.5))
    
    predictive_value_score = np.clip(
        conv * 0.50 +
        rfm * 0.30 +
        sentiment * 0.20,
        0.0,
        1.0
    )
    
    churn = float(row_series.get("churn_risk_score", 0))
    
    decision_priority_score = np.clip(
        behavioral_engagement_score * 0.35 +
        predictive_value_score * 0.45 +
        churn * 0.20,
        0.0,
        1.0
    )
    
    row_series["behavioral_engagement_score"] = float(behavioral_engagement_score)
    row_series["predictive_value_score"] = float(predictive_value_score)
    row_series["decision_priority_score"] = float(decision_priority_score)
    return row_series

# 10. Predict Dynamic Class with Confidence Metrics
DEFAULTS = {
    'basic_profile_score': 0.5,
    'behavioral_engagement_score': 0.0,
    'predictive_value_score': 0.0,
    'decision_priority_score': 0.0,
    'recency_days': 30.0,
    'visits_30d': 0.0,
    'product_views_30d': 0.0,
    'cart_additions_30d': 0.0,
    'purchases_90d': 0.0,
    'total_spent_90d_mad': 0.0,
    'avg_order_value_mad': 0.0,
    'email_open_rate': 0.0,
    'email_click_rate': 0.0,
    'complaint_count_90d': 0.0,
    'review_score_avg': np.nan,
    'social_mentions_30d': 0.0,
    'social_sentiment_avg': 0.5,
    'rfm_score': 0.0,
    'conversion_probability': 0.0,
    'churn_risk_score': 0.0,
    'marketing_consent': True,
    'price_sensitivity': 0.5,
    'income_power_score': 0.5,
    'initial_interest_score': 0.5,
    'entity_type': 0,
    'region': 'Unknown',
    'source_channel': 'Unknown',
    'segment': 'Unknown',
    'persona': 'Unknown',
    'age_group': 'Unknown',
    'preferred_device': 'Unknown',
    'preferred_category': 'Unknown',
    'dynamic_class': 'Unknown'
}

def predict_class(model_artifact, row_df):
    model = model_artifact["model"]
    label_encoder = model_artifact["label_encoder"]
    feature_columns = model_artifact["feature_columns"]
    
    pred_df = pd.DataFrame(index=[0])
    missing_cols = []
    
    for col in feature_columns:
        if col in row_df.columns:
            val = row_df[col].iloc[0]
            if pd.isna(val):
                pred_df[col] = np.nan
            else:
                pred_df[col] = val
        else:
            missing_cols.append(col)
            pred_df[col] = DEFAULTS.get(col, 0.0)
            
    st.session_state["missing_cols_class"] = missing_cols
            
    if 'entity_type' in pred_df.columns:
        val = pred_df['entity_type'].iloc[0]
        entity_type_format = model_artifact.get("entity_type_format", "string")
        
        if entity_type_format == "string":
            if str(val).lower() in ["prospect", "0"]:
                pred_df['entity_type'] = "Prospect"
            elif str(val).lower() in ["client", "1"]:
                pred_df['entity_type'] = "Client"
            else:
                pred_df['entity_type'] = "Prospect"
        else: # numeric
            if str(val).lower() in ["prospect", "0"]:
                pred_df['entity_type'] = 0
            elif str(val).lower() in ["client", "1"]:
                pred_df['entity_type'] = 1
            else:
                pred_df['entity_type'] = 0
            
    pred_df = pred_df[feature_columns]
    
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(pred_df)[0]
        class_probs = list(zip(label_encoder.classes_, proba))
        class_probs = sorted(class_probs, key=lambda x: x[1], reverse=True)
        predicted_label = class_probs[0][0]
        confidence = class_probs[0][1]
        top_3 = class_probs[:3]
    else:
        encoded_pred = model.predict(pred_df)[0]
        predicted_label = label_encoder.inverse_transform([encoded_pred])[0]
        confidence = 1.0
        top_3 = [(predicted_label, 1.0)]
        
    return {
        "class": predicted_label,
        "confidence": confidence,
        "top_3": top_3
    }

# 11. Conversion detection check
def detect_prospect_to_client_conversion(old_row, new_row, old_class, new_class, event_type):
    was_prospect = str(old_row.get("entity_type")).lower() == "prospect"
    is_client = str(new_row.get("entity_type")).lower() == "client"
    became_client_class = any(c in str(new_class) for c in ["Client", "Active", "VIP", "Loyal", "New", "Dormant"])
    is_purchase = event_type == "purchase"
    
    if was_prospect and (is_client or became_client_class or is_purchase):
        return True
    return False

# 12. Simulate Event logic
def simulate_event(df, history, entity_id, event_type, event_value=None):
    row_idx = df[df["entity_id"] == entity_id].index
    if len(row_idx) == 0:
        return df, history, None, None, None, None, None, False, None
        
    idx = row_idx[0]
    before_row = df.loc[idx].copy()
    
    if len(history) > 0:
        max_num = max([int(x[1:]) for x in history["event_id"].values if str(x).startswith("E") and x[1:].isdigit()])
        new_event_id = f"E{max_num + 1:07d}"
    else:
        new_event_id = "E0000001"
        
    is_conversion_trigger = False
    
    entity_type = before_row.get("entity_type")
    original_entity_type = before_row.get("original_entity_type")
    converted_at = before_row.get("converted_at")
    conversion_event_id = before_row.get("conversion_event_id")
    completed_client_profile = before_row.get("completed_client_profile")
    
    recency_days = float(before_row.get("recency_days", 30))
    visits_30d = float(before_row.get("visits_30d", 0))
    product_views_30d = float(before_row.get("product_views_30d", 0))
    cart_additions_30d = float(before_row.get("cart_additions_30d", 0))
    purchases_90d = float(before_row.get("purchases_90d", 0))
    total_spent_90d_mad = float(before_row.get("total_spent_90d_mad", 0.0))
    email_open_rate = float(before_row.get("email_open_rate", 0.0))
    email_click_rate = float(before_row.get("email_click_rate", 0.0))
    complaint_count_90d = float(before_row.get("complaint_count_90d", 0))
    review_score_avg = before_row.get("review_score_avg")
    social_mentions_30d = float(before_row.get("social_mentions_30d", 0))
    social_sentiment_avg = float(before_row.get("social_sentiment_avg", 0.5))
    conversion_probability = float(before_row.get("conversion_probability", 0.0))
    churn_risk_score = float(before_row.get("churn_risk_score", 0.0))
    
    if event_type == "purchase" and str(entity_type).lower() == "prospect":
        entity_type = "Client"
        original_entity_type = "Prospect"
        converted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conversion_event_id = new_event_id
        completed_client_profile = False
        is_conversion_trigger = True
        recency_days = 0.0
        conversion_probability = 1.0
        
    changes = []
    
    if event_type == "page_visit":
        visits_30d += 1
        new_recency = max(0.0, recency_days - 2.0)
        changes.append(f"visits_30d: {int(before_row.get('visits_30d'))} ➔ {int(visits_30d)}")
        changes.append(f"recency_days: {before_row.get('recency_days')} ➔ {new_recency}")
        recency_days = new_recency
        
    elif event_type == "product_view":
        product_views_30d += 1
        visits_30d += 1
        new_recency = max(0.0, recency_days - 1.0)
        changes.append(f"product_views_30d: {int(before_row.get('product_views_30d'))} ➔ {int(product_views_30d)}")
        changes.append(f"visits_30d: {int(before_row.get('visits_30d'))} ➔ {int(visits_30d)}")
        changes.append(f"recency_days: {before_row.get('recency_days')} ➔ {new_recency}")
        recency_days = new_recency
        
    elif event_type == "add_to_cart":
        cart_additions_30d += 1
        product_views_30d += 1
        new_recency = max(0.0, recency_days - 1.0)
        new_conv = min(1.0, conversion_probability + 0.15)
        changes.append(f"cart_additions_30d: {int(before_row.get('cart_additions_30d'))} ➔ {int(cart_additions_30d)}")
        changes.append(f"product_views_30d: {int(before_row.get('product_views_30d'))} ➔ {int(product_views_30d)}")
        changes.append(f"conversion_probability: {before_row.get('conversion_probability'):.3f} ➔ {new_conv:.3f}")
        changes.append(f"recency_days: {before_row.get('recency_days')} ➔ {new_recency}")
        recency_days = new_recency
        conversion_probability = new_conv
        
    elif event_type == "purchase":
        purchases_90d += 1
        spend_val = float(event_value) if event_value is not None else 150.0
        new_spent = total_spent_90d_mad + spend_val
        new_conv = 1.0
        changes.append(f"purchases_90d: {int(before_row.get('purchases_90d'))} ➔ {int(purchases_90d)}")
        changes.append(f"total_spent_90d_mad: {before_row.get('total_spent_90d_mad'):.2f} ➔ {new_spent:.2f}")
        changes.append(f"recency_days: {before_row.get('recency_days')} ➔ 0.0")
        changes.append(f"conversion_probability: {before_row.get('conversion_probability'):.3f} ➔ 1.000")
        recency_days = 0.0
        total_spent_90d_mad = new_spent
        conversion_probability = new_conv
        
    elif event_type == "email_open":
        new_open = min(1.0, email_open_rate + 0.05)
        changes.append(f"email_open_rate: {before_row.get('email_open_rate'):.3f} ➔ {new_open:.3f}")
        email_open_rate = new_open
        
    elif event_type == "email_click":
        new_click = min(1.0, email_click_rate + 0.08)
        new_conv = min(1.0, conversion_probability + 0.05)
        changes.append(f"email_click_rate: {before_row.get('email_click_rate'):.3f} ➔ {new_click:.3f}")
        changes.append(f"conversion_probability: {before_row.get('conversion_probability'):.3f} ➔ {new_conv:.3f}")
        email_click_rate = new_click
        conversion_probability = new_conv
        
    elif event_type == "complaint":
        complaint_count_90d += 1
        new_churn = min(1.0, churn_risk_score + 0.25)
        new_sentiment = max(0.0, social_sentiment_avg - 0.20)
        changes.append(f"complaint_count_90d: {int(before_row.get('complaint_count_90d'))} ➔ {int(complaint_count_90d)}")
        changes.append(f"churn_risk_score: {before_row.get('churn_risk_score'):.3f} ➔ {new_churn:.3f}")
        changes.append(f"social_sentiment_avg: {before_row.get('social_sentiment_avg'):.3f} ➔ {new_sentiment:.3f}")
        complaint_count_90d = complaint_count_90d
        churn_risk_score = new_churn
        social_sentiment_avg = new_sentiment
        
    elif event_type == "positive_review":
        current_avg = float(review_score_avg) if not pd.isna(review_score_avg) else 3.0
        new_avg = min(5.0, (current_avg * 4.0 + 5.0) / 5.0)
        new_sentiment = min(1.0, social_sentiment_avg + 0.15)
        changes.append(f"review_score_avg: {before_row.get('review_score_avg')} ➔ {new_avg:.2f}")
        changes.append(f"social_sentiment_avg: {before_row.get('social_sentiment_avg'):.3f} ➔ {new_sentiment:.3f}")
        review_score_avg = new_avg
        social_sentiment_avg = new_sentiment
        
    elif event_type == "negative_review":
        current_avg = float(review_score_avg) if not pd.isna(review_score_avg) else 3.0
        new_avg = max(1.0, (current_avg * 4.0 + 1.0) / 5.0)
        new_churn = min(1.0, churn_risk_score + 0.20)
        changes.append(f"review_score_avg: {before_row.get('review_score_avg')} ➔ {new_avg:.2f}")
        changes.append(f"churn_risk_score: {before_row.get('churn_risk_score'):.3f} ➔ {new_churn:.3f}")
        review_score_avg = new_avg
        churn_risk_score = new_churn
        
    elif event_type == "inactivity_period":
        inactivity_days = float(event_value) if event_value is not None else 15.0
        new_recency = recency_days + inactivity_days
        new_churn = min(1.0, churn_risk_score + 0.15)
        new_visits = max(0.0, visits_30d - (inactivity_days / 5.0))
        new_views = max(0.0, product_views_30d - (inactivity_days / 2.0))
        changes.append(f"recency_days: {before_row.get('recency_days')} ➔ {new_recency}")
        changes.append(f"churn_risk_score: {before_row.get('churn_risk_score'):.3f} ➔ {new_churn:.3f}")
        changes.append(f"visits_30d: {int(before_row.get('visits_30d'))} ➔ {int(new_visits)}")
        changes.append(f"product_views_30d: {int(before_row.get('product_views_30d'))} ➔ {int(new_views)}")
        recency_days = new_recency
        churn_risk_score = new_churn
        visits_30d = new_visits
        product_views_30d = new_views
        
    elif event_type == "social_positive_mention":
        social_mentions_30d += 1
        new_sentiment = min(1.0, social_sentiment_avg + 0.20)
        changes.append(f"social_mentions_30d: {int(before_row.get('social_mentions_30d'))} ➔ {int(social_mentions_30d)}")
        changes.append(f"social_sentiment_avg: {before_row.get('social_sentiment_avg'):.3f} ➔ {new_sentiment:.3f}")
        social_mentions_30d = social_mentions_30d
        social_sentiment_avg = new_sentiment
        
    elif event_type == "social_negative_mention":
        social_mentions_30d += 1
        new_sentiment = max(0.0, social_sentiment_avg - 0.20)
        new_churn = min(1.0, churn_risk_score + 0.10)
        changes.append(f"social_mentions_30d: {int(before_row.get('social_mentions_30d'))} ➔ {int(social_mentions_30d)}")
        changes.append(f"social_sentiment_avg: {before_row.get('social_sentiment_avg'):.3f} ➔ {new_sentiment:.3f}")
        changes.append(f"churn_risk_score: {before_row.get('churn_risk_score'):.3f} ➔ {new_churn:.3f}")
        social_mentions_30d = social_mentions_30d
        social_sentiment_avg = new_sentiment
        churn_risk_score = new_churn

    df.at[idx, "entity_type"] = entity_type
    df.at[idx, "recency_days"] = recency_days
    df.at[idx, "visits_30d"] = visits_30d
    df.at[idx, "product_views_30d"] = product_views_30d
    df.at[idx, "cart_additions_30d"] = cart_additions_30d
    df.at[idx, "purchases_90d"] = purchases_90d
    df.at[idx, "total_spent_90d_mad"] = total_spent_90d_mad
    df.at[idx, "avg_order_value_mad"] = total_spent_90d_mad / purchases_90d if purchases_90d > 0 else 0.0
    df.at[idx, "email_open_rate"] = email_open_rate
    df.at[idx, "email_click_rate"] = email_click_rate
    df.at[idx, "complaint_count_90d"] = complaint_count_90d
    df.at[idx, "review_score_avg"] = review_score_avg
    df.at[idx, "social_mentions_30d"] = social_mentions_30d
    df.at[idx, "social_sentiment_avg"] = social_sentiment_avg
    df.at[idx, "conversion_probability"] = conversion_probability
    df.at[idx, "churn_risk_score"] = churn_risk_score
    df.at[idx, "original_entity_type"] = original_entity_type
    df.at[idx, "converted_at"] = converted_at
    df.at[idx, "conversion_event_id"] = conversion_event_id
    df.at[idx, "completed_client_profile"] = completed_client_profile
    
    artifact = load_model_artifact()
    df = calculate_rfm_from_model(df, artifact)
    
    df.loc[idx] = update_scores(df.loc[idx].copy())
    
    old_class = before_row.get("dynamic_class")
    if is_cold_start_client(df.loc[idx]):
        new_class = "New Client"
        df.at[idx, "dynamic_class"] = new_class
        df.at[idx, "predicted_clv_segment"] = "Insufficient History"
        df.at[idx, "predicted_clv_amount_mad"] = np.nan
        df.at[idx, "predicted_clv_score"] = np.nan
        df.at[idx, "clv_model_name"] = None
        df.at[idx, "clv_segment_model_name"] = None
        df.at[idx, "clv_method_used"] = "None (Insufficient History)"
        df.at[idx, "clv_segment_prediction_source"] = "None"
        df.at[idx, "clv_segment_confidence"] = np.nan
        df.at[idx, "clv_segment_top_3"] = None
        pred_res = {
            "class": "New Client",
            "confidence": 1.0,
            "top_3": [("New Client", 1.0)]
        }
    else:
        pred_res = predict_class(artifact, df.iloc[[idx]])
        new_class = pred_res["class"]
        df.at[idx, "dynamic_class"] = new_class
    
    prospect_to_client_conversion = detect_prospect_to_client_conversion(
        before_row, df.loc[idx], old_class, new_class, event_type
    )
    
    if prospect_to_client_conversion:
        df.at[idx, "entity_type"] = "Client"
        df.at[idx, "original_entity_type"] = "Prospect"
        df.at[idx, "converted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.at[idx, "conversion_event_id"] = new_event_id
        df.at[idx, "completed_client_profile"] = False
        is_conversion_trigger = True
        
        df = calculate_rfm_from_model(df, artifact)
        df.loc[idx] = update_scores(df.loc[idx].copy())
        if is_cold_start_client(df.loc[idx]):
            new_class = "New Client"
            df.at[idx, "dynamic_class"] = new_class
            df.at[idx, "predicted_clv_segment"] = "Insufficient History"
            df.at[idx, "predicted_clv_amount_mad"] = np.nan
            df.at[idx, "predicted_clv_score"] = np.nan
            df.at[idx, "clv_model_name"] = None
            df.at[idx, "clv_segment_model_name"] = None
            df.at[idx, "clv_method_used"] = "None (Insufficient History)"
            df.at[idx, "clv_segment_prediction_source"] = "None"
            df.at[idx, "clv_segment_confidence"] = np.nan
            df.at[idx, "clv_segment_top_3"] = None
            pred_res = {
                "class": "New Client",
                "confidence": 1.0,
                "top_3": [("New Client", 1.0)]
            }
        else:
            pred_res = predict_class(artifact, df.iloc[[idx]])
            new_class = pred_res["class"]
            df.at[idx, "dynamic_class"] = new_class
        
    # Recalculate CLV for Clients on specific events
    clv_artifact = load_clv_model_artifact()
    if str(df.loc[idx, "entity_type"]).lower() == "client" and event_type in ["purchase", "complaint", "negative_review", "positive_review", "inactivity_period"]:
        if not is_cold_start_client(df.loc[idx]):
            df = update_client_clv(df, entity_id, clv_artifact)
        else:
            df.at[idx, "predicted_clv_segment"] = "Insufficient History"
            df.at[idx, "predicted_clv_amount_mad"] = np.nan
            df.at[idx, "predicted_clv_score"] = np.nan
            df.at[idx, "clv_model_name"] = None
            df.at[idx, "clv_segment_model_name"] = None
            df.at[idx, "clv_method_used"] = "None (Insufficient History)"
            df.at[idx, "clv_segment_prediction_source"] = "None"
            df.at[idx, "clv_segment_confidence"] = np.nan
            df.at[idx, "clv_segment_top_3"] = None
        
    # Update customer segmentation/persona
    df = update_customer_segmentation(df, entity_id)
        
    class_changed = bool(old_class != new_class)
    event_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    changed_vars_list = []
    before_vals_dict = {}
    after_vals_dict = {}
    
    audit_cols = [
        "entity_type", "dynamic_class", "recency_days", "visits_30d", 
        "product_views_30d", "cart_additions_30d", "purchases_90d", 
        "total_spent_90d_mad", "avg_order_value_mad", "rfm_score", 
        "conversion_probability", "churn_risk_score", "behavioral_engagement_score", 
        "predictive_value_score", "decision_priority_score",
        "predicted_clv_amount_mad", "predicted_clv_score", "predicted_clv_segment",
        "clv_model_name", "clv_segment_model_name", "clv_method_used",
        "clv_segment_prediction_source", "clv_segment_confidence",
        "ml_predicted_clv_amount_mad", "math_clv_amount_mad",
        "customer_segment", "customer_persona", "persona_recommended_action"
    ]
    
    for c in audit_cols:
        b_val = before_row.get(c)
        a_val = df.loc[idx, c]
        
        has_chg = False
        if safe_isna(b_val) and safe_isna(a_val):
            has_chg = False
        elif safe_isna(b_val) or safe_isna(a_val):
            has_chg = True
        else:
            try:
                has_chg = round(float(b_val), 4) != round(float(a_val), 4)
            except Exception:
                has_chg = str(b_val) != str(a_val)
                
        if has_chg:
            changed_vars_list.append(c)
            
        before_vals_dict[c] = str(b_val) if not safe_isna(b_val) else None
        after_vals_dict[c] = str(a_val) if not safe_isna(a_val) else None

        
    hist_record = {
        "event_id": new_event_id,
        "entity_id": entity_id,
        "event_type": event_type,
        "event_date": event_date_str,
        "old_class": old_class,
        "new_class": new_class,
        "class_changed": class_changed,
        "old_entity_type": before_row.get("entity_type"),
        "new_entity_type": df.loc[idx, "entity_type"],
        "prospect_to_client_conversion": is_conversion_trigger,
        "completed_client_profile": False,
        "changed_variables": json.dumps(changed_vars_list),
        "before_values": json.dumps(before_vals_dict),
        "after_values": json.dumps(after_vals_dict)
    }
    # Log CLV old/new values and set clv_changed flag
    hist_record = log_clv_before_after(hist_record, before_row, df.loc[idx])
    history_row = pd.DataFrame([hist_record])

    
    history = pd.concat([history_row, history], ignore_index=True)
    storage_manager.save_entity_snapshot(df, entity_id, history)
    
    return df, history, before_row, df.loc[idx], old_class, new_class, pred_res, is_conversion_trigger, new_event_id


# 13. Create New Entity logic
def create_new_entity(df, entity_data):
    entity_type = entity_data["entity_type"]
    prefix = "P" if entity_type == "Prospect" else "C"
    
    existing_ids = df[df["entity_id"].str.startswith(prefix)]["entity_id"]
    if len(existing_ids) > 0:
        max_num = max([int(x[1:]) for x in existing_ids])
        new_id = f"{prefix}{max_num + 1:05d}"
    else:
        new_id = f"{prefix}00001"
        
    if entity_type == "Client":
        recency = float(entity_data.get("initial_recency_days", 0.0))
        visits = float(entity_data.get("initial_visits_30d", 1.0))
        views = float(entity_data.get("initial_product_views_30d", 1.0))
        carts = float(entity_data.get("initial_cart_additions_30d", 1.0))
        purchases = float(entity_data.get("initial_purchase_count", 1.0))
        spent = float(entity_data.get("initial_total_spent_mad", 250.0))
        opens = float(entity_data.get("initial_email_open_rate", 0.0))
        clicks = float(entity_data.get("initial_email_click_rate", 0.0))
        conversion_prob = 1.0
    else:
        recency = 30.0
        visits = 0.0
        views = 0.0
        carts = 0.0
        purchases = 0.0
        spent = 0.0
        opens = 0.0
        clicks = 0.0
        conversion_prob = 0.0

    new_row = {
        "entity_id": new_id,
        "entity_type": entity_type,
        "region": entity_data["region"],
        "source_channel": entity_data["source_channel"],
        "segment": entity_data["segment"],
        "persona": entity_data["persona"],
        "age_group": entity_data["age_group"],
        "preferred_device": entity_data["preferred_device"],
        "preferred_category": entity_data["preferred_category"],
        "marketing_consent": entity_data["marketing_consent"],
        "price_sensitivity": float(entity_data["price_sensitivity"]),
        "income_power_score": float(entity_data["income_power_score"]),
        "initial_interest_score": float(entity_data["initial_interest_score"]),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
        "recency_days": recency,
        "visits_30d": visits,
        "product_views_30d": views,
        "cart_additions_30d": carts,
        "purchases_90d": purchases,
        "total_spent_90d_mad": spent,
        "avg_order_value_mad": spent / purchases if purchases > 0 else 0.0,
        "email_open_rate": opens,
        "email_click_rate": clicks,
        "complaint_count_90d": 0.0,
        "review_score_avg": np.nan,
        "social_mentions_30d": 0.0,
        "social_sentiment_avg": 0.5,
        "conversion_probability": conversion_prob,
        "churn_risk_score": 0.0,
        "basic_profile_score": 0.5,
        "rfm_score": 0.0,
        "original_entity_type": None,
        "converted_at": None,
        "conversion_event_id": None,
        "completed_client_profile": None,
        "age": np.nan,
        "sex": None,
        "email": None,
        "customer_type": None,
        "household_size": np.nan,
        "phone_number": None,
        "company_name": None,
        "job_title": None,
        "city": None,
        "address": None
    }
    
    new_row_df = pd.DataFrame([new_row])
    df = pd.concat([df, new_row_df], ignore_index=True)
    
    artifact = load_model_artifact()
    df = calculate_rfm_from_model(df, artifact)
    
    idx = df[df["entity_id"] == new_id].index[0]
    df.loc[idx] = update_scores(df.loc[idx].copy())
    
    if is_cold_start_client(df.loc[idx]):
        initial_class = "New Client"
        df.at[idx, "dynamic_class"] = initial_class
        df.at[idx, "predicted_clv_segment"] = "Insufficient History"
        df.at[idx, "predicted_clv_amount_mad"] = np.nan
        df.at[idx, "predicted_clv_score"] = np.nan
        df.at[idx, "clv_model_name"] = None
        df.at[idx, "clv_segment_model_name"] = None
        df.at[idx, "clv_method_used"] = "None (Insufficient History)"
        df.at[idx, "clv_segment_prediction_source"] = "None"
        df.at[idx, "clv_segment_confidence"] = np.nan
        df.at[idx, "clv_segment_top_3"] = None
        df.at[idx, "clv_last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Predict CLV for client
        if entity_type == "Client":
            clv_art = load_clv_model_artifact()
            df = update_client_clv(df, new_id, clv_art)
            
        pred_res = predict_class(artifact, df.iloc[[idx]])
        initial_class = pred_res["class"]
        df.at[idx, "dynamic_class"] = initial_class
        
    # Update customer segmentation/persona
    df = update_customer_segmentation(df, new_id)
        
    # Reload or fetch history directly
    _, history = get_data()
    storage_manager.save_entity_snapshot(df, new_id, history)
    
    return df, new_id, initial_class


def update_client_profile(df, entity_id, profile_data):
    idx = df[df["entity_id"] == entity_id].index[0]
    df.at[idx, "age"] = profile_data["age"]
    df.at[idx, "sex"] = profile_data["sex"]
    df.at[idx, "email"] = profile_data["email"]
    df.at[idx, "customer_type"] = profile_data["customer_type"]
    df.at[idx, "company_name"] = profile_data["company_name"]
    df.at[idx, "job_title"] = profile_data["job_title"]
    df.at[idx, "household_size"] = profile_data["household_size"]
    df.at[idx, "phone_number"] = profile_data["phone_number"]
    df.at[idx, "city"] = profile_data["city"]
    df.at[idx, "address"] = profile_data["address"]
    df.at[idx, "completed_client_profile"] = True
    df = update_customer_segmentation(df, entity_id)
    return df

# Safe dialog fallback wrapper
if hasattr(st, "dialog"):
    @st.dialog("Complete / Edit Client Profile")
    def show_client_completion_form(entity_id, is_edit=False):
        render_dialog_ui(entity_id, is_edit)
else:
    def show_client_completion_form(entity_id, is_edit=False):
        st.warning("⚠️ Native popup modal is not available. Rendering profile form below.")
        with st.container():
            render_dialog_ui(entity_id, is_edit)

def render_dialog_ui(entity_id, is_edit=False):
    global df_data, df_history
    entity_row = df_data[df_data["entity_id"] == entity_id].iloc[0]
    
    st.markdown(f"### Profile for `{entity_id}`")
    if is_edit:
        st.write("Modify the demographic details for this client.")
    else:
        st.write("This entity converted from a **Prospect** to a **Client**! Please enrich their profile below.")
        
    default_age = int(entity_row["age"]) if not pd.isna(entity_row.get("age")) else 25
    default_sex = entity_row.get("sex") if entity_row.get("sex") else "Male"
    default_email = entity_row.get("email") if entity_row.get("email") else ""
    default_cust_type = entity_row.get("customer_type") if entity_row.get("customer_type") else "B2C"
    default_hh_size = int(entity_row["household_size"]) if not pd.isna(entity_row.get("household_size")) else 1
    default_phone = entity_row.get("phone_number") if entity_row.get("phone_number") else ""
    default_company = entity_row.get("company_name") if entity_row.get("company_name") else ""
    default_job = entity_row.get("job_title") if entity_row.get("job_title") else ""
    default_city = entity_row.get("city") if entity_row.get("city") else ""
    default_addr = entity_row.get("address") if entity_row.get("address") else ""

    customer_type = st.selectbox(
        "Customer Type (Required):", 
        ["B2C", "B2B"], 
        index=0 if default_cust_type == "B2C" else 1,
        key="dlg_cust_type"
    )
    
    age = st.number_input(
        "Age (Required, 16-100):", 
        min_value=16, 
        max_value=100, 
        value=default_age, 
        step=1, 
        key="dlg_age"
    )
    
    sex = st.selectbox(
        "Sex (Required):", 
        ["Male", "Female", "Other", "Prefer not to say"], 
        index=["Male", "Female", "Other", "Prefer not to say"].index(default_sex) if default_sex in ["Male", "Female", "Other", "Prefer not to say"] else 0,
        key="dlg_sex"
    )
    
    email = st.text_input(
        "Email (Required):", 
        value=default_email, 
        key="dlg_email"
    )
    
    company_name = ""
    job_title = ""
    household_size = 1
    
    if customer_type == "B2B":
        company_name = st.text_input("Company Name (Required for B2B):", value=default_company, key="dlg_company")
        job_title = st.text_input("Job Title (Optional):", value=default_job, key="dlg_job")
    else:
        household_size = st.number_input("Household Size (Optional, default 1):", min_value=1, max_value=20, value=default_hh_size, step=1, key="dlg_hh")
        
    phone_number = st.text_input("Phone Number (Optional):", value=default_phone, key="dlg_phone")
    city = st.text_input("City (Optional):", value=default_city, key="dlg_city")
    address = st.text_area("Address (Optional):", value=default_addr, key="dlg_address")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        save_clicked = st.button("Save Profile & Close", key="dlg_save_btn")
    with col_btn2:
        cancel_clicked = st.button("Cancel & Skip Enrichment", key="dlg_cancel_btn")
        
    if save_clicked:
        if not email:
            st.error("❌ Email is required.")
        elif not validate_email(email):
            st.error("❌ Invalid email format.")
        elif customer_type == "B2B" and not company_name:
            st.error("❌ Company Name is required for B2B client type.")
        else:
            profile_data = {
                "age": int(age),
                "sex": sex,
                "email": email,
                "customer_type": customer_type,
                "company_name": company_name if customer_type == "B2B" else None,
                "job_title": job_title if customer_type == "B2B" else None,
                "household_size": int(household_size) if customer_type == "B2C" else None,
                "phone_number": phone_number if phone_number else None,
                "city": city if city else None,
                "address": address if address else None
            }
            
            df_data = update_client_profile(df_data, entity_id, profile_data)
            
            # Predict CLV upon conversion if enough history exists
            clv_art = load_clv_model_artifact()
            df_data = update_client_clv(df_data, entity_id, clv_art)
            
            if not is_edit and st.session_state.get("conversion_event_id"):
                ev_id = st.session_state["conversion_event_id"]
                h_idx = df_history[df_history["event_id"] == ev_id].index
                if len(h_idx) > 0:
                    df_history.at[h_idx[0], "completed_client_profile"] = True
                    
            storage_manager.save_entity_snapshot(df_data, entity_id, df_history)
            
            st.session_state["conversion_form_open"] = False
            st.session_state["edit_form_open"] = False
            st.session_state["profile_completed"] = True
            
            st.success("✅ Client profile saved successfully!")
            st.rerun()
            
    if cancel_clicked:
        if not is_edit:
            idx = df_data[df_data["entity_id"] == entity_id].index[0]
            df_data.at[idx, "completed_client_profile"] = False
            
            if st.session_state.get("conversion_event_id"):
                ev_id = st.session_state["conversion_event_id"]
                h_idx = df_history[df_history["event_id"] == ev_id].index
                if len(h_idx) > 0:
                    df_history.at[h_idx[0], "completed_client_profile"] = False
                    
            storage_manager.save_entity_snapshot(df_data, entity_id, df_history)
            st.warning("⚠️ Profile enrichment skipped. You can edit this profile later.")
            
        st.session_state["conversion_form_open"] = False
        st.session_state["edit_form_open"] = False
        st.rerun()


# Execute Streamlit layout rendering only under __main__ scope
if __name__ == "__main__":
    df_data, df_history = get_data()
    df_data = ensure_client_columns(df_data)
    df_history = ensure_history_columns(df_history)
    
    if "missing_cols_class" not in st.session_state:
        st.session_state["missing_cols_class"] = []
    if "missing_cols_clv" not in st.session_state:
        st.session_state["missing_cols_clv"] = []
        
    model_artifact = load_model_artifact()
    active_model = model_artifact.get('best_model_name', 'Dynamic Classification Model') if model_artifact else "Dynamic Classification Model"
    df_data = calculate_rfm_from_model(df_data, model_artifact)
    df_data = update_customer_segmentation(df_data)
    clv_artifact = load_clv_model_artifact()

    if "conversion_form_open" not in st.session_state:
        st.session_state["conversion_form_open"] = False
    if "pending_conversion_entity_id" not in st.session_state:
        st.session_state["pending_conversion_entity_id"] = None
    if "conversion_event_id" not in st.session_state:
        st.session_state["conversion_event_id"] = None
    if "profile_completed" not in st.session_state:
        st.session_state["profile_completed"] = False
    if "edit_form_open" not in st.session_state:
        st.session_state["edit_form_open"] = False
    if "pending_edit_entity_id" not in st.session_state:
        st.session_state["pending_edit_entity_id"] = None
    # ── Active page tracker (replaces radio)
    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Dashboard Overview"

    if st.session_state.get("conversion_form_open") and st.session_state.get("pending_conversion_entity_id"):
        show_client_completion_form(st.session_state["pending_conversion_entity_id"], is_edit=False)

    if st.session_state.get("edit_form_open") and st.session_state.get("pending_edit_entity_id"):
        show_client_completion_form(st.session_state["pending_edit_entity_id"], is_edit=True)


    # ── Sidebar ──────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div class='sidebar-brand'>
        <div class='brand-mark'>O</div>
        <div class='brand-copy'>
            <div class='brand-title'>OSMOS</div>
            <div class='brand-subtitle'>Digital Twin Platform</div>
        </div>
    </div>
    <div class='sidebar-rule'></div>
    """, unsafe_allow_html=True)

    # ── Custom nav menu ──────────────────────────────────────────
    _pages = [
        ("Dashboard Overview", "📊"),
        ("Entity Profile",     "👤"),
        ("Customer Segments & Personas", "🎯"),
        ("Digital Twin & Persona", "🧬"),
        ("Campaign Simulation", "🚀"),
        ("Simulate Event",     "⚡"),
        ("Create New Entity",  "➕"),
        ("Database Intelligence", "🧠"),
    ]


    _active = st.session_state["active_page"]

    # Inject base nav button CSS
    _nav_base = (
        "<style>"
        "[data-testid='stSidebar'] .stButton > button {"
        "width:100%!important;background:rgba(255,255,255,0.025)!important;"
        "border:1px solid rgba(255,255,255,0.07)!important;border-radius:10px!important;"
        "color:#94a3b8!important;font-size:13.5px!important;font-weight:600!important;"
        "padding:12px 16px!important;text-align:left!important;margin-bottom:6px!important;"
        "transition:all 0.2s cubic-bezier(0.4,0,0.2,1)!important;box-shadow:none!important;"
        "letter-spacing:0!important;line-height:1.4!important;transform:none!important;}"
        "[data-testid='stSidebar'] .stButton > button:hover {"
        "background:linear-gradient(90deg,rgba(34,211,238,0.12),rgba(99,102,241,0.06))!important;border-color:rgba(34,211,238,0.35)!important;"
        "color:#f8fafc!important;transform:translateX(4px)!important;"
        "box-shadow:0 6px 20px rgba(0,0,0,0.25)!important;}"
        "</style>"
    )
    st.sidebar.markdown(_nav_base, unsafe_allow_html=True)

    # Render nav buttons with active state
    for _pid, _icon in _pages:
        _is_act = _active == _pid
        if _is_act:
            _act = (
                "<style>[data-testid='stSidebar'] button[title='"
                + _pid
                + "']{background:linear-gradient(90deg,rgba(34,211,238,0.18),rgba(99,102,241,0.08))!important;"
                "border-color:rgba(34,211,238,0.5)!important;color:#ffffff!important;"
                "font-weight:700!important;box-shadow:0 4px 16px rgba(34,211,238,0.18),-4px 0 0 #22d3ee!important;}"
                "</style>"
            )
            st.sidebar.markdown(_act, unsafe_allow_html=True)
        _label = ("● " if _is_act else "  ") + _icon + "  " + _pid
        if st.sidebar.button(_label, key="nav_" + _pid, width="stretch", help=_pid):
            st.session_state["active_page"] = _pid
            st.rerun()

    page = st.session_state["active_page"]
    st.sidebar.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Sidebar model panels
    
    # ── Panel 1: Dynamic Classification Model ──
    class_status = "⚠️ Missing"
    class_model_name = "N/A"
    class_selection_metric = "N/A"
    class_f1_str = "N/A"
    class_entity_format = "N/A"
    class_rfm_version = "N/A"
    class_export_date_val = "N/A"
    
    if model_artifact:
        class_status = "✅ Loaded"
        class_model_name = model_artifact.get('best_model_name', 'Dynamic Classification Model')
        class_selection_metric = model_artifact.get('selection_metric', 'f1_macro')
        class_entity_format = model_artifact.get('entity_type_format', 'string')
        class_rfm_version = model_artifact.get('rfm_version', 'RFM_ES_3_EXPERT_AHP')
        class_export_date_val = model_artifact.get('export_date', 'N/A')
        
        if "results" in model_artifact:
            results_df = model_artifact["results"]
            if isinstance(results_df, pd.DataFrame):
                matching_rows = results_df[results_df["model"] == class_model_name]
                if len(matching_rows) > 0:
                    for f1_col in ["f1_macro", "f1", "accuracy", "F1"]:
                        if f1_col in matching_rows.columns:
                            class_f1_str = f"{matching_rows[f1_col].values[0]:.4f}"
                            break
                            
    st.sidebar.markdown(f"""
    <div style='background: rgba(34,211,238,0.06); border: 1px solid rgba(34,211,238,0.2);
                border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; backdrop-filter: blur(10px);'>
        <div style='font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 8px; font-weight: 700;'>Dynamic Classification Model</div>
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 10px;'>
            <span style='font-size: 18px;'>🤖</span>
            <span style='font-size: 13px; font-weight: 700; color: #22d3ee; font-family: "JetBrains Mono", monospace;'>{class_model_name}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Status</span>
            <span style='color: #cbd5e1; font-weight: 600;'>{class_status}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Selection Metric</span>
            <span style='color: #cbd5e1; font-weight: 600;'>{class_selection_metric}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>F1-Macro</span>
            <span style='color: #10b981; font-weight: 700; font-family: "JetBrains Mono", monospace;'>{class_f1_str}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Entity Type Format</span>
            <span style='color: #cbd5e1; font-weight: 600;'>{class_entity_format}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px;'>
            <span style='color: #64748b;'>RFM Version</span>
            <span style='color: #cbd5e1; font-weight: 600; font-size: 10.5px;'>{class_rfm_version}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel 2: CLV Models ──
    clv_status = "⚠️ Missing"
    clv_amt_model = "N/A"
    clv_seg_model = "N/A"
    clv_export_date_str = "N/A"
    clv_amt_metric = "N/A"
    clv_seg_f1_str = "N/A"
    clv_seg_avail = "No"
    
    clv_art_local = clv_artifact if 'clv_artifact' in locals() or 'clv_artifact' in globals() else None
    
    if clv_art_local:
        clv_status = "✅ Loaded"
        clv_amt_model = clv_art_local.get("best_amount_model_name", clv_art_local.get("best_model_name", "CLV Amount Model"))
        clv_export_date_str = clv_art_local.get("export_date", "N/A")
        
        if "results" in clv_art_local:
            res_df = clv_art_local["results"]
            if isinstance(res_df, pd.DataFrame):
                matching = res_df[res_df["model"] == clv_amt_model]
                if len(matching) > 0:
                    metrics_found = []
                    for m in ["MAE", "mae", "R2", "r2", "RMSE", "rmse"]:
                        if m in matching.columns:
                            metrics_found.append(f"{m}: {matching[m].values[0]:.4f}")
                    if metrics_found:
                        clv_amt_metric = ", ".join(metrics_found)
                        
        if "segment_model" in clv_art_local:
            clv_seg_avail = "Yes"
            clv_seg_model = clv_art_local.get("best_segment_model_name", "CLV Segment Classifier")
            if "segment_results" in clv_art_local:
                seg_res = clv_art_local["segment_results"]
                if isinstance(seg_res, pd.DataFrame):
                    matching = seg_res[seg_res["model"] == clv_seg_model]
                    if len(matching) > 0:
                        for f1_col in ["f1_macro", "f1", "accuracy", "F1"]:
                            if f1_col in matching.columns:
                                clv_seg_f1_str = f"{matching[f1_col].values[0]:.4f}"
                                break
        else:
            clv_seg_model = "N/A (Threshold-based)"
            
    st.sidebar.markdown(f"""
    <div style='background: rgba(139,92,246,0.06); border: 1px solid rgba(139,92,246,0.2);
                border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; backdrop-filter: blur(10px);'>
        <div style='font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 8px; font-weight: 700;'>CLV Models</div>
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 10px;'>
            <span style='font-size: 18px;'>💰</span>
            <span style='font-size: 13px; font-weight: 700; color: #a78bfa; font-family: "JetBrains Mono", monospace;'>{clv_amt_model}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Status</span>
            <span style='color: #cbd5e1; font-weight: 600;'>{clv_status}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Segment Model</span>
            <span style='color: #cbd5e1; font-weight: 600; font-size: 10.5px;'>{clv_seg_model}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Segment Classifier</span>
            <span style='color: #cbd5e1; font-weight: 600;'>{clv_seg_avail}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 4px;'>
            <span style='color: #64748b;'>Amt Metric</span>
            <span style='color: #10b981; font-weight: 700; font-family: "JetBrains Mono", monospace;'>{clv_amt_metric}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px;'>
            <span style='color: #64748b;'>Seg F1-Macro</span>
            <span style='color: #10b981; font-weight: 700; font-family: "JetBrains Mono", monospace;'>{clv_seg_f1_str}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel 3: Storage Backend ──
    is_pg = storage_manager.is_postgres_enabled()
    fallback_active, fallback_reason = storage_manager.get_fallback_status()
    
    if fallback_active:
        backend_label = "Excel (Fallback)"
        backend_color = "#f43f5e" # Rose/Red
        backend_status_text = f"PostgreSQL failed: {fallback_reason[:30]}..."
    elif is_pg:
        backend_label = "PostgreSQL"
        backend_color = "#10b981" # Emerald/Green
        backend_status_text = "Active & Connected"
    else:
        backend_label = "Excel"
        backend_color = "#cbd5e1" # Slate/Grey
        backend_status_text = "Active & Local File"
        
    st.sidebar.markdown(f"""
    <div style='background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.2);
                border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; backdrop-filter: blur(10px);'>
        <div style='font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 8px; font-weight: 700;'>Storage Backend</div>
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 10px;'>
            <span style='font-size: 18px;'>💾</span>
            <span style='font-size: 13px; font-weight: 700; color: {backend_color}; font-family: "JetBrains Mono", monospace;'>{backend_label}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px;'>
            <span style='color: #64748b;'>Status</span>
            <span style='color: {backend_color}; font-weight: 600; font-size: 10.5px;'>{backend_status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel 4: LLM Assistant ──
    from llm.llm_client import check_llm_available
    from llm.llm_config import is_llm_enabled, get_llm_model
    
    if not is_llm_enabled():
        llm_label = "Disabled"
        llm_color = "#94a3b8"  # Slate/Grey
        llm_status_text = "OSMOS_LLM_ENABLED=false"
    else:
        llm_avail, llm_reason = check_llm_available()
        if llm_avail:
            llm_label = "Enabled"
            llm_color = "#34d399"  # Emerald/Green
            llm_status_text = f"Connected: {get_llm_model()}"
        else:
            llm_label = "Unavailable"
            llm_color = "#fb7185"  # Rose/Red
            llm_status_text = llm_reason[:30]
            
    st.sidebar.markdown(f"""
    <div style='background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.2);
                border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; backdrop-filter: blur(10px);'>
        <div style='font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 8px; font-weight: 700;'>LLM Assistant</div>
        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 10px;'>
            <span style='font-size: 18px;'>🧠</span>
            <span style='font-size: 13px; font-weight: 700; color: {llm_color}; font-family: "JetBrains Mono", monospace;'>{llm_label}</span>
        </div>
        <div style='display: flex; justify-content: space-between; font-size: 11.5px;'>
            <span style='color: #64748b;'>Status</span>
            <span style='color: {llm_color}; font-weight: 600; font-size: 10.5px;'>{llm_status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # ── Model Diagnostics Expander ──
    with st.sidebar.expander("🛠️ Model Diagnostics"):
        class_loaded_yesno = "Yes" if model_artifact else "No"
        clv_loaded_yesno = "Yes" if clv_art_local else "No"
        
        class_feat_count = len(model_artifact.get("feature_columns", [])) if model_artifact else 0
        clv_amt_feat_count = len(clv_art_local.get("amount_feature_columns", clv_art_local.get("feature_columns", []))) if clv_art_local else 0
        clv_seg_feat_count = len(clv_art_local.get("segment_feature_columns", [])) if clv_art_local else 0
        if clv_art_local and clv_seg_feat_count == 0:
            clv_seg_feat_count = clv_amt_feat_count
            
        class_exp_date = class_export_date_val if model_artifact else "N/A"
        clv_exp_date = clv_export_date_str if clv_art_local else "N/A"
        
        ent_type_fmt = class_entity_format if model_artifact else "N/A"
        rfm_ver = class_rfm_version if model_artifact else "N/A"
        
        st.markdown(f"""
        **Classification Loaded:** {class_loaded_yesno}
        **CLV Loaded:** {clv_loaded_yesno}
        **Class. Features:** {class_feat_count}
        **CLV Amt Features:** {clv_amt_feat_count}
        **CLV Seg Features:** {clv_seg_feat_count}
        **Class. Export Date:** {class_exp_date}
        **CLV Export Date:** {clv_exp_date}
        **Entity Type Format:** {ent_type_fmt}
        **RFM Version:** {rfm_ver}
        """)
        
        missing_cols_class = st.session_state.get("missing_cols_class", [])
        missing_cols_clv = st.session_state.get("missing_cols_clv", [])
        if missing_cols_class:
            st.warning(f"⚠️ Missing Class. Cols: {', '.join(missing_cols_class)}")
        if missing_cols_clv:
            st.warning(f"⚠️ Missing CLV Cols: {', '.join(missing_cols_clv)}")
            
        st.markdown("<p style='font-size: 11px; color: #94a3b8; margin-top: 10px;'>After replacing model files, click Reload Models to avoid using cached artifacts.</p>", unsafe_allow_html=True)
        if st.button("Reload Models", width="stretch"):
            st.cache_resource.clear()
            st.cache_data.clear()
            st.rerun()

    st.sidebar.markdown("""
    <div class='privacy-card'>
        <strong style='color:#fb7185;'>Privacy Notice</strong><br>
        Email, Phone & Address are personal data stored for local prototype testing only.
        Production deployments must enforce encrypted storage & access controls.
    </div>
    """, unsafe_allow_html=True)

    def render_clv_dashboard(df):
        all_clients = df[df["entity_type"] == "Client"]
        evaluated_count = len(all_clients)
        
        clients_with_val = all_clients[all_clients["predicted_clv_amount_mad"].notna()]
        
        avg_clv = clients_with_val["predicted_clv_amount_mad"].mean() if len(clients_with_val) > 0 else 0.0
        total_clv = clients_with_val["predicted_clv_amount_mad"].sum() if len(clients_with_val) > 0 else 0.0
        vh_count = len(all_clients[all_clients["predicted_clv_segment"] == "Very High Future Value"])
        low_count = len(all_clients[all_clients["predicted_clv_segment"] == "Low Future Value"])
        insufficient_count = len(all_clients[all_clients["predicted_clv_segment"] == "Insufficient History"])
        
        st.markdown("<div class='section-header' style='margin-top:16px;'><span class='icon'>💰</span><span class='title'>Customer Lifetime Value KPIs</span></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='kpi-container'>
            <div class='kpi-card'>
                <span class='kpi-icon'>📊</span>
                <div class='kpi-val color-prospect'>{avg_clv:.2f} MAD</div>
                <div class='kpi-label'>Average Final CLV</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>💎</span>
                <div class='kpi-val color-client'>{total_clv:.2f} MAD</div>
                <div class='kpi-label'>Total Future Value</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>⚡</span>
                <div class='kpi-val color-vip'>{vh_count}</div>
                <div class='kpi-label'>Very High Value Clients</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>📉</span>
                <div class='kpi-val color-churn'>{low_count}</div>
                <div class='kpi-label'>Low Value Clients</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>❄️</span>
                <div class='kpi-val color-cold'>{insufficient_count}</div>
                <div class='kpi-label'>Insufficient History</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>👥</span>
                <div class='kpi-val color-total'>{evaluated_count}</div>
                <div class='kpi-label'>Clients Evaluated</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Render segment distribution bar chart
        st.markdown("<div class='section-header'><span class='icon'>📈</span><span class='title'>CLV Segment Distribution</span></div>", unsafe_allow_html=True)
        with st.container(border=True):
            seg_counts = df[df["entity_type"] == "Client"]["predicted_clv_segment"].value_counts().reset_index()
            seg_counts.columns = ["CLV Segment", "Count"]
            
            # Ensure all segments are represented
            all_segs = ["Low Future Value", "Medium Future Value", "High Future Value", "Very High Future Value", "Insufficient History"]
            seg_counts = seg_counts.set_index("CLV Segment").reindex(all_segs, fill_value=0).reset_index()
            
            st.bar_chart(seg_counts.set_index("CLV Segment"), color="#f59e0b")
            
        # CLV Model Info Panel
        amount_model_name = "N/A"
        segment_model_name = "N/A"
        clv_export_date = "N/A"
        amount_feats = 0
        segment_feats = 0
        seg_class_avail = "No"
        
        clv_art_local = clv_artifact if 'clv_artifact' in locals() or 'clv_artifact' in globals() else None
        if clv_art_local:
            amount_model_name = clv_art_local.get("best_amount_model_name", clv_art_local.get("best_model_name", "CLV Amount Model"))
            clv_export_date = clv_art_local.get("export_date", "N/A")
            amount_feats = len(clv_art_local.get("amount_feature_columns", clv_art_local.get("feature_columns", [])))
            
            if "segment_model" in clv_art_local:
                seg_class_avail = "Yes"
                segment_model_name = clv_art_local.get("best_segment_model_name", "CLV Segment Model")
                segment_feats = len(clv_art_local.get("segment_feature_columns", []))
                if segment_feats == 0:
                    segment_feats = amount_feats
            else:
                segment_model_name = "N/A (Threshold-based)"
                segment_feats = 0
                
        st.markdown("<div class='section-header' style='margin-top:12px;'><span class='icon'>⚙️</span><span class='title'>CLV Model Information</span></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"""
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; padding: 4px;'>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>CLV Amount Model</span><br>
                    <strong style='color: #2dd4bf; font-family: JetBrains Mono, monospace; font-size: 12px;'>{amount_model_name}</strong>
                </div>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>CLV Segment Model</span><br>
                    <strong style='color: #a78bfa; font-family: JetBrains Mono, monospace; font-size: 12px;'>{segment_model_name}</strong>
                </div>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>Segment Classifier Available</span><br>
                    <strong style='color: #34d399; font-size: 12px;'>{seg_class_avail}</strong>
                </div>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>Export Date</span><br>
                    <strong style='color: #cbd5e1; font-size: 12px;'>{clv_export_date}</strong>
                </div>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>Amount Features</span><br>
                    <strong style='color: #cbd5e1; font-size: 12px;'>{amount_feats}</strong>
                </div>
                <div>
                    <span style='color: #64748b; font-size: 11px;'>Segment Features</span><br>
                    <strong style='color: #cbd5e1; font-size: 12px;'>{segment_feats}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)


    # ── Page 1: Dashboard Overview ────────────────────────────────
    if page == "Dashboard Overview":
        # Header
        st.markdown(f"""
        <div class='page-hero'>
            <div class='page-kicker'>Live Intelligence</div>
            <h1>OSMOS Digital Twin Dashboard</h1>
            <p>Real-time customer intelligence powered by <strong>{active_model}</strong> classification.</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Critical Action Alerts Widget ──
        if storage_manager.is_postgres_enabled():
            import database.action_recommendations_repository as action_repo
            import analytics.clv_trend_alerts as clv_alerts
            import analytics.segment_transitions as seg_trans
            import analytics.prediction_drift as pred_drift
            
            # Fetch data safely (non-blocking)
            try:
                pending_actions = action_repo.get_pending_critical_actions(limit=5)
                # CLV drop alerts of > 35% drop
                high_clv_drops = clv_alerts.get_clv_trend_alerts(days=30, drop_threshold=0.35)
                # Segment transitions with Risk Increase or Downgrade in last 90 days
                transitions = seg_trans.get_segment_transitions(days=90)
                risky_transitions = transitions[transitions["transition_type"].isin(["Downgrade", "Risk Increase"])] if not transitions.empty else pd.DataFrame()
                # Drift alerts
                drift_df = pred_drift.detect_prediction_drift()
                high_drift_alerts = drift_df[drift_df["drift_level"] == "High"] if not drift_df.empty else pd.DataFrame()
            except Exception as e:
                pending_actions = []
                high_clv_drops = pd.DataFrame()
                risky_transitions = pd.DataFrame()
                high_drift_alerts = pd.DataFrame()

            total_alerts_count = len(pending_actions) + len(high_clv_drops) + len(risky_transitions) + len(high_drift_alerts)
            
            if total_alerts_count > 0:
                st.markdown(f"""
                <div style='background: rgba(239, 68, 68, 0.08); border: 1.5px solid rgba(239, 68, 68, 0.3); 
                            border-radius: 8px; padding: 18px; margin-bottom: 24px;'>
                    <div style='font-size: 16px; font-weight: 700; color: #f87171; display: flex; align-items: center; gap: 8px; margin-bottom: 12px;'>
                        <span>🚨</span> Critical Action Alerts — Admin Attention Required ({total_alerts_count})
                    </div>
                    <div style='display: flex; flex-direction: column; gap: 12px; font-size: 13px; color: #cbd5e1;'>
                """, unsafe_allow_html=True)
                
                # Render CLV drops
                if not high_clv_drops.empty:
                    for _, row in high_clv_drops.iterrows():
                        st.markdown(f"""
                        <div style='border-left: 3px solid #f87171; padding-left: 10px; margin-bottom: 4px;'>
                            <strong style='color: #f87171;'>[💰 CLV Drop Alert]</strong><br>
                            <b>Client:</b> {row['entity_id']} | <b>Severity:</b> {row['alert_level']}<br>
                            <b>Reason:</b> CLV dropped by {row['clv_change_percent']*100:.1f}% to {row['latest_clv_amount']:.2f} MAD (previously {row['previous_clv_amount']:.2f} MAD).<br>
                            <span style='color: #94a3b8; font-size: 12px;'><b>Recommended Next Step:</b> Go to <i>Database Intelligence ➔ LLM-Assisted Action Intelligence ➔ CLV Alert Actions</i> to generate an explanation and recommended action.</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Render Transitions
                if not risky_transitions.empty:
                    for _, row in risky_transitions.iterrows():
                        st.markdown(f"""
                        <div style='border-left: 3px solid #fbbf24; padding-left: 10px; margin-bottom: 4px;'>
                            <strong style='color: #fbbf24;'>[🔀 Segment Transition Alert]</strong><br>
                            <b>Client:</b> {row['entity_id']} | <b>Severity:</b> High<br>
                            <b>Reason:</b> Segment downgraded/changed from '{row['previous_segment']}' ({row['previous_persona']}) to '{row['latest_segment']}' ({row['latest_persona']}).<br>
                            <span style='color: #94a3b8; font-size: 12px;'><b>Recommended Next Step:</b> Go to <i>Database Intelligence ➔ LLM-Assisted Action Intelligence ➔ Segment Transition Actions</i> to generate an explanation and recommended action.</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Render Drift
                if not high_drift_alerts.empty:
                    for _, row in high_drift_alerts.iterrows():
                        st.markdown(f"""
                        <div style='border-left: 3px solid #fb7185; padding-left: 10px; margin-bottom: 4px;'>
                            <strong style='color: #fb7185;'>[📊 Prediction Drift Alert]</strong><br>
                            <b>Class:</b> {row['dynamic_class']} | <b>Severity:</b> High<br>
                            <b>Reason:</b> Distribution changed by {row['change_percent']*100:+.1f}% vs baseline.<br>
                            <i>This means the proportion of this class changed significantly compared with the baseline period.</i><br>
                            <span style='color: #94a3b8; font-size: 12px;'><b>Recommended Next Step:</b> Go to <i>Database Intelligence ➔ LLM-Assisted Action Intelligence ➔ Prediction Drift Actions</i> to generate an explanation and recommended action.</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                # Render Pending LLM recommendations
                if pending_actions:
                    for item in pending_actions:
                        st.markdown(f"""
                        <div style='border-left: 3px solid #2dd4bf; padding-left: 10px; margin-bottom: 4px;'>
                            <strong style='color: #2dd4bf;'>[🧠 Pending LLM Recommendation]</strong><br>
                            <b>Entity:</b> {item['entity_id'] or 'Platform'} | <b>Priority:</b> {item['priority']} | <b>Suggested Channel:</b> {item['suggested_channel']}<br>
                            <b>Action Drafted (FR):</b> {item['recommended_action_fr']}<br>
                            <span style='color: #94a3b8; font-size: 12px;'><b>Recommended Next Step:</b> Review recommendation details and update status under <i>Database Intelligence ➔ LLM-Assisted Action Intelligence ➔ Generated Recommendations</i>.</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)

        # Small Closed-Loop Campaign Summary Banner
        try:
            from campaigns.campaign_repository import get_campaign_metrics
            c_metrics = get_campaign_metrics()
            st.markdown(f"""<div style='background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 13px; font-weight: 700; color: #38bdf8;'>🚀 Closed-Loop Campaign Simulation:</span>
                <span style='font-size: 12.5px; color: #cbd5e1;'>Drafts: <b style='color:#facc15;'>{c_metrics['draft_campaigns']}</b> | Dispatches: <b style='color:#38bdf8;'>{c_metrics['simulated_dispatches']}</b> | Responses: <b style='color:#34d399;'>{c_metrics['total_responses']}</b></span>
            </div>""", unsafe_allow_html=True)

        except Exception:
            pass




        total_entities = len(df_data)
        total_prospects = len(df_data[df_data["entity_type"] == "Prospect"])
        total_clients   = len(df_data[df_data["entity_type"] == "Client"])
        cold_prospects  = len(df_data[df_data["dynamic_class"] == "Cold Prospect"])
        warm_prospects  = len(df_data[df_data["dynamic_class"] == "Warm Prospect"])
        hot_prospects   = len(df_data[df_data["dynamic_class"] == "Hot Prospect"])
        active_clients  = len(df_data[df_data["dynamic_class"] == "Active Client"])
        vip_clients     = len(df_data[df_data["dynamic_class"] == "VIP Client"])
        churn_risk_clients = len(df_data[df_data["dynamic_class"] == "Churn Risk Client"])

        # KPI row
        st.markdown(f"""
        <div class='kpi-container'>
            <div class='kpi-card'>
                <span class='kpi-icon'>🌐</span>
                <div class='kpi-val color-total'>{total_entities}</div>
                <div class='kpi-label'>Total Entities</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>🎯</span>
                <div class='kpi-val color-prospect'>{total_prospects}</div>
                <div class='kpi-label'>Prospects</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>✅</span>
                <div class='kpi-val color-client'>{total_clients}</div>
                <div class='kpi-label'>Clients</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>❄️</span>
                <div class='kpi-val color-cold'>{cold_prospects}</div>
                <div class='kpi-label'>Cold Prospects</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>🔥</span>
                <div class='kpi-val color-warm'>{warm_prospects}</div>
                <div class='kpi-label'>Warm Prospects</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>⚡</span>
                <div class='kpi-val color-hot'>{hot_prospects}</div>
                <div class='kpi-label'>Hot Prospects</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>💚</span>
                <div class='kpi-val color-active'>{active_clients}</div>
                <div class='kpi-label'>Active Clients</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>👑</span>
                <div class='kpi-val color-vip'>{vip_clients}</div>
                <div class='kpi-label'>VIP Clients</div>
            </div>
            <div class='kpi-card'>
                <span class='kpi-icon'>⚠️</span>
                <div class='kpi-val color-churn'>{churn_risk_clients}</div>
                <div class='kpi-label'>Churn Risk</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Charts row
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown("<div class='section-header'><span class='icon'>📊</span><span class='title'>Dynamic Class Distribution</span></div>", unsafe_allow_html=True)
            with st.container(border=True):
                class_counts = df_data["dynamic_class"].value_counts().reset_index()
                class_counts.columns = ["Dynamic Class", "Count"]
                st.bar_chart(class_counts.set_index("Dynamic Class"), color="#2dd4bf")
        
        with col2:
            st.markdown("<div class='section-header'><span class='icon'>🌍</span><span class='title'>Top Segments</span></div>", unsafe_allow_html=True)
            with st.container(border=True):
                region_counts = df_data["region"].value_counts().head(5)
                channel_counts = df_data["source_channel"].value_counts().head(4)

                # Regions as inline bars
                max_r = region_counts.max() if len(region_counts) > 0 else 1
                for reg, cnt in region_counts.items():
                    pct = int(cnt / max_r * 100)
                    short = reg.split("-")[0] if "-" in reg else reg[:18]
                    st.markdown(f"""
                    <div class='score-bar-wrap'>
                        <div class='score-bar-label'><span>{short}</span><span>{cnt}</span></div>
                        <div class='score-bar-track'><div class='score-bar-fill fill-indigo' style='width:{pct}%'></div></div>
                    </div>""", unsafe_allow_html=True)

                st.markdown("<div style='margin-top:14px; font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:0; font-weight:600;'>Channels</div>", unsafe_allow_html=True)
                max_c = channel_counts.max() if len(channel_counts) > 0 else 1
                for ch, cnt in channel_counts.items():
                    pct = int(cnt / max_c * 100)
                    st.markdown(f"""
                    <div class='score-bar-wrap'>
                        <div class='score-bar-label'><span>{ch[:20]}</span><span>{cnt}</span></div>
                        <div class='score-bar-track'><div class='score-bar-fill fill-violet' style='width:{pct}%'></div></div>
                    </div>""", unsafe_allow_html=True)

        # Render CLV KPIs & Chart on Dashboard
        clv_art = load_clv_model_artifact()
        if clv_art is not None:
            render_clv_dashboard(df_data)

        # Customer Segmentation Overview
        st.markdown("<div class='section-header' style='margin-top:8px;'><span class='icon'>🎯</span><span class='title'>Customer Segmentation Overview</span></div>", unsafe_allow_html=True)
        with st.container(border=True):
            seg_col1, seg_col2, seg_col3 = st.columns([1, 1, 1])
            
            clients_df = df_data[df_data["entity_type"] == "Client"]
            
            with seg_col1:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#2dd4bf; text-transform:uppercase; letter-spacing:0; margin-bottom:8px;'>Top 5 Customer Segments</div>", unsafe_allow_html=True)
                if len(clients_df) > 0:
                    top_segs = clients_df["customer_segment"].value_counts().head(5)
                    for seg_name, count in top_segs.items():
                        st.markdown(f"<div style='display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:4px;'><span style='color:#cbd5e1;'>{seg_name}</span><span style='color:#34d399; font-weight:700;'>{count}</span></div>", unsafe_allow_html=True)
                else:
                    st.caption("No clients available.")
                    
            with seg_col2:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#a78bfa; text-transform:uppercase; letter-spacing:0; margin-bottom:8px;'>Top 5 Customer Personas</div>", unsafe_allow_html=True)
                if len(clients_df) > 0:
                    top_pers = clients_df["customer_persona"].value_counts().head(5)
                    for pers_name, count in top_pers.items():
                        st.markdown(f"<div style='display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:4px;'><span style='color:#cbd5e1;'>{pers_name}</span><span style='color:#2dd4bf; font-weight:700;'>{count}</span></div>", unsafe_allow_html=True)
                else:
                    st.caption("No clients available.")
                    
            with seg_col3:
                st.markdown("<div style='font-size:12px; font-weight:700; color:#fb7185; text-transform:uppercase; letter-spacing:0; margin-bottom:8px;'>Key Segment Audits</div>", unsafe_allow_html=True)
                at_risk_count = len(clients_df[clients_df["customer_segment"] == "At-Risk Premium Clients"])
                loyalist_count = len(clients_df[clients_df["customer_segment"] == "High-Value Loyalists"])
                dormant_count = len(clients_df[clients_df["customer_segment"] == "Dormant Low-Value Clients"])
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:6px;'>
                    <span style='color:#cbd5e1;'>🔥 At-Risk Premium</span>
                    <span style='color:#f87171; font-weight:700;'>{at_risk_count}</span>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:12.5px; margin-bottom:6px;'>
                    <span style='color:#cbd5e1;'>👑 High-Value Loyalists</span>
                    <span style='color:#34d399; font-weight:700;'>{loyalist_count}</span>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:12.5px;'>
                    <span style='color:#cbd5e1;'>💤 Dormant Clients</span>
                    <span style='color:#94a3b8; font-weight:700;'>{dormant_count}</span>
                </div>
                """, unsafe_allow_html=True)

        # Database table
        st.markdown("<div class='section-header' style='margin-top:8px;'><span class='icon'>👥</span><span class='title'>Client & Prospect Database</span></div>", unsafe_allow_html=True)
        with st.container(border=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                type_filter = st.selectbox("Filter by Type", ["All", "Prospect", "Client"], key="db_type_filter")
            with f_col2:
                class_filter = st.selectbox("Filter by Class", ["All"] + sorted(df_data["dynamic_class"].dropna().unique().tolist()), key="db_class_filter")
            with f_col3:
                search_query = st.text_input("🔍 Search by ID or Region", key="db_search")

            filtered_df = df_data.copy()
            if type_filter != "All":
                filtered_df = filtered_df[filtered_df["entity_type"] == type_filter]
            if class_filter != "All":
                filtered_df = filtered_df[filtered_df["dynamic_class"] == class_filter]
            if search_query:
                filtered_df = filtered_df[
                    filtered_df["entity_id"].astype(str).str.contains(search_query, case=False) |
                    filtered_df["region"].astype(str).str.contains(search_query, case=False)
                ]

            display_cols = [
                "entity_id", "entity_type", "region", "source_channel",
                "segment", "persona", "dynamic_class", "recency_days",
                "visits_30d", "product_views_30d", "cart_additions_30d",
                "purchases_90d", "total_spent_90d_mad", "conversion_probability",
                "churn_risk_score", "decision_priority_score"
            ]
            st.dataframe(
                filtered_df[display_cols].style.format({
                    "total_spent_90d_mad": "{:.2f} MAD",
                    "conversion_probability": "{:.3f}",
                    "churn_risk_score": "{:.3f}",
                    "decision_priority_score": "{:.3f}",
                    "recency_days": "{:.0f}",
                    "visits_30d": "{:.0f}",
                    "product_views_30d": "{:.0f}",
                    "cart_additions_30d": "{:.0f}",
                    "purchases_90d": "{:.0f}"
                }),
                width="stretch", hide_index=True
            )

    # ── Page 2: Entity Profile ─────────────────────────────────────
    elif page == "Entity Profile":
        st.markdown("""
        <div class='page-hero'>
            <div class='page-kicker'>Entity Profile</div>
            <h1>Digital Twin Entity Profile</h1>
            <p>Deep-dive behavioral, predictive and decision intelligence for any entity.</p>
        </div>
        """, unsafe_allow_html=True)

        entity_id_list = sorted(df_data["entity_id"].unique())
        selected_entity_id = st.selectbox("🔍 Select Entity ID", entity_id_list, key="profile_entity_sel")
        entity_row = df_data[df_data["entity_id"] == selected_entity_id].iloc[0]

        dyn_class = entity_row["dynamic_class"]
        class_tag_class = "tag-cold"
        if dyn_class == "Warm Prospect":     class_tag_class = "tag-warm"
        elif dyn_class == "Hot Prospect":    class_tag_class = "tag-hot"
        elif dyn_class == "New Client":      class_tag_class = "tag-new"
        elif dyn_class == "Active Client":   class_tag_class = "tag-active"
        elif dyn_class == "Loyal Client":    class_tag_class = "tag-loyal"
        elif dyn_class == "VIP Client":      class_tag_class = "tag-vip"
        elif dyn_class == "Dormant Client":  class_tag_class = "tag-dormant"
        elif dyn_class == "Churn Risk Client": class_tag_class = "tag-churn"

        is_client_entity  = str(entity_row.get("entity_type")).lower() == "client"
        profile_complete_val = entity_row.get("completed_client_profile")
        is_incomplete = is_client_entity and (pd.isna(profile_complete_val) or str(profile_complete_val).lower() != "true")

        entity_type_val = entity_row.get("entity_type", "Prospect")
        type_color = "#34d399" if entity_type_val == "Client" else "#2dd4bf"
        incomplete_badge = "<span class='tag tag-churn' style='margin-left:12px;'>⚠️ Profile Incomplete</span>" if is_incomplete else ""

        st.markdown(f"""<div class='glass-card-accent' style='display:flex; align-items:center; gap:20px; flex-wrap:wrap;'>
<div>
<div style='font-size:11px; text-transform:uppercase; letter-spacing:0; color:#64748b; margin-bottom:4px;'>Entity</div>
<div style='font-family: JetBrains Mono, monospace; font-size:22px; font-weight:700; color:#e2e8f0;'>{selected_entity_id}</div>
</div>
<div style='width:1px; height:40px; background:rgba(255,255,255,0.1);'></div>
<div>
<div style='font-size:11px; text-transform:uppercase; letter-spacing:0; color:#64748b; margin-bottom:4px;'>Type</div>
<div style='font-size:16px; font-weight:700; color:{type_color};'>{entity_type_val}</div>
</div>
<div style='width:1px; height:40px; background:rgba(255,255,255,0.1);'></div>
<div>
<div style='font-size:11px; text-transform:uppercase; letter-spacing:0; color:#64748b; margin-bottom:6px;'>Classification</div>
<span class='tag {class_tag_class}' style='font-size:14px; padding:6px 16px;'>{dyn_class}</span>
{incomplete_badge}
</div>
</div>""", unsafe_allow_html=True)

        # Score gauges row
        rfm   = float(entity_row.get("rfm_score", 0))
        conv  = float(entity_row.get("conversion_probability", 0))
        churn = float(entity_row.get("churn_risk_score", 0))
        beh   = float(entity_row.get("behavioral_engagement_score", 0))
        pred  = float(entity_row.get("predictive_value_score", 0))
        dec   = float(entity_row.get("decision_priority_score", 0))

        def _bar(label, val, fill_cls, fmt="{:.1%}"):
            formatted = fmt.format(val)
            width = f"{val*100:.1f}%"
            return (
                f"<div class='score-bar-wrap'>"
                f"<div class='score-bar-label'><span>{label}</span>"
                f"<span style='color:#e2e8f0; font-weight:600;'>{formatted}</span></div>"
                f"<div class='score-bar-track'><div class='score-bar-fill {fill_cls}' style='width:{width}'></div></div>"
                f"</div>"
            )

        # Get weight values from entity_row
        w_R = float(entity_row.get("ahp_weight_R", 0.0))
        w_F = float(entity_row.get("ahp_weight_F", 0.0))
        w_M = float(entity_row.get("ahp_weight_M", 0.0))
        w_E = float(entity_row.get("ahp_weight_E", 0.0))
        w_S = float(entity_row.get("ahp_weight_S", 0.0))
        
        if str(entity_row.get("entity_type")).lower() == "prospect":
            w_M = 0.0

        # Calculate CR for display using group decision logic
        ahp_result = get_group_ahp_result()
        client_cr = ahp_result["CR"]
        expert_count = ahp_result["expert_count"]
        
        cr_status = "Group AHP matrix consistent" if client_cr <= 0.10 else "Warning: Group AHP matrix inconsistent"
        cr_color = "#34d399" if client_cr <= 0.10 else "#fb7185"
        
        ahp_section_html = "".join([
            "<div style='margin:10px 0;padding:10px;background:rgba(45,212,191,0.05);border:1px solid rgba(45,212,191,0.15);border-radius:8px;'>",
            f"<div style='font-size:11px;font-weight:700;color:#2dd4bf;text-transform:uppercase;letter-spacing:0;margin-bottom:6px;'>Group AHP Weights — {expert_count} Experts</div>",
            "<div style='display:grid;grid-template-columns:repeat(5,1fr);gap:4px;text-align:center;margin-bottom:8px;'>",
            f"<div><div style='font-size:15px;color:#64748b;'>R</div><div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{w_R:.3f}</div></div>",
            f"<div><div style='font-size:15px;color:#64748b;'>F</div><div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{w_F:.3f}</div></div>",
            f"<div><div style='font-size:15px;color:#64748b;'>M</div><div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{w_M:.3f}</div></div>",
            f"<div><div style='font-size:15px;color:#64748b;'>E</div><div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{w_E:.3f}</div></div>",
            f"<div><div style='font-size:15px;color:#64748b;'>S</div><div style='font-size:15px;font-weight:600;color:#e2e8f0;'>{w_S:.3f}</div></div>",
            "</div>",
            f"<div style='font-size:10px;color:{cr_color};font-weight:500;text-align:center;'>{cr_status} (CR = {client_cr:.4f})</div>",
            "</div>",
        ])

        sc1, sc2, sc3 = st.columns(3)
        visits_n = min(float(entity_row.get('visits_30d', 0)) / 50.0, 1.0)
        views_n  = min(float(entity_row.get('product_views_30d', 0)) / 80.0, 1.0)
        carts_n  = min(float(entity_row.get('cart_additions_30d', 0)) / 10.0, 1.0)
        
        # Pre-build all score bar HTML strings to avoid f-string conflicts
        bar_rfm   = _bar("RFM Score", rfm, "fill-indigo")
        bar_conv  = _bar("Conversion Probability", conv, "fill-green")
        bar_churn = _bar("Churn Risk", churn, "fill-rose")
        bar_beh   = _bar("Behavioral Engagement", beh, "fill-violet")
        bar_pred  = _bar("Predictive Value", pred, "fill-cyan")
        bar_dec   = _bar("Decision Priority", dec, "fill-amber")
        
        visits_val = int(entity_row.get('visits_30d', 0))
        views_val  = int(entity_row.get('product_views_30d', 0))
        carts_val  = int(entity_row.get('cart_additions_30d', 0))
        visits_w   = f"{visits_n*100:.0f}%"
        views_w    = f"{views_n*100:.0f}%"
        carts_w    = f"{carts_n*100:.0f}%"

        with sc1:
            card1_html = "".join([
                "<div class='glass-card'>",
                "<div class='section-header'><span class='icon'>📈</span><span class='title'>Predictive Scores</span></div>",
                bar_rfm.strip(),
                ahp_section_html.strip(),
                bar_conv.strip(),
                bar_churn.strip(),
                "</div>"
            ])
            st.markdown(card1_html, unsafe_allow_html=True)
        with sc2:
            card2_html = (
                "<div class='glass-card'>"
                "<div class='section-header'><span class='icon'>⚙️</span><span class='title'>Engagement &amp; Priority</span></div>"
                + bar_beh
                + bar_pred
                + bar_dec
                + "</div>"
            )
            st.markdown(card2_html, unsafe_allow_html=True)
        with sc3:
            activity_html = (
                "<div class='glass-card'>"
                "<div class='section-header'><span class='icon'>⚡</span><span class='title'>Activity (30d)</span></div>"
                f"<div class='score-bar-wrap'><div class='score-bar-label'><span>Visits</span><span style='color:#e2e8f0;font-weight:600;'>{visits_val}</span></div>"
                f"<div class='score-bar-track'><div class='score-bar-fill fill-indigo' style='width:{visits_w}'></div></div></div>"
                f"<div class='score-bar-wrap'><div class='score-bar-label'><span>Product Views</span><span style='color:#e2e8f0;font-weight:600;'>{views_val}</span></div>"
                f"<div class='score-bar-track'><div class='score-bar-fill fill-violet' style='width:{views_w}'></div></div></div>"
                f"<div class='score-bar-wrap'><div class='score-bar-label'><span>Cart Additions</span><span style='color:#e2e8f0;font-weight:600;'>{carts_val}</span></div>"
                f"<div class='score-bar-track'><div class='score-bar-fill fill-cyan' style='width:{carts_w}'></div></div></div>"
                "</div>"
            )
            st.markdown(activity_html, unsafe_allow_html=True)

        prof_col1, prof_col2 = st.columns(2)
        with prof_col1:
            profile_rows = [
                ("Entity ID", entity_row.get("entity_id")),
                ("Entity Type", entity_row.get("entity_type")),
                ("Region", entity_row.get("region")),
                ("Source Channel", entity_row.get("source_channel")),
                ("Segment", entity_row.get("segment")),
                ("Persona", entity_row.get("persona")),
                ("Age Group", entity_row.get("age_group")),
                ("Preferred Device", entity_row.get("preferred_device")),
                ("Preferred Category", entity_row.get("preferred_category")),
                ("Marketing Consent", str(entity_row.get("marketing_consent"))),
                ("Price Sensitivity", f"{entity_row.get('price_sensitivity',0):.3f}"),
                ("Income Power", f"{entity_row.get('income_power_score',0):.3f}"),
                ("Created", str(entity_row.get("created_at"))[:10] if entity_row.get("created_at") else "—"),
            ]
            rows_html = "".join([f"<div class='info-row'><span class='info-label'>{k}</span><span class='info-value'>{v}</span></div>" for k,v in profile_rows])
            st.markdown(f"""
            <div class='glass-card'>
                <div class='section-header'><span class='icon'>ℹ️</span><span class='title'>Basic Profile</span></div>
                {rows_html}
            </div>""", unsafe_allow_html=True)

        with prof_col2:
            beh_rows = [
                ("Recency", f"{entity_row.get('recency_days',0):.0f} days"),
                ("Purchases (90d)", f"{entity_row.get('purchases_90d',0):.0f}"),
                ("Total Spent (90d)", f"{entity_row.get('total_spent_90d_mad',0):.2f} MAD"),
                ("Avg Order Value", f"{entity_row.get('avg_order_value_mad',0):.2f} MAD"),
                ("Email Open Rate", f"{entity_row.get('email_open_rate',0)*100:.1f}%"),
                ("Email Click Rate", f"{entity_row.get('email_click_rate',0)*100:.1f}%"),
                ("Complaints (90d)", f"{entity_row.get('complaint_count_90d',0):.0f}"),
                ("Avg Review Score", f"{entity_row.get('review_score_avg',0):.2f}" if not pd.isna(entity_row.get('review_score_avg')) else "No reviews"),
                ("Social Mentions", f"{entity_row.get('social_mentions_30d',0):.0f}"),
                ("Social Sentiment", f"{entity_row.get('social_sentiment_avg',0):.3f}"),
            ]
            rows_html2 = "".join([f"<div class='info-row'><span class='info-label'>{k}</span><span class='info-value'>{v}</span></div>" for k,v in beh_rows])
            st.markdown(f"""
            <div class='glass-card'>
                <div class='section-header'><span class='icon'>🛒</span><span class='title'>Behavioral Data</span></div>
                {rows_html2}
            </div>""", unsafe_allow_html=True)

        # Client demographics — uses native widgets so we use st.container
        st.markdown("<div class='section-header' style='margin-top:8px;'><span class='icon'>📋</span><span class='title'>Client Demographic Profile</span></div>", unsafe_allow_html=True)
        with st.container(border=True):
            if is_client_entity:
                if is_incomplete:
                    st.warning("⚠️ Client profile incomplete. Click **Edit** to complete demographics.")
                dem_rows = [
                    ("Age", str(int(entity_row["age"])) if not pd.isna(entity_row.get("age")) else "Not completed"),
                    ("Sex", entity_row.get("sex") or "Not completed"),
                    ("Email", entity_row.get("email") or "Not completed"),
                    ("Customer Type", entity_row.get("customer_type") or "Not completed"),
                    ("Household Size", str(int(entity_row["household_size"])) if not pd.isna(entity_row.get("household_size")) else ("N/A (B2B)" if entity_row.get("customer_type") == "B2B" else "Not completed")),
                    ("Phone Number", entity_row.get("phone_number") or "Not completed"),
                    ("Company Name", entity_row.get("company_name") or ("N/A (B2C)" if entity_row.get("customer_type") == "B2C" else "Not completed")),
                    ("Job Title", entity_row.get("job_title") or ("N/A (B2C)" if entity_row.get("customer_type") == "B2C" else "Not completed")),
                    ("City", entity_row.get("city") or "Not completed"),
                    ("Address", entity_row.get("address") or "Not completed"),
                ]
                dem_html = "".join([f"<div class='info-row'><span class='info-label'>{k}</span><span class='info-value'>{v}</span></div>" for k,v in dem_rows])
                st.markdown(dem_html, unsafe_allow_html=True)
                if st.button("✏️ Edit Client Information", key="edit_client_profile_btn"):
                    st.session_state["edit_form_open"] = True
                    st.session_state["pending_edit_entity_id"] = selected_entity_id
                    st.rerun()
            else:
                st.info("ℹ️ Client information will be available after this entity converts to a Client.")
            
        # Customer Lifetime Value (CLV) Prediction Section
        def render_clv_card(row):
            clv_val = row.get("predicted_clv_amount_mad")
            clv_score = row.get("predicted_clv_score")
            clv_seg = row.get("predicted_clv_segment")
            clv_model = row.get("clv_model_name") or "—"
            clv_seg_model = row.get("clv_segment_model_name") or "—"
            clv_updated = row.get("clv_last_updated") or "—"
            
            ml_val = row.get("ml_predicted_clv_amount_mad")
            math_val = row.get("math_clv_amount_mad")
            method_used = row.get("clv_method_used")
            pred_source = row.get("clv_segment_prediction_source") or "—"
            confidence = row.get("clv_segment_confidence")
            
            st.markdown("<div class='section-header' style='margin-top:8px;'><span class='icon'>💰</span><span class='title'>Customer Lifetime Value</span></div>", unsafe_allow_html=True)
            with st.container(border=True):
                if str(row.get("entity_type")).lower() == "prospect":
                    st.info("ℹ️ **CLV Estimation:** CLV will be estimated after conversion and enough purchase history.")
                elif clv_seg == "Insufficient History" or pd.isna(clv_val):
                    st.warning("⚠️ **CLV Estimation:** Insufficient History")
                else:
                    seg_class = "tag-clv-low"
                    if clv_seg == "Medium Future Value":
                        seg_class = "tag-clv-medium"
                    elif clv_seg == "High Future Value":
                        seg_class = "tag-clv-high"
                    elif clv_seg == "Very High Future Value":
                        seg_class = "tag-clv-veryhigh"
                        
                    clv_amt_str = f"{float(clv_val):,.2f} MAD" if not pd.isna(clv_val) else "—"
                    clv_score_str = f"{float(clv_score):.1f} / 100" if not pd.isna(clv_score) else "—"
                    clv_seg_str = clv_seg if clv_seg else "—"
                    
                    ml_amt_str = f"{float(ml_val):,.2f} MAD" if not pd.isna(ml_val) and ml_val is not None else "—"
                    math_amt_str = f"{float(math_val):,.2f} MAD" if not pd.isna(math_val) and math_val is not None else "—"
                    confidence_str = f"{float(confidence):.1%}" if not pd.isna(confidence) and confidence is not None else "N/A"
                    method_str = method_used if method_used else clv_model
                    
                    st.markdown(f"""
                    <div class='info-row'><span class='info-label'>Final CLV Amount</span><span class='info-value' style='font-size:14px;color:#ecfeff;font-weight:700;'>{clv_amt_str}</span></div>
                    <div class='info-row'><span class='info-label'>CLV Score</span><span class='info-value'>{clv_score_str}</span></div>
                    <div class='info-row'><span class='info-label'>Final CLV Segment</span><span class='info-value'><span class='tag {seg_class}'>{clv_seg_str}</span></span></div>
                    <div class='info-row'><span class='info-label'>CLV Amount Model</span><span class='info-value'>{clv_model}</span></div>
                    <div class='info-row'><span class='info-label'>CLV Segment Model</span><span class='info-value'>{clv_seg_model}</span></div>
                    <div class='info-row'><span class='info-label'>Segment Prediction Source</span><span class='info-value'>{pred_source}</span></div>
                    <div class='info-row'><span class='info-label'>Segment Confidence</span><span class='info-value'>{confidence_str}</span></div>
                    <div class='info-row'><span class='info-label'>ML CLV Amount</span><span class='info-value'>{ml_amt_str}</span></div>
                    <div class='info-row'><span class='info-label'>Mathematical CLV Amount</span><span class='info-value'>{math_amt_str}</span></div>
                    <div class='info-row'><span class='info-label'>Method Used</span><span class='info-value' style='color:#a5b4fc;font-weight:600;'>{method_str}</span></div>
                    <div class='info-row'><span class='info-label'>Last CLV Update</span><span class='info-value'>{clv_updated}</span></div>
                    """, unsafe_allow_html=True)
                    
                    # Top 3 distribution
                    top_3_val = row.get("clv_segment_top_3")
                    parsed_top_3 = None
                    if top_3_val:
                        if isinstance(top_3_val, str):
                            try:
                                parsed_top_3 = json.loads(top_3_val)
                            except Exception:
                                pass
                        elif isinstance(top_3_val, (list, tuple)):
                            parsed_top_3 = top_3_val
                            
                    if parsed_top_3:
                        st.markdown("<div style='font-size:12px; font-weight:600; color:#2dd4bf; margin-top:14px; margin-bottom:6px;'>Segment Probability Distribution:</div>", unsafe_allow_html=True)
                        for idx_top, item in enumerate(parsed_top_3):
                            if isinstance(item, (list, tuple)) and len(item) >= 2:
                                lbl = item[0]
                                val_prob = float(item[1])
                                st.markdown(f"""
                                <div style='display:flex; justify-content:space-between; font-size:11px; margin-bottom:4px;'>
                                    <span style='color:#94a3b8;'>{idx_top+1}. {lbl}</span>
                                    <span style='color:#34d399; font-weight:700;'>{val_prob:.1%}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                
                    if method_used == "Hybrid CLV: Mathematical Fallback":
                        st.warning("⚠️ **Hybrid fallback used because ML CLV was inconsistent with current Digital Twin behavior.**")
                        
                    if pred_source == "Segment Classifier":
                        st.info("ℹ️ **CLV segment predicted directly using the segment classification model.**")
                    elif pred_source == "Score Thresholds":
                        st.info("ℹ️ **CLV segment derived from percentile-based CLV score.**")
                        
                    st.caption("ℹ️ **Interpretation Note:** The CLV segment represents the client's future value relative to your current customer base, predicted or derived from their behavioral digital twin history.")
        
        col_clv_card, col_seg_card = st.columns(2)
        with col_clv_card:
            render_clv_card(entity_row)
        with col_seg_card:
            st.markdown("<div class='section-header' style='margin-top:8px;'><span class='icon'>🎯</span><span class='title'>Customer Segment & Persona</span></div>", unsafe_allow_html=True)
            with st.container(border=True):
                if str(entity_row.get("entity_type")).lower() == "prospect":
                    st.info("ℹ️ **Persona Layer:** Persona will be created after conversion to Client.")
                else:
                    seg = entity_row.get("customer_segment") or "Standard Active Clients"
                    persona = entity_row.get("customer_persona") or "Regular Buyer"
                    desc = entity_row.get("persona_description") or "Client with normal activity and moderate value."
                    act = entity_row.get("persona_recommended_action") or "Maintain engagement with personalized recommendations."
                    method = entity_row.get("segmentation_method") or "Rule-Based RFM-ES + CLV Segmentation"
                    updated = entity_row.get("segmentation_last_updated") or "—"
                    
                    seg_class = "tag-vip" if "High-Value" in seg or "Premium" in seg else ("tag-churn" if "Risk" in seg or "At-Risk" in seg else "tag-active")
                    
                    st.markdown(f"""
                    <div class='info-row'><span class='info-label'>Customer Segment</span><span class='info-value'><span class='tag {seg_class}'>{seg}</span></span></div>
                    <div class='info-row'><span class='info-label'>Customer Persona</span><span class='info-value' style='font-weight:700;color:#fb7185;'>{persona}</span></div>
                    <div class='info-row'><span class='info-label'>Description</span><span class='info-value' style='font-size:12.5px;color:#cbd5e1;white-space:normal;line-height:1.4;'>{desc}</span></div>
                    <div class='info-row'><span class='info-label'>Recommended Action</span><span class='info-value' style='font-size:12.5px;color:#34d399;font-weight:600;white-space:normal;line-height:1.4;'>{act}</span></div>
                    <div class='info-row'><span class='info-label'>Method</span><span class='info-value'>{method}</span></div>
                    <div class='info-row'><span class='info-label'>Last Updated</span><span class='info-value'>{updated}</span></div>
                    """, unsafe_allow_html=True)

        # Refresh CLV button — only shown for Clients
        if str(entity_row.get("entity_type", "")).lower() == "client":
            st.markdown("<div style='margin-top:4px;'>", unsafe_allow_html=True)
            if st.button("🔄 Refresh CLV", key="btn_refresh_clv", help="Recalculate CLV prediction for this client using the latest data"):
                clv_art = load_clv_model_artifact()
                if clv_art is None:
                    st.error("CLV model artifact not found. Please ensure 'osmos_best_clv_model_artifact.pkl' is available.")
                elif is_cold_start_client(df_data[df_data["entity_id"] == selected_entity_id].iloc[0]):
                    st.warning("⚠️ This client has no purchase history. CLV cannot be estimated yet (cold-start).")
                else:
                    with st.spinner("Recalculating CLV..."):
                        df_data = update_client_clv(df_data, selected_entity_id, clv_art)
                        df_data = update_customer_segmentation(df_data, selected_entity_id)
                        _, history = get_data()
                        # Save only this one entity row — not all 1508
                        storage_manager.save_entity_snapshot(df_data, selected_entity_id, history)
                        st.session_state["df"] = df_data

                    st.success("✅ CLV and Customer Segment refreshed successfully!")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    
            # ── Page: Customer Segments & Personas ─────────────────────────
    elif page == "Customer Segments & Personas":
        st.markdown("""
        <div class='page-hero'>
            <div class='page-kicker'>Customer Cohorts</div>
            <h1>Customer Segments & Personas</h1>
            <p>Explainable cohort segmentation, persona assignment, and ML clustering support.</p>
        </div>
        """, unsafe_allow_html=True)
        
        clients_df = df_data[df_data["entity_type"] == "Client"]
        total_clients_cnt = len(clients_df)
        unique_segments = clients_df["customer_segment"].nunique() if total_clients_cnt > 0 else 0
        loyalists_cnt = len(clients_df[clients_df["customer_segment"] == "High-Value Loyalists"])
        at_risk_cnt = len(clients_df[clients_df["customer_segment"] == "At-Risk Premium Clients"])
        dormant_cnt = len(clients_df[clients_df["customer_segment"] == "Dormant Low-Value Clients"])

        # ── Tabs ──────────────────────────────────────────────────────
        tab_overview, tab_personas = st.tabs(["📊 Overview", "🎭 Personas"])

        # ── TAB 1: OVERVIEW ───────────────────────────────────────────
        with tab_overview:
            # A. KPI Cards
            st.markdown(f"""
            <div class='kpi-container'>
                <div class='kpi-card'>
                    <span class='kpi-icon'>👥</span>
                    <div class='kpi-val color-total'>{total_clients_cnt}</div>
                    <div class='kpi-label'>Total Clients</div>
                </div>
                <div class='kpi-card'>
                    <span class='kpi-icon'>🗂️</span>
                    <div class='kpi-val color-prospect'>{unique_segments}</div>
                    <div class='kpi-label'>Active Segments</div>
                </div>
                <div class='kpi-card'>
                    <span class='kpi-icon'>👑</span>
                    <div class='kpi-val color-vip'>{loyalists_cnt}</div>
                    <div class='kpi-label'>High-Value Loyalists</div>
                </div>
                <div class='kpi-card'>
                    <span class='kpi-icon'>🔥</span>
                    <div class='kpi-val color-churn'>{at_risk_cnt}</div>
                    <div class='kpi-label'>At-Risk Premium</div>
                </div>
                <div class='kpi-card'>
                    <span class='kpi-icon'>💤</span>
                    <div class='kpi-val color-cold'>{dormant_cnt}</div>
                    <div class='kpi-label'>Dormant Clients</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # B & C. Distribution Charts
            st.markdown("<div class='section-header' style='margin-top:16px;'><span class='icon'>📊</span><span class='title'>Segment & Persona Distribution</span></div>", unsafe_allow_html=True)
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px;font-weight:700;color:#2dd4bf;text-transform:uppercase;letter-spacing:0;margin-bottom:8px;'>Clients per Segment</div>", unsafe_allow_html=True)
                    if total_clients_cnt > 0:
                        seg_counts = clients_df["customer_segment"].value_counts().reset_index()
                        seg_counts.columns = ["Segment", "Count"]
                        st.bar_chart(seg_counts.set_index("Segment"), color="#2dd4bf", height=200)
                    else:
                        st.caption("No client data available.")
            with chart_col2:
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px;font-weight:700;color:#fb7185;text-transform:uppercase;letter-spacing:0;margin-bottom:8px;'>Clients per Persona</div>", unsafe_allow_html=True)
                    if total_clients_cnt > 0:
                        pers_counts = clients_df["customer_persona"].value_counts().reset_index()
                        pers_counts.columns = ["Persona", "Count"]
                        st.bar_chart(pers_counts.set_index("Persona"), color="#fb7185", height=200)
                    else:
                        st.caption("No client data available.")

            # D & E. Interactive Filter and Segment Table
            st.markdown("<div class='section-header' style='margin-top:16px;'><span class='icon'>🔍</span><span class='title'>Interactive Cohort Table</span></div>", unsafe_allow_html=True)
            with st.container(border=True):
                f1, f2, f3, f4 = st.columns(4)
                with f1:
                    all_segs = ["All"] + sorted(clients_df["customer_segment"].dropna().unique().tolist())
                    sel_seg = st.selectbox("Segment Filter", all_segs, key="filter_seg")
                with f2:
                    all_pers = ["All"] + sorted(clients_df["customer_persona"].dropna().unique().tolist())
                    sel_pers = st.selectbox("Persona Filter", all_pers, key="filter_pers")
                with f3:
                    all_clv_segs = ["All"] + sorted(clients_df["predicted_clv_segment"].dropna().unique().tolist())
                    sel_clv_seg = st.selectbox("CLV Segment", all_clv_segs, key="filter_clv_seg")
                with f4:
                    all_classes = ["All"] + sorted(clients_df["dynamic_class"].dropna().unique().tolist())
                    sel_class = st.selectbox("Dynamic Class", all_classes, key="filter_class")
                table_df = clients_df.copy()
                if sel_seg != "All":
                    table_df = table_df[table_df["customer_segment"] == sel_seg]
                if sel_pers != "All":
                    table_df = table_df[table_df["customer_persona"] == sel_pers]
                if sel_clv_seg != "All":
                    table_df = table_df[table_df["predicted_clv_segment"] == sel_clv_seg]
                if sel_class != "All":
                    table_df = table_df[table_df["dynamic_class"] == sel_class]
                display_cols = [
                    "entity_id", "dynamic_class", "customer_segment", "customer_persona",
                    "predicted_clv_score", "predicted_clv_segment", "rfm_score",
                    "churn_risk_score", "recency_days", "persona_recommended_action"
                ]
                st.dataframe(
                    table_df[display_cols].style.format({
                        "predicted_clv_score": "{:.1f}",
                        "rfm_score": "{:.3f}",
                        "churn_risk_score": "{:.3f}",
                        "recency_days": "{:.0f}"
                    }),
                    width="stretch", hide_index=True
                )

            # F. Action buttons
            act_col1, act_col2 = st.columns([1, 2])
            with act_col1:
                if st.button("🔄 Refresh Segmentation", key="btn_refresh_segmentation", width="stretch", help="Recalculate segments and personas for all clients"):
                    with st.spinner("Recalculating cohorts..."):
                        df_data = update_customer_segmentation(df_data)
                        _, history = get_data()
                        save_data(df_data, history)
                        st.session_state["df"] = df_data
                    st.success("✅ Customer segments re-evaluated and saved!")
                    st.rerun()

            # G. ML Clustering
            with st.expander("🧠 Complementary ML Clustering Analytics", expanded=True):
                st.markdown("""
                This module runs a **KMeans Clustering** model over 16 behavioral, predictive, and engagement features
                to discover hidden cohorts. It applies **PCA (Principal Component Analysis)** to project clusters into a 2D or 3D space.
                """)
                
                clust_col1, clust_col2 = st.columns([1, 2])
                with clust_col1:
                    n_clusters = st.slider("Select Number of Clusters", min_value=2, max_value=8, value=5, step=1, key="clust_n_clusters")
                    pca_dim = st.radio("PCA Visualization Dimensions:", ["2D Scatter Plot", "3D Spatial Projection"], horizontal=True, key="rad_pca_dim")
                    run_clust_btn = st.button("🤖 Run KMeans Clustering", type="primary", width="stretch", key="btn_run_kmeans")
                    
                # Auto-run clustering if not in session state or if button clicked or if cluster count changed
                if run_clust_btn or "pca_df" not in st.session_state or st.session_state.get("last_n_clusters") != n_clusters:
                    with st.spinner("Fitting KMeans and projecting PCA coordinates..."):
                        df_data, pca_df_res, exp_var_res = run_customer_clustering(df_data, n_clusters=n_clusters)
                        st.session_state["df"] = df_data
                        st.session_state["pca_df"] = pca_df_res
                        st.session_state["exp_var"] = exp_var_res
                        st.session_state["last_n_clusters"] = n_clusters

                pca_df = st.session_state.get("pca_df")
                exp_var = st.session_state.get("exp_var", [0.0, 0.0, 0.0])

                if pca_df is not None and not pca_df.empty:
                    st.success(f"✅ Grouped {len(pca_df)} clients into {n_clusters} behavioral clusters!")
                    
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    tot_var = sum(exp_var[:2]) * 100
                    
                    if "2D" in pca_dim:
                        fig = px.scatter(
                            pca_df,
                            x="PCA1",
                            y="PCA2",
                            color="cluster",
                            symbol="cluster",
                            hover_name="entity_id",
                            hover_data={
                                "PCA1": ":.2f",
                                "PCA2": ":.2f",
                                "dynamic_class": True,
                                "customer_segment": True,
                                "cluster_persona": True,
                                "rfm_score": ":.2f",
                                "predicted_clv_score": ":.1f",
                                "total_spent_90d_mad": ":.2f"
                            },
                            title=f"KMeans Cluster Map (PCA 2D Space — {tot_var:.1f}% Variance Explained)",
                            color_discrete_sequence=["#38bdf8", "#34d399", "#facc15", "#f87171", "#c084fc", "#fb923c", "#a7f3d0", "#e879f9"]
                        )
                        
                        # Compute centroids in 2D
                        centroids = pca_df.groupby("cluster")[["PCA1", "PCA2"]].mean().reset_index()
                        fig.add_trace(
                            go.Scatter(
                                x=centroids["PCA1"],
                                y=centroids["PCA2"],
                                mode="markers+text",
                                marker=dict(size=14, symbol="diamond", color="#ffffff", line=dict(width=2, color="#000000")),
                                text=centroids["cluster"],
                                textposition="top center",
                                name="Cluster Centroids"
                            )
                        )
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=480,
                            paper_bgcolor="rgba(15, 23, 42, 0.6)",
                            plot_bgcolor="rgba(15, 23, 42, 0.6)",
                            margin=dict(l=20, r=20, t=40, b=20),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        tot_var_3d = sum(exp_var[:3]) * 100
                        fig3d = px.scatter_3d(
                            pca_df,
                            x="PCA1",
                            y="PCA2",
                            z="PCA3",
                            color="cluster",
                            hover_name="entity_id",
                            hover_data={
                                "dynamic_class": True,
                                "customer_segment": True,
                                "cluster_persona": True,
                                "rfm_score": ":.2f",
                                "predicted_clv_score": ":.1f"
                            },
                            title=f"KMeans 3D Spatial Cluster Projection ({tot_var_3d:.1f}% Variance Explained)",
                            color_discrete_sequence=["#38bdf8", "#34d399", "#facc15", "#f87171", "#c084fc", "#fb923c", "#a7f3d0", "#e879f9"]
                        )
                        fig3d.update_layout(
                            template="plotly_dark",
                            height=540,
                            paper_bgcolor="rgba(15, 23, 42, 0.6)",
                            margin=dict(l=10, r=10, t=40, b=10)
                        )
                        st.plotly_chart(fig3d, use_container_width=True)

                    st.markdown("---")
                    
                    # 2. Cluster Profiles Summary & Metrics Breakdown
                    st.markdown("<div class='section-header'><span class='icon'>📊</span><span class='title'>Cluster Cohort Characteristics & Profiles</span></div>", unsafe_allow_html=True)
                    
                    col_m1, col_m2 = st.columns([1, 1])
                    with col_m1:
                        st.markdown("<strong style='font-size:13px; color:#38bdf8;'>Entity Distribution across Clusters</strong>", unsafe_allow_html=True)
                        counts_df = pca_df["cluster"].value_counts().reset_index()
                        counts_df.columns = ["Cluster", "Count"]
                        
                        fig_bar = px.bar(
                            counts_df,
                            x="Cluster",
                            y="Count",
                            color="Cluster",
                            text="Count",
                            color_discrete_sequence=["#38bdf8", "#34d399", "#facc15", "#f87171", "#c084fc", "#fb923c", "#a7f3d0", "#e879f9"]
                        )
                        fig_bar.update_layout(
                            template="plotly_dark",
                            height=260,
                            paper_bgcolor="rgba(15, 23, 42, 0.6)",
                            plot_bgcolor="rgba(15, 23, 42, 0.6)",
                            showlegend=False,
                            margin=dict(l=10, r=10, t=20, b=10)
                        )
                        st.plotly_chart(fig_bar, use_container_width=True)

                    with col_m2:
                        st.markdown("<strong style='font-size:13px; color:#34d399;'>Mean Metric Comparison by Cluster</strong>", unsafe_allow_html=True)
                        cluster_means = pca_df.groupby("cluster")[["rfm_score", "predicted_clv_score", "churn_risk_score", "total_spent_90d_mad"]].mean().reset_index()
                        cluster_means.columns = ["Cluster", "Avg RFM", "Avg CLV", "Avg Churn Risk", "Avg Spend (MAD)"]
                        
                        st.dataframe(
                            cluster_means.style.format({
                                "Avg RFM": "{:.2f}",
                                "Avg CLV": "{:.1f}",
                                "Avg Churn Risk": "{:.2f}",
                                "Avg Spend (MAD)": "{:.2f}"
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                    # 3. Cluster Entity Inspector
                    st.markdown("<div class='section-header'><span class='icon'>🔎</span><span class='title'>Cluster Entity Inspector</span></div>", unsafe_allow_html=True)
                    sel_clust_inspect = st.selectbox("Select Cluster to inspect entities:", sorted(pca_df["cluster"].unique()), key="sb_clust_inspect")
                    
                    clust_entities = pca_df[pca_df["cluster"] == sel_clust_inspect]
                    st.dataframe(
                        clust_entities[["entity_id", "dynamic_class", "customer_segment", "cluster_persona", "rfm_score", "predicted_clv_score", "total_spent_90d_mad"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.error("Insufficient client data to run KMeans clustering.")


        # ── TAB 2: PERSONAS EXPLORER ──────────────────────────────────
        with tab_personas:
            st.markdown("""
            <style>
            .persona-card {
                position: relative;
                overflow: hidden;
                min-height: 100%;
                margin-bottom: 16px;
                padding: 22px 22px 18px 22px;
                background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018)), var(--panel-2) !important;
                border: 1px solid var(--line) !important;
                border-left: 4px solid var(--teal) !important;
                border-radius: var(--radius) !important;
                box-shadow: var(--shadow) !important;
                transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
            }
            .persona-card:hover {
                transform: translateY(-3px);
                border-color: var(--line-strong) !important;
                background: var(--panel-3) !important;
            }
            .persona-icon-badge { font-size: 32px; line-height: 1; display: inline-block; margin-bottom: 8px; opacity: 0.9; }
            .persona-name {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 19px; font-weight: 800; color: var(--text); margin: 4px 0 4px 0;
            }
            .persona-segment-tag {
                display: inline-block; font-size: 11px; font-weight: 800;
                padding: 4px 10px; border-radius: 999px; letter-spacing: 0; margin-bottom: 12px;
            }
            .persona-desc { font-size: 13px; color: var(--muted); line-height: 1.6; margin-bottom: 14px; }
            .persona-metric-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
            .persona-metric-chip {
                background: rgba(255,255,255,0.035);
                border: 1px solid rgba(148,163,184,0.16);
                border-radius: var(--radius); padding: 6px 10px; font-size: 12px; color: var(--muted);
            }
            .persona-metric-chip strong { color: var(--teal); font-family: 'JetBrains Mono', monospace; }
            .persona-action-box {
                background: rgba(52,211,153,0.08); border: 1px solid rgba(52,211,153,0.24);
                border-radius: var(--radius); padding: 10px 12px; font-size: 13px; color: var(--green); margin-bottom: 10px;
            }
            .persona-rule-box {
                background: #0b1118; border: 1px solid rgba(148,163,184,0.16);
                border-radius: var(--radius); padding: 9px 12px; font-size: 11.5px; color: var(--teal);
                font-family: 'JetBrains Mono', monospace;
            }
            .persona-client-count {
                position: absolute; top: 14px; right: 14px;
                background: rgba(45,212,191,0.12); border: 1px solid rgba(45,212,191,0.30);
                border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 800;
                color: var(--teal); font-family: 'Space Grotesk', sans-serif;
            }
            </style>
            """, unsafe_allow_html=True)

            PERSONA_CATALOG = [
                {
                    "persona": "Premium Loyalist",
                    "segment": "High-Value Loyalists",
                    "icon": "👑",
                    "tag_style": "background:rgba(251,113,133,0.15);color:#fb7185;border:1px solid rgba(251,113,133,0.3);",
                    "description": "Your most valuable and loyal clients. They buy frequently, spend significantly, and show no signs of leaving. They form the backbone of long-term revenue.",
                    "action": "🎁 Reward with VIP offers, exclusive early access, and premium white-glove service. Invite to loyalty programs and ambassador initiatives.",
                    "trigger": "rfm_score ≥ 0.75 AND predicted_clv_score ≥ 75 AND churn_risk_score < 0.35",
                    "metrics_focus": ["rfm_score", "predicted_clv_score", "churn_risk_score", "purchases_90d"],
                },
                {
                    "persona": "Silent VIP at Risk",
                    "segment": "At-Risk Premium Clients",
                    "icon": "🔥",
                    "tag_style": "background:rgba(251,113,133,0.15);color:#fb7185;border:1px solid rgba(251,113,133,0.3);",
                    "description": "High-value clients who are beginning to disengage. Their CLV is still strong but churn signals are rising — inaction here is costly.",
                    "action": "🚨 Trigger immediate retention campaign. Send personalized follow-up, exclusive discounts, or direct account manager outreach.",
                    "trigger": "predicted_clv_score ≥ 70 AND churn_risk_score ≥ 0.50",
                    "metrics_focus": ["predicted_clv_score", "churn_risk_score", "recency_days", "rfm_score"],
                },
                {
                    "persona": "Emerging Loyalist",
                    "segment": "Growth Potential Clients",
                    "icon": "🚀",
                    "tag_style": "background:rgba(34,211,238,0.15);color:#22d3ee;border:1px solid rgba(34,211,238,0.3);",
                    "description": "Clients with above-average engagement and spending trajectories. With the right nudge, they can become your next Premium Loyalists.",
                    "action": "📦 Use cross-selling strategies, loyalty tier upgrades, bundle deals, and behavior-based product recommendations.",
                    "trigger": "predicted_clv_score ≥ 50 AND rfm_score ≥ 0.55 AND behavioral_engagement_score ≥ 0.50",
                    "metrics_focus": ["predicted_clv_score", "rfm_score", "behavioral_engagement_score", "purchases_90d"],
                },
                {
                    "persona": "Deal Seeker",
                    "segment": "Price-Sensitive Occasional Buyers",
                    "icon": "🏷️",
                    "tag_style": "background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);",
                    "description": "Clients who buy primarily when there are promotions or discounts. Their frequency is event-driven and price sensitivity is their defining trait.",
                    "action": "💸 Target with flash sales, limited-time offers, loyalty points, and promotional sequences tied to seasonal events.",
                    "trigger": "price_sensitivity ≥ 0.70 AND predicted_clv_score < 60",
                    "metrics_focus": ["price_sensitivity", "predicted_clv_score", "purchases_90d", "avg_order_value_mad"],
                },
                {
                    "persona": "Frustrated Client",
                    "segment": "Complaint-Driven Risk Clients",
                    "icon": "😠",
                    "tag_style": "background:rgba(248,113,113,0.15);color:#f87171;border:1px solid rgba(248,113,113,0.3);",
                    "description": "Clients expressing dissatisfaction through complaints or negative social signals. Left unaddressed, they will churn and damage brand reputation.",
                    "action": "🛠️ Escalate to support immediately. Offer service recovery incentives. Monitor sentiment and follow up post-resolution.",
                    "trigger": "complaint_count_90d ≥ 1 OR social_sentiment_avg < 0.35",
                    "metrics_focus": ["complaint_count_90d", "social_sentiment_avg", "churn_risk_score", "recency_days"],
                },
                {
                    "persona": "Sleeping Client",
                    "segment": "Dormant Low-Value Clients",
                    "icon": "💤",
                    "tag_style": "background:rgba(100,116,139,0.15);color:#94a3b8;border:1px solid rgba(100,116,139,0.3);",
                    "description": "Clients who haven't engaged or purchased in a long time. Engagement is near zero. Re-engagement ROI must be carefully evaluated.",
                    "action": "📬 Launch low-cost win-back campaigns. Consider sunset sequences if no engagement. Reduce marketing spend allocation.",
                    "trigger": "recency_days ≥ 60 AND behavioral_engagement_score < 0.30",
                    "metrics_focus": ["recency_days", "behavioral_engagement_score", "rfm_score", "churn_risk_score"],
                },
                {
                    "persona": "Brand Advocate",
                    "segment": "Social Advocates",
                    "icon": "📢",
                    "tag_style": "background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.3);",
                    "description": "Clients who actively talk positively about your brand online and respond enthusiastically to email campaigns. Natural brand amplifiers.",
                    "action": "🤝 Invite to referral programs and ambassador campaigns. Leverage their reach with co-created content and exclusive previews.",
                    "trigger": "social_sentiment_avg ≥ 0.75 AND email_click_rate ≥ 0.30",
                    "metrics_focus": ["social_sentiment_avg", "email_click_rate", "email_open_rate", "behavioral_engagement_score"],
                },
                {
                    "persona": "New Explorer",
                    "segment": "New Customers",
                    "icon": "🧭",
                    "tag_style": "background:rgba(45,212,191,0.15);color:#2dd4bf;border:1px solid rgba(45,212,191,0.3);",
                    "description": "Recently acquired clients in their discovery phase. The first 90 days are critical — the right experience here determines long-term retention.",
                    "action": "👋 Send onboarding sequences, highlight top products, offer first-purchase follow-up discounts, and invite feedback.",
                    "trigger": "purchases_90d ≤ 1 OR predicted_clv_segment == 'Insufficient History'",
                    "metrics_focus": ["purchases_90d", "recency_days", "email_open_rate", "behavioral_engagement_score"],
                },
                {
                    "persona": "Regular Buyer",
                    "segment": "Standard Active Clients",
                    "icon": "👥",
                    "tag_style": "background:rgba(71,85,105,0.20);color:#94a3b8;border:1px solid rgba(71,85,105,0.35);",
                    "description": "Clients with steady, average purchase behavior. No strong signals in either direction — a stable base that benefits from continued personalization.",
                    "action": "💬 Maintain consistent engagement with personalized product recommendations and periodic check-in offers.",
                    "trigger": "Default — no other conditions met",
                    "metrics_focus": ["rfm_score", "behavioral_engagement_score", "predicted_clv_score", "recency_days"],
                },
            ]

            METRIC_LABELS = {
                "rfm_score": "Avg RFM Score",
                "predicted_clv_score": "Avg CLV Score",
                "churn_risk_score": "Avg Churn Risk",
                "behavioral_engagement_score": "Avg Engagement",
                "purchases_90d": "Avg Purchases (90d)",
                "recency_days": "Avg Recency (days)",
                "price_sensitivity": "Avg Price Sensitivity",
                "complaint_count_90d": "Avg Complaints (90d)",
                "social_sentiment_avg": "Avg Social Sentiment",
                "email_click_rate": "Avg Email Click Rate",
                "email_open_rate": "Avg Email Open Rate",
                "avg_order_value_mad": "Avg Order Value (MAD)",
            }

            st.markdown("""
            <div style='margin-bottom:20px;'>
                <p style='color:#64748b; font-size:13px; line-height:1.6;'>
                    Each card below represents a distinct behavioral archetype derived from your rule-based RFM-ES + CLV segmentation.
                    Live metrics and client counts are computed from your current database.
                </p>
            </div>
            """, unsafe_allow_html=True)

            for i in range(0, len(PERSONA_CATALOG), 2):
                row_cols = st.columns(2)
                for j, col in enumerate(row_cols):
                    if i + j >= len(PERSONA_CATALOG):
                        break
                    p = PERSONA_CATALOG[i + j]

                    # Compute live metrics for this persona's clients
                    grp_df = clients_df[clients_df["customer_persona"] == p["persona"]]
                    client_count = len(grp_df)

                    chips_html = ""
                    for col_name in p["metrics_focus"]:
                        label = METRIC_LABELS.get(col_name, col_name)
                        if col_name in grp_df.columns and client_count > 0:
                            vals = pd.to_numeric(grp_df[col_name], errors="coerce").dropna()
                            val_str = f"{float(vals.mean()):.3f}" if len(vals) > 0 else "—"
                        else:
                            val_str = "—"
                        chips_html += f"<div class='persona-metric-chip'>{label}: <strong>{val_str}</strong></div>"

                    with col:
                        st.markdown(f"""
                        <div class='persona-card'>
                            <div class='persona-client-count'>{client_count} clients</div>
                            <div class='persona-icon-badge'>{p["icon"]}</div>
                            <div class='persona-name'>{p["persona"]}</div>
                            <div style='margin-bottom:10px;'>
                                <span class='persona-segment-tag' style='{p["tag_style"]}'>{p["segment"]}</span>
                            </div>
                            <div class='persona-desc'>{p["description"]}</div>
                            <div class='persona-metric-row'>{chips_html}</div>
                            <div class='persona-action-box'>
                                <strong style='color:#6ee7b7;font-size:11px;text-transform:uppercase;letter-spacing:0;'>Recommended Action</strong><br>
                                {p["action"]}
                            </div>
                            <div class='persona-rule-box'>
                                <span style='color:#64748b;font-size:10px;'>TRIGGER: </span>{p["trigger"]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if client_count > 0:
                            with st.expander(f"👁 View {min(client_count, 20)} clients in this persona"):
                                show_cols = ["entity_id", "dynamic_class", "predicted_clv_score",
                                             "rfm_score", "churn_risk_score", "recency_days"]
                                avail_cols = [c for c in show_cols if c in grp_df.columns]
                                st.dataframe(
                                    grp_df[avail_cols].head(20).style.format({
                                        "predicted_clv_score": "{:.1f}",
                                        "rfm_score": "{:.3f}",
                                        "churn_risk_score": "{:.3f}",
                                        "recency_days": "{:.0f}"
                                    }),
                                    hide_index=True, width="stretch"
                                )

    # ── Page 3: Simulate Event ────────────────────────────────────
    elif page == "Simulate Event":
        st.markdown("""
        <div class='page-hero'>
            <div class='page-kicker'>Simulation Console</div>
            <h1>Real-time Event Simulation</h1>
            <p>Trigger behavioral events and watch the Digital Twin classification update instantly.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        sim_col1, sim_col2 = st.columns([1, 1])

        with sim_col1:
            st.markdown("<div class='section-header'><span class='icon'>🎛️</span><span class='title'>Event Configuration</span></div>", unsafe_allow_html=True)
            entity_id_list = sorted(df_data["entity_id"].unique())
            selected_id = st.selectbox("Target Entity ID", entity_id_list, key="sim_entity")

            ent_details = df_data[df_data["entity_id"] == selected_id].iloc[0]
            ent_type = ent_details['entity_type']
            ent_class = ent_details['dynamic_class']
            type_color_sim = "#34d399" if ent_type == "Client" else "#2dd4bf"
            st.markdown(f"""
            <div style='background:rgba(45,212,191,0.08); border:1px solid rgba(45,212,191,0.2); border-radius:8px; padding:12px 16px; margin-bottom:16px;'>
                <div style='display:flex; gap:20px; flex-wrap:wrap;'>
                    <div><div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0;'>Type</div>
                    <div style='font-weight:700;color:{type_color_sim};font-size:14px;'>{ent_type}</div></div>
                    <div><div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0;'>Current Class</div>
                    <div style='font-weight:600;color:#e2e8f0;font-size:14px;font-family:JetBrains Mono,monospace;'>{ent_class}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            event_types = [
                ("page_visit",              "📄 Page Visit"),
                ("product_view",            "👁️ Product View"),
                ("add_to_cart",             "🛒 Add to Cart"),
                ("purchase",                "💳 Purchase"),
                ("email_open",              "📧 Email Open"),
                ("email_click",             "🖱️ Email Click"),
                ("complaint",               "😠 Customer Complaint"),
                ("positive_review",         "⭐ Positive Review"),
                ("negative_review",         "💢 Negative Review"),
                ("inactivity_period",       "💤 Inactivity Period"),
                ("social_positive_mention", "💬 Social Positive Mention"),
                ("social_negative_mention", "⚡ Social Negative Mention"),
            ]
            selected_event = st.selectbox(
                "Event Type",
                [e[0] for e in event_types],
                format_func=lambda x: next(item[1] for item in event_types if item[0] == x),
                key="sim_event_type"
            )

            val_input = None
            if selected_event == "purchase":
                val_input = st.number_input("Purchase Amount (MAD)", min_value=1.0, max_value=50000.0, value=250.0, step=50.0)
            elif selected_event == "inactivity_period":
                val_input = st.number_input("Inactivity Duration (Days)", min_value=1.0, max_value=90.0, value=15.0, step=5.0)

            submit_btn = st.button("🚀 Run Simulation", type="primary")
            
        with sim_col2:
            st.markdown("<div class='section-header'><span class='icon'>🧠</span><span class='title'>Dynamic Classification Output</span></div>", unsafe_allow_html=True)

            if submit_btn:
                df_data, df_history, before, after, old_c, new_c, pred_result, is_conv, ev_id = simulate_event(
                    df_data, df_history, selected_id, selected_event, val_input
                )
                st.success("✅ Event processed & saved to Excel workbook.")

                if is_conv:
                    st.session_state["pending_conversion_entity_id"] = selected_id
                    st.session_state["conversion_form_open"] = True
                    st.session_state["conversion_event_id"] = ev_id
                    st.session_state["profile_completed"] = False
                    st.markdown("<div class='conversion-banner'>🎉 <strong style='color:#34d399;'>Prospect converted to Client!</strong><br><span style='font-size:13px;color:#94a3b8;'>Complete the demographic profile in the popup form.</span></div>", unsafe_allow_html=True)

                conf = pred_result["confidence"]
                top_3 = pred_result["top_3"]
                class_changed = old_c != new_c

                # Main result card
                result_border = "#34d399" if not class_changed else "#2dd4bf"
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,rgba(45,212,191,0.15),rgba(139,92,246,0.10));
                            border:2px solid {result_border}; border-radius:8px; padding:20px;
                            text-align:center; margin-bottom:16px;
                            box-shadow: 0 8px 30px rgba(45,212,191,0.2);'>
                    <div style='font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#64748b;margin-bottom:8px;font-weight:600;'>{active_model} Prediction</div>
                    <div style='font-size:26px;font-weight:800;color:#e2e8f0;font-family:Space Grotesk,sans-serif;'>{new_c}</div>
                    <div style='font-size:15px;font-weight:700;color:#2dd4bf;margin-top:6px;'>Confidence: {conf*100:.1f}%</div>
                    <div style='font-size:12px;color:#64748b;margin-top:4px;'>{'✨ Classification Changed' if class_changed else '• Same Classification'}</div>
                </div>
                """, unsafe_allow_html=True)

                # Transition metrics
                m1, m2 = st.columns(2)
                with m1:
                    st.metric("Entity Type", after["entity_type"], delta="Converted" if is_conv else None)
                with m2:
                    st.metric("Class", new_c, delta="Changed ↑" if class_changed else None)

                # Top 3 probabilities
                st.markdown("<div style='margin:16px 0 8px; font-size:13px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0;'>Probability Distribution</div>", unsafe_allow_html=True)
                for rank, (cls_name, prob_val) in enumerate(top_3):
                    bar_fill = "fill-indigo" if rank == 0 else ("fill-violet" if rank == 1 else "fill-cyan")
                    label_color = "#2dd4bf" if rank == 0 else "#94a3b8"
                    st.markdown(f"""
                    <div class='score-bar-wrap'>
                        <div class='score-bar-label'>
                            <span style='color:{label_color};font-weight:{"700" if rank==0 else "500"};'>
                                {'🥇' if rank==0 else ('🥈' if rank==1 else '🥉')} {cls_name}
                            </span>
                            <span style='color:#e2e8f0;font-weight:700;'>{prob_val*100:.1f}%</span>
                        </div>
                        <div class='score-bar-track'><div class='score-bar-fill {bar_fill}' style='width:{prob_val*100:.1f}%'></div></div>
                    </div>
                    """, unsafe_allow_html=True)

                # Variable delta table
                st.markdown("<div style='margin:16px 0 8px; font-size:13px; font-weight:600; color:#94a3b8; text-transform:uppercase; letter-spacing:0;'>Changed Variables</div>", unsafe_allow_html=True)
                comp_cols = [
                    "recency_days", "visits_30d", "product_views_30d", "cart_additions_30d",
                    "purchases_90d", "total_spent_90d_mad", "avg_order_value_mad", "email_open_rate",
                    "email_click_rate", "complaint_count_90d", "review_score_avg", "social_mentions_30d",
                    "social_sentiment_avg", "rfm_score", "conversion_probability", "churn_risk_score",
                    "behavioral_engagement_score", "predictive_value_score", "decision_priority_score",
                    "predicted_clv_amount_mad", "predicted_clv_score", "predicted_clv_segment",
                    "clv_model_name", "clv_segment_model_name", "clv_method_used",
                    "clv_segment_prediction_source", "clv_segment_confidence",
                    "ml_predicted_clv_amount_mad", "math_clv_amount_mad",
                    "customer_segment", "customer_persona", "persona_recommended_action"
                ]
                comp_rows = []
                for col in comp_cols:
                    b_val = before.get(col)
                    a_val = after.get(col)
                    has_changed = False
                    if pd.isna(b_val) and pd.isna(a_val): has_changed = False
                    elif pd.isna(b_val) or pd.isna(a_val): has_changed = True
                    else:
                        try: has_changed = round(float(b_val),4) != round(float(a_val),4)
                        except: has_changed = str(b_val) != str(a_val)
                    if has_changed:
                        if col in ["total_spent_90d_mad", "avg_order_value_mad", "predicted_clv_amount_mad", "ml_predicted_clv_amount_mad", "math_clv_amount_mad"]: 
                            b_str = f"{float(b_val):.2f} MAD" if not pd.isna(b_val) and b_val is not None else "—"
                            a_str = f"{float(a_val):.2f} MAD" if not pd.isna(a_val) and a_val is not None else "—"
                        elif col in ["email_open_rate", "email_click_rate"]: 
                            b_str, a_str = f"{float(b_val)*100:.1f}%", f"{float(a_val)*100:.1f}%"
                        elif col in ["conversion_probability", "churn_risk_score", "rfm_score", "behavioral_engagement_score", "predictive_value_score", "decision_priority_score", "social_sentiment_avg"]: 
                            b_str, a_str = f"{float(b_val):.3f}", f"{float(a_val):.3f}"
                        elif col == "predicted_clv_score":
                            b_str = f"{float(b_val):.1f}" if not pd.isna(b_val) else "—"
                            a_str = f"{float(a_val):.1f}" if not pd.isna(a_val) else "—"
                        elif col == "clv_segment_confidence":
                            b_str = f"{float(b_val)*100:.1f}%" if not pd.isna(b_val) and b_val is not None else "N/A"
                            a_str = f"{float(a_val)*100:.1f}%" if not pd.isna(a_val) and a_val is not None else "N/A"
                        elif col == "review_score_avg": 
                            b_str, a_str = (f"{float(b_val):.2f}" if not pd.isna(b_val) else "N/A"), (f"{float(a_val):.2f}" if not pd.isna(a_val) else "N/A")
                        else: 
                            b_str = str(b_val) if not pd.isna(b_val) and b_val is not None else "—"
                            a_str = str(a_val) if not pd.isna(a_val) and a_val is not None else "—"
                        comp_rows.append({"Variable": col, "Before": b_str, "After": a_str})
                if comp_rows:
                    st.dataframe(pd.DataFrame(comp_rows), width="stretch", hide_index=True)
                else:
                    st.info("No variable values changed by this event.")

                if is_conv:
                    st.rerun()
            else:
                st.markdown("""
                <div style='display:flex;flex-direction:column;align-items:center;justify-content:center;
                            height:300px; opacity:0.5;'>
                    <div style='font-size:50px; margin-bottom:16px;'>⚡</div>
                    <div style='font-size:15px; color:#64748b; text-align:center;'>Configure an event on the left<br>and click <strong>Run Simulation</strong></div>
                </div>
                """, unsafe_allow_html=True)



    # ── Page 4: Create New Entity ──────────────────────────────────
    elif page == "Create New Entity":
        st.markdown(f"""
        <div class='page-hero'>
            <div class='page-kicker'>Entity Intake</div>
            <h1>Create New Entity</h1>
            <p>Register a Prospect or Client, initialize their Digital Twin, and get an instant {active_model} classification.</p>
        </div>
        """, unsafe_allow_html=True)

        entity_type = st.selectbox("Entity Type", ["Prospect", "Client"])

        with st.form("new_entity_form"):
            st.markdown("<div class='section-header'><span class='icon'>👤</span><span class='title'>Profile & Demographics</span></div>", unsafe_allow_html=True)

            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                region = st.selectbox("Region", [
                    "Casablanca-Settat", "Rabat-Salé-Kénitra", "Fès-Meknès",
                    "Marrakech-Safi", "Tangier-Tetouan-Al Hoceima", "Souss-Massa",
                    "Oriental", "Béni Mellal-Khénifra", "Daraa-Tafilalet",
                    "Guelmim-Oued Noun", "Laâyoune-Sakia El Hamra", "Dakhla-Oued Ed-Dahab"
                ])
                source_channel = st.selectbox("Acquisition Channel", [
                    "Organic SEO", "Google Search", "Facebook Ads", "Instagram Ads",
                    "Referral", "Marketplace App", "Direct Traffic", "Newsletter"
                ])
            with f_col2:
                segment = st.selectbox("Segment", ["B2C", "B2B", "Student", "Family", "Enterprise"])
                persona = st.selectbox("Customer Persona", [
                    "Price Sensitive", "Quality Seeker", "Trend Follower",
                    "B2B Decision Maker", "Loyalty Driven", "Tech Enthusiast"
                ])
                age_group = st.selectbox("Age Group", ["18-24", "25-34", "35-44", "45-54", "55+"])
            with f_col3:
                preferred_device   = st.selectbox("Preferred Device", ["Mobile", "Desktop", "Tablet"])
                preferred_category = st.selectbox("Preferred Category", ["Electronics", "Fashion", "Home", "Beauty", "Sports"])
                marketing_consent  = st.checkbox("Marketing Consent Given", value=True)

            if entity_type == "Client":
                st.markdown("<div class='section-header' style='margin-top:20px;'><span class='icon'>📈</span><span class='title'>Initial Client Activity</span></div>", unsafe_allow_html=True)
                c_col1, c_col2, c_col3 = st.columns(3)
                with c_col1:
                    initial_purchase_count = st.number_input("Initial Purchase Count", min_value=0, value=1, step=1)
                    initial_total_spent_mad = st.number_input("Initial Total Spent MAD", min_value=0.0, value=250.0, step=10.0)
                with c_col2:
                    initial_recency_days = st.number_input("Initial Recency Days", min_value=0, value=0, step=1)
                    initial_visits_30d = st.number_input("Initial Visits 30d", min_value=0, value=1, step=1)
                with c_col3:
                    initial_product_views_30d = st.number_input("Initial Product Views 30d", min_value=0, value=1, step=1)
                    initial_cart_additions_30d = st.number_input("Initial Cart Additions 30d", min_value=0, value=0, step=1)
                    
                st.markdown("<div style='margin-top:10px; font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:0;'>Optional Email Activity Settings</div>", unsafe_allow_html=True)
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    initial_email_open_rate = st.slider("Initial Email Open Rate", 0.0, 1.0, 0.0, 0.05)
                with e_col2:
                    initial_email_click_rate = st.slider("Initial Email Click Rate", 0.0, 1.0, 0.0, 0.05)
            else:
                initial_purchase_count = 0
                initial_total_spent_mad = 0.0
                initial_recency_days = 30.0
                initial_visits_30d = 0.0
                initial_product_views_30d = 0.0
                initial_cart_additions_30d = 0.0
                initial_email_open_rate = 0.0
                initial_email_click_rate = 0.0

            st.markdown("<div style='margin:20px 0 12px; font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0;'>Interest & Financial Scores</div>", unsafe_allow_html=True)
            sl1, sl2, sl3 = st.columns(3)
            with sl1: initial_interest_score = st.slider("Initial Interest Score", 0.0, 1.0, 0.3, 0.05)
            with sl2: income_power_score     = st.slider("Income Power Score",    0.0, 1.0, 0.5, 0.05)
            with sl3: price_sensitivity      = st.slider("Price Sensitivity",     0.0, 1.0, 0.6, 0.05)

            create_btn = st.form_submit_button("🔮 Initialize Digital Twin & Predict")

        if create_btn:
            entity_data = {
                "entity_type": entity_type, "region": region,
                "source_channel": source_channel, "segment": segment,
                "persona": persona, "age_group": age_group,
                "preferred_device": preferred_device, "preferred_category": preferred_category,
                "marketing_consent": marketing_consent,
                "initial_interest_score": initial_interest_score,
                "income_power_score": income_power_score, "price_sensitivity": price_sensitivity,
                "initial_purchase_count": initial_purchase_count,
                "initial_total_spent_mad": initial_total_spent_mad,
                "initial_recency_days": initial_recency_days,
                "initial_visits_30d": initial_visits_30d,
                "initial_product_views_30d": initial_product_views_30d,
                "initial_cart_additions_30d": initial_cart_additions_30d,
                "initial_email_open_rate": initial_email_open_rate,
                "initial_email_click_rate": initial_email_click_rate
            }
            df_data, new_entity_id, initial_class = create_new_entity(df_data, entity_data)

            if entity_type == "Client":
                st.session_state["pending_conversion_entity_id"] = new_entity_id
                st.session_state["conversion_form_open"] = True
                st.session_state["conversion_event_id"] = None
                st.session_state["profile_completed"] = False

            type_grad = "#2dd4bf" if entity_type == "Prospect" else "#34d399"
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(45,212,191,0.15),rgba(139,92,246,0.08));
                        border:2px solid {type_grad}; border-radius:8px; padding:28px;
                        text-align:center; margin-top:20px;
                        box-shadow:0 8px 30px rgba(45,212,191,0.2);'>
                <div style='font-size:40px; margin-bottom:10px;'>🔮</div>
                <h3 style='margin:0 0 14px; font-family:Space Grotesk,sans-serif; color:#f1f5f9;'>Digital Twin Initialized</h3>
                <div style='display:inline-flex; gap:30px; flex-wrap:wrap; justify-content:center;'>
                    <div><div style='font-size:11px;text-transform:uppercase;letter-spacing:0;color:#64748b;'>Entity ID</div>
                    <div style='font-size:20px;font-weight:700;color:#e2e8f0;font-family:JetBrains Mono,monospace;'>{new_entity_id}</div></div>
                    <div><div style='font-size:11px;text-transform:uppercase;letter-spacing:0;color:#64748b;'>Type</div>
                    <div style='font-size:20px;font-weight:700;color:{type_grad};'>{entity_type}</div></div>
                    <div><div style='font-size:11px;text-transform:uppercase;letter-spacing:0;color:#64748b;'>Predicted Class</div>
                    <div style='font-size:16px;font-weight:700;color:#2dd4bf;margin-top:4px;'>{initial_class}</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if entity_type == "Client":
                st.rerun()

    elif page == "Digital Twin & Persona":
        from digital_twin.digital_twin_dashboard import render_digital_twin_dashboard
        render_digital_twin_dashboard(df_data, df_history)

    elif page == "Campaign Simulation":
        from campaigns.campaign_dashboard import render_campaign_dashboard
        render_campaign_dashboard(df_data)

    elif page == "Database Intelligence":
        from admin.database_dashboard import render_database_dashboard
        render_database_dashboard(df_data, df_history)




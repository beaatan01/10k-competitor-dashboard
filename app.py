import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import html as py_html

from tenk_engine import (
    process_uploaded_file,
    process_peers,
    build_benchmark_dataframe,
    answer_question,
    stream_answer,
    build_forecast_dataframe,
    build_scenario_dataframe,
    monte_carlo_forecast,
    sensitivity_grid,
)

# ================================================================
# Page Setup
# ================================================================

st.set_page_config(
    page_title="Microsoft Financial Intelligence Platform",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# Session state defaults
# ================================================================

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}
if "copilot_question" not in st.session_state:
    st.session_state.copilot_question = "Summarize Microsoft revenue, margins, and cash flow."

# ================================================================
# Helpers
# ================================================================

def safe_html(content: str):
    st.markdown(content, unsafe_allow_html=True)


def fmt_cur(v, unit="auto"):
    if v is None:
        return "N/A"
    if unit == "B" or (unit == "auto" and abs(v) >= 1000):
        return f"${v / 1000:.1f}B"
    return f"${v:,.0f}M"


def fmt_pct(v):
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


def dataframe_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def render_section(title, subtitle, tag):
    safe_html(
        f"""
        <div class="section-head">
            <div>
                <div class="section-title">{py_html.escape(title)}</div>
                <div class="section-subtitle">{py_html.escape(subtitle)}</div>
            </div>
            <div class="section-tag">{py_html.escape(tag)}</div>
        </div>
        """
    )


def sparkline_svg(values, color="#0078D4", width=120, height=30):
    """Tiny inline SVG sparkline for KPI cards."""
    if not values or len(values) < 2:
        return ""
    vmin, vmax = min(values), max(values)
    rng = vmax - vmin if vmax != vmin else 1
    pts = []
    for i, v in enumerate(values):
        x = i * (width / (len(values) - 1))
        y = height - ((v - vmin) / rng) * height
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    last_x, last_y = pts[-1].split(",")
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;margin-top:6px;">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{path}"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        f'</svg>'
    )


def render_kpi_card(label, title, value, subtext, badge, badge_class="", spark_values=None, spark_color="#0078D4"):
    spark = sparkline_svg(spark_values, color=spark_color) if spark_values else ""
    safe_html(
        f"""
        <div class="kpi-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="card-title">{py_html.escape(title)}</div>
            <div class="card-value">{py_html.escape(value)}</div>
            <div class="card-sub">{py_html.escape(subtext)}</div>
            <div class="badge {badge_class}">
                <span class="dot"></span>{py_html.escape(badge)}
            </div>
            {spark}
        </div>
        """
    )


def render_capability_card(label, title, text):
    safe_html(
        f"""
        <div class="capability-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="capability-title">{py_html.escape(title)}</div>
            <div class="capability-text">{py_html.escape(text)}</div>
        </div>
        """
    )


def render_info_card(label, title, text, formula=None):
    formula_html = f'<div class="formula">{py_html.escape(formula)}</div>' if formula else ""
    safe_html(
        f"""
        <div class="info-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="info-title">{py_html.escape(title)}</div>
            <div class="info-text">{py_html.escape(text)}</div>
            {formula_html}
        </div>
        """
    )


def render_scenario_card(label, title, value, text):
    safe_html(
        f"""
        <div class="scenario-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="scenario-title">{py_html.escape(title)}</div>
            <div class="scenario-value">{py_html.escape(value)}</div>
            <div class="scenario-text">{py_html.escape(text)}</div>
        </div>
        """
    )


def render_insight(title, text):
    safe_html(
        f"""
        <div class="insight-card">
            <div class="insight-label">{py_html.escape(title)}</div>
            <div class="insight-text">{py_html.escape(text)}</div>
        </div>
        """
    )


def render_chart_title(title, caption):
    safe_html(
        f"""
        <div class="chart-title-card">
            <div class="chart-title">{py_html.escape(title)}</div>
            <div class="chart-caption">{py_html.escape(caption)}</div>
        </div>
        """
    )


def render_financial_table(title, df, note=None):
    headers = "".join([f"<th>{py_html.escape(str(col))}</th>" for col in df.columns])
    rows = ""
    for _, row in df.iterrows():
        cells = "".join([f"<td>{py_html.escape(str(value))}</td>" for value in row])
        rows += f"<tr>{cells}</tr>"
    note_html = f'<div class="table-note">{py_html.escape(note)}</div>' if note else ""
    safe_html(
        f"""
        <div class="table-card">
            <div class="table-card-head">
                <div>
                    <div class="table-title">{py_html.escape(title)}</div>
                    {note_html}
                </div>
            </div>
            <div class="table-wrap">
                <table class="finance-table">
                    <thead><tr>{headers}</tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
        """
    )


# ================================================================
# CSS (unchanged base styling)
# ================================================================

safe_html(
    """
    <style>
    :root {
        --blue: #0078D4; --green: #7FBA00; --orange: #F25022;
        --yellow: #FFB900; --purple: #8661C5;
        --text: #F3F2F1; --muted: #AEB6C5; --muted2: #7D8798;
        --glass: rgba(13, 19, 32, 0.42);
        --border: rgba(255, 255, 255, 0.12);
        --shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
        --shadow-hover: 0 26px 68px rgba(0, 0, 0, 0.50);
    }
    html, body, .stApp {
        color: var(--text) !important;
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    body { background: #030814 !important; }
    .stApp {
        background:
            radial-gradient(circle at 12% 12%, rgba(0,120,212,0.34), transparent 30%),
            radial-gradient(circle at 88% 10%, rgba(127,186,0,0.18), transparent 28%),
            radial-gradient(circle at 70% 84%, rgba(134,97,197,0.30), transparent 34%),
            linear-gradient(135deg, #031021 0%, #050817 48%, #06120d 100%) !important;
        background-size: 160% 160%;
        animation: ambientShift 18s ease-in-out infinite alternate;
        min-height: 100vh;
    }
    @keyframes ambientShift {
        0% { background-position: 0% 0%, 100% 0%, 70% 100%, 0% 0%; }
        50% { background-position: 18% 10%, 86% 18%, 60% 84%, 50% 50%; }
        100% { background-position: 6% 18%, 74% 10%, 82% 70%, 100% 100%; }
    }
    [data-testid="stAppViewContainer"] { background: transparent !important; }
    [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
    [data-testid="stSidebar"] {
        background: rgba(8, 12, 22, 0.75) !important;
        border-right: 1px solid rgba(255,255,255,0.08);
        backdrop-filter: blur(24px);
    }
    .block-container { max-width: 1500px !important; padding: 1.05rem 1.35rem 2.25rem 1.35rem !important; }
    #MainMenu, footer, header { visibility: hidden; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.34rem; background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.08); border-radius: 999px;
        padding: 0.30rem; margin-bottom: 1rem; backdrop-filter: blur(24px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px; padding: 0 1.05rem; border-radius: 999px !important;
        color: rgba(218,226,238,0.66); font-weight: 680; font-size: 0.92rem;
        transition: all 0.16s ease !important; border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255,255,255,0.075) !important; color: #E6F4FF !important;
        border-color: rgba(255,255,255,0.13);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0,120,212,0.22) !important;
        border: 1px solid rgba(0,120,212,0.50) !important;
        color: #E6F4FF !important; box-shadow: 0 0 24px rgba(0,120,212,0.22);
    }

    .hero {
        position: relative; min-height: 154px; border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.13);
        background: linear-gradient(145deg, rgba(255,255,255,0.105), rgba(255,255,255,0.026)), rgba(10, 15, 28, 0.38);
        backdrop-filter: blur(28px); box-shadow: var(--shadow);
        padding: 1.05rem 1.25rem; overflow: hidden; margin-bottom: 1rem;
    }
    .hero::after {
        content: ""; position: absolute; right: -120px; top: -120px;
        width: 280px; height: 280px;
        background: radial-gradient(circle, rgba(0,120,212,0.28), transparent 64%);
        pointer-events: none;
    }
    .hero-content { position: relative; z-index: 2; max-width: 930px; }
    .hero-topline {
        display: flex; align-items: center; gap: 0.48rem; color: #D9EEFF;
        font-size: 0.57rem; font-weight: 760; letter-spacing: 0.145em;
        text-transform: uppercase; margin-bottom: 0.46rem;
    }
    .logo-squares { width: 10px; height: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 2px; }
    .logo-squares span:nth-child(1) { background: #F25022; }
    .logo-squares span:nth-child(2) { background: #7FBA00; }
    .logo-squares span:nth-child(3) { background: #0078D4; }
    .logo-squares span:nth-child(4) { background: #FFB900; }
    .hero-title { color: #FFFFFF; font-size: clamp(1.55rem, 1.95vw, 2.06rem); font-weight: 720; letter-spacing: -0.015em; line-height: 1.22; margin-bottom: 0.43rem; max-width: 700px; }
    .hero-subtitle { color: #C8CED9; font-size: 0.725rem; line-height: 1.58; max-width: 940px; }
    .pill-row { display: flex; flex-wrap: wrap; gap: 0.38rem; margin-top: 0.70rem; }
    .pill {
        display: inline-flex; align-items: center; padding: 0.27rem 0.48rem;
        border-radius: 999px; color: #DDE5F0; background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.115); font-size: 0.595rem; font-weight: 700;
    }
    .pill.blue { color: #E0F2FF; background: rgba(0,120,212,0.18); border-color: rgba(0,120,212,0.42); }

    .section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 0.85rem; margin: 1rem 0 0.54rem 0; }
    .section-title { color: #FFFFFF; font-size: 0.845rem; font-weight: 740; line-height: 1.32; }
    .section-subtitle { color: var(--muted2); font-size: 0.665rem; line-height: 1.48; margin-top: 0.16rem; }
    .section-tag {
        color: #DDF1FF; background: rgba(0,120,212,0.15);
        border: 1px solid rgba(0,120,212,0.36); border-radius: 999px;
        padding: 0.28rem 0.50rem; font-size: 0.60rem; font-weight: 740; white-space: nowrap;
    }

    .kpi-card, .capability-card, .info-card, .scenario-card, .insight-card, .chart-title-card, .table-card {
        position: relative; border-radius: 18px; border: 1px solid rgba(255,255,255,0.125);
        background: linear-gradient(145deg, rgba(255,255,255,0.095), rgba(255,255,255,0.022)), rgba(12, 18, 31, 0.36);
        backdrop-filter: blur(26px); box-shadow: var(--shadow); overflow: hidden;
        transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }
    .kpi-card:hover, .capability-card:hover, .info-card:hover, .scenario-card:hover, .insight-card:hover {
        transform: translateY(-4px); border-color: rgba(0,120,212,0.55);
        box-shadow: var(--shadow-hover);
    }
    .kpi-card { min-height: 148px; padding: 0.76rem; margin-bottom: 0.72rem; }
    .capability-card, .info-card, .scenario-card { min-height: 104px; padding: 0.76rem; margin-bottom: 0.72rem; }
    .card-label { color: #D9EEFF; font-size: 0.54rem; font-weight: 780; letter-spacing: 0.145em; text-transform: uppercase; margin-bottom: 0.36rem; }
    .card-title { color: #D8DEE9; font-size: 0.70rem; font-weight: 700; line-height: 1.32; margin-bottom: 0.36rem; }
    .card-value { color: #FFFFFF; font-size: 1.14rem; font-weight: 780; letter-spacing: -0.025em; margin-bottom: 0.24rem; }
    .card-sub { color: #AAB2C1; font-size: 0.60rem; line-height: 1.38; margin-bottom: 0.46rem; }
    .badge {
        display: inline-flex; align-items: center; gap: 0.31rem;
        padding: 0.245rem 0.415rem; border-radius: 999px; color: #DDF1FF;
        border: 1px solid rgba(0,120,212,0.34); background: rgba(0,120,212,0.15);
        font-size: 0.555rem; font-weight: 760;
    }
    .badge.green { color: #E7FAC2; border-color: rgba(127,186,0,0.38); background: rgba(127,186,0,0.145); }
    .badge.orange { color: #FFC7BD; border-color: rgba(242,80,34,0.36); background: rgba(242,80,34,0.14); }
    .dot { width: 6px; height: 6px; border-radius: 999px; background: currentColor; box-shadow: 0 0 10px currentColor; display: inline-block; }
    .capability-title, .info-title, .scenario-title { color: #FFFFFF; font-size: 0.80rem; font-weight: 720; margin-bottom: 0.30rem; line-height: 1.35; }
    .capability-text, .info-text, .scenario-text { color: #AAB2C1; font-size: 0.63rem; line-height: 1.46; }
    .scenario-value { color: #FFFFFF; font-size: 1.12rem; font-weight: 780; letter-spacing: -0.028em; margin-bottom: 0.24rem; }
    .formula { margin-top: 0.46rem; padding: 0.36rem 0.46rem; color: #DDF1FF; background: rgba(0,120,212,0.13); border: 1px solid rgba(0,120,212,0.30); border-radius: 10px; font-size: 0.56rem; font-weight: 700; }
    .insight-card { padding: 0.78rem 0.85rem; margin-top: 0.35rem; margin-bottom: 0.72rem; border-color: rgba(0,120,212,0.30); }
    .insight-label { color: #DDF1FF; font-size: 0.56rem; font-weight: 780; letter-spacing: 0.145em; text-transform: uppercase; margin-bottom: 0.36rem; }
    .insight-text { color: #DDE3EE; font-size: 0.66rem; line-height: 1.54; }
    .chart-title-card { min-height: 46px; padding: 0.60rem 0.70rem; margin-bottom: 0.50rem; display: flex; justify-content: space-between; align-items: center; }
    .chart-title { color: #FFFFFF; font-size: 0.70rem; font-weight: 720; }
    .chart-caption { color: #8F99AA; font-size: 0.57rem; font-weight: 680; }
    .table-card { padding: 0.82rem; margin-bottom: 0.9rem; }
    .table-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.58rem; }
    .table-title { color: #FFFFFF; font-size: 0.78rem; font-weight: 720; }
    .table-note { color: var(--muted2); font-size: 0.58rem; margin-top: 0.12rem; }
    .table-wrap { overflow-x: auto; border-radius: 13px; border: 1px solid rgba(255,255,255,0.08); background: rgba(5,8,18,0.32); }
    table.finance-table { width: 100%; border-collapse: collapse; font-size: 0.64rem; color: #DDE3EE; min-width: 520px; }
    .finance-table th { background: rgba(255,255,255,0.055); color: #DDF1FF; text-align: left; font-weight: 720; padding: 0.46rem 0.54rem; border-bottom: 1px solid rgba(255,255,255,0.09); }
    .finance-table td { padding: 0.46rem 0.54rem; border-bottom: 1px solid rgba(255,255,255,0.060); color: #D6DCE7; }
    .finance-table tr:hover td { background: rgba(0,120,212,0.08); }
    h3 { color: #FFFFFF !important; font-size: 0.82rem !important; font-weight: 720 !important; margin: 0.52rem 0 0.42rem 0 !important; }

    .stDownloadButton button, .stButton button {
        font-size: 0.62rem !important; padding: 0.35rem 0.60rem !important;
        border-radius: 999px !important; color: #FFFFFF !important;
        background: rgba(0,120,212,0.68) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        box-shadow: 0 10px 22px rgba(0,120,212,0.20);
    }
    .stButton button:hover {
        background: rgba(0,120,212,0.85) !important;
        border-color: rgba(0,120,212,0.60) !important;
    }
    .stTextArea textarea, .stTextInput input {
        color: #F3F2F1 !important; background: rgba(15,20,34,0.35) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important; font-size: 0.70rem !important;
    }
    .stTextArea label, .stTextInput label, .stSlider label, .stSelectbox label, .stMultiSelect label, .stRadio label {
        color: #AAB2C1 !important; font-size: 0.62rem !important; font-weight: 720 !important;
        text-transform: uppercase; letter-spacing: 0.10em;
    }
    </style>
    """
)

# ================================================================
# Sidebar: global controls
# ================================================================

with st.sidebar:
    safe_html('<div class="card-label" style="margin-bottom:0.6rem;">Global Controls</div>')

    uploaded = st.file_uploader(
        "Upload a 10-K (optional)",
        type=["pdf", "xlsx", "csv"],
        help="If omitted, the Microsoft demo dataset is used.",
    )

    unit_choice = st.radio(
        "Display unit",
        options=["Auto", "Millions", "Billions"],
        horizontal=True,
        index=0,
    )
    unit_map = {"Auto": "auto", "Millions": "M", "Billions": "B"}
    unit = unit_map[unit_choice]

    peer_options = ["Apple", "Alphabet", "Amazon"]
    selected_peers = st.multiselect(
        "Compare against peers",
        options=peer_options,
        default=["Apple", "Alphabet"],
    )

    st.markdown("---")
    safe_html('<div class="card-label" style="margin-bottom:0.4rem;">About</div>')
    safe_html(
        '<div style="color:#AAB2C1; font-size:0.62rem; line-height:1.5;">'
        'This platform transforms 10-K disclosures into an executive-ready analytics experience. '
        'Peer data is illustrative.'
        '</div>'
    )

# ================================================================
# Data
# ================================================================

result = process_uploaded_file(uploaded)
peer_results = process_peers(selected_peers)
company_results = {"Microsoft": result, **peer_results}
benchmark_df = build_benchmark_dataframe(company_results)

k = result["kpis"]
ts = k["time_series"].copy()
segment_revenue = k["segment_revenue"].copy()

def _cur(v):
    return fmt_cur(v, unit=unit)

# ================================================================
# Plotly Styling
# ================================================================

def style_fig(fig, height=236, showlegend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, Inter, sans-serif", color="#C9D0DC", size=10),
        margin=dict(l=34, r=18, t=8, b=30),
        hovermode="x unified",
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1,
                    font=dict(color="#C9D0DC", size=

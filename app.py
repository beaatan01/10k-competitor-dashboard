import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import html as py_html
from datetime import datetime

from tenk_engine import (
    process_uploaded_file, process_peers, build_benchmark_dataframe,
    answer_question, stream_answer,
    build_forecast_dataframe, build_scenario_dataframe,
    monte_carlo_forecast, sensitivity_grid,
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

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}
if "copilot_question" not in st.session_state:
    st.session_state.copilot_question = "Summarize Microsoft revenue, margins, and cash flow."

# ================================================================
# Helpers
# ================================================================

def safe_html(content: str):
    st.markdown(content, unsafe_allow_html=True)

def fmt_cur(v):
    if v is None: return "N/A"
    if abs(v) >= 1000: return f"${v/1000:,.1f}B"
    return f"${v:,.0f}M"

def fmt_pct(v):
    if v is None: return "N/A"
    return f"{v*100:.1f}%"

def dataframe_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def delta_html(value, positive_is_good=True):
    """Return colored delta arrow + value."""
    if value is None:
        return ""
    is_positive = value >= 0
    good = (is_positive and positive_is_good) or (not is_positive and not positive_is_good)
    color = "#0F7B3D" if good else "#B42318"
    arrow = "▲" if is_positive else "▼"
    return f'<span class="delta" style="color:{color};">{arrow} {fmt_pct(abs(value))}</span>'

def render_section(title, subtitle, tag):
    safe_html(f"""
        <div class="section-head">
            <div>
                <div class="section-title">{py_html.escape(title)}</div>
                <div class="section-subtitle">{py_html.escape(subtitle)}</div>
            </div>
            <div class="section-tag">{py_html.escape(tag)}</div>
        </div>
    """)

def sparkline_svg(values, color="#0A2540", width=140, height=32):
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
    # Area fill
    area = f"0,{height} " + path + f" {width},{height}"
    last_x, last_y = pts[-1].split(",")
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block;margin-top:8px;">'
        f'<polygon fill="{color}" fill-opacity="0.08" points="{area}"/>'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{path}"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        f'</svg>'
    )

def render_kpi_card(label, title, value, subtext, delta_val=None, positive_is_good=True,
                    spark_values=None, spark_color="#0A2540"):
    spark = sparkline_svg(spark_values, color=spark_color) if spark_values else ""
    delta = delta_html(delta_val, positive_is_good) if delta_val is not None else ""
    safe_html(f"""
        <div class="kpi-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="card-title">{py_html.escape(title)}</div>
            <div class="card-value">{py_html.escape(value)}</div>
            <div class="card-sub">{py_html.escape(subtext)} {delta}</div>
            {spark}
        </div>
    """)

def render_capability_card(label, title, text):
    safe_html(f"""
        <div class="capability-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="capability-title">{py_html.escape(title)}</div>
            <div class="capability-text">{py_html.escape(text)}</div>
        </div>
    """)

def render_info_card(label, title, text, formula=None):
    formula_html = f'<div class="formula">{py_html.escape(formula)}</div>' if formula else ""
    safe_html(f"""
        <div class="info-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="info-title">{py_html.escape(title)}</div>
            <div class="info-text">{py_html.escape(text)}</div>
            {formula_html}
        </div>
    """)

def render_scenario_card(label, title, value, text):
    safe_html(f"""
        <div class="scenario-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="scenario-title">{py_html.escape(title)}</div>
            <div class="scenario-value">{py_html.escape(value)}</div>
            <div class="scenario-text">{py_html.escape(text)}</div>
        </div>
    """)

def render_insight(title, text):
    safe_html(f"""
        <div class="insight-card">
            <div class="insight-label">{py_html.escape(title)}</div>
            <div class="insight-text">{py_html.escape(text)}</div>
        </div>
    """)

def render_chart_title(title, caption):
    safe_html(f"""
        <div class="chart-title-card">
            <div class="chart-title">{py_html.escape(title)}</div>
            <div class="chart-caption">{py_html.escape(caption)}</div>
        </div>
    """)

def render_financial_table(title, df, note=None):
    headers = "".join([f"<th>{py_html.escape(str(c))}</th>" for c in df.columns])
    rows = ""
    for _, row in df.iterrows():
        cells = "".join([f"<td>{py_html.escape(str(v))}</td>" for v in row])
        rows += f"<tr>{cells}</tr>"
    note_html = f'<div class="table-note">{py_html.escape(note)}</div>' if note else ""
    safe_html(f"""
        <div class="table-card">
            <div class="table-card-head"><div><div class="table-title">{py_html.escape(title)}</div>{note_html}</div></div>
            <div class="table-wrap"><table class="finance-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>
        </div>
    """)

# ================================================================
# CSS — Option B: Executive Light
# ================================================================

safe_html("""
<style>
:root {
    --bg: #F7F7F4;
    --bg-alt: #FFFFFF;
    --ink: #0A2540;
    --ink-2: #1A2B44;
    --muted: #4A5878;
    --muted-2: #7A879B;
    --hairline: #E4E7EC;
    --accent: #0A2540;
    --accent-soft: #E8EDF5;
    --good: #0F7B3D;
    --bad: #B42318;
    --warn: #B54708;
    --card: #FFFFFF;
    --shadow: 0 1px 2px rgba(16,24,40,0.05), 0 1px 3px rgba(16,24,40,0.08);
    --shadow-hover: 0 8px 24px rgba(10,37,64,0.12), 0 2px 6px rgba(10,37,64,0.08);
    --radius: 10px;
}

html, body, .stApp {
    color: var(--ink) !important;
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    font-feature-settings: "cv02","cv03","cv04","cv11";
}
body, .stApp { background: var(--bg) !important; }
[data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="stSidebar"] {
    background: var(--bg-alt) !important;
    border-right: 1px solid var(--hairline);
}
[data-testid="stSidebar"] * { color: var(--ink) !important; }
.block-container { max-width: 1500px !important; padding: 1.05rem 1.35rem 2.25rem !important; }
#MainMenu, footer, header { visibility: hidden; }

/* Sticky top bar */
.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; margin-bottom: 12px;
    background: var(--bg-alt); border: 1px solid var(--hairline);
    border-radius: var(--radius); box-shadow: var(--shadow);
}
.topbar-left { display: flex; align-items: center; gap: 10px; }
.topbar-logo {
    width: 22px; height: 22px; display: grid; grid-template-columns: 1fr 1fr; gap: 2px;
}
.topbar-logo span:nth-child(1){background:#F25022;}
.topbar-logo span:nth-child(2){background:#7FBA00;}
.topbar-logo span:nth-child(3){background:#00A4EF;}
.topbar-logo span:nth-child(4){background:#FFB900;}
.topbar-title { font-weight: 700; font-size: 0.92rem; color: var(--ink); letter-spacing: -0.01em; }
.topbar-crumb { color: var(--muted); font-size: 0.72rem; font-weight: 500; }
.topbar-right { display: flex; gap: 14px; align-items: center; color: var(--muted); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.02em; }
.topbar-dot { width:6px; height:6px; border-radius:999px; background: var(--good); display:inline-block; margin-right:6px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: transparent;
    border-bottom: 1px solid var(--hairline);
    padding: 0; margin-bottom: 18px; border-radius: 0;
    box-shadow: none;
}
.stTabs [data-baseweb="tab"] {
    height: 40px; padding: 0 14px; border-radius: 0 !important;
    color: var(--muted); font-weight: 600; font-size: 0.82rem;
    border: none; border-bottom: 2px solid transparent;
    background: transparent !important;
    transition: all 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
    background: rgba(10,37,64,0.03) !important;
    border-bottom: 2px solid var(--hairline);
}
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    background: transparent !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 700;
}

/* Hero */
.hero {
    position: relative;
    border-radius: var(--radius);
    border: 1px solid var(--hairline);
    background: linear-gradient(135deg, #FFFFFF 0%, #F0F3F8 100%);
    padding: 20px 24px; overflow: hidden;
    margin-bottom: 18px;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s ease;
}
.hero:hover { box-shadow: var(--shadow-hover); }
.hero::after {
    content: ""; position: absolute; right: -80px; top: -80px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(10,37,64,0.06), transparent 70%);
    pointer-events: none;
}
.hero-content { position: relative; z-index: 2; max-width: 940px; }
.hero-topline {
    display: flex; align-items: center; gap: 8px;
    color: var(--muted); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 10px;
}
.hero-title {
    color: var(--ink); font-size: clamp(1.6rem, 2vw, 2.1rem);
    font-weight: 700; letter-spacing: -0.02em; line-height: 1.2;
    margin-bottom: 8px; max-width: 780px;
}
.hero-subtitle { color: var(--muted); font-size: 0.78rem; line-height: 1.55; max-width: 900px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.pill {
    display: inline-flex; align-items: center; padding: 4px 10px;
    border-radius: 999px; color: var(--ink); background: var(--accent-soft);
    border: 1px solid var(--hairline);
    font-size: 0.64rem; font-weight: 600; letter-spacing: 0.02em;
}
.pill.blue {
    color: #FFFFFF; background: var(--accent);
    border-color: var(--accent);
}

/* Section headers */
.section-head {
    display: flex; align-items: flex-end; justify-content: space-between;
    gap: 12px; margin: 20px 0 10px 0;
    padding-bottom: 8px; border-bottom: 1px solid var(--hairline);
}
.section-title { color: var(--ink); font-size: 0.95rem; font-weight: 700; letter-spacing: -0.005em; }
.section-subtitle { color: var(--muted); font-size: 0.72rem; margin-top: 3px; }
.section-tag {
    color: var(--muted); background: transparent;
    border: 1px solid var(--hairline); border-radius: 4px;
    padding: 3px 8px; font-size: 0.62rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    white-space: nowrap;
}

/* Cards */
.kpi-card, .capability-card, .info-card, .scenario-card, .insight-card, .chart-title-card, .table-card {
    position: relative; border-radius: var(--radius);
    border: 1px solid var(--hairline); background: var(--card);
    box-shadow: var(--shadow); overflow: hidden;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.kpi-card:hover, .capability-card:hover, .info-card:hover, .scenario-card:hover, .insight-card:hover {
    transform: translateY(-3px);
    border-color: #C7D0DD;
    box-shadow: var(--shadow-hover);
}
.kpi-card { min-height: 160px; padding: 16px; margin-bottom: 12px; }
.capability-card, .info-card, .scenario-card { min-height: 110px; padding: 16px; margin-bottom: 12px; }

.card-label {
    color: var(--muted); font-size: 0.60rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 8px;
}
.card-title {
    color: var(--muted); font-size: 0.74rem; font-weight: 600;
    line-height: 1.3; margin-bottom: 6px;
}
.card-value {
    color: var(--ink); font-size: 1.55rem; font-weight: 700;
    letter-spacing: -0.02em; margin-bottom: 4px; line-height: 1.15;
    font-variant-numeric: tabular-nums;
    font-family: "Inter", -apple-system, sans-serif;
}
.card-sub {
    color: var(--muted); font-size: 0.68rem; line-height: 1.4;
    font-variant-numeric: tabular-nums;
}
.delta { font-weight: 700; font-size: 0.68rem; margin-left: 4px; font-variant-numeric: tabular-nums; }

.capability-title, .info-title, .scenario-title {
    color: var(--ink); font-size: 0.86rem; font-weight: 700;
    margin-bottom: 6px; line-height: 1.3; letter-spacing: -0.005em;
}
.capability-text, .info-text, .scenario-text {
    color: var(--muted); font-size: 0.70rem; line-height: 1.5;
}
.scenario-value {
    color: var(--ink); font-size: 1.32rem; font-weight: 700;
    letter-spacing: -0.02em; margin-bottom: 4px;
    font-variant-numeric: tabular-nums;
}
.formula {
    margin-top: 10px; padding: 8px 10px;
    color: var(--ink); background: var(--accent-soft);
    border: 1px solid var(--hairline);
    border-radius: 6px; font-size: 0.62rem; font-weight: 600;
    font-family: "SF Mono", Menlo, monospace;
}

.insight-card {
    padding: 14px 16px; margin-top: 6px; margin-bottom: 12px;
    border-left: 3px solid var(--accent);
    background: var(--accent-soft);
}
.insight-label {
    color: var(--accent); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 6px;
}
.insight-text { color: var(--ink-2); font-size: 0.76rem; line-height: 1.55; font-variant-numeric: tabular-nums; }

.chart-title-card {
    min-height: 44px; padding: 10px 14px; margin-bottom: 8px;
    display: flex; justify-content: space-between; align-items: center;
}
.chart-title { color: var(--ink); font-size: 0.80rem; font-weight: 700; }
.chart-caption {
    color: var(--muted); font-size: 0.64rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em;
}

.table-card { padding: 16px; margin-bottom: 14px; }
.table-card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.table-title { color: var(--ink); font-size: 0.88rem; font-weight: 700; }
.table-note { color: var(--muted); font-size: 0.64rem; margin-top: 3px; }
.table-wrap {
    overflow-x: auto; border-radius: 6px;
    border: 1px solid var(--hairline); background: #FDFDFC;
}
table.finance-table {
    width: 100%; border-collapse: collapse; font-size: 0.72rem;
    color: var(--ink-2); min-width: 520px;
    font-variant-numeric: tabular-nums;
}
.finance-table th {
    background: #F5F7FA; color: var(--muted);
    text-align: left; font-weight: 700; font-size: 0.62rem;
    text-transform: uppercase; letter-spacing: 0.08em;
    padding: 10px 12px; border-bottom: 1px solid var(--hairline);
}
.finance-table td {
    padding: 10px 12px; border-bottom: 1px solid var(--hairline);
    color: var(--ink-2);
}
.finance-table tr:nth-child(even) td { background: #FAFBFC; }
.finance-table tr:hover td { background: var(--accent-soft); }
/* Right-align columns after the first */
.finance-table th:not(:first-child), .finance-table td:not(:first-child) { text-align: right; }

h3 {
    color: var(--ink) !important; font-size: 0.90rem !important;
    font-weight: 700 !important; margin: 12px 0 8px 0 !important;
}

/* Buttons */
.stDownloadButton button, .stButton button {
    font-size: 0.72rem !important; padding: 8px 14px !important;
    border-radius: 6px !important; color: #FFFFFF !important;
    background: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: none;
    font-weight: 600 !important;
    transition: all 0.15s ease;
}
.stButton button:hover, .stDownloadButton button:hover {
    background: #143557 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(10,37,64,0.18);
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    color: var(--ink) !important; background: #FFFFFF !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 6px !important; font-size: 0.80rem !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(10,37,64,0.10) !important;
}
.stTextArea label, .stTextInput label, .stSlider label,
.stSelectbox label, .stMultiSelect label, .stRadio label, .stFileUploader label {
    color: var(--muted) !important; font-size: 0.66rem !important;
    font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.10em;
}

/* Slider polish */
.stSlider [data-baseweb="slider"] > div > div { background: var(--accent) !important; }
</style>
""")

# ================================================================
# Sticky top bar
# ================================================================

now_str = datetime.now().strftime("%b %d, %Y · %H:%M")
safe_html(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-logo"><span></span><span></span><span></span><span></span></div>
    <div>
      <div class="topbar-title">Microsoft Financial Intelligence Platform</div>
      <div class="topbar-crumb">Enlyte Analytics · FY2025 10-K Analysis · Source: SEC Filing</div>
    </div>
  </div>
  <div class="topbar-right">
    <span><span class="topbar-dot"></span>Live</span>
    <span>Last refresh · {now_str}</span>
  </div>
</div>
""")

# ================================================================
# Sidebar
# ================================================================

with st.sidebar:
    safe_html('<div class="card-label" style="margin-bottom:10px;">Global Controls</div>')
    uploaded = st.file_uploader("Upload 10-K (optional)", type=["pdf", "xlsx", "csv"])
    peer_options = ["Apple", "Alphabet", "Amazon"]
    selected_peers = st.multiselect("Peer set", options=peer_options, default=["Apple", "Alphabet"])
    st.markdown("---")
    safe_html('<div class="card-label" style="margin-bottom:6px;">About</div>')
    safe_html('<div style="color:#4A5878; font-size:0.72rem; line-height:1.5;">Transforms 10-K disclosures into an executive-ready analytics experience. Peer data is illustrative.</div>')

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

# ================================================================
# Plotly styling (light theme)
# ================================================================

def style_fig(fig, height=240, showlegend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color="#4A5878", size=11),
        margin=dict(l=44, r=18, t=10, b=34),
        hovermode="x unified",
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1,
                    font=dict(color="#4A5878", size=10)),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1,
                   linecolor="#E4E7EC",
                   tickfont=dict(color="#7A879B", size=10),
                   title_font=dict(color="#4A5878", size=11)),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#F0F2F5",
                   zeroline=False, showline=False,
                   tickfont=dict(color="#7A879B", size=10),
                   title_font=dict(color="#4A5878", size=11)),
    )
    return fig

# Executive palette
PALETTE = {
    "primary": "#0A2540",
    "accent": "#3E5C8E",
    "gold": "#B08D2E",
    "green": "#0F7B3D",
    "red": "#B42318",
    "warn": "#B54708",
    "muted": "#7A879B",
}
CHART_SEQ = ["#0A2540", "#3E5C8E", "#B08D2E", "#0F7B3D", "#7A879B", "#B54708"]

# ================================================================
# Tabs
# ================================================================

tab_welcome, tab_summary, tab_kpi, tab_revenue, tab_peers, tab_forecast, tab_financials, tab_ai = st.tabs(
    ["Welcome", "Executive Summary", "Intelligence Hub", "Revenue Intelligence",
     "Peer Benchmark", "AI Forecasting", "Financial Statements", "AI Copilot"]
)

# ---------- Welcome ----------
with tab_welcome:
    safe_html("""
    <div class="hero"><div class="hero-content">
        <div class="hero-topline">Microsoft Financial Intelligence Platform</div>
        <div class="hero-title">Executive analytics for FY2025 10-K disclosures</div>
        <div class="hero-subtitle">A modern executive dashboard that transforms 10-K financial data into a clean, presentation-ready intelligence experience. Use the sidebar to upload your own filing and toggle peer comparisons.</div>
        <div class="pill-row">
            <span class="pill blue">Executive Ready</span>
            <span class="pill">FY2023-FY2025</span>
            <span class="pill">Peer Benchmarks</span>
            <span class="pill">Monte Carlo Forecast</span>
            <span class="pill">AI Copilot</span>
        </div>
    </div></div>
    """)
    render_section("Platform Overview", "Why this dashboard was built and how it supports presentation workflows.", "Welcome")
    w1, w2 = st.columns(2, gap="medium")
    with w1:
        render_info_card("Why Built", "Executive Financial Clarity",
            "Converts dense 10-K disclosures into an executive-ready analytics experience.")
    with w2:
        render_info_card("Why FY2023-FY2025", "Three-Year Business Trend Window",
            "Long enough to show trend direction while staying recent enough for relevant interpretation.")
    w3, w4 = st.columns(2, gap="medium")
    with w3:
        render_info_card("Dashboard Architecture", "Layered Intelligence Design",
            "Welcome → KPIs → Revenue → Peer Benchmark → Forecasting → Statements → AI commentary.")
    with w4:
        render_info_card("Presentation Workflow", "From Data to Boardroom Narrative",
            "Context, then signals, then evidence, then outlook, then support.")

# ---------- Executive Summary ----------
with tab_summary:
    safe_html("""
    <div class="hero"><div class="hero-content">
        <div class="hero-topline">Executive Summary · FY2025</div>
        <div class="hero-title">Microsoft Financial Intelligence Platform</div>
        <div class="hero-subtitle">An analytics application built from Microsoft's FY2025 10-K data. Executive KPIs, revenue intelligence, forecasting scenarios, and natural-language commentary.</div>
        <div class="pill-row">
            <span class="pill blue">FY2025</span><span class="pill">10-K Analysis</span>
            <span class="pill">Revenue Intelligence</span><span class="pill">AI Forecasting</span>
        </div>
    </div></div>
    """)

    revenue = k["revenue"]; revenue_yoy = k["revenue_yoy_growth"]
    gross_margin = k["gross_margin"]; operating_margin = k["operating_margin"]; net_margin = k["net_margin"]
    fcf = k["free_cash_flow"]; cash_balance = k["cash_balance"]; total_debt = k["total_debt"]
    debt_to_cash = total_debt / cash_balance if cash_balance else None

    ts_chrono = ts.iloc[::-1].reset_index(drop=True)
    rev_spark = ts_chrono["revenue"].tolist()
    op_spark = ts_chrono["operating_margin"].tolist()
    fcf_spark = ts_chrono["free_cash_flow"].tolist()
    cash_spark = ts_chrono["cash_balance"].tolist()

    # Compute deltas
    op_prior = ts.loc[ts["period"] == "2024", "operating_margin"].iloc[0]
    op_delta = operating_margin - op_prior
    fcf_prior_row = ts.loc[ts["period"] == "2024", "free_cash_flow"].iloc[0]
    fcf_delta = (fcf - fcf_prior_row) / fcf_prior_row if fcf_prior_row else None
    cash_prior = ts.loc[ts["period"] == "2024", "cash_balance"].iloc[0]
    cash_delta = (cash_balance - cash_prior) / cash_prior if cash_prior else None

    render_section("Executive Snapshot", "Latest reported signals with three-year trend and prior-year delta.", "FY2025 View")
    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1:
        render_kpi_card("Revenue", f"FY{k['latest_period']} Total Revenue",
            fmt_cur(revenue), "vs FY2024",
            delta_val=revenue_yoy, spark_values=rev_spark, spark_color=PALETTE["primary"])
    with s2:
        render_kpi_card("Profitability", "Operating Margin",
            fmt_pct(operating_margin),
            f"Gross {fmt_pct(gross_margin)} · Net {fmt_pct(net_margin)}",
            delta_val=op_delta, spark_values=op_spark, spark_color=PALETTE["accent"])
    with s3:
        render_kpi_card("Cash Flow", "Free Cash Flow",
            fmt_cur(fcf), "OCF less capex",
            delta_val=fcf_delta, spark_values=fcf_spark, spark_color=PALETTE["green"])
    with s4:
        d2c = f"Debt {fmt_cur(total_debt)} · {debt_to_cash:.1f}x debt/cash" if debt_to_cash else "N/A"
        render_kpi_card("Liquidity", "Cash Position",
            fmt_cur(cash_balance), d2c,
            delta_val=cash_delta, spark_values=cash_spark, spark_color=PALETTE["gold"])

    render_section("Performance Drivers", "How each KPI should be interpreted.", "Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue", "Business Scale", "Top-line size and growth momentum.", "Growth = Current / Prior − 1")
    with e2: render_info_card("Margin", "Operating Efficiency", "How revenue converts to operating income.", "Operating Income / Revenue")
    with e3: render_info_card("Cash Flow", "Financial Output", "Cash available after capex.", "OCF − Capex")
    with e4: render_info_card("Liquidity", "Balance Sheet Flexibility", "Relationship between cash and debt.", "Debt / Cash")

# ---------- Intelligence Hub ----------
with tab_kpi:
    render_section("Executive KPI Intelligence", "Interpretive guidance for scale, efficiency, and flexibility.", "CFO View")
    render_insight("Intelligence Hub Overview",
        "The Executive Summary tab holds the KPI cards. This tab expands the interpretation guide for each metric.")
    render_section("Performance Drivers", "How each KPI should be interpreted.", "Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue", "Business Scale", "Top-line size and growth momentum.", "Growth = Current / Prior − 1")
    with e2: render_info_card("Margin", "Operating Efficiency", "How revenue converts to operating income.", "Operating Income / Revenue")
    with e3: render_info_card("Cash Flow", "Financial Output", "Cash available after capex.", "OCF − Capex")
    with e4: render_info_card("Liquidity", "Balance Sheet Flexibility", "Relationship between cash and debt.", "Debt / Cash")

# ---------- Revenue Intelligence ----------
with tab_revenue:
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]

    render_section("Revenue Performance", "Historical trend, mix, and growth bridge.", "Growth Analytics")

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        render_kpi_card("FY2025 Revenue", "Total Revenue", fmt_cur(k["revenue"]),
            "vs FY2024", delta_val=k["revenue_yoy_growth"])
    with r2:
        render_kpi_card("Revenue Mix", "Service & Other", fmt_pct(services_mix),
            "Share of FY2025 revenue")
    with r3:
        render_kpi_card("Growth Spread", "2025 vs 2024", fmt_cur(growth_spread),
            "Incremental revenue")

    left, right = st.columns(2, gap="medium")
    with left:
        render_chart_title("Revenue Over Time", "FY2023 – FY2025")
        fig_ts = px.line(ts.sort_values("period"), x="period", y="revenue", markers=True,
            color_discrete_sequence=[PALETTE["primary"]])
        fig_ts.update_traces(line=dict(width=2.5, shape="spline"),
            marker=dict(size=8, color=PALETTE["primary"], line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>")
        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_ts, height=240), width="stretch", config={"displayModeBar": False})

    with right:
        render_chart_title("Revenue Mix by Category", "Product vs Service")
        seg_long = segment_revenue.melt(id_vars=["period"],
            value_vars=["Product Revenue", "Service and Other Revenue"],
            var_name="category", value_name="revenue")
        fig_seg = px.bar(seg_long.sort_values("period"), x="period", y="revenue",
            color="category", barmode="stack",
            color_discrete_map={"Product Revenue": PALETTE["primary"],
                                "Service and Other Revenue": PALETTE["accent"]})
        fig_seg.update_traces(marker_line_width=0,
            hovertemplate="<b>FY%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
        fig_seg.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_seg, height=240, showlegend=True), width="stretch", config={"displayModeBar": False})

    render_chart_title("Revenue Bridge: FY2024 → FY2025", "Decomposed by segment contribution")
    prod_delta = k["product_revenue"] - k["product_revenue_prior"]
    svc_delta = k["service_revenue"] - k["service_revenue_prior"]
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["FY24 Revenue", "Product Δ", "Service Δ", "FY25 Revenue"],
        y=[k["prior_year_revenue"], prod_delta, svc_delta, k["revenue"]],
        connector={"line": {"color": "#C7D0DD", "dash": "dot"}},
        increasing={"marker": {"color": PALETTE["green"]}},
        decreasing={"marker": {"color": PALETTE["red"]}},
        totals={"marker": {"color": PALETTE

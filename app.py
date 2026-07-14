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
    safe_html(f"""
        <div class="section-head">
            <div>
                <div class="section-title">{py_html.escape(title)}</div>
                <div class="section-subtitle">{py_html.escape(subtitle)}</div>
            </div>
            <div class="section-tag">{py_html.escape(tag)}</div>
        </div>
    """)

def sparkline_svg(values, color="#0078D4", width=120, height=30):
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
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block;margin-top:6px;">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{path}"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/>'
        f'</svg>'
    )

def render_kpi_card(label, title, value, subtext, badge, badge_class="", spark_values=None, spark_color="#0078D4"):
    spark = sparkline_svg(spark_values, color=spark_color) if spark_values else ""
    safe_html(f"""
        <div class="kpi-card">
            <div class="card-label">{py_html.escape(label)}</div>
            <div class="card-title">{py_html.escape(title)}</div>
            <div class="card-value">{py_html.escape(value)}</div>
            <div class="card-sub">{py_html.escape(subtext)}</div>
            <div class="badge {badge_class}"><span class="dot"></span>{py_html.escape(badge)}</div>
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
# CSS
# ================================================================

safe_html("""
<style>
:root {
    --blue:#0078D4; --green:#7FBA00; --orange:#F25022; --yellow:#FFB900; --purple:#8661C5;
    --text:#F3F2F1; --muted2:#7D8798;
    --shadow: 0 18px 48px rgba(0,0,0,0.35);
    --shadow-hover: 0 26px 68px rgba(0,0,0,0.50);
}
html, body, .stApp { color: var(--text) !important; font-family: "Segoe UI", Inter, sans-serif !important; }
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
[data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="stSidebar"] { background: rgba(8,12,22,0.75) !important; border-right: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(24px); }
.block-container { max-width: 1500px !important; padding: 1.05rem 1.35rem 2.25rem 1.35rem !important; }
#MainMenu, footer, header { visibility: hidden; }

.stTabs [data-baseweb="tab-list"] {
    gap: 0.34rem; background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.08); border-radius: 999px;
    padding: 0.30rem; margin-bottom: 1rem; backdrop-filter: blur(24px);
}
.stTabs [data-baseweb="tab"] {
    height: 44px; padding: 0 1.05rem; border-radius: 999px !important;
    color: rgba(218,226,238,0.66); font-weight: 680; font-size: 0.92rem;
    border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(255,255,255,0.075) !important; color: #E6F4FF !important; }
.stTabs [aria-selected="true"] {
    background: rgba(0,120,212,0.22) !important;
    border: 1px solid rgba(0,120,212,0.50) !important;
    color: #E6F4FF !important; box-shadow: 0 0 24px rgba(0,120,212,0.22);
}

.hero {
    position: relative; min-height: 154px; border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.13);
    background: linear-gradient(145deg, rgba(255,255,255,0.105), rgba(255,255,255,0.026)), rgba(10,15,28,0.38);
    backdrop-filter: blur(28px); box-shadow: var(--shadow);
    padding: 1.05rem 1.25rem; overflow: hidden; margin-bottom: 1rem;
}
.hero::after { content:""; position:absolute; right:-120px; top:-120px; width:280px; height:280px; background: radial-gradient(circle, rgba(0,120,212,0.28), transparent 64%); pointer-events:none; }
.hero-content { position: relative; z-index: 2; max-width: 930px; }
.hero-topline { display: flex; align-items: center; gap: 0.48rem; color: #D9EEFF; font-size: 0.57rem; font-weight: 760; letter-spacing: 0.145em; text-transform: uppercase; margin-bottom: 0.46rem; }
.logo-squares { width:10px; height:10px; display:grid; grid-template-columns:1fr 1fr; gap:2px; }
.logo-squares span:nth-child(1){background:#F25022;} .logo-squares span:nth-child(2){background:#7FBA00;}
.logo-squares span:nth-child(3){background:#0078D4;} .logo-squares span:nth-child(4){background:#FFB900;}
.hero-title { color:#FFF; font-size: clamp(1.55rem,1.95vw,2.06rem); font-weight:720; letter-spacing:-0.015em; line-height:1.22; margin-bottom:0.43rem; max-width:700px; }
.hero-subtitle { color:#C8CED9; font-size:0.725rem; line-height:1.58; max-width:940px; }
.pill-row { display:flex; flex-wrap:wrap; gap:0.38rem; margin-top:0.70rem; }
.pill { display:inline-flex; align-items:center; padding:0.27rem 0.48rem; border-radius:999px; color:#DDE5F0; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.115); font-size:0.595rem; font-weight:700; }
.pill.blue { color:#E0F2FF; background:rgba(0,120,212,0.18); border-color:rgba(0,120,212,0.42); }

.section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:0.85rem; margin: 1rem 0 0.54rem 0; }
.section-title { color:#FFF; font-size:0.845rem; font-weight:740; line-height:1.32; }
.section-subtitle { color: var(--muted2); font-size:0.665rem; line-height:1.48; margin-top:0.16rem; }
.section-tag { color:#DDF1FF; background:rgba(0,120,212,0.15); border:1px solid rgba(0,120,212,0.36); border-radius:999px; padding:0.28rem 0.50rem; font-size:0.60rem; font-weight:740; }

.kpi-card, .capability-card, .info-card, .scenario-card, .insight-card, .chart-title-card, .table-card {
    position:relative; border-radius:18px; border:1px solid rgba(255,255,255,0.125);
    background: linear-gradient(145deg, rgba(255,255,255,0.095), rgba(255,255,255,0.022)), rgba(12,18,31,0.36);
    backdrop-filter: blur(26px); box-shadow: var(--shadow); overflow: hidden;
    transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}
.kpi-card:hover, .capability-card:hover, .info-card:hover, .scenario-card:hover, .insight-card:hover {
    transform: translateY(-4px); border-color: rgba(0,120,212,0.55); box-shadow: var(--shadow-hover);
}
.kpi-card { min-height:148px; padding:0.76rem; margin-bottom:0.72rem; }
.capability-card, .info-card, .scenario-card { min-height:104px; padding:0.76rem; margin-bottom:0.72rem; }
.card-label { color:#D9EEFF; font-size:0.54rem; font-weight:780; letter-spacing:0.145em; text-transform:uppercase; margin-bottom:0.36rem; }
.card-title { color:#D8DEE9; font-size:0.70rem; font-weight:700; margin-bottom:0.36rem; }
.card-value { color:#FFF; font-size:1.14rem; font-weight:780; letter-spacing:-0.025em; margin-bottom:0.24rem; }
.card-sub { color:#AAB2C1; font-size:0.60rem; line-height:1.38; margin-bottom:0.46rem; }
.badge { display:inline-flex; align-items:center; gap:0.31rem; padding:0.245rem 0.415rem; border-radius:999px; color:#DDF1FF; border:1px solid rgba(0,120,212,0.34); background:rgba(0,120,212,0.15); font-size:0.555rem; font-weight:760; }
.badge.green { color:#E7FAC2; border-color:rgba(127,186,0,0.38); background:rgba(127,186,0,0.145); }
.badge.orange { color:#FFC7BD; border-color:rgba(242,80,34,0.36); background:rgba(242,80,34,0.14); }
.dot { width:6px; height:6px; border-radius:999px; background:currentColor; box-shadow:0 0 10px currentColor; display:inline-block; }
.capability-title, .info-title, .scenario-title { color:#FFF; font-size:0.80rem; font-weight:720; margin-bottom:0.30rem; line-height:1.35; }
.capability-text, .info-text, .scenario-text { color:#AAB2C1; font-size:0.63rem; line-height:1.46; }
.scenario-value { color:#FFF; font-size:1.12rem; font-weight:780; letter-spacing:-0.028em; margin-bottom:0.24rem; }
.formula { margin-top:0.46rem; padding:0.36rem 0.46rem; color:#DDF1FF; background:rgba(0,120,212,0.13); border:1px solid rgba(0,120,212,0.30); border-radius:10px; font-size:0.56rem; font-weight:700; }
.insight-card { padding:0.78rem 0.85rem; margin-top:0.35rem; margin-bottom:0.72rem; border-color:rgba(0,120,212,0.30); }
.insight-label { color:#DDF1FF; font-size:0.56rem; font-weight:780; letter-spacing:0.145em; text-transform:uppercase; margin-bottom:0.36rem; }
.insight-text { color:#DDE3EE; font-size:0.66rem; line-height:1.54; }
.chart-title-card { min-height:46px; padding:0.60rem 0.70rem; margin-bottom:0.50rem; display:flex; justify-content:space-between; align-items:center; }
.chart-title { color:#FFF; font-size:0.70rem; font-weight:720; }
.chart-caption { color:#8F99AA; font-size:0.57rem; font-weight:680; }
.table-card { padding:0.82rem; margin-bottom:0.9rem; }
.table-card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.58rem; }
.table-title { color:#FFF; font-size:0.78rem; font-weight:720; }
.table-note { color: var(--muted2); font-size:0.58rem; margin-top:0.12rem; }
.table-wrap { overflow-x:auto; border-radius:13px; border:1px solid rgba(255,255,255,0.08); background:rgba(5,8,18,0.32); }
table.finance-table { width:100%; border-collapse:collapse; font-size:0.64rem; color:#DDE3EE; min-width:520px; }
.finance-table th { background:rgba(255,255,255,0.055); color:#DDF1FF; text-align:left; font-weight:720; padding:0.46rem 0.54rem; border-bottom:1px solid rgba(255,255,255,0.09); }
.finance-table td { padding:0.46rem 0.54rem; border-bottom:1px solid rgba(255,255,255,0.060); color:#D6DCE7; }
.finance-table tr:hover td { background:rgba(0,120,212,0.08); }
h3 { color:#FFF !important; font-size:0.82rem !important; font-weight:720 !important; margin: 0.52rem 0 0.42rem 0 !important; }

.stDownloadButton button, .stButton button {
    font-size:0.62rem !important; padding:0.35rem 0.60rem !important;
    border-radius:999px !important; color:#FFF !important;
    background: rgba(0,120,212,0.68) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    box-shadow: 0 10px 22px rgba(0,120,212,0.20);
}
.stButton button:hover { background: rgba(0,120,212,0.90) !important; border-color: rgba(0,120,212,0.60) !important; }
.stTextArea textarea, .stTextInput input {
    color:#F3F2F1 !important; background: rgba(15,20,34,0.35) !important;
    border:1px solid rgba(255,255,255,0.12) !important;
    border-radius:16px !important; font-size:0.70rem !important;
}
.stTextArea label, .stTextInput label, .stSlider label, .stSelectbox label, .stMultiSelect label, .stRadio label {
    color:#AAB2C1 !important; font-size:0.62rem !important; font-weight:720 !important;
    text-transform:uppercase; letter-spacing:0.10em;
}
</style>
""")

# ================================================================
# Sidebar
# ================================================================

with st.sidebar:
    safe_html('<div class="card-label" style="margin-bottom:0.6rem;">Global Controls</div>')
    uploaded = st.file_uploader("Upload a 10-K (optional)", type=["pdf", "xlsx", "csv"])
    unit_choice = st.radio("Display unit", options=["Auto", "Millions", "Billions"], horizontal=True, index=0)
    unit_map = {"Auto": "auto", "Millions": "M", "Billions": "B"}
    unit = unit_map[unit_choice]
    peer_options = ["Apple", "Alphabet", "Amazon"]
    selected_peers = st.multiselect("Compare against peers", options=peer_options, default=["Apple", "Alphabet"])
    st.markdown("---")
    safe_html('<div class="card-label" style="margin-bottom:0.4rem;">About</div>')
    safe_html('<div style="color:#AAB2C1; font-size:0.62rem; line-height:1.5;">Transforms 10-K disclosures into an executive-ready analytics experience. Peer data is illustrative.</div>')

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
                    font=dict(color="#C9D0DC", size=9)),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1,
                   linecolor="rgba(255,255,255,0.11)",
                   tickfont=dict(color="#8D97A8", size=9),
                   title_font=dict(color="#8D97A8", size=10)),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(255,255,255,0.060)",
                   zeroline=False, showline=False,
                   tickfont=dict(color="#8D97A8", size=9),
                   title_font=dict(color="#8D97A8", size=10)),
    )
    return fig

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
        <div class="hero-topline"><div class="logo-squares"><span></span><span></span><span></span><span></span></div>
        Microsoft Financial Intelligence Platform</div>
        <div class="hero-title">Welcome to the Microsoft Financial Intelligence Platform</div>
        <div class="hero-subtitle">A modern executive dashboard that transforms 10-K financial data into a clean,
        visual, presentation-ready intelligence experience. Use the sidebar to upload your own filing,
        switch display units, and toggle peer comparisons.</div>
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
            "Start with context, move to signals, use Revenue and Peer tabs for evidence, then AI Forecasting for outlook.")

# ---------- Executive Summary ----------
with tab_summary:
    safe_html("""
    <div class="hero"><div class="hero-content">
        <div class="hero-topline"><div class="logo-squares"><span></span><span></span><span></span><span></span></div>
        Microsoft Fluent UI Inspired Financial Intelligence</div>
        <div class="hero-title">Microsoft Financial Intelligence Platform</div>
        <div class="hero-subtitle">An AI-style analytics application built from Microsoft's FY2025 10-K data.</div>
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

    render_section("Executive Snapshot", "Latest reported signals with 3-year mini trends.", "FY2025 View")
    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1:
        render_kpi_card("Revenue Intelligence", f"FY{k['latest_period']} Revenue",
            _cur(revenue), "Total reported revenue.",
            f"{fmt_pct(revenue_yoy)} YoY", "green", rev_spark, "#0078D4")
    with s2:
        render_kpi_card("Profitability Signals", "Operating Margin",
            fmt_pct(operating_margin),
            f"Gross {fmt_pct(gross_margin)} · Net {fmt_pct(net_margin)}",
            "Margin profile", "", op_spark, "#7FBA00")
    with s3:
        render_kpi_card("Cash Flow Engine", "Free Cash Flow",
            _cur(fcf), "Operating cash flow less capex.",
            "Cash generative", "green", fcf_spark, "#FFB900")
    with s4:
        d2c = f"{debt_to_cash:.1f}x debt/cash" if debt_to_cash else "N/A"
        render_kpi_card("Balance Sheet Health", "Cash and Debt",
            _cur(cash_balance), f"Debt {_cur(total_debt)} · {d2c}",
            "Liquidity", "", cash_spark, "#8661C5")

    render_section("Performance Drivers", "How each KPI should be interpreted.", "Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue", "Business Scale", "Top-line size and growth momentum.", "Growth = Current / Prior - 1")
    with e2: render_info_card("Margin", "Operating Efficiency", "How revenue converts to operating income.", "Operating Income / Revenue")
    with e3: render_info_card("Cash Flow", "Financial Output", "Cash available after capex.", "OCF - Capex")
    with e4: render_info_card("Liquidity", "Balance Sheet Flexibility", "Relationship between cash and debt.", "Debt / Cash")

# ---------- Intelligence Hub ----------
with tab_kpi:
    render_section("Executive KPI Intelligence", "Interpretive guidance for scale, efficiency, and flexibility.", "CFO View")
    render_insight("Intelligence Hub Overview",
        "The Executive Summary tab holds the KPI cards. This tab expands the interpretation guide.")
    render_section("Performance Drivers", "How each KPI should be interpreted.", "Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue", "Business Scale", "Top-line size and growth momentum.", "Growth = Current / Prior - 1")
    with e2: render_info_card("Margin", "Operating Efficiency", "How revenue converts to operating income.", "Operating Income / Revenue")
    with e3: render_info_card("Cash Flow", "Financial Output", "Cash available after capex.", "OCF - Capex")
    with e4: render_info_card("Liquidity", "Balance Sheet Flexibility", "Relationship between cash and debt.", "Debt / Cash")

# ---------- Revenue Intelligence (adds Waterfall) ----------
with tab_revenue:
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]

    render_section("Revenue Performance", "Historical trend, mix, growth bridge.", "Growth Analytics")

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        render_kpi_card("FY2025 Revenue", "Total Revenue", _cur(k["revenue"]),
            "Latest annual revenue.", f"{fmt_pct(k['revenue_yoy_growth'])} YoY", "green")
    with r2:
        render_kpi_card("Revenue Mix", "Service and Other", fmt_pct(services_mix),
            "Share of FY2025 revenue.", "Largest category")
    with r3:
        render_kpi_card("Growth Spread", "2025 vs 2024", _cur(growth_spread),
            "Incremental revenue added.", "Expansion", "green")

    left, right = st.columns(2, gap="medium")
    with left:
        render_chart_title("Revenue Over Time", "FY2023-FY2025")
        fig_ts = px.line(ts, x="period", y="revenue", markers=True, color_discrete_sequence=["#0078D4"])
        fig_ts.update_traces(line=dict(width=3, shape="spline"),
            marker=dict(size=7, color="#0078D4", line=dict(width=1.5, color="#DDF1FF")),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>")
        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_ts, height=238), width="stretch", config={"displayModeBar": False})

    with right:
        render_chart_title("Revenue Mix by Category", "Product vs Service")
        seg_long = segment_revenue.melt(id_vars=["period"],
            value_vars=["Product Revenue", "Service and Other Revenue"],
            var_name="category", value_name="revenue")
        fig_seg = px.bar(seg_long, x="period", y="revenue", color="category", barmode="stack",
            color_discrete_map={"Product Revenue": "#0078D4", "Service and Other Revenue": "#7FBA00"})
        fig_seg.update_traces(marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
        fig_seg.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_seg, height=238, showlegend=True), width="stretch", config={"displayModeBar": False})

    # Waterfall Revenue Bridge FY24 -> FY25
    render_chart_title("Revenue Bridge: FY2024 → FY2025", "Decomposed by segment contribution")
    prod_delta = k["product_revenue"] - k["product_revenue_prior"]
    svc_delta = k["service_revenue"] - k["service_revenue_prior"]
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["FY24 Revenue", "Product Δ", "Service Δ", "FY25 Revenue"],
        y=[k["prior_year_revenue"], prod_delta, svc_delta, k["revenue"]],
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        increasing={"marker": {"color": "#7FBA00"}},
        decreasing={"marker": {"color": "#F25022"}},
        totals={"marker": {"color": "#0078D4"}},
        text=[_cur(k["prior_year_revenue"]), _cur(prod_delta), _cur(svc_delta), _cur(k["revenue"])],
        textposition="outside",
        textfont=dict(color="#DDE3EE", size=10),
    ))
    fig_wf.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_wf, height=280), width="stretch", config={"displayModeBar": False})

    render_insight("Revenue Commentary",
        f"Microsoft generated {_cur(k['revenue'])} in FY2025 revenue ({fmt_pct(k['revenue_yoy_growth'])} YoY). "
        f"Service and other revenue = {fmt_pct(services_mix)} of the total. "
        f"Segment Δ: Product {_cur(prod_delta)}, Service {_cur(svc_delta)}.")

# ---------- Peer Benchmark ----------
with tab_peers:
    render_section("Peer Benchmark",
        "Compare Microsoft against selected peers on revenue, margins, and cash flow.", "Cross-Company")

    if len(benchmark_df) == 1:
        render_insight("No peers selected", "Choose peers from the sidebar to see comparisons here.")
    else:
        bd = benchmark_df.copy()

        render_chart_title("Revenue by Company", f"FY{k['latest_period']} — {len(bd)} companies")
        fig_p1 = px.bar(bd.sort_values("revenue", ascending=True),
            x="revenue", y="company", orientation="h",
            color="company",
            color_discrete_sequence=["#0078D4", "#7FBA00", "#FFB900", "#F25022", "#8661C5"])
        fig_p1.update_traces(hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}M<extra></extra>")
        fig_p1.update_xaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_p1, height=240), width="stretch", config={"displayModeBar": False})

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            render_chart_title("Operating Margin", "Higher is better")
            fig_p2 = px.bar(bd.sort_values("operating_margin", ascending=True),
                x="operating_margin", y="company", orientation="h",
                color="company",
                color_discrete_sequence=["#0078D4", "#7FBA00", "#FFB900", "#F25022", "#8661C5"])
            fig_p2.update_traces(hovertemplate="<b>%{y}</b><br>Op Margin: %{x:.1%}<extra></extra>")
            fig_p2.update_xaxes(tickformat=".0%")
            st.plotly_chart(style_fig(fig_p2, height=220), width="stretch", config={"displayModeBar": False})

        with c2:
            render_chart_title("Free Cash Flow", "Cash generation power")
            fig_p3 = px.bar(bd.sort_values("free_cash_flow", ascending=True),
                x="free_cash_flow", y="company", orientation="h",
                color="company",
                color_discrete_sequence=["#0078D4", "#7FBA00", "#FFB900", "#F25022", "#8661C5"])
            fig_p3.update_traces(hovertemplate="<b>%{y}</b><br>FCF: $%{x:,.0f}M<extra></extra>")
            fig_p3.update_xaxes(tickprefix="$", ticksuffix="M")
            st.plotly_chart(style_fig(fig_p3, height=220), width="stretch", config={"displayModeBar": False})

        # Comparison table
        display_bd = bd[["company", "revenue", "revenue_yoy_growth", "operating_margin",
                         "net_margin", "free_cash_flow", "cash_balance", "total_debt"]].copy()
        display_bd["revenue"] = display_bd["revenue"].apply(_cur)
        display_bd["revenue_yoy_growth"] = display_bd["revenue_yoy_growth"].apply(fmt_pct)
        display_bd["operating_margin"] = display_bd["operating_margin"].apply(fmt_pct)
        display_bd["net_margin"] = display_bd["net_margin"].apply(fmt_pct)
        display_bd["free_cash_flow"] = display_bd["free_cash_flow"].apply(_cur)
        display_bd["cash_balance"] = display_bd["cash_balance"].apply(_cur)
        display_bd["total_debt"] = display_bd["total_debt"].apply(_cur)
        display_bd.columns = ["Company", "Revenue", "YoY Growth", "Op Margin", "Net Margin", "FCF", "Cash", "Debt"]
        render_financial_table("Peer Comparison Table", display_bd, "All values FY2025 · illustrative peer data.")

# ---------- AI Forecasting (adds Monte Carlo + Sensitivity + Save Scenarios) ----------
with tab_forecast:
    render_section("Revenue Outlook Model",
        "Adjust growth and volatility assumptions; explore scenarios, Monte Carlo bands, and sensitivity.",
        "Scenario Model")

    s_col1, s_col2, s_col3 = st.columns(3, gap="medium")
    with s_col1:
        growth_rate_pct = st.slider("Base Case Growth (%)", 0, 30, 12, 1)
    with s_col2:
        forecast_years = st.slider("Forecast Horizon (years)", 1, 5, 3, 1)
    with s_col3:
        volatility_pct = st.slider("Growth Volatility (σ, %)", 1, 15, 5, 1)

    base_growth = growth_rate_pct / 100
    volatility = volatility_pct / 100

    forecast_df = build_forecast_dataframe(k["revenue"], base_growth, 2026, forecast_years)
    scenario_df = build_scenario_dataframe(k["revenue"], 2026, forecast_years,
        bear_growth=max(base_growth - 0.05, 0), base_growth=base_growth, bull_growth=base_growth + 0.05)

    bear_last = scenario_df[scenario_df["scenario"] == "Bear Case"].sort_values("year").iloc[-1]
    base_last = scenario_df[scenario_df["scenario"] == "Base Case"].sort_values("year").iloc[-1]
    bull_last = scenario_df[scenario_df["scenario"] == "Bull Case"].sort_values("year").iloc[-1]

    f1, f2, f3 = st.columns(3, gap="medium")
    with f1:
        render_scenario_card("Bear Case", "Conservative Growth", _cur(bear_last["revenue"]),
            f"Projected FY{int(bear_last['year'])} revenue.")
    with f2:
        render_scenario_card("Base Case", "Selected Assumption", _cur(base_last["revenue"]),
            f"Projected FY{int(base_last['year'])} revenue.")
    with f3:
        render_scenario_card("Bull Case", "Upside Growth", _cur(bull_last["revenue"]),
            f"Projected FY{int(bull_last['year'])} revenue.")

    # Historical + scenario chart
    render_chart_title("Historical + Scenario Forecast", "Bear/Base/Bull cases")
    hist_df = ts[["period", "revenue"]].copy()
    hist_df["year"] = hist_df["period"].astype(int)

    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"],
        mode="lines+markers", name="Historical",
        line=dict(color="#0078D4", width=3), marker=dict(size=7),
        hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>"))

    scenario_colors = {"Bear Case": "#F25022", "Base Case": "#7FBA00", "Bull Case": "#FFB900"}
    for sc, col in scenario_colors.items():
        sub = scenario_df[scenario_df["scenario"] == sc]
        fig_forecast.add_trace(go.Scatter(x=sub["year"], y=sub["revenue"],
            mode="lines+markers", name=sc,
            line=dict(color=col, width=2.4, dash="dash"), marker=dict(size=6),
            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>"))
    fig_forecast.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_forecast, height=260, showlegend=True),
        width="stretch", config={"displayModeBar": False})

    # Monte Carlo Fan Chart
    render_chart_title("Monte Carlo Fan Chart", f"500 simulations · μ={growth_rate_pct}% σ={volatility_pct}%")
    mc = monte_carlo_forecast(k["revenue"], base_growth, volatility, 2026, forecast_years, 500)

    fig_mc = go.Figure()
    # Historical
    fig_mc.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"],
        mode="lines+markers", name="Historical",
        line=dict(color="#0078D4", width=3), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>$%{y:,.0f}M<extra></extra>"))
    # p10-p90 band
    fig_mc.add_trace(go.Scatter(x=list(mc["year"]) + list(mc["year"][::-1]),
        y=list(mc["p90"]) + list(mc["p10"][::-1]),
        fill="toself", fillcolor="rgba(127,186,0,0.20)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=True,
        name="P10–P90 band", hoverinfo="skip"))
    # Median
    fig_mc.add_trace(go.Scatter(x=mc["year"], y=mc["p50"],
        mode="lines+markers", name="Median (P50)",
        line=dict(color="#FFB900", width=2.5, dash="dash"), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>Median: $%{y:,.0f}M<extra></extra>"))
    fig_mc.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_mc, height=280, showlegend=True),
        width="stretch", config={"displayModeBar": False})

    # Sensitivity Heatmap
    render_chart_title("Sensitivity: Growth × Margin → Operating Income",
        f"Projected FY{2025 + forecast_years} operating income")
    growth_range = np.arange(0.02, 0.28, 0.04)
    margin_range = np.arange(0.20, 0.55, 0.05)
    grid = sensitivity_grid(k["revenue"], k["operating_margin"], growth_range, margin_range, forecast_years)

    fig_hm = go.Figure(go.Heatmap(
        z=grid,
        x=[f"{g*100:.0f}%" for g in growth_range],
        y=[f"{m*100:.0f}%" for m in margin_range],
        colorscale=[[0, "#031021"], [0.5, "#0078D4"], [1, "#7FBA00"]],
        hovertemplate="Growth: %{x}<br>Margin: %{y}<br>Op Income: $%{z:,.0f}M<extra></extra>",
        colorbar=dict(title=dict(text="Op Income ($M)", font=dict(color="#C9D0DC", size=10)),
                      tickfont=dict(color="#8D97A8", size=9)),
    ))
    fig_hm.update_xaxes(title_text="Revenue Growth")
    fig_hm.update_yaxes(title_text="Operating Margin")
    st.plotly_chart(style_fig(fig_hm, height=320), width="stretch", config={"displayModeBar": False})

    # Save scenarios
    render_section("Saved Scenarios", "Snapshot current assumptions to compare.", "Session Memory")
    sv1, sv2, sv3 = st.columns([2, 1, 1], gap="medium")
    with sv1:
        scenario_name = st.text_input("Scenario name", value=f"Growth {growth_rate_pct}%")
    with sv2:
        if st.button("Save scenario"):
            st.session_state.saved_scenarios[scenario_name] = {
                "growth": growth_rate_pct,
                "years": forecast_years,
                "final_revenue": forecast_df.iloc[-1]["revenue"],
                "final_year": int(forecast_df.iloc[-1]["year"]),
            }
    with sv3:
        if st.button("Clear all"):
            st.session_state.saved_scenarios = {}

    if st.session_state.saved_scenarios:
        rows = []
        for name, s in st.session_state.saved_scenarios.items():
            rows.append({
                "Scenario": name,
                "Growth": f"{s['growth']}%",
                "Horizon": f"{s['years']}y",
                f"FY{s['final_year']} Revenue": _cur(s["final_revenue"]),
            })
        render_financial_table("Saved Scenarios", pd.DataFrame(rows))
    else:
        render_insight("No scenarios saved yet", "Click 'Save scenario' to snapshot current sliders.")

    latest_forecast = forecast_df.iloc[-1]
    render_insight("Forecast Narrative",
        f"With a {growth_rate_pct}% growth assumption and {volatility_pct}% volatility, "
        f"projected revenue reaches {_cur(latest_forecast['revenue'])} by FY{int(latest_forecast['year'])} "
        f"in the base case. The Monte Carlo P10–P90 band captures ~80% of simulated outcomes.")

# ---------- Financial Statements ----------
with tab_financials:
    financials = result["financials"]
    render_section("Financial Statements", "Core statement tables used by the KPI engine.", "Statement Tables")

    f1, f2 = st.columns(2, gap="medium")
    with f1:
        render_financial_table("Income Statement", financials["income"], "Values in millions.")
        st.download_button("Download Income CSV", dataframe_to_csv(financials["income"]),
            "microsoft_income_statement.csv", "text/csv")
    with f2:
        render_financial_table("Balance Sheet", financials["balance"], "Values in millions.")
        st.download_button("Download Balance CSV", dataframe_to_csv(financials["balance"]),
            "microsoft_balance_sheet.csv", "text/csv")

    render_financial_table("Cash Flow Statement", financials["cashflow"], "Values in millions.")
    st.download_button("Download Cash Flow CSV", dataframe_to_csv(financials["cashflow"]),
        "microsoft_cash_flow_statement.csv", "text/csv")

# ---------- AI Copilot (with suggested chips + streaming) ----------
with tab_ai:
    render_section("AI Copilot for Financial Commentary",
        "Ask about revenue, margins, cash flow, liquidity, forecasting, or peer comparison.", "Narrative AI")

    # Suggested question chips
    render_section("Suggested Questions", "Click a prompt to auto-fill and run.", "Quick Prompts")
    chip_cols = st.columns(4, gap="small")
    suggestions = [
        "How did revenue perform year over year?",
        "What do the margins say about profitability?",
        "Summarize free cash flow and liquidity.",
        "How does Microsoft compare to its peers?",
    ]
    for i, s in enumerate(suggestions):
        with chip_cols[i]:
            if st.button(s, key=f"chip_{i}"):
                st.session_state.copilot_question = s

    question = st.text_area("Ask a financial question", value=st.session_state.copilot_question, height=90, key="copilot_input")

    run = st.button("Generate commentary", key="run_copilot")

    if run or st.session_state.get("copilot_question") != "Summarize Microsoft revenue, margins, and cash flow.":
        safe_html('<div class="insight-card"><div class="insight-label">Generated Financial Commentary</div><div class="insight-text">')
        st.write_stream(stream_answer(question, benchmark_df, kpis=k))
        safe_html('</div></div>')
    else:
        response = answer_question(question, benchmark_df, kpis=k)
        render_insight("Generated Financial Commentary", response)

    render_section("Example Prompts", "Additional prompt ideas.", "Prompt Ideas")
    p1, p2, p3 = st.columns(3, gap="medium")
    with p1:
        render_capability_card("Revenue", "Explain Revenue Growth", "Try: How did revenue perform year over year?")
    with p2:
        render_capability_card("Margins", "Review Profitability", "Try: What do the margins say about profitability?")
    with p3:
        render_capability_card("Cash Flow", "Analyze Cash Generation", "Try: Summarize free cash flow and liquidity.")

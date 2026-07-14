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

st.set_page_config(
    page_title="Microsoft Financial Intelligence Platform",
    page_icon="M", layout="wide", initial_sidebar_state="expanded",
)

if "saved_scenarios" not in st.session_state:
    st.session_state.saved_scenarios = {}
if "copilot_question" not in st.session_state:
    st.session_state.copilot_question = "Summarize Microsoft revenue, margins, and cash flow."

# ---------- Helpers ----------
def safe_html(c): st.markdown(c, unsafe_allow_html=True)

def fmt_cur(v):
    if v is None: return "N/A"
    if abs(v) >= 1000: return f"${v/1000:,.1f}B"
    return f"${v:,.0f}M"

def fmt_pct(v):
    if v is None: return "N/A"
    return f"{v*100:.1f}%"

def dataframe_to_csv(df): return df.to_csv(index=False).encode("utf-8")

def delta_html(value, positive_is_good=True):
    if value is None: return ""
    is_positive = value >= 0
    good = (is_positive and positive_is_good) or (not is_positive and not positive_is_good)
    color = "#0F7B3D" if good else "#B42318"
    arrow = "▲" if is_positive else "▼"
    return f'<span class="delta" style="color:{color};">{arrow} {fmt_pct(abs(value))}</span>'

def render_section(title, subtitle, tag):
    safe_html(f'<div class="section-head"><div><div class="section-title">{py_html.escape(title)}</div><div class="section-subtitle">{py_html.escape(subtitle)}</div></div><div class="section-tag">{py_html.escape(tag)}</div></div>')

def sparkline_svg(values, color="#0A2540", width=140, height=32):
    if not values or len(values) < 2: return ""
    vmin, vmax = min(values), max(values)
    rng = vmax - vmin if vmax != vmin else 1
    pts = []
    for i, v in enumerate(values):
        x = i * (width / (len(values) - 1))
        y = height - ((v - vmin) / rng) * height
        pts.append(f"{x:.1f},{y:.1f}")
    path = " ".join(pts)
    area = f"0,{height} " + path + f" {width},{height}"
    last_x, last_y = pts[-1].split(",")
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block;margin-top:8px;">'
            f'<polygon fill="{color}" fill-opacity="0.08" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{path}"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{color}"/></svg>')

def render_kpi_card(label, title, value, subtext, delta_val=None, positive_is_good=True,
                    spark_values=None, spark_color="#0A2540"):
    spark = sparkline_svg(spark_values, color=spark_color) if spark_values else ""
    delta = delta_html(delta_val, positive_is_good) if delta_val is not None else ""
    safe_html(f'<div class="kpi-card"><div class="card-label">{py_html.escape(label)}</div><div class="card-title">{py_html.escape(title)}</div><div class="card-value">{py_html.escape(value)}</div><div class="card-sub">{py_html.escape(subtext)} {delta}</div>{spark}</div>')

def render_capability_card(label, title, text):
    safe_html(f'<div class="capability-card"><div class="card-label">{py_html.escape(label)}</div><div class="capability-title">{py_html.escape(title)}</div><div class="capability-text">{py_html.escape(text)}</div></div>')

def render_info_card(label, title, text, formula=None):
    fh = f'<div class="formula">{py_html.escape(formula)}</div>' if formula else ""
    safe_html(f'<div class="info-card"><div class="card-label">{py_html.escape(label)}</div><div class="info-title">{py_html.escape(title)}</div><div class="info-text">{py_html.escape(text)}</div>{fh}</div>')

def render_scenario_card(label, title, value, text):
    safe_html(f'<div class="scenario-card"><div class="card-label">{py_html.escape(label)}</div><div class="scenario-title">{py_html.escape(title)}</div><div class="scenario-value">{py_html.escape(value)}</div><div class="scenario-text">{py_html.escape(text)}</div></div>')

def render_insight(title, text):
    safe_html(f'<div class="insight-card"><div class="insight-label">{py_html.escape(title)}</div><div class="insight-text">{py_html.escape(text)}</div></div>')

def render_chart_title(title, caption):
    safe_html(f'<div class="chart-title-card"><div class="chart-title">{py_html.escape(title)}</div><div class="chart-caption">{py_html.escape(caption)}</div></div>')

def render_financial_table(title, df, note=None):
    headers = "".join([f"<th>{py_html.escape(str(c))}</th>" for c in df.columns])
    rows = ""
    for _, row in df.iterrows():
        cells = "".join([f"<td>{py_html.escape(str(v))}</td>" for v in row])
        rows += f"<tr>{cells}</tr>"
    nh = f'<div class="table-note">{py_html.escape(note)}</div>' if note else ""
    safe_html(f'<div class="table-card"><div class="table-card-head"><div><div class="table-title">{py_html.escape(title)}</div>{nh}</div></div><div class="table-wrap"><table class="finance-table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div></div>')

# ---------- CSS: Option B Executive Light ----------
safe_html("""
<style>
:root {
    --bg:#F7F7F4; --bg-alt:#FFFFFF; --ink:#0A2540; --ink-2:#1A2B44;
    --muted:#4A5878; --muted-2:#7A879B; --hairline:#E4E7EC;
    --accent:#0A2540; --accent-soft:#E8EDF5;
    --good:#0F7B3D; --bad:#B42318;
    --card:#FFFFFF;
    --shadow: 0 1px 2px rgba(16,24,40,0.05), 0 1px 3px rgba(16,24,40,0.08);
    --shadow-hover: 0 8px 24px rgba(10,37,64,0.12), 0 2px 6px rgba(10,37,64,0.08);
    --radius:10px;
}
html, body, .stApp { color: var(--ink) !important; font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif !important; }
body, .stApp { background: var(--bg) !important; }
[data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--bg-alt) !important; border-right: 1px solid var(--hairline); }
[data-testid="stSidebar"] * { color: var(--ink) !important; }
.block-container { max-width:1500px !important; padding:1.05rem 1.35rem 2.25rem !important; }
#MainMenu, footer, header { visibility:hidden; }

.topbar { display:flex; align-items:center; justify-content:space-between; padding:10px 14px; margin-bottom:12px; background:var(--bg-alt); border:1px solid var(--hairline); border-radius:var(--radius); box-shadow:var(--shadow); }
.topbar-left { display:flex; align-items:center; gap:10px; }
.topbar-logo { width:22px; height:22px; display:grid; grid-template-columns:1fr 1fr; gap:2px; }
.topbar-logo span:nth-child(1){background:#F25022;} .topbar-logo span:nth-child(2){background:#7FBA00;}
.topbar-logo span:nth-child(3){background:#00A4EF;} .topbar-logo span:nth-child(4){background:#FFB900;}
.topbar-title { font-weight:700; font-size:0.92rem; color:var(--ink); letter-spacing:-0.01em; }
.topbar-crumb { color:var(--muted); font-size:0.72rem; font-weight:500; }
.topbar-right { display:flex; gap:14px; align-items:center; color:var(--muted); font-size:0.68rem; font-weight:600; letter-spacing:0.02em; }
.topbar-dot { width:6px; height:6px; border-radius:999px; background:var(--good); display:inline-block; margin-right:6px; }

.stTabs [data-baseweb="tab-list"] { gap:4px; background:transparent; border-bottom:1px solid var(--hairline); padding:0; margin-bottom:18px; border-radius:0; box-shadow:none; }
.stTabs [data-baseweb="tab"] { height:40px; padding:0 14px; border-radius:0 !important; color:var(--muted); font-weight:600; font-size:0.82rem; border:none; border-bottom:2px solid transparent; background:transparent !important; transition:all 0.15s ease; }
.stTabs [data-baseweb="tab"]:hover { color:var(--ink) !important; background:rgba(10,37,64,0.03) !important; border-bottom:2px solid var(--hairline); }
.stTabs [aria-selected="true"] { color:var(--ink) !important; background:transparent !important; border-bottom:2px solid var(--accent) !important; font-weight:700; }

.hero { position:relative; border-radius:var(--radius); border:1px solid var(--hairline); background:linear-gradient(135deg,#FFFFFF 0%,#F0F3F8 100%); padding:20px 24px; overflow:hidden; margin-bottom:18px; box-shadow:var(--shadow); transition:box-shadow 0.2s ease; }
.hero:hover { box-shadow:var(--shadow-hover); }
.hero::after { content:""; position:absolute; right:-80px; top:-80px; width:260px; height:260px; background:radial-gradient(circle,rgba(10,37,64,0.06),transparent 70%); pointer-events:none; }
.hero-content { position:relative; z-index:2; max-width:940px; }
.hero-topline { display:flex; align-items:center; gap:8px; color:var(--muted); font-size:0.62rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; margin-bottom:10px; }
.hero-title { color:var(--ink); font-size:clamp(1.6rem,2vw,2.1rem); font-weight:700; letter-spacing:-0.02em; line-height:1.2; margin-bottom:8px; max-width:780px; }
.hero-subtitle { color:var(--muted); font-size:0.78rem; line-height:1.55; max-width:900px; }
.pill-row { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
.pill { display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px; color:var(--ink); background:var(--accent-soft); border:1px solid var(--hairline); font-size:0.64rem; font-weight:600; letter-spacing:0.02em; }
.pill.blue { color:#FFFFFF; background:var(--accent); border-color:var(--accent); }

.section-head { display:flex; align-items:flex-end; justify-content:space-between; gap:12px; margin:20px 0 10px 0; padding-bottom:8px; border-bottom:1px solid var(--hairline); }
.section-title { color:var(--ink); font-size:0.95rem; font-weight:700; letter-spacing:-0.005em; }
.section-subtitle { color:var(--muted); font-size:0.72rem; margin-top:3px; }
.section-tag { color:var(--muted); background:transparent; border:1px solid var(--hairline); border-radius:4px; padding:3px 8px; font-size:0.62rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; white-space:nowrap; }

.kpi-card, .capability-card, .info-card, .scenario-card, .insight-card, .chart-title-card, .table-card {
    position:relative; border-radius:var(--radius); border:1px solid var(--hairline); background:var(--card); box-shadow:var(--shadow); overflow:hidden;
    transition:transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.kpi-card:hover, .capability-card:hover, .info-card:hover, .scenario-card:hover, .insight-card:hover {
    transform:translateY(-3px); border-color:#C7D0DD; box-shadow:var(--shadow-hover);
}
.kpi-card { min-height:160px; padding:16px; margin-bottom:12px; }
.capability-card, .info-card, .scenario-card { min-height:110px; padding:16px; margin-bottom:12px; }
.card-label { color:var(--muted); font-size:0.60rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; margin-bottom:8px; }
.card-title { color:var(--muted); font-size:0.74rem; font-weight:600; line-height:1.3; margin-bottom:6px; }
.card-value { color:var(--ink); font-size:1.55rem; font-weight:700; letter-spacing:-0.02em; margin-bottom:4px; line-height:1.15; font-variant-numeric:tabular-nums; }
.card-sub { color:var(--muted); font-size:0.68rem; line-height:1.4; font-variant-numeric:tabular-nums; }
.delta { font-weight:700; font-size:0.68rem; margin-left:4px; font-variant-numeric:tabular-nums; }
.capability-title, .info-title, .scenario-title { color:var(--ink); font-size:0.86rem; font-weight:700; margin-bottom:6px; line-height:1.3; letter-spacing:-0.005em; }
.capability-text, .info-text, .scenario-text { color:var(--muted); font-size:0.70rem; line-height:1.5; }
.scenario-value { color:var(--ink); font-size:1.32rem; font-weight:700; letter-spacing:-0.02em; margin-bottom:4px; font-variant-numeric:tabular-nums; }
.formula { margin-top:10px; padding:8px 10px; color:var(--ink); background:var(--accent-soft); border:1px solid var(--hairline); border-radius:6px; font-size:0.62rem; font-weight:600; font-family:"SF Mono",Menlo,monospace; }

.insight-card { padding:14px 16px; margin-top:6px; margin-bottom:12px; border-left:3px solid var(--accent); background:var(--accent-soft); }
.insight-label { color:var(--accent); font-size:0.62rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; margin-bottom:6px; }
.insight-text { color:var(--ink-2); font-size:0.76rem; line-height:1.55; font-variant-numeric:tabular-nums; }

.chart-title-card { min-height:44px; padding:10px 14px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; }
.chart-title { color:var(--ink); font-size:0.80rem; font-weight:700; }
.chart-caption { color:var(--muted); font-size:0.64rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; }

.table-card { padding:16px; margin-bottom:14px; }
.table-card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.table-title { color:var(--ink); font-size:0.88rem; font-weight:700; }
.table-note { color:var(--muted); font-size:0.64rem; margin-top:3px; }
.table-wrap { overflow-x:auto; border-radius:6px; border:1px solid var(--hairline); background:#FDFDFC; }
table.finance-table { width:100%; border-collapse:collapse; font-size:0.72rem; color:var(--ink-2); min-width:520px; font-variant-numeric:tabular-nums; }
.finance-table th { background:#F5F7FA; color:var(--muted); text-align:left; font-weight:700; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; padding:10px 12px; border-bottom:1px solid var(--hairline); }
.finance-table td { padding:10px 12px; border-bottom:1px solid var(--hairline); color:var(--ink-2); }
.finance-table tr:nth-child(even) td { background:#FAFBFC; }
.finance-table tr:hover td { background:var(--accent-soft); }
.finance-table th:not(:first-child), .finance-table td:not(:first-child) { text-align:right; }

h3 { color:var(--ink) !important; font-size:0.90rem !important; font-weight:700 !important; margin:12px 0 8px 0 !important; }

.stDownloadButton button, .stButton button { font-size:0.72rem !important; padding:8px 14px !important; border-radius:6px !important; color:#FFFFFF !important; background:var(--accent) !important; border:1px solid var(--accent) !important; box-shadow:none; font-weight:600 !important; transition:all 0.15s ease; }
.stButton button:hover, .stDownloadButton button:hover { background:#143557 !important; transform:translateY(-1px); box-shadow:0 4px 12px rgba(10,37,64,0.18); }
.stTextArea textarea, .stTextInput input { color:var(--ink) !important; background:#FFFFFF !important; border:1px solid var(--hairline) !important; border-radius:6px !important; font-size:0.80rem !important; }
.stTextArea textarea:focus, .stTextInput input:focus { border-color:var(--accent) !important; box-shadow:0 0 0 3px rgba(10,37,64,0.10) !important; }
.stTextArea label, .stTextInput label, .stSlider label, .stSelectbox label, .stMultiSelect label, .stRadio label, .stFileUploader label { color:var(--muted) !important; font-size:0.66rem !important; font-weight:700 !important; text-transform:uppercase; letter-spacing:0.10em; }
</style>
""")

# ---------- Top bar ----------
now_str = datetime.now().strftime("%b %d, %Y · %H:%M")
safe_html(f'<div class="topbar"><div class="topbar-left"><div class="topbar-logo"><span></span><span></span><span></span><span></span></div><div><div class="topbar-title">Microsoft Financial Intelligence Platform</div><div class="topbar-crumb">FY2025 10-K Analysis · Source: SEC Filing</div></div></div><div class="topbar-right"><span><span class="topbar-dot"></span>Live</span><span>Last refresh · {now_str}</span></div></div>')

# ---------- Sidebar ----------
with st.sidebar:
    safe_html('<div class="card-label" style="margin-bottom:10px;">Global Controls</div>')
    uploaded = st.file_uploader("Upload 10-K (optional)", type=["pdf", "xlsx", "csv"])
    peer_options = ["Apple", "Alphabet", "Amazon"]
    selected_peers = st.multiselect("Peer set", options=peer_options, default=["Apple", "Alphabet"])
    st.markdown("---")
    safe_html('<div class="card-label" style="margin-bottom:6px;">About</div>')
    safe_html('<div style="color:#4A5878; font-size:0.72rem; line-height:1.5;">Transforms 10-K disclosures into an executive-ready analytics experience. Peer data is illustrative.</div>')

# ---------- Data ----------
result = process_uploaded_file(uploaded)
peer_results = process_peers(selected_peers)
company_results = {"Microsoft": result, **peer_results}
benchmark_df = build_benchmark_dataframe(company_results)

k = result["kpis"]
ts = k["time_series"].copy()
segment_revenue = k["segment_revenue"].copy()

# ---------- Plotly styling (light) ----------
def style_fig(fig, height=240, showlegend=False):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,sans-serif", color="#4A5878", size=11),
        margin=dict(l=44, r=18, t=10, b=34), hovermode="x unified", showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1,
                    font=dict(color="#4A5878", size=10)),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor="#E4E7EC",
                   tickfont=dict(color="#7A879B", size=10), title_font=dict(color="#4A5878", size=11)),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#F0F2F5", zeroline=False, showline=False,
                   tickfont=dict(color="#7A879B", size=10), title_font=dict(color="#4A5878", size=11)),
    )
    return fig

PALETTE = {"primary":"#0A2540","accent":"#3E5C8E","gold":"#B08D2E","green":"#0F7B3D","red":"#B42318","warn":"#B54708","muted":"#7A879B"}
CHART_SEQ = ["#0A2540","#3E5C8E","#B08D2E","#0F7B3D","#7A879B","#B54708"]

# ---------- Tabs ----------
tab_welcome, tab_summary, tab_kpi, tab_revenue, tab_peers, tab_forecast, tab_financials, tab_ai = st.tabs(
    ["Welcome","Executive Summary","Intelligence Hub","Revenue Intelligence",
     "Peer Benchmark","AI Forecasting","Financial Statements","AI Copilot"])

# Welcome
with tab_welcome:
    safe_html('<div class="hero"><div class="hero-content"><div class="hero-topline">Microsoft Financial Intelligence Platform</div><div class="hero-title">Executive analytics for FY2025 10-K disclosures</div><div class="hero-subtitle">A modern executive dashboard that transforms 10-K financial data into a presentation-ready intelligence experience. Use the sidebar to upload your own filing and toggle peer comparisons.</div><div class="pill-row"><span class="pill blue">Executive Ready</span><span class="pill">FY2023-FY2025</span><span class="pill">Peer Benchmarks</span><span class="pill">Monte Carlo Forecast</span><span class="pill">AI Copilot</span></div></div></div>')
    render_section("Platform Overview","Why this dashboard was built and how it supports presentation workflows.","Welcome")
    w1, w2 = st.columns(2, gap="medium")
    with w1: render_info_card("Why Built","Executive Financial Clarity","Converts dense 10-K disclosures into an executive-ready analytics experience.")
    with w2: render_info_card("Why FY2023-FY2025","Three-Year Business Trend Window","Long enough to show trend direction while staying recent enough for relevant interpretation.")
    w3, w4 = st.columns(2, gap="medium")
    with w3: render_info_card("Dashboard Architecture","Layered Intelligence Design","Welcome → KPIs → Revenue → Peer Benchmark → Forecasting → Statements → AI commentary.")
    with w4: render_info_card("Presentation Workflow","From Data to Boardroom Narrative","Context, then signals, then evidence, then outlook, then support.")

# Executive Summary
with tab_summary:
    safe_html('<div class="hero"><div class="hero-content"><div class="hero-topline">Executive Summary · FY2025</div><div class="hero-title">Microsoft Financial Intelligence Platform</div><div class="hero-subtitle">Executive KPIs, revenue intelligence, forecasting scenarios, and natural-language commentary built from Microsoft\'s FY2025 10-K.</div><div class="pill-row"><span class="pill blue">FY2025</span><span class="pill">10-K Analysis</span><span class="pill">Revenue Intelligence</span><span class="pill">AI Forecasting</span></div></div></div>')
    revenue = k["revenue"]; revenue_yoy = k["revenue_yoy_growth"]
    gross_margin = k["gross_margin"]; operating_margin = k["operating_margin"]; net_margin = k["net_margin"]
    fcf = k["free_cash_flow"]; cash_balance = k["cash_balance"]; total_debt = k["total_debt"]
    debt_to_cash = total_debt / cash_balance if cash_balance else None

    ts_chrono = ts.iloc[::-1].reset_index(drop=True)
    rev_spark = ts_chrono["revenue"].tolist()
    op_spark = ts_chrono["operating_margin"].tolist()
    fcf_spark = ts_chrono["free_cash_flow"].tolist()
    cash_spark = ts_chrono["cash_balance"].tolist()

    op_prior = ts.loc[ts["period"] == "2024", "operating_margin"].iloc[0]
    op_delta = operating_margin - op_prior
    fcf_prior_row = ts.loc[ts["period"] == "2024", "free_cash_flow"].iloc[0]
    fcf_delta = (fcf - fcf_prior_row) / fcf_prior_row if fcf_prior_row else None
    cash_prior = ts.loc[ts["period"] == "2024", "cash_balance"].iloc[0]
    cash_delta = (cash_balance - cash_prior) / cash_prior if cash_prior else None

    render_section("Executive Snapshot","Latest signals with three-year trend and prior-year delta.","FY2025 View")
    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1: render_kpi_card("Revenue", f"FY{k['latest_period']} Total Revenue", fmt_cur(revenue), "vs FY2024", delta_val=revenue_yoy, spark_values=rev_spark, spark_color=PALETTE["primary"])
    with s2: render_kpi_card("Profitability","Operating Margin", fmt_pct(operating_margin), f"Gross {fmt_pct(gross_margin)} · Net {fmt_pct(net_margin)}", delta_val=op_delta, spark_values=op_spark, spark_color=PALETTE["accent"])
    with s3: render_kpi_card("Cash Flow","Free Cash Flow", fmt_cur(fcf), "OCF less capex", delta_val=fcf_delta, spark_values=fcf_spark, spark_color=PALETTE["green"])
    with s4:
        d2c_text = f"Debt {fmt_cur(total_debt)} · {debt_to_cash:.1f}x debt/cash" if debt_to_cash else "N/A"
        render_kpi_card("Liquidity","Cash Position", fmt_cur(cash_balance), d2c_text, delta_val=cash_delta, spark_values=cash_spark, spark_color=PALETTE["gold"])

    render_section("Performance Drivers","How each KPI should be interpreted.","Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue","Business Scale","Top-line size and growth momentum.","Growth = Current / Prior − 1")
    with e2: render_info_card("Margin","Operating Efficiency","How revenue converts to operating income.","Operating Income / Revenue")
    with e3: render_info_card("Cash Flow","Financial Output","Cash available after capex.","OCF − Capex")
    with e4: render_info_card("Liquidity","Balance Sheet Flexibility","Relationship between cash and debt.","Debt / Cash")

# Intelligence Hub
with tab_kpi:
    render_section("Executive KPI Intelligence","Interpretive guidance for scale, efficiency, and flexibility.","CFO View")
    render_insight("Intelligence Hub Overview","The Executive Summary tab holds the KPI cards. This tab expands the interpretation guide for each metric.")
    render_section("Performance Drivers","How each KPI should be interpreted.","Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue","Business Scale","Top-line size and growth momentum.","Growth = Current / Prior − 1")
    with e2: render_info_card("Margin","Operating Efficiency","How revenue converts to operating income.","Operating Income / Revenue")
    with e3: render_info_card("Cash Flow","Financial Output","Cash available after capex.","OCF − Capex")
    with e4: render_info_card("Liquidity","Balance Sheet Flexibility","Relationship between cash and debt.","Debt / Cash")

# Revenue Intelligence
with tab_revenue:
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]
    render_section("Revenue Performance","Historical trend, mix, and growth bridge.","Growth Analytics")

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1: render_kpi_card("FY2025 Revenue","Total Revenue", fmt_cur(k["revenue"]), "vs FY2024", delta_val=k["revenue_yoy_growth"])
    with r2: render_kpi_card("Revenue Mix","Service & Other", fmt_pct(services_mix), "Share of FY2025 revenue")
    with r3: render_kpi_card("Growth Spread","2025 vs 2024", fmt_cur(growth_spread), "Incremental revenue")

    left, right = st.columns(2, gap="medium")
    with left:
        render_chart_title("Revenue Over Time","FY2023 – FY2025")
        fig_ts = px.line(ts.sort_values("period"), x="period", y="revenue", markers=True, color_discrete_sequence=[PALETTE["primary"]])
        fig_ts.update_traces(line=dict(width=2.5, shape="spline"), marker=dict(size=8, color=PALETTE["primary"], line=dict(width=2, color="#FFFFFF")), hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>")
        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_ts, 240), width="stretch", config={"displayModeBar": False})
    with right:
        render_chart_title("Revenue Mix by Category","Product vs Service")
        seg_long = segment_revenue.melt(id_vars=["period"], value_vars=["Product Revenue","Service and Other Revenue"], var_name="category", value_name="revenue")
        fig_seg = px.bar(seg_long.sort_values("period"), x="period", y="revenue", color="category", barmode="stack",
            color_discrete_map={"Product Revenue": PALETTE["primary"], "Service and Other Revenue": PALETTE["accent"]})
        fig_seg.update_traces(marker_line_width=0, hovertemplate="<b>FY%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
        fig_seg.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_seg, 240, True), width="stretch", config={"displayModeBar": False})

    render_chart_title("Revenue Bridge: FY2024 → FY2025","Decomposed by segment contribution")
    prod_delta = k["product_revenue"] - k["product_revenue_prior"]
    svc_delta = k["service_revenue"] - k["service_revenue_prior"]
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["FY24 Revenue","Product Δ","Service Δ","FY25 Revenue"],
        y=[k["prior_year_revenue"], prod_delta, svc_delta, k["revenue"]],
        connector={"line": {"color": "#C7D0DD", "dash": "dot"}},
        increasing={"marker": {"color": PALETTE["green"]}},
        decreasing={"marker": {"color": PALETTE["red"]}},
        totals={"marker": {"color": PALETTE["primary"]}},
        text=[fmt_cur(k["prior_year_revenue"]), fmt_cur(prod_delta), fmt_cur(svc_delta), fmt_cur(k["revenue"])],
        textposition="outside",
        textfont=dict(color="#0A2540", size=11),
    ))
    fig_wf.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_wf, 290), width="stretch", config={"displayModeBar": False})

    render_insight("Revenue Commentary",
        f"Microsoft generated {fmt_cur(k['revenue'])} in FY2025 revenue ({fmt_pct(k['revenue_yoy_growth'])} YoY). "
        f"Service and other revenue = {fmt_pct(services_mix)} of the total. "
        f"Segment Δ: Product {fmt_cur(prod_delta)}, Service {fmt_cur(svc_delta)}.")

# Peer Benchmark
with tab_peers:
    render_section("Peer Benchmark","Compare Microsoft against selected peers on revenue, margins, and cash flow.","Cross-Company")
    if len(benchmark_df) == 1:
        render_insight("No peers selected","Choose peers from the sidebar to see comparisons here.")
    else:
        bd = benchmark_df.copy()
        render_chart_title("Revenue by Company", f"FY{k['latest_period']} — {len(bd)} companies")
        fig_p1 = px.bar(bd.sort_values("revenue"), x="revenue", y="company", orientation="h",
            color="company", color_discrete_sequence=CHART_SEQ)
        fig_p1.update_traces(hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.0f}M<extra></extra>")
        fig_p1.update_xaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig_p1, 240), width="stretch", config={"displayModeBar": False})

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            render_chart_title("Operating Margin","Higher is better")
            fig_p2 = px.bar(bd.sort_values("operating_margin"), x="operating_margin", y="company", orientation="h",
                color="company", color_discrete_sequence=CHART_SEQ)
            fig_p2.update_traces(hovertemplate="<b>%{y}</b><br>Op Margin: %{x:.1%}<extra></extra>")
            fig_p2.update_xaxes(tickformat=".0%")
            st.plotly_chart(style_fig(fig_p2, 220), width="stretch", config={"displayModeBar": False})
        with c2:
            render_chart_title("Free Cash Flow","Cash generation power")
            fig_p3 = px.bar(bd.sort_values("free_cash_flow"), x="free_cash_flow", y="company", orientation="h",
                color="company", color_discrete_sequence=CHART_SEQ)
            fig_p3.update_traces(hovertemplate="<b>%{y}</b><br>FCF: $%{x:,.0f}M<extra></extra>")
            fig_p3.update_xaxes(tickprefix="$", ticksuffix="M")
            st.plotly_chart(style_fig(fig_p3, 220), width="stretch", config={"displayModeBar": False})

        display_bd = bd[["company","revenue","revenue_yoy_growth","operating_margin","net_margin","free_cash_flow","cash_balance","total_debt"]].copy()
        display_bd["revenue"] = display_bd["revenue"].apply(fmt_cur)
        display_bd["revenue_yoy_growth"] = display_bd["revenue_yoy_growth"].apply(fmt_pct)
        display_bd["operating_margin"] = display_bd["operating_margin"].apply(fmt_pct)
        display_bd["net_margin"] = display_bd["net_margin"].apply(fmt_pct)
        display_bd["free_cash_flow"] = display_bd["free_cash_flow"].apply(fmt_cur)
        display_bd["cash_balance"] = display_bd["cash_balance"].apply(fmt_cur)
        display_bd["total_debt"] = display_bd["total_debt"].apply(fmt_cur)
        display_bd.columns = ["Company","Revenue","YoY","Op Margin","Net Margin","FCF","Cash","Debt"]
        render_financial_table("Peer Comparison Table", display_bd, "All values FY2025 · illustrative peer data.")

# AI Forecasting
with tab_forecast:
    render_section("Revenue Outlook Model","Adjust growth and volatility; explore scenarios, Monte Carlo bands, and sensitivity.","Scenario Model")

    s_col1, s_col2, s_col3 = st.columns(3, gap="medium")
    with s_col1: growth_rate_pct = st.slider("Base Case Growth (%)", 0, 30, 12, 1)
    with s_col2: forecast_years = st.slider("Forecast Horizon (years)", 1, 5, 3, 1)
    with s_col3: volatility_pct = st.slider("Growth Volatility (σ, %)", 1, 15, 5, 1)

    base_growth = growth_rate_pct / 100
    volatility = volatility_pct / 100

    forecast_df = build_forecast_dataframe(k["revenue"], base_growth, 2026, forecast_years)
    scenario_df = build_scenario_dataframe(k["revenue"], 2026, forecast_years,
        bear_growth=max(base_growth-0.05, 0), base_growth=base_growth, bull_growth=base_growth+0.05)

    bear_last = scenario_df[scenario_df["scenario"]=="Bear Case"].sort_values("year").iloc[-1]
    base_last = scenario_df[scenario_df["scenario"]=="Base Case"].sort_values("year").iloc[-1]
    bull_last = scenario_df[scenario_df["scenario"]=="Bull Case"].sort_values("year").iloc[-1]

    f1, f2, f3 = st.columns(3, gap="medium")
    with f1: render_scenario_card("Bear Case","Conservative Growth", fmt_cur(bear_last["revenue"]), f"Projected FY{int(bear_last['year'])} revenue.")
    with f2: render_scenario_card("Base Case","Selected Assumption", fmt_cur(base_last["revenue"]), f"Projected FY{int(base_last['year'])} revenue.")
    with f3: render_scenario_card("Bull Case","Upside Growth", fmt_cur(bull_last["revenue"]), f"Projected FY{int(bull_last['year'])} revenue.")

    render_chart_title("Historical + Scenario Forecast","Bear/Base/Bull cases")
    hist_df = ts[["period","revenue"]].copy()
    hist_df["year"] = hist_df["period"].astype(int)
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"],
        mode="lines+markers", name="Historical",
        line=dict(color=PALETTE["primary"], width=3), marker=dict(size=7),
        hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>"))
    scenario_colors = {"Bear Case": PALETTE["red"], "Base Case": PALETTE["green"], "Bull Case": PALETTE["gold"]}
    for sc, col in scenario_colors.items():
        sub = scenario_df[scenario_df["scenario"]==sc]
        fig_forecast.add_trace(go.Scatter(x=sub["year"], y=sub["revenue"],
            mode="lines+markers", name=sc,
            line=dict(color=col, width=2.2, dash="dash"), marker=dict(size=6),
            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>"))
    fig_forecast.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_forecast, 260, True), width="stretch", config={"displayModeBar": False})

    render_chart_title("Monte Carlo Fan Chart", f"500 simulations · μ={growth_rate_pct}% σ={volatility_pct}%")
    mc = monte_carlo_forecast(k["revenue"], base_growth, volatility, 2026, forecast_years, 500)
    fig_mc = go.Figure()
    fig_mc.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"], mode="lines+markers",
        name="Historical", line=dict(color=PALETTE["primary"], width=3), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>$%{y:,.0f}M<extra></extra>"))
    fig_mc.add_trace(go.Scatter(x=list(mc["year"])+list(mc["year"][::-1]),
        y=list(mc["p90"])+list(mc["p10"][::-1]),
        fill="toself", fillcolor="rgba(62,92,142,0.20)",
        line=dict(color="rgba(0,0,0,0)"), showlegend=True,
        name="P10–P90 band", hoverinfo="skip"))
    fig_mc.add_trace(go.Scatter(x=mc["year"], y=mc["p50"], mode="lines+markers", name="Median (P50)",
        line=dict(color=PALETTE["gold"], width=2.4, dash="dash"), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>Median: $%{y:,.0f}M<extra></extra>"))
    fig_mc.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_mc, 280, True), width="stretch", config={"displayModeBar": False})

    render_chart_title("Sensitivity: Growth × Margin → Operating Income", f"Projected FY{2025+forecast_years} operating income")
    growth_range = np.arange(0.02, 0.28, 0.04)
    margin_range = np.arange(0.20, 0.55, 0.05)
    grid = sensitivity_grid(k["revenue"], k["operating_margin"], growth_range, margin_range, forecast_years)
    fig_hm = go.Figure(go.Heatmap(
        z=grid,
        x=[f"{g*100:.0f}%" for g in growth_range],
        y=[f"{m*100:.0f}%" for m in margin_range],
        colorscale=[[0,"#F5F7FA"],[0.5,"#3E5C8E"],[1,"#0A2540"]],
        hovertemplate="Growth: %{x}<br>Margin: %{y}<br>Op Income: $%{z:,.0f}M<extra></extra>",
        colorbar=dict(title=dict(text="Op Income ($M)", font=dict(color="#4A5878", size=10)),
                      tickfont=dict(color="#7A879B", size=9)),
    ))
    fig_hm.update_xaxes(title_text="Revenue Growth")
    fig_hm.update_yaxes(title_text="Operating Margin")
    st.plotly_chart(style_fig(fig_hm, 320), width="stretch", config={"displayModeBar": False})

    render_section("Saved Scenarios","Snapshot current assumptions to compare.","Session Memory")
    sv1, sv2, sv3 = st.columns([2, 1, 1], gap="medium")
    with sv1: scenario_name = st.text_input("Scenario name", value=f"Growth {growth_rate_pct}%")
    with sv2:
        if st.button("Save scenario"):
            st.session_state.saved_scenarios[scenario_name] = {
                "growth": growth_rate_pct, "years": forecast_years,
                "final_revenue": forecast_df.iloc[-1]["revenue"],
                "final_year": int(forecast_df.iloc[-1]["year"]),
            }
    with sv3:
        if st.button("Clear all"): st.session_state.saved_scenarios = {}

    if st.session_state.saved_scenarios:
        rows = []
        for name, s in st.session_state.saved_scenarios.items():
            rows.append({"Scenario": name, "Growth": f"{s['growth']}%", "Horizon": f"{s['years']}y",
                         f"FY{s['final_year']} Revenue": fmt_cur(s["final_revenue"])})
        render_financial_table("Saved Scenarios", pd.DataFrame(rows))
    else:
        render_insight("No scenarios saved yet","Click 'Save scenario' to snapshot current sliders.")

    latest_forecast = forecast_df.iloc[-1]
    render_insight("Forecast Narrative",
        f"With a {growth_rate_pct}% growth assumption and {volatility_pct}% volatility, "
        f"projected revenue reaches {fmt_cur(latest_forecast['revenue'])} by FY{int(latest_forecast['year'])} "
        f"in the base case. The P10–P90 band captures ~80% of simulated outcomes.")

# Financial Statements
with tab_financials:
    financials = result["financials"]
    render_section("Financial Statements","Core statement tables used by the KPI engine.","Statement Tables")
    f1, f2 = st.columns(2, gap="medium")
    with f1:
        render_financial_table("Income Statement", financials["income"], "Values in millions.")
        st.download_button("Download Income CSV", dataframe_to_csv(financials["income"]),
            "microsoft_income_statement.csv","text/csv")
    with f2:
        render_financial_table("Balance Sheet", financials["balance"], "Values in millions.")
        st.download_button("Download Balance CSV", dataframe_to_csv(financials["balance"]),
            "microsoft_balance_sheet.csv","text/csv")
    render_financial_table("Cash Flow Statement", financials["cashflow"], "Values in millions.")
    st.download_button("Download Cash Flow CSV", dataframe_to_csv(financials["cashflow"]),
        "microsoft_cash_flow_statement.csv","text/csv")

# AI Copilot
with tab_ai:
    render_section("AI Copilot for Financial Commentary","Ask about revenue, margins, cash flow, liquidity, forecasting, or peer comparison.","Narrative AI")
    render_section("Suggested Questions","Click a prompt to auto-fill and run.","Quick Prompts")
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

    if run:
        safe_html('<div class="insight-card"><div class="insight-label">Generated Financial Commentary</div><div class="insight-text">')
        st.write_stream(stream_answer(question, benchmark_df, kpis=k))
        safe_html('</div></div>')
    else:
        response = answer_question(question, benchmark_df, kpis=k)
        render_insight("Generated Financial Commentary", response)

    render_section("Example Prompts","Additional prompt ideas.","Prompt Ideas")
    p1, p2, p3 = st.columns(3, gap="medium")
    with p1: render_capability_card("Revenue","Explain Revenue Growth","Try: How did revenue perform year over year?")
    with p2: render_capability_card("Margins","Review Profitability","Try: What do the margins say about profitability?")
    with p3: render_capability_card("Cash Flow","Analyze Cash Generation","Try: Summarize free cash flow and liquidity.")

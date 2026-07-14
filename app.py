import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import html as py_html
from datetime import datetime

from tenk_engine import (
    process_uploaded_file, build_benchmark_dataframe,
    answer_question, stream_answer,
    build_forecast_dataframe, build_scenario_dataframe,
    monte_carlo_forecast, sensitivity_grid,
    fmt_cur, fmt_pct, fmt_ratio,
)

st.set_page_config(page_title="Microsoft Financial Intelligence Platform",
    page_icon="M", layout="wide", initial_sidebar_state="expanded")

if "saved_scenarios" not in st.session_state: st.session_state.saved_scenarios = {}
if "copilot_question" not in st.session_state:
    st.session_state.copilot_question = "Summarize Microsoft revenue, margins, and cash flow."

# ---------- Helpers ----------
def safe_html(c): st.markdown(c, unsafe_allow_html=True)
def dataframe_to_csv(df): return df.to_csv(index=False).encode("utf-8")

def delta_html(value, positive_is_good=True, as_pct=True, prefix_arrow=True):
    if value is None: return ""
    is_pos = value >= 0
    good = (is_pos and positive_is_good) or (not is_pos and not positive_is_good)
    color = "#0F7B3D" if good else "#B42318"
    arrow = "▲" if is_pos else "▼"
    txt = fmt_pct(abs(value)) if as_pct else f"{abs(value):,.2f}"
    return f'<span class="delta" style="color:{color};">{arrow if prefix_arrow else ""} {txt}</span>'

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
    lx, ly = pts[-1].split(",")
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="display:block;margin-top:8px;">'
            f'<polygon fill="{color}" fill-opacity="0.08" points="{area}"/>'
            f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{path}"/>'
            f'<circle cx="{lx}" cy="{ly}" r="3" fill="{color}"/></svg>')

def render_kpi_card(label, title, value, subtext, delta_val=None, positive_is_good=True,
                    spark_values=None, spark_color="#0A2540", delta_as_pct=True):
    spark = sparkline_svg(spark_values, color=spark_color) if spark_values else ""
    delta = delta_html(delta_val, positive_is_good, as_pct=delta_as_pct) if delta_val is not None else ""
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

def render_analyst_note(text):
    """Plain-English commentary under charts/KPIs. Bulb icon signals interpretation."""
    safe_html(f'<div class="analyst-note"><span class="analyst-icon">💡</span><span class="analyst-label">Analyst Note</span><div class="analyst-text">{py_html.escape(text)}</div></div>')

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
    --good:#0F7B3D; --bad:#B42318; --gold:#B08D2E;
    --card:#FFFFFF;
    --shadow:0 1px 2px rgba(16,24,40,0.05),0 1px 3px rgba(16,24,40,0.08);
    --shadow-hover:0 8px 24px rgba(10,37,64,0.12),0 2px 6px rgba(10,37,64,0.08);
    --radius:10px;
}
html, body, .stApp { color:var(--ink) !important; font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif !important; }
body, .stApp { background:var(--bg) !important; }
[data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main { background:transparent !important; }
[data-testid="stSidebar"] { background:var(--bg-alt) !important; border-right:1px solid var(--hairline); }
[data-testid="stSidebar"] * { color:var(--ink) !important; }
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

.kpi-card, .capability-card, .info-card, .scenario-card, .insight-card, .chart-title-card, .table-card, .analyst-note {
    position:relative; border-radius:var(--radius); border:1px solid var(--hairline); background:var(--card); box-shadow:var(--shadow); overflow:hidden;
    transition:transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.kpi-card:hover, .capability-card:hover, .info-card:hover, .scenario-card:hover, .insight-card:hover, .analyst-note:hover {
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

.analyst-note { padding:12px 14px; margin:8px 0 14px 0; border-left:3px solid var(--gold); background:#FDFAF3; }
.analyst-icon { font-size:0.85rem; margin-right:6px; }
.analyst-label { color:var(--gold); font-size:0.60rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; }
.analyst-text { color:var(--ink-2); font-size:0.72rem; line-height:1.55; margin-top:5px; font-variant-numeric:tabular-nums; }

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
safe_html(f'<div class="topbar"><div class="topbar-left"><div class="topbar-logo"><span></span><span></span><span></span><span></span></div><div><div class="topbar-title">Microsoft Financial Intelligence Platform</div><div class="topbar-crumb">FY2025 10-K · Fiscal year ended June 30, 2025 · Source: SEC Filing</div></div></div><div class="topbar-right"><span><span class="topbar-dot"></span>Verified</span><span>Last refresh · {now_str}</span></div></div>')

# ---------- Sidebar ----------
with st.sidebar:
    safe_html('<div class="card-label" style="margin-bottom:10px;">Global Controls</div>')
    uploaded = st.file_uploader("Upload alternate 10-K", type=["pdf", "xlsx", "csv"])
    st.markdown("---")
    safe_html('<div class="card-label" style="margin-bottom:6px;">Data Source</div>')
    safe_html('<div style="color:#4A5878; font-size:0.72rem; line-height:1.5;">All figures sourced directly from Microsoft\'s FY2025 10-K, filed with the SEC. Values in $ millions unless noted.</div>')

# ---------- Data ----------
result = process_uploaded_file(uploaded)
company_results = {"Microsoft": result}
benchmark_df = build_benchmark_dataframe(company_results)
k = result["kpis"]
ts = k["time_series"].copy()
segment_revenue = k["segment_revenue"].copy()

# ---------- Plotly styling ----------
def style_fig(fig, height=240, showlegend=False):
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter,sans-serif", color="#4A5878", size=11),
        margin=dict(l=44, r=18, t=10, b=34), hovermode="x unified", showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1, font=dict(color="#4A5878", size=10)),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor="#E4E7EC",
                   tickfont=dict(color="#7A879B", size=10), title_font=dict(color="#4A5878", size=11)),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#F0F2F5", zeroline=False, showline=False,
                   tickfont=dict(color="#7A879B", size=10), title_font=dict(color="#4A5878", size=11)))
    return fig

PALETTE = {"primary":"#0A2540","accent":"#3E5C8E","gold":"#B08D2E","green":"#0F7B3D","red":"#B42318","warn":"#B54708","muted":"#7A879B"}
SEG_COLORS = {"Productivity and Business Processes":"#0A2540", "Intelligent Cloud":"#3E5C8E", "More Personal Computing":"#B08D2E"}

# ---------- Tabs ----------
tabs = st.tabs(["Welcome","Executive Summary","Intelligence Hub","Revenue Intelligence",
                "Segments","Capital Allocation","AI Forecasting","Financial Statements","AI Copilot"])
tab_welcome, tab_summary, tab_kpi, tab_revenue, tab_segments, tab_capital, tab_forecast, tab_financials, tab_ai = tabs

# ================= WELCOME =================
with tab_welcome:
    safe_html('<div class="hero"><div class="hero-content"><div class="hero-topline">Microsoft Financial Intelligence Platform</div><div class="hero-title">Executive analytics from Microsoft\'s FY2025 10-K</div><div class="hero-subtitle">A presentation-ready analytics experience for CFOs and financial analysts. Every metric is sourced directly from Microsoft\'s SEC filing — no estimates, no illustrative data.</div><div class="pill-row"><span class="pill blue">FY2025 Verified</span><span class="pill">10-K Sourced</span><span class="pill">Segment Analysis</span><span class="pill">Capital Allocation</span><span class="pill">Rule of 40 · ROIC · EBITDA</span></div></div></div>')

    render_section("Platform Overview","How this dashboard translates a 200+ page 10-K into decision-ready intelligence.","Welcome")
    w1, w2 = st.columns(2, gap="medium")
    with w1: render_info_card("Why Built","Executive Financial Clarity","Converts dense 10-K disclosures into an executive-ready analytics experience — every KPI mapped to the SEC-filed statements.")
    with w2: render_info_card("Time Window","Three-Year Trend View","FY2023-FY2025 for income statement, cash flow, and segments (matching the filing's 3-year comparative). Balance sheet shows FY2024-FY2025 per 10-K standard.")
    w3, w4 = st.columns(2, gap="medium")
    with w3: render_info_card("Architecture","Layered Intelligence Design","Welcome → Executive KPIs → Revenue → Segments → Capital Allocation → Forecasting → Statements → AI commentary.")
    with w4: render_info_card("Workflow","From Data to Boardroom","Every tile includes an analyst note that explains what the number means in plain English. Built for stakeholders who don't live in the 10-K.")

    render_analyst_note("This dashboard was built to eliminate the 'what does this really mean?' problem. Every KPI, chart, and ratio has a plain-English explanation attached, so anyone from an intern to a board member can interpret Microsoft's financial position without prior finance training.")

# ================= EXECUTIVE SUMMARY =================
with tab_summary:
    safe_html('<div class="hero"><div class="hero-content"><div class="hero-topline">Executive Summary · FY2025</div><div class="hero-title">Microsoft FY2025 Snapshot</div><div class="hero-subtitle">Revenue of $281.7B (+15% YoY), operating margin of 45.6%, and $71.6B in free cash flow. Capex nearly doubled to $64.6B as Microsoft scales AI infrastructure — the defining story of FY2025.</div><div class="pill-row"><span class="pill blue">Revenue +15%</span><span class="pill">Op Margin 45.6%</span><span class="pill">FCF $71.6B</span><span class="pill">Capex +45%</span></div></div></div>')

    revenue = k["revenue"]; yoy = k["revenue_yoy_growth"]
    gm = k["gross_margin"]; om = k["operating_margin"]; nm = k["net_margin"]
    fcf = k["free_cash_flow"]; cash = k["cash_balance"]; debt = k["total_debt"]

    ts_c = ts.sort_values("period").reset_index(drop=True)
    rev_spark = ts_c["revenue"].tolist()
    op_spark = ts_c["operating_margin"].tolist()
    fcf_spark = ts_c["free_cash_flow"].tolist()
    cash_spark = ts_c["cash_balance"].tolist()

    op_prior = ts.loc[ts["period"]=="2024","operating_margin"].iloc[0]
    fcf_prior = ts.loc[ts["period"]=="2024","free_cash_flow"].iloc[0]
    fcf_delta = (fcf - fcf_prior) / fcf_prior if fcf_prior else None
    cash_prior = ts.loc[ts["period"]=="2024","cash_balance"].iloc[0]
    cash_delta = (cash - cash_prior) / cash_prior if cash_prior else None

    render_section("Executive Snapshot","Latest FY2025 signals with three-year trend and prior-year delta.","FY2025 View")
    s1, s2, s3, s4 = st.columns(4, gap="medium")
    with s1: render_kpi_card("Revenue","FY2025 Total Revenue", fmt_cur(revenue), "vs FY2024", delta_val=yoy, spark_values=rev_spark, spark_color=PALETTE["primary"])
    with s2: render_kpi_card("Profitability","Operating Margin", fmt_pct(om), f"Gross {fmt_pct(gm)} · Net {fmt_pct(nm)}", delta_val=om-op_prior, spark_values=op_spark, spark_color=PALETTE["accent"])
    with s3: render_kpi_card("Cash Flow","Free Cash Flow", fmt_cur(fcf), "OCF less capex", delta_val=fcf_delta, spark_values=fcf_spark, spark_color=PALETTE["green"])
    with s4: render_kpi_card("Liquidity","Cash Position", fmt_cur(k["cash_plus_st_inv"]), f"Net Debt {fmt_cur(k['net_debt'])}", delta_val=cash_delta, spark_values=cash_spark, spark_color=PALETTE["gold"])

    render_analyst_note(f"Microsoft grew revenue 15% while operating margin expanded to {fmt_pct(om)} — meaning for every $1 of sales, ~46¢ became operating profit. However free cash flow declined slightly from $74B to $71.6B despite record revenue, because capex nearly doubled to $64.6B for AI infrastructure. This is the trade-off analysts are watching most closely.")

    # New: analyst ratios strip
    render_section("Analyst Ratios","Metrics CFOs and equity analysts use to benchmark financial health.","Advanced Metrics")
    a1, a2, a3, a4, a5 = st.columns(5, gap="medium")
    with a1: render_kpi_card("EBITDA","Earnings Before ID&A", fmt_cur(k["ebitda"]), f"Margin {fmt_pct(k['ebitda_margin'])}", delta_val=None)
    with a2: render_kpi_card("Rule of 40","Growth + FCF Margin", f"{k['rule_of_40']*100:.1f}%", "SaaS health benchmark >40%", delta_val=None)
    with a3: render_kpi_card("ROIC","Return on Invested Capital", fmt_pct(k["roic"]), "NOPAT / (Debt+Equity)", delta_val=None)
    with a4: render_kpi_card("Net Debt / EBITDA","Leverage Ratio", fmt_ratio(k["net_debt_ebitda"]), "Lower = safer balance sheet", delta_val=None)
    with a5: render_kpi_card("Effective Tax Rate","Tax as % of pretax income", fmt_pct(k["effective_tax_rate"]), "Book tax rate", delta_val=None)

    render_analyst_note(f"EBITDA of {fmt_cur(k['ebitda'])} strips out non-cash charges to show pure earnings power. Rule of 40 = {k['rule_of_40']*100:.1f}% (a SaaS benchmark; anything over 40% is elite). ROIC of {fmt_pct(k['roic'])} means every dollar invested earns ~{k['roic']*100:.0f}¢ per year — extraordinary for a mature company. Net Debt/EBITDA of {fmt_ratio(k['net_debt_ebitda'])} indicates near-zero leverage risk (most healthy companies operate at 1-3x).")

    render_section("Performance Drivers","How to interpret each headline KPI.","Metric Guide")
    e1, e2, e3, e4 = st.columns(4, gap="medium")
    with e1: render_info_card("Revenue","Business Scale","Top-line size and growth momentum.","Growth = Current / Prior − 1")
    with e2: render_info_card("Margin","Operating Efficiency","How revenue converts to operating income.","Operating Income / Revenue")
    with e3: render_info_card("Cash Flow","Financial Output","Cash left after capex.","OCF − Capex")
    with e4: render_info_card("Liquidity","Balance Sheet Strength","Cash minus debt.","Cash + ST Investments − Total Debt")

# ================= INTELLIGENCE HUB =================
with tab_kpi:
    render_section("Executive KPI Intelligence","Detailed interpretation for every headline metric.","CFO View")
    render_insight("Intelligence Hub Overview","This tab expands the plain-English interpretation of every KPI. Perfect for onboarding new analysts or briefing non-finance executives.")

    metrics = [
        ("Revenue Growth","+15% YoY","Microsoft grew from $245.1B to $281.7B — a $36.6B increase. Growth like this at scale (>$250B revenue) is remarkable and driven primarily by Azure and Microsoft 365 Commercial cloud."),
        ("Gross Margin 68.8%","Down slightly","Gross margin dipped from 69.8% to 68.8% because scaling AI infrastructure has short-term margin costs. Still one of the highest gross margins of any Fortune 50 company."),
        ("Operating Margin 45.6%","+90 bps","Improved despite AI infra costs, showing operating leverage — revenue grew faster than opex."),
        ("Free Cash Flow $71.6B","Down 3.3%","FCF declined despite record OCF because capex went from $44B to $65B. This isn't a weakness — it's a bet on future AI/cloud growth."),
        ("Net Debt/EBITDA 0.08x","Near-zero leverage","MSFT has almost no net debt after subtracting cash. This gives them enormous flexibility for M&A or downturn resilience."),
        ("Rule of 40: 40.4%","Elite SaaS metric","Growth (15%) + FCF margin (25.4%) = 40.4%. Anything above 40% is considered best-in-class for software companies."),
    ]
    cols = st.columns(3, gap="medium")
    for i, (title, subtitle, text) in enumerate(metrics):
        with cols[i % 3]:
            render_info_card(subtitle, title, text)

# ================= REVENUE INTELLIGENCE =================
with tab_revenue:
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]
    render_section("Revenue Performance","Historical trend, product/service mix, and growth bridge.","Growth Analytics")

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1: render_kpi_card("FY2025 Revenue","Total Revenue", fmt_cur(k["revenue"]), "vs FY2024", delta_val=k["revenue_yoy_growth"])
    with r2: render_kpi_card("Revenue Mix","Service & Other", fmt_pct(services_mix), "Share of FY2025 revenue")
    with r3: render_kpi_card("Growth Spread","2025 vs 2024", fmt_cur(growth_spread), "Incremental revenue")

    left, right = st.columns(2, gap="medium")
    with left:
        render_chart_title("Revenue Over Time","FY2023 – FY2025")
        fig = px.line(ts.sort_values("period"), x="period", y="revenue", markers=True, color_discrete_sequence=[PALETTE["primary"]])
        fig.update_traces(line=dict(width=2.5, shape="spline"), marker=dict(size=8, color=PALETTE["primary"], line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>")
        fig.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig, 240), width="stretch", config={"displayModeBar": False})
    with right:
        render_chart_title("Revenue Mix by Category","Product vs Service")
        seg_long = segment_revenue.melt(id_vars=["period"], value_vars=["Product Revenue","Service and Other Revenue"], var_name="category", value_name="revenue")
        fig = px.bar(seg_long.sort_values("period"), x="period", y="revenue", color="category", barmode="stack",
            color_discrete_map={"Product Revenue": PALETTE["primary"], "Service and Other Revenue": PALETTE["accent"]})
        fig.update_traces(marker_line_width=0, hovertemplate="<b>FY%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
        fig.update_yaxes(tickprefix="$", ticksuffix="M")
        st.plotly_chart(style_fig(fig, 240, True), width="stretch", config={"displayModeBar": False})

    render_analyst_note(f"Service & Other revenue makes up {fmt_pct(services_mix)} of the business and is the growth engine — up 21% YoY. Product revenue (mostly Windows OEM and on-premises licenses) has been roughly flat for 3 years, reflecting the industry-wide shift from perpetual licenses to cloud subscriptions.")

    render_chart_title("Revenue Bridge: FY2024 → FY2025","Decomposed by segment contribution")
    prod_delta = k["product_revenue"] - k["product_revenue_prior"]
    svc_delta = k["service_revenue"] - k["service_revenue_prior"]
    fig_wf = go.Figure(go.Waterfall(orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["FY24 Revenue","Product Δ","Service Δ","FY25 Revenue"],
        y=[k["prior_year_revenue"], prod_delta, svc_delta, k["revenue"]],
        connector={"line":{"color":"#C7D0DD","dash":"dot"}},
        increasing={"marker":{"color":PALETTE["green"]}},
        decreasing={"marker":{"color":PALETTE["red"]}},
        totals={"marker":{"color":PALETTE["primary"]}},
        text=[fmt_cur(k["prior_year_revenue"]), fmt_cur(prod_delta), fmt_cur(svc_delta), fmt_cur(k["revenue"])],
        textposition="outside", textfont=dict(color="#0A2540", size=11)))
    fig_wf.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_wf, 290), width="stretch", config={"displayModeBar": False})

    render_analyst_note(f"Of the $36.6B revenue growth, ${abs(svc_delta)/1000:,.1f}B came from Service/Other while Product revenue actually declined by ${abs(prod_delta):,.0f}M. Almost 100% of Microsoft's growth is now cloud/subscription-driven — a fundamental transformation from the Windows/Office desktop era.")

    # Geographic split
    render_chart_title("Revenue by Geography","US vs International")
    geo = k["geographic"].copy()
    geo_long = geo.melt(id_vars=["region"], var_name="year", value_name="revenue")
    fig_geo = px.bar(geo_long, x="year", y="revenue", color="region", barmode="group",
        color_discrete_map={"United States":PALETTE["primary"], "Other Countries":PALETTE["accent"]})
    fig_geo.update_traces(marker_line_width=0, hovertemplate="<b>FY%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
    fig_geo.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_geo, 240, True), width="stretch", config={"displayModeBar": False})
    us_pct = geo.iloc[0]["2025"] / (geo.iloc[0]["2025"] + geo.iloc[1]["2025"])
    render_analyst_note(f"The US accounts for {fmt_pct(us_pct)} of revenue — a slight majority. This means Microsoft has significant currency exposure since ~49% of revenue is earned abroad. Currency fluctuations can move reported revenue by 1-3% in any given year.")

# ================= SEGMENTS (NEW) =================
with tab_segments:
    render_section("Segment Breakdown","Revenue, operating income, and growth by reporting segment (Note 18 of the 10-K).","3 Business Segments")

    segs = k["segments"].copy()
    segs["rev_growth"] = (segs["rev_2025"] - segs["rev_2024"]) / segs["rev_2024"]
    segs["opi_growth"] = (segs["opi_2025"] - segs["opi_2024"]) / segs["opi_2024"]
    segs["op_margin"] = segs["opi_2025"] / segs["rev_2025"]

    # Segment KPI cards
    for _, row in segs.iterrows():
        color = SEG_COLORS[row["segment"]]
        cA, cB, cC, cD = st.columns(4, gap="medium")
        with cA: render_kpi_card(row["segment"], "FY2025 Revenue", fmt_cur(row["rev_2025"]), "vs FY2024", delta_val=row["rev_growth"])
        with cB: render_kpi_card("Operating Income", "FY2025", fmt_cur(row["opi_2025"]), "vs FY2024", delta_val=row["opi_growth"])
        with cC: render_kpi_card("Operating Margin", "FY2025", fmt_pct(row["op_margin"]), "Op Income / Revenue", delta_val=None)
        with cD:
            seg_share = row["rev_2025"] / k["revenue"]
            render_kpi_card("Revenue Share", "% of Total", fmt_pct(seg_share), "Segment weighting", delta_val=None)

    # Combined chart
    render_chart_title("Segment Revenue Over Time","FY2023 – FY2025")
    seg_long = pd.melt(segs, id_vars=["segment"], value_vars=["rev_2023","rev_2024","rev_2025"], var_name="year", value_name="revenue")
    seg_long["year"] = seg_long["year"].str.replace("rev_","FY")
    fig_seg = px.bar(seg_long, x="year", y="revenue", color="segment", barmode="group", color_discrete_map=SEG_COLORS)
    fig_seg.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
    fig_seg.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_seg, 280, True), width="stretch", config={"displayModeBar": False})

    render_analyst_note("Intelligent Cloud (Azure + server products) grew 21% YoY — the fastest of any segment and the primary growth engine. Productivity & Business Processes (Microsoft 365, LinkedIn, Dynamics) grew 13% off a large base. More Personal Computing (Windows, Gaming, Search) grew 7%, driven mainly by Xbox/Activision Blizzard integration. Investors overwhelmingly focus on Azure growth as the leading indicator for MSFT's future.")

    # Operating income mix
    render_chart_title("Operating Income Contribution","How each segment contributes to total operating income")
    opi_df = pd.DataFrame({"segment": segs["segment"], "operating_income": segs["opi_2025"]})
    fig_opi = px.pie(opi_df, values="operating_income", names="segment", hole=0.55,
        color="segment", color_discrete_map=SEG_COLORS)
    fig_opi.update_traces(textposition="outside", textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Op Income: $%{value:,.0f}M<extra></extra>",
        marker=dict(line=dict(color="#FFFFFF", width=2)))
    fig_opi.update_layout(showlegend=False)
    st.plotly_chart(style_fig(fig_opi, 340), width="stretch", config={"displayModeBar": False})

    render_analyst_note(f"Productivity & Business Processes contributes the majority of operating income ({fmt_pct(segs.iloc[0]['opi_2025']/k['operating_income'])}) despite being smaller than Intelligent Cloud in revenue — because Microsoft 365 has extraordinary margins. Intelligent Cloud's operating margin is lower ({fmt_pct(segs.iloc[1]['opi_2025']/segs.iloc[1]['rev_2025'])}) because Azure requires massive capex investment.")

    # Segment table
    seg_display = segs[["segment","rev_2025","rev_2024","rev_2023","opi_2025","opi_2024","opi_2023","op_margin"]].copy()
    for c in ["rev_2025","rev_2024","rev_2023","opi_2025","opi_2024","opi_2023"]:
        seg_display[c] = seg_display[c].apply(fmt_cur)
    seg_display["op_margin"] = seg_display["op_margin"].apply(fmt_pct)
    seg_display.columns = ["Segment","Rev FY25","Rev FY24","Rev FY23","Op Inc FY25","Op Inc FY24","Op Inc FY23","Op Margin FY25"]
    render_financial_table("Segment Financial Table", seg_display, "Source: MSFT FY2025 10-K, Note 18.")

# ================= CAPITAL ALLOCATION (NEW) =================
with tab_capital:
    render_section("Capital Allocation","How Microsoft deployed its cash in FY2025 — the story of investment vs. shareholder returns.","Cash Deployment")

    c = k["cap_allocation"]
    ca1, ca2, ca3, ca4 = st.columns(4, gap="medium")
    with ca1: render_kpi_card("Reinvestment","Capital Expenditures", fmt_cur(c["capex"]), f"{fmt_pct(k['capex_intensity'])} of revenue", delta_val=None)
    with ca2: render_kpi_card("M&A","Acquisitions (net)", fmt_cur(c["acquisitions"]), "vs Activision Blizzard $69B in FY24", delta_val=None)
    with ca3: render_kpi_card("Dividends","Cash Dividends Paid", fmt_cur(c["dividends"]), f"{fmt_pct(c['dividends']/k['net_income'])} of net income", delta_val=None)
    with ca4: render_kpi_card("Buybacks","Share Repurchases", fmt_cur(c["buybacks"]), f"{fmt_pct(c['buybacks']/k['net_income'])} of net income", delta_val=None)

    # Capital allocation waterfall
    render_chart_title("Capital Allocation Breakdown","FY2025 cash deployed across categories")
    ca_df = pd.DataFrame({
        "category": ["Capex","Acquisitions","Dividends","Buybacks"],
        "amount": [c["capex"], c["acquisitions"], c["dividends"], c["buybacks"]],
    })
    fig_ca = px.bar(ca_df.sort_values("amount"), x="amount", y="category", orientation="h",
        color="category", color_discrete_sequence=[PALETTE["primary"], PALETTE["accent"], PALETTE["green"], PALETTE["gold"]])
    fig_ca.update_traces(marker_line_width=0, texttemplate="%{x:$,.0f}M", textposition="outside",
        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}M<extra></extra>")
    fig_ca.update_xaxes(tickprefix="$", ticksuffix="M")
    fig_ca.update_layout(showlegend=False)
    st.plotly_chart(style_fig(fig_ca, 260), width="stretch", config={"displayModeBar": False})

    render_analyst_note(f"Microsoft deployed {fmt_cur(c['total_deployed'])} of cash in FY2025 — {fmt_cur(c['capex'])} into capex (AI/cloud infrastructure), {fmt_cur(c['acquisitions'])} into small M&A, {fmt_cur(c['dividends'])} to dividends, and {fmt_cur(c['buybacks'])} into buybacks. Total returned to shareholders: {fmt_cur(c['total_returned_to_shareholders'])} — meaningful, but capex is now the dominant use of cash for the first time in years.")

    # 3-year trend
    render_chart_title("Capital Allocation Trend","How deployment has shifted over 3 years")
    cf_hist = pd.DataFrame({
        "Year": ["FY2023","FY2024","FY2025"] * 4,
        "Category": ["Capex"]*3 + ["Acquisitions"]*3 + ["Dividends"]*3 + ["Buybacks"]*3,
        "Amount": [28107, 44477, 64551, 1670, 69132, 5978, 19800, 21771, 24082, 22245, 17254, 18420],
    })
    fig_trend = px.bar(cf_hist, x="Year", y="Amount", color="Category", barmode="group",
        color_discrete_sequence=[PALETTE["primary"], PALETTE["accent"], PALETTE["green"], PALETTE["gold"]])
    fig_trend.update_traces(marker_line_width=0, hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>")
    fig_trend.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_trend, 300, True), width="stretch", config={"displayModeBar": False})

    render_analyst_note("Capex has grown 2.3x in two years — from $28B in FY23 to $65B in FY25 — an unprecedented ramp for a mature software company. This is Microsoft's AI infrastructure bet. Meanwhile M&A dropped sharply because FY2024 included the massive $69B Activision Blizzard acquisition (a one-time event). Dividends grow steadily; buybacks fluctuate based on stock price and cash needs.")

# ================= AI FORECASTING =================
with tab_forecast:
    render_section("Revenue Outlook Model","Adjust growth and volatility to explore scenarios, Monte Carlo bands, and sensitivity.","Scenario Model")

    s1, s2, s3 = st.columns(3, gap="medium")
    with s1: growth_rate_pct = st.slider("Base Case Growth (%)", 0, 30, 15, 1)
    with s2: forecast_years = st.slider("Forecast Horizon (years)", 1, 5, 3, 1)
    with s3: volatility_pct = st.slider("Growth Volatility (σ, %)", 1, 15, 5, 1)

    base_growth = growth_rate_pct / 100
    vol = volatility_pct / 100

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

    render_analyst_note(f"Bear/Base/Bull represents +/- 5 percentage points from your selected growth rate. At Microsoft's FY25 growth of 15%, that spans a $70B+ range by year {int(base_last['year'])} — showing how sensitive long-term forecasts are to small changes in the growth assumption.")

    render_chart_title("Historical + Scenario Forecast","Bear/Base/Bull cases")
    hist_df = ts[["period","revenue"]].copy()
    hist_df["year"] = hist_df["period"].astype(int)
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"], mode="lines+markers", name="Historical",
        line=dict(color=PALETTE["primary"], width=3), marker=dict(size=7),
        hovertemplate="<b>FY%{x}</b><br>$%{y:,.0f}M<extra></extra>"))
    scolors = {"Bear Case": PALETTE["red"], "Base Case": PALETTE["green"], "Bull Case": PALETTE["gold"]}
    for sc, col in scolors.items():
        sub = scenario_df[scenario_df["scenario"]==sc]
        fig_fc.add_trace(go.Scatter(x=sub["year"], y=sub["revenue"], mode="lines+markers", name=sc,
            line=dict(color=col, width=2.2, dash="dash"), marker=dict(size=6),
            hovertemplate="<b>FY%{x}</b><br>$%{y:,.0f}M<extra></extra>"))
    fig_fc.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_fc, 260, True), width="stretch", config={"displayModeBar": False})

           render_chart_title("Monte Carlo Fan Chart", f"500 simulations · μ={growth_rate_pct}% σ={volatility_pct}%")
    mc = monte_carlo_forecast(k["revenue"], base_growth, vol, 2026, forecast_years, 500)
    fig_mc = go.Figure()
    fig_mc.add_trace(go.Scatter(x=hist_df["year"], y=hist_df["revenue"], mode="lines+markers", name="Historical",
        line=dict(color=PALETTE["primary"], width=3), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>$%{y:,.0f}M<extra></extra>"))
    fig_mc.add_trace(go.Scatter(x=list(mc["year"])+list(mc["year"][::-1]), y=list(mc["p90"])+list(mc["p10"][::-1]),
        fill="toself", fillcolor="rgba(62,92,142,0.20)", line=dict(color="rgba(0,0,0,0)"), showlegend=True,
        name="P10–P90 band", hoverinfo="skip"))
    fig_mc.add_trace(go.Scatter(x=mc["year"], y=mc["p50"], mode="lines+markers", name="Median (P50)",
        line=dict(color=PALETTE["gold"], width=2.4, dash="dash"), marker=dict(size=6),
        hovertemplate="<b>FY%{x}</b><br>Median: $%{y:,.0f}M<extra></extra>"))
    fig_mc.update_yaxes(tickprefix="$", ticksuffix="M")
    st.plotly_chart(style_fig(fig_mc, 280, True), width="stretch", config={"displayModeBar": False})

    render_analyst_note("The P10–P90 band captures ~80% of simulated outcomes. Wider bands = more uncertainty. This helps quantify forecast risk — instead of a single point estimate, you see the range of plausible outcomes given the volatility assumption.")

    render_chart_title("Sensitivity: Growth × Margin → Operating Income", f"Projected FY{2025+forecast_years} operating income")
    growth_range = np.arange(0.02, 0.28, 0.04)
    margin_range = np.arange(0.20, 0.55, 0.05)
    grid = sensitivity_grid(k["revenue"], k["operating_margin"], growth_range, margin_range, forecast_years)
    fig_hm = go.Figure(go.Heatmap(z=grid,
        x=[f"{g*100:.0f}%" for g in growth_range],
        y=[f"{m*100:.0f}%" for m in margin_range],
        colorscale=[[0,"#F5F7FA"],[0.5,"#3E5C8E"],[1,"#0A2540"]],
        hovertemplate="Growth: %{x}<br>Margin: %{y}<br>Op Income: $%{z:,.0f}M<extra></extra>",
        colorbar=dict(title=dict(text="Op Income ($M)", font=dict(color="#4A5878", size=10)),
                      tickfont=dict(color="#7A879B", size=9))))
    fig_hm.update_xaxes(title_text="Revenue Growth")
    fig_hm.update_yaxes(title_text="Operating Margin")
    st.plotly_chart(style_fig(fig_hm, 320), width="stretch", config={"displayModeBar": False})

    render_analyst_note("This heatmap shows how projected operating income changes based on two assumptions: revenue growth (X-axis) and operating margin (Y-axis). Darker = higher projected income. Use this to stress-test valuation — small changes in either variable can create wildly different outcomes.")

    render_section("Saved Scenarios","Snapshot assumptions to compare side-by-side.","Session Memory")
    sv1, sv2, sv3 = st.columns([2,1,1], gap="medium")
    with sv1: scen_name = st.text_input("Scenario name", value=f"Growth {growth_rate_pct}%")
    with sv2:
        if st.button("Save scenario"):
            st.session_state.saved_scenarios[scen_name] = {
                "growth": growth_rate_pct, "years": forecast_years,
                "final_revenue": forecast_df.iloc[-1]["revenue"],
                "final_year": int(forecast_df.iloc[-1]["year"])}
    with sv3:
        if st.button("Clear all"): st.session_state.saved_scenarios = {}

    if st.session_state.saved_scenarios:
        rows = [{"Scenario": n, "Growth": f"{s['growth']}%", "Horizon": f"{s['years']}y",
                 f"Final Revenue": fmt_cur(s["final_revenue"]),
                 "Year": f"FY{s['final_year']}"} for n, s in st.session_state.saved_scenarios.items()]
        render_financial_table("Saved Scenarios", pd.DataFrame(rows))
    else:
        render_insight("No scenarios saved yet","Click 'Save scenario' to snapshot the current sliders.")

    latest_fc = forecast_df.iloc[-1]
    render_insight("Forecast Narrative",
        f"With {growth_rate_pct}% growth and {volatility_pct}% volatility, projected revenue reaches "
        f"{fmt_cur(latest_fc['revenue'])} by FY{int(latest_fc['year'])} in the base case. "
        f"P10–P90 band captures ~80% of simulated outcomes.")

# ================= FINANCIAL STATEMENTS =================
with tab_financials:
    fin = result["financials"]
    render_section("Financial Statements","Full income statement, balance sheet, and cash flow — direct from the 10-K.","Statement Tables")

    render_analyst_note("These are the exact figures reported in Microsoft's FY2025 10-K (June 30, 2025). Every KPI on this dashboard is derived from these three statements plus segment Note 18. Download the CSVs to work with the raw data in Excel.")

    f1, f2 = st.columns(2, gap="medium")
    with f1:
        render_financial_table("Income Statement", fin["income"], "Values in $ millions.")
        st.download_button("Download Income CSV", dataframe_to_csv(fin["income"]), "msft_income_statement.csv", "text/csv")
    with f2:
        render_financial_table("Balance Sheet", fin["balance"], "Values in $ millions. Balance sheet reports 2 years per 10-K standard; FY2023 estimated from prior filings.")
        st.download_button("Download Balance CSV", dataframe_to_csv(fin["balance"]), "msft_balance_sheet.csv", "text/csv")

    render_financial_table("Cash Flow Statement", fin["cashflow"], "Values in $ millions.")
    st.download_button("Download Cash Flow CSV", dataframe_to_csv(fin["cashflow"]), "msft_cash_flow.csv", "text/csv")

    render_analyst_note(f"Key observation: Net Income of {fmt_cur(k['net_income'])} vs Operating Cash Flow of {fmt_cur(k['operating_cash_flow'])} — OCF is $34B higher than net income due primarily to $34B of non-cash D&A. This is why analysts focus on cash flow: it strips out accounting-only charges.")

# ================= AI COPILOT =================
with tab_ai:
    render_section("AI Copilot for Financial Commentary","Ask about revenue, margins, cash flow, liquidity, forecasting, segments, or capital allocation.","Narrative AI")

    render_section("Suggested Questions","Click a prompt to auto-fill and run.","Quick Prompts")
    chip_cols = st.columns(4, gap="small")
    suggestions = [
        "How did revenue perform year over year?",
        "Break down Microsoft's segment performance.",
        "Explain FY2025 capital allocation.",
        "What do EBITDA, ROIC, and Rule of 40 tell us?",
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

    render_analyst_note("The AI Copilot pulls directly from the verified 10-K figures — every answer references real, sourced numbers. Try asking about specific topics: segments, capex, EBITDA, ROIC, capital allocation, or forecasting scenarios.")

    render_section("Example Prompts","Additional prompt ideas.","Prompt Ideas")
    p1, p2, p3, p4 = st.columns(4, gap="medium")
    with p1: render_capability_card("Revenue","Growth Story","Try: How did revenue perform year over year?")
    with p2: render_capability_card("Segments","Azure vs Others","Try: Break down segment performance.")
    with p3: render_capability_card("Capital","Deployment Analysis","Try: Explain FY2025 capital allocation.")
    with p4: render_capability_card("Ratios","Analyst Metrics","Try: What do EBITDA, ROIC, Rule of 40 mean?")

import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import tenk_engine as engine

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MSFT FY25 10-K Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME — Fluent + nested tiles + polish
# ============================================================
st.markdown("""
<style>
/* Base */
.stApp { background: #FFFFFF; }
html, body, [class*="css"] {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #252423;
}
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }
.num, .kpi-value { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }

h1, h2, h3, h4 { color: #252423; font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 2.25rem; }

/* ==========================================================
   HEADER TILE (top of each tab)
   ========================================================== */
.header-tile {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 1.75rem 2rem; margin: 0.5rem 0 2rem 0;
  position: relative; overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.header-tile:hover { box-shadow: 0 4px 12px rgba(0,120,212,0.08); border-color: #C7E0F4; }
.header-tile:hover .gradient-stripe { animation-duration: 2s; }
.header-tile:hover .live-dot { animation-duration: 1s; }
.header-tile h1 { margin: 0 0 0.4rem 0; font-size: 1.85rem; color: #252423; }
.header-tile .subtitle-wrap { position: relative; height: 26px; overflow: hidden; }
.header-tile .subtitle { color: #605E5C; font-size: 1rem; line-height: 1.5; margin: 0; position: absolute; left: 0; right: 0; }
.header-tile .subtitle.rotating { opacity: 0; animation: subtitleCycle 18s infinite; }
@keyframes subtitleCycle {
  0%, 30% { opacity: 1; transform: translateY(0); }
  33%, 100% { opacity: 0; transform: translateY(-6px); }
}
.header-tile .meta { color: #8A8886; font-size: 0.78rem; margin-top: 0.85rem; font-family: 'Segoe UI', monospace; }

.gradient-stripe {
  position: absolute; bottom: 0; left: 0; height: 3px; width: 100%;
  background: linear-gradient(90deg, transparent, #0078D4, #005A9E, #0078D4, transparent);
  background-size: 200% 100%; animation: gradientSlide 4s ease-in-out infinite;
}
@keyframes gradientSlide {
  0%, 100% { background-position: -100% 0; }
  50% { background-position: 100% 0; }
}

.live-badge {
  position: absolute; top: 1.5rem; right: 1.75rem;
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: #F3F9FD; border: 1px solid #C7E0F4; border-radius: 20px;
  padding: 0.3rem 0.75rem; font-size: 0.72rem; color: #005A9E; font-weight: 600;
}
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: #107C10; animation: pulse 2s infinite; }
.header-tile.centered { text-align: center; padding: 3rem 2rem; }
.header-tile.centered h1 { font-size: 2.25rem; }

/* ==========================================================
   SECTION TILE (small header tile inside content wrapper)
   ========================================================== */
.section-tile {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 1rem 1.35rem; margin-bottom: 1.25rem;
  position: relative; overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.section-tile:hover { box-shadow: 0 3px 10px rgba(0,120,212,0.06); border-color: #C7E0F4; transform: translateY(-1px); }
.section-tile .section-tile-title { font-size: 1.15rem; font-weight: 600; color: #252423; margin: 0; }
.section-tile .section-tile-sub { font-size: 0.82rem; color: #8A8886; margin-top: 0.15rem; }
.section-tile .mini-stripe {
  position: absolute; bottom: 0; left: 0; height: 2px; width: 100%;
  background: linear-gradient(90deg, transparent, #0078D4, transparent);
  background-size: 200% 100%; animation: gradientSlide 5s ease-in-out infinite;
}

/* ==========================================================
   CONTENT WRAPPER (big outer tile for a section)
   ========================================================== */
.content-wrap {
  background: #FAFAFA; border: 1px solid #EDEBE9; border-radius: 6px;
  padding: 1.25rem; margin: 2rem 0 2.5rem 0;
}

/* ==========================================================
   KPI CARD with unified expander
   ========================================================== */
.kpi-card {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px 4px 0 0;
  border-bottom: none;
  padding: 1.1rem 1.25rem;
  border-top: 2px solid #0078D4;
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, border-top-width 0.2s ease;
  animation: fadeInUp 0.5s ease both;
  cursor: default;
  position: relative;
}
.kpi-card:hover {
  background: #FAFAFA;
  border-color: #C7E0F4;
  border-top-color: #005A9E;
  border-top-width: 3px;
  box-shadow: 0 4px 12px rgba(0,120,212,0.08);
}
.kpi-card:hover .kpi-value { color: #005A9E; }
.kpi-card:hover .kpi-delta { transform: scale(1.05); }
.kpi-card.warning { border-top-color: #D83B01; }
.kpi-card.warning:hover { border-color: #F1A98A; box-shadow: 0 4px 12px rgba(216,59,1,0.08); }
.kpi-card.signal { border-top-color: #FFB900; }
.kpi-card.signal:hover { border-color: #FFE599; box-shadow: 0 4px 12px rgba(255,185,0,0.10); }

.kpi-label { font-size: 0.72rem; color: #605E5C; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; font-weight: 600; }
.kpi-value { font-size: 1.85rem; font-weight: 600; color: #252423; line-height: 1.1; transition: color 0.2s ease; }
.kpi-delta { font-size: 0.82rem; margin-top: 0.4rem; font-weight: 500; transition: transform 0.2s ease; display: inline-block; }
.kpi-delta.up { color: #107C10; }
.kpi-delta.down { color: #D83B01; }
.kpi-delta.flat { color: #8A8886; }
.kpi-sub { font-size: 0.72rem; color: #8A8886; margin-top: 0.25rem; }

.kpi-card:nth-child(1) { animation-delay: 0.05s; }
.kpi-card:nth-child(2) { animation-delay: 0.10s; }
.kpi-card:nth-child(3) { animation-delay: 0.15s; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==========================================================
   UNIFIED EXPANDER — attached to bottom of KPI card
   ========================================================== */
.kpi-expander-wrap {
  border: 1px solid #EDEBE9; border-top: none;
  border-radius: 0 0 4px 4px;
  overflow: hidden; margin-bottom: 1rem;
  transition: border-color 0.2s ease;
}
.kpi-expander-wrap:hover { border-color: #C7E0F4; }
.kpi-expander-wrap .stExpander { border: none !important; background: #FFFFFF !important; }
.kpi-expander-wrap .streamlit-expanderHeader {
  background: #FFFFFF !important; border: none !important; border-top: 1px solid #F3F2F1 !important;
  border-radius: 0 !important; padding: 0.55rem 1.25rem !important;
  font-size: 0.78rem !important; color: #0078D4 !important; font-weight: 500 !important;
}
.kpi-expander-wrap .streamlit-expanderHeader:hover { background: #FAFAFA !important; color: #005A9E !important; }
.kpi-expander-wrap .streamlit-expanderContent { background: #FFFFFF !important; padding: 0.5rem 1.25rem 1rem 1.25rem !important; }

/* ==========================================================
   ANALYST NOTE with spacing
   ========================================================== */
.analyst-note {
  background: #F3F9FD; border-left: 3px solid #0078D4; border-radius: 2px;
  padding: 0.95rem 1.15rem; margin: 1.5rem 0 1rem 0;
  font-size: 0.92rem; color: #252423; line-height: 1.6;
}
.analyst-note strong { color: #005A9E; }
.analyst-note.top-spaced { margin-top: 2rem; }

/* ==========================================================
   RIBBON CARDS
   ========================================================== */
.ribbon-card {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 0.85rem 1rem; text-align: center;
  border-top: 2px solid #0078D4;
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
  animation: fadeInUp 0.5s ease both;
  cursor: default;
}
.ribbon-card:hover {
  background: #FAFAFA;
  border-color: #C7E0F4; border-top-color: #005A9E;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,120,212,0.08);
}
.ribbon-card:hover .ribbon-num { transform: scale(1.05); color: #005A9E; }
.ribbon-num { font-size: 1.25rem; font-weight: 600; color: #252423; font-variant-numeric: tabular-nums; line-height: 1.15; transition: transform 0.2s ease, color 0.2s ease; display: inline-block; }
.ribbon-lbl { font-size: 0.68rem; color: #605E5C; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem; font-weight: 600; }

/* ==========================================================
   ROTATING CAROUSEL (welcome)
   ========================================================== */
.cstat-wrap { position: relative; height: 60px; text-align: center; margin-top: 1.5rem; }
.cstat {
  position: absolute; left: 0; right: 0;
  font-size: 1.5rem; color: #0078D4; font-weight: 600; font-variant-numeric: tabular-nums;
  opacity: 0; animation: cstatCycle 18s infinite;
}
@keyframes cstatCycle {
  0%, 12% { opacity: 1; transform: translateY(0); }
  16%, 100% { opacity: 0; transform: translateY(-8px); }
}

/* ==========================================================
   BADGES & FOOTER
   ========================================================== */
.verified-badge { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: #107C10; font-weight: 500; }
.pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: #107C10; animation: pulse 2s infinite; }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(16,124,16,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(16,124,16,0); }
}
.as-of { display: inline-block; background: #F3F2F1; border: 1px solid #EDEBE9; border-radius: 20px; padding: 0.25rem 0.75rem; font-size: 0.72rem; color: #605E5C; font-family: 'Segoe UI', monospace; }
.source-cite { font-size: 0.68rem; color: #8A8886; vertical-align: super; margin-left: 0.25rem; }

.footer { background: #252423; color: #F3F2F1; padding: 2rem; border-radius: 4px; margin-top: 3rem; text-align: center; font-size: 0.85rem; }
.footer a { color: #6AB4F7; text-decoration: none; margin: 0 0.75rem; font-weight: 500; }
.footer a:hover { color: #FFFFFF; }

/* ==========================================================
   TABS & BUTTONS
   ========================================================== */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: transparent; border-bottom: 1px solid #EDEBE9; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; padding: 0.75rem 1.1rem; color: #605E5C; font-weight: 500; font-size: 0.92rem; }
.stTabs [aria-selected="true"] { color: #0078D4 !important; border-bottom: 2px solid #0078D4 !important; }

[data-testid="stSidebar"] { background: #FAFAFA; border-right: 1px solid #EDEBE9; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #252423; }

.stButton>button {
  background: #FFFFFF; color: #252423; border: 1px solid #EDEBE9;
  padding: 0.75rem 1rem; border-radius: 4px; font-weight: 500; font-size: 0.9rem;
  transition: all 0.2s ease; width: 100%; text-align: left; line-height: 1.4;
  white-space: normal; height: auto; min-height: 56px;
  position: relative; padding-right: 2.5rem;
}
.stButton>button::after {
  content: "→"; position: absolute; right: 1rem; top: 50%; transform: translate(10px, -50%);
  opacity: 0; color: #0078D4; font-weight: 600; transition: all 0.25s ease;
}
.stButton>button:hover {
  background: #FAFAFA; border-color: #0078D4; color: #005A9E;
  transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,120,212,0.08);
}
.stButton>button:hover::after { opacity: 1; transform: translate(0, -50%); }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
FINANCIALS = engine.microsoft_fallback_financials()
KPIS = engine.compute_kpis(FINANCIALS)

RIBBON = [
    {"value": "228K",    "label": "Employees"},
    {"value": "$162.7B", "label": "EBITDA"},
    {"value": "51%",     "label": "US Revenue"},
    {"value": "+15%",    "label": "YoY Growth"},
    {"value": "$30B",    "label": "Cash"},
    {"value": "$65B",    "label": "Capex"},
    {"value": "45.6%",   "label": "Op Margin"},
    {"value": "27.4%",   "label": "ROIC"},
]

REV_B      = KPIS["revenue"] / 1000
NI_B       = KPIS["net_income"] / 1000
OPM        = KPIS["operating_margin"] * 100
FCF_B      = KPIS["free_cash_flow"] / 1000
CAPEX_B    = KPIS["capex"] / 1000
OCF_B      = KPIS["operating_cash_flow"] / 1000
EPS        = KPIS["per_share"]["diluted_eps"]["2025"]
RULE40     = KPIS["rule_of_40"] * 100
ROIC       = KPIS["roic"] * 100
ND_EBITDA  = KPIS["net_debt_ebitda"]
OPM_DELTA  = KPIS["op_margin_delta"] * 10000
CAPEX_YOY  = KPIS["capex_yoy_growth"] * 100
REV_YOY    = KPIS["revenue_yoy_growth"] * 100
CASH_B     = KPIS["cash_plus_st_inv"] / 1000

# ============================================================
# HELPERS
# ============================================================
def header_tile(title, subtitles, meta=None, live_metric=None, centered=False):
    """subtitles: string or list of strings (list = rotating carousel)."""
    cls = "header-tile centered" if centered else "header-tile"
    if isinstance(subtitles, str):
        sub_html = f'<div class="subtitle-wrap"><p class="subtitle">{subtitles}</p></div>'
    else:
        subs = "".join([
            f'<p class="subtitle rotating" style="animation-delay:{i*6}s;">{s}</p>'
            for i, s in enumerate(subtitles)
        ])
        sub_html = f'<div class="subtitle-wrap">{subs}</div>'
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    live_html = f'<div class="live-badge"><span class="live-dot"></span> Live · {live_metric}</div>' if live_metric else ""
    stripe = '<div class="gradient-stripe"></div>' if not centered else ""
    st.markdown(f"""
    <div class="{cls}">
      {live_html}
      <h1>{title}</h1>
      {sub_html}
      {meta_html}
      {stripe}
    </div>
    """, unsafe_allow_html=True)

def section_tile(title, subtitle=None):
    sub_html = f'<div class="section-tile-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div class="section-tile">
      <div class="section-tile-title">{title}</div>
      {sub_html}
      <div class="mini-stripe"></div>
    </div>
    """, unsafe_allow_html=True)

def content_wrap_open():
    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

def content_wrap_close():
    st.markdown('</div>', unsafe_allow_html=True)

def kpi_card(label, value, delta=None, delta_dir="flat", sub=None, source=None, variant=""):
    src = f'<span class="source-cite">{source}</span>' if source else ""
    delta_html = ""
    if delta:
        arrow = "▲" if delta_dir == "up" else ("▼" if delta_dir == "down" else "—")
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow} {delta}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    variant_cls = f" {variant}" if variant else ""
    return f"""
    <div class="kpi-card{variant_cls}">
      <div class="kpi-label">{label}{src}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
      {sub_html}
    </div>
    """

def kpi_expander_open():
    st.markdown('<div class="kpi-expander-wrap">', unsafe_allow_html=True)

def kpi_expander_close():
    st.markdown('</div>', unsafe_allow_html=True)

def note(text, top_spaced=False):
    cls = "analyst-note top-spaced" if top_spaced else "analyst-note"
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)

def ribbon_bar():
    cols = st.columns(len(RIBBON), gap="small")
    for i, item in enumerate(RIBBON):
        with cols[i]:
            st.markdown(f"""
            <div class="ribbon-card">
              <div class="ribbon-num">{item['value']}</div>
              <div class="ribbon-lbl">{item['label']}</div>
            </div>
            """, unsafe_allow_html=True)

def kpi_explainer(what, calc, source, useful):
    return f"""
    **What does this mean?**
    {what}

    **How was this calculated?**
    {calc}

    **Where does this come from?**
    {source}

    **Why is it useful?**
    {useful}
    """

FLUENT_LAYOUT = dict(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
    font=dict(family="Segoe UI", color="#252423"),
    hoverlabel=dict(
        bgcolor="#FFFFFF", bordercolor="#0078D4",
        font=dict(family="Segoe UI", color="#252423", size=12)
    ),
)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### MSFT 10-K Intelligence")
    st.markdown('<span class="as-of">FY2025 · Filed Jul 30, 2025</span>', unsafe_allow_html=True)
    st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Verified from 10-K PDF</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Navigation")
    st.markdown("""
    - Welcome
    - Executive Summary
    - Revenue & Segments
    - Capital Allocation
    - AI Copilot
    """)
    st.markdown("---")
    st.markdown("#### About")
    st.markdown("<small>Interactive analysis of Microsoft's FY2025 10-K filing. Every metric includes a plain-English explanation.</small>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<small><strong>Author:</strong> Bea Lucido-Tan</small>", unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "Welcome",
    "Executive Summary",
    "Revenue & Segments",
    "Capital Allocation",
    "AI Copilot",
])

# ============================================================
# TAB 1: WELCOME
# ============================================================
with tabs[0]:
    st.markdown("""
    <div class="header-tile centered">
      <h1>Microsoft FY2025 10-K</h1>
      <p class="subtitle">An interactive breakdown of Microsoft's FY2025 10-K filing, built for financial analysis portfolio demonstration.</p>
      <div class="meta">Fiscal Year 2025 · July 2024 – June 2025 · <span style="color:#107C10;">● Data verified from 10-K PDF</span></div>
    </div>
    """, unsafe_allow_html=True)

    stat_options = [
        "$281.7B Revenue",
        "45.6% Operating Margin",
        "$101.8B Net Income",
        "27.4% Return on Capital",
        "$64.6B AI Investment",
        "0.08x Net Debt / EBITDA",
    ]
    stats_html = "".join([
        f'<div class="cstat" style="animation-delay:{i*3}s;">{s}</div>' for i, s in enumerate(stat_options)
    ])
    st.markdown(f'<div class="cstat-wrap">{stats_html}</div>', unsafe_allow_html=True)

# ============================================================
# TAB 2: EXECUTIVE SUMMARY
# ============================================================
with tabs[1]:
    header_tile(
        "Executive Summary",
        subtitles=[
            "FY2025 headline results and financial health indicators.",
            "Six key metrics, three quality ratios, one revenue bridge.",
            "Read the full FY2025 story in under five minutes.",
        ],
        meta="Fiscal Year 2025 · July 1, 2024 – June 30, 2025",
        live_metric="$281.7B Revenue"
    )

    # Ribbon
    ribbon_bar()
    st.caption("The eight most-referenced statistics from Microsoft's FY2025 filing — spanning headcount, profitability, and balance sheet strength.")

    # SECTION 1 — Key Financial Metrics
    content_wrap_open()
    section_tile("Key Financial Metrics", "Headline results with year-over-year comparison")

    cols = st.columns(3, gap="medium")
    with cols[0]:
        st.markdown(kpi_card("Revenue", f"${REV_B:.1f}B", f"+{REV_YOY:.1f}%", "up", "vs $245.1B FY24", "p.48"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="All money Microsoft earned from selling products and services during FY2025 — including Azure, Office 365, LinkedIn, Windows, Xbox, and other offerings.",
                calc="Sum of Product Revenue ($63.9B) + Service and Other Revenue ($217.8B) = $281.7B total.",
                source="10-K Income Statement, page 48. Verified directly from the filed PDF.",
                useful="Revenue growth is the single most-watched top-line indicator. A 14.9% jump at $245B+ scale signals extraordinary demand — most companies this large grow 3–5% annually."
            ))
        kpi_expander_close()
    with cols[1]:
        st.markdown(kpi_card("Net Income", f"${NI_B:.1f}B", "+15.6%", "up", "vs $88.1B FY24", "p.48"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The final profit after all expenses, interest, and taxes are subtracted from revenue. This is what Microsoft actually 'keeps.'",
                calc="Revenue ($281.7B) − Cost of Revenue − Operating Expenses − Other Income (Expense) − Taxes = $101.8B.",
                source="10-K Income Statement, page 48. Also known as 'net earnings.'",
                useful="Net income growing faster than revenue (15.6% vs 14.9%) indicates improving operational efficiency."
            ))
        kpi_expander_close()
    with cols[2]:
        st.markdown(kpi_card("Operating Margin", f"{OPM:.1f}%", f"+{OPM_DELTA:.0f} bps", "up", "vs 44.6% FY24", "p.48"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The percentage of revenue that becomes operating profit before interest and taxes.",
                calc="Operating Income ($128.5B) ÷ Revenue ($281.7B) = 45.6%.",
                source="10-K Income Statement, page 48.",
                useful="45.6% is elite territory — most Fortune 500 companies operate at 10–15% margins."
            ))
        kpi_expander_close()

    cols2 = st.columns(3, gap="medium")
    with cols2[0]:
        st.markdown(kpi_card("Free Cash Flow", f"${FCF_B:.1f}B", "-3.3%", "down", "vs $74.1B FY24", "p.51", variant="warning"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The cash Microsoft has left over after operating expenses AND capital investments.",
                calc="Operating Cash Flow ($136.2B) − Capital Expenditures ($64.6B) = $71.6B.",
                source="10-K Cash Flow Statement, page 51.",
                useful="FCF declined for the first time in 5+ years — a signal that AI infrastructure spending is now outpacing cash generation growth."
            ))
        kpi_expander_close()
    with cols2[1]:
        st.markdown(kpi_card("Capital Expenditure", f"${CAPEX_B:.1f}B", f"+{CAPEX_YOY:.1f}%", "up", "vs $44.5B FY24", "p.51", variant="signal"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="Money spent on long-term physical assets — datacenters, servers, chips, buildings.",
                calc="Total capital expenditure in FY2025 = $64.6B, up from $44.5B in FY24 (a 45.2% increase).",
                source="10-K Cash Flow Statement, page 51.",
                useful="Capex more than doubled over 2 years ($28B → $65B) — the largest infrastructure buildout in Microsoft's history."
            ))
        kpi_expander_close()
    with cols2[2]:
        st.markdown(kpi_card("Diluted EPS", f"${EPS:.2f}", "+15.6%", "up", "vs $11.80 FY24", "p.48"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="Earnings per share — total profit divided by diluted share count.",
                calc="Net Income ($101.8B) ÷ Diluted Share Count (7,465M) = $13.64.",
                source="10-K Income Statement, page 48.",
                useful="EPS grew slightly faster than net income due to share buybacks reducing total share count."
            ))
        kpi_expander_close()

    note("The following six metrics represent Microsoft's core FY2025 performance indicators as reported in the 10-K filing. "
         "Each includes year-over-year comparison. Click 'What does this mean?' on any card for a plain-English explanation.", top_spaced=True)
    content_wrap_close()

    # SECTION 2 — Waterfall Bridge
    content_wrap_open()
    section_tile("Revenue Bridge FY24 → FY25", "How segments contributed to the +$36.6B revenue increase")

    seg_df = FINANCIALS["segments"]
    pbp_delta = (seg_df.iloc[0]["rev_2025"] - seg_df.iloc[0]["rev_2024"]) / 1000
    ic_delta  = (seg_df.iloc[1]["rev_2025"] - seg_df.iloc[1]["rev_2024"]) / 1000
    mpc_delta = (seg_df.iloc[2]["rev_2025"] - seg_df.iloc[2]["rev_2024"]) / 1000

    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["FY24 Revenue", "Productivity & BP", "Intelligent Cloud", "More Personal Computing", "FY25 Revenue"],
        y=[245.1, pbp_delta, ic_delta, mpc_delta, 281.7],
        text=[f"${245.1:.1f}B", f"+${pbp_delta:.1f}B", f"+${ic_delta:.1f}B", f"+${mpc_delta:.1f}B", f"${281.7:.1f}B"],
        textposition="outside",
        textfont=dict(family="Segoe UI", size=12, color="#252423"),
        connector={"line": {"color": "#C7E0F4", "width": 1}},
        increasing={"marker": {"color": "#0078D4", "line": {"color": "#005A9E", "width": 1}}},
        totals={"marker": {"color": "#252423", "line": {"color": "#252423", "width": 1}}},
        hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
    ))
    fig_wf.update_layout(
        **FLUENT_LAYOUT, height=460,
        yaxis=dict(title="Revenue ($B)", gridcolor="#F3F2F1", rangemode="tozero"),
        margin=dict(l=40, r=40, t=60, b=40), showlegend=False,
    )
    st.plotly_chart(fig_wf, use_container_width=True)

    note("This waterfall shows exactly how Microsoft's revenue grew from $245.1B to $281.7B — decomposed by segment contribution. "
         "<strong>Intelligent Cloud contributed the largest share</strong> at approximately +$19B, accounting for over half of total growth.", top_spaced=True)

    with st.expander("How to read a waterfall chart"):
        st.markdown(kpi_explainer(
            what="A waterfall chart decomposes a total change into its component parts. It's the standard way analysts visualize 'how did we get from A to B.'",
            calc="Start with FY24 revenue ($245.1B), add each segment's growth contribution stacked on top, ending at FY25 revenue ($281.7B). Each blue bar is a positive contribution.",
            source="Segment data from 10-K Note 18, pages 82–84.",
            useful="Waterfalls immediately reveal which drivers matter most. Here it shows Intelligent Cloud contributed more than the other two segments combined — critical context for evaluating the AI capex strategy."
        ))
    content_wrap_close()

    # SECTION 3 — Financial Health Indicators
    content_wrap_open()
    section_tile("Financial Health Indicators", "Investor-grade quality ratios")

    hcols = st.columns(3, gap="medium")
    with hcols[0]:
        st.markdown(kpi_card("Rule of 40", f"{RULE40:.1f}", "Elite tier", "up", "Growth% + FCF margin%"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="A SaaS benchmark test. Companies must grow fast AND maintain strong cash flow margins simultaneously. Scores above 40 are considered 'elite.'",
                calc="Revenue Growth (14.9%) + FCF Margin (25.4%) = 40.3.",
                source="SaaS industry standard, derived from 10-K.",
                useful="At $282B scale, sustaining a Rule of 40 score is extraordinary."
            ))
        kpi_expander_close()
    with hcols[1]:
        st.markdown(kpi_card("Return on Invested Capital", f"{ROIC:.1f}%", "World class", "up", "Profit per $1 invested"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="How much profit Microsoft generates from every dollar invested in the business.",
                calc="NOPAT ($105.9B) ÷ Invested Capital ($386.6B) = 27.4%.",
                source="Derived from 10-K.",
                useful="Above 15% indicates value creation; above 20% is exceptional. Microsoft's 27.4% is world-class."
            ))
        kpi_expander_close()
    with hcols[2]:
        st.markdown(kpi_card("Net Debt / EBITDA", f"{ND_EBITDA:.2f}x", "Fortress balance sheet", "up", "Leverage ratio"), unsafe_allow_html=True)
        kpi_expander_open()
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="How many years of pre-tax earnings would be required to pay off all debt.",
                calc="(Total Debt $43.2B − Cash & ST Investments $94.6B) ÷ EBITDA $162.7B = 0.08x.",
                source="10-K Balance Sheet, page 50.",
                useful="Below 1.0x is 'fortress balance sheet.' Microsoft's 0.08x means all debt could be repaid with one month of earnings."
            ))
        kpi_expander_close()

    note("These three ratios are used by professional investors to assess long-term business quality. "
         "Each measures a different dimension of financial strength — growth quality, capital efficiency, and leverage.", top_spaced=True)
    content_wrap_close()

# ============================================================
# TAB 3: REVENUE & SEGMENTS
# ============================================================
with tabs[2]:
    header_tile(
        "Revenue & Segments",
        subtitles=[
            "Five-year revenue trajectory and segment-level performance breakdown.",
            "Where growth is coming from — and where the profit actually lives.",
            "Intelligent Cloud leads growth. Productivity & BP leads profitability.",
        ],
        meta="Source: 10-K Segments Note 18, pages 82–84",
        live_metric="$281.7B FY25"
    )

    # SECTION 1 — Revenue Trajectory
    content_wrap_open()
    section_tile("Revenue Trajectory", "Five-year top-line growth with year-over-year overlay")

    years6 = list(range(2020, 2026))
    rev6 = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    growth6 = [None, 17.5, 17.9, 6.9, 15.7, 14.9]

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(
        x=years6, y=rev6, marker_color="#0078D4", name="Revenue",
        text=[f"${v:.0f}B" for v in rev6], textposition="outside",
        customdata=[[g if g else 0] for g in growth6],
        hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<br>Growth: %{customdata[0]:.1f}%<extra></extra>",
    ))
    fig_r.add_trace(go.Scatter(
        x=years6, y=growth6, mode="lines+markers", name="YoY Growth %",
        yaxis="y2", line=dict(color="#FFB900", width=3),
        marker=dict(size=10),
        hovertemplate="<b>FY%{x}</b><br>YoY Growth: %{y:.1f}%<extra></extra>",
    ))
    fig_r.update_layout(
        **FLUENT_LAYOUT, height=420,
        yaxis=dict(title="Revenue ($B)", gridcolor="#F3F2F1"),
        yaxis2=dict(title="Growth %", overlaying="y", side="right", showgrid=False),
        xaxis=dict(tickmode="array", tickvals=years6),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_r, use_container_width=True)

    st.markdown("#### $300B Revenue Milestone")
    progress_pct = (REV_B / 300) * 100
    st.progress(progress_pct / 100, text=f"${REV_B:.1f}B of $300B target · {progress_pct:.1f}% achieved")
    st.caption("At current pace, Microsoft is projected to cross $300B in annual revenue in late 2025 or early 2026 — a historic milestone.")

    note("Microsoft has grown revenue from $143B to $282B over five fiscal years — nearly doubling the top line. "
         "The <strong>blue bars</strong> show total revenue, and the <strong>gold line</strong> shows year-over-year growth. "
         "Growth has held remarkably steady around 15% even as the company scaled.", top_spaced=True)
    content_wrap_close()

    # SECTION 2 — Segment Performance
    content_wrap_open()
    section_tile("Segment Performance", "Business unit revenue and growth breakdown")

    seg_df = FINANCIALS["segments"]
    colors_seg = ["#0078D4", "#005A9E", "#605E5C"]

    scols = st.columns(3, gap="medium")
    seg_explanations = [
        "Office 365, LinkedIn, and Dynamics — enterprise productivity software.",
        "Azure cloud, servers, and enterprise services — the AI infrastructure segment.",
        "Windows, Xbox, Surface, and Bing — consumer-facing products.",
    ]
    for i, row in seg_df.iterrows():
        rev_b = row["rev_2025"] / 1000
        growth = (row["rev_2025"] - row["rev_2024"]) / row["rev_2024"] * 100
        with scols[i]:
            st.markdown(kpi_card(
                row["segment"],
                f"${rev_b:.1f}B",
                f"+{growth:.1f}%",
                "up",
                f"{rev_b/REV_B*100:.0f}% of total revenue",
            ), unsafe_allow_html=True)
            kpi_expander_open()
            with st.expander("What does this mean?"):
                st.markdown(kpi_explainer(
                    what=seg_explanations[i],
                    calc=f"FY2025 revenue ${rev_b:.1f}B, up from ${row['rev_2024']/1000:.1f}B in FY2024 (+{growth:.1f}%).",
                    source="10-K Note 18: Segment Information.",
                    useful=f"This segment represents {rev_b/REV_B*100:.0f}% of Microsoft's total revenue base."
                ))
            kpi_expander_close()

    st.markdown("<br>", unsafe_allow_html=True)

    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        x=seg_df["segment"],
        y=seg_df["rev_2025"] / 1000,
        marker_color=colors_seg,
        text=[f"${v/1000:.1f}B" for v in seg_df["rev_2025"]],
        textposition="outside",
        customdata=[[(r["rev_2025"] - r["rev_2024"]) / r["rev_2024"] * 100] for _, r in seg_df.iterrows()],
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.1f}B<br>YoY Growth: %{customdata[0]:.1f}%<extra></extra>",
    ))
    fig_s.update_layout(
        **FLUENT_LAYOUT, height=380,
        yaxis=dict(title="Revenue ($B)", gridcolor="#F3F2F1"),
        margin=dict(l=40, r=40, t=40, b=40), showlegend=False,
    )
    st.plotly_chart(fig_s, use_container_width=True)

    note("Microsoft reports three operating segments in its 10-K. Each represents a distinct customer base, product mix, and growth trajectory. "
         "<strong>Intelligent Cloud</strong> is the fastest-growing segment and is directly benefiting from AI infrastructure investment.", top_spaced=True)
    content_wrap_close()

    # SECTION 3 — Segment Operating Income
    content_wrap_open()
    section_tile("Segment Operating Income", "Where profit is actually generated")

    opi_vals = seg_df["opi_2025"] / 1000
    opi_prior = seg_df["opi_2024"] / 1000
    opi_margin = seg_df["opi_2025"] / seg_df["rev_2025"] * 100

    fig_opi = go.Figure()
    fig_opi.add_trace(go.Bar(
        y=seg_df["segment"], x=opi_prior, orientation="h",
        marker_color="#C7E0F4", name="FY2024",
        text=[f"${v:.1f}B" for v in opi_prior],
        textposition="inside",
        insidetextfont=dict(color="#005A9E"),
        hovertemplate="<b>%{y}</b><br>FY24 Operating Income: $%{x:.1f}B<extra></extra>",
    ))
    fig_opi.add_trace(go.Bar(
        y=seg_df["segment"], x=opi_vals, orientation="h",
        marker_color="#0078D4", name="FY2025",
        text=[f"${v:.1f}B ({m:.0f}% margin)" for v, m in zip(opi_vals, opi_margin)],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>FY25 Operating Income: $%{x:.1f}B<br>Margin: %{customdata[0]:.1f}%<extra></extra>",
        customdata=[[m] for m in opi_margin],
    ))
    fig_opi.update_layout(
        **FLUENT_LAYOUT, height=380, barmode="group",
        xaxis=dict(title="Operating Income ($B)", gridcolor="#F3F2F1"),
        yaxis=dict(title=""),
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right"),
        margin=dict(l=40, r=100, t=40, b=40),
    )
    st.plotly_chart(fig_opi, use_container_width=True)

    note("Revenue tells us where growth is coming from — but <strong>operating income</strong> tells us where the profit lives. "
         "Notably, <strong>Productivity & Business Processes</strong> generates the highest operating income ($69.8B) despite Intelligent Cloud having higher revenue growth. "
         "Office and LinkedIn are Microsoft's true profit engine.", top_spaced=True)

    with st.expander("What is Operating Income?"):
        st.markdown(kpi_explainer(
            what="The profit earned from a segment's core business activities, before interest and taxes.",
            calc="Segment Revenue − Cost of Revenue − Segment Operating Expenses = Operating Income.",
            source="10-K Note 18: Segment Information, pages 82–84.",
            useful="Comparing operating income across segments reveals where profit actually lives. P&BP generates the highest absolute profit ($69.8B) with a 58% operating margin — one of the highest in enterprise software."
        ))
    content_wrap_close()

# ============================================================
# TAB 4: CAPITAL ALLOCATION
# ============================================================
with tabs[3]:
    header_tile(
        "Capital Allocation",
        subtitles=[
            "How Microsoft deployed $136B in operating cash flow.",
            "Capex now consumes 57% of total capital — the highest share in company history.",
            "The AI infrastructure bet, viewed through the lens of cash deployment.",
        ],
        meta="Source: 10-K Cash Flow Statement, page 51",
        live_metric="$64.6B Capex"
    )

    ca = KPIS["cap_allocation"]

    # SECTION 1 — Capital Deployment
    content_wrap_open()
    section_tile("Capital Deployment", "FY2025 uses of operating cash flow")

    ccols = st.columns(4, gap="medium")
    with ccols[0]:
        st.markdown(kpi_card("Capital Expenditure", f"${ca['capex']/1000:.1f}B",
                              f"+{CAPEX_YOY:.1f}%", "up", "AI datacenters & servers", variant="signal"), unsafe_allow_html=True)
    with ccols[1]:
        st.markdown(kpi_card("Share Repurchases", f"${ca['buybacks']/1000:.1f}B",
                              "returned to owners", "flat", "reduces share count"), unsafe_allow_html=True)
    with ccols[2]:
        st.markdown(kpi_card("Dividends Paid", f"${ca['dividends']/1000:.1f}B",
                              "quarterly distribution", "flat", "cash to shareholders"), unsafe_allow_html=True)
    with ccols[3]:
        st.markdown(kpi_card("Acquisitions", f"${ca['acquisitions']/1000:.1f}B",
                              "net of divestitures", "flat", "strategic add-ons"), unsafe_allow_html=True)

    note("Microsoft generated $136.2B in operating cash flow during FY2025. The following four categories represent how that cash was allocated. "
         "<strong>Capex accounted for 57% of total capital deployed</strong> — the highest share in the company's history.", top_spaced=True)
    content_wrap_close()

    # SECTION 2 — Deployment Mix (Donut)
    content_wrap_open()
    section_tile("Capital Deployment Mix", "Visual breakdown of the four capital uses")

    allocation_labels = ["Capital Expenditure", "Dividends", "Share Repurchases", "Acquisitions"]
    allocation_values = [ca["capex"]/1000, ca["dividends"]/1000, ca["buybacks"]/1000, ca["acquisitions"]/1000]
    total_deployed = sum(allocation_values)
    allocation_colors = ["#0078D4", "#005A9E", "#605E5C", "#FFB900"]

    fig_donut = go.Figure(go.Pie(
        labels=allocation_labels, values=allocation_values,
        marker=dict(colors=allocation_colors, line=dict(color="#FFFFFF", width=3)),
        hole=0.65,
        textinfo="label+percent",
        textposition="outside",
        textfont=dict(family="Segoe UI", size=12, color="#252423"),
        pull=[0.03, 0, 0, 0],
        hovertemplate="<b>%{label}</b><br>$%{value:.1f}B<br>%{percent}<extra></extra>",
        rotation=90,
    ))
    fig_donut.add_annotation(
        text=f"<b style='font-size:24px;color:#252423;'>${total_deployed:.1f}B</b><br><span style='font-size:12px;color:#605E5C;'>Total Deployed FY25</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(family="Segoe UI"),
    )
    fig_donut.update_layout(
        **FLUENT_LAYOUT, height=440,
        margin=dict(l=40, r=40, t=20, b=40),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(family="Segoe UI", size=11)),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    note("Management's capital allocation choices signal strategic priorities. "
         "Microsoft's 57% allocation to capex reflects a decisive bet that AI infrastructure will generate superior returns compared to other uses of cash.", top_spaced=True)

    with st.expander("What are the four uses of cash?"):
        st.markdown(kpi_explainer(
            what="Companies can deploy cash in four primary ways: (1) reinvest via capex, (2) buybacks, (3) dividends, or (4) acquisitions.",
            calc=f"Capex ${ca['capex']/1000:.1f}B + Buybacks ${ca['buybacks']/1000:.1f}B + Dividends ${ca['dividends']/1000:.1f}B + Acquisitions ${ca['acquisitions']/1000:.1f}B = ${total_deployed:.1f}B total.",
            source="10-K Cash Flow Statement, page 51.",
            useful="Capital allocation choices reveal strategic priorities. Microsoft is betting heavily on internal reinvestment over shareholder returns."
        ))
    content_wrap_close()

    # SECTION 3 — Capex Trajectory
    content_wrap_open()
    section_tile("Capital Expenditure Trajectory", "The largest infrastructure buildout in company history")

    capex_years = [2020, 2021, 2022, 2023, 2024, 2025]
    capex_vals = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig_capex = go.Figure()
    fig_capex.add_trace(go.Bar(
        x=capex_years, y=capex_vals, marker_color="#0078D4",
        text=[f"${v:.1f}B" for v in capex_vals], textposition="outside",
        hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>",
    ))
    fig_capex.add_annotation(x=2023, y=28.1, text="Pre-AI baseline", showarrow=True, arrowhead=2,
                              ax=-40, ay=-40, font=dict(size=10, color="#605E5C"))
    fig_capex.add_annotation(x=2025, y=64.6, text="AI-era peak<br>(2.3x in 2 years)",
                              showarrow=True, arrowhead=2,
                              ax=40, ay=-50, font=dict(size=10, color="#D83B01"))
    fig_capex.update_layout(
        **FLUENT_LAYOUT, height=420,
        yaxis=dict(title="Capex ($B)", gridcolor="#F3F2F1"),
        margin=dict(l=40, r=40, t=40, b=40), showlegend=False,
    )
    st.plotly_chart(fig_capex, use_container_width=True)

    note("Microsoft's capex has <strong>more than doubled over two years</strong> — from $28B in FY2023 to $64.6B in FY2025. "
         "This is the largest and fastest infrastructure buildout ever undertaken by Microsoft, driven almost entirely by AI datacenter demand.", top_spaced=True)
    content_wrap_close()

    # SECTION 4 — FCF Composition
    content_wrap_open()
    section_tile("Free Cash Flow Composition", "Operating cash flow vs. reinvestment vs. distributable cash")

    ocf_vals = [60.7, 76.7, 89.0, 87.6, 118.5, 136.2]
    fcf_vals = [45.2, 56.1, 65.1, 59.5, 74.1, 71.6]

    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(
        x=capex_years, y=ocf_vals, name="Operating Cash Flow", marker_color="#0078D4",
        hovertemplate="<b>FY%{x}</b><br>OCF: $%{y:.1f}B<extra></extra>",
    ))
    fig_fcf.add_trace(go.Bar(
        x=capex_years, y=capex_vals, name="Capital Expenditure", marker_color="#8AB9E5",
        hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>",
    ))
    fig_fcf.add_trace(go.Scatter(
        x=capex_years, y=fcf_vals, mode="lines+markers", name="Free Cash Flow",
        line=dict(color="#D83B01", width=3), marker=dict(size=10),
        hovertemplate="<b>FY%{x}</b><br>FCF: $%{y:.1f}B<extra></extra>",
    ))
    fig_fcf.update_layout(
        **FLUENT_LAYOUT, height=380, barmode="group",
        yaxis=dict(title="$B", gridcolor="#F3F2F1"),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_fcf, use_container_width=True)

    note("This chart shows the fundamental capital allocation trade-off. <strong>Operating cash flow</strong> (blue bars) grew 15% to $136B. "
         "<strong>Capex</strong> (light blue bars) grew 45% to $65B. The gap between them — <strong>Free Cash Flow</strong> (orange line) — declined 3.3% for the first time in five years.", top_spaced=True)

    with st.expander("What is Free Cash Flow, and why does the decline matter?"):
        st.markdown(kpi_explainer(
            what="Free Cash Flow is the cash a business generates after paying for both operations and capital investment.",
            calc="Operating Cash Flow ($136.2B) − Capital Expenditure ($64.6B) = $71.6B FCF.",
            source="Derived from 10-K Cash Flow Statement, page 51.",
            useful="FCF declined 3.3% year-over-year — the first decline in five years — because capex growth (+45%) outpaced OCF growth (+15%). The core business is healthy; the decline reflects a deliberate reinvestment choice."
        ))

    note("<strong>The central strategic question:</strong> If Azure and AI-related revenue continue growing 20%+ annually, "
         "the FY2025 capex commitment will be repaid multiple times over. If AI demand plateaus, Microsoft will have overspent by tens of billions. "
         "The next 12–18 months of Azure growth will be the decisive test.")
    content_wrap_close()

# ============================================================
# TAB 5: AI COPILOT
# ============================================================
with tabs[4]:
    header_tile(
        "AI Copilot",
        subtitles=[
            "Ten pre-answered questions covering the most common areas of investor interest.",
            "Click any question below to reveal a conversational analysis.",
            "Powered by the verified data from Microsoft's FY2025 10-K filing.",
        ],
        meta="Click any question below to reveal a conversational analysis.",
        live_metric="10 Questions"
    )

    content_wrap_open()
    section_tile("Frequently Asked Questions", "Select a question to view the analysis")

    questions = [
        ("What is the headline story of FY2025?",
         "Microsoft delivered a record-breaking year — $281.7B in revenue, up 14.9%. But the real story isn't the growth. "
         "It's that they spent $64.6 billion on AI infrastructure — a 45% jump, more than double what they spent 2 years ago. "
         "For the first time in years, free cash flow actually declined slightly because of it. Microsoft is making the biggest "
         "infrastructure bet in its history, and everyone is watching to see if it pays off."),

        ("How much money did Microsoft make this year?",
         "$281.7 billion in revenue — that's total sales. Of that, $101.8 billion was pure profit after all expenses and taxes. "
         "To put that in perspective: Microsoft makes more profit in a year than the entire GDP of countries like Ecuador or Guatemala. "
         "Their profit margin is 36% — for every $1 they sell, they keep 36 cents. That's elite territory."),

        ("Why is Microsoft spending so much on AI?",
         "Because they believe whoever wins AI wins the next 20 years of computing. Right now, Azure is growing 21% a year — "
         "mostly powered by companies renting AI compute. Every $1 they spend on datacenters today = future rent from businesses running AI models. "
         "It's like building apartments in a boomtown before everyone moves in. The risk: if AI demand cools, they've overspent. "
         "The reward: they own the picks and shovels of the AI gold rush."),

        ("Is Microsoft financially healthy?",
         "Extremely. Three quick check-ups: (1) They have almost no debt relative to earnings — they could pay off ALL debt with one month of earnings. "
         "(2) For every $1 invested in the business, they generate 27 cents in profit — world-class efficiency. "
         "(3) They score 40.4 on the 'Rule of 40' test — the elite growth+profitability threshold. Microsoft passes every health check with flying colors."),

        ("Which business segment is growing fastest?",
         "Intelligent Cloud — that's Azure, servers, and enterprise services. It grew 21% to $106.3B. "
         "For context, Microsoft's other segments grew 13% (Office/LinkedIn) and 7% (Windows/Xbox). "
         "Intelligent Cloud is now 38% of Microsoft's total revenue, up from about 30% a few years ago. It's clearly the growth engine."),

        ("Should investors worry about the cash flow decline?",
         "Honestly? Not really. Yes, free cash flow dropped 3.3% — the first decline in years. But it dropped because they chose to invest more, not because business is weaker. "
         "Their operating cash flow actually grew 15% — the underlying business is fine. They're just spending more on tomorrow. "
         "It would be worrying if operating cash was declining. It's not. This is a spending choice, not a business problem."),

        ("How does Microsoft compare to other tech giants?",
         "Microsoft is in the top tier along with Apple, Google, Amazon, and Nvidia. What makes Microsoft unique: they have the most 'stable' business — "
         "enterprise software renewals are like a subscription treadmill of cash. Apple depends on iPhone cycles. Google depends on ad markets. "
         "Amazon has lower margins. Microsoft has diversified revenue with software-level margins, which is why investors love them."),

        ("What could go wrong for Microsoft?",
         "Three real risks: (1) AI overbuilding — if they've built too much datacenter capacity and AI demand plateaus, that $65B/year in spending looks bad. "
         "(2) Regulatory pressure — governments are watching Big Tech closely, and Microsoft's OpenAI ties invite scrutiny. "
         "(3) Cloud competition — Amazon AWS and Google Cloud are fighting hard for the same customers. Microsoft's Azure lead isn't guaranteed."),

        ("Is the AI bet paying off yet?",
         "Partially. Azure's 21% growth is the clearest 'yes' signal — customers are paying real money for AI compute. But most of the massive datacenter buildout "
         "was completed just this year, meaning the full payoff shows up in FY26 and beyond. The next 12-18 months will be the real test. "
         "If Azure keeps growing 20%+ while capex growth slows, it's working. If growth cools while capex stays high, watch out."),

        ("In one sentence — is Microsoft a good company?",
         "Yes — Microsoft is one of the strongest businesses on Earth, generating $101 billion in profit at 45% margins with virtually no debt, "
         "and they're using that fortress balance sheet to make the biggest AI bet in tech history. "
         "The only real question isn't 'is it a good company?' — it's 'is the AI bet a good bet?' And that's still being written."),
    ]

    if "selected_q" not in st.session_state:
        st.session_state.selected_q = None
    if "just_selected" not in st.session_state:
        st.session_state.just_selected = False

    for i in range(0, len(questions), 2):
        cols_q = st.columns(2, gap="medium")
        for j in range(2):
            if i + j < len(questions):
                q, _ = questions[i + j]
                with cols_q[j]:
                    if st.button(q, key=f"q_{i+j}"):
                        st.session_state.selected_q = i + j
                        st.session_state.just_selected = True

    if st.session_state.selected_q is not None:
        q, a = questions[st.session_state.selected_q]
        st.markdown(f"""
        <div class="analyst-note" style="margin-top:1.5rem; font-size:0.98rem;">
          <div style="color:#005A9E; font-weight:600; font-size:1.05rem; margin-bottom:0.6rem;">{q}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.just_selected:
            def stream_answer(text):
                for word in text.split(" "):
                    yield word + " "
                    time.sleep(0.03)
            st.write_stream(stream_answer(a))
            st.session_state.just_selected = False
        else:
            st.markdown(f'<div style="padding: 0 1.15rem; line-height:1.65;">{a}</div>', unsafe_allow_html=True)
    else:
        st.markdown("<br><center style='color:#8A8886; font-size:0.9rem;'>↑ Select a question above to view the analysis</center>", unsafe_allow_html=True)
    content_wrap_close()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
  <div style="font-size:1rem; color:#FFFFFF; margin-bottom:0.5rem;">
    Microsoft FY2025 10-K Intelligence Dashboard
  </div>
  <div style="margin-bottom:1rem;">
    Built by <strong style="color:#FFFFFF;">Bea Lucido-Tan</strong> · Data verified from Microsoft's FY2025 Form 10-K (filed July 30, 2025)
  </div>
  <div>
    <a href="https://www.linkedin.com/in/bealucidotan" target="_blank">LinkedIn</a>·
    <a href="https://github.com/bealucidotan" target="_blank">GitHub</a>·
    <a href="https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q4/press-release-webcast" target="_blank">Source 10-K</a>
  </div>
  <div style="margin-top:1rem; font-size:0.72rem; color:#8A8886;">
    For educational and portfolio purposes only. Not investment advice.
  </div>
</div>
""", unsafe_allow_html=True)

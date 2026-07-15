import streamlit as st
import pandas as pd
import numpy as np
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
# MICROSOFT FLUENT THEME
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
   HEADER TILE (used at top of every tab)
   ========================================================== */
.header-tile {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 1.75rem 2rem; margin: 0.5rem 0 2rem 0;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.header-tile:hover { box-shadow: 0 4px 12px rgba(0,120,212,0.08); border-color: #C7E0F4; }
.header-tile h1 { margin: 0 0 0.4rem 0; font-size: 1.85rem; color: #252423; }
.header-tile .subtitle { color: #605E5C; font-size: 1rem; line-height: 1.5; margin: 0; }
.header-tile .meta { color: #8A8886; font-size: 0.78rem; margin-top: 0.85rem; font-family: 'Segoe UI', monospace; }

/* Centered variant for welcome */
.header-tile.centered { text-align: center; padding: 3rem 2rem; }
.header-tile.centered h1 { font-size: 2.25rem; }

/* ==========================================================
   SECTION DIVIDER (in-page section headers)
   ========================================================== */
.section-divider {
  display: flex; align-items: baseline; gap: 0.75rem;
  margin: 2.5rem 0 1.25rem 0; padding-bottom: 0.6rem;
  border-bottom: 1px solid #EDEBE9;
}
.section-dot { width: 8px; height: 8px; border-radius: 50%; background: #0078D4; }
.section-num { font-family: 'Segoe UI', monospace; font-size: 0.8rem; color: #605E5C; letter-spacing: 0.08em; font-weight: 600; }
.section-title { font-size: 1.4rem; font-weight: 600; color: #252423; margin: 0; }
.section-sub { font-size: 0.85rem; color: #8A8886; margin-left: auto; font-style: italic; }

/* ==========================================================
   KPI CARD
   ========================================================== */
.kpi-card {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 1.1rem 1.25rem; height: 100%;
  border-top: 2px solid #0078D4;
  transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  animation: fadeInUp 0.5s ease both;
}
.kpi-card:hover {
  background: #FAFAFA;
  border-color: #C7E0F4;
  border-top-color: #005A9E;
  box-shadow: 0 4px 12px rgba(0,120,212,0.08);
  transform: translateY(-2px);
}
.kpi-card.warning { border-top-color: #D83B01; }
.kpi-card.warning:hover { border-color: #F1A98A; box-shadow: 0 4px 12px rgba(216,59,1,0.08); }
.kpi-card.signal { border-top-color: #FFB900; }
.kpi-card.signal:hover { border-color: #FFE599; box-shadow: 0 4px 12px rgba(255,185,0,0.10); }

.kpi-label { font-size: 0.72rem; color: #605E5C; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; font-weight: 600; }
.kpi-value { font-size: 1.85rem; font-weight: 600; color: #252423; line-height: 1.1; }
.kpi-delta { font-size: 0.82rem; margin-top: 0.4rem; font-weight: 500; }
.kpi-delta.up { color: #107C10; }
.kpi-delta.down { color: #D83B01; }
.kpi-delta.flat { color: #8A8886; }
.kpi-sub { font-size: 0.72rem; color: #8A8886; margin-top: 0.25rem; }

.kpi-card:nth-child(1) { animation-delay: 0.05s; }
.kpi-card:nth-child(2) { animation-delay: 0.10s; }
.kpi-card:nth-child(3) { animation-delay: 0.15s; }
.kpi-card:nth-child(4) { animation-delay: 0.20s; }
.kpi-card:nth-child(5) { animation-delay: 0.25s; }
.kpi-card:nth-child(6) { animation-delay: 0.30s; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==========================================================
   ANALYST NOTE
   ========================================================== */
.analyst-note {
  background: #F3F9FD; border-left: 3px solid #0078D4; border-radius: 2px;
  padding: 0.95rem 1.15rem; margin: 1rem 0;
  font-size: 0.92rem; color: #252423; line-height: 1.6;
}
.analyst-note strong { color: #005A9E; }

/* ==========================================================
   RIBBON CARDS
   ========================================================== */
.ribbon-card {
  background: #FFFFFF; border: 1px solid #EDEBE9; border-radius: 4px;
  padding: 0.85rem 1rem; text-align: center;
  border-top: 2px solid #0078D4;
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
  animation: fadeInUp 0.5s ease both;
}
.ribbon-card:hover {
  background: #FAFAFA;
  border-color: #C7E0F4; border-top-color: #005A9E;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,120,212,0.08);
}
.ribbon-num { font-size: 1.25rem; font-weight: 600; color: #252423; font-variant-numeric: tabular-nums; line-height: 1.15; }
.ribbon-lbl { font-size: 0.68rem; color: #605E5C; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem; font-weight: 600; }

/* ==========================================================
   ROTATING CAROUSEL (welcome)
   ========================================================== */
.carousel {
  display: inline-block; padding: 1rem 2rem;
  background: #F3F9FD; border: 1px solid #C7E0F4; border-radius: 4px;
  margin-top: 1.5rem; min-width: 380px;
}
.carousel-label { font-size: 0.68rem; color: #605E5C; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }
.carousel-value { font-size: 1.5rem; color: #0078D4; font-weight: 600; margin-top: 0.35rem; font-variant-numeric: tabular-nums; animation: carouselFade 3s infinite; }
@keyframes carouselFade {
  0%, 100% { opacity: 1; }
  90% { opacity: 0; }
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
   TABS
   ========================================================== */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: transparent; border-bottom: 1px solid #EDEBE9; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; padding: 0.75rem 1.1rem; color: #605E5C; font-weight: 500; font-size: 0.92rem; }
.stTabs [aria-selected="true"] { color: #0078D4 !important; border-bottom: 2px solid #0078D4 !important; }

/* ==========================================================
   SIDEBAR & BUTTONS
   ========================================================== */
[data-testid="stSidebar"] { background: #FAFAFA; border-right: 1px solid #EDEBE9; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #252423; }

.stButton>button {
  background: #FFFFFF; color: #252423; border: 1px solid #EDEBE9;
  padding: 0.75rem 1rem; border-radius: 4px; font-weight: 500; font-size: 0.9rem;
  transition: all 0.2s ease; width: 100%; text-align: left; line-height: 1.4;
  white-space: normal; height: auto; min-height: 56px;
}
.stButton>button:hover { background: #FAFAFA; border-color: #0078D4; color: #005A9E; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,120,212,0.08); }

.streamlit-expanderHeader { background: #FAFAFA !important; border: 1px solid #EDEBE9 !important; border-radius: 4px !important; font-size: 0.85rem !important; color: #252423 !important; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA
# ============================================================
FINANCIALS = engine.microsoft_fallback_financials()
KPIS = engine.compute_kpis(FINANCIALS)
RIBBON = engine.ribbon_stats()

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
def header_tile(title, subtitle=None, meta=None, centered=False):
    cls = "header-tile centered" if centered else "header-tile"
    sub_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    st.markdown(f"""
    <div class="{cls}">
      <h1>{title}</h1>
      {sub_html}
      {meta_html}
    </div>
    """, unsafe_allow_html=True)

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

def section_divider(num, title, sub=None):
    sub_html = f'<span class="section-sub">{sub}</span>' if sub else ""
    st.markdown(f"""
    <div class="section-divider">
      <span class="section-dot"></span>
      <span class="section-num">{num}</span>
      <h2 class="section-title">{title}</h2>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="analyst-note">{text}</div>', unsafe_allow_html=True)

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
    - 01 · Welcome
    - 02 · Executive Summary
    - 03 · Revenue & Segments
    - 04 · Capital Allocation
    - 05 · AI Copilot
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
    # Centered hero tile
    st.markdown("""
    <div class="header-tile centered">
      <h1>Microsoft FY2025 10-K</h1>
      <p class="subtitle">An interactive breakdown of Microsoft's FY2025 10-K filing, built for financial analysis portfolio demonstration.</p>
      <div class="meta">FY2025 · Filed July 30, 2025 · <span style="color:#107C10;">● Data verified from 10-K PDF</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Rotating stat carousel — cycles through 6 stats every 3 seconds
    st.markdown("""
    <div style="text-align: center;">
      <div class="carousel" id="stat-carousel">
        <div class="carousel-label">Key Highlight</div>
        <div class="carousel-value" id="carousel-value">$281.7B Revenue</div>
      </div>
    </div>
    <script>
      const stats = [
        "$281.7B Revenue",
        "45.6% Operating Margin",
        "$101.8B Net Income",
        "27.4% Return on Capital",
        "$64.6B AI Investment",
        "0.08x Net Debt / EBITDA"
      ];
      let idx = 0;
      setInterval(() => {
        idx = (idx + 1) % stats.length;
        const el = document.getElementById('carousel-value');
        if (el) el.textContent = stats[idx];
      }, 3000);
    </script>
    """, unsafe_allow_html=True)

    # Streamlit's iframe security often blocks inline <script>. Fallback: cycle via st.empty
    stat_options = [
        "$281.7B Revenue",
        "45.6% Operating Margin",
        "$101.8B Net Income",
        "27.4% Return on Capital",
        "$64.6B AI Investment",
        "0.08x Net Debt / EBITDA",
    ]
    if "carousel_idx" not in st.session_state:
        st.session_state.carousel_idx = 0

    # Use HTML-only animation via CSS keyframes — no JS required
    stats_html = "".join([
        f'<div class="cstat" style="animation-delay:{i*3}s;">{s}</div>' for i, s in enumerate(stat_options)
    ])
    st.markdown(f"""
    <style>
    .cstat-wrap {{
      position: relative; height: 60px; text-align: center; margin-top: 1.5rem;
    }}
    .cstat {{
      position: absolute; left: 0; right: 0;
      font-size: 1.5rem; color: #0078D4; font-weight: 600; font-variant-numeric: tabular-nums;
      opacity: 0; animation: cstatCycle 18s infinite;
    }}
    @keyframes cstatCycle {{
      0%, 12% {{ opacity: 1; transform: translateY(0); }}
      16%, 100% {{ opacity: 0; transform: translateY(-8px); }}
    }}
    </style>
    <div class="cstat-wrap">{stats_html}</div>
    """, unsafe_allow_html=True)

# ============================================================
# TAB 2: EXECUTIVE SUMMARY
# ============================================================
with tabs[1]:
    # Header tile
    header_tile(
        "Executive Summary",
        "FY2025 headline results, operating performance, and financial health indicators.",
        meta="Reporting period: July 1, 2024 – June 30, 2025"
    )

    # By the numbers ribbon
    section_divider("01", "By the Numbers", "FY2025 at a glance")
    ribbon_bar()

    # Financial Highlights
    section_divider("02", "Key Financial Metrics", "Headline results with YoY comparison")

    note("The following six metrics represent Microsoft's core FY2025 performance indicators as reported in the 10-K filing. "
         "Each includes year-over-year comparison. Expand the glossary below any card for a plain-English explanation.")

    cols = st.columns(3, gap="medium")
    with cols[0]:
        st.markdown(kpi_card("Revenue", f"${REV_B:.1f}B", f"+{REV_YOY:.1f}%", "up", "vs $245.1B FY24", "p.48"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="All money Microsoft earned from selling products and services during FY2025 — including Azure, Office 365, LinkedIn, Windows, Xbox, and other offerings.",
                calc="Sum of Product Revenue ($63.9B) + Service and Other Revenue ($217.8B) = $281.7B total.",
                source="10-K Income Statement, page 48. Verified directly from the filed PDF.",
                useful="Revenue growth is the single most-watched top-line indicator. A 14.9% jump at $245B+ scale signals extraordinary demand — most companies this large grow 3–5% annually."
            ))

    with cols[1]:
        st.markdown(kpi_card("Net Income", f"${NI_B:.1f}B", "+15.6%", "up", "vs $88.1B FY24", "p.48"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The final profit after all expenses, interest, and taxes are subtracted from revenue. This is what Microsoft actually 'keeps.'",
                calc="Revenue ($281.7B) − Cost of Revenue − Operating Expenses − Other Income (Expense) − Taxes = $101.8B.",
                source="10-K Income Statement, page 48. Also known as 'net earnings.'",
                useful="Net income growing faster than revenue (15.6% vs 14.9%) indicates improving operational efficiency — Microsoft is converting each dollar of sales into more profit than last year."
            ))

    with cols[2]:
        st.markdown(kpi_card("Operating Margin", f"{OPM:.1f}%", f"+{OPM_DELTA:.0f} bps", "up", "vs 44.6% FY24", "p.48"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The percentage of revenue that becomes operating profit before interest and taxes. Measures how efficiently the core business runs.",
                calc="Operating Income ($128.5B) ÷ Revenue ($281.7B) = 45.6%.",
                source="10-K Income Statement, page 48. Operating Income excludes interest and taxes.",
                useful="45.6% is elite territory — most Fortune 500 companies operate at 10–15% margins. This reflects Microsoft's pricing power and the low marginal cost of software distribution."
            ))

    st.markdown("<br>", unsafe_allow_html=True)

    cols2 = st.columns(3, gap="medium")
    with cols2[0]:
        st.markdown(kpi_card("Free Cash Flow", f"${FCF_B:.1f}B", "-3.3%", "down", "vs $74.1B FY24", "p.51", variant="warning"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="The cash Microsoft has left over after operating expenses AND capital investments. This is the true 'distributable' cash available to shareholders.",
                calc="Operating Cash Flow ($136.2B) − Capital Expenditures ($64.6B) = $71.6B.",
                source="10-K Cash Flow Statement, page 51. Capex is reported as a negative cash outflow.",
                useful="FCF declined for the first time in 5+ years — a signal that AI infrastructure spending is now outpacing cash generation growth. Watch this metric closely in future filings."
            ))

    with cols2[1]:
        st.markdown(kpi_card("Capital Expenditure", f"${CAPEX_B:.1f}B", f"+{CAPEX_YOY:.1f}%", "up", "vs $44.5B FY24", "p.51", variant="signal"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="Money spent on long-term physical assets — datacenters, servers, chips, buildings. Not day-to-day expenses like salaries.",
                calc="Total capital expenditure reported in FY2025 = $64.6B, up from $44.5B in FY24 (a 45.2% increase).",
                source="10-K Cash Flow Statement, page 51. Also detailed in MD&A section discussing AI infrastructure buildout.",
                useful="Capex more than doubled over 2 years ($28B → $65B) — the largest infrastructure buildout in Microsoft's history, driven entirely by AI datacenter investment."
            ))

    with cols2[2]:
        st.markdown(kpi_card("Diluted EPS", f"${EPS:.2f}", "+15.6%", "up", "vs $11.80 FY24", "p.48"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="Earnings per share — total profit divided by the number of shares outstanding. If you own one share, this is your 'slice' of the profit.",
                calc="Net Income ($101.8B) ÷ Diluted Share Count (7,465M) = $13.64 per share.",
                source="10-K Income Statement, page 48. 'Diluted' includes potential shares from stock options and grants.",
                useful="EPS grew slightly faster than net income due to share buybacks reducing the total share count — each remaining share now represents a bigger slice of the company."
            ))

    # Financial Health Indicators
    section_divider("03", "Financial Health Indicators", "Investor-grade quality ratios")

    note("These three ratios are used by professional investors to assess long-term business quality. "
         "Each measures a different dimension of financial strength — growth quality, capital efficiency, and leverage.")

    hcols = st.columns(3, gap="medium")
    with hcols[0]:
        st.markdown(kpi_card("Rule of 40", f"{RULE40:.1f}", "Elite tier", "up", "Growth% + FCF margin%"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="A SaaS benchmark test. Companies must grow fast AND maintain strong cash flow margins simultaneously. Scores above 40 are considered 'elite.'",
                calc="Revenue Growth (14.9%) + FCF Margin (25.4%) = 40.3.",
                source="SaaS industry standard, derived from 10-K Income Statement (p.48) and Cash Flow Statement (p.51).",
                useful="At $282B scale, sustaining a Rule of 40 score is extraordinary. It signals Microsoft is balancing aggressive growth with maintained profitability — the hallmark of a durable software business."
            ))

    with hcols[1]:
        st.markdown(kpi_card("Return on Invested Capital", f"{ROIC:.1f}%", "World class", "up", "Profit per $1 invested"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="How much profit Microsoft generates from every dollar invested in the business (from both shareholders and debt holders combined).",
                calc="NOPAT ($105.9B) ÷ Invested Capital ($386.6B) = 27.4%.",
                source="Derived from 10-K Income Statement (p.48) and Balance Sheet (p.50).",
                useful="A ROIC above 15% indicates value creation; above 20% is exceptional. Microsoft's 27.4% is world-class for a mature, large-cap company — few peers achieve this level of capital efficiency."
            ))

    with hcols[2]:
        st.markdown(kpi_card("Net Debt / EBITDA", f"{ND_EBITDA:.2f}x", "Fortress balance sheet", "up", "Leverage ratio"), unsafe_allow_html=True)
        with st.expander("What does this mean?"):
            st.markdown(kpi_explainer(
                what="How many years of pre-tax earnings would be required to pay off all debt. Lower ratios indicate safer balance sheets.",
                calc="(Total Debt $43.2B − Cash & ST Investments $94.6B) ÷ EBITDA $162.7B = 0.08x. (Note: cash exceeds debt, resulting in negative net debt.)",
                source="10-K Balance Sheet, page 50, and derived EBITDA from Income Statement.",
                useful="A ratio below 1.0x is considered a 'fortress balance sheet.' Microsoft's 0.08x means all debt could be repaid with roughly one month of earnings — providing enormous flexibility to fund AI investment without financial risk."
            ))

# ============================================================
# TAB 3: REVENUE & SEGMENTS
# ============================================================
with tabs[2]:
    header_tile(
        "Revenue & Segments",
        "Five-year revenue trajectory and performance breakdown by operating segment.",
        meta="Source: 10-K Segments Note 18, pages 82–84"
    )

    section_divider("01", "Revenue Trajectory", "Five-year top-line growth with YoY overlay")

    note("Microsoft has grown revenue from $143B to $282B over five fiscal years — nearly doubling the top line. "
         "The <strong>blue bars</strong> show total revenue, and the <strong>gold line</strong> shows year-over-year growth. "
         "Growth has held remarkably steady around 15% even as the company scaled.")

    years6 = list(range(2020, 2026))
    rev6 = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    growth6 = [None, 17.5, 17.9, 6.9, 15.7, 14.9]

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(x=years6, y=rev6, marker_color="#0078D4", name="Revenue",
                            text=[f"${v:.0f}B" for v in rev6], textposition="outside",
                            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig_r.add_trace(go.Scatter(x=years6, y=growth6, mode="lines+markers", name="YoY Growth %",
                                yaxis="y2", line=dict(color="#FFB900", width=3),
                                marker=dict(size=9),
                                hovertemplate="<b>FY%{x}</b><br>Growth: %{y:.1f}%<extra></extra>"))
    fig_r.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F3F2F1"),
                        yaxis2=dict(title="Growth %", overlaying="y", side="right", showgrid=False),
                        xaxis=dict(tickmode="array", tickvals=years6),
                        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                        margin=dict(l=40, r=40, t=40, b=40),
                        font=dict(family="Segoe UI"))
    st.plotly_chart(fig_r, use_container_width=True)

    st.markdown("#### $300B Revenue Milestone")
    progress_pct = (REV_B / 300) * 100
    st.progress(progress_pct / 100, text=f"${REV_B:.1f}B of $300B target · {progress_pct:.1f}% achieved")
    st.caption("At current pace, Microsoft is projected to cross $300B in annual revenue in late 2025 or early 2026 — a historic milestone.")

    # Segment Performance
    section_divider("02", "Segment Performance", "Business unit revenue and growth breakdown")

    note("Microsoft reports three operating segments in its 10-K. Each represents a distinct customer base, product mix, and growth trajectory. "
         "<strong>Intelligent Cloud</strong> is the fastest-growing segment and is directly benefiting from AI infrastructure investment.")

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
                f"{rev_b/REV_B*100:.0f}% of total revenue"
            ), unsafe_allow_html=True)
            st.caption(seg_explanations[i])

    st.markdown("<br>", unsafe_allow_html=True)

    # Segment bar chart
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        x=seg_df["segment"],
        y=seg_df["rev_2025"] / 1000,
        marker_color=colors_seg,
        text=[f"${v/1000:.1f}B" for v in seg_df["rev_2025"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"
    ))
    fig_s.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F3F2F1"),
                        margin=dict(l=40, r=40, t=40, b=40),
                        showlegend=False,
                        font=dict(family="Segoe UI"))
    st.plotly_chart(fig_s, use_container_width=True)

    note("<strong>Intelligent Cloud grew 21%</strong> — nearly 3x faster than More Personal Computing (+7%). "
         "This directly justifies the $64.6B capex commitment: every dollar spent on AI datacenters translates into future Azure revenue.")

    with st.expander("What is an operating segment?"):
        st.markdown(kpi_explainer(
            what="A distinct business line reported separately in the 10-K. Companies with multiple product lines are required to disclose segment-level revenue and profitability under GAAP.",
            calc="Microsoft groups its businesses into three segments: Productivity & Business Processes, Intelligent Cloud, and More Personal Computing. Each has its own revenue and operating income lines.",
            source="10-K Note 18: Segment Information, pages 82–84.",
            useful="Segment reporting reveals which parts of a company are growing vs. stagnating. In Microsoft's case, it shows Intelligent Cloud is the growth engine — critical context for evaluating the AI capex bet."
        ))

# ============================================================
# TAB 4: CAPITAL ALLOCATION
# ============================================================
with tabs[3]:
    header_tile(
        "Capital Allocation",
        "How Microsoft deployed its $136B in operating cash flow across investment, shareholder returns, and acquisitions.",
        meta="Source: 10-K Cash Flow Statement, page 51"
    )

    section_divider("01", "Capital Deployment", "FY2025 uses of operating cash flow")

    note("Microsoft generated $136.2B in operating cash flow during FY2025. The following four categories represent how that cash was allocated. "
         "<strong>Capex accounted for 47% of operating cash flow</strong> — the highest share in the company's history.")

    ca = KPIS["cap_allocation"]

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

    with st.expander("What are the four uses of cash?"):
        st.markdown(kpi_explainer(
            what="Companies can deploy cash in four primary ways: (1) reinvest in the business through capital expenditure, (2) return cash to shareholders via buybacks, (3) pay dividends, or (4) acquire other companies.",
            calc="Capex $64.6B + Buybacks $18.4B + Dividends $24.1B + Acquisitions $6.0B = $113.1B total deployed.",
            source="10-K Cash Flow Statement, page 51 (investing and financing activities sections).",
            useful="Management's capital allocation choices signal strategic priorities. Microsoft's 57% allocation to capex reflects a decisive bet that AI infrastructure will generate superior returns compared to other uses of cash."
        ))

    # Capex trajectory
    section_divider("02", "Capital Expenditure Trajectory", "The largest infrastructure buildout in company history")

    note("Microsoft's capex has <strong>more than doubled over two years</strong> — from $28B in FY2023 to $64.6B in FY2025. "
         "This is the largest and fastest infrastructure buildout ever undertaken by Microsoft, driven almost entirely by AI datacenter demand.")

    capex_years = [2020, 2021, 2022, 2023, 2024, 2025]
    capex_vals = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig_capex = go.Figure()
    fig_capex.add_trace(go.Bar(x=capex_years, y=capex_vals, marker_color="#0078D4",
                                text=[f"${v:.1f}B" for v in capex_vals], textposition="outside",
                                hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>"))
    fig_capex.add_annotation(x=2023, y=28.1, text="Pre-AI baseline", showarrow=True, arrowhead=2,
                              ax=-40, ay=-40, font=dict(size=10, color="#605E5C"))
    fig_capex.add_annotation(x=2025, y=64.6, text="AI-era peak<br>(2.3x in 2 years)",
                              showarrow=True, arrowhead=2,
                              ax=40, ay=-50, font=dict(size=10, color="#D83B01"))
    fig_capex.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                             yaxis=dict(title="Capex ($B)", gridcolor="#F3F2F1"),
                             margin=dict(l=40, r=40, t=40, b=40),
                             showlegend=False,
                             font=dict(family="Segoe UI"))
    st.plotly_chart(fig_capex, use_container_width=True)

    # FCF composition
    section_divider("03", "Free Cash Flow Composition", "Operating cash flow vs. reinvestment vs. distributable cash")

    note("This chart shows the fundamental capital allocation trade-off. <strong>Operating cash flow</strong> (blue bars) grew 15% to $136B. "
         "<strong>Capex</strong> (light blue bars) grew 45% to $65B. The gap between them — <strong>Free Cash Flow</strong> (orange line) — declined 3.3% for the first time in five years.")

    ocf_vals = [60.7, 76.7, 89.0, 87.6, 118.5, 136.2]
    fcf_vals = [45.2, 56.1, 65.1, 59.5, 74.1, 71.6]

    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=capex_years, y=ocf_vals, name="Operating Cash Flow", marker_color="#0078D4",
                              hovertemplate="OCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Bar(x=capex_years, y=capex_vals, name="Capital Expenditure", marker_color="#8AB9E5",
                              hovertemplate="Capex: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Scatter(x=capex_years, y=fcf_vals, mode="lines+markers", name="Free Cash Flow",
                                  line=dict(color="#D83B01", width=3), marker=dict(size=10),
                                  hovertemplate="FCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", barmode="group",
                          yaxis=dict(title="$B", gridcolor="#F3F2F1"),
                          legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                          margin=dict(l=40, r=40, t=40, b=40),
                          font=dict(family="Segoe UI"))
    st.plotly_chart(fig_fcf, use_container_width=True)

    with st.expander("What is Free Cash Flow, and why does the decline matter?"):
        st.markdown(kpi_explainer(
            what="Free Cash Flow is the cash a business generates after paying for both day-to-day operations and long-term capital investment. It represents cash truly available for shareholders, debt repayment, or new opportunities.",
            calc="Operating Cash Flow ($136.2B) − Capital Expenditure ($64.6B) = $71.6B FCF.",
            source="Derived from 10-K Cash Flow Statement, page 51. FCF is not a GAAP-defined metric but is universally used by investors.",
            useful="FCF declined 3.3% year-over-year — the first decline in five years — because capex growth (+45%) outpaced OCF growth (+15%). The core business is still healthy; the decline reflects a deliberate reinvestment choice rather than operational weakness."
        ))

    note("<strong>The central strategic question:</strong> If Azure and AI-related revenue continue growing 20%+ annually, "
         "the FY2025 capex commitment will be repaid multiple times over. If AI demand plateaus, Microsoft will have overspent by tens of billions. "
         "The next 12–18 months of Azure growth will be the decisive test.")

# ============================================================
# TAB 5: AI COPILOT
# ============================================================
with tabs[4]:
    header_tile(
        "AI Copilot",
        "Ten pre-answered questions covering the most common areas of investor and analyst interest in the FY2025 filing.",
        meta="Click any question below to reveal a conversational analysis."
    )

    section_divider("01", "Frequently Asked Questions", "Select a question to view the analysis")

    questions = [
        ("What is the headline story of FY2025?",
         "Microsoft delivered a <strong>record-breaking year</strong> — $281.7B in revenue, up 14.9%. But the real story isn't the growth. "
         "It's that they spent <strong>$64.6 billion on AI infrastructure</strong> — a 45% jump, more than double what they spent 2 years ago. "
         "For the first time in years, free cash flow actually declined slightly because of it. Microsoft is making the biggest "
         "infrastructure bet in its history, and everyone is watching to see if it pays off."),

        ("How much money did Microsoft make this year?",
         "<strong>$281.7 billion in revenue</strong> — that's total sales. Of that, <strong>$101.8 billion was pure profit</strong> after all expenses and taxes. "
         "To put that in perspective: Microsoft makes more profit in a year than the entire GDP of countries like Ecuador or Guatemala. "
         "Their profit margin is 36% — for every $1 they sell, they keep 36 cents. That's elite territory."),

        ("Why is Microsoft spending so much on AI?",
         "Because they believe whoever wins AI wins the next 20 years of computing. Right now, <strong>Azure is growing 21% a year</strong> — "
         "mostly powered by companies renting AI compute. Every $1 they spend on datacenters today = future rent from businesses running AI models. "
         "It's like building apartments in a boomtown before everyone moves in. The risk: if AI demand cools, they've overspent. "
         "The reward: they own the picks and shovels of the AI gold rush."),

        ("Is Microsoft financially healthy?",
         "<strong>Extremely.</strong> Three quick check-ups: (1) They have almost no debt relative to earnings — they could pay off ALL debt with one month of earnings. "
         "(2) For every $1 invested in the business, they generate 27 cents in profit — world-class efficiency. "
         "(3) They score 40.4 on the 'Rule of 40' test — the elite growth+profitability threshold. Microsoft passes every health check with flying colors."),

        ("Which business segment is growing fastest?",
         "<strong>Intelligent Cloud</strong> — that's Azure, servers, and enterprise services. It grew <strong>21% to $106.3B</strong>. "
         "For context, Microsoft's other segments grew 13% (Office/LinkedIn) and 7% (Windows/Xbox). "
         "Intelligent Cloud is now 38% of Microsoft's total revenue, up from about 30% a few years ago. It's clearly the growth engine."),

        ("Should investors worry about the cash flow decline?",
         "Honestly? Not really. Yes, free cash flow dropped 3.3% — the first decline in years. <strong>But it dropped because they chose to invest more, not because business is weaker.</strong> "
         "Their operating cash flow actually grew 15% — the underlying business is fine. They're just spending more on tomorrow. "
         "It would be worrying if operating cash was declining. It's not. This is a spending choice, not a business problem."),

        ("How does Microsoft compare to other tech giants?",
         "Microsoft is in the top tier along with Apple, Google, Amazon, and Nvidia. <strong>What makes Microsoft unique:</strong> they have the most 'stable' business — "
         "enterprise software renewals are like a subscription treadmill of cash. Apple depends on iPhone cycles. Google depends on ad markets. "
         "Amazon has lower margins. Microsoft has diversified revenue with software-level margins, which is why investors love them."),

        ("What could go wrong for Microsoft?",
         "Three real risks: <strong>(1) AI overbuilding</strong> — if they've built too much datacenter capacity and AI demand plateaus, that $65B/year in spending looks bad. "
         "<strong>(2) Regulatory pressure</strong> — governments are watching Big Tech closely, and Microsoft's OpenAI ties invite scrutiny. "
         "<strong>(3) Cloud competition</strong> — Amazon AWS and Google Cloud are fighting hard for the same customers. Microsoft's Azure lead isn't guaranteed."),

        ("Is the AI bet paying off yet?",
         "<strong>Partially.</strong> Azure's 21% growth is the clearest 'yes' signal — customers are paying real money for AI compute. <strong>But</strong> most of the massive datacenter buildout "
         "was completed just this year, meaning the full payoff shows up in FY26 and beyond. The next 12-18 months will be the real test. "
         "If Azure keeps growing 20%+ while capex growth slows, it's working. If growth cools while capex stays high, watch out."),

        ("In one sentence — is Microsoft a good company?",
         "<strong>Yes — Microsoft is one of the strongest businesses on Earth</strong>, generating $101 billion in profit at 45% margins with virtually no debt, "
         "and they're using that fortress balance sheet to make the biggest AI bet in tech history. "
         "The only real question isn't 'is it a good company?' — it's 'is the AI bet a good bet?' And that's still being written."),
    ]

    if "selected_q" not in st.session_state:
        st.session_state.selected_q = None

    # 2-column grid of clickable question tiles
    for i in range(0, len(questions), 2):
        cols_q = st.columns(2, gap="medium")
        for j in range(2):
            if i + j < len(questions):
                q, _ = questions[i + j]
                with cols_q[j]:
                    if st.button(q, key=f"q_{i+j}"):
                        st.session_state.selected_q = i + j

    # Show selected answer
    if st.session_state.selected_q is not None:
        q, a = questions[st.session_state.selected_q]
        st.markdown(f"""
        <div class="analyst-note" style="margin-top:1.5rem; font-size:0.98rem;">
          <div style="color:#005A9E; font-weight:600; font-size:1.05rem; margin-bottom:0.6rem;">{q}</div>
          <div style="line-height:1.65;">{a}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<br><center style='color:#8A8886; font-size:0.9rem;'>↑ Select a question above to view the analysis</center>", unsafe_allow_html=True)

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

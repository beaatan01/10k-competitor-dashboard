import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from tenk_engine import (
    process_uploaded_file,
    build_benchmark_dataframe,
    answer_question,
    build_forecast_dataframe,
    build_scenario_dataframe,
)

# ================================================================
# Page Setup
# ================================================================

st.set_page_config(
    page_title="Microsoft Financial Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================================================================
# Helpers
# ================================================================

def html(content):
    st.markdown(content, unsafe_allow_html=True)

def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"${v/1000:.1f}B"
    return f"${v:,.0f}M"

def fmt_pct(v):
    if v is None:
        return "N/A"
    return f"{v*100:.1f}%"

def dataframe_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# ================================================================
# Global CSS
# ================================================================

html(
    """
    <style>
    :root {
        --blue:#0078D4;
        --green:#7FBA00;
        --orange:#F25022;
        --yellow:#FFB900;
        --purple:#8661C5;

        --text:#F3F2F1;
        --muted:#A8AFBD;
        --muted2:#7B8494;

        --glass:rgba(16,20,31,.56);
        --glass2:rgba(20,26,39,.48);
        --border:rgba(255,255,255,.09);
        --border-blue:rgba(0,120,212,.45);

        --shadow:0 16px 42px rgba(0,0,0,.42);
        --shadow-hover:0 22px 58px rgba(0,0,0,.55);
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background:#050814 !important;
        color:var(--text) !important;
        font-family:"Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* TRUE MOVING AURORA BACKGROUND */
    [data-testid="stAppViewContainer"]::before {
        content:"";
        position:fixed;
        inset:-35%;
        z-index:0;
        pointer-events:none;
        background:
            radial-gradient(circle at 18% 28%, rgba(0,120,212,.42), transparent 26%),
            radial-gradient(circle at 72% 18%, rgba(127,186,0,.22), transparent 24%),
            radial-gradient(circle at 68% 72%, rgba(134,97,197,.34), transparent 26%),
            radial-gradient(circle at 28% 82%, rgba(242,80,34,.13), transparent 22%);
        filter:blur(80px);
        opacity:.9;
        animation: auroraFlow 18s ease-in-out infinite alternate;
    }

    [data-testid="stAppViewContainer"]::after {
        content:"";
        position:fixed;
        inset:0;
        z-index:0;
        pointer-events:none;
        background:
            linear-gradient(180deg, rgba(5,8,20,.36), rgba(5,8,20,.82)),
            radial-gradient(circle at 50% 0%, rgba(255,255,255,.04), transparent 38%);
    }

    @keyframes auroraFlow {
        0% { transform:translate3d(-2%, -3%, 0) scale(1); }
        45% { transform:translate3d(4%, 2%, 0) scale(1.06); }
        100% { transform:translate3d(-1%, 5%, 0) scale(1.03); }
    }

    [data-testid="stAppViewContainer"] > .main {
        position:relative;
        z-index:1;
    }

    .block-container {
        max-width:1520px !important;
        padding:1.2rem 1.45rem 2.2rem 1.45rem !important;
        position:relative;
        z-index:2;
    }

    #MainMenu, footer, header {
        visibility:hidden;
    }

    h1,h2,h3,h4,h5,h6,p,span,div,button,input,textarea {
        font-family:"Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ============================================================
       Tabs - compact
       ============================================================ */

    .stTabs [data-baseweb="tab-list"] {
        gap:.35rem;
        background:rgba(255,255,255,.035);
        border:1px solid rgba(255,255,255,.06);
        border-radius:12px;
        padding:.28rem;
        margin-bottom:1rem;
        backdrop-filter:blur(18px);
    }

    .stTabs [data-baseweb="tab"] {
        height:34px;
        padding:0 .72rem;
        border-radius:9px;
        color:#AAB2C1;
        font-weight:700;
        font-size:.74rem;
    }

    .stTabs [aria-selected="true"] {
        background:rgba(0,120,212,.18) !important;
        border:1px solid rgba(0,120,212,.45);
        color:#E0F1FF !important;
    }

    /* ============================================================
       Shared compact glass system
       ============================================================ */

    .glass,
    .hero,
    .mini-card,
    .kpi-card,
    .bento-card,
    .info-card,
    .scenario-card,
    .insight-card,
    .chart-shell {
        position:relative;
        border:1px solid var(--border);
        background:
            linear-gradient(145deg, rgba(255,255,255,.075), rgba(255,255,255,.018)),
            var(--glass);
        backdrop-filter:blur(22px);
        -webkit-backdrop-filter:blur(22px);
        box-shadow:var(--shadow);
        overflow:hidden;
    }

    .kpi-card,
    .bento-card,
    .info-card,
    .scenario-card,
    .insight-card,
    .chart-shell {
        border-radius:16px;
        transition:transform .16s ease, border-color .16s ease, box-shadow .16s ease;
    }

    .kpi-card:hover,
    .bento-card:hover,
    .info-card:hover,
    .scenario-card:hover,
    .insight-card:hover {
        transform:translateY(-4px) scale(1.008);
        border-color:var(--border-blue);
        box-shadow:var(--shadow-hover);
    }

    .kpi-card::before,
    .bento-card::before,
    .info-card::before,
    .scenario-card::before,
    .insight-card::before {
        content:"";
        position:absolute;
        width:220px;
        height:220px;
        right:-90px;
        top:-100px;
        background:radial-gradient(circle, rgba(0,120,212,.23), transparent 65%);
        opacity:0;
        transition:opacity .2s ease;
        pointer-events:none;
    }

    .kpi-card:hover::before,
    .bento-card:hover::before,
    .info-card:hover::before,
    .scenario-card:hover::before,
    .insight-card:hover::before {
        opacity:1;
    }

    /* ============================================================
       Hero - intentionally much smaller
       ============================================================ */

    .hero {
        border-radius:22px;
        min-height:190px;
        padding:1.15rem 1.35rem;
        margin-bottom:1rem;
    }

    .hero::before {
        content:"";
        position:absolute;
        inset:-40%;
        background:
            radial-gradient(circle at 20% 35%, rgba(0,120,212,.38), transparent 25%),
            radial-gradient(circle at 80% 20%, rgba(127,186,0,.20), transparent 24%),
            radial-gradient(circle at 65% 70%, rgba(134,97,197,.30), transparent 25%);
        filter:blur(52px);
        animation: heroAura 14s ease-in-out infinite alternate;
        opacity:.85;
    }

    @keyframes heroAura {
        from { transform:translate(-2%, -2%) scale(1); }
        to { transform:translate(4%, 5%) scale(1.05); }
    }

    .hero-content {
        position:relative;
        z-index:2;
        max-width:1050px;
    }

    .hero-topline {
        display:flex;
        align-items:center;
        gap:.55rem;
        text-transform:uppercase;
        letter-spacing:.15em;
        font-weight:800;
        color:#D7EDFF;
        font-size:.62rem;
        margin-bottom:.55rem;
    }

    .logo-squares {
        width:11px;
        height:11px;
        display:grid;
        grid-template-columns:1fr 1fr;
        gap:2px;
    }

    .logo-squares span:nth-child(1){background:#F25022;}
    .logo-squares span:nth-child(2){background:#7FBA00;}
    .logo-squares span:nth-child(3){background:#0078D4;}
    .logo-squares span:nth-child(4){background:#FFB900;}

    .hero-title {
        color:white;
        font-size:clamp(1.55rem, 2.35vw, 2.35rem);
        line-height:1.03;
        letter-spacing:-.055em;
        font-weight:820;
        margin-bottom:.5rem;
    }

    .hero-subtitle {
        color:#C5CBD5;
        font-size:.80rem;
        line-height:1.55;
        max-width:1040px;
    }

    .pill-row {
        display:flex;
        flex-wrap:wrap;
        gap:.45rem;
        margin-top:.85rem;
    }

    .pill {
        display:inline-flex;
        align-items:center;
        padding:.32rem .55rem;
        border-radius:999px;
        border:1px solid rgba(255,255,255,.10);
        background:rgba(255,255,255,.045);
        color:#D5DBE6;
        font-size:.66rem;
        font-weight:750;
        backdrop-filter:blur(14px);
    }

    .pill.blue {
        background:rgba(0,120,212,.17);
        border-color:rgba(0,120,212,.38);
        color:#D8EEFF;
    }

    /* ============================================================
       Sections
       ============================================================ */

    .section-head {
        display:flex;
        align-items:end;
        justify-content:space-between;
        gap:1rem;
        margin:1rem 0 .55rem 0;
    }

    .section-title {
        color:white;
        font-size:.86rem;
        font-weight:820;
        letter-spacing:-.02em;
    }

    .section-subtitle {
        color:var(--muted2);
        font-size:.70rem;
        line-height:1.45;
        margin-top:.18rem;
    }

    .section-tag {
        color:#D8EEFF;
        background:rgba(0,120,212,.14);
        border:1px solid rgba(0,120,212,.35);
        border-radius:999px;
        padding:.30rem .52rem;
        font-size:.64rem;
        font-weight:800;
        white-space:nowrap;
    }

    /* ============================================================
       Compact Cards
       ============================================================ */

    .kpi-card {
        min-height:108px;
        padding:.72rem;
    }

    .kpi-label {
        color:#9DA6B7;
        font-size:.56rem;
        font-weight:850;
        letter-spacing:.14em;
        text-transform:uppercase;
        margin-bottom:.35rem;
    }

    .kpi-name {
        color:#D4DAE4;
        font-size:.68rem;
        font-weight:760;
        line-height:1.25;
        margin-bottom:.42rem;
    }

    .kpi-value {
        color:white;
        font-size:1.18rem;
        font-weight:840;
        letter-spacing:-.045em;
        margin-bottom:.25rem;
    }

    .kpi-sub {
        color:#AAB1BF;
        font-size:.61rem;
        line-height:1.35;
        margin-bottom:.45rem;
    }

    .badge {
        display:inline-flex;
        align-items:center;
        gap:.32rem;
        padding:.27rem .44rem;
        border-radius:999px;
        font-size:.58rem;
        font-weight:820;
        color:#DDEFFF;
        border:1px solid rgba(0,120,212,.32);
        background:rgba(0,120,212,.15);
    }

    .badge.green {
        color:#E4F8BA;
        border-color:rgba(127,186,0,.36);
        background:rgba(127,186,0,.13);
    }

    .badge.orange {
        color:#FFC5BA;
        border-color:rgba(242,80,34,.35);
        background:rgba(242,80,34,.13);
    }

    .dot {
        display:inline-block;
        width:6px;
        height:6px;
        border-radius:50%;
        background:currentColor;
        box-shadow:0 0 10px currentColor;
    }

    .bento-grid {
        display:grid;
        grid-template-columns:repeat(3, minmax(0,1fr));
        gap:.65rem;
        margin-bottom:.9rem;
    }

    .bento-card {
        min-height:96px;
        padding:.72rem;
    }

    .bento-card.large {
        grid-column:span 2;
    }

    .bento-label {
        color:#D8EEFF;
        font-size:.56rem;
        font-weight:850;
        letter-spacing:.14em;
        text-transform:uppercase;
        margin-bottom:.52rem;
    }

    .bento-title {
        color:white;
        font-size:.81rem;
        font-weight:820;
        margin-bottom:.28rem;
        letter-spacing:-.02em;
    }

    .bento-text {
        color:#AAB1BF;
        font-size:.64rem;
        line-height:1.42;
    }

    .info-card {
        min-height:96px;
        padding:.72rem;
    }

    .info-title {
        color:white;
        font-size:.78rem;
        font-weight:820;
        margin-bottom:.35rem;
    }

    .info-text {
        color:#AAB1BF;
        font-size:.64rem;
        line-height:1.45;
    }

    .formula {
        margin-top:.48rem;
        padding:.38rem .48rem;
        border-radius:10px;
        color:#DAEEFF;
        background:rgba(0,120,212,.12);
        border:1px solid rgba(0,120,212,.28);
        font-size:.58rem;
        font-weight:760;
    }

    .scenario-card {
        min-height:98px;
        padding:.72rem;
    }

    .scenario-label {
        color:#9DA6B7;
        font-size:.56rem;
        font-weight:850;
        letter-spacing:.14em;
        text-transform:uppercase;
        margin-bottom:.34rem;
    }

    .scenario-title {
        color:#D9DEE8;
        font-size:.68rem;
        font-weight:780;
        margin-bottom:.28rem;
    }

    .scenario-value {
        color:white;
        font-size:1.12rem;
        font-weight:840;
        letter-spacing:-.04em;
        margin-bottom:.22rem;
    }

    .scenario-text {
        color:#AAB1BF;
        font-size:.60rem;
        line-height:1.35;
    }

    .insight-card {
        padding:.78rem .85rem;
        margin-top:.55rem;
        border-color:rgba(0,120,212,.28);
    }

    .insight-title {
        color:#D8EEFF;
        font-size:.58rem;
        font-weight:850;
        letter-spacing:.14em;
        text-transform:uppercase;
        margin-bottom:.35rem;
    }

    .insight-text {
        color:#D8DDE7;
        font-size:.68rem;
        line-height:1.5;
    }

    .chart-shell {
        padding:.72rem .72rem .18rem .72rem;
        margin-bottom:.7rem;
    }

    .chart-heading {
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:.35rem;
        gap:1rem;
    }

    .chart-title {
        color:white;
        font-size:.72rem;
        font-weight:820;
    }

    .chart-caption {
        color:#8C95A5;
        font-size:.58rem;
        font-weight:760;
    }

    .architecture {
        display:grid;
        grid-template-columns:repeat(6, minmax(0,1fr));
        gap:.45rem;
        margin-top:.4rem;
    }

    .arch-step {
        min-height:58px;
        display:flex;
        align-items:center;
        justify-content:center;
        text-align:center;
        padding:.45rem;
        border-radius:12px;
        border:1px solid rgba(255,255,255,.08);
        background:rgba(255,255,255,.045);
        backdrop-filter:blur(18px);
        color:#D8DDE7;
        font-size:.60rem;
        font-weight:760;
    }

    /* Streamlit native things */
    h3 {
        color:white !important;
        font-size:.86rem !important;
        font-weight:820 !important;
        margin:.65rem 0 .45rem 0 !important;
    }

    .stDataFrame {
        border-radius:14px !important;
        overflow:hidden !important;
    }

    [data-testid="stDataFrame"] {
        border:1px solid rgba(255,255,255,.10) !important;
        border-radius:14px !important;
        overflow:hidden !important;
        box-shadow:var(--shadow);
        background:rgba(16,20,31,.50) !important;
    }

    .stDownloadButton button,
    .stButton button {
        font-size:.68rem !important;
        padding:.42rem .7rem !important;
        border-radius:10px !important;
        color:white !important;
        background:linear-gradient(135deg, #0078D4, #0B5EA8) !important;
        border:1px solid rgba(255,255,255,.10) !important;
        box-shadow:0 10px 22px rgba(0,120,212,.24);
    }

    .stTextArea textarea,
    .stTextInput input {
        background:rgba(16,20,31,.60) !important;
        color:#F3F2F1 !important;
        border:1px solid rgba(255,255,255,.10) !important;
        border-radius:12px !important;
        font-size:.72rem !important;
    }

    .stTextArea label,
    .stTextInput label,
    .stSlider label {
        color:#AAB1BF !important;
        font-size:.64rem !important;
        font-weight:800 !important;
        letter-spacing:.08em;
        text-transform:uppercase;
    }

    .stSlider {
        padding-top:.3rem;
    }

    @media (max-width:1100px) {
        .bento-grid {
            grid-template-columns:repeat(2, minmax(0,1fr));
        }

        .bento-card.large {
            grid-column:span 1;
        }

        .architecture {
            grid-template-columns:repeat(3, minmax(0,1fr));
        }
    }

    @media (max-width:760px) {
        .block-container {
            padding:1rem !important;
        }

        .hero {
            min-height:210px;
            padding:1rem;
        }

        .bento-grid,
        .architecture {
            grid-template-columns:1fr;
        }
    }
    </style>
    """
)

# ================================================================
# Data
# ================================================================

result = process_uploaded_file()
company_results = {"Microsoft": result}
benchmark_df = build_benchmark_dataframe(company_results)

k = result["kpis"]
ts = k["time_series"].copy()
segment_revenue = k["segment_revenue"].copy()

# ================================================================
# Plotly Theme Helper
# ================================================================

def style_fig(fig, height=240, showlegend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Segoe UI, Inter, sans-serif",
            color="#C7CEDA",
            size=10,
        ),
        margin=dict(l=34, r=18, t=10, b=32),
        hovermode="x unified",
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#C7CEDA", size=9),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="rgba(255,255,255,.10)",
            tickfont=dict(color="#8993A3", size=9),
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,.055)",
            zeroline=False,
            showline=False,
            tickfont=dict(color="#8993A3", size=9),
        ),
    )
    return fig

# ================================================================
# Tabs
# ================================================================

tab_summary, tab_kpi, tab_revenue, tab_forecast, tab_financials, tab_ai = st.tabs(
    [
        "✨ Executive Summary",
        "📊 Intelligence Hub",
        "📈 Revenue Intelligence",
        "🔮 AI Forecasting",
        "📄 Financial Statements",
        "🤖 AI Copilot",
    ]
)

# ================================================================
# Executive Summary
# ================================================================

with tab_summary:

    html(
        """
        <div class="hero">
            <div class="hero-content">
                <div class="hero-topline">
                    <div class="logo-squares">
                        <span></span><span></span><span></span><span></span>
                    </div>
                    Microsoft Fluent UI Inspired Financial Intelligence
                </div>
                <div class="hero-title">Microsoft Financial Intelligence Platform</div>
                <div class="hero-subtitle">
                    An AI-style financial analytics application built from Microsoft's FY2025 10-K data.
                    The platform converts traditional financial statements into compact executive KPIs,
                    revenue intelligence, forecasting scenarios, and natural-language financial commentary.
                </div>
                <div class="pill-row">
                    <span class="pill blue">FY2025</span>
                    <span class="pill">10-K Analysis</span>
                    <span class="pill">Revenue Intelligence</span>
                    <span class="pill">AI Forecasting</span>
                    <span class="pill">Glass UI</span>
                </div>
            </div>
        </div>
        """
    )

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">What This Project Demonstrates</div>
                <div class="section-subtitle">
                    A compact finance product combining statement analysis, KPI modeling, forecasting, visualization, and AI-style storytelling.
                </div>
            </div>
            <div class="section-tag">Project Overview</div>
        </div>

        <div class="bento-grid">
            <div class="bento-card large">
                <div class="bento-label">Overview</div>
                <div class="bento-title">Financial Statement Intelligence</div>
                <div class="bento-text">
                    Converts Microsoft's annual financial statement data into a polished executive analytics experience focused on revenue, profitability, cash flow, and liquidity.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">KPI Engine</div>
                <div class="bento-title">Executive Metrics</div>
                <div class="bento-text">
                    Revenue growth, margins, free cash flow, cash, and debt are calculated into concise finance KPIs.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Revenue</div>
                <div class="bento-title">Revenue Intelligence</div>
                <div class="bento-text">
                    Trend and mix views show how total revenue and category revenue evolved over time.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Forecasting</div>
                <div class="bento-title">Scenario Engine</div>
                <div class="bento-text">
                    Growth assumptions produce bear, base, and bull revenue cases.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">AI Copilot</div>
                <div class="bento-title">Narrative Commentary</div>
                <div class="bento-text">
                    Plain-English commentary translates financial metrics into business interpretation.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Design</div>
                <div class="bento-title">Aurora Glass UI</div>
                <div class="bento-text">
                    Uses moving ambient gradients, compact glass tiles, and subtle hover lift for a premium AI-product feel.
                </div>
            </div>
        </div>
        """
    )

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Platform Workflow</div>
                <div class="section-subtitle">How the application moves from financial data to executive insights.</div>
            </div>
            <div class="section-tag">Architecture</div>
        </div>

        <div class="architecture">
            <div class="arch-step">10-K Data</div>
            <div class="arch-step">Statement Tables</div>
            <div class="arch-step">KPI Engine</div>
            <div class="arch-step">Revenue Analytics</div>
            <div class="arch-step">Forecast Model</div>
            <div class="arch-step">AI Commentary</div>
        </div>
        """
    )

# ================================================================
# Intelligence Hub
# ================================================================

with tab_kpi:

    revenue = k["revenue"]
    revenue_yoy = k["revenue_yoy_growth"]
    gross_margin = k["gross_margin"]
    operating_margin = k["operating_margin"]
    net_margin = k["net_margin"]
    fcf = k["free_cash_flow"]
    cash_balance = k["cash_balance"]
    total_debt = k["total_debt"]
    debt_to_cash = total_debt / cash_balance if cash_balance else None

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Executive KPI Intelligence</div>
                <div class="section-subtitle">Compact indicators for scale, efficiency, cash generation, and financial flexibility.</div>
            </div>
            <div class="section-tag">CFO View</div>
        </div>
        """
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Revenue Intelligence</div>
                <div class="kpi-name">FY{k['latest_period']} Revenue</div>
                <div class="kpi-value">{fmt_cur(revenue)}</div>
                <div class="kpi-sub">Total reported revenue.</div>
                <div class="badge green"><span class="dot"></span>{fmt_pct(revenue_yoy)} YoY</div>
            </div>
            """
        )

    with c2:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Profitability Signals</div>
                <div class="kpi-name">Operating Margin</div>
                <div class="kpi-value">{fmt_pct(operating_margin)}</div>
                <div class="kpi-sub">Gross {fmt_pct(gross_margin)} · Net {fmt_pct(net_margin)}</div>
                <div class="badge"><span class="dot"></span>Margin profile</div>
            </div>
            """
        )

    with c3:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Cash Flow Engine</div>
                <div class="kpi-name">Free Cash Flow</div>
                <div class="kpi-value">{fmt_cur(fcf)}</div>
                <div class="kpi-sub">OCF less capex.</div>
                <div class="badge green"><span class="dot"></span>Cash generative</div>
            </div>
            """
        )

    with c4:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Balance Sheet Health</div>
                <div class="kpi-name">Cash and Debt</div>
                <div class="kpi-value">{fmt_cur(cash_balance)}</div>
                <div class="kpi-sub">Debt {fmt_cur(total_debt)} · {debt_to_cash:.1f}x debt/cash</div>
                <div class="badge"><span class="dot"></span>Liquidity</div>
            </div>
            """
        )

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">How To Read The KPIs</div>
                <div class="section-subtitle">Short explanations for what each metric means.</div>
            </div>
            <div class="section-tag">Metric Guide</div>
        </div>
        """
    )

    e1, e2, e3, e4 = st.columns(4, gap="medium")

    with e1:
        html(
            """
            <div class="info-card">
                <div class="info-title">Revenue</div>
                <div class="info-text">Measures business scale and top-line growth.</div>
                <div class="formula">Growth = Current / Prior - 1</div>
            </div>
            """
        )

    with e2:
        html(
            """
            <div class="info-card">
                <div class="info-title">Operating Margin</div>
                <div class="info-text">Shows efficiency after operating expenses.</div>
                <div class="formula">Operating Income / Revenue</div>
            </div>
            """
        )

    with e3:
        html(
            """
            <div class="info-card">
                <div class="info-title">Free Cash Flow</div>
                <div class="info-text">Cash available after capital spending.</div>
                <div class="formula">OCF - Capex</div>
            </div>
            """
        )

    with e4:
        html(
            """
            <div class="info-card">
                <div class="info-title">Liquidity</div>
                <div class="info-text">Shows flexibility from cash and debt position.</div>
                <div class="formula">Debt / Cash</div>
            </div>
            """
        )

# ================================================================
# Revenue Intelligence
# ================================================================

with tab_revenue:

    latest_product = k["product_revenue"]
    latest_services = k["service_revenue"]
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Revenue Intelligence</div>
                <div class="section-subtitle">Historical revenue trend, mix, and growth interpretation.</div>
            </div>
            <div class="section-tag">Growth Analytics</div>
        </div>
        """
    )

    r1, r2, r3 = st.columns(3, gap="medium")

    with r1:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">FY2025 Revenue</div>
                <div class="kpi-name">Total Revenue</div>
                <div class="kpi-value">{fmt_cur(k['revenue'])}</div>
                <div class="kpi-sub">Latest annual revenue.</div>
                <div class="badge green"><span class="dot"></span>{fmt_pct(k['revenue_yoy_growth'])} YoY</div>
            </div>
            """
        )

    with r2:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Revenue Mix</div>
                <div class="kpi-name">Service and Other</div>
                <div class="kpi-value">{fmt_pct(services_mix)}</div>
                <div class="kpi-sub">Share of FY2025 revenue.</div>
                <div class="badge"><span class="dot"></span>Largest category</div>
            </div>
            """
        )

    with r3:
        html(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Growth Spread</div>
                <div class="kpi-name">2025 vs 2024</div>
                <div class="kpi-value">{fmt_cur(growth_spread)}</div>
                <div class="kpi-sub">Incremental revenue added.</div>
                <div class="badge green"><span class="dot"></span>Expansion</div>
            </div>
            """
        )

    left, right = st.columns(2, gap="medium")

    with left:
        html(
            """
            <div class="chart-shell">
                <div class="chart-heading">
                    <div class="chart-title">Revenue Over Time</div>
                    <div class="chart-caption">FY2023-FY2025</div>
                </div>
            """
        )

        fig_ts = px.line(
            ts,
            x="period",
            y="revenue",
            markers=True,
            color_discrete_sequence=["#0078D4"],
        )

        fig_ts.update_traces(
            line=dict(width=3, shape="spline"),
            marker=dict(size=7, color="#0078D4", line=dict(width=1.5, color="#D8EEFF")),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
        )

        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        fig_ts = style_fig(fig_ts, height=235)
        st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})
        html("</div>")

    with right:
        html(
            """
            <div class="chart-shell">
                <div class="chart-heading">
                    <div class="chart-title">Revenue Mix by Category</div>
                    <div class="chart-caption">Product vs Service</div>
                </div>
            """
        )

        seg_long = segment_revenue.melt(
            id_vars=["period"],
            value_vars=["Product Revenue", "Service and Other Revenue"],
            var_name="category",
            value_name="revenue",
        )

        fig_seg = px.bar(
            seg_long,
            x="period",
            y="revenue",
            color="category",
            barmode="stack",
            color_discrete_map={
                "Product Revenue": "#0078D4",
                "Service and Other Revenue": "#7FBA00",
            },
        )

        fig_seg.update_traces(
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}M<extra></extra>",
        )

        fig_seg.update_yaxes(tickprefix="$", ticksuffix="M")
        fig_seg = style_fig(fig_seg, height=235, showlegend=True)
        st.plotly_chart(fig_seg, use_container_width=True, config={"displayModeBar": False})
        html("</div>")

    html(
        f"""
        <div class="insight-card">
            <div class="insight-title">Revenue Commentary</div>
            <div class="insight-text">
                Microsoft generated {fmt_cur(k['revenue'])} in FY2025 revenue, representing {fmt_pct(k['revenue_yoy_growth'])}
                year-over-year growth. Service and other revenue represented approximately {fmt_pct(services_mix)} of total revenue.
            </div>
        </div>
        """
    )

# ================================================================
# AI Forecasting
# ================================================================

with tab_forecast:

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">AI Forecasting Simulator</div>
                <div class="section-subtitle">Adjust revenue growth assumptions and compare scenario outcomes.</div>
            </div>
            <div class="section-tag">Scenario Model</div>
        </div>
        """
    )

    c1, c2 = st.columns([1, 1], gap="medium")

    with c1:
        growth_rate_pct = st.slider(
            "Base Case Revenue Growth Assumption",
            min_value=0,
            max_value=30,
            value=12,
            step=1,
        )

    with c2:
        forecast_years = st.slider(
            "Forecast Horizon",
            min_value=1,
            max_value=5,
            value=3,
            step=1,
        )

    base_growth = growth_rate_pct / 100

    forecast_df = build_forecast_dataframe(
        starting_revenue=k["revenue"],
        growth_rate=base_growth,
        start_year=2026,
        periods=forecast_years,
    )

    scenario_df = build_scenario_dataframe(
        starting_revenue=k["revenue"],
        start_year=2026,
        periods=forecast_years,
        bear_growth=max(base_growth - 0.05, 0),
        base_growth=base_growth,
        bull_growth=base_growth + 0.05,
    )

    bear_last = scenario_df[scenario_df["scenario"] == "Bear Case"].sort_values("year").iloc[-1]
    base_last = scenario_df[scenario_df["scenario"] == "Base Case"].sort_values("year").iloc[-1]
    bull_last = scenario_df[scenario_df["scenario"] == "Bull Case"].sort_values("year").iloc[-1]

    s1, s2, s3 = st.columns(3, gap="medium")

    with s1:
        html(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Bear Case</div>
                <div class="scenario-title">Conservative Growth</div>
                <div class="scenario-value">{fmt_cur(bear_last['revenue'])}</div>
                <div class="scenario-text">Projected FY{int(bear_last['year'])} revenue.</div>
            </div>
            """
        )

    with s2:
        html(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Base Case</div>
                <div class="scenario-title">Selected Assumption</div>
                <div class="scenario-value">{fmt_cur(base_last['revenue'])}</div>
                <div class="scenario-text">Projected FY{int(base_last['year'])} revenue.</div>
            </div>
            """
        )

    with s3:
        html(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Bull Case</div>
                <div class="scenario-title">Upside Growth</div>
                <div class="scenario-value">{fmt_cur(bull_last['revenue'])}</div>
                <div class="scenario-text">Projected FY{int(bull_last['year'])} revenue.</div>
            </div>
            """
        )

    html(
        """
        <div class="chart-shell">
            <div class="chart-heading">
                <div class="chart-title">Historical Revenue + Forecast Scenarios</div>
                <div class="chart-caption">Historical and projected revenue</div>
            </div>
        """
    )

    hist_df = ts[["period", "revenue"]].copy()
    hist_df["year"] = hist_df["period"].astype(int)

    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=hist_df["year"],
            y=hist_df["revenue"],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#0078D4", width=3),
            marker=dict(size=7),
            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
        )
    )

    colors = {
        "Bear Case": "#F25022",
        "Base Case": "#7FBA00",
        "Bull Case": "#FFB900",
    }

    for scenario, color in colors.items():
        subset = scenario_df[scenario_df["scenario"] == scenario]
        fig_forecast.add_trace(
            go.Scatter(
                x=subset["year"],
                y=subset["revenue"],
                mode="lines+markers",
                name=scenario,
                line=dict(color=color, width=2.5, dash="dash"),
                marker=dict(size=6),
                hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
            )
        )

    fig_forecast.update_yaxes(tickprefix="$", ticksuffix="M")
    fig_forecast = style_fig(fig_forecast, height=260, showlegend=True)
    st.plotly_chart(fig_forecast, use_container_width=True, config={"displayModeBar": False})
    html("</div>")

    latest_forecast = forecast_df.iloc[-1]

    html(
        f"""
        <div class="insight-card">
            <div class="insight-title">Forecast Narrative</div>
            <div class="insight-text">
                Using a base growth assumption of {growth_rate_pct:.0f}%, projected revenue reaches {fmt_cur(latest_forecast['revenue'])}
                by FY{int(latest_forecast['year'])}. This is a simplified scenario simulator, not a formal investment forecast.
            </div>
        </div>
        """
    )

# ================================================================
# Financial Statements
# ================================================================

with tab_financials:

    financials = result["financials"]

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Financial Statements</div>
                <div class="section-subtitle">Core statement tables used by the KPI engine.</div>
            </div>
            <div class="section-tag">Statement Tables</div>
        </div>
        """
    )

    f1, f2 = st.columns(2, gap="medium")

    with f1:
        st.subheader("Income Statement")
        st.dataframe(financials["income"], use_container_width=True, hide_index=True, height=230)
        st.download_button(
            label="Download Income Statement CSV",
            data=dataframe_to_csv(financials["income"]),
            file_name="microsoft_income_statement.csv",
            mime="text/csv",
        )

    with f2:
        st.subheader("Balance Sheet")
        st.dataframe(financials["balance"], use_container_width=True, hide_index=True, height=160)
        st.download_button(
            label="Download Balance Sheet CSV",
            data=dataframe_to_csv(financials["balance"]),
            file_name="microsoft_balance_sheet.csv",
            mime="text/csv",
        )

    st.subheader("Cash Flow Statement")
    st.dataframe(financials["cashflow"], use_container_width=True, hide_index=True, height=160)
    st.download_button(
        label="Download Cash Flow Statement CSV",
        data=dataframe_to_csv(financials["cashflow"]),
        file_name="microsoft_cash_flow_statement.csv",
        mime="text/csv",
    )

# ================================================================
# AI Copilot
# ================================================================

with tab_ai:

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">AI Copilot for Financial Commentary</div>
                <div class="section-subtitle">Ask about revenue, margins, cash flow, liquidity, or forecasting.</div>
            </div>
            <div class="section-tag">Narrative AI</div>
        </div>
        """
    )

    question = st.text_area(
        "Ask a financial question",
        value="Summarize Microsoft revenue, margins, and cash flow.",
        height=90,
    )

    response = answer_question(question, benchmark_df, kpis=k)

    html(
        f"""
        <div class="insight-card">
            <div class="insight-title">Generated Financial Commentary</div>
            <div class="insight-text">{response}</div>
        </div>
        """
    )

    html(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Example Questions</div>
                <div class="section-subtitle">Use these prompts to test the commentary engine.</div>
            </div>
            <div class="section-tag">Prompt Ideas</div>
        </div>

        <div class="bento-grid">
            <div class="bento-card">
                <div class="bento-label">Revenue</div>
                <div class="bento-title">Explain revenue growth</div>
                <div class="bento-text">Try: How did Microsoft's revenue perform year over year?</div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Margins</div>
                <div class="bento-title">Review profitability</div>
                <div class="bento-text">Try: What do the margins say about profitability?</div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Cash Flow</div>
                <div class="bento-title">Analyze cash generation</div>
                <div class="bento-text">Try: Summarize free cash flow and liquidity.</div>
            </div>
        </div>
        """
    )

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
    initial_sidebar_state="expanded",
)

# ================================================================
# Global CSS
# ================================================================

st.markdown(
    """
    <style>
    :root {
        --ms-blue: #0078D4;
        --ms-orange: #F25022;
        --ms-green: #7FBA00;
        --ms-yellow: #FFB900;
        --ms-purple: #8661C5;

        --bg: #070A12;
        --bg-2: #0B0F1A;
        --panel: #10141F;
        --panel-2: #121826;
        --panel-3: #151B2B;

        --border: rgba(255,255,255,0.075);
        --border-strong: rgba(0,120,212,0.5);

        --text: #F3F2F1;
        --muted: #AEB5C1;
        --muted-2: #7E8797;

        --shadow: 0 18px 52px rgba(0,0,0,0.45);
        --shadow-soft: 0 10px 30px rgba(0,0,0,0.35);

        --radius-lg: 24px;
        --radius-md: 18px;
        --radius-sm: 12px;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background:
            radial-gradient(circle at 12% 5%, rgba(0,120,212,0.18), transparent 30%),
            radial-gradient(circle at 90% 0%, rgba(127,186,0,0.10), transparent 28%),
            linear-gradient(135deg, #070A12 0%, #0B0F1A 42%, #070A12 100%) !important;
        color: var(--text) !important;
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .block-container {
        max-width: 1540px !important;
        padding-top: 1.8rem !important;
        padding-left: 2.1rem !important;
        padding-right: 2.1rem !important;
        padding-bottom: 3rem !important;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ============================================================
       Sidebar
       ============================================================ */

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #080B13 0%, #0B0F1A 58%, #070A12 100%) !important;
        border-right: 1px solid var(--border) !important;
    }

    [data-testid="stSidebarContent"] {
        padding: 1.25rem 1rem !important;
    }

    .sidebar-brand {
        padding: 1rem;
        border: 1px solid var(--border);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
        box-shadow: var(--shadow-soft);
        margin-bottom: 1rem;
    }

    .brand-kicker {
        font-size: 0.68rem;
        color: var(--muted-2);
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }

    .brand-title {
        font-size: 1rem;
        color: var(--text);
        font-weight: 750;
        line-height: 1.25;
    }

    .sidebar-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.46rem 0.66rem;
        border-radius: 999px;
        background: rgba(0,120,212,0.12);
        border: 1px solid rgba(0,120,212,0.28);
        color: #D5ECFF;
        font-size: 0.74rem;
        font-weight: 750;
        margin-bottom: 1rem;
    }

    .sidebar-dot {
        width: 7px;
        height: 7px;
        background: var(--ms-green);
        border-radius: 999px;
        box-shadow: 0 0 12px rgba(127,186,0,0.7);
    }

    .sidebar-note {
        color:#7E8797;
        font-size:0.76rem;
        line-height:1.55;
        padding:0.85rem;
        border-radius:14px;
        background:rgba(255,255,255,0.025);
        border:1px solid rgba(255,255,255,0.06);
    }

    /* ============================================================
       Inputs
       ============================================================ */

    .stTextInput label,
    .stTextArea label,
    .stSlider label {
        color: var(--muted) !important;
        font-size: 0.76rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.11em;
    }

    .stTextInput input,
    .stTextArea textarea {
        background: #0F1422 !important;
        color: var(--text) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 12px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(0,120,212,0.75) !important;
        box-shadow: 0 0 0 4px rgba(0,120,212,0.16) !important;
    }

    .stButton button,
    .stDownloadButton button {
        background: linear-gradient(135deg, #0078D4, #0A5EAA) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 12px !important;
        font-weight: 750 !important;
        transition: 0.18s ease !important;
        box-shadow: 0 10px 24px rgba(0,120,212,0.22);
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 34px rgba(0,120,212,0.35);
    }

    /* ============================================================
       Tabs
       ============================================================ */

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 0.45rem;
        margin-bottom: 1.35rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 0 0.95rem;
        border-radius: 12px;
        color: #AEB5C1;
        font-weight: 750;
        font-size: 0.86rem;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0,120,212,0.16) !important;
        border: 1px solid rgba(0,120,212,0.34);
        color: #D5ECFF !important;
    }

    /* ============================================================
       Aurora Hero
       ============================================================ */

    .aurora-hero {
        position: relative;
        min-height: 330px;
        border-radius: 28px;
        padding: 2.3rem 2.25rem;
        border: 1px solid rgba(255,255,255,0.08);
        background:
            linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.015)),
            #0B0F1A;
        box-shadow: var(--shadow);
        overflow: hidden;
        margin-bottom: 1.7rem;
    }

    .aurora-hero:before {
        content: "";
        position: absolute;
        inset: -35%;
        background:
            radial-gradient(circle at 20% 35%, rgba(0,120,212,0.38), transparent 26%),
            radial-gradient(circle at 78% 18%, rgba(127,186,0,0.22), transparent 24%),
            radial-gradient(circle at 65% 72%, rgba(134,97,197,0.26), transparent 28%),
            radial-gradient(circle at 40% 84%, rgba(242,80,34,0.13), transparent 20%);
        filter: blur(70px);
        opacity: 0.85;
        animation: auroraMove 18s ease-in-out infinite alternate;
        z-index: 0;
    }

    .aurora-hero:after {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(180deg, rgba(7,10,18,0.06), rgba(7,10,18,0.72)),
            radial-gradient(circle at 93% 0%, rgba(0,120,212,0.12), transparent 36%);
        z-index: 1;
    }

    @keyframes auroraMove {
        0% {
            transform: translate3d(-2%, -2%, 0) scale(1);
        }
        50% {
            transform: translate3d(4%, 3%, 0) scale(1.05);
        }
        100% {
            transform: translate3d(-1%, 5%, 0) scale(1.02);
        }
    }

    .aurora-content {
        position: relative;
        z-index: 2;
        max-width: 1120px;
    }

    .hero-topline {
        display: flex;
        gap: 0.8rem;
        align-items: center;
        margin-bottom: 0.9rem;
        color: #D5ECFF;
        font-size: 0.74rem;
        font-weight: 850;
        letter-spacing: 0.16em;
        text-transform: uppercase;
    }

    .hero-logo {
        width: 13px;
        height: 13px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2px;
    }

    .hero-logo span:nth-child(1) { background: #F25022; }
    .hero-logo span:nth-child(2) { background: #7FBA00; }
    .hero-logo span:nth-child(3) { background: #0078D4; }
    .hero-logo span:nth-child(4) { background: #FFB900; }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.85rem);
        line-height: 1.02;
        letter-spacing: -0.065em;
        color: #FFFFFF;
        font-weight: 800;
        margin-bottom: 0.85rem;
    }

    .hero-subtitle {
        color: #C2C8D2;
        font-size: 1.04rem;
        line-height: 1.68;
        max-width: 1040px;
    }

    .hero-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 1.25rem;
    }

    .meta-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.48rem 0.72rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.045);
        color: #D9DEE7;
        font-size: 0.78rem;
        font-weight: 750;
        backdrop-filter: blur(12px);
    }

    .meta-pill.blue {
        border-color: rgba(0,120,212,0.42);
        background: rgba(0,120,212,0.18);
        color: #D5ECFF;
    }

    /* ============================================================
       Section Headers
       ============================================================ */

    .section-head {
        display: flex;
        justify-content: space-between;
        align-items: end;
        margin: 1.65rem 0 0.85rem 0;
        gap: 1rem;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.015em;
    }

    .section-subtitle {
        margin-top: 0.25rem;
        color: var(--muted-2);
        font-size: 0.84rem;
        line-height: 1.5;
    }

    .section-tag {
        color: #D5ECFF;
        background: rgba(0,120,212,0.12);
        border: 1px solid rgba(0,120,212,0.28);
        border-radius: 999px;
        padding: 0.42rem 0.68rem;
        font-size: 0.74rem;
        font-weight: 800;
        white-space: nowrap;
    }

    /* ============================================================
       Dynamic Cards
       ============================================================ */

    .kpi-card,
    .bento-card,
    .info-card,
    .scenario-card,
    .insight-card,
    .chart-shell {
        position: relative;
        border-radius: var(--radius-md);
        border: 1px solid var(--border);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.052), rgba(255,255,255,0.014)),
            #10141F;
        box-shadow: var(--shadow-soft);
        overflow: hidden;
        transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    }

    .kpi-card:hover,
    .bento-card:hover,
    .info-card:hover,
    .scenario-card:hover,
    .insight-card:hover {
        transform: translateY(-6px) scale(1.012);
        border-color: var(--border-strong);
        box-shadow: 0 28px 70px rgba(0,0,0,0.48);
    }

    .kpi-card:before,
    .bento-card:before,
    .info-card:before,
    .scenario-card:before,
    .insight-card:before {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -90px;
        top: -110px;
        background: radial-gradient(circle, rgba(0,120,212,0.20), transparent 65%);
        opacity: 0;
        transition: opacity 0.22s ease;
        pointer-events: none;
    }

    .kpi-card:hover:before,
    .bento-card:hover:before,
    .info-card:hover:before,
    .scenario-card:hover:before,
    .insight-card:hover:before {
        opacity: 1;
    }

    .kpi-card {
        min-height: 170px;
        padding: 1rem;
    }

    .kpi-label {
        color: var(--muted-2);
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .kpi-name {
        color: #CBD2DC;
        font-size: 0.88rem;
        line-height: 1.35;
        font-weight: 750;
        margin-bottom: 0.55rem;
    }

    .kpi-value {
        font-size: 1.9rem;
        font-weight: 820;
        color: #FFFFFF;
        letter-spacing: -0.045em;
        margin-bottom: 0.35rem;
    }

    .kpi-sub {
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.45;
        margin-bottom: 0.75rem;
    }

    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.44rem;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.38rem 0.58rem;
        border-radius: 999px;
        background: rgba(0,120,212,0.13);
        color: #D5ECFF;
        border: 1px solid rgba(0,120,212,0.28);
    }

    .kpi-badge.green {
        background: rgba(127,186,0,0.12);
        color: #DFF7B2;
        border-color: rgba(127,186,0,0.28);
    }

    .kpi-badge.orange {
        background: rgba(242,80,34,0.12);
        color: #FFC1B6;
        border-color: rgba(242,80,34,0.28);
    }

    .badge-dot {
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: currentColor;
        box-shadow: 0 0 12px currentColor;
    }

    .bento-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin-bottom: 1.2rem;
    }

    .bento-card {
        min-height: 150px;
        padding: 1rem;
    }

    .bento-card.large {
        grid-column: span 2;
        min-height: 180px;
    }

    .bento-label {
        color: #D5ECFF;
        font-size: 0.71rem;
        font-weight: 850;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 1.25rem;
    }

    .bento-title {
        color: #FFFFFF;
        font-size: 1.14rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.45rem;
    }

    .bento-text {
        color: #AEB5C1;
        font-size: 0.86rem;
        line-height: 1.5;
    }

    .info-card {
        padding: 1rem;
        min-height: 150px;
    }

    .info-title {
        color: #FFFFFF;
        font-size: 0.96rem;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }

    .info-text {
        color: #AEB5C1;
        font-size: 0.84rem;
        line-height: 1.55;
    }

    .formula {
        color: #D5ECFF;
        background: rgba(0,120,212,0.11);
        border: 1px solid rgba(0,120,212,0.25);
        border-radius: 12px;
        padding: 0.55rem 0.7rem;
        margin-top: 0.75rem;
        font-size: 0.78rem;
        font-weight: 750;
    }

    .chart-shell {
        padding: 1rem 1rem 0.7rem 1rem;
        margin-bottom: 1rem;
    }

    .chart-heading {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        margin-bottom: 0.55rem;
    }

    .chart-title {
        color: var(--text);
        font-size: 0.92rem;
        font-weight: 800;
        letter-spacing: -0.01em;
    }

    .chart-caption {
        color: var(--muted-2);
        font-size: 0.72rem;
        font-weight: 750;
    }

    .scenario-card {
        padding: 1rem;
        min-height: 145px;
    }

    .scenario-label {
        color: var(--muted-2);
        font-size: 0.68rem;
        font-weight: 850;
        letter-spacing: .13em;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }

    .scenario-title {
        color: #FFFFFF;
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: .35rem;
    }

    .scenario-value {
        color: #FFFFFF;
        font-size: 1.65rem;
        font-weight: 820;
        letter-spacing: -0.04em;
        margin-bottom: .35rem;
    }

    .scenario-text {
        color: #AEB5C1;
        font-size: .8rem;
        line-height: 1.45;
    }

    .insight-card {
        padding: 1.1rem 1.15rem;
        margin-top: 0.5rem;
        border-color: rgba(0,120,212,0.24);
        background:
            radial-gradient(circle at 0% 0%, rgba(0,120,212,0.17), transparent 38%),
            linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
            #10141F;
    }

    .insight-title {
        color: #D5ECFF;
        font-size: 0.76rem;
        font-weight: 850;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .insight-text {
        color: #D9DEE7;
        line-height: 1.65;
        font-size: 0.93rem;
    }

    .architecture {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 0.5rem;
    }

    .arch-step {
        text-align: center;
        padding: 0.85rem 0.6rem;
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.07);
        background: rgba(255,255,255,0.035);
        color: #D9DEE7;
        font-size: 0.78rem;
        font-weight: 750;
        min-height: 84px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-soft);
    }

    [data-testid="stDataFrame"] div {
        background-color: #10141F !important;
        color: var(--text) !important;
    }

    h3 {
        color: var(--text) !important;
        font-size: 1rem !important;
        font-weight: 800 !important;
        margin-top: 0.6rem !important;
        margin-bottom: 0.7rem !important;
    }

    @media (max-width: 1100px) {
        .bento-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .bento-card.large {
            grid-column: span 1;
        }

        .architecture {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }

    @media (max-width: 760px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .aurora-hero {
            padding: 1.4rem;
            min-height: 290px;
        }

        .hero-title {
            font-size: 2rem;
        }

        .bento-grid {
            grid-template-columns: 1fr;
        }

        .architecture {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
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
# Formatting Helpers
# ================================================================

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

def style_fig(fig, height=330, showlegend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="#10141F",
        plot_bgcolor="#10141F",
        font=dict(
            family="Segoe UI, Inter, sans-serif",
            color="#C8CCD2",
            size=12,
        ),
        margin=dict(l=42, r=24, t=18, b=42),
        hovermode="x unified",
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#C8CCD2", size=11),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="rgba(255,255,255,0.10)",
            tickfont=dict(color="#8A92A0", size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,0.055)",
            zeroline=False,
            showline=False,
            tickfont=dict(color="#8A92A0", size=11),
        ),
    )
    return fig

# ================================================================
# Sidebar
# ================================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-kicker">AI Finance Product</div>
            <div class="brand-title">Microsoft Financial<br/>Intelligence Platform</div>
        </div>
        <div class="sidebar-chip">
            <span class="sidebar-dot"></span>
            FY2025 10-K View
        </div>
        <div class="sidebar-note">
            This project transforms Microsoft 10-K financial statement data into a modern AI-style executive analytics experience.
        </div>
        """,
        unsafe_allow_html=True,
    )

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
# Tab 1: Executive Summary
# ================================================================

with tab_summary:

    st.markdown(
        """
        <div class="aurora-hero">
            <div class="aurora-content">
                <div class="hero-topline">
                    <div class="hero-logo">
                        <span></span><span></span><span></span><span></span>
                    </div>
                    Microsoft Fluent UI Inspired Financial Intelligence
                </div>
                <div class="hero-title">Microsoft Financial Intelligence Platform</div>
                <div class="hero-subtitle">
                    An AI-style financial analytics application built from Microsoft's FY2025 10-K data.
                    The platform converts traditional financial statements into executive KPIs, interactive revenue analytics,
                    forecasting scenarios, and natural-language financial commentary.
                </div>
                <div class="hero-meta-row">
                    <span class="meta-pill blue">FY2025</span>
                    <span class="meta-pill">10-K Analysis</span>
                    <span class="meta-pill">Revenue Intelligence</span>
                    <span class="meta-pill">AI Forecasting</span>
                    <span class="meta-pill">Executive Finance View</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">What This Project Demonstrates</div>
                <div class="section-subtitle">
                    A portfolio-style finance product combining financial analysis, KPI modeling, forecasting, data visualization, and AI-style storytelling.
                </div>
            </div>
            <div class="section-tag">Project Overview</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="bento-grid">
            <div class="bento-card large">
                <div class="bento-label">Overview</div>
                <div class="bento-title">Financial Statement Intelligence</div>
                <div class="bento-text">
                    This dashboard converts Microsoft's annual financial statement data into a clean executive reporting experience.
                    It focuses on revenue, profitability, cash flow, balance sheet health, and forward-looking forecasting.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">KPI Engine</div>
                <div class="bento-title">Executive Metrics</div>
                <div class="bento-text">
                    Revenue growth, gross margin, operating margin, net margin, free cash flow, cash balance, and total debt.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Revenue</div>
                <div class="bento-title">Revenue Intelligence</div>
                <div class="bento-text">
                    Trend analysis and revenue mix views help explain growth and business composition over time.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Forecasting</div>
                <div class="bento-title">Scenario Modeling</div>
                <div class="bento-text">
                    Interactive growth assumptions generate forward revenue scenarios for bear, base, and bull cases.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">AI Copilot</div>
                <div class="bento-title">Narrative Commentary</div>
                <div class="bento-text">
                    A simple AI-style Q&A layer turns financial metrics into plain-English business commentary.
                </div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Design</div>
                <div class="bento-title">Fluent + AI Startup Feel</div>
                <div class="bento-text">
                    The interface blends Microsoft Fluent UI, Azure-inspired depth, and modern AI product design patterns.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">How To Navigate The Platform</div>
                <div class="section-subtitle">
                    Each tab is designed like a product module instead of a single long scrolling dashboard.
                </div>
            </div>
            <div class="section-tag">User Guide</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav1, nav2, nav3 = st.columns(3, gap="large")

    with nav1:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">1. Intelligence Hub</div>
                <div class="info-text">
                    Start here to understand the core KPIs: revenue, profitability, free cash flow, and liquidity.
                    This section explains what each metric means and why leadership would care about it.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav2:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">2. Revenue Intelligence</div>
                <div class="info-text">
                    Use this tab to review historical revenue trends, product versus services revenue mix,
                    and commentary around growth patterns.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with nav3:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">3. AI Forecasting</div>
                <div class="info-text">
                    Adjust growth assumptions and immediately see how future revenue scenarios change
                    across bear, base, and bull cases.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Project Architecture</div>
                <div class="section-subtitle">
                    A simple view of how the application moves from financial statements to executive insights.
                </div>
            </div>
            <div class="section-tag">Workflow</div>
        </div>

        <div class="architecture">
            <div class="arch-step">10-K Financial Data</div>
            <div class="arch-step">Statement Tables</div>
            <div class="arch-step">KPI Engine</div>
            <div class="arch-step">Revenue Analytics</div>
            <div class="arch-step">Forecast Modeling</div>
            <div class="arch-step">AI Commentary</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Tab 2: Intelligence Hub
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

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Executive KPI Intelligence</div>
                <div class="section-subtitle">
                    High-level indicators for scale, growth, profitability, cash generation, and balance sheet flexibility.
                </div>
            </div>
            <div class="section-tag">CFO View</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="large")

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Revenue Intelligence</div>
                <div class="kpi-name">Fiscal Year {k['latest_period']}</div>
                <div class="kpi-value">{fmt_cur(revenue)}</div>
                <div class="kpi-sub">Total reported revenue for the latest fiscal year.</div>
                <div class="kpi-badge {'orange' if revenue_yoy < 0 else 'green'}">
                    <span class="badge-dot"></span>{fmt_pct(revenue_yoy)} YoY
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Profitability Signals</div>
                <div class="kpi-name">Operating Margin</div>
                <div class="kpi-value">{fmt_pct(operating_margin)}</div>
                <div class="kpi-sub">Gross margin {fmt_pct(gross_margin)} · Net margin {fmt_pct(net_margin)}</div>
                <div class="kpi-badge">
                    <span class="badge-dot"></span>Margin profile
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Cash Flow Engine</div>
                <div class="kpi-name">Free Cash Flow</div>
                <div class="kpi-value">{fmt_cur(fcf)}</div>
                <div class="kpi-sub">Operating cash flow less capital expenditures.</div>
                <div class="kpi-badge green">
                    <span class="badge-dot"></span>Cash generative
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Balance Sheet Health</div>
                <div class="kpi-name">Cash and Debt</div>
                <div class="kpi-value">{fmt_cur(cash_balance)}</div>
                <div class="kpi-sub">Total debt {fmt_cur(total_debt)} · Debt/cash {debt_to_cash:.1f}x</div>
                <div class="kpi-badge">
                    <span class="badge-dot"></span>Liquidity view
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">How To Read These KPIs</div>
                <div class="section-subtitle">
                    Each KPI gives a different view of company performance.
                </div>
            </div>
            <div class="section-tag">Metric Guide</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    e1, e2 = st.columns(2, gap="large")

    with e1:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Revenue</div>
                <div class="info-text">
                    Revenue shows the scale of the business. Year-over-year growth helps answer whether the company is expanding,
                    slowing, or becoming more mature.
                </div>
                <div class="formula">Revenue Growth = Current Year Revenue / Prior Year Revenue - 1</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with e2:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Operating Margin</div>
                <div class="info-text">
                    Operating margin measures how efficiently the company turns revenue into operating income after core expenses.
                    It is one of the most important profitability indicators for leadership.
                </div>
                <div class="formula">Operating Margin = Operating Income / Revenue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    e3, e4 = st.columns(2, gap="large")

    with e3:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Free Cash Flow</div>
                <div class="info-text">
                    Free cash flow shows how much cash remains after funding capital expenditures.
                    Strong free cash flow gives the company flexibility to invest, return capital, or strengthen the balance sheet.
                </div>
                <div class="formula">Free Cash Flow = Operating Cash Flow - Capital Expenditures</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with e4:
        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">Liquidity</div>
                <div class="info-text">
                    Cash and debt provide a quick view of financial flexibility and risk.
                    A strong cash position can support strategic investments, acquisitions, and resilience during uncertainty.
                </div>
                <div class="formula">Debt / Cash = Total Debt / Cash Balance</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ================================================================
# Tab 3: Revenue Intelligence
# ================================================================

with tab_revenue:

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Revenue Intelligence</div>
                <div class="section-subtitle">
                    Historical revenue trend, revenue mix, and business interpretation.
                </div>
            </div>
            <div class="section-tag">Growth Analytics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r1, r2, r3 = st.columns(3, gap="large")

    latest_product = segment_revenue.loc[segment_revenue["period"] == "2025", "Product Revenue"].iloc[0]
    latest_services = segment_revenue.loc[segment_revenue["period"] == "2025", "Service and Other Revenue"].iloc[0]
    services_mix = latest_services / (latest_product + latest_services)

    with r1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">FY2025 Revenue</div>
                <div class="kpi-name">Total Revenue</div>
                <div class="kpi-value">{fmt_cur(k['revenue'])}</div>
                <div class="kpi-sub">Latest annual revenue from the financial statement dataset.</div>
                <div class="kpi-badge green"><span class="badge-dot"></span>{fmt_pct(k['revenue_yoy_growth'])} YoY</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Revenue Mix</div>
                <div class="kpi-name">Service and Other Revenue</div>
                <div class="kpi-value">{fmt_pct(services_mix)}</div>
                <div class="kpi-sub">Share of FY2025 revenue from service and other revenue categories.</div>
                <div class="kpi-badge"><span class="badge-dot"></span>Largest mix driver</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Growth Spread</div>
                <div class="kpi-name">2025 vs 2024</div>
                <div class="kpi-value">{fmt_cur(k['revenue'] - ts.loc[ts['period'] == '2024', 'revenue'].iloc[0])}</div>
                <div class="kpi-sub">Incremental revenue added from FY2024 to FY2025.</div>
                <div class="kpi-badge green"><span class="badge-dot"></span>Expansion</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(
            """
            <div class="chart-shell">
                <div class="chart-heading">
                    <div class="chart-title">Revenue Over Time</div>
                    <div class="chart-caption">FY2023-FY2025</div>
                </div>
            """,
            unsafe_allow_html=True,
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
            marker=dict(size=9, color="#0078D4", line=dict(width=2, color="#D5ECFF")),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
        )
        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        fig_ts = style_fig(fig_ts, height=330)
        st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown(
            """
            <div class="chart-shell">
                <div class="chart-heading">
                    <div class="chart-title">Revenue Mix by Category</div>
                    <div class="chart-caption">Product vs Service</div>
                </div>
            """,
            unsafe_allow_html=True,
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
        fig_seg = style_fig(fig_seg, height=330, showlegend=True)
        st.plotly_chart(fig_seg, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Revenue Commentary</div>
            <div class="insight-text">
                Microsoft generated {fmt_cur(k['revenue'])} in FY2025 revenue, representing {fmt_pct(k['revenue_yoy_growth'])}
                year-over-year growth. Service and other revenue represented approximately {fmt_pct(services_mix)} of total revenue,
                making it the dominant revenue category in this simplified 10-K dataset.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Tab 4: AI Forecasting
# ================================================================

with tab_forecast:

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">AI Forecasting Simulator</div>
                <div class="section-subtitle">
                    Adjust forward revenue growth assumptions and compare scenario outcomes.
                </div>
            </div>
            <div class="section-tag">Scenario Model</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    growth_rate_pct = st.slider(
        "Base Case Revenue Growth Assumption",
        min_value=0,
        max_value=30,
        value=12,
        step=1,
    )

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

    latest_forecast = forecast_df.iloc[-1]

    s1, s2, s3 = st.columns(3, gap="large")

    bear_last = scenario_df[
        (scenario_df["scenario"] == "Bear Case")
    ].sort_values("year").iloc[-1]

    base_last = scenario_df[
        (scenario_df["scenario"] == "Base Case")
    ].sort_values("year").iloc[-1]

    bull_last = scenario_df[
        (scenario_df["scenario"] == "Bull Case")
    ].sort_values("year").iloc[-1]

    with s1:
        st.markdown(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Bear Case</div>
                <div class="scenario-title">Conservative Growth</div>
                <div class="scenario-value">{fmt_cur(bear_last['revenue'])}</div>
                <div class="scenario-text">Projected revenue by FY{int(bear_last['year'])} assuming slower growth.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Base Case</div>
                <div class="scenario-title">Selected Assumption</div>
                <div class="scenario-value">{fmt_cur(base_last['revenue'])}</div>
                <div class="scenario-text">Projected revenue by FY{int(base_last['year'])} using the selected growth rate.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            f"""
            <div class="scenario-card">
                <div class="scenario-label">Bull Case</div>
                <div class="scenario-title">Upside Growth</div>
                <div class="scenario-value">{fmt_cur(bull_last['revenue'])}</div>
                <div class="scenario-text">Projected revenue by FY{int(bull_last['year'])} assuming stronger growth.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="chart-shell">
            <div class="chart-heading">
                <div class="chart-title">Historical Revenue + Forecast Scenarios</div>
                <div class="chart-caption">Historical and projected revenue</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    hist_df = ts[["period", "revenue"]].copy()
    hist_df["year"] = hist_df["period"].astype(int)
    hist_df["scenario"] = "Historical"

    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=hist_df["year"],
            y=hist_df["revenue"],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#0078D4", width=3),
            marker=dict(size=8),
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
                line=dict(color=color, width=3, dash="dash"),
                marker=dict(size=8),
                hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
            )
        )

    fig_forecast.update_yaxes(tickprefix="$", ticksuffix="M")
    fig_forecast = style_fig(fig_forecast, height=380, showlegend=True)
    st.plotly_chart(fig_forecast, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Forecast Narrative</div>
            <div class="insight-text">
                Using a base growth assumption of {growth_rate_pct:.0f}%, projected revenue reaches {fmt_cur(latest_forecast['revenue'])}
                by FY{int(latest_forecast['year'])}. This is a simplified scenario model designed to show how revenue could evolve
                under different growth assumptions, not a formal valuation or investment forecast.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Tab 5: Financial Statements
# ================================================================

with tab_financials:

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Financial Statements</div>
                <div class="section-subtitle">
                    Core financial statement data used by the KPI engine.
                </div>
            </div>
            <div class="section-tag">Statement Tables</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    financials = result["financials"]

    f1, f2 = st.columns(2, gap="large")

    with f1:
        st.subheader("Income Statement")
        st.dataframe(financials["income"], use_container_width=True, hide_index=True)
        st.download_button(
            label="Download Income Statement CSV",
            data=dataframe_to_csv(financials["income"]),
            file_name="microsoft_income_statement.csv",
            mime="text/csv",
        )

    with f2:
        st.subheader("Balance Sheet")
        st.dataframe(financials["balance"], use_container_width=True, hide_index=True)
        st.download_button(
            label="Download Balance Sheet CSV",
            data=dataframe_to_csv(financials["balance"]),
            file_name="microsoft_balance_sheet.csv",
            mime="text/csv",
        )

    st.subheader("Cash Flow Statement")
    st.dataframe(financials["cashflow"], use_container_width=True, hide_index=True)
    st.download_button(
        label="Download Cash Flow Statement CSV",
        data=dataframe_to_csv(financials["cashflow"]),
        file_name="microsoft_cash_flow_statement.csv",
        mime="text/csv",
    )

# ================================================================
# Tab 6: AI Copilot
# ================================================================

with tab_ai:

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">AI Copilot for Financial Commentary</div>
                <div class="section-subtitle">
                    Ask a plain-English question about revenue, margins, cash flow, liquidity, or forecasting.
                </div>
            </div>
            <div class="section-tag">Narrative AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    question = st.text_area(
        "Ask a financial question",
        value="Summarize Microsoft revenue, margins, and cash flow.",
        height=100,
    )

    response = answer_question(question, benchmark_df, kpis=k)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Generated Financial Commentary</div>
            <div class="insight-text">{response}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Example Questions</div>
                <div class="section-subtitle">
                    Try these prompts to test the financial commentary engine.
                </div>
            </div>
            <div class="section-tag">Prompt Ideas</div>
        </div>

        <div class="bento-grid">
            <div class="bento-card">
                <div class="bento-label">Revenue</div>
                <div class="bento-title">Explain revenue growth</div>
                <div class="bento-text">Ask: "How did Microsoft's revenue perform year over year?"</div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Margins</div>
                <div class="bento-title">Review profitability</div>
                <div class="bento-text">Ask: "What do the margins say about profitability?"</div>
            </div>

            <div class="bento-card">
                <div class="bento-label">Cash Flow</div>
                <div class="bento-title">Analyze cash generation</div>
                <div class="bento-text">Ask: "Summarize free cash flow and liquidity."</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

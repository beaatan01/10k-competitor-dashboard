import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import html as py_html

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

def safe_html(content: str):
    st.markdown(content, unsafe_allow_html=True)


def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
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


def render_kpi_card(label, title, value, subtext, badge, badge_class=""):
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
    formula_html = ""
    if formula:
        formula_html = f'<div class="formula">{py_html.escape(formula)}</div>'

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

    note_html = ""
    if note:
        note_html = f'<div class="table-note">{py_html.escape(note)}</div>'

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
                    <thead>
                        <tr>{headers}</tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
        </div>
        """
    )


# ================================================================
# CSS
# ================================================================

safe_html(
    """
    <style>
    :root {
        --blue: #0078D4;
        --green: #7FBA00;
        --orange: #F25022;
        --yellow: #FFB900;
        --purple: #8661C5;

        --text: #F3F2F1;
        --muted: #AEB6C5;
        --muted2: #7D8798;

        --glass: rgba(13, 19, 32, 0.42);
        --glass-soft: rgba(255, 255, 255, 0.045);
        --border: rgba(255, 255, 255, 0.12);
        --border-blue: rgba(0, 120, 212, 0.48);

        --shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
        --shadow-hover: 0 26px 68px rgba(0, 0, 0, 0.50);
    }

    html, body, .stApp {
        color: var(--text) !important;
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    body {
        background: #030814 !important;
    }

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
        0% {
            background-position: 0% 0%, 100% 0%, 70% 100%, 0% 0%;
        }
        50% {
            background-position: 18% 10%, 86% 18%, 60% 84%, 50% 50%;
        }
        100% {
            background-position: 6% 18%, 74% 10%, 82% 70%, 100% 100%;
        }
    }

    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }

    [data-testid="stAppViewContainer"] > .main {
        background: transparent !important;
    }

    .block-container {
        max-width: 1500px !important;
        padding: 1.05rem 1.35rem 2.25rem 1.35rem !important;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    h1, h2, h3, h4, h5, h6, p, span, div, button, label, input, textarea {
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.34rem;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 999px;
        padding: 0.30rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }

    .stTabs [data-baseweb="tab"] {
        height: 34px;
        padding: 0 0.72rem;
        border-radius: 999px !important;
        color: rgba(218,226,238,0.66);
        font-weight: 680;
        font-size: 0.735rem;
        transition: all 0.16s ease !important;
        border: 1px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        border-radius: 999px !important;
        background: rgba(255,255,255,0.075) !important;
        color: #E6F4FF !important;
        border-color: rgba(255,255,255,0.13);
    }

    .stTabs [aria-selected="true"] {
        border-radius: 999px !important;
        background: rgba(0,120,212,0.22) !important;
        border: 1px solid rgba(0,120,212,0.50) !important;
        color: #E6F4FF !important;
        box-shadow: 0 0 24px rgba(0,120,212,0.22);
    }

    .hero {
        position: relative;
        min-height: 154px;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.13);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.105), rgba(255,255,255,0.026)),
            rgba(10, 15, 28, 0.38);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        box-shadow: var(--shadow);
        padding: 1.05rem 1.25rem;
        overflow: hidden;
        margin-bottom: 1rem;
    }

    .hero::after {
        content: "";
        position: absolute;
        right: -120px;
        top: -120px;
        width: 280px;
        height: 280px;
        background: radial-gradient(circle, rgba(0,120,212,0.28), transparent 64%);
        pointer-events: none;
    }

    .hero-content {
        position: relative;
        z-index: 2;
        max-width: 930px;
    }

    .hero-topline {
        display: flex;
        align-items: center;
        gap: 0.48rem;
        color: #D9EEFF;
        font-size: 0.57rem;
        font-weight: 760;
        letter-spacing: 0.145em;
        text-transform: uppercase;
        margin-bottom: 0.46rem;
    }

    .logo-squares {
        width: 10px;
        height: 10px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2px;
        flex: 0 0 auto;
    }

    .logo-squares span:nth-child(1) { background: #F25022; }
    .logo-squares span:nth-child(2) { background: #7FBA00; }
    .logo-squares span:nth-child(3) { background: #0078D4; }
    .logo-squares span:nth-child(4) { background: #FFB900; }

    .hero-title {
        color: #FFFFFF;
        font-size: clamp(1.55rem, 1.95vw, 2.06rem);
        font-weight: 720;
        letter-spacing: -0.015em;
        line-height: 1.22;
        margin-bottom: 0.43rem;
        max-width: 700px;
    }

    .hero-subtitle {
        color: #C8CED9;
        font-size: 0.725rem;
        line-height: 1.58;
        max-width: 940px;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.38rem;
        margin-top: 0.70rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.27rem 0.48rem;
        border-radius: 999px;
        color: #DDE5F0;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.115);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        font-size: 0.595rem;
        font-weight: 700;
    }

    .pill.blue {
        color: #E0F2FF;
        background: rgba(0,120,212,0.18);
        border-color: rgba(0,120,212,0.42);
    }

    .section-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 0.85rem;
        margin: 1rem 0 0.54rem 0;
    }

    .section-title {
        color: #FFFFFF;
        font-size: 0.845rem;
        font-weight: 740;
        letter-spacing: 0.002em;
        line-height: 1.32;
    }

    .section-subtitle {
        color: var(--muted2);
        font-size: 0.665rem;
        line-height: 1.48;
        margin-top: 0.16rem;
    }

    .section-tag {
        color: #DDF1FF;
        background: rgba(0,120,212,0.15);
        border: 1px solid rgba(0,120,212,0.36);
        border-radius: 999px;
        padding: 0.28rem 0.50rem;
        font-size: 0.60rem;
        font-weight: 740;
        white-space: nowrap;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }

    .kpi-card,
    .capability-card,
    .info-card,
    .scenario-card,
    .insight-card,
    .chart-title-card,
    .table-card {
        position: relative;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.125);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.095), rgba(255,255,255,0.022)),
            rgba(12, 18, 31, 0.36);
        backdrop-filter: blur(26px);
        -webkit-backdrop-filter: blur(26px);
        box-shadow: var(--shadow);
        overflow: hidden;
        transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }

    .kpi-card:hover,
    .capability-card:hover,
    .info-card:hover,
    .scenario-card:hover,
    .insight-card:hover {
        transform: translateY(-4px);
        border-color: rgba(0,120,212,0.55);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.035)),
            rgba(14, 21, 37, 0.48);
        box-shadow: var(--shadow-hover);
    }

    .kpi-card {
        min-height: 114px;
        padding: 0.76rem;
        margin-bottom: 0.72rem;
    }

    .capability-card,
    .info-card,
    .scenario-card {
        min-height: 104px;
        padding: 0.76rem;
        margin-bottom: 0.72rem;
    }

    .card-label {
        color: #D9EEFF;
        font-size: 0.54rem;
        font-weight: 780;
        letter-spacing: 0.145em;
        text-transform: uppercase;
        margin-bottom: 0.36rem;
    }

    .card-title {
        color: #D8DEE9;
        font-size: 0.70rem;
        font-weight: 700;
        line-height: 1.32;
        letter-spacing: 0.003em;
        margin-bottom: 0.36rem;
    }

    .card-value {
        color: #FFFFFF;
        font-size: 1.14rem;
        font-weight: 780;
        letter-spacing: -0.025em;
        margin-bottom: 0.24rem;
    }

    .card-sub {
        color: #AAB2C1;
        font-size: 0.60rem;
        line-height: 1.38;
        margin-bottom: 0.46rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.31rem;
        padding: 0.245rem 0.415rem;
        border-radius: 999px;
        color: #DDF1FF;
        border: 1px solid rgba(0,120,212,0.34);
        background: rgba(0,120,212,0.15);
        font-size: 0.555rem;
        font-weight: 760;
    }

    .badge.green {
        color: #E7FAC2;
        border-color: rgba(127,186,0,0.38);
        background: rgba(127,186,0,0.145);
    }

    .badge.orange {
        color: #FFC7BD;
        border-color: rgba(242,80,34,0.36);
        background: rgba(242,80,34,0.14);
    }

    .dot {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        background: currentColor;
        box-shadow: 0 0 10px currentColor;
        display: inline-block;
    }

    .capability-title,
    .info-title,
    .scenario-title {
        color: #FFFFFF;
        font-size: 0.80rem;
        font-weight: 720;
        margin-bottom: 0.30rem;
        letter-spacing: 0.006em;
        line-height: 1.35;
    }

    .capability-text,
    .info-text,
    .scenario-text {
        color: #AAB2C1;
        font-size: 0.63rem;
        line-height: 1.46;
    }

    .scenario-value {
        color: #FFFFFF;
        font-size: 1.12rem;
        font-weight: 780;
        letter-spacing: -0.028em;
        margin-bottom: 0.24rem;
    }

    .formula {
        margin-top: 0.46rem;
        padding: 0.36rem 0.46rem;
        color: #DDF1FF;
        background: rgba(0,120,212,0.13);
        border: 1px solid rgba(0,120,212,0.30);
        border-radius: 10px;
        font-size: 0.56rem;
        font-weight: 700;
    }

    .insight-card {
        padding: 0.78rem 0.85rem;
        margin-top: 0.35rem;
        margin-bottom: 0.72rem;
        border-color: rgba(0,120,212,0.30);
    }

    .insight-label {
        color: #DDF1FF;
        font-size: 0.56rem;
        font-weight: 780;
        letter-spacing: 0.145em;
        text-transform: uppercase;
        margin-bottom: 0.36rem;
    }

    .insight-text {
        color: #DDE3EE;
        font-size: 0.66rem;
        line-height: 1.54;
    }

    .chart-title-card {
        min-height: 46px;
        padding: 0.60rem 0.70rem;
        margin-bottom: 0.50rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chart-title {
        color: #FFFFFF;
        font-size: 0.70rem;
        font-weight: 720;
        line-height: 1.32;
    }

    .chart-caption {
        color: #8F99AA;
        font-size: 0.57rem;
        font-weight: 680;
    }

    .table-card {
        padding: 0.82rem;
        margin-bottom: 0.9rem;
    }

    .table-card-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.58rem;
    }

    .table-title {
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 720;
        line-height: 1.35;
    }

    .table-note {
        color: var(--muted2);
        font-size: 0.58rem;
        margin-top: 0.12rem;
    }

    .table-wrap {
        overflow-x: auto;
        border-radius: 13px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(5,8,18,0.32);
    }

    table.finance-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.64rem;
        color: #DDE3EE;
        min-width: 520px;
    }

    .finance-table th {
        background: rgba(255,255,255,0.055);
        color: #DDF1FF;
        text-align: left;
        font-weight: 720;
        padding: 0.46rem 0.54rem;
        border-bottom: 1px solid rgba(255,255,255,0.09);
        white-space: nowrap;
    }

    .finance-table td {
        padding: 0.46rem 0.54rem;
        border-bottom: 1px solid rgba(255,255,255,0.060);
        color: #D6DCE7;
        white-space: nowrap;
    }

    .finance-table tr:hover td {
        background: rgba(0,120,212,0.08);
    }

    h3 {
        color: #FFFFFF !important;
        font-size: 0.82rem !important;
        font-weight: 720 !important;
        margin: 0.52rem 0 0.42rem 0 !important;
    }

    .stDownloadButton button,
    .stButton button {
        font-size: 0.62rem !important;
        padding: 0.35rem 0.60rem !important;
        border-radius: 999px !important;
        color: #FFFFFF !important;
        background: rgba(0,120,212,0.68) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        box-shadow: 0 10px 22px rgba(0,120,212,0.20);
        backdrop-filter: blur(18px);
    }

    .stTextArea textarea,
    .stTextInput input {
        color: #F3F2F1 !important;
        background: rgba(15,20,34,0.35) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important;
        font-size: 0.70rem !important;
        backdrop-filter: blur(20px);
    }

    .stTextArea textarea:focus,
    .stTextInput input:focus {
        border-color: rgba(0,120,212,0.60) !important;
        box-shadow: 0 0 0 3px rgba(0,120,212,0.16) !important;
    }

    .stTextArea label,
    .stTextInput label,
    .stSlider label {
        color: #AAB2C1 !important;
        font-size: 0.62rem !important;
        font-weight: 720 !important;
        text-transform: uppercase;
        letter-spacing: 0.10em;
    }

    @media (max-width: 760px) {
        .block-container {
            padding: 1rem !important;
        }

        .hero {
            min-height: 170px;
            padding: 0.95rem;
        }

        .hero-title {
            font-size: 1.42rem;
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
# Plotly Styling
# ================================================================

def style_fig(fig, height=236, showlegend=False):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Segoe UI, Inter, sans-serif",
            color="#C9D0DC",
            size=10,
        ),
        margin=dict(l=34, r=18, t=8, b=30),
        hovermode="x unified",
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.03,
            xanchor="right",
            x=1,
            font=dict(color="#C9D0DC", size=9),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linewidth=1,
            linecolor="rgba(255,255,255,0.11)",
            tickfont=dict(color="#8D97A8", size=9),
            title_font=dict(color="#8D97A8", size=10),
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,0.060)",
            zeroline=False,
            showline=False,
            tickfont=dict(color="#8D97A8", size=9),
            title_font=dict(color="#8D97A8", size=10),
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
    safe_html(
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
                    <span class="pill">Executive Analytics</span>
                </div>
            </div>
        </div>
        """
    )

    render_section(
        "Strategic Platform Capabilities",
        "A polished executive overview of the dashboard's core finance, analytics, forecasting, and commentary layers.",
        "Executive Summary",
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        render_capability_card(
            "Finance Model",
            "Statement Intelligence",
            "Transforms financial statement data into structured income, balance sheet, and cash flow views.",
        )

    with c2:
        render_capability_card(
            "Performance",
            "KPI Intelligence",
            "Summarizes revenue, profitability, free cash flow, liquidity, and operating performance.",
        )

    with c3:
        render_capability_card(
            "Outlook",
            "Forecasting Engine",
            "Simulates bear, base, and bull case revenue outcomes using forward growth assumptions.",
        )

    with c4:
        render_capability_card(
            "Narrative",
            "AI Commentary Layer",
            "Turns financial metrics into plain-English executive commentary for business interpretation.",
        )

    render_section(
        "Executive Snapshot",
        "A quick view of the latest reported financial signals powering the platform.",
        "FY2025 View",
    )

    s1, s2, s3, s4 = st.columns(4, gap="medium")

    with s1:
        render_kpi_card(
            "Revenue",
            "FY2025 Revenue",
            fmt_cur(k["revenue"]),
            "Latest annual revenue in the dataset.",
            f"{fmt_pct(k['revenue_yoy_growth'])} YoY",
            "green",
        )

    with s2:
        render_kpi_card(
            "Margin",
            "Operating Margin",
            fmt_pct(k["operating_margin"]),
            f"Gross {fmt_pct(k['gross_margin'])} · Net {fmt_pct(k['net_margin'])}",
            "Profitability",
        )

    with s3:
        render_kpi_card(
            "Cash Flow",
            "Free Cash Flow",
            fmt_cur(k["free_cash_flow"]),
            "Operating cash flow less capital expenditures.",
            "Cash generative",
            "green",
        )

    with s4:
        render_kpi_card(
            "Liquidity",
            "Cash Balance",
            fmt_cur(k["cash_balance"]),
            f"Debt {fmt_cur(k['total_debt'])}",
            "Balance sheet",
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

    render_section(
        "Executive KPI Intelligence",
        "Compact indicators for scale, efficiency, cash generation, and financial flexibility.",
        "CFO View",
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        render_kpi_card(
            "Revenue Intelligence",
            f"FY{k['latest_period']} Revenue",
            fmt_cur(revenue),
            "Total reported revenue.",
            f"{fmt_pct(revenue_yoy)} YoY",
            "green",
        )

    with c2:
        render_kpi_card(
            "Profitability Signals",
            "Operating Margin",
            fmt_pct(operating_margin),
            f"Gross {fmt_pct(gross_margin)} · Net {fmt_pct(net_margin)}",
            "Margin profile",
        )

    with c3:
        render_kpi_card(
            "Cash Flow Engine",
            "Free Cash Flow",
            fmt_cur(fcf),
            "Operating cash flow less capex.",
            "Cash generative",
            "green",
        )

    with c4:
        render_kpi_card(
            "Balance Sheet Health",
            "Cash and Debt",
            fmt_cur(cash_balance),
            f"Debt {fmt_cur(total_debt)} · {debt_to_cash:.1f}x debt/cash",
            "Liquidity",
        )

    render_section(
        "Performance Drivers",
        "Short explanations for how each KPI should be interpreted.",
        "Metric Guide",
    )

    e1, e2, e3, e4 = st.columns(4, gap="medium")

    with e1:
        render_info_card(
            "Revenue",
            "Business Scale",
            "Measures top-line size and growth momentum.",
            "Growth = Current / Prior - 1",
        )

    with e2:
        render_info_card(
            "Margin",
            "Operating Efficiency",
            "Shows how efficiently revenue turns into operating income.",
            "Operating Income / Revenue",
        )

    with e3:
        render_info_card(
            "Cash Flow",
            "Financial Output",
            "Shows cash available after capital spending.",
            "OCF - Capex",
        )

    with e4:
        render_info_card(
            "Liquidity",
            "Balance Sheet Flexibility",
            "Shows the relationship between cash and debt.",
            "Debt / Cash",
        )

# ================================================================
# Revenue Intelligence
# ================================================================

with tab_revenue:
    services_mix = k["service_revenue_mix"]
    growth_spread = k["revenue"] - k["prior_year_revenue"]

    render_section(
        "Revenue Performance",
        "Historical revenue trend, mix, and growth interpretation.",
        "Growth Analytics",
    )

    r1, r2, r3 = st.columns(3, gap="medium")

    with r1:
        render_kpi_card(
            "FY2025 Revenue",
            "Total Revenue",
            fmt_cur(k["revenue"]),
            "Latest annual revenue.",
            f"{fmt_pct(k['revenue_yoy_growth'])} YoY",
            "green",
        )

    with r2:
        render_kpi_card(
            "Revenue Mix",
            "Service and Other",
            fmt_pct(services_mix),
            "Share of FY2025 revenue.",
            "Largest category",
        )

    with r3:
        render_kpi_card(
            "Growth Spread",
            "2025 vs 2024",
            fmt_cur(growth_spread),
            "Incremental revenue added.",
            "Expansion",
            "green",
        )

    left, right = st.columns(2, gap="medium")

    with left:
        render_chart_title("Revenue Over Time", "FY2023-FY2025")

        fig_ts = px.line(
            ts,
            x="period",
            y="revenue",
            markers=True,
            color_discrete_sequence=["#0078D4"],
        )

        fig_ts.update_traces(
            line=dict(width=3, shape="spline"),
            marker=dict(size=7, color="#0078D4", line=dict(width=1.5, color="#DDF1FF")),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
        )

        fig_ts.update_yaxes(tickprefix="$", ticksuffix="M")
        fig_ts = style_fig(fig_ts, height=238)
        st.plotly_chart(fig_ts, width="stretch", config={"displayModeBar": False})

    with right:
        render_chart_title("Revenue Mix by Category", "Product vs Service")

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
        fig_seg = style_fig(fig_seg, height=238, showlegend=True)
        st.plotly_chart(fig_seg, width="stretch", config={"displayModeBar": False})

    render_insight(
        "Revenue Commentary",
        (
            f"Microsoft generated {fmt_cur(k['revenue'])} in FY2025 revenue, representing "
            f"{fmt_pct(k['revenue_yoy_growth'])} year-over-year growth. Service and other revenue represented "
            f"approximately {fmt_pct(services_mix)} of total revenue."
        ),
    )

# ================================================================
# AI Forecasting
# ================================================================

with tab_forecast:
    render_section(
        "Revenue Outlook Model",
        "Adjust revenue growth assumptions and compare scenario outcomes.",
        "Scenario Model",
    )

    s_col1, s_col2 = st.columns(2, gap="medium")

    with s_col1:
        growth_rate_pct = st.slider(
            "Base Case Revenue Growth Assumption",
            min_value=0,
            max_value=30,
            value=12,
            step=1,
        )

    with s_col2:
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

    f1, f2, f3 = st.columns(3, gap="medium")

    with f1:
        render_scenario_card(
            "Bear Case",
            "Conservative Growth",
            fmt_cur(bear_last["revenue"]),
            f"Projected FY{int(bear_last['year'])} revenue.",
        )

    with f2:
        render_scenario_card(
            "Base Case",
            "Selected Assumption",
            fmt_cur(base_last["revenue"]),
            f"Projected FY{int(base_last['year'])} revenue.",
        )

    with f3:
        render_scenario_card(
            "Bull Case",
            "Upside Growth",
            fmt_cur(bull_last["revenue"]),
            f"Projected FY{int(bull_last['year'])} revenue.",
        )

    render_chart_title("Historical Revenue + Forecast Scenarios", "Historical and projected revenue")

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
                line=dict(color=color, width=2.4, dash="dash"),
                marker=dict(size=6),
                hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:,.0f}M<extra></extra>",
            )
        )

    fig_forecast.update_yaxes(tickprefix="$", ticksuffix="M")
    fig_forecast = style_fig(fig_forecast, height=260, showlegend=True)
    st.plotly_chart(fig_forecast, width="stretch", config={"displayModeBar": False})

    latest_forecast = forecast_df.iloc[-1]

    render_insight(
        "Forecast Narrative",
        (
            f"Using a base growth assumption of {growth_rate_pct:.0f}%, projected revenue reaches "
            f"{fmt_cur(latest_forecast['revenue'])} by FY{int(latest_forecast['year'])}. "
            f"This is a simplified scenario simulator, not a formal investment forecast."
        ),
    )

# ================================================================
# Financial Statements
# ================================================================

with tab_financials:
    financials = result["financials"]

    render_section(
        "Financial Statements",
        "Core statement tables used by the KPI engine.",
        "Statement Tables",
    )

    f1, f2 = st.columns(2, gap="medium")

    with f1:
        render_financial_table(
            "Income Statement",
            financials["income"],
            "Values shown in millions.",
        )

        st.download_button(
            label="Download Income Statement CSV",
            data=dataframe_to_csv(financials["income"]),
            file_name="microsoft_income_statement.csv",
            mime="text/csv",
        )

    with f2:
        render_financial_table(
            "Balance Sheet",
            financials["balance"],
            "Values shown in millions.",
        )

        st.download_button(
            label="Download Balance Sheet CSV",
            data=dataframe_to_csv(financials["balance"]),
            file_name="microsoft_balance_sheet.csv",
            mime="text/csv",
        )

    render_financial_table(
        "Cash Flow Statement",
        financials["cashflow"],
        "Values shown in millions.",
    )

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
    render_section(
        "AI Copilot for Financial Commentary",
        "Ask about revenue, margins, cash flow, liquidity, or forecasting.",
        "Narrative AI",
    )

    question = st.text_area(
        "Ask a financial question",
        value="Summarize Microsoft revenue, margins, and cash flow.",
        height=90,
    )

    response = answer_question(question, benchmark_df, kpis=k)

    render_insight(
        "Generated Financial Commentary",
        response,
    )

    render_section(
        "Example Questions",
        "Use these prompts to test the commentary engine.",
        "Prompt Ideas",
    )

    p1, p2, p3 = st.columns(3, gap="medium")

    with p1:
        render_capability_card(
            "Revenue",
            "Explain Revenue Growth",
            "Try: How did Microsoft's revenue perform year over year?",
        )

    with p2:
        render_capability_card(
            "Margins",
            "Review Profitability",
            "Try: What do the margins say about profitability?",
        )

    with p3:
        render_capability_card(
            "Cash Flow",
            "Analyze Cash Generation",
            "Try: Summarize free cash flow and liquidity.",
        )

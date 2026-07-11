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
# Core Helpers
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


def render_kpi_card(label, title, value, subtext, badge, badge_class=""):
    card = f"""
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
    safe_html(card)


def render_info_card(label, title, text, formula=None):
    formula_html = ""
    if formula:
        formula_html = f'<div class="formula">{py_html.escape(formula)}</div>'

    card = f"""
    <div class="info-card">
        <div class="card-label">{py_html.escape(label)}</div>
        <div class="info-title">{py_html.escape(title)}</div>
        <div class="info-text">{py_html.escape(text)}</div>
        {formula_html}
    </div>
    """
    safe_html(card)


def render_bento_card(label, title, text, large=False):
    large_class = "large-card" if large else ""
    card = f"""
    <div class="bento-card {large_class}">
        <div class="card-label">{py_html.escape(label)}</div>
        <div class="bento-title">{py_html.escape(title)}</div>
        <div class="bento-text">{py_html.escape(text)}</div>
    </div>
    """
    safe_html(card)


def render_scenario_card(label, title, value, text):
    card = f"""
    <div class="scenario-card">
        <div class="card-label">{py_html.escape(label)}</div>
        <div class="scenario-title">{py_html.escape(title)}</div>
        <div class="scenario-value">{py_html.escape(value)}</div>
        <div class="scenario-text">{py_html.escape(text)}</div>
    </div>
    """
    safe_html(card)


def render_insight(title, text):
    card = f"""
    <div class="insight-card">
        <div class="insight-label">{py_html.escape(title)}</div>
        <div class="insight-text">{py_html.escape(text)}</div>
    </div>
    """
    safe_html(card)


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

    table_html = f"""
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
    safe_html(table_html)


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

        --glass: rgba(16, 21, 34, 0.34);
        --glass-strong: rgba(18, 23, 36, 0.48);
        --glass-soft: rgba(255, 255, 255, 0.045);

        --border: rgba(255, 255, 255, 0.10);
        --border-blue: rgba(0, 120, 212, 0.46);

        --shadow: 0 16px 42px rgba(0, 0, 0, 0.38);
        --shadow-hover: 0 24px 64px rgba(0, 0, 0, 0.55);
    }

    html, body, .stApp {
        background: #040816 !important;
        color: var(--text) !important;
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ------------------------------------------------------------
       Reliable moving aurora background
       ------------------------------------------------------------ */
    .aurora-bg {
        position: fixed;
        inset: 0;
        overflow: hidden;
        z-index: 0;
        pointer-events: none;
        background:
            radial-gradient(circle at 20% 0%, rgba(0, 120, 212, 0.12), transparent 32%),
            linear-gradient(135deg, #04111f 0%, #050817 45%, #06120d 100%);
    }

    .aurora-blob {
        position: absolute;
        width: 58vw;
        height: 58vw;
        min-width: 560px;
        min-height: 560px;
        border-radius: 999px;
        filter: blur(92px);
        opacity: 0.62;
        mix-blend-mode: screen;
        will-change: transform;
    }

    .aurora-blob.one {
        left: -15%;
        top: -22%;
        background: radial-gradient(circle, rgba(0,120,212,0.75), rgba(0,120,212,0.10), transparent 66%);
        animation: driftOne 18s ease-in-out infinite alternate;
    }

    .aurora-blob.two {
        right: -18%;
        top: -20%;
        background: radial-gradient(circle, rgba(127,186,0,0.45), rgba(127,186,0,0.08), transparent 64%);
        animation: driftTwo 22s ease-in-out infinite alternate;
    }

    .aurora-blob.three {
        left: 28%;
        bottom: -34%;
        background: radial-gradient(circle, rgba(134,97,197,0.62), rgba(134,97,197,0.10), transparent 64%);
        animation: driftThree 24s ease-in-out infinite alternate;
    }

    .aurora-blob.four {
        right: 18%;
        bottom: -36%;
        background: radial-gradient(circle, rgba(242,80,34,0.26), rgba(242,80,34,0.07), transparent 66%);
        animation: driftFour 20s ease-in-out infinite alternate;
    }

    .aurora-vignette {
        position: absolute;
        inset: 0;
        background:
            linear-gradient(180deg, rgba(4,8,22,0.08), rgba(4,8,22,0.78)),
            radial-gradient(circle at 50% 6%, rgba(255,255,255,0.055), transparent 36%);
        z-index: 2;
    }

    @keyframes driftOne {
        from { transform: translate3d(-2%, -3%, 0) scale(1.00); }
        to   { transform: translate3d(12%, 9%, 0) scale(1.10); }
    }

    @keyframes driftTwo {
        from { transform: translate3d(3%, -2%, 0) scale(1.00); }
        to   { transform: translate3d(-10%, 12%, 0) scale(1.08); }
    }

    @keyframes driftThree {
        from { transform: translate3d(-4%, 4%, 0) scale(1.00); }
        to   { transform: translate3d(8%, -8%, 0) scale(1.12); }
    }

    @keyframes driftFour {
        from { transform: translate3d(5%, 6%, 0) scale(1.00); }
        to   { transform: translate3d(-8%, -7%, 0) scale(1.08); }
    }

    [data-testid="stAppViewContainer"] {
        background: transparent !important;
    }

    .block-container {
        position: relative;
        z-index: 3;
        max-width: 1520px !important;
        padding: 1.10rem 1.45rem 2.2rem 1.45rem !important;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    h1, h2, h3, h4, h5, h6, p, span, div, button, label, input, textarea {
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ------------------------------------------------------------
       Tabs - rounded pill hover and active state
       ------------------------------------------------------------ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.42rem;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.075);
        border-radius: 999px;
        padding: 0.32rem;
        margin-bottom: 1.05rem;
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
    }

    .stTabs [data-baseweb="tab"] {
        height: 34px;
        padding: 0 0.76rem;
        border-radius: 999px !important;
        color: rgba(215,222,234,0.58);
        font-weight: 720;
        font-size: 0.74rem;
        transition: all 0.16s ease !important;
        border: 1px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        border-radius: 999px !important;
        background: rgba(255,255,255,0.075) !important;
        color: #E5F3FF !important;
        border-color: rgba(255,255,255,0.12);
    }

    .stTabs [aria-selected="true"] {
        border-radius: 999px !important;
        background: rgba(0,120,212,0.20) !important;
        border: 1px solid rgba(0,120,212,0.48) !important;
        color: #E5F3FF !important;
        box-shadow: 0 0 24px rgba(0,120,212,0.18);
    }

    /* ------------------------------------------------------------
       Hero
       ------------------------------------------------------------ */
    .hero {
        position: relative;
        min-height: 152px;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.12);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.10), rgba(255,255,255,0.025)),
            rgba(15,20,34,0.36);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        box-shadow: var(--shadow);
        padding: 1.05rem 1.25rem;
        overflow: hidden;
        margin-bottom: 1.05rem;
    }

    .hero::before {
        content: "";
        position: absolute;
        inset: -60%;
        background:
            radial-gradient(circle at 18% 32%, rgba(0,120,212,0.52), transparent 28%),
            radial-gradient(circle at 78% 22%, rgba(127,186,0,0.25), transparent 24%),
            radial-gradient(circle at 66% 72%, rgba(134,97,197,0.38), transparent 28%);
        filter: blur(70px);
        opacity: 0.78;
        animation: heroGlow 16s ease-in-out infinite alternate;
    }

    @keyframes heroGlow {
        from { transform: translate3d(-2%, -2%, 0) scale(1.0); }
        to   { transform: translate3d(5%, 4%, 0) scale(1.06); }
    }

    .hero-content {
        position: relative;
        z-index: 2;
        max-width: 920px;
    }

    .hero-topline {
        display: flex;
        align-items: center;
        gap: 0.50rem;
        color: #D8EEFF;
        font-size: 0.58rem;
        font-weight: 820;
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
        font-size: clamp(1.42rem, 1.95vw, 2.02rem);
        font-weight: 760;
        letter-spacing: -0.028em;
        line-height: 1.15;
        margin-bottom: 0.42rem;
        max-width: 780px;
    }

    .hero-subtitle {
        color: #C8CED9;
        font-size: 0.72rem;
        line-height: 1.55;
        max-width: 930px;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.42rem;
        margin-top: 0.72rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.28rem 0.50rem;
        border-radius: 999px;
        color: #DDE4EF;
        background: rgba(255,255,255,0.060);
        border: 1px solid rgba(255,255,255,0.12);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        font-size: 0.60rem;
        font-weight: 740;
    }

    .pill.blue {
        color: #DDF1FF;
        background: rgba(0,120,212,0.18);
        border-color: rgba(0,120,212,0.40);
    }

    /* ------------------------------------------------------------
       Sections
       ------------------------------------------------------------ */
    .section-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1rem;
        margin: 1.05rem 0 0.62rem 0;
    }

    .section-title {
        color: #FFFFFF;
        font-size: 0.84rem;
        font-weight: 820;
        letter-spacing: -0.015em;
    }

    .section-subtitle {
        color: var(--muted2);
        font-size: 0.68rem;
        line-height: 1.45;
        margin-top: 0.16rem;
    }

    .section-tag {
        color: #DDF1FF;
        background: rgba(0,120,212,0.16);
        border: 1px solid rgba(0,120,212,0.38);
        border-radius: 999px;
        padding: 0.30rem 0.52rem;
        font-size: 0.61rem;
        font-weight: 820;
        white-space: nowrap;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
    }

    /* ------------------------------------------------------------
       Glass Cards
       ------------------------------------------------------------ */
    .kpi-card,
    .bento-card,
    .info-card,
    .scenario-card,
    .insight-card,
    .chart-title-card,
    .table-card {
        position: relative;
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.12);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.09), rgba(255,255,255,0.025)),
            rgba(15,20,34,0.34);
        backdrop-filter: blur(26px);
        -webkit-backdrop-filter: blur(26px);
        box-shadow: var(--shadow);
        overflow: hidden;
        transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
    }

    .kpi-card:hover,
    .bento-card:hover,
    .info-card:hover,
    .scenario-card:hover,
    .insight-card:hover {
        transform: translateY(-4px);
        border-color: rgba(0,120,212,0.52);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.11), rgba(255,255,255,0.035)),
            rgba(16,22,38,0.42);
        box-shadow: var(--shadow-hover);
    }

    .kpi-card::before,
    .bento-card::before,
    .info-card::before,
    .scenario-card::before,
    .insight-card::before {
        content: "";
        position: absolute;
        width: 230px;
        height: 230px;
        right: -92px;
        top: -108px;
        background: radial-gradient(circle, rgba(0,120,212,0.25), transparent 68%);
        opacity: 0;
        transition: opacity 0.18s ease;
        pointer-events: none;
    }

    .kpi-card:hover::before,
    .bento-card:hover::before,
    .info-card:hover::before,
    .scenario-card:hover::before,
    .insight-card:hover::before {
        opacity: 1;
    }

    .kpi-card {
        min-height: 118px;
        padding: 0.78rem;
        margin-bottom: 0.95rem;
    }

    .bento-card,
    .info-card,
    .scenario-card {
        min-height: 108px;
        padding: 0.78rem;
        margin-bottom: 0.95rem;
    }

    .card-label {
        color: #D8EEFF;
        font-size: 0.55rem;
        font-weight: 850;
        letter-spacing: 0.145em;
        text-transform: uppercase;
        margin-bottom: 0.38rem;
    }

    .card-title {
        color: #D8DEE9;
        font-size: 0.70rem;
        font-weight: 760;
        line-height: 1.25;
        margin-bottom: 0.38rem;
    }

    .card-value {
        color: #FFFFFF;
        font-size: 1.16rem;
        font-weight: 820;
        letter-spacing: -0.035em;
        margin-bottom: 0.25rem;
    }

    .card-sub {
        color: #AAB2C1;
        font-size: 0.60rem;
        line-height: 1.36;
        margin-bottom: 0.48rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.32rem;
        padding: 0.25rem 0.42rem;
        border-radius: 999px;
        color: #DDF1FF;
        border: 1px solid rgba(0,120,212,0.34);
        background: rgba(0,120,212,0.16);
        font-size: 0.56rem;
        font-weight: 820;
    }

    .badge.green {
        color: #E7FAC2;
        border-color: rgba(127,186,0,0.38);
        background: rgba(127,186,0,0.15);
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

    .bento-title,
    .info-title,
    .scenario-title {
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 820;
        margin-bottom: 0.30rem;
        letter-spacing: -0.015em;
    }

    .bento-text,
    .info-text,
    .scenario-text {
        color: #AAB2C1;
        font-size: 0.63rem;
        line-height: 1.44;
    }

    .scenario-value {
        color: #FFFFFF;
        font-size: 1.12rem;
        font-weight: 820;
        letter-spacing: -0.035em;
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
        font-weight: 760;
    }

    .insight-card {
        padding: 0.78rem 0.85rem;
        margin-top: 0.35rem;
        margin-bottom: 0.95rem;
        border-color: rgba(0,120,212,0.30);
    }

    .insight-label {
        color: #DDF1FF;
        font-size: 0.56rem;
        font-weight: 850;
        letter-spacing: 0.145em;
        text-transform: uppercase;
        margin-bottom: 0.36rem;
    }

    .insight-text {
        color: #DDE3EE;
        font-size: 0.66rem;
        line-height: 1.52;
    }

    /* ------------------------------------------------------------
       Charts
       ------------------------------------------------------------ */
    .chart-title-card {
        min-height: 48px;
        padding: 0.62rem 0.72rem;
        margin-bottom: 0.55rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .chart-title {
        color: #FFFFFF;
        font-size: 0.70rem;
        font-weight: 820;
    }

    .chart-caption {
        color: #8F99AA;
        font-size: 0.57rem;
        font-weight: 760;
    }

    /* ------------------------------------------------------------
       Architecture
       ------------------------------------------------------------ */
    .architecture-grid {
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 0.62rem;
        margin-top: 0.45rem;
    }

    .arch-step {
        min-height: 58px;
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.11);
        background: rgba(255,255,255,0.052);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #DDE3EE;
        font-size: 0.60rem;
        font-weight: 760;
        text-align: center;
        padding: 0.45rem;
    }

    /* ------------------------------------------------------------
       Financial tables - no white Streamlit dataframes
       ------------------------------------------------------------ */
    .table-card {
        padding: 0.82rem;
        margin-bottom: 1.15rem;
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
        font-weight: 820;
        letter-spacing: -0.015em;
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
        background: rgba(5,8,18,0.30);
    }

    table.finance-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.64rem;
        color: #DDE3EE;
        min-width: 520px;
    }

    .finance-table th {
        background: rgba(255,255,255,0.060);
        color: #DDF1FF;
        text-align: left;
        font-weight: 820;
        padding: 0.48rem 0.56rem;
        border-bottom: 1px solid rgba(255,255,255,0.09);
        white-space: nowrap;
    }

    .finance-table td {
        padding: 0.48rem 0.56rem;
        border-bottom: 1px solid rgba(255,255,255,0.065);
        color: #D6DCE7;
        white-space: nowrap;
    }

    .finance-table tr:hover td {
        background: rgba(0,120,212,0.08);
    }

    /* ------------------------------------------------------------
       Streamlit native UI
       ------------------------------------------------------------ */
    h3 {
        color: #FFFFFF !important;
        font-size: 0.82rem !important;
        font-weight: 820 !important;
        margin: 0.55rem 0 0.45rem 0 !important;
    }

    .stDownloadButton button,
    .stButton button {
        font-size: 0.62rem !important;
        padding: 0.36rem 0.62rem !important;
        border-radius: 999px !important;
        color: #FFFFFF !important;
        background: rgba(0,120,212,0.70) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        box-shadow: 0 10px 22px rgba(0,120,212,0.20);
        backdrop-filter: blur(18px);
    }

    .stTextArea textarea,
    .stTextInput input {
        color: #F3F2F1 !important;
        background: rgba(15,20,34,0.40) !important;
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
        font-weight: 820 !important;
        text-transform: uppercase;
        letter-spacing: 0.10em;
    }

    @media (max-width: 1100px) {
        .architecture-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
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
            font-size: 1.45rem;
        }

        .architecture-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """
)

# ================================================================
# Actual Aurora HTML Layer
# ================================================================

safe_html(
    """
    <div class="aurora-bg">
        <div class="aurora-blob one"></div>
        <div class="aurora-blob two"></div>
        <div class="aurora-blob three"></div>
        <div class="aurora-blob four"></div>
        <div class="aurora-vignette"></div>
    </div>
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
                    <span class="pill">Aurora Glass UI</span>
                </div>
            </div>
        </div>
        """
    )

    render_section(
        "What This Project Demonstrates",
        "A compact finance product combining statement analysis, KPI modeling, forecasting, visualization, and AI-style storytelling.",
        "Project Overview",
    )

    top1, top2 = st.columns([2, 1], gap="large")
    with top1:
        render_bento_card(
            "Overview",
            "Financial Statement Intelligence",
            "Converts Microsoft's annual financial statement data into a polished executive analytics experience focused on revenue, profitability, cash flow, and liquidity.",
            large=True,
        )
    with top2:
        render_bento_card(
            "KPI Engine",
            "Executive Metrics",
            "Calculates growth, margins, free cash flow, cash, debt, and revenue mix into concise finance KPIs.",
        )

    b1, b2, b3 = st.columns(3, gap="large")
    with b1:
        render_bento_card(
            "Revenue",
            "Revenue Intelligence",
            "Trend and mix views show how total revenue and category revenue evolved over time.",
        )
    with b2:
        render_bento_card(
            "Forecasting",
            "Scenario Engine",
            "Growth assumptions produce bear, base, and bull revenue cases.",
        )
    with b3:
        render_bento_card(
            "AI Copilot",
            "Narrative Commentary",
            "Plain-English commentary translates financial metrics into business interpretation.",
        )

    render_section(
        "Platform Workflow",
        "How the application moves from financial data to executive insights.",
        "Architecture",
    )

    safe_html(
        """
        <div class="architecture-grid">
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

    render_section(
        "Executive KPI Intelligence",
        "Compact indicators for scale, efficiency, cash generation, and financial flexibility.",
        "CFO View",
    )

    c1, c2, c3, c4 = st.columns(4, gap="large")
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
        "How To Read The KPIs",
        "Short explanations for what each metric means.",
        "Metric Guide",
    )

    e1, e2, e3, e4 = st.columns(4, gap="large")
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
        "Revenue Intelligence",
        "Historical revenue trend, mix, and growth interpretation.",
        "Growth Analytics",
    )

    r1, r2, r3 = st.columns(3, gap="large")
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

    left, right = st.columns(2, gap="large")

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
        st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})

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
        st.plotly_chart(fig_seg, use_container_width=True, config={"displayModeBar": False})

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
        "AI Forecasting Simulator",
        "Adjust revenue growth assumptions and compare scenario outcomes.",
        "Scenario Model",
    )

    s_col1, s_col2 = st.columns(2, gap="large")
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

    f1, f2, f3 = st.columns(3, gap="large")
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
    st.plotly_chart(fig_forecast, use_container_width=True, config={"displayModeBar": False})

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

    f1, f2 = st.columns(2, gap="large")

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

    p1, p2, p3 = st.columns(3, gap="large")

    with p1:
        render_bento_card(
            "Revenue",
            "Explain revenue growth",
            "Try: How did Microsoft's revenue perform year over year?",
        )

    with p2:
        render_bento_card(
            "Margins",
            "Review profitability",
            "Try: What do the margins say about profitability?",
        )

    with p3:
        render_bento_card(
            "Cash Flow",
            "Analyze cash generation",
            "Try: Summarize free cash flow and liquidity.",
        )

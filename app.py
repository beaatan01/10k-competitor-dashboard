import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from tenk_engine import (
    process_uploaded_file,
    build_benchmark_dataframe,
    answer_question,
)

# ================================================================
# Page Setup
# ================================================================

st.set_page_config(
    page_title="Microsoft 10-K Dashboard",
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
        --ms-blue-soft: rgba(0, 120, 212, 0.16);
        --ms-orange: #F25022;
        --ms-green: #7FBA00;
        --ms-yellow: #FFB900;

        --bg: #070A12;
        --bg-2: #0B0F1A;
        --panel: #10141F;
        --panel-2: #121826;
        --panel-3: #151B2B;
        --border: rgba(255,255,255,0.075);
        --border-strong: rgba(0,120,212,0.45);

        --text: #F3F2F1;
        --muted: #9EA0A6;
        --muted-2: #6F7684;
        --shadow: 0 18px 52px rgba(0,0,0,0.45);
        --shadow-soft: 0 10px 30px rgba(0,0,0,0.35);
        --radius: 20px;
    }

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background:
            radial-gradient(circle at 12% 5%, rgba(0,120,212,0.18), transparent 30%),
            radial-gradient(circle at 90% 0%, rgba(127,186,0,0.11), transparent 28%),
            linear-gradient(135deg, #070A12 0%, #0B0F1A 42%, #070A12 100%) !important;
        color: var(--text) !important;
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .block-container {
        max-width: 1480px !important;
        padding-top: 2.1rem !important;
        padding-left: 2.25rem !important;
        padding-right: 2.25rem !important;
        padding-bottom: 3rem !important;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #080B13 0%, #0B0F1A 60%, #070A12 100%) !important;
        border-right: 1px solid var(--border) !important;
    }

    [data-testid="stSidebarContent"] {
        padding: 1.4rem 1.1rem !important;
    }

    .sidebar-brand {
        padding: 1rem;
        border: 1px solid var(--border);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
        box-shadow: var(--shadow-soft);
        margin-bottom: 1.1rem;
    }

    .brand-kicker {
        font-size: 0.72rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.13em;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }

    .brand-title {
        font-size: 1rem;
        color: var(--text);
        font-weight: 700;
        line-height: 1.25;
    }

    .sidebar-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.48rem 0.66rem;
        border-radius: 999px;
        background: rgba(0,120,212,0.12);
        border: 1px solid rgba(0,120,212,0.28);
        color: #D5ECFF;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .sidebar-dot {
        width: 7px;
        height: 7px;
        background: var(--ms-green);
        border-radius: 999px;
        box-shadow: 0 0 12px rgba(127,186,0,0.7);
    }

    /* Inputs */
    .stTextInput label {
        color: var(--muted) !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.11em;
    }

    .stTextInput input {
        background: #0F1422 !important;
        color: var(--text) !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 12px !important;
        min-height: 44px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
    }

    .stTextInput input:focus {
        border-color: rgba(0,120,212,0.75) !important;
        box-shadow: 0 0 0 4px rgba(0,120,212,0.16) !important;
    }

    /* Header */
    .hero {
        position: relative;
        padding: 1.45rem 1.55rem;
        border-radius: 24px;
        border: 1px solid var(--border);
        background:
            linear-gradient(135deg, rgba(255,255,255,0.066), rgba(255,255,255,0.018)),
            radial-gradient(circle at 95% 10%, rgba(0,120,212,0.24), transparent 32%);
        box-shadow: var(--shadow);
        overflow: hidden;
        margin-bottom: 1.6rem;
    }

    .hero:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 3px;
        width: 160px;
        background: linear-gradient(90deg, var(--ms-blue), transparent);
    }

    .hero-topline {
        display: flex;
        gap: 0.8rem;
        align-items: center;
        margin-bottom: 0.75rem;
        color: #D5ECFF;
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.15em;
        text-transform: uppercase;
    }

    .hero-logo {
        width: 12px;
        height: 12px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2px;
    }

    .hero-logo span:nth-child(1) { background: #F25022; }
    .hero-logo span:nth-child(2) { background: #7FBA00; }
    .hero-logo span:nth-child(3) { background: #0078D4; }
    .hero-logo span:nth-child(4) { background: #FFB900; }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3.1rem);
        line-height: 1.02;
        letter-spacing: -0.055em;
        color: var(--text);
        font-weight: 750;
        margin-bottom: 0.75rem;
        max-width: 1050px;
    }

    .hero-subtitle {
        color: #AEB5C1;
        font-size: 1rem;
        line-height: 1.65;
        max-width: 980px;
    }

    .hero-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.7rem;
        margin-top: 1.1rem;
    }

    .meta-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.48rem 0.68rem;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.035);
        color: #C8CCD2;
        font-size: 0.76rem;
        font-weight: 650;
    }

    .meta-pill.blue {
        border-color: rgba(0,120,212,0.35);
        background: rgba(0,120,212,0.12);
        color: #D5ECFF;
    }

    /* Sections */
    .section-head {
        display: flex;
        justify-content: space-between;
        align-items: end;
        margin: 1.85rem 0 0.9rem 0;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 750;
        color: var(--text);
        letter-spacing: -0.015em;
    }

    .section-subtitle {
        margin-top: 0.25rem;
        color: var(--muted);
        font-size: 0.83rem;
    }

    .section-tag {
        color: #D5ECFF;
        background: rgba(0,120,212,0.12);
        border: 1px solid rgba(0,120,212,0.28);
        border-radius: 999px;
        padding: 0.42rem 0.64rem;
        font-size: 0.74rem;
        font-weight: 750;
    }

    /* KPI cards */
    .kpi-card {
        position: relative;
        min-height: 190px;
        border-radius: var(--radius);
        border: 1px solid var(--border);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
            #10141F;
        box-shadow: var(--shadow-soft);
        padding: 1.15rem;
        overflow: hidden;
        transition: 0.18s ease;
    }

    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: var(--border-strong);
        box-shadow: var(--shadow);
    }

    .kpi-card:after {
        content: "";
        position: absolute;
        right: -40px;
        top: -42px;
        width: 132px;
        height: 132px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(0,120,212,0.22), transparent 62%);
        pointer-events: none;
    }

    .kpi-label {
        color: var(--muted);
        font-size: 0.71rem;
        font-weight: 800;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.65rem;
    }

    .kpi-name {
        color: #CBD2DC;
        font-size: 0.9rem;
        line-height: 1.35;
        font-weight: 650;
        margin-bottom: 0.7rem;
    }

    .kpi-value {
        font-size: 2.15rem;
        font-weight: 760;
        color: #FFFFFF;
        letter-spacing: -0.045em;
        margin-bottom: 0.4rem;
    }

    .kpi-sub {
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.45;
        margin-bottom: 1rem;
    }

    .kpi-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.44rem;
        font-size: 0.74rem;
        font-weight: 750;
        padding: 0.42rem 0.62rem;
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

    /* Chart shell */
    .chart-shell {
        border-radius: var(--radius);
        border: 1px solid var(--border);
        background:
            linear-gradient(145deg, rgba(255,255,255,0.048), rgba(255,255,255,0.015)),
            #10141F;
        box-shadow: var(--shadow-soft);
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
        font-size: 0.94rem;
        font-weight: 750;
        letter-spacing: -0.01em;
    }

    .chart-caption {
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 650;
    }

    .insight-card {
        border-radius: var(--radius);
        border: 1px solid rgba(0,120,212,0.24);
        background:
            radial-gradient(circle at 0% 0%, rgba(0,120,212,0.17), transparent 38%),
            linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.018)),
            #10141F;
        box-shadow: var(--shadow);
        padding: 1.15rem 1.2rem;
        margin-top: 0.5rem;
    }

    .insight-title {
        color: #D5ECFF;
        font-size: 0.78rem;
        font-weight: 850;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .insight-text {
        color: #D9DEE7;
        line-height: 1.65;
        font-size: 0.95rem;
    }

    /* Make dataframes darker */
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

    .stDataFrame {
        background: #10141F !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: "Segoe UI", Inter, -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    h3 {
        color: var(--text) !important;
        font-size: 1rem !important;
        font-weight: 750 !important;
        margin-top: 0.6rem !important;
        margin-bottom: 0.7rem !important;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1.1rem !important;
            padding-right: 1.1rem !important;
        }

        .hero {
            padding: 1.2rem;
        }

        .kpi-card {
            min-height: 170px;
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

# ================================================================
# Formatting Helpers
# ================================================================

def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    return f"${v:,.0f}M"

def fmt_pct(v):
    return "N/A" if v is None else f"{v*100:.1f}%"

def human_metric(v):
    if v is None:
        return "N/A"
    return f"${v:,.0f}M"

# ================================================================
# Sidebar
# ================================================================

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-kicker">Financial Analytics</div>
            <div class="brand-title">Microsoft 10-K<br/>Executive Dashboard</div>
        </div>
        <div class="sidebar-chip">
            <span class="sidebar-dot"></span>
            FY2025 filing view
        </div>
        """,
        unsafe_allow_html=True,
    )

    question = st.text_input(
        "Ask a financial question",
        value="Summarize Microsoft revenue, margins, and cash flow."
    )

    st.markdown(
        """
        <div style="height: 1rem;"></div>
        <div style="
            color:#6F7684;
            font-size:0.76rem;
            line-height:1.55;
            padding:0.85rem;
            border-radius:14px;
            background:rgba(255,255,255,0.025);
            border:1px solid rgba(255,255,255,0.06);
        ">
            Built as an analyst workspace for revenue, profitability, liquidity, and cash flow review.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Header
# ================================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-topline">
            <div class="hero-logo">
                <span></span><span></span><span></span><span></span>
            </div>
            Microsoft Fluent UI Inspired Dashboard
        </div>
        <div class="hero-title">Microsoft 2025 10-K Financial Statement Analysis</div>
        <div class="hero-subtitle">
            The 2026 Microsoft 10-K has not yet been released. This dashboard reflects the most up-to-date
            financial information available from the 2025 filing, organized for CFO, finance, and analytics review.
        </div>
        <div class="hero-meta-row">
            <span class="meta-pill blue">FY2025</span>
            <span class="meta-pill">Revenue, margins, cash flow</span>
            <span class="meta-pill">Dark enterprise analytics</span>
            <span class="meta-pill">Hard-coded 10-K fallback</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================================================================
# KPI Cards
# ================================================================

revenue = k["revenue"]
revenue_yoy = k["revenue_yoy_growth"]
gross_margin = k["gross_margin"]
operating_margin = k["operating_margin"]
net_margin = k["net_margin"]
fcf = k["free_cash_flow"]
cash_balance = k["cash_balance"]
total_debt = k["total_debt"]

st.markdown(
    """
    <div class="section-head">
        <div>
            <div class="section-title">Executive KPI Overview</div>
            <div class="section-subtitle">High-level indicators for growth, profitability, and liquidity.</div>
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
            <div class="kpi-label">Revenue</div>
            <div class="kpi-name">Fiscal Year {k['latest_period']}</div>
            <div class="kpi-value">{fmt_cur(revenue)}</div>
            <div class="kpi-sub">Total reported revenue for latest fiscal year.</div>
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
            <div class="kpi-label">Profitability</div>
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
            <div class="kpi-label">Cash Flow</div>
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
    debt_to_cash = total_debt / cash_balance if cash_balance else None
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Liquidity</div>
            <div class="kpi-name">Cash and Debt</div>
            <div class="kpi-value">{fmt_cur(cash_balance)}</div>
            <div class="kpi-sub">Total debt {fmt_cur(total_debt)} · Debt/cash {debt_to_cash:.1f}x</div>
            <div class="kpi-badge">
                <span class="badge-dot"></span>Balance sheet
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ================================================================
# Chart Theme Helper
# ================================================================

def style_fig(fig, height=360, showlegend=False):
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
# Charts
# ================================================================

st.markdown(
    """
    <div class="section-head">
        <div>
            <div class="section-title">Performance Analytics</div>
            <div class="section-subtitle">Trend and margin visuals styled directly inside Plotly.</div>
        </div>
        <div class="section-tag">Interactive Charts</div>
    </div>
    """,
    unsafe_allow_html=True,
)

ts = k["time_series"].copy()

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
    fig_ts = style_fig(fig_ts, height=345)
    st.plotly_chart(fig_ts, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        """
        <div class="chart-shell">
            <div class="chart-heading">
                <div class="chart-title">Margin Profile</div>
                <div class="chart-caption">Latest fiscal year</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    latest_row = ts[ts["period"] == k["latest_period"]].iloc[0]
    margin_df = pd.DataFrame(
        {
            "metric": ["Gross Margin", "Operating Margin", "Net Margin"],
            "margin": [
                latest_row["gross_margin"],
                latest_row["operating_margin"],
                latest_row["net_margin"],
            ],
        }
    )

    fig_margin = px.bar(
        margin_df,
        x="metric",
        y="margin",
        color="metric",
        text_auto=".1%",
        color_discrete_map={
            "Gross Margin": "#7FBA00",
            "Operating Margin": "#0078D4",
            "Net Margin": "#F25022",
        },
    )
    fig_margin.update_traces(
        marker_line_width=0,
        textfont=dict(color="#FFFFFF", size=12),
        hovertemplate="<b>%{x}</b><br>Margin: %{y:.1%}<extra></extra>",
    )
    fig_margin.update_yaxes(tickformat=".0%")
    fig_margin = style_fig(fig_margin, height=345)
    st.plotly_chart(fig_margin, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)

left2, right2 = st.columns(2, gap="large")

with left2:
    st.markdown(
        """
        <div class="chart-shell">
            <div class="chart-heading">
                <div class="chart-title">Operating Cash Flow and Free Cash Flow</div>
                <div class="chart-caption">Cash generation</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    ts_cf = ts[["period", "operating_cash_flow", "free_cash_flow"]]
    ts_cf_long = ts_cf.melt(
        id_vars=["period"],
        value_vars=["operating_cash_flow", "free_cash_flow"],
        var_name="metric",
        value_name="value",
    )
    metric_labels = {
        "operating_cash_flow": "Operating Cash Flow",
        "free_cash_flow": "Free Cash Flow",
    }
    ts_cf_long["metric"] = ts_cf_long["metric"].map(metric_labels)

    fig_cf = px.line(
        ts_cf_long,
        x="period",
        y="value",
        color="metric",
        markers=True,
        color_discrete_map={
            "Operating Cash Flow": "#0078D4",
            "Free Cash Flow": "#7FBA00",
        },
    )
    fig_cf.update_traces(
        line=dict(width=3, shape="spline"),
        marker=dict(size=8, line=dict(width=2, color="#10141F")),
        hovertemplate="<b>%{x}</b><br>%{y:,.0f}M<extra></extra>",
    )
    fig_cf.update_yaxes(tickprefix="$", ticksuffix="M")
    fig_cf = style_fig(fig_cf, height=345, showlegend=True)
    st.plotly_chart(fig_cf, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)

with right2:
    st.markdown(
        """
        <div class="chart-shell">
            <div class="chart-heading">
                <div class="chart-title">Revenue Mix by Category</div>
                <div class="chart-caption">Product vs service revenue</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    segment_df = k.get("segment_revenue")
    if segment_df is not None and not segment_df.empty:
        seg_long = segment_df.melt(
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
        fig_seg = style_fig(fig_seg, height=345, showlegend=True)
        st.plotly_chart(fig_seg, use_container_width=True, config={"displayModeBar": False})
    else:
        fig_rev = px.bar(
            benchmark_df,
            x="company",
            y="revenue",
            text_auto=".2s",
            color_discrete_sequence=["#0078D4"],
        )
        fig_rev.update_traces(marker_line_width=0)
        fig_rev.update_yaxes(tickprefix="$", ticksuffix="M")
        fig_rev = style_fig(fig_rev, height=345)
        st.plotly_chart(fig_rev, use_container_width=True, config={"displayModeBar": False})

    st.markdown("</div>", unsafe_allow_html=True)

# ================================================================
# Tables
# ================================================================

st.markdown(
    """
    <div class="section-head">
        <div>
            <div class="section-title">Financial Statements</div>
            <div class="section-subtitle">Core financial statement tables in dark mode.</div>
        </div>
        <div class="section-tag">Statements</div>
    </div>
    """,
    unsafe_allow_html=True,
)

t1, t2 = st.columns(2, gap="large")

with t1:
    st.subheader("Income Statement")
    st.dataframe(result["financials"]["income"], use_container_width=True, hide_index=True)

with t2:
    st.subheader("Balance Sheet")
    st.dataframe(result["financials"]["balance"], use_container_width=True, hide_index=True)

st.subheader("Cash Flow Statement")
st.dataframe(result["financials"]["cashflow"], use_container_width=True, hide_index=True)

# ================================================================
# AI Insight
# ================================================================

st.markdown(
    """
    <div class="section-head">
        <div>
            <div class="section-title">AI-Style Insight</div>
            <div class="section-subtitle">Natural-language explanation based on the benchmark dataframe.</div>
        </div>
        <div class="section-tag">Analyst Summary</div>
    </div>
    """,
    unsafe_allow_html=True,
)

insight = answer_question(question, benchmark_df)

st.markdown(
    f"""
    <div class="insight-card">
        <div class="insight-title">Generated Financial Commentary</div>
        <div class="insight-text">{insight}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

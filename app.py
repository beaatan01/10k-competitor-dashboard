import streamlit as st
import plotly.express as px
import pandas as pd

from tenk_engine import (
    process_uploaded_file,
    build_benchmark_dataframe,
    format_display_dataframe,
    answer_question,
)

# ================================================================
# Page Setup
# ================================================================

st.set_page_config(page_title="Microsoft 10-K Dashboard", layout="wide")

# Global dark theme + card CSS
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #0b0c10;
        color: #f3f2f1;
        font-family: "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
    }

    h1, h2, h3, h4 {
        color: #f3f2f1;
    }

    /* Card container */
    .kpi-row {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .kpi-card {
        background: #111319;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        border: 1px solid rgba(255,255,255,0.04);
        flex: 1 1 260px;
        min-width: 260px;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 18px 40px rgba(0,0,0,0.55);
        border-color: rgba(0,120,212,0.7);
    }

    .kpi-label {
        font-size: 0.75rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #9ea0a6;
        margin-bottom: 4px;
    }

    .kpi-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f3f2f1;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #f3f2f1;
        margin-bottom: 4px;
    }

    .kpi-sub {
        font-size: 0.85rem;
        color: #9ea0a6;
    }

    .kpi-pill {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        margin-top: 8px;
        background: rgba(0,120,212,0.12);
        color: #cfe6ff;
    }

    .kpi-pill.negative {
        background: rgba(242,80,34,0.12);
        color: #ffd0c4;
    }

    .kpi-pill span.dot {
        width: 6px;
        height: 6px;
        border-radius: 999px;
        margin-right: 6px;
        background: #0078d4;
    }

    .kpi-pill.negative span.dot {
        background: #f25022;
    }

    /* Tabs styling */
    .stTabs [role="tablist"] {
        gap: 0.5rem;
    }

    .stTabs [role="tab"] {
        padding: 0.4rem 0.9rem;
        border-radius: 999px;
        background-color: #111319;
        color: #cfd2da;
        border: 1px solid rgba(255,255,255,0.04);
    }

    .stTabs [role="tab"][aria-selected="true"] {
        background-color: #0078d4;
        color: #ffffff;
        border-color: #0078d4;
    }

    /* Dataframe background */
    .stDataFrame, .stTable {
        background-color: #111319;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================================================================
# Header
# ================================================================

st.markdown(
    """
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin-bottom: 0.2rem;">Microsoft 2025 10‑K Financial Statement Analysis</h1>
        <p style="color:#9ea0a6; font-size:0.9rem; max-width:720px;">
            The 2026 Microsoft 10‑K has not yet been released. This dashboard reflects the most up‑to‑date
            financial information available from the 2025 filing, presented from a financial analyst and CFO perspective.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ================================================================
# Load Microsoft data (A1 Hard)
# ================================================================

result = process_uploaded_file()
company_results = {"Microsoft": result}
benchmark_df = build_benchmark_dataframe(company_results)
k = result["kpis"]

# ================================================================
# Sidebar Question Input
# ================================================================

question = st.sidebar.text_input(
    "Ask a financial question",
    value="Summarize Microsoft revenue, margins, and cash flow."
)

# ================================================================
# KPI Cards Row (Dark Fluent UI style)
# ================================================================

revenue = k["revenue"]
revenue_yoy = k["revenue_yoy_growth"]
gross_margin = k["gross_margin"]
operating_margin = k["operating_margin"]
net_margin = k["net_margin"]
fcf = k["free_cash_flow"]
cash_balance = k["cash_balance"]
total_debt = k["total_debt"]

def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    return f"${v:,.0f}"

def fmt_pct(v):
    return "N/A" if v is None else f"{v*100:.1f}%"

st.markdown('<div class="kpi-row">', unsafe_allow_html=True)

# Revenue card
st.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">Revenue</div>
        <div class="kpi-title">Fiscal Year {k['latest_period']}</div>
        <div class="kpi-value">{fmt_cur(revenue)}</div>
        <div class="kpi-sub">Year-over-year growth</div>
        <div class="kpi-pill {'negative' if revenue_yoy < 0 else ''}">
            <span class="dot"></span>
            {fmt_pct(revenue_yoy)} vs prior year
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Margin card
st.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">Profitability</div>
        <div class="kpi-title">Margin Profile</div>
        <div class="kpi-value">{fmt_pct(operating_margin)}</div>
        <div class="kpi-sub">
            Gross margin: {fmt_pct(gross_margin)} · Net margin: {fmt_pct(net_margin)}
        </div>
        <div class="kpi-pill">
            <span class="dot"></span>
            Operating margin reflects Microsoft's ability to convert revenue into operating profit.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Cash & FCF card
st.markdown(
    f"""
    <div class="kpi-card">
        <div class="kpi-label">Liquidity & Cash Flow</div>
        <div class="kpi-title">Cash and Free Cash Flow</div>
        <div class="kpi-value">{fmt_cur(fcf)}</div>
        <div class="kpi-sub">
            Cash balance: {fmt_cur(cash_balance)} · Total debt: {fmt_cur(total_debt)}
        </div>
        <div class="kpi-pill">
            <span class="dot"></span>
            Strong free cash flow supports ongoing investment, capital returns, and balance sheet resilience.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# Tabs
# ================================================================

kpi_tab, chart_tab, table_tab, insight_tab = st.tabs([
    "Benchmark KPIs",
    "Charts",
    "Financial Tables",
    "AI-Style Insights",
])

# ================================================================
# KPI TAB
# ================================================================

with kpi_tab:
    st.subheader("Benchmark KPIs")

    st.dataframe(
        format_display_dataframe(benchmark_df),
        use_container_width=True,
        hide_index=True,
    )

# ================================================================
# CHART TAB
# ================================================================

with chart_tab:
    st.subheader("Financial Charts")

    fig_rev = px.bar(
        benchmark_df,
        x="company",
        y="revenue",
        text_auto=".2s",
        title="Latest Revenue",
        color_discrete_sequence=["#0078D4"],
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    margin_cols = ["gross_margin", "operating_margin", "net_margin"]
    margin_long = benchmark_df.melt(
        id_vars=["company", "year"],
        value_vars=margin_cols,
        var_name="metric",
        value_name="margin",
    )

    fig_margin = px.bar(
        margin_long,
        x="company",
        y="margin",
        color="metric",
        barmode="group",
        text_auto=".1%",
        title="Latest Margins",
        color_discrete_map={
            "gross_margin": "#7FBA00",
            "operating_margin": "#0078D4",
            "net_margin": "#F25022",
        },
    )
    fig_margin.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_margin, use_container_width=True)

    ts = result["kpis"]["time_series"]
    fig_ts = px.line(
        ts,
        x="period",
        y="revenue",
        markers=True,
        title="Revenue Over Time",
        color_discrete_sequence=["#0078D4"],
    )
    st.plotly_chart(fig_ts, use_container_width=True)

# ================================================================
# FINANCIAL TABLES TAB
# ================================================================

with table_tab:
    st.subheader("Income Statement")
    st.dataframe(result["financials"]["income"], use_container_width=True)

    st.subheader("Balance Sheet")
    st.dataframe(result["financials"]["balance"], use_container_width=True)

    st.subheader("Cash Flow Statement")
    st.dataframe(result["financials"]["cashflow"], use_container_width=True)

# ================================================================
# AI INSIGHT TAB
# ================================================================

with insight_tab:
    st.subheader("AI-Style Insight")
    st.write(answer_question(question, benchmark_df))

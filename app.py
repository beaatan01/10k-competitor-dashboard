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

st.title("📊 Microsoft 2025 10‑K Financial Statement Analysis")
st.caption(
    "The 2026 Microsoft 10‑K has not yet been released. "
    "This dashboard reflects the most up‑to‑date financial information available."
)

# ================================================================
# Always load Microsoft (A1 Hard)
# ================================================================

result = process_uploaded_file()
company_results = {"Microsoft": result}

benchmark_df = build_benchmark_dataframe(company_results)

# ================================================================
# Sidebar Question Input
# ================================================================

question = st.sidebar.text_input(
    "Ask a financial question",
    value="Summarize Microsoft revenue, margins, and cash flow."
)

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

    # Revenue Bar
    fig_rev = px.bar(
        benchmark_df,
        x="company",
        y="revenue",
        text_auto=".2s",
        title="Latest Revenue",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Margin Bar
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
    )
    fig_margin.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_margin, use_container_width=True)

    # Time Series
    ts = result["kpis"]["time_series"]
    fig_ts = px.line(
        ts,
        x="period",
        y="revenue",
        markers=True,
        title="Revenue Over Time",
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

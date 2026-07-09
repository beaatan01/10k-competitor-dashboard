import re

import pandas as pd
import plotly.express as px
import streamlit as st

from tenk_engine import (
    answer_question,
    apply_manual_statement_selection,
    build_benchmark_dataframe,
    format_display_dataframe,
    process_uploaded_file,
    raw_table_label,
)


st.set_page_config(page_title="10-K Competitor Dashboard", layout="wide")

st.title("10-K Competitor Dashboard")
st.caption(
    "Upload 10-K filings, review extracted tables, manually map financial statements if needed, "
    "and benchmark KPIs across companies."
)


def safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)


with st.sidebar:
    st.header("Inputs")

    uploaded_files = st.file_uploader(
        "Upload 10-K filings",
        type=["pdf", "html", "htm", "txt"],
        accept_multiple_files=True,
    )

    question = st.text_input(
        "Ask a financial question",
        value="Compare margins and cash flow.",
    )


if not uploaded_files:
    st.info("Upload at least one 10-K filing to begin.")
    st.stop()


company_results = {}

for file in uploaded_files:
    with st.spinner(f"Processing {file.name}..."):
        try:
            result = process_uploaded_file(file)
            name = result["company"]

            original_name = name
            counter = 2

            while name in company_results:
                name = f"{original_name} ({counter})"
                counter += 1

            company_results[name] = result

        except Exception as error:
            st.error(f"Could not process {file.name}: {error}")


if not company_results:
    st.warning("No files could be processed.")
    st.stop()


with st.sidebar:
    st.header("Manual Statement Mapping")
    st.caption("Use this when Benchmark KPIs show N/A or Period is None.")

    manual_settings = {}

    for company, result in company_results.items():
        raw_tables = result.get("raw_tables", [])
        company_key = safe_key(company)

        with st.expander(company, expanded=False):
            if not raw_tables:
                st.info("No raw tables were extracted.")
                manual_settings[company] = {
                    "income": -1,
                    "balance": -1,
                    "cashflow": -1,
                }
                continue

            table_options = [-1] + list(range(len(raw_tables)))

            income_index = st.selectbox(
                "Income Statement",
                options=table_options,
                format_func=lambda idx, tables=raw_tables: (
                    "Auto-detect / None"
                    if idx == -1
                    else raw_table_label(idx, tables[idx])
                ),
                key=f"{company_key}_income_table",
            )

            balance_index = st.selectbox(
                "Balance Sheet",
                options=table_options,
                format_func=lambda idx, tables=raw_tables: (
                    "Auto-detect / None"
                    if idx == -1
                    else raw_table_label(idx, tables[idx])
                ),
                key=f"{company_key}_balance_table",
            )

            cashflow_index = st.selectbox(
                "Cash Flow Statement",
                options=table_options,
                format_func=lambda idx, tables=raw_tables: (
                    "Auto-detect / None"
                    if idx == -1
                    else raw_table_label(idx, tables[idx])
                ),
                key=f"{company_key}_cashflow_table",
            )

            manual_settings[company] = {
                "income": income_index,
                "balance": balance_index,
                "cashflow": cashflow_index,
            }


for company, settings in manual_settings.items():
    if any(index != -1 for index in settings.values()):
        company_results[company] = apply_manual_statement_selection(
            result=company_results[company],
            income_index=settings["income"],
            balance_index=settings["balance"],
            cashflow_index=settings["cashflow"],
        )


benchmark_df = build_benchmark_dataframe(company_results)

kpi_tab, chart_tab, table_tab, debug_tab, insight_tab = st.tabs([
    "Benchmark KPIs",
    "Charts",
    "Financial Tables",
    "Extraction Debug",
    "AI-Style Insights",
])


with kpi_tab:
    st.subheader("Benchmark KPIs")

    if benchmark_df.empty:
        st.warning("No usable KPI data was extracted.")
    else:
        st.dataframe(
            format_display_dataframe(benchmark_df),
            width="stretch",
            hide_index=True,
        )

    st.subheader("Extraction Status")

    status_rows = []

    for company, result in company_results.items():
        financials = result.get("financials", {})

        status_rows.append({
            "company": company,
            "tables_detected": result.get("table_count", 0),
            "income_statement_detected": not financials.get("income", pd.DataFrame()).empty,
            "balance_sheet_detected": not financials.get("balance", pd.DataFrame()).empty,
            "cash_flow_detected": not financials.get("cashflow", pd.DataFrame()).empty,
            "manual_selection_applied": result.get("manual_selection_applied", False),
            "extraction_confidence": result.get("confidence", "Unknown"),
        })

    st.dataframe(
        pd.DataFrame(status_rows),
        width="stretch",
        hide_index=True,
    )

    st.info(
        "If Benchmark KPIs show N/A, use the sidebar Manual Statement Mapping controls. "
        "Pick the raw table that visually looks like the Income Statement, Balance Sheet, and Cash Flow Statement."
    )


with chart_tab:
    st.subheader("Competitor Comparison")

    if benchmark_df.empty:
        st.info("No benchmark data available for charts.")
    else:
        revenue_latest = benchmark_df.dropna(subset=["revenue"])

        if not revenue_latest.empty:
            fig_revenue = px.bar(
                revenue_latest,
                x="company",
                y="revenue",
                text_auto=".2s",
                title="Latest Revenue Comparison",
            )
            st.plotly_chart(fig_revenue, width="stretch")
        else:
            st.info("Revenue data is not available yet.")

        margin_cols = [
            col for col in ["gross_margin", "operating_margin", "net_margin"]
            if col in benchmark_df.columns and benchmark_df[col].notna().any()
        ]

        if margin_cols:
            margin_long = benchmark_df.melt(
                id_vars=["company"],
                value_vars=margin_cols,
                var_name="metric",
                value_name="margin",
            ).dropna(subset=["margin"])

            fig_margin = px.bar(
                margin_long,
                x="company",
                y="margin",
                color="metric",
                barmode="group",
                text_auto=".1%",
                title="Latest Margin Comparison",
            )
            fig_margin.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_margin, width="stretch")
        else:
            st.info("Margin data is not available yet.")

        ts_frames = []

        for company, result in company_results.items():
            ts = result.get("kpis", {}).get("time_series")

            if isinstance(ts, pd.DataFrame) and not ts.empty:
                temp = ts.copy()
                temp["company"] = company
                ts_frames.append(temp)

        if ts_frames:
            full_ts = pd.concat(ts_frames, ignore_index=True)
            revenue_ts = full_ts.dropna(subset=["revenue"])

            if not revenue_ts.empty:
                fig_ts = px.line(
                    revenue_ts,
                    x="period",
                    y="revenue",
                    color="company",
                    markers=True,
                    title="Revenue Over Time",
                )
                st.plotly_chart(fig_ts, width="stretch")


with table_tab:
    selected_company = st.selectbox(
        "Select company",
        list(company_results.keys()),
        key="financial_table_company",
    )

    selected_result = company_results[selected_company]
    selected_financials = selected_result.get("financials", {})

    st.caption(
        f"Confidence: {selected_result.get('confidence', 'Unknown')} | "
        f"Manual selection applied: {selected_result.get('manual_selection_applied', False)}"
    )

    for key, label in [
        ("income", "Income Statement"),
        ("balance", "Balance Sheet"),
        ("cashflow", "Cash Flow Statement"),
    ]:
        st.subheader(label)

        df = selected_financials.get(key, pd.DataFrame())

        if df.empty:
            st.info(f"{label} was not selected or not confidently detected.")
        else:
            st.dataframe(df, width="stretch", hide_index=True)


with debug_tab:
    selected_company_debug = st.selectbox(
        "Select company for raw table review",
        list(company_results.keys()),
        key="debug_company",
    )

    selected_result = company_results[selected_company_debug]
    raw_tables = selected_result.get("raw_tables", [])

    st.write(f"Detected **{len(raw_tables)}** raw tables.")

    if not raw_tables:
        st.warning("No raw tables were extracted from this file.")
    else:
        st.info(
            "Review these raw tables, then use the sidebar to map the correct tables. "
            "Look for rows like Revenue, Net Income, Total Assets, Total Liabilities, "
            "Net Cash Provided by Operating Activities, and Capital Expenditures."
        )

        for idx, table in enumerate(raw_tables):
            with st.expander(
                f"Raw table {idx + 1} — {table.shape[0]} rows x {table.shape[1]} columns",
                expanded=False,
            ):
                st.dataframe(table, width="stretch")


with insight_tab:
    st.subheader("AI-Style Insight")

    if benchmark_df.empty:
        st.info("No benchmark data available yet.")
    elif question.strip():
        st.write(answer_question(question, benchmark_df))
    else:
        st.info("Enter a question in the sidebar.")

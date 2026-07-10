import io
import re
from pathlib import Path

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


DEFAULT_MICROSOFT_10K = Path("data/microsoft_10k.html")


class LocalFileAdapter:
    def __init__(self, path: Path, name: str):
        self.name = name
        self._buffer = io.BytesIO(path.read_bytes())

    def read(self):
        return self._buffer.read()

    def seek(self, position):
        return self._buffer.seek(position)


st.set_page_config(page_title="Microsoft 10-K Financial Dashboard", layout="wide")

st.title("Microsoft 10-K Financial Dashboard")
st.caption(
    "Microsoft financial statement extraction, KPI review, and trend analysis from the 10-K."
)


def safe_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)


def display_statement_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    display_df = df.copy()
    return display_df.astype(object).where(pd.notna(display_df), "")


with st.sidebar:
    st.header("Inputs")

    use_microsoft_default = st.checkbox(
        "Use built-in Microsoft 10-K",
        value=True,
    )

    uploaded_files = st.file_uploader(
        "Optional: upload additional 10-K filings",
        type=["pdf", "html", "htm", "txt"],
        accept_multiple_files=True,
    )

    question = st.text_input(
        "Ask a financial question",
        value="Summarize Microsoft revenue, margins, and cash flow.",
    )


files_to_process = []

if use_microsoft_default:
    if DEFAULT_MICROSOFT_10K.exists():
        files_to_process.append(
            LocalFileAdapter(DEFAULT_MICROSOFT_10K, "Microsoft_10-K.html")
        )
    else:
        st.sidebar.error("Missing built-in filing: data/microsoft_10k.html")

files_to_process.extend(uploaded_files or [])

if not files_to_process:
    st.info("Use the built-in Microsoft 10-K or upload at least one filing to begin.")
    st.stop()


company_results = {}

for file in files_to_process:
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
    st.caption("Use only if extraction selected the wrong raw table.")

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
            use_container_width=True,
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
        use_container_width=True,
        hide_index=True,
    )


with chart_tab:
    st.subheader("Financial Charts")

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
                title="Latest Revenue",
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("Revenue data is not available.")

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
                title="Latest Margins",
            )
            fig_margin.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig_margin, use_container_width=True)
        else:
            st.info("Margin data is not available.")

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
                st.plotly_chart(fig_ts, use_container_width=True)


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
            st.info(f"{label} was not detected or is not available.")
        else:
            st.dataframe(
                display_statement_dataframe(df),
                use_container_width=True,
                hide_index=True,
            )


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
            "Review these raw tables if extraction looks wrong. "
            "For the built-in Microsoft filing, the dashboard uses a curated fallback "
            "when extraction misses core income statement values."
        )

        for idx, table in enumerate(raw_tables):
            with st.expander(
                f"Raw table {idx + 1} — {table.shape[0]} rows x {table.shape[1]} columns",
                expanded=False,
            ):
                st.dataframe(
                    display_statement_dataframe(table),
                    use_container_width=True,
                )


with insight_tab:
    st.subheader("AI-Style Insight")

    if benchmark_df.empty:
        st.info("No benchmark data available.")
    elif question.strip():
        st.write(answer_question(question, benchmark_df))
    else:
        st.info("Enter a question in the sidebar.")

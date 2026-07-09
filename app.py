import io
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ================================================================
# File handling and text extraction
# ================================================================

def get_file_extension(file) -> str:
    return Path(file.name).suffix.lower().replace(".", "")


def read_uploaded_file_bytes(file) -> bytes:
    file.seek(0)
    data = file.read()
    file.seek(0)
    return data


def clean_whitespace(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"(?i)table of contents.*?(item\s+1\.)", r"\1", text, flags=re.DOTALL)
    return text.strip()


def remove_repeated_headers_footers(page_texts: List[str]) -> str:
    if not page_texts:
        return ""

    first_lines, last_lines, split_pages = [], [], []

    for page in page_texts:
        lines = [line.strip() for line in page.splitlines() if line.strip()]
        split_pages.append(lines)

        if lines:
            first_lines.extend(lines[:3])
            last_lines.extend(lines[-3:])

    repeated = set()

    for line in first_lines + last_lines:
        if len(line) < 120:
            count = sum(line in lines[:3] or line in lines[-3:] for lines in split_pages)
            if count >= max(2, len(split_pages) // 3):
                repeated.add(line)

    cleaned_pages = []

    for lines in split_pages:
        kept = [
            line for line in lines
            if line not in repeated
            and not re.fullmatch(r"\d+", line)
            and not re.fullmatch(r"page\s+\d+", line, flags=re.IGNORECASE)
        ]
        cleaned_pages.append("\n".join(kept))

    return "\n\n".join(cleaned_pages)


def extract_text(file) -> str:
    ext = get_file_extension(file)
    data = read_uploaded_file_bytes(file)

    if ext == "pdf":
        try:
            import pdfplumber
        except ImportError:
            st.error("PDF text extraction requires pdfplumber.")
            return ""

        page_texts = []

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                page_texts.append(text)

        return clean_whitespace(remove_repeated_headers_footers(page_texts))

    if ext in {"html", "htm"}:
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            st.error("HTML extraction requires beautifulsoup4.")
            return ""

        html = data.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        return clean_whitespace(soup.get_text(separator="\n"))

    if ext == "txt":
        return clean_whitespace(data.decode("utf-8", errors="ignore"))

    return ""


# ================================================================
# Table extraction
# ================================================================

def normalize_dataframe_shape(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = df.replace(r"^\s*$", np.nan, regex=True)
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)


def extract_tables_from_pdf_with_camelot(file_path: str) -> List[pd.DataFrame]:
    try:
        import camelot
    except ImportError:
        return []

    try:
        parsed = camelot.read_pdf(file_path, pages="all", flavor="stream")
        tables = []

        for table in parsed:
            df = normalize_dataframe_shape(table.df)
            if df.shape[0] >= 3 and df.shape[1] >= 2:
                tables.append(df)

        return tables

    except Exception:
        return []


def extract_tables_from_pdf_with_tabula(file_path: str) -> List[pd.DataFrame]:
    try:
        import tabula
    except ImportError:
        return []

    try:
        parsed = tabula.read_pdf(
            file_path,
            pages="all",
            multiple_tables=True,
            lattice=False,
            stream=True,
        )

        tables = []

        for df in parsed:
            df = normalize_dataframe_shape(df)
            if df.shape[0] >= 3 and df.shape[1] >= 2:
                tables.append(df)

        return tables

    except Exception:
        return []


def extract_tables_from_pdf_with_pdfplumber(data: bytes) -> List[pd.DataFrame]:
    try:
        import pdfplumber
    except ImportError:
        return []

    tables = []

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                df = normalize_dataframe_shape(pd.DataFrame(table))

                if df.shape[0] >= 3 and df.shape[1] >= 2:
                    tables.append(df)

    return tables


def extract_tables(file) -> List[pd.DataFrame]:
    ext = get_file_extension(file)
    data = read_uploaded_file_bytes(file)

    if ext == "pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(data)
            tmp.flush()

            tables = extract_tables_from_pdf_with_camelot(tmp.name)
            if tables:
                return tables

            tables = extract_tables_from_pdf_with_tabula(tmp.name)
            if tables:
                return tables

        return extract_tables_from_pdf_with_pdfplumber(data)

    if ext in {"html", "htm"}:
        html = data.decode("utf-8", errors="ignore")

        try:
            parsed = pd.read_html(io.StringIO(html))
        except ValueError:
            return []

        tables = []

        for df in parsed:
            df = normalize_dataframe_shape(df)
            if df.shape[0] >= 3 and df.shape[1] >= 2:
                tables.append(df)

        return tables

    return []


# ================================================================
# Financial statement identification
# ================================================================

def parse_financial_value(value: Any) -> Optional[float]:
    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    if text == "":
        return np.nan

    text = (
        text.replace("\u2014", "-")
        .replace("—", "-")
        .replace("–", "-")
        .replace("$", "")
        .replace(",", "")
        .replace("%", "")
    )

    lower_text = text.lower()

    if lower_text in {"-", "nm", "n/m", "na", "n/a", "none", "nan"}:
        return np.nan

    negative = bool(re.search(r"\(.*\)", text))
    text = text.replace("(", "").replace(")", "")

    multiplier = 1

    if "billion" in lower_text or "billions" in lower_text:
        multiplier = 1_000_000_000
    elif "million" in lower_text or "millions" in lower_text:
        multiplier = 1_000_000

    text = re.sub(r"(?i)\bmillion(s)?\b|\bbillion(s)?\b", "", text)

    matches = re.findall(r"-?\d+(?:\.\d+)?", text)

    if not matches:
        return np.nan

    numeric_text = matches[0]

    try:
        number = float(numeric_text) * multiplier
    except ValueError:
        return np.nan

    return -abs(number) if negative else number


def clean_line_item(value: Any) -> str:
    if pd.isna(value):
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def promote_header_row(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_dataframe_shape(df)

    if df.empty:
        return df

    best_row, best_score = None, -1

    for idx in range(min(5, len(df))):
        row = df.iloc[idx].tolist()

        score = sum(
            bool(re.search(r"20\d{2}|19\d{2}|three months|year ended|years ended", str(cell), re.I))
            for cell in row
        )

        score -= sum(str(cell).strip().lower() in {"", "nan"} for cell in row) * 0.25

        if score > best_score:
            best_score = score
            best_row = idx

    if best_row is not None and best_score > 0:
        new_columns = [
            clean_line_item(c) if clean_line_item(c) else f"Column_{i}"
            for i, c in enumerate(df.iloc[best_row].tolist())
        ]

        df = df.iloc[best_row + 1:].copy()
        df.columns = new_columns

    return normalize_dataframe_shape(df)


def make_unique_name(name: str, used: set) -> str:
    name = name or "value"
    original = name
    counter = 2

    while name in used:
        name = f"{original}_{counter}"
        counter += 1

    used.add(name)
    return name


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = promote_header_row(df)

    if df.empty:
        return df

    columns = [str(c).strip() for c in df.columns]

    renamed = {columns[0]: "line_item"}
    used = {"line_item"}

    for col in columns[1:]:
        raw = str(col)
        year = re.search(r"(20\d{2}|19\d{2})", raw)

        if year:
            name = year.group(1)
        else:
            name = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_") or "value"

        name = make_unique_name(name, used)
        renamed[col] = name

    df = df.rename(columns=renamed)

    if "line_item" not in df.columns:
        return pd.DataFrame()

    df["line_item"] = df["line_item"].map(clean_line_item)

    for col in df.columns:
        if col != "line_item":
            if isinstance(df[col], pd.DataFrame):
                continue
            df[col] = df[col].map(parse_financial_value)

    numeric_cols = [
        c for c in df.columns
        if c != "line_item" and not isinstance(df[c], pd.DataFrame) and df[c].notna().sum() > 0
    ]

    if not numeric_cols:
        return pd.DataFrame()

    df = df[["line_item"] + numeric_cols]
    df = df[df["line_item"].astype(str).str.len() > 0]
    df = df.drop_duplicates(subset=["line_item"], keep="first")

    return df.reset_index(drop=True)


def classify_statement(df: pd.DataFrame) -> Optional[str]:
    text = " ".join(df.fillna("").astype(str).values.flatten()).lower()

    scores = {
        "income": sum(re.search(pattern, text) is not None for pattern in [
            r"net sales",
            r"total revenue",
            r"revenues",
            r"gross profit",
            r"operating income",
            r"income from operations",
            r"net income",
        ]),
        "balance": sum(re.search(pattern, text) is not None for pattern in [
            r"total assets",
            r"total liabilities",
            r"stockholders.? equity",
            r"shareholders.? equity",
            r"cash and cash equivalents",
        ]),
        "cashflow": sum(re.search(pattern, text) is not None for pattern in [
            r"net cash.*operating",
            r"cash flows from operating",
            r"net cash.*investing",
            r"net cash.*financing",
            r"capital expenditures",
        ]),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


def identify_financial_statements(tables: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    out = {
        "income": pd.DataFrame(),
        "balance": pd.DataFrame(),
        "cashflow": pd.DataFrame(),
    }

    for table in tables:
        stype = classify_statement(table)

        if not stype:
            continue

        std = standardize_columns(table)

        if std.empty:
            continue

        if out[stype].empty or std.shape[0] > out[stype].shape[0]:
            out[stype] = std

    return out


# ================================================================
# KPI computation
# ================================================================

def safe_div(numerator, denominator):
    if numerator is None or denominator is None:
        return None

    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return None

    return numerator / denominator


def is_valid_number(value) -> bool:
    return value is not None and not pd.isna(value)


def extract_metric(df: pd.DataFrame, pattern: str) -> Dict[str, float]:
    if df.empty or "line_item" not in df.columns:
        return {}

    df2 = df.copy()
    df2["match"] = df2["line_item"].astype(str).str.lower().str.contains(pattern, regex=True, na=False)

    if df2["match"].sum() == 0:
        return {}

    row = df2[df2["match"]].iloc[0]

    return {
        col: row[col]
        for col in df.columns
        if col != "line_item" and pd.notna(row[col])
    }


def compute_kpis(financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    inc = financials.get("income", pd.DataFrame())
    bal = financials.get("balance", pd.DataFrame())
    cf = financials.get("cashflow", pd.DataFrame())

    revenue = extract_metric(inc, r"^total revenue$|^revenues$|^revenue$|^net sales$|^sales$")
    gp = extract_metric(inc, r"gross")
    op = extract_metric(inc, r"operating income|income from operations")
    ni = extract_metric(inc, r"^net income$|^net earnings$|net income attributable|net earnings attributable")
    cash = extract_metric(bal, r"cash and cash equivalents|cash and short-term investments")
    debt = extract_metric(bal, r"total debt|short-term debt|long-term debt|borrowings")
    cfo = extract_metric(cf, r"net cash.*operating|cash provided by operating|operating activities")
    capex = extract_metric(cf, r"capital expenditures|property and equipment|purchases of property")

    all_periods = set().union(
        revenue.keys(),
        gp.keys(),
        op.keys(),
        ni.keys(),
        cash.keys(),
        debt.keys(),
        cfo.keys(),
        capex.keys(),
    )

    periods = sorted(all_periods, reverse=True)

    if not periods:
        return {
            "latest_period": None,
            "periods": [],
            "time_series": pd.DataFrame(),
            "revenue": None,
            "revenue_yoy_growth": None,
            "gross_margin": None,
            "operating_margin": None,
            "net_margin": None,
            "net_income": None,
            "cash_balance": None,
            "total_debt": None,
            "operating_cash_flow": None,
            "capex": None,
            "free_cash_flow": None,
        }

    latest = periods[0]
    rows = []

    for period in periods:
        rev = revenue.get(period)
        gpv = gp.get(period)
        opv = op.get(period)
        niv = ni.get(period)
        cfov = cfo.get(period)
        cap_raw = capex.get(period)

        cap = abs(cap_raw) if is_valid_number(cap_raw) else None
        fcf = cfov - cap if is_valid_number(cfov) and is_valid_number(cap) else None

        rows.append({
            "period": period,
            "revenue": rev,
            "gross_profit": gpv,
            "gross_margin": safe_div(gpv, rev),
            "operating_income": opv,
            "operating_margin": safe_div(opv, rev),
            "net_income": niv,
            "net_margin": safe_div(niv, rev),
            "cash_balance": cash.get(period),
            "total_debt": debt.get(period),
            "operating_cash_flow": cfov,
            "capex": cap,
            "free_cash_flow": fcf,
        })

    ts = pd.DataFrame(rows)

    def yoy(series: Dict[str, float]):
        if latest not in series:
            return None

        idx = periods.index(latest)

        if idx + 1 >= len(periods):
            return None

        prev = periods[idx + 1]

        if prev not in series or not is_valid_number(series[prev]) or series[prev] == 0:
            return None

        return (series[latest] - series[prev]) / series[prev]

    latest_row = ts.loc[ts["period"] == latest].iloc[0]

    return {
        "latest_period": latest,
        "periods": periods,
        "time_series": ts,
        "revenue": revenue.get(latest),
        "revenue_yoy_growth": yoy(revenue),
        "gross_margin": latest_row.get("gross_margin"),
        "operating_margin": latest_row.get("operating_margin"),
        "net_margin": latest_row.get("net_margin"),
        "net_income": ni.get(latest),
        "cash_balance": cash.get(latest),
        "total_debt": debt.get(latest),
        "operating_cash_flow": cfo.get(latest),
        "capex": latest_row.get("capex"),
        "free_cash_flow": latest_row.get("free_cash_flow"),
    }


# ================================================================
# Company name extraction
# ================================================================

def extract_company_name(text: str, fallback: str) -> str:
    fallback_name = Path(fallback).stem.replace("_", " ").replace("-", " ").title()

    patterns = [
        r"Exact name.*?charter.*?:\s*([A-Za-z0-9 .,&-]+)",
        r"Exact name of registrant as specified in its charter\)?\s*([A-Za-z0-9 .,&-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.I)

        if match:
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()

            if 2 <= len(candidate) <= 80:
                return candidate.title()

    return fallback_name


# ================================================================
# Segment revenue extraction
# ================================================================

def extract_segment_revenue(tables: List[pd.DataFrame]) -> pd.DataFrame:
    out = []

    for table in tables:
        txt = " ".join(table.fillna("").astype(str).values.flatten()).lower()

        if "segment" not in txt and "business" not in txt and "product" not in txt:
            continue

        if "revenue" not in txt and "sales" not in txt:
            continue

        df = standardize_columns(table)

        if df.empty or "line_item" not in df.columns:
            continue

        cols = [c for c in df.columns if c != "line_item"]

        if not cols:
            continue

        latest = sorted(cols, reverse=True)[0]

        for _, row in df.iterrows():
            label = str(row["line_item"]).strip()
            value = row.get(latest)

            if pd.isna(value):
                continue

            if "total" in label.lower() or "consolidated" in label.lower():
                continue

            if len(label) < 2 or len(label) > 100:
                continue

            out.append({
                "segment": label,
                "period": latest,
                "revenue": float(value),
            })

    if not out:
        return pd.DataFrame(columns=["segment", "period", "revenue"])

    result = pd.DataFrame(out)
    result = result.drop_duplicates(subset=["segment", "period"], keep="first")
    result = result.sort_values("revenue", ascending=False).head(20)

    return result


# ================================================================
# Formatting and AI-style Q&A
# ================================================================

def fmt_cur(value):
    if value is None or pd.isna(value):
        return "N/A"

    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.1f}B"

    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"

    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"

    return f"{sign}${value:,.0f}"


def fmt_pct(value):
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value * 100:.1f}%"


def answer_question(question: str, df: pd.DataFrame) -> str:
    if df.empty:
        return "Upload filings first so I can compare extracted KPIs."

    q = question.lower()
    lines = []

    if "margin" in q or "profit" in q:
        valid = df.dropna(subset=["operating_margin"])

        if valid.empty:
            return "Operating margin could not be extracted from the uploaded filings."

        best = valid.sort_values("operating_margin", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with operating margin of {fmt_pct(best['operating_margin'])}.")

        for _, row in valid.iterrows():
            lines.append(
                f"{row['company']}: gross margin {fmt_pct(row.get('gross_margin'))}, "
                f"operating margin {fmt_pct(row.get('operating_margin'))}, "
                f"net margin {fmt_pct(row.get('net_margin'))}."
            )

    elif "cash" in q or "fcf" in q or "free cash" in q:
        valid = df.dropna(subset=["free_cash_flow"])

        if valid.empty:
            return "Free cash flow could not be extracted from the uploaded filings."

        best = valid.sort_values("free_cash_flow", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with free cash flow of {fmt_cur(best['free_cash_flow'])}.")

        for _, row in valid.iterrows():
            lines.append(
                f"{row['company']}: operating cash flow {fmt_cur(row.get('operating_cash_flow'))}, "
                f"capex {fmt_cur(row.get('capex'))}, "
                f"free cash flow {fmt_cur(row.get('free_cash_flow'))}."
            )

    elif "risk" in q or "competitive" in q:
        for _, row in df.iterrows():
            risks = []

            if pd.notna(row.get("revenue_yoy_growth")) and row["revenue_yoy_growth"] < 0:
                risks.append("declining revenue")

            if pd.notna(row.get("operating_margin")) and row["operating_margin"] < 0.10:
                risks.append("low operating margin")

            if pd.notna(row.get("free_cash_flow")) and row["free_cash_flow"] < 0:
                risks.append("negative free cash flow")

            if pd.notna(row.get("total_debt")) and pd.notna(row.get("cash_balance")) and row["total_debt"] > row["cash_balance"]:
                risks.append("debt above cash balance")

            if risks:
                lines.append(f"{row['company']}: watch {', '.join(risks)}.")
            else:
                lines.append(f"{row['company']}: no major KPI-based risk signal detected.")

    else:
        for _, row in df.iterrows():
            lines.append(
                f"{row['company']}: revenue {fmt_cur(row.get('revenue'))}, "
                f"YoY growth {fmt_pct(row.get('revenue_yoy_growth'))}, "
                f"operating margin {fmt_pct(row.get('operating_margin'))}, "
                f"free cash flow {fmt_cur(row.get('free_cash_flow'))}."
            )

    return "\n".join(lines)


def format_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    formatted = df.copy()

    currency_cols = [
        "revenue",
        "net_income",
        "operating_cash_flow",
        "free_cash_flow",
        "cash_balance",
        "total_debt",
        "capex",
    ]

    percent_cols = [
        "revenue_yoy_growth",
        "gross_margin",
        "operating_margin",
        "net_margin",
    ]

    for col in currency_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(fmt_cur)

    for col in percent_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(fmt_pct)

    return formatted


# ================================================================
# Streamlit UI
# ================================================================

st.set_page_config(page_title="10-K Competitor Dashboard", layout="wide")

st.title("10-K Competitor Dashboard")
st.caption("Upload one or more 10-K filings to extract KPIs, compare competitors, and generate concise financial insights.")

with st.sidebar:
    st.header("Inputs")

    uploaded_files = st.file_uploader(
        "Upload 10-K filings",
        type=["pdf", "html", "htm", "txt"],
        accept_multiple_files=True,
    )

    question = st.text_input("Ask a financial question", value="Compare margins and cash flow.")

company_results = {}

if uploaded_files:
    for file in uploaded_files:
        with st.spinner(f"Processing {file.name}..."):
            try:
                text = extract_text(file)
                tables = extract_tables(file)
                financials = identify_financial_statements(tables)
                kpis = compute_kpis(financials)
                name = extract_company_name(text, file.name)
                segment = extract_segment_revenue(tables)

                original_name = name
                counter = 2

                while name in company_results:
                    name = f"{original_name} ({counter})"
                    counter += 1

                company_results[name] = {
                    "kpis": kpis,
                    "segment": segment,
                    "financials": financials,
                    "table_count": len(tables),
                }

            except Exception as error:
                st.error(f"Could not process {file.name}: {error}")

    rows = []

    for name, result in company_results.items():
        k = result["kpis"]

        rows.append({
            "company": name,
            "period": k.get("latest_period"),
            "revenue": k.get("revenue"),
            "revenue_yoy_growth": k.get("revenue_yoy_growth"),
            "gross_margin": k.get("gross_margin"),
            "operating_margin": k.get("operating_margin"),
            "net_margin": k.get("net_margin"),
            "net_income": k.get("net_income"),
            "operating_cash_flow": k.get("operating_cash_flow"),
            "free_cash_flow": k.get("free_cash_flow"),
            "cash_balance": k.get("cash_balance"),
            "total_debt": k.get("total_debt"),
            "capex": k.get("capex"),
        })

    benchmark_df = pd.DataFrame(rows)

    if benchmark_df.empty:
        st.warning("No usable KPI data was extracted from the uploaded filings.")
    else:
        kpi_tab, chart_tab, table_tab, insight_tab = st.tabs([
            "Benchmark KPIs",
            "Charts",
            "Financial Tables",
            "AI-Style Insights",
        ])

        with kpi_tab:
            st.subheader("Benchmark KPIs")
            st.dataframe(format_display_dataframe(benchmark_df), use_container_width=True, hide_index=True)

            st.subheader("Extraction Status")

            status_rows = []

            for name, result in company_results.items():
                financials = result["financials"]

                status_rows.append({
                    "company": name,
                    "tables_detected": result["table_count"],
                    "income_statement_detected": not financials["income"].empty,
                    "balance_sheet_detected": not financials["balance"].empty,
                    "cash_flow_detected": not financials["cashflow"].empty,
                })

            st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)

        with chart_tab:
            st.subheader("Competitor Comparison")

            ts_frames = []

            for name, result in company_results.items():
                ts = result["kpis"].get("time_series")

                if isinstance(ts, pd.DataFrame) and not ts.empty:
                    temp = ts.copy()
                    temp["company"] = name
                    ts_frames.append(temp)

            if ts_frames:
                full_ts = pd.concat(ts_frames, ignore_index=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Revenue over time")
                    revenue_df = full_ts.dropna(subset=["revenue"])

                    if revenue_df.empty:
                        st.info("Revenue data was not available.")
                    else:
                        fig_rev = px.line(
                            revenue_df,
                            x="period",
                            y="revenue",
                            color="company",
                            markers=True,
                        )
                        st.plotly_chart(fig_rev, use_container_width=True)

                with col2:
                    st.markdown("### Operating margin over time")
                    margin_df = full_ts.dropna(subset=["operating_margin"])

                    if margin_df.empty:
                        st.info("Operating margin data was not available.")
                    else:
                        fig_op = px.line(
                            margin_df,
                            x="period",
                            y="operating_margin",
                            color="company",
                            markers=True,
                        )
                        fig_op.update_yaxes(tickformat=".0%")
                        st.plotly_chart(fig_op, use_container_width=True)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### Latest revenue comparison")
                    revenue_latest = benchmark_df.dropna(subset=["revenue"])

                    if revenue_latest.empty:
                        st.info("Revenue data was not available.")
                    else:
                        fig_latest_rev = px.bar(
                            revenue_latest,
                            x="company",
                            y="revenue",
                            text_auto=".2s",
                        )
                        st.plotly_chart(fig_latest_rev, use_container_width=True)

                with col2:
                    st.markdown("### Latest margin comparison")
                    margin_cols = ["gross_margin", "operating_margin", "net_margin"]
                    available_margin_cols = [
                        col for col in margin_cols
                        if col in benchmark_df.columns and benchmark_df[col].notna().any()
                    ]

                    if not available_margin_cols:
                        st.info("Margin data was not available.")
                    else:
                        margin_long = benchmark_df.melt(
                            id_vars=["company"],
                            value_vars=available_margin_cols,
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
                        )
                        fig_margin.update_yaxes(tickformat=".0%")
                        st.plotly_chart(fig_margin, use_container_width=True)

            else:
                st.info("No time-series KPI data was available for charting.")

            st.subheader("Segment revenue, latest detected period")

            seg_frames = []

            for name, result in company_results.items():
                seg = result["segment"]

                if isinstance(seg, pd.DataFrame) and not seg.empty:
                    temp = seg.copy()
                    temp["company"] = name
                    seg_frames.append(temp)

            if seg_frames:
                seg_all = pd.concat(seg_frames, ignore_index=True)

                fig_seg = px.bar(
                    seg_all,
                    x="segment",
                    y="revenue",
                    color="company",
                    barmode="group",
                )
                fig_seg.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig_seg, use_container_width=True)
            else:
                st.info("No segment revenue tables detected.")

        with table_tab:
            selected_company = st.selectbox("Select company", list(company_results.keys()))
            selected_financials = company_results[selected_company]["financials"]

            for key, label in [
                ("income", "Income Statement"),
                ("balance", "Balance Sheet"),
                ("cashflow", "Cash Flow Statement"),
            ]:
                st.subheader(label)

                df = selected_financials.get(key, pd.DataFrame())

                if df.empty:
                    st.info(f"{label} was not confidently detected.")
                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)

        with insight_tab:
            st.subheader("AI-Style Insight")

            if question.strip():
                st.write(answer_question(question, benchmark_df))
            else:
                st.info("Enter a question in the sidebar.")

else:
    st.info("Upload at least one 10-K filing to begin.")

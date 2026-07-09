import io
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =============================================================================
# File handling and text extraction
# =============================================================================

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

    first_lines = []
    last_lines = []

    split_pages = []
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
    """
    Extract raw text from PDF, HTML, HTM, or TXT 10-K filings.
    PDF extraction uses pdfplumber.
    HTML extraction uses BeautifulSoup.
    TXT extraction reads raw text.
    """
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
            st.error("HTML extraction requires BeautifulSoup.")
            return ""

        html = data.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        return clean_whitespace(text)

    if ext == "txt":
        text = data.decode("utf-8", errors="ignore")
        return clean_whitespace(text)

    return ""


# =============================================================================
# Table extraction
# =============================================================================

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

    tables = []
    try:
        parsed = camelot.read_pdf(file_path, pages="all", flavor="stream")
        for table in parsed:
            df = normalize_dataframe_shape(table.df)
            if df.shape[0] >= 3 and df.shape[1] >= 2:
                tables.append(df)
    except Exception:
        return []

    return tables


def extract_tables_from_pdf_with_tabula(file_path: str) -> List[pd.DataFrame]:
    try:
        import tabula
    except ImportError:
        return []

    try:
        parsed = tabula.read_pdf(file_path, pages="all", multiple_tables=True, lattice=False, stream=True)
    except Exception:
        return []

    tables = []
    for df in parsed:
        df = normalize_dataframe_shape(df)
        if df.shape[0] >= 3 and df.shape[1] >= 2:
            tables.append(df)

    return tables


def extract_tables_from_pdf_with_pdfplumber(data: bytes) -> List[pd.DataFrame]:
    try:
        import pdfplumber
    except ImportError:
        return []

    tables = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables() or []
            for table in extracted:
                if not table or len(table) < 3:
                    continue
                df = pd.DataFrame(table)
                df = normalize_dataframe_shape(df)
                if df.shape[0] >= 3 and df.shape[1] >= 2:
                    tables.append(df)

    return tables


def extract_tables(file) -> List[pd.DataFrame]:
    """
    Extract tables from PDF or HTML filings.
    PDF extraction tries camelot, then tabula, then pdfplumber.
    HTML extraction uses pandas.read_html.
    TXT files usually do not contain reliable table structure, so this returns an empty list.
    """
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

        return [
            normalize_dataframe_shape(df)
            for df in parsed
            if df.shape[0] >= 3 and df.shape[1] >= 2
        ]

    return []


# =============================================================================
# Financial statement identification and normalization
# =============================================================================

def parse_financial_value(value: Any) -> Optional[float]:
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if text == "":
        return np.nan

    text = text.replace("\u2014", "-").replace("—", "-").replace("–", "-")
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = re.sub(r"\s+", " ", text)

    if text.lower() in {"-", "nm", "n/m", "na", "n/a"}:
        return np.nan

    negative = bool(re.fullmatch(r"\(.*\)", text))
    text = text.strip("()")

    multiplier = 1
    if re.search(r"(?i)\bmillion\b|\bmillions\b", text):
        multiplier = 1_000_000
    elif re.search(r"(?i)\bbillion\b|\bbillions\b", text):
        multiplier = 1_000_000_000

    text = re.sub(r"(?i)\bmillion(s)?\b|\bbillion(s)?\b", "", text).strip()

    match = re.search(r"-?\d+(\.\d+)?", text)
    if not match:
        return np.nan

    number = float(match.group(0)) * multiplier
    return -abs(number) if negative else number


def clean_line_item(value: Any) -> str:
    if pd.isna(value):
        return ""

    text = str(value)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^\$?\s*", "", text)
    return text.strip()


def promote_header_row(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_dataframe_shape(df)

    if df.empty:
        return df

    best_row = None
    best_score = -1

    for idx in range(min(5, len(df))):
        row = df.iloc[idx].astype(str).tolist()
        score = sum(bool(re.search(r"20\d{2}|19\d{2}|three months|year ended|years ended", cell, re.I)) for cell in row)
        score += sum(cell.strip().lower() in {"", "nan"} for cell in row) * -0.25

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


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = promote_header_row(df)

    if df.empty:
        return df

    columns = [str(c).strip() for c in df.columns]
    first_col = columns[0]

    renamed = {first_col: "line_item"}
    used = {"line_item"}

    for col in columns[1:]:
        raw = str(col).strip()
        year_match = re.search(r"(20\d{2}|19\d{2})", raw)
        if year_match:
            name = year_match.group(1)
        else:
            name = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_") or "value"

        original_name = name
        counter = 2
        while name in used:
            name = f"{original_name}_{counter}"
            counter += 1

        renamed[col] = name
        used.add(name)

    df = df.rename(columns=renamed)
    df["line_item"] = df["line_item"].map(clean_line_item)

    for col in df.columns:
        if col != "line_item":
            df[col] = df[col].map(parse_financial_value)

    numeric_cols = [c for c in df.columns if c != "line_item"]
    keep_numeric = [c for c in numeric_cols if df[c].notna().sum() > 0]

    if not keep_numeric:
        return pd.DataFrame()

    df = df[["line_item"] + keep_numeric]
    df = df[df["line_item"].astype(str).str.len() > 0]
    df = df.drop_duplicates(subset=["line_item"], keep="first")

    return df.reset_index(drop=True)


def table_text_for_classification(df: pd.DataFrame) -> str:
    values = df.fillna("").astype(str).values.flatten().tolist()
    return " ".join(values).lower()


def classify_statement(df: pd.DataFrame) -> Optional[str]:
    text = table_text_for_classification(df)

    income_score = sum(bool(re.search(pattern, text)) for pattern in [
        r"net sales|total revenue|revenues",
        r"gross margin|gross profit",
        r"operating income|income from operations",
        r"net income|net earnings",
        r"selling.*general.*administrative|research.*development",
    ])

    balance_score = sum(bool(re.search(pattern, text)) for pattern in [
        r"cash and cash equivalents",
        r"total assets",
        r"total liabilities",
        r"stockholders.? equity|shareholders.? equity",
        r"long-term debt|short-term debt",
    ])

    cashflow_score = sum(bool(re.search(pattern, text)) for pattern in [
        r"net cash.*operating activities",
        r"cash flows from operating activities",
        r"capital expenditures|property and equipment",
        r"net cash.*investing activities",
        r"net cash.*financing activities",
    ])

    scores = {
        "income": income_score,
        "balance": balance_score,
        "cashflow": cashflow_score,
    }

    statement, score = max(scores.items(), key=lambda item: item[1])
    return statement if score >= 2 else None


def identify_financial_statements(tables: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Identify and normalize Income Statement, Balance Sheet, and Cash Flow Statement tables.
    Returns:
        {
            "income": df,
            "balance": df,
            "cashflow": df
        }
    """
    candidates = {"income": [], "balance": [], "cashflow": []}

    for raw_table in tables:
        statement_type = classify_statement(raw_table)
        if not statement_type:
            continue

        standardized = standardize_columns(raw_table)
        if standardized.empty:
            continue

        candidates[statement_type].append(standardized)

    financials = {}
    for statement_type, dfs in candidates.items():
        if dfs:
            financials[statement_type] = max(
                dfs,
                key=lambda d: d.shape[0] * d.shape[1] + d.notna().sum().sum()
            )
        else:
            financials[statement_type] = pd.DataFrame()

    return financials


# =============================================================================
# KPI computation
# =============================================================================

LINE_PATTERNS = {
    "revenue": [
        r"^total revenue$",
        r"^revenues$",
        r"^revenue$",
        r"^net sales$",
        r"^sales$",
        r"total net sales",
    ],
    "gross_profit": [
        r"gross profit",
        r"gross margin",
    ],
    "operating_income": [
        r"operating income",
        r"income from operations",
    ],
    "net_income": [
        r"^net income$",
        r"^net earnings$",
        r"net income attributable",
        r"net earnings attributable",
    ],
    "rnd": [
        r"research and development",
        r"research development",
        r"r&d",
    ],
    "sga": [
        r"selling.*general.*administrative",
        r"sales.*marketing.*general.*administrative",
        r"general and administrative",
    ],
    "cash": [
        r"cash and cash equivalents$",
        r"cash, cash equivalents",
        r"cash and short-term investments",
    ],
    "total_debt": [
        r"total debt",
        r"short-term debt",
        r"long-term debt",
        r"current portion of long-term debt",
        r"borrowings",
    ],
    "operating_cash_flow": [
        r"net cash.*operating activities",
        r"cash provided by operating activities",
        r"net cash provided by operating activities",
    ],
    "capex": [
        r"capital expenditures",
        r"additions to property and equipment",
        r"purchases of property and equipment",
        r"payments for property and equipment",
    ],
}


def find_matching_row(df: pd.DataFrame, patterns: List[str]) -> Optional[pd.Series]:
    if df.empty or "line_item" not in df.columns:
        return None

    labels = df["line_item"].astype(str).str.lower()

    exact_penalty_terms = [
        "per share",
        "basic",
        "diluted",
        "weighted average",
        "percentage",
    ]

    matches = []
    for idx, label in labels.items():
        if any(term in label for term in exact_penalty_terms):
            continue

        for pattern in patterns:
            if re.search(pattern, label, flags=re.IGNORECASE):
                matches.append((idx, len(label)))
                break

    if not matches:
        return None

    best_idx = sorted(matches, key=lambda item: item[1])[0][0]
    return df.loc[best_idx]


def extract_metric_series(df: pd.DataFrame, metric_name: str) -> Dict[str, float]:
    row = find_matching_row(df, LINE_PATTERNS[metric_name])
    if row is None:
        return {}

    return {
        col: float(row[col])
        for col in df.columns
        if col != "line_item" and pd.notna(row[col])
    }


def combine_debt_series(balance: pd.DataFrame) -> Dict[str, float]:
    if balance.empty:
        return {}

    debt_rows = []
    labels = balance["line_item"].astype(str).str.lower()

    for idx, label in labels.items():
        if any(re.search(pattern, label) for pattern in LINE_PATTERNS["total_debt"]):
            if "lease" not in label and "deferred" not in label:
                debt_rows.append(balance.loc[idx])

    if not debt_rows:
        return {}

    combined = {}
    numeric_cols = [c for c in balance.columns if c != "line_item"]

    for col in numeric_cols:
        values = [row[col] for row in debt_rows if pd.notna(row[col])]
        if values:
            combined[col] = float(np.nansum(values))

    return combined


def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator in {None, 0}:
        return None
    if pd.isna(numerator) or pd.isna(denominator):
        return None
    return float(numerator) / float(denominator)


def period_sort_key(period: str) -> Tuple[int, str]:
    year_match = re.search(r"(20\d{2}|19\d{2})", str(period))
    if year_match:
        return int(year_match.group(1)), str(period)
    return 0, str(period)


def compute_yoy_growth(series: Dict[str, float], latest_period: str, periods: List[str]) -> Optional[float]:
    if latest_period not in series:
        return None

    sorted_periods = sorted(periods, key=period_sort_key, reverse=True)
    if latest_period not in sorted_periods:
        return None

    latest_idx = sorted_periods.index(latest_period)
    if latest_idx + 1 >= len(sorted_periods):
        return None

    prior_period = sorted_periods[latest_idx + 1]
    prior = series.get(prior_period)
    latest = series.get(latest_period)

    return safe_divide(latest - prior, prior) if prior not in {None, 0} else None


def compute_kpis(financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Compute standardized KPIs:
    Revenue, Gross Margin, Operating Margin, Net Income, Free Cash Flow,
    R&D %, SG&A %, Cash Balance, Total Debt, Capex, YoY Revenue Growth.
    """
    income = financials.get("income", pd.DataFrame())
    balance = financials.get("balance", pd.DataFrame())
    cashflow = financials.get("cashflow", pd.DataFrame())

    revenue = extract_metric_series(income, "revenue")
    gross_profit = extract_metric_series(income, "gross_profit")
    operating_income = extract_metric_series(income, "operating_income")
    net_income = extract_metric_series(income, "net_income")
    rnd = extract_metric_series(income, "rnd")
    sga = extract_metric_series(income, "sga")
    cash = extract_metric_series(balance, "cash")
    total_debt = combine_debt_series(balance)
    operating_cash_flow = extract_metric_series(cashflow, "operating_cash_flow")
    capex_raw = extract_metric_series(cashflow, "capex")

    periods = sorted(
        set().union(
            revenue.keys(),
            gross_profit.keys(),
            operating_income.keys(),
            net_income.keys(),
            rnd.keys(),
            sga.keys(),
            cash.keys(),
            total_debt.keys(),
            operating_cash_flow.keys(),
            capex_raw.keys(),
        ),
        key=period_sort_key,
        reverse=True,
    )

    if not periods:
        return {
            "latest_period": None,
            "periods": [],
            "time_series": pd.DataFrame(),
        }

    latest_period = periods[0]
    rows = []

    for period in periods:
        rev = revenue.get(period)
        gp = gross_profit.get(period)
        op_income = operating_income.get(period)
        ni = net_income.get(period)
        rd = rnd.get(period)
        sgna = sga.get(period)
        cfo = operating_cash_flow.get(period)
        capex = abs(capex_raw.get(period)) if capex_raw.get(period) is not None else None
        fcf = cfo - capex if cfo is not None and capex is not None else None

        rows.append({
            "period": period,
            "revenue": rev,
            "gross_profit": gp,
            "gross_margin": safe_divide(gp, rev),
            "operating_income": op_income,
            "operating_margin": safe_divide(op_income, rev),
            "net_income": ni,
            "net_margin": safe_divide(ni, rev),
            "rnd": rd,
            "rnd_pct": safe_divide(rd, rev),
            "sga": sgna,
            "sga_pct": safe_divide(sgna, rev),
            "cash_balance": cash.get(period),
            "total_debt": total_debt.get(period),
            "operating_cash_flow": cfo,
            "capex": capex,
            "free_cash_flow": fcf,
        })

    time_series = pd.DataFrame(rows)
    latest = time_series[time_series["period"] == latest_period].iloc[0].to_dict()

    latest["revenue_yoy_growth"] = compute_yoy_growth(revenue, latest_period, periods)
    latest["latest_period"] = latest_period
    latest["periods"] = periods
    latest["time_series"] = time_series

    return latest


# =============================================================================
# Competitor analysis
# =============================================================================

def extract_company_name(text: str, fallback_name: str) -> str:
    clean_fallback = Path(fallback_name).stem.replace("_", " ").replace("-", " ").strip()

    patterns = [
        r"Exact name of registrant as specified in its charter\)?\s*[:\-]?\s*([A-Z][A-Z0-9 &,.\-]+)",
        r"Registrant(?:’s|'s)? exact name\s*[:\-]?\s*([A-Z][A-Z0-9 &,.\-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()
            candidate = re.sub(r"\bCommission File Number\b.*", "", candidate, flags=re.I).strip()
            if 2 <= len(candidate) <= 80:
                return candidate.title()

    top_lines = [line.strip() for line in text.splitlines()[:80] if line.strip()]
    uppercase_lines = [
        line for line in top_lines
        if line.isupper()
        and 3 <= len(line) <= 80
        and not re.search(r"FORM 10-K|UNITED STATES|SECURITIES|COMMISSION|WASHINGTON", line)
    ]

    if uppercase_lines:
        return uppercase_lines[0].title()

    return clean_fallback.title()


def create_benchmarking_table(company_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for company, result in company_results.items():
        kpis = result["kpis"]
        rows.append({
            "company": company,
            "period": kpis.get("latest_period"),
            "revenue": kpis.get("revenue"),
            "revenue_yoy_growth": kpis.get("revenue_yoy_growth"),
            "gross_margin": kpis.get("gross_margin"),
            "operating_margin": kpis.get("operating_margin"),
            "net_margin": kpis.get("net_margin"),
            "net_income": kpis.get("net_income"),
            "operating_cash_flow": kpis.get("operating_cash_flow"),
            "free_cash_flow": kpis.get("free_cash_flow"),
            "cash_balance": kpis.get("cash_balance"),
            "total_debt": kpis.get("total_debt"),
            "rnd_pct": kpis.get("rnd_pct"),
            "sga_pct": kpis.get("sga_pct"),
            "capex": kpis.get("capex"),
        })

    return pd.DataFrame(rows)


def extract_segment_revenue(tables: List[pd.DataFrame]) -> pd.DataFrame:
    segment_keywords = [
        "segment",
        "productivity",
        "cloud",
        "services",
        "devices",
        "advertising",
        "geographic",
        "business unit",
    ]

    rows = []

    for raw_table in tables:
        text = table_text_for_classification(raw_table)
        if not any(keyword in text for keyword in segment_keywords):
            continue
        if not re.search(r"revenue|sales", text):
            continue

        df = standardize_columns(raw_table)
        if df.empty:
            continue

        numeric_cols = [c for c in df.columns if c != "line_item"]
        if not numeric_cols:
            continue

        latest_col = sorted(numeric_cols, key=period_sort_key, reverse=True)[0]

        for _, row in df.iterrows():
            label = str(row["line_item"]).strip()
            value = row.get(latest_col)

            if pd.isna(value):
                continue

            is_total = bool(re.search(r"total|consolidated", label, re.I))
            is_revenue_line = bool(re.search(r"revenue|sales", label, re.I))

            if is_total or is_revenue_line:
                continue

            if 2 <= len(label) <= 80 and abs(value) > 0:
                rows.append({
                    "segment": label,
                    "period": latest_col,
                    "revenue": float(value),
                })

    segment_df = pd.DataFrame(rows)
    if segment_df.empty:
        return segment_df

    segment_df = segment_df.drop_duplicates(subset=["segment", "period"], keep="first")
    segment_df = segment_df.sort_values("revenue", ascending=False).head(15)
    return segment_df


# =============================================================================
# AI-style insight module
# =============================================================================

def format_currency(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "not available"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:,.1f}B"
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:,.1f}M"
    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:,.1f}K"

    return f"{sign}${abs_value:,.0f}"


def format_percent(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "not available"
    return f"{value * 100:,.1f}%"


def get_best_company(df: pd.DataFrame, metric: str, higher_is_better: bool = True) -> Optional[pd.Series]:
    if df.empty or metric not in df.columns:
        return None

    valid = df.dropna(subset=[metric])
    if valid.empty:
        return None

    idx = valid[metric].idxmax() if higher_is_better else valid[metric].idxmin()
    return valid.loc[idx]


def answer_financial_question(question: str, benchmark_df: pd.DataFrame) -> str:
    """
    Local AI-style insight engine.
    It references extracted KPIs directly and produces concise structured analysis.
    """
    if benchmark_df.empty:
        return "No extracted KPI data is available yet. Upload one or more filings and confirm financial statements were detected."

    q = question.lower().strip()
    mentioned_companies = [
        company for company in benchmark_df["company"].tolist()
        if company.lower() in q
    ]

    scoped = benchmark_df
    if mentioned_companies:
        scoped = benchmark_df[benchmark_df["company"].isin(mentioned_companies)]

    lines = []

    if any(term in q for term in ["margin", "profitability", "gross", "operating"]):
        best_operating = get_best_company(scoped, "operating_margin")
        best_gross = get_best_company(scoped, "gross_margin")

        if best_operating is not None:
            lines.append(
                f"- Operating margin leader: {best_operating['company']} at "
                f"{format_percent(best_operating['operating_margin'])}."
            )
        if best_gross is not None:
            lines.append(
                f"- Gross margin leader: {best_gross['company']} at "
                f"{format_percent(best_gross['gross_margin'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"- {row['company']}: gross margin {format_percent(row.get('gross_margin'))}, "
                f"operating margin {format_percent(row.get('operating_margin'))}, "
                f"net margin {format_percent(row.get('net_margin'))}."
            )

    elif any(term in q for term in ["cash flow", "cashflow", "free cash", "fcf"]):
        best_fcf = get_best_company(scoped, "free_cash_flow")
        best_cfo = get_best_company(scoped, "operating_cash_flow")

        if best_fcf is not None:
            lines.append(
                f"- Free cash flow leader: {best_fcf['company']} with "
                f"{format_currency(best_fcf['free_cash_flow'])}."
            )
        if best_cfo is not None:
            lines.append(
                f"- Operating cash flow leader: {best_cfo['company']} with "
                f"{format_currency(best_cfo['operating_cash_flow'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"- {row['company']}: operating cash flow {format_currency(row.get('operating_cash_flow'))}, "
                f"capex {format_currency(row.get('capex'))}, "
                f"free cash flow {format_currency(row.get('free_cash_flow'))}."
            )

    elif any(term in q for term in ["risk", "risks", "competitive", "competition"]):
        for _, row in scoped.iterrows():
            risk_signals = []

            if pd.notna(row.get("revenue_yoy_growth")) and row["revenue_yoy_growth"] < 0:
                risk_signals.append("declining revenue")
            if pd.notna(row.get("operating_margin")) and row["operating_margin"] < 0.10:
                risk_signals.append("thin operating margin")
            if pd.notna(row.get("free_cash_flow")) and row["free_cash_flow"] < 0:
                risk_signals.append("negative free cash flow")
            if pd.notna(row.get("total_debt")) and pd.notna(row.get("cash_balance")) and row["total_debt"] > row["cash_balance"]:
                risk_signals.append("debt above cash balance")
            if pd.notna(row.get("rnd_pct")) and row["rnd_pct"] < 0.03:
                risk_signals.append("low R&D intensity")

            if risk_signals:
                lines.append(f"- {row['company']}: watch {', '.join(risk_signals)}.")
            else:
                lines.append(f"- {row['company']}: no major KPI-based risk signal detected from extracted metrics.")

    elif any(term in q for term in ["growth", "revenue", "sales"]):
        best_revenue = get_best_company(scoped, "revenue")
        best_growth = get_best_company(scoped, "revenue_yoy_growth")

        if best_revenue is not None:
            lines.append(
                f"- Revenue leader: {best_revenue['company']} with "
                f"{format_currency(best_revenue['revenue'])}."
            )
        if best_growth is not None:
            lines.append(
                f"- Fastest YoY revenue growth: {best_growth['company']} at "
                f"{format_percent(best_growth['revenue_yoy_growth'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"- {row['company']}: revenue {format_currency(row.get('revenue'))}, "
                f"YoY growth {format_percent(row.get('revenue_yoy_growth'))}."
            )

    else:
        leader_revenue = get_best_company(scoped, "revenue")
        leader_margin = get_best_company(scoped, "operating_margin")
        leader_fcf = get_best_company(scoped, "free_cash_flow")

        lines.append("- Summary:")
        if leader_revenue is not None:
            lines.append(f"  - Scale leader: {leader_revenue['company']} at {format_currency(leader_revenue['revenue'])} revenue.")
        if leader_margin is not None:
            lines.append(f"  - Profitability leader: {leader_margin['company']} at {format_percent(leader_margin['operating_margin'])} operating margin.")
        if leader_fcf is not None:
            lines.append(f"  - Cash generation leader: {leader_fcf['company']} at {format_currency(leader_fcf['free_cash_flow'])} free cash flow.")

    return "\n".join(lines) if lines else "The uploaded filings did not contain enough comparable KPI data to answer that question confidently."


def generate_default_insights(benchmark_df: pd.DataFrame) -> List[str]:
    if benchmark_df.empty:
        return ["Upload filings to generate KPI-based insights."]

    insights = []

    revenue_leader = get_best_company(benchmark_df, "revenue")
    margin_leader = get_best_company(benchmark_df, "operating_margin")
    fcf_leader = get_best_company(benchmark_df, "free_cash_flow")
    growth_leader = get_best_company(benchmark_df, "revenue_yoy_growth")

    if revenue_leader is not None:
        insights.append(
            f"{revenue_leader['company']} has the largest extracted revenue base at "
            f"{format_currency(revenue_leader['revenue'])}."
        )

    if growth_leader is not None and pd.notna(growth_leader.get("revenue_yoy_growth")):
        insights.append(
            f"{growth_leader['company']} shows the strongest extracted YoY revenue growth at "
            f"{format_percent(growth_leader['revenue_yoy_growth'])}."
        )

    if margin_leader is not None:
        insights.append(
            f"{margin_leader['company']} leads operating profitability at "
            f"{format_percent(margin_leader['operating_margin'])}."
        )

    if fcf_leader is not None:
        insights.append(
            f"{fcf_leader['company']} leads cash generation with "
            f"{format_currency(fcf_leader['free_cash_flow'])} in free cash flow."
        )

    if not insights:
        insights.append("Financial statements were detected, but comparable KPI coverage is limited.")

    return insights


# =============================================================================
# Visualization helpers
# =============================================================================

def make_revenue_chart(benchmark_df: pd.DataFrame):
    df = benchmark_df.dropna(subset=["revenue"])
    if df.empty:
        return None

    fig = px.bar(
        df,
        x="company",
        y="revenue",
        text_auto=".2s",
        title="Revenue Comparison",
        labels={"company": "Company", "revenue": "Revenue"},
    )
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def make_margin_chart(benchmark_df: pd.DataFrame):
    cols = ["gross_margin", "operating_margin", "net_margin"]
    available = [c for c in cols if c in benchmark_df.columns and benchmark_df[c].notna().any()]

    if not available:
        return None

    long_df = benchmark_df.melt(
        id_vars=["company"],
        value_vars=available,
        var_name="metric",
        value_name="margin",
    ).dropna(subset=["margin"])

    long_df["metric"] = long_df["metric"].map({
        "gross_margin": "Gross Margin",
        "operating_margin": "Operating Margin",
        "net_margin": "Net Margin",
    })

    fig = px.bar(
        long_df,
        x="company",
        y="margin",
        color="metric",
        barmode="group",
        text_auto=".1%",
        title="Margin Comparison",
        labels={"company": "Company", "margin": "Margin", "metric": "Metric"},
    )
    fig.update_yaxes_tickformat(".0%")
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def make_cash_flow_chart(benchmark_df: pd.DataFrame):
    cols = ["operating_cash_flow", "free_cash_flow"]
    available = [c for c in cols if c in benchmark_df.columns and benchmark_df[c].notna().any()]

    if not available:
        return None

    long_df = benchmark_df.melt(
        id_vars=["company"],
        value_vars=available,
        var_name="metric",
        value_name="amount",
    ).dropna(subset=["amount"])

    long_df["metric"] = long_df["metric"].map({
        "operating_cash_flow": "Operating Cash Flow",
        "free_cash_flow": "Free Cash Flow",
    })

    fig = px.bar(
        long_df,
        x="company",
        y="amount",
        color="metric",
        barmode="group",
        text_auto=".2s",
        title="Cash Flow Comparison",
        labels={"company": "Company", "amount": "Amount", "metric": "Metric"},
    )
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def make_revenue_trend_chart(company_results: Dict[str, Dict[str, Any]]):
    rows = []

    for company, result in company_results.items():
        ts = result["kpis"].get("time_series")
        if isinstance(ts, pd.DataFrame) and not ts.empty and "revenue" in ts.columns:
            for _, row in ts.dropna(subset=["revenue"]).iterrows():
                rows.append({
                    "company": company,
                    "period": row["period"],
                    "revenue": row["revenue"],
                })

    df = pd.DataFrame(rows)
    if df.empty:
        return None

    fig = px.line(
        df,
        x="period",
        y="revenue",
        color="company",
        markers=True,
        title="Revenue Trend",
        labels={"period": "Period", "revenue": "Revenue", "company": "Company"},
    )
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def make_segment_chart(company_results: Dict[str, Dict[str, Any]]):
    rows = []

    for company, result in company_results.items():
        segment_df = result.get("segments", pd.DataFrame())
        if segment_df.empty:
            continue

        temp = segment_df.copy()
        temp["company"] = company
        rows.append(temp)

    if not rows:
        return None

    df = pd.concat(rows, ignore_index=True)

    fig = px.bar(
        df,
        x="segment",
        y="revenue",
        color="company",
        barmode="group",
        title="Segment Revenue Comparison",
        labels={"segment": "Segment", "revenue": "Revenue", "company": "Company"},
    )
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=80), xaxis_tickangle=-35)
    return fig


# =============================================================================
# Formatting helpers
# =============================================================================

def format_kpi_table(df: pd.DataFrame) -> pd.DataFrame:
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
        "rnd_pct",
        "sga_pct",
    ]

    for col in currency_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(format_currency)

    for col in percent_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(format_percent)

    pretty_names = {
        "company": "Company",
        "period": "Period",
        "revenue": "Revenue",
        "revenue_yoy_growth": "YoY Revenue Growth",
        "gross_margin": "Gross Margin",
        "operating_margin": "Operating Margin",
        "net_margin": "Net Margin",
        "net_income": "Net Income",
        "operating_cash_flow": "Operating Cash Flow",
        "free_cash_flow": "Free Cash Flow",
        "cash_balance": "Cash Balance",
        "total_debt": "Total Debt",
        "rnd_pct": "R&D %",
        "sga_pct": "SG&A %",
        "capex": "Capex",
    }

    return formatted.rename(columns=pretty_names)


def process_uploaded_file(file) -> Dict[str, Any]:
    text = extract_text(file)
    tables = extract_tables(file)
    financials = identify_financial_statements(tables)
    kpis = compute_kpis(financials)
    company_name = extract_company_name(text, file.name)
    segments = extract_segment_revenue(tables)

    return {
        "company": company_name,
        "file_name": file.name,
        "text": text,
        "tables": tables,
        "financials": financials,
        "kpis": kpis,
        "segments": segments,
    }


# =============================================================================
# Streamlit app
# =============================================================================

def main():
    st.set_page_config(
        page_title="10-K Financial Analysis",
        page_icon="📄",
        layout="wide",
    )

    st.title("10-K Financial Analysis")
    st.caption("Upload SEC 10-K filings to extract KPIs, benchmark competitors, and generate concise financial insights.")

    with st.sidebar:
        st.header("Files")
        uploaded_files = st.file_uploader(
            "Upload 10-K filings",
            type=["pdf", "html", "htm", "txt"],
            accept_multiple_files=True,
        )

    if not uploaded_files:
        st.info("Upload one or more PDF, HTML, or TXT 10-K filings to begin.")
        return

    company_results = {}

    with st.spinner("Extracting financial statements and KPIs..."):
        for file in uploaded_files:
            result = process_uploaded_file(file)
            company = result["company"]

            original_company = company
            counter = 2
            while company in company_results:
                company = f"{original_company} ({counter})"
                counter += 1

            result["company"] = company
            company_results[company] = result

    company_names = list(company_results.keys())

    with st.sidebar:
        st.header("Company")
        selected_company = st.selectbox("Select company", company_names)

    benchmark_df = create_benchmarking_table(company_results)

    overview_tab, tables_tab, charts_tab, insights_tab = st.tabs([
        "KPIs",
        "Financial Tables",
        "Benchmarking Charts",
        "AI Insights",
    ])

    with overview_tab:
        st.subheader("Extracted KPIs")
        st.dataframe(
            format_kpi_table(benchmark_df),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader(f"{selected_company} KPI Detail")
        selected_kpis = company_results[selected_company]["kpis"]
        detail_cols = st.columns(4)

        detail_cols[0].metric("Revenue", format_currency(selected_kpis.get("revenue")))
        detail_cols[1].metric("Operating Margin", format_percent(selected_kpis.get("operating_margin")))
        detail_cols[2].metric("Net Income", format_currency(selected_kpis.get("net_income")))
        detail_cols[3].metric("Free Cash Flow", format_currency(selected_kpis.get("free_cash_flow")))

        detail_cols = st.columns(4)
        detail_cols[0].metric("YoY Revenue Growth", format_percent(selected_kpis.get("revenue_yoy_growth")))
        detail_cols[1].metric("Gross Margin", format_percent(selected_kpis.get("gross_margin")))
        detail_cols[2].metric("Cash Balance", format_currency(selected_kpis.get("cash_balance")))
        detail_cols[3].metric("Total Debt", format_currency(selected_kpis.get("total_debt")))

    with tables_tab:
        st.subheader(f"Detected Financial Statements: {selected_company}")

        selected_financials = company_results[selected_company]["financials"]

        for statement_key, statement_label in [
            ("income", "Income Statement"),
            ("balance", "Balance Sheet"),
            ("cashflow", "Cash Flow Statement"),
        ]:
            st.markdown(f"#### {statement_label}")
            df = selected_financials.get(statement_key, pd.DataFrame())

            if df.empty:
                st.warning(f"{statement_label} was not confidently detected.")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

    with charts_tab:
        st.subheader("Competitor Comparison")

        revenue_chart = make_revenue_chart(benchmark_df)
        margin_chart = make_margin_chart(benchmark_df)
        cash_flow_chart = make_cash_flow_chart(benchmark_df)
        revenue_trend_chart = make_revenue_trend_chart(company_results)
        segment_chart = make_segment_chart(company_results)

        col1, col2 = st.columns(2)

        with col1:
            if revenue_chart:
                st.plotly_chart(revenue_chart, use_container_width=True)
            else:
                st.info("Revenue comparison is unavailable from extracted data.")

        with col2:
            if margin_chart:
                st.plotly_chart(margin_chart, use_container_width=True)
            else:
                st.info("Margin comparison is unavailable from extracted data.")

        col1, col2 = st.columns(2)

        with col1:
            if cash_flow_chart:
                st.plotly_chart(cash_flow_chart, use_container_width=True)
            else:
                st.info("Cash flow comparison is unavailable from extracted data.")

        with col2:
            if revenue_trend_chart:
                st.plotly_chart(revenue_trend_chart, use_container_width=True)
            else:
                st.info("Revenue trend is unavailable from extracted data.")

        if segment_chart:
            st.plotly_chart(segment_chart, use_container_width=True)
        else:
            st.info("Segment revenue comparison is unavailable from extracted tables.")

    with insights_tab:
        st.subheader("AI-Generated Financial Insights")

        for insight in generate_default_insights(benchmark_df):
            st.write(f"- {insight}")

        st.divider()

        question = st.text_input(
            "Ask a question",
            value="Compare company margins and cash flow.",
        )

        if question:
            answer = answer_financial_question(question, benchmark_df)
            st.markdown(answer)


if __name__ == "__main__":
    main()

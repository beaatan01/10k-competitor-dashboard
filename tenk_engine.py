import io
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


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
    ext = get_file_extension(file)
    data = read_uploaded_file_bytes(file)

    if ext == "pdf":
        try:
            import pdfplumber
        except ImportError:
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

def make_unique_columns(columns: List[Any]) -> List[str]:
    used = {}
    output = []

    for col in columns:
        name = str(col).strip()

        if name == "" or name.lower() == "nan":
            name = "Column"

        if name not in used:
            used[name] = 1
            output.append(name)
        else:
            used[name] += 1
            output.append(f"{name}_{used[name]}")

    return output


def normalize_dataframe_shape(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df = df.replace(r"^\s*$", np.nan, regex=True)
    df = df.dropna(how="all").dropna(axis=1, how="all")

    if df.empty:
        return pd.DataFrame()

    df.columns = make_unique_columns(list(df.columns))
    return df.reset_index(drop=True)


def extract_tables_from_pdf_with_camelot(file_path: str) -> List[pd.DataFrame]:
    try:
        import camelot
    except ImportError:
        return []

    try:
        parsed = camelot.read_pdf(file_path, pages="all", flavor="stream")
    except Exception:
        return []

    tables = []

    for table in parsed:
        df = normalize_dataframe_shape(table.df)

        if df.shape[0] >= 3 and df.shape[1] >= 2:
            tables.append(df)

    return tables


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
            page_tables = page.extract_tables() or []

            for table in page_tables:
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
# Financial value parsing
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
        .replace("\xa0", " ")
    )

    lower_text = text.lower().strip()

    if lower_text in {"-", "nm", "n/m", "na", "n/a", "none", "nan"}:
        return np.nan

    negative = bool(re.search(r"\(.*\)", text))
    text = text.replace("(", "").replace(")", "")

    multiplier = 1

    if "billion" in lower_text or "billions" in lower_text:
        multiplier = 1_000_000_000
    elif "million" in lower_text or "millions" in lower_text:
        multiplier = 1_000_000

    text = re.sub(r"(?i)\bmillion(s)?\b|\bbillion(s)?\b|\bthousand(s)?\b", "", text)
    matches = re.findall(r"-?\d+(?:\.\d+)?", text)

    if not matches:
        return np.nan

    try:
        number = float(matches[0]) * multiplier
    except ValueError:
        return np.nan

    return -abs(number) if negative else number


def clean_line_item(value: Any) -> str:
    if pd.isna(value):
        return ""

    text = str(value)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^\$?\s*", "", text)

    return text.strip()


# ================================================================
# Statement table normalization
# ================================================================

def header_score(row: pd.Series) -> float:
    cells = row.fillna("").astype(str).tolist()

    score = 0.0
    score += sum(bool(re.search(r"20\d{2}|19\d{2}", cell)) for cell in cells) * 2.0
    score += sum(
        bool(re.search(r"year ended|years ended|fiscal year|twelve months", cell, re.I))
        for cell in cells
    ) * 1.5
    score -= sum(cell.strip() == "" for cell in cells) * 0.25

    return score


def promote_header_row(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_dataframe_shape(df)

    if df.empty:
        return df

    best_row = None
    best_score = -1.0

    for idx in range(min(8, len(df))):
        score = header_score(df.iloc[idx])

        if score > best_score:
            best_score = score
            best_row = idx

    if best_row is not None and best_score > 0:
        new_columns = [
            clean_line_item(value) if clean_line_item(value) else f"Column_{i}"
            for i, value in enumerate(df.iloc[best_row].tolist())
        ]

        df = df.iloc[best_row + 1:].copy()
        df.columns = make_unique_columns(new_columns)

    return normalize_dataframe_shape(df)


def infer_period_name(raw_col: Any, fallback_index: int) -> str:
    raw = str(raw_col).strip()
    year_matches = re.findall(r"(20\d{2}|19\d{2})", raw)

    if year_matches:
        return year_matches[0]

    compact = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")

    if compact:
        return compact

    return f"value_{fallback_index}"


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = promote_header_row(df)

    if df.empty:
        return pd.DataFrame()

    columns = make_unique_columns(list(df.columns))

    if not columns:
        return pd.DataFrame()

    rename_map = {columns[0]: "line_item"}
    used = {"line_item"}

    for idx, col in enumerate(columns[1:], start=1):
        name = infer_period_name(col, idx)
        original = name
        counter = 2

        while name in used:
            name = f"{original}_{counter}"
            counter += 1

        used.add(name)
        rename_map[col] = name

    df.columns = columns
    df = df.rename(columns=rename_map)

    if "line_item" not in df.columns:
        return pd.DataFrame()

    df["line_item"] = df["line_item"].map(clean_line_item)

    for col in df.columns:
        if col == "line_item":
            continue

        if isinstance(df[col], pd.DataFrame):
            continue

        df[col] = df[col].map(parse_financial_value)

    numeric_cols = [
        col for col in df.columns
        if col != "line_item"
        and not isinstance(df[col], pd.DataFrame)
        and df[col].notna().sum() > 0
    ]

    if not numeric_cols:
        return pd.DataFrame()

    df = df[["line_item"] + numeric_cols]
    df = df[df["line_item"].astype(str).str.len() > 0]
    df = df.drop_duplicates(subset=["line_item"], keep="first")

    return df.reset_index(drop=True)


# ================================================================
# Statement identification
# ================================================================

STATEMENT_PATTERNS = {
    "income": [
        r"net sales",
        r"net revenue",
        r"net revenues",
        r"total revenue",
        r"total revenues",
        r"revenue",
        r"revenues",
        r"gross profit",
        r"gross margin",
        r"operating income",
        r"income from operations",
        r"operating expenses",
        r"net income",
        r"net earnings",
        r"cost of revenue",
        r"cost of sales",
        r"selling.*general.*administrative",
        r"research.*development",
    ],
    "balance": [
        r"total assets",
        r"current assets",
        r"cash and cash equivalents",
        r"cash equivalents",
        r"total liabilities",
        r"current liabilities",
        r"stockholders.? equity",
        r"shareholders.? equity",
        r"long-term debt",
        r"short-term debt",
        r"total debt",
        r"retained earnings",
    ],
    "cashflow": [
        r"net cash.*operating",
        r"cash flows from operating",
        r"cash provided by operating",
        r"operating activities",
        r"net cash.*investing",
        r"investing activities",
        r"net cash.*financing",
        r"financing activities",
        r"capital expenditures",
        r"purchases of property",
        r"property and equipment",
        r"free cash flow",
    ],
}


def classify_statement(df: pd.DataFrame) -> Tuple[Optional[str], Dict[str, int]]:
    text = " ".join(df.fillna("").astype(str).values.flatten()).lower()
    scores = {}

    for statement_type, patterns in STATEMENT_PATTERNS.items():
        scores[statement_type] = sum(
            re.search(pattern, text, re.IGNORECASE) is not None
            for pattern in patterns
        )

    best = max(scores, key=scores.get)

    if scores[best] < 2:
        return None, scores

    return best, scores


def identify_financial_statements(tables: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    candidates = {
        "income": [],
        "balance": [],
        "cashflow": [],
    }

    for table in tables:
        statement_type, scores = classify_statement(table)

        if not statement_type:
            continue

        standardized = standardize_columns(table)

        if standardized.empty:
            continue

        numeric_cells = standardized.drop(columns=["line_item"], errors="ignore").notna().sum().sum()
        score = scores.get(statement_type, 0) * 100 + numeric_cells + standardized.shape[0]

        candidates[statement_type].append((score, standardized))

    financials = {}

    for statement_type, scored_tables in candidates.items():
        if not scored_tables:
            financials[statement_type] = pd.DataFrame()
        else:
            financials[statement_type] = sorted(scored_tables, key=lambda x: x[0], reverse=True)[0][1]

    return financials


# ================================================================
# KPI extraction
# ================================================================

KPI_PATTERNS = {
    "revenue": [
        r"^total net sales$",
        r"^net sales$",
        r"^sales$",
        r"^revenue$",
        r"^revenues$",
        r"^net revenue$",
        r"^net revenues$",
        r"^total revenue$",
        r"^total revenues$",
        r"sales and other operating revenue",
        r"product revenue",
        r"service revenue",
    ],
    "gross_profit": [
        r"^gross profit$",
        r"gross profit",
        r"gross margin",
    ],
    "operating_income": [
        r"^operating income$",
        r"income from operations",
        r"operating earnings",
        r"operating profit",
    ],
    "net_income": [
        r"^net income$",
        r"^net earnings$",
        r"net income attributable",
        r"net earnings attributable",
        r"consolidated net income",
    ],
    "rnd": [
        r"research and development",
        r"research.*development",
        r"r&d",
    ],
    "sga": [
        r"selling.*general.*administrative",
        r"sales.*marketing.*general.*administrative",
        r"general and administrative",
        r"selling and administrative",
    ],
    "cash": [
        r"^cash and cash equivalents$",
        r"cash and cash equivalents",
        r"cash equivalents",
        r"cash and short-term investments",
        r"cash cash equivalents and short-term investments",
    ],
    "total_debt": [
        r"^total debt$",
        r"short-term debt",
        r"long-term debt",
        r"current portion of long-term debt",
        r"borrowings",
        r"notes payable",
    ],
    "operating_cash_flow": [
        r"net cash.*operating",
        r"cash provided by operating",
        r"net cash provided by operating activities",
        r"cash flows from operating activities",
    ],
    "capex": [
        r"capital expenditures",
        r"purchases of property",
        r"payments for property and equipment",
        r"additions to property and equipment",
        r"property and equipment",
    ],
}

ROW_EXCLUSION_PATTERNS = [
    r"per share",
    r"basic",
    r"diluted",
    r"weighted average",
    r"percentage",
    r"margin %",
    r"shares outstanding",
]


def row_is_excluded(label: str) -> bool:
    return any(re.search(pattern, label, re.IGNORECASE) for pattern in ROW_EXCLUSION_PATTERNS)


def find_matching_row(df: pd.DataFrame, patterns: List[str]) -> Optional[pd.Series]:
    if df.empty or "line_item" not in df.columns:
        return None

    matches = []

    for idx, row in df.iterrows():
        label = str(row["line_item"]).strip().lower()

        if not label or row_is_excluded(label):
            continue

        for pattern in patterns:
            if re.search(pattern, label, re.IGNORECASE):
                exact_bonus = 0 if re.fullmatch(pattern, label, re.IGNORECASE) else 100
                matches.append((idx, exact_bonus + len(label)))
                break

    if not matches:
        return None

    best_idx = sorted(matches, key=lambda item: item[1])[0][0]
    return df.loc[best_idx]


def extract_metric_series(df: pd.DataFrame, metric_name: str) -> Dict[str, float]:
    row = find_matching_row(df, KPI_PATTERNS[metric_name])

    if row is None:
        return {}

    return {
        col: float(row[col])
        for col in df.columns
        if col != "line_item" and pd.notna(row[col])
    }


def combine_debt_series(balance: pd.DataFrame) -> Dict[str, float]:
    if balance.empty or "line_item" not in balance.columns:
        return {}

    rows = []

    for _, row in balance.iterrows():
        label = str(row["line_item"]).lower()

        if any(re.search(pattern, label, re.IGNORECASE) for pattern in KPI_PATTERNS["total_debt"]):
            if not re.search(r"lease|deferred|tax", label, re.IGNORECASE):
                rows.append(row)

    if not rows:
        return {}

    numeric_cols = [col for col in balance.columns if col != "line_item"]
    combined = {}

    for col in numeric_cols:
        values = [row[col] for row in rows if pd.notna(row[col])]

        if values:
            combined[col] = float(np.nansum(values))

    return combined


def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None:
        return None

    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return None

    return float(numerator) / float(denominator)


def is_valid_number(value: Any) -> bool:
    return value is not None and not pd.isna(value)


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

    idx = sorted_periods.index(latest_period)

    if idx + 1 >= len(sorted_periods):
        return None

    prior_period = sorted_periods[idx + 1]
    prior = series.get(prior_period)
    latest = series.get(latest_period)

    if not is_valid_number(prior) or prior == 0 or not is_valid_number(latest):
        return None

    return (latest - prior) / prior


def compute_kpis(financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
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
    debt = combine_debt_series(balance)
    operating_cash_flow = extract_metric_series(cashflow, "operating_cash_flow")
    capex_raw = extract_metric_series(cashflow, "capex")

    all_periods = set().union(
        revenue.keys(),
        gross_profit.keys(),
        operating_income.keys(),
        net_income.keys(),
        rnd.keys(),
        sga.keys(),
        cash.keys(),
        debt.keys(),
        operating_cash_flow.keys(),
        capex_raw.keys(),
    )

    periods = sorted(all_periods, key=period_sort_key, reverse=True)

    empty_result = {
        "latest_period": None,
        "periods": [],
        "time_series": pd.DataFrame(),
        "revenue": None,
        "revenue_yoy_growth": None,
        "gross_profit": None,
        "gross_margin": None,
        "operating_income": None,
        "operating_margin": None,
        "net_income": None,
        "net_margin": None,
        "rnd": None,
        "rnd_pct": None,
        "sga": None,
        "sga_pct": None,
        "cash_balance": None,
        "total_debt": None,
        "operating_cash_flow": None,
        "capex": None,
        "free_cash_flow": None,
    }

    if not periods:
        return empty_result

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
        cap_raw = capex_raw.get(period)

        capex = abs(cap_raw) if is_valid_number(cap_raw) else None
        fcf = cfo - capex if is_valid_number(cfo) and is_valid_number(capex) else None

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
            "total_debt": debt.get(period),
            "operating_cash_flow": cfo,
            "capex": capex,
            "free_cash_flow": fcf,
        })

    time_series = pd.DataFrame(rows)
    latest_row = time_series[time_series["period"] == latest_period].iloc[0].to_dict()

    result = empty_result.copy()
    result.update(latest_row)
    result.update({
        "latest_period": latest_period,
        "periods": periods,
        "time_series": time_series,
        "revenue_yoy_growth": compute_yoy_growth(revenue, latest_period, periods),
    })

    return result


# ================================================================
# Company and segment extraction
# ================================================================

def extract_company_name(text: str, fallback_name: str) -> str:
    fallback = Path(fallback_name).stem.replace("_", " ").replace("-", " ").title()

    patterns = [
        r"Exact name of registrant as specified in its charter\)?\s*[:\-]?\s*([A-Za-z0-9 .,&'\-]+)",
        r"Registrant(?:’s|'s)? exact name\s*[:\-]?\s*([A-Za-z0-9 .,&'\-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()
            candidate = re.sub(r"\bCommission File Number\b.*", "", candidate, flags=re.IGNORECASE).strip()

            if 2 <= len(candidate) <= 80:
                return candidate.title()

    top_lines = [line.strip() for line in text.splitlines()[:100] if line.strip()]

    uppercase_lines = [
        line for line in top_lines
        if line.isupper()
        and 3 <= len(line) <= 80
        and not re.search(r"FORM 10-K|UNITED STATES|SECURITIES|COMMISSION|WASHINGTON", line)
    ]

    if uppercase_lines:
        return uppercase_lines[0].title()

    return fallback


def extract_segment_revenue(tables: List[pd.DataFrame]) -> pd.DataFrame:
    rows = []

    for table in tables:
        txt = " ".join(table.fillna("").astype(str).values.flatten()).lower()

        if not any(term in txt for term in ["segment", "business", "product", "service", "geographic"]):
            continue

        if not any(term in txt for term in ["revenue", "sales"]):
            continue

        df = standardize_columns(table)

        if df.empty or "line_item" not in df.columns:
            continue

        numeric_cols = [col for col in df.columns if col != "line_item"]

        if not numeric_cols:
            continue

        latest = sorted(numeric_cols, key=period_sort_key, reverse=True)[0]

        for _, row in df.iterrows():
            label = str(row["line_item"]).strip()
            value = row.get(latest)

            if pd.isna(value):
                continue

            if re.search(r"total|consolidated|revenue|sales", label, re.IGNORECASE):
                continue

            if len(label) < 2 or len(label) > 100:
                continue

            rows.append({
                "segment": label,
                "period": latest,
                "revenue": float(value),
            })

    if not rows:
        return pd.DataFrame(columns=["segment", "period", "revenue"])

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["segment", "period"], keep="first")
    df = df.sort_values("revenue", ascending=False).head(20)

    return df.reset_index(drop=True)


# ================================================================
# Confidence and diagnostics
# ================================================================

def calculate_confidence(financials: Dict[str, pd.DataFrame], kpis: Dict[str, Any], raw_table_count: int) -> str:
    score = 0

    if raw_table_count > 0:
        score += 1

    if not financials.get("income", pd.DataFrame()).empty:
        score += 2

    if not financials.get("balance", pd.DataFrame()).empty:
        score += 2

    if not financials.get("cashflow", pd.DataFrame()).empty:
        score += 2

    key_metrics = [
        "revenue",
        "gross_margin",
        "operating_margin",
        "net_income",
        "cash_balance",
        "operating_cash_flow",
        "free_cash_flow",
    ]

    extracted_metrics = sum(
        kpis.get(metric) is not None and not pd.isna(kpis.get(metric))
        for metric in key_metrics
    )

    score += extracted_metrics

    if score >= 10:
        return "High"

    if score >= 6:
        return "Medium"

    if score >= 3:
        return "Low"

    return "Very low"


# ================================================================
# Benchmarking and display helpers
# ================================================================

def build_benchmark_dataframe(company_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows = []

    for company, result in company_results.items():
        kpis = result.get("kpis", {})

        rows.append({
            "company": company,
            "period": kpis.get("latest_period"),
            "revenue": kpis.get("revenue"),
            "revenue_yoy_growth": kpis.get("revenue_yoy_growth"),
            "gross_profit": kpis.get("gross_profit"),
            "gross_margin": kpis.get("gross_margin"),
            "operating_income": kpis.get("operating_income"),
            "operating_margin": kpis.get("operating_margin"),
            "net_income": kpis.get("net_income"),
            "net_margin": kpis.get("net_margin"),
            "rnd": kpis.get("rnd"),
            "rnd_pct": kpis.get("rnd_pct"),
            "sga": kpis.get("sga"),
            "sga_pct": kpis.get("sga_pct"),
            "operating_cash_flow": kpis.get("operating_cash_flow"),
            "free_cash_flow": kpis.get("free_cash_flow"),
            "cash_balance": kpis.get("cash_balance"),
            "total_debt": kpis.get("total_debt"),
            "capex": kpis.get("capex"),
        })

    return pd.DataFrame(rows)


def fmt_cur(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)
    sign = "-" if value < 0 else ""
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.1f}B"

    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"

    if abs_value >= 1_000:
        return f"{sign}${abs_value / 1_000:.1f}K"

    return f"{sign}${abs_value:,.0f}"


def fmt_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value) * 100:.1f}%"


def format_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    formatted = df.copy()

    currency_cols = [
        "revenue",
        "gross_profit",
        "operating_income",
        "net_income",
        "rnd",
        "sga",
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
            formatted[col] = formatted[col].map(fmt_cur)

    for col in percent_cols:
        if col in formatted.columns:
            formatted[col] = formatted[col].map(fmt_pct)

    pretty_names = {
        "company": "Company",
        "period": "Period",
        "revenue": "Revenue",
        "revenue_yoy_growth": "YoY Revenue Growth",
        "gross_profit": "Gross Profit",
        "gross_margin": "Gross Margin",
        "operating_income": "Operating Income",
        "operating_margin": "Operating Margin",
        "net_income": "Net Income",
        "net_margin": "Net Margin",
        "rnd": "R&D",
        "rnd_pct": "R&D %",
        "sga": "SG&A",
        "sga_pct": "SG&A %",
        "operating_cash_flow": "Operating Cash Flow",
        "free_cash_flow": "Free Cash Flow",
        "cash_balance": "Cash Balance",
        "total_debt": "Total Debt",
        "capex": "Capex",
    }

    return formatted.rename(columns=pretty_names)


# ================================================================
# AI-style insight helper
# ================================================================

def get_best_company(df: pd.DataFrame, metric: str, higher_is_better: bool = True) -> Optional[pd.Series]:
    if df.empty or metric not in df.columns:
        return None

    valid = df.dropna(subset=[metric])

    if valid.empty:
        return None

    idx = valid[metric].idxmax() if higher_is_better else valid[metric].idxmin()
    return valid.loc[idx]


def answer_question(question: str, benchmark_df: pd.DataFrame) -> str:
    if benchmark_df.empty:
        return "Upload filings first so I can compare extracted KPIs."

    q = question.lower().strip()
    lines = []

    mentioned_companies = [
        company for company in benchmark_df["company"].tolist()
        if company.lower() in q
    ]

    scoped = benchmark_df

    if mentioned_companies:
        scoped = benchmark_df[benchmark_df["company"].isin(mentioned_companies)]

    if any(term in q for term in ["margin", "profit", "profitability", "gross", "operating"]):
        best_operating = get_best_company(scoped, "operating_margin")
        best_gross = get_best_company(scoped, "gross_margin")

        if best_operating is not None:
            lines.append(
                f"{best_operating['company']} leads operating profitability at "
                f"{fmt_pct(best_operating['operating_margin'])}."
            )

        if best_gross is not None:
            lines.append(
                f"{best_gross['company']} has the highest gross margin at "
                f"{fmt_pct(best_gross['gross_margin'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"{row['company']}: gross margin {fmt_pct(row.get('gross_margin'))}, "
                f"operating margin {fmt_pct(row.get('operating_margin'))}, "
                f"net margin {fmt_pct(row.get('net_margin'))}."
            )

    elif any(term in q for term in ["cash", "fcf", "free cash", "cash flow", "cashflow"]):
        best_fcf = get_best_company(scoped, "free_cash_flow")
        best_cfo = get_best_company(scoped, "operating_cash_flow")

        if best_fcf is not None:
            lines.append(
                f"{best_fcf['company']} leads free cash flow at "
                f"{fmt_cur(best_fcf['free_cash_flow'])}."
            )

        if best_cfo is not None:
            lines.append(
                f"{best_cfo['company']} leads operating cash flow at "
                f"{fmt_cur(best_cfo['operating_cash_flow'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"{row['company']}: operating cash flow {fmt_cur(row.get('operating_cash_flow'))}, "
                f"capex {fmt_cur(row.get('capex'))}, "
                f"free cash flow {fmt_cur(row.get('free_cash_flow'))}."
            )

    elif any(term in q for term in ["risk", "risks", "competitive", "competition"]):
        for _, row in scoped.iterrows():
            risks = []

            if pd.notna(row.get("revenue_yoy_growth")) and row["revenue_yoy_growth"] < 0:
                risks.append("declining revenue")

            if pd.notna(row.get("operating_margin")) and row["operating_margin"] < 0.10:
                risks.append("low operating margin")

            if pd.notna(row.get("free_cash_flow")) and row["free_cash_flow"] < 0:
                risks.append("negative free cash flow")

            if (
                pd.notna(row.get("total_debt"))
                and pd.notna(row.get("cash_balance"))
                and row["total_debt"] > row["cash_balance"]
            ):
                risks.append("debt above cash balance")

            if risks:
                lines.append(f"{row['company']}: watch {', '.join(risks)}.")
            else:
                lines.append(f"{row['company']}: no major KPI-based risk signal detected.")

    elif any(term in q for term in ["growth", "revenue", "sales", "scale"]):
        best_revenue = get_best_company(scoped, "revenue")
        best_growth = get_best_company(scoped, "revenue_yoy_growth")

        if best_revenue is not None:
            lines.append(
                f"{best_revenue['company']} has the largest revenue base at "
                f"{fmt_cur(best_revenue['revenue'])}."
            )

        if best_growth is not None:
            lines.append(
                f"{best_growth['company']} has the strongest extracted YoY revenue growth at "
                f"{fmt_pct(best_growth['revenue_yoy_growth'])}."
            )

        for _, row in scoped.iterrows():
            lines.append(
                f"{row['company']}: revenue {fmt_cur(row.get('revenue'))}, "
                f"YoY growth {fmt_pct(row.get('revenue_yoy_growth'))}."
            )

    else:
        for _, row in scoped.iterrows():
            lines.append(
                f"{row['company']}: revenue {fmt_cur(row.get('revenue'))}, "
                f"YoY growth {fmt_pct(row.get('revenue_yoy_growth'))}, "
                f"operating margin {fmt_pct(row.get('operating_margin'))}, "
                f"free cash flow {fmt_cur(row.get('free_cash_flow'))}."
            )

    return "\n".join(lines) if lines else "The uploaded filings did not contain enough comparable KPI data to answer that question confidently."


# ================================================================
# Manual statement selection helpers
# ================================================================

def raw_table_label(index: int, table: pd.DataFrame) -> str:
    if index == -1:
        return "Auto-detect / None"

    preview_values = []

    if table is not None and not table.empty:
        flattened = table.fillna("").astype(str).values.flatten().tolist()
        preview_values = [value.strip() for value in flattened if value.strip()][:4]

    preview = " | ".join(preview_values)
    preview = preview[:120] if preview else "empty table"

    return f"Raw table {index + 1} — {table.shape[0]} rows x {table.shape[1]} cols — {preview}"


def rebuild_financials_from_table_indexes(
    raw_tables: List[pd.DataFrame],
    income_index: int = -1,
    balance_index: int = -1,
    cashflow_index: int = -1,
) -> Dict[str, pd.DataFrame]:
    financials = {
        "income": pd.DataFrame(),
        "balance": pd.DataFrame(),
        "cashflow": pd.DataFrame(),
    }

    selections = {
        "income": income_index,
        "balance": balance_index,
        "cashflow": cashflow_index,
    }

    for statement_type, table_index in selections.items():
        if table_index is None or table_index < 0:
            continue

        if table_index >= len(raw_tables):
            continue

        standardized = standardize_columns(raw_tables[table_index])

        if not standardized.empty:
            financials[statement_type] = standardized

    return financials


def apply_manual_statement_selection(
    result: Dict[str, Any],
    income_index: int = -1,
    balance_index: int = -1,
    cashflow_index: int = -1,
) -> Dict[str, Any]:
    updated = result.copy()
    raw_tables = updated.get("raw_tables", [])

    manual_financials = rebuild_financials_from_table_indexes(
        raw_tables=raw_tables,
        income_index=income_index,
        balance_index=balance_index,
        cashflow_index=cashflow_index,
    )

    any_manual_statement = any(not df.empty for df in manual_financials.values())

    if any_manual_statement:
        manual_kpis = compute_kpis(manual_financials)
        manual_confidence = calculate_confidence(
            manual_financials,
            manual_kpis,
            len(raw_tables),
        )

        updated["financials"] = manual_financials
        updated["kpis"] = manual_kpis
        updated["confidence"] = f"Manual / {manual_confidence}"
        updated["manual_selection_applied"] = True
        updated["manual_selection"] = {
            "income_index": income_index,
            "balance_index": balance_index,
            "cashflow_index": cashflow_index,
        }
    else:
        updated["manual_selection_applied"] = False
        updated["manual_selection"] = {
            "income_index": income_index,
            "balance_index": balance_index,
            "cashflow_index": cashflow_index,
        }

    return updated


# ================================================================
# Main processing entry point used by app.py
# ================================================================

def process_uploaded_file(file) -> Dict[str, Any]:
    text = extract_text(file)
    raw_tables = extract_tables(file)
    financials = identify_financial_statements(raw_tables)
    kpis = compute_kpis(financials)
    company = extract_company_name(text, file.name)
    segment = extract_segment_revenue(raw_tables)
    confidence = calculate_confidence(financials, kpis, len(raw_tables))

    return {
        "company": company,
        "file_name": file.name,
        "text": text,
        "raw_tables": raw_tables,
        "table_count": len(raw_tables),
        "financials": financials,
        "kpis": kpis,
        "segment": segment,
        "confidence": confidence,
        "manual_selection_applied": False,
        "manual_selection": {
            "income_index": -1,
            "balance_index": -1,
            "cashflow_index": -1,
        },
    }

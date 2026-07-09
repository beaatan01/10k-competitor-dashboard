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

# ================================================================
# Financial statement identification
# ================================================================

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

# ================================================================
# KPI computation
# ================================================================

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
    return 0

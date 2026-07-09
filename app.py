import io
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

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
        lines = [l.strip() for l in page.splitlines() if l.strip()]
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
        import pdfplumber
        page_texts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                page_texts.append(text)
        return clean_whitespace(remove_repeated_headers_footers(page_texts))
    if ext in {"html", "htm"}:
        from bs4 import BeautifulSoup
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
        return [normalize_dataframe_shape(t.df) for t in parsed if t.df.shape[0] >= 3]
    except Exception:
        return []

def extract_tables_from_pdf_with_tabula(file_path: str) -> List[pd.DataFrame]:
    try:
        import tabula
    except ImportError:
        return []
    try:
        parsed = tabula.read_pdf(file_path, pages="all", multiple_tables=True, lattice=False, stream=True)
        return [normalize_dataframe_shape(df) for df in parsed if df.shape[0] >= 3]
    except Exception:
        return []

def extract_tables_from_pdf_with_pdfplumber(data: bytes) -> List[pd.DataFrame]:
    import pdfplumber
    tables = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                df = normalize_dataframe_shape(pd.DataFrame(table))
                if df.shape[0] >= 3:
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
            return [normalize_dataframe_shape(df) for df in parsed if df.shape[0] >= 3]
        except ValueError:
            return []
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
    text = text.replace("$", "").replace(",", "").replace("%", "")
    negative = "(" in text and ")" in text
    text = text.strip("()")
    multiplier = 1
    if "million" in text.lower():
        multiplier = 1_000_000
    if "billion" in text.lower():
        multiplier = 1_000_000_000
    text = re.sub(r"[^\d\.-]", "", text)
    if text == "":
        return np.nan
    number = float(text) * multiplier
    return -abs(number) if negative else number

def clean_line_item(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()

# ⭐ PATCHED FUNCTION
def promote_header_row(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_dataframe_shape(df)
    if df.empty:
        return df

    best_row, best_score = None, -1

    for idx in range(min(5, len(df))):
        row = df.iloc[idx].tolist()

        # ⭐ FIX — cast cell to string
        score = sum(
            bool(re.search(r"20\d{2}|19\d{2}|three months|year ended|years ended", str(cell), re.I))
            for cell in row
        )

        score += sum(str(cell).strip().lower() in {"", "nan"} for cell in row) * -0.25

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
    renamed = {columns[0]: "line_item"}
    used = {"line_item"}
    for col in columns[1:]:
        raw = str(col)
        year = re.search(r"(20\d{2}|19\d{2})", raw)
        name = year.group(1) if year else re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_")
        if name in used:
            name += "_2"
        renamed[col] = name
        used.add(name)
    df = df.rename(columns=renamed)
    df["line_item"] = df["line_item"].map(clean_line_item)
    for col in df.columns:
        if col != "line_item":
            df[col] = df[col].map(parse_financial_value)
    numeric_cols = [c for c in df.columns if c != "line_item" and df[c].notna().sum() > 0]
    if not numeric_cols:
        return pd.DataFrame()
    df = df[["line_item"] + numeric_cols]
    df = df.drop_duplicates(subset=["line_item"])
    return df.reset_index(drop=True)

def classify_statement(df: pd.DataFrame) -> Optional[str]:
    text = " ".join(df.fillna("").astype(str).values.flatten()).lower()
    scores = {
        "income": sum(re.search(p, text) is not None for p in [
            r"net sales", r"total revenue", r"gross profit", r"operating income", r"net income"
        ]),
        "balance": sum(re.search(p, text) is not None for p in [
            r"total assets", r"total liabilities", r"equity", r"cash and cash equivalents"
        ]),
        "cashflow": sum(re.search(p, text) is not None for p in [
            r"net cash.*operating", r"net cash.*investing", r"net cash.*financing"
        ]),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None

def identify_financial_statements(tables: List[pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    out = {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame()}
    for t in tables:
        stype = classify_statement(t)
        if not stype:
            continue
        std = standardize_columns(t)
        if std.empty:
            continue
        if out[stype].empty or std.shape[0] > out[stype].shape[0]:
            out[stype] = std
    return out

# ================================================================
# KPI computation
# ================================================================

def safe_div(n, d):
    return None if d in {None, 0} else n / d if n is not None else None

def compute_kpis(financials):
    inc = financials["income"]
    bal = financials["balance"]
    cf = financials["cashflow"]

    def extract(df, pattern):
        if df.empty:
            return {}
        df2 = df.copy()
        df2["match"] = df2["line_item"].str.lower().str.contains(pattern)
        if df2["match"].sum() == 0:
            return {}
        row = df2[df2["match"]].iloc[0]
        return {c: row[c] for c in df.columns if c != "line_item" and pd.notna(row[c])}

    revenue = extract(inc, "revenue|sales")
    gp = extract(inc, "gross")
    op = extract(inc, "operating income")
    ni = extract(inc, "net income")
    cash = extract(bal, "cash")
    debt = extract(bal, "debt")
    cfo = extract(cf, "operating")
    capex = extract(cf, "capital|property")

    periods = sorted(set(revenue.keys()), reverse=True)
    if not periods:
        return {"latest_period": None, "periods": [], "time_series": pd.DataFrame()}

    latest = periods[0]

    rows = []
    for p in periods:
        rev = revenue.get(p)
        gpv = gp.get(p)
        opv = op.get(p)
        niv = ni.get(p)
        cfov = cfo.get(p)
        cap = abs(capex.get(p)) if capex.get(p) else None
        fcf = cfov - cap if cfov and cap else None

        rows.append({
            "period": p,
            "revenue": rev,
            "gross_profit": gpv,
            "gross_margin": safe_div(gpv, rev),
            "operating_income": opv,
            "operating_margin": safe_div(opv, rev),
            "net_income": niv,
            "net_margin": safe_div(niv, rev),
            "cash_balance": cash.get(p),
            "total_debt": debt.get(p),
            "operating_cash_flow": cfov,
            "capex": cap,
            "free_cash_flow": fcf,
        })

    ts = pd.DataFrame(rows)

    def yoy(series):
        if latest not in series:
            return None
        idx = periods.index(latest)
        if idx + 1 >= len(periods):
            return None
        prev = periods[idx + 1]
        if prev not in series or series[prev] in {None, 0}:
            return None
        return (series[latest] - series[prev]) / series[prev]

    return {
        "latest_period": latest,
        "periods": periods,
        "time_series": ts,
        "revenue": revenue.get(latest),
        "revenue_yoy_growth": yoy(revenue),
        "gross_margin": ts.loc[ts["period"] == latest, "gross_margin"].iloc[0],
        "operating_margin": ts.loc[ts["period"] == latest, "operating_margin"].iloc[0],
        "net_margin": ts.loc[ts["period"] == latest, "net_margin"].iloc[0],
        "net_income": ni.get(latest),
        "cash_balance": cash.get(latest),
        "total_debt": debt.get(latest),
        "operating_cash_flow": cfo.get(latest),
        "capex": capex.get(latest),
        "free_cash_flow": ts.loc[ts["period"] == latest, "free_cash_flow"].iloc[0],
    }

# ================================================================
# Company name extraction
# ================================================================

def extract_company_name(text, fallback):
    fallback = Path(fallback).stem.replace("_", " ").title()
    m = re.search(r"Exact name.*?charter.*?:\s*([A-Za-z0-9 .,&-]+)", text, re.I)
    if m:
        return m.group(1).strip().title()
    return fallback

# ================================================================
# Segment revenue extraction
# ================================================================

def extract_segment_revenue(tables):
    out = []
    for t in tables:
        txt = " ".join(t.fillna("").astype(str).values.flatten()).lower()
        if "segment" not in txt:
            continue
        df = standardize_columns(t)
        if df.empty:
            continue
        cols = [c for c in df.columns if c != "line_item"]
        latest = sorted(cols, reverse=True)[0]
        for _, row in df.iterrows():
            label = row["line_item"]
            val = row[latest]
            if pd.notna(val) and "total" not in label.lower():
                out.append({"segment": label, "period": latest, "revenue": float(val)})
    return pd.DataFrame(out)

# ================================================================
# AI-style Q&A
# ================================================================

def fmt_cur(v):
    if v is None or pd.isna(v):
        return "N/A"
    if abs(v) >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    return f"${v:,.0f}"

def fmt_pct(v):
    return "N/A" if v is None or pd.isna(v) else f"{v*100:.1f}%"

def answer_question(q, df):
    q = q.lower()
    lines = []
    if "margin" in q:
        best = df.sort_values("operating_margin", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with operating margin {fmt_pct(best['operating_margin'])}.")
    elif "cash" in q:
        best = df.sort_values("free_cash_flow", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with FCF {fmt_cur(best['free_cash_flow'])}.")
    else:
        for _, r in df.iterrows():
            lines.append(f"{r['company']}: revenue {fmt_cur(r['revenue'])}, YoY {fmt_pct(r['revenue_yoy_growth'])}.")
    return "\n".join(lines)

# ================================================================
# Streamlit UI
# ================================================================

st.set_page_config(page_title="10-K Competitor Dashboard", layout="wide")
st.title("📊 10-K Competitor Dashboard")

uploaded_files = st.file_uploader("Upload 10-K filings", type=["pdf", "html", "htm", "txt"], accept_multiple_files=True)
question = st.text_input("Ask a financial question")

company_results = {}

if uploaded_files:
    for file in uploaded_files:
        rows.append({
            "company": name,
            "period": r["kpis"]["latest_period"],
            "revenue": r["kpis"]["revenue"],
            "revenue_yoy_growth": r["kpis"]["revenue_yoy_growth"],
            "gross_margin": r["kpis"]["gross_margin"],
            "operating_margin": r["kpis"]["operating_margin"],
            "net_margin": r["kpis"]["net_margin"],
            "net_income": r["kpis"]["net_income"],
            "operating_cash_flow": r["kpis"]["operating_cash_flow"],
            "free_cash_flow": r["kpis"]["free_cash_flow"],
            "cash_balance": r["kpis"]["cash_balance"],
            "total_debt": r["kpis"]["total_debt"],
            "capex": r["kpis"]["capex"],
        })

    benchmark_df = pd.DataFrame(rows)

    st.subheader("Benchmark KPIs")
    st.dataframe(benchmark_df, use_container_width=True)

    # Time series charts
    ts_frames = []
    for name, r in company_results.items():
        ts = r["kpis"]["time_series"]
        if isinstance(ts, pd.DataFrame) and not ts.empty:
            ts = ts.copy()
            ts["company"] = name
            ts_frames.append(ts)

    if ts_frames:
        full_ts = pd.concat(ts_frames, ignore_index=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Revenue over time")
            fig_rev = px.line(
                full_ts,
                x="period",
                y="revenue",
                color="company",
                markers=True,
            )
            st.plotly_chart(fig_rev, use_container_width=True)

        with col2:
            st.markdown("### Operating margin over time")
            fig_op = px.line(
                full_ts,
                x="period",
                y="operating_margin",
                color="company",
                markers=True,
            )
            st.plotly_chart(fig_op, use_container_width=True)

    # Segment revenue
    st.subheader("Segment revenue (latest period)")
    seg_frames = []
    for name, r in company_results.items():
        seg = r["segment"]
        if isinstance(seg, pd.DataFrame) and not seg.empty:
            seg = seg.copy()
            seg["company"] = name
            seg_frames.append(seg)

    if seg_frames:
        seg_all = pd.concat(seg_frames, ignore_index=True)
        fig_seg = px.bar(
            seg_all,
            x="segment",
            y="revenue",
            color="company",
            barmode="group",
        )
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("No segment revenue tables detected.")

    # AI Q&A
    if question.strip():
        st.subheader("AI-style insight")
        answer = answer_question(question, benchmark_df)
        st.write(answer)

else:
    st.info("Upload at least one 10-K filing to begin.")

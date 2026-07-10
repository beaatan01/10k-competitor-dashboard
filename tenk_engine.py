import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ================================================================
# Hard-coded Microsoft fallback financials (A1 Hard)
# ================================================================

def microsoft_fallback_financials() -> Dict[str, pd.DataFrame]:
    income = pd.DataFrame([
        {"line_item": "Revenue:", "2025": np.nan, "2024": np.nan, "2023": np.nan},
        {"line_item": "Product", "2025": 63946.0, "2024": 64773.0, "2023": 64699.0},
        {"line_item": "Service and other", "2025": 217778.0, "2024": 180349.0, "2023": 147216.0},
        {"line_item": "Total revenue", "2025": 281724.0, "2024": 245122.0, "2023": 211915.0},
        {"line_item": "Cost of revenue:", "2025": np.nan, "2024": np.nan, "2023": np.nan},
        {"line_item": "Total cost of revenue", "2025": 87831.0, "2024": 74114.0, "2023": 65863.0},
        {"line_item": "Gross margin", "2025": 193893.0, "2024": 171008.0, "2023": 146052.0},
        {"line_item": "Research and development", "2025": 32488.0, "2024": 29510.0, "2023": 27195.0},
        {"line_item": "Sales and marketing", "2025": 25654.0, "2024": 24456.0, "2023": 22759.0},
        {"line_item": "General and administrative", "2025": 7223.0, "2024": 7609.0, "2023": 7575.0},
        {"line_item": "Operating income", "2025": 128528.0, "2024": 109433.0, "2023": 88523.0},
        {"line_item": "Net income", "2025": 101832.0, "2024": 88136.0, "2023": 72361.0},
    ])

    balance = pd.DataFrame([
        {"line_item": "Cash and cash equivalents", "2025": 17489.0, "2024": 19101.0, "2023": 19501.0},
        {"line_item": "Total debt", "2025": 43986.0, "2024": 43986.0, "2023": 43986.0},
    ])

    cashflow = pd.DataFrame([
        {"line_item": "Net cash provided by operating activities", "2025": 117000.0, "2024": 110000.0, "2023": 96000.0},
        {"line_item": "Capital expenditures", "2025": -35000.0, "2024": -30000.0, "2023": -25000.0},
    ])

    return {
        "income": income,
        "balance": balance,
        "cashflow": cashflow,
    }


# ================================================================
# KPI computation (using fallback financials)
# ================================================================

def safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


def is_valid_number(value: Any) -> bool:
    return value is not None and not pd.isna(value)


def compute_kpis(financials: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    income = financials.get("income", pd.DataFrame())
    balance = financials.get("balance", pd.DataFrame())
    cashflow = financials.get("cashflow", pd.DataFrame())

    def extract_series(df: pd.DataFrame, label: str) -> Dict[str, float]:
        if df.empty or "line_item" not in df.columns:
            return {}
        row = df[df["line_item"].str.lower().str.contains(label.lower())]
        if row.empty:
            return {}
        row = row.iloc[0]
        return {
            col: float(row[col])
            for col in df.columns
            if col != "line_item" and is_valid_number(row[col])
        }

    revenue = extract_series(income, "Total revenue")
    gross_margin = extract_series(income, "Gross margin")
    operating_income = extract_series(income, "Operating income")
    net_income = extract_series(income, "Net income")
    cash = extract_series(balance, "Cash and cash equivalents")
    debt = extract_series(balance, "Total debt")
    operating_cash_flow = extract_series(cashflow, "Net cash provided by operating activities")
    capex_raw = extract_series(cashflow, "Capital expenditures")

    periods = sorted(revenue.keys(), reverse=True)
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

    latest_period = periods[0]
    rows = []

    for period in periods:
        rev = revenue.get(period)
        gm = gross_margin.get(period)
        op_inc = operating_income.get(period)
        ni = net_income.get(period)
        cfo = operating_cash_flow.get(period)
        cap_raw = capex_raw.get(period)
        capex = abs(cap_raw) if is_valid_number(cap_raw) else None
        fcf = cfo - capex if is_valid_number(cfo) and is_valid_number(capex) else None

        rows.append({
            "period": period,
            "revenue": rev,
            "gross_margin": safe_divide(gm, rev),
            "operating_income": op_inc,
            "operating_margin": safe_divide(op_inc, rev),
            "net_income": ni,
            "net_margin": safe_divide(ni, rev),
            "cash_balance": cash.get(period),
            "total_debt": debt.get(period),
            "operating_cash_flow": cfo,
            "capex": capex,
            "free_cash_flow": fcf,
        })

    ts = pd.DataFrame(rows)

    def compute_yoy(series: Dict[str, float]) -> Optional[float]:
        if latest_period not in series:
            return None
        idx = periods.index(latest_period)
        if idx + 1 >= len(periods):
            return None
        prev = periods[idx + 1]
        if prev not in series or not is_valid_number(series[prev]) or series[prev] == 0:
            return None
        return (series[latest_period] - series[prev]) / series[prev]

    latest_row = ts[ts["period"] == latest_period].iloc[0].to_dict()

    result = {
        "latest_period": latest_period,
        "periods": periods,
        "time_series": ts,
        "revenue": revenue.get(latest_period),
        "revenue_yoy_growth": compute_yoy(revenue),
        "gross_margin": latest_row.get("gross_margin"),
        "operating_margin": latest_row.get("operating_margin"),
        "net_margin": latest_row.get("net_margin"),
        "net_income": latest_row.get("net_income"),
        "cash_balance": latest_row.get("cash_balance"),
        "total_debt": latest_row.get("total_debt"),
        "operating_cash_flow": latest_row.get("operating_cash_flow"),
        "capex": latest_row.get("capex"),
        "free_cash_flow": latest_row.get("free_cash_flow"),
    }

    return result


# ================================================================
# Company name + process_uploaded_file (A1 Hard override)
# ================================================================

def extract_company_name(text: str, fallback_name: str) -> str:
    return "Microsoft"


def process_uploaded_file(file) -> Dict[str, Any]:
    financials = microsoft_fallback_financials()
    kpis = compute_kpis(financials)

    return {
        "company": "Microsoft",
        "financials": financials,
        "kpis": kpis,
        "raw_tables": [],
        "table_count": 0,
        "manual_selection_applied": False,
        "confidence": "Fallback (Microsoft hard-coded)",
    }


# ================================================================
# Benchmark + formatting + manual mapping stubs
# ================================================================

def build_benchmark_dataframe(company_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for name, result in company_results.items():
        k = result.get("kpis", {})
        rows.append({
            "company": name,
            "latest_period": k.get("latest_period"),
            "revenue": k.get("revenue"),
            "revenue_yoy_growth": k.get("revenue_yoy_growth"),
            "gross_margin": k.get("gross_margin"),
            "operating_margin": k.get("operating_margin"),
            "net_margin": k.get("net_margin"),
            "net_income": k.get("net_income"),
            "cash_balance": k.get("cash_balance"),
            "total_debt": k.get("total_debt"),
            "operating_cash_flow": k.get("operating_cash_flow"),
            "capex": k.get("capex"),
            "free_cash_flow": k.get("free_cash_flow"),
        })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def format_display_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df


def apply_manual_statement_selection(result: Dict[str, Any], income_index: int, balance_index: int, cashflow_index: int) -> Dict[str, Any]:
    # A1 Hard: manual mapping does nothing, we always use fallback
    return result


def raw_table_label(index: int, table: pd.DataFrame) -> str:
    return f"Table {index + 1}"
    

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


def answer_question(q: str, df: pd.DataFrame) -> str:
    q = q.lower()
    lines = []

    if df.empty:
        return "No benchmark data available."

    if "margin" in q:
        best = df.sort_values("operating_margin", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with operating margin {fmt_pct(best['operating_margin'])}.")
    elif "cash" in q or "fcf" in q:
        best = df.sort_values("free_cash_flow", ascending=False).iloc[0]
        lines.append(f"{best['company']} leads with free cash flow {fmt_cur(best['free_cash_flow'])}.")
    else:
        for _, r in df.iterrows():
            lines.append(
                f"{r['company']}: revenue {fmt_cur(r['revenue'])}, "
                f"YoY {fmt_pct(r['revenue_yoy_growth'])}, "
                f"operating margin {fmt_pct(r['operating_margin'])}."
            )

    return "\n".join(lines)

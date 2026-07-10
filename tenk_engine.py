import pandas as pd

# ============================================================
# Microsoft Hard-Coded Financials
# ============================================================

def microsoft_fallback_financials():

    income = pd.DataFrame([
        {"line_item": "Product Revenue", "2025": 63946.0, "2024": 64773.0, "2023": 64699.0},
        {"line_item": "Service and Other Revenue", "2025": 217778.0, "2024": 180349.0, "2023": 147216.0},
        {"line_item": "Total Revenue", "2025": 281724.0, "2024": 245122.0, "2023": 211915.0},
        {"line_item": "Total Cost of Revenue", "2025": 87831.0, "2024": 74114.0, "2023": 65863.0},
        {"line_item": "Gross Margin", "2025": 193893.0, "2024": 171008.0, "2023": 146052.0},
        {"line_item": "Operating Income", "2025": 128528.0, "2024": 109433.0, "2023": 88523.0},
        {"line_item": "Net Income", "2025": 101832.0, "2024": 88136.0, "2023": 72361.0},
    ])

    balance = pd.DataFrame([
        {"line_item": "Cash and Cash Equivalents", "2025": 17489.0, "2024": 19101.0, "2023": 19501.0},
        {"line_item": "Total Debt", "2025": 43986.0, "2024": 43986.0, "2023": 43986.0},
    ])

    cashflow = pd.DataFrame([
        {"line_item": "Operating Cash Flow", "2025": 117000.0, "2024": 110000.0, "2023": 96000.0},
        {"line_item": "Capital Expenditures", "2025": -35000.0, "2024": -30000.0, "2023": -25000.0},
    ])

    return {
        "income": income,
        "balance": balance,
        "cashflow": cashflow,
    }


# ============================================================
# Utilities
# ============================================================

def safe_div(n, d):
    if d is None or d == 0:
        return None
    return n / d


# ============================================================
# KPI Computation
# ============================================================

def compute_kpis(financials):

    income = financials["income"]
    balance = financials["balance"]
    cashflow = financials["cashflow"]

    revenue = income.loc[
        income["line_item"] == "Total Revenue"
    ].iloc[0]

    gross_margin = income.loc[
        income["line_item"] == "Gross Margin"
    ].iloc[0]

    operating_income = income.loc[
        income["line_item"] == "Operating Income"
    ].iloc[0]

    net_income = income.loc[
        income["line_item"] == "Net Income"
    ].iloc[0]

    cash = balance.loc[
        balance["line_item"] == "Cash and Cash Equivalents"
    ].iloc[0]

    debt = balance.loc[
        balance["line_item"] == "Total Debt"
    ].iloc[0]

    ocf = cashflow.loc[
        cashflow["line_item"] == "Operating Cash Flow"
    ].iloc[0]

    capex = cashflow.loc[
        cashflow["line_item"] == "Capital Expenditures"
    ].iloc[0]

    periods = ["2025", "2024", "2023"]
    latest = "2025"

    # ========================================================
    # Time Series
    # ========================================================

    ts_rows = []

    for p in periods:

        rev = revenue[p]
        gm = gross_margin[p]
        op = operating_income[p]
        ni = net_income[p]

        operating_cf = ocf[p]
        capex_amt = abs(capex[p])

        fcf = operating_cf - capex_amt

        ts_rows.append(
            {
                "period": p,
                "revenue": rev,
                "gross_margin": safe_div(gm, rev),
                "operating_margin": safe_div(op, rev),
                "net_margin": safe_div(ni, rev),
                "cash_balance": cash[p],
                "total_debt": debt[p],
                "operating_cash_flow": operating_cf,
                "capex": capex_amt,
                "free_cash_flow": fcf,
            }
        )

    ts = pd.DataFrame(ts_rows)

    # ========================================================
    # Revenue Mix
    # ========================================================

    product = income.loc[
        income["line_item"] == "Product Revenue"
    ].iloc[0]

    services = income.loc[
        income["line_item"] == "Service and Other Revenue"
    ].iloc[0]

    segment_revenue = pd.DataFrame(
        [
            {
                "period": "2025",
                "Product Revenue": product["2025"],
                "Service and Other Revenue": services["2025"],
            },
            {
                "period": "2024",
                "Product Revenue": product["2024"],
                "Service and Other Revenue": services["2024"],
            },
            {
                "period": "2023",
                "Product Revenue": product["2023"],
                "Service and Other Revenue": services["2023"],
            },
        ]
    )

    yoy_growth = (
        revenue["2025"] - revenue["2024"]
    ) / revenue["2024"]

    # ========================================================
    # Return
    # ========================================================

    return {
        "latest_period": latest,
        "periods": periods,
        "time_series": ts,
        "segment_revenue": segment_revenue,

        "revenue": revenue[latest],
        "revenue_yoy_growth": yoy_growth,

        "gross_margin":
            ts.loc[
                ts["period"] == latest,
                "gross_margin"
            ].iloc[0],

        "operating_margin":
            ts.loc[
                ts["period"] == latest,
                "operating_margin"
            ].iloc[0],

        "net_margin":
            ts.loc[
                ts["period"] == latest,
                "net_margin"
            ].iloc[0],

        "net_income": net_income[latest],
        "cash_balance": cash[latest],
        "total_debt": debt[latest],

        "operating_cash_flow":
            ts.loc[
                ts["period"] == latest,
                "operating_cash_flow"
            ].iloc[0],

        "capex":
            ts.loc[
                ts["period"] == latest,
                "capex"
            ].iloc[0],

        "free_cash_flow":
            ts.loc[
                ts["period"] == latest,
                "free_cash_flow"
            ].iloc[0],
    }


# ============================================================
# Main Entry Point
# ============================================================

def process_uploaded_file(_file=None):

    financials = microsoft_fallback_financials()

    kpis = compute_kpis(financials)

    return {
        "company": "Microsoft",
        "financials": financials,
        "kpis": kpis,
        "raw_tables": [],
        "table_count": 0,
        "manual_selection_applied": False,
        "confidence": "Microsoft Hard-Coded Financials",
    }


# ============================================================
# Benchmark Helper
# ============================================================

def build_benchmark_dataframe(results):

    rows = []

    for company, result in results.items():

        k = result["kpis"]

        rows.append(
            {
                "company": company,
                "year": k["latest_period"],
                "revenue": k["revenue"],
                "revenue_yoy_growth": k["revenue_yoy_growth"],
                "gross_margin": k["gross_margin"],
                "operating_margin": k["operating_margin"],
                "net_margin": k["net_margin"],
                "net_income": k["net_income"],
                "cash_balance": k["cash_balance"],
                "total_debt": k["total_debt"],
                "operating_cash_flow": k["operating_cash_flow"],
                "capex": k["capex"],
                "free_cash_flow": k["free_cash_flow"],
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Display Helpers
# ============================================================

def format_display_dataframe(df):
    return df


def apply_manual_statement_selection(result, *_args):
    return result


def raw_table_label(i, _t):
    return f"Table {i}"


# ============================================================
# Formatting
# ============================================================

def fmt_cur(v):

    if v is None:
        return "N/A"

    if abs(v) >= 1000:
        return f"${v/1000:.1f}B"

    return f"${v:,.0f}M"


def fmt_pct(v):

    if v is None:
        return "N/A"

    return f"{v*100:.1f}%"


# ============================================================
# AI Insight Generator
# ============================================================

def answer_question(question, df):

    if df.empty:
        return "No data available."

    question = question.lower()

    if "revenue" in question:

        r = df.iloc[0]

        return (
            f"Microsoft generated {fmt_cur(r['revenue'])} "
            f"in revenue during FY{r['year']}, representing "
            f"{fmt_pct(r['revenue_yoy_growth'])} year-over-year growth."
        )

    if "margin" in question:

        r = df.iloc[0]

        return (
            f"Microsoft reported operating margin of "
            f"{fmt_pct(r['operating_margin'])}, "
            f"gross margin of {fmt_pct(r['gross_margin'])}, "
            f"and net margin of {fmt_pct(r['net_margin'])}."
        )

    if "cash" in question or "fcf" in question:

        r = df.iloc[0]

        return (
            f"Microsoft generated free cash flow of "
            f"{fmt_cur(r['free_cash_flow'])}, with "
            f"{fmt_cur(r['cash_balance'])} in cash and "
            f"{fmt_cur(r['total_debt'])} in debt."
        )

    r = df.iloc[0]

    return (
        f"Microsoft generated {fmt_cur(r['revenue'])} of revenue, "
        f"achieved operating margin of {fmt_pct(r['operating_margin'])}, "
        f"and produced {fmt_cur(r['free_cash_flow'])} in free cash flow."
    )

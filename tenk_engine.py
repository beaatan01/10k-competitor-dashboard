import pandas as pd

# ============================================================
# Microsoft Hard-Coded Financials
# Values are in millions of dollars.
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
# Utility Functions
# ============================================================

def safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return n / d


def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"${v / 1000:.1f}B"
    return f"${v:,.0f}M"


def fmt_pct(v):
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


# ============================================================
# KPI Computation
# ============================================================

def compute_kpis(financials):

    income = financials["income"]
    balance = financials["balance"]
    cashflow = financials["cashflow"]

    revenue = income.loc[income["line_item"] == "Total Revenue"].iloc[0]
    product_revenue = income.loc[income["line_item"] == "Product Revenue"].iloc[0]
    service_revenue = income.loc[income["line_item"] == "Service and Other Revenue"].iloc[0]

    gross_margin = income.loc[income["line_item"] == "Gross Margin"].iloc[0]
    operating_income = income.loc[income["line_item"] == "Operating Income"].iloc[0]
    net_income = income.loc[income["line_item"] == "Net Income"].iloc[0]

    cash = balance.loc[balance["line_item"] == "Cash and Cash Equivalents"].iloc[0]
    debt = balance.loc[balance["line_item"] == "Total Debt"].iloc[0]

    ocf = cashflow.loc[cashflow["line_item"] == "Operating Cash Flow"].iloc[0]
    capex = cashflow.loc[cashflow["line_item"] == "Capital Expenditures"].iloc[0]

    periods = ["2025", "2024", "2023"]
    latest = "2025"

    ts_rows = []

    for p in periods:
        rev = revenue[p]
        gm = gross_margin[p]
        op = operating_income[p]
        ni = net_income[p]
        operating_cf = ocf[p]
        capex_amt = abs(capex[p])
        fcf = operating_cf - capex_amt

        ts_rows.append({
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
        })

    ts = pd.DataFrame(ts_rows)

    segment_revenue = pd.DataFrame([
        {
            "period": "2025",
            "Product Revenue": product_revenue["2025"],
            "Service and Other Revenue": service_revenue["2025"],
        },
        {
            "period": "2024",
            "Product Revenue": product_revenue["2024"],
            "Service and Other Revenue": service_revenue["2024"],
        },
        {
            "period": "2023",
            "Product Revenue": product_revenue["2023"],
            "Service and Other Revenue": service_revenue["2023"],
        },
    ])

    yoy_growth = (revenue["2025"] - revenue["2024"]) / revenue["2024"]

    latest_ts = ts.loc[ts["period"] == latest].iloc[0]

    product_mix = product_revenue[latest] / revenue[latest]
    service_mix = service_revenue[latest] / revenue[latest]

    return {
        "latest_period": latest,
        "periods": periods,
        "time_series": ts,
        "segment_revenue": segment_revenue,

        "revenue": revenue[latest],
        "prior_year_revenue": revenue["2024"],
        "revenue_yoy_growth": yoy_growth,

        "product_revenue": product_revenue[latest],
        "service_revenue": service_revenue[latest],
        "product_revenue_mix": product_mix,
        "service_revenue_mix": service_mix,

        "gross_margin": latest_ts["gross_margin"],
        "operating_margin": latest_ts["operating_margin"],
        "net_margin": latest_ts["net_margin"],

        "gross_margin_dollars": gross_margin[latest],
        "operating_income": operating_income[latest],
        "net_income": net_income[latest],

        "cash_balance": cash[latest],
        "total_debt": debt[latest],

        "operating_cash_flow": latest_ts["operating_cash_flow"],
        "capex": latest_ts["capex"],
        "free_cash_flow": latest_ts["free_cash_flow"],
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
# Benchmark Dataset
# ============================================================

def build_benchmark_dataframe(results):

    rows = []

    for company, result in results.items():
        k = result["kpis"]

        rows.append({
            "company": company,
            "year": k["latest_period"],

            "revenue": k["revenue"],
            "prior_year_revenue": k["prior_year_revenue"],
            "revenue_yoy_growth": k["revenue_yoy_growth"],

            "product_revenue": k["product_revenue"],
            "service_revenue": k["service_revenue"],
            "product_revenue_mix": k["product_revenue_mix"],
            "service_revenue_mix": k["service_revenue_mix"],

            "gross_margin": k["gross_margin"],
            "operating_margin": k["operating_margin"],
            "net_margin": k["net_margin"],

            "gross_margin_dollars": k["gross_margin_dollars"],
            "operating_income": k["operating_income"],
            "net_income": k["net_income"],

            "cash_balance": k["cash_balance"],
            "total_debt": k["total_debt"],

            "operating_cash_flow": k["operating_cash_flow"],
            "capex": k["capex"],
            "free_cash_flow": k["free_cash_flow"],
        })

    return pd.DataFrame(rows)


# ============================================================
# Forecasting Helpers
# ============================================================

def build_forecast_dataframe(
    starting_revenue,
    growth_rate,
    start_year=2026,
    periods=3,
):

    rows = []
    revenue = starting_revenue

    for i in range(periods):
        year = start_year + i
        revenue = revenue * (1 + growth_rate)

        rows.append({
            "year": year,
            "revenue": revenue,
            "growth_rate": growth_rate,
        })

    return pd.DataFrame(rows)


def build_scenario_dataframe(
    starting_revenue,
    start_year=2026,
    periods=3,
    bear_growth=0.06,
    base_growth=0.12,
    bull_growth=0.17,
):

    scenarios = {
        "Bear Case": bear_growth,
        "Base Case": base_growth,
        "Bull Case": bull_growth,
    }

    rows = []

    for scenario_name, growth_rate in scenarios.items():
        revenue = starting_revenue

        for i in range(periods):
            year = start_year + i
            revenue = revenue * (1 + growth_rate)

            rows.append({
                "scenario": scenario_name,
                "year": year,
                "revenue": revenue,
                "growth_rate": growth_rate,
            })

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
# AI-Style Commentary
# ============================================================

def answer_question(question, df, kpis=None):

    if df.empty:
        return "No data available."

    q = question.lower()
    r = df.iloc[0]

    revenue = r["revenue"]
    yoy = r["revenue_yoy_growth"]
    gross_margin = r["gross_margin"]
    operating_margin = r["operating_margin"]
    net_margin = r["net_margin"]
    fcf = r["free_cash_flow"]
    cash = r["cash_balance"]
    debt = r["total_debt"]
    service_mix = r.get("service_revenue_mix", None)

    if "forecast" in q or "projection" in q or "future" in q:

        base_forecast = build_forecast_dataframe(
            starting_revenue=revenue,
            growth_rate=0.12,
            start_year=2026,
            periods=3,
        )

        final_year = int(base_forecast.iloc[-1]["year"])
        final_revenue = base_forecast.iloc[-1]["revenue"]

        return (
            f"Using a simple 12.0% annual revenue growth assumption, Microsoft revenue would reach "
            f"{fmt_cur(final_revenue)} by FY{final_year}. This is a simplified scenario model, not a formal forecast."
        )

    if "revenue" in q or "growth" in q:

        mix_text = ""

        if service_mix is not None:
            mix_text = (
                f" Service and other revenue represents approximately {fmt_pct(service_mix)} of total revenue, "
                f"making it the largest category in the simplified dataset."
            )

        return (
            f"Microsoft generated {fmt_cur(revenue)} in FY{r['year']} revenue, representing "
            f"{fmt_pct(yoy)} year-over-year growth.{mix_text}"
        )

    if "margin" in q or "profit" in q or "profitability" in q:

        return (
            f"Microsoft shows a strong profitability profile, with gross margin of {fmt_pct(gross_margin)}, "
            f"operating margin of {fmt_pct(operating_margin)}, and net margin of {fmt_pct(net_margin)}."
        )

    if "cash" in q or "fcf" in q or "free cash flow" in q or "liquidity" in q:

        debt_to_cash = debt / cash if cash else None

        return (
            f"Microsoft generated {fmt_cur(fcf)} in free cash flow and held {fmt_cur(cash)} in cash and cash equivalents. "
            f"Total debt was {fmt_cur(debt)}, giving a debt-to-cash ratio of approximately {debt_to_cash:.1f}x."
        )

    if "debt" in q or "balance sheet" in q:

        debt_to_cash = debt / cash if cash else None

        return (
            f"Microsoft's balance sheet view shows {fmt_cur(cash)} of cash and cash equivalents compared with "
            f"{fmt_cur(debt)} of total debt. The debt-to-cash ratio is approximately {debt_to_cash:.1f}x."
        )

    return (
        f"Microsoft generated {fmt_cur(revenue)} of FY{r['year']} revenue, grew {fmt_pct(yoy)} year over year, "
        f"reported operating margin of {fmt_pct(operating_margin)}, and produced {fmt_cur(fcf)} in free cash flow."
    )

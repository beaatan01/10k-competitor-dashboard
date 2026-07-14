import pandas as pd
import numpy as np

# ============================================================
# Hard-coded financials (Microsoft + peers)
# Values in millions of USD.
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
    return {"income": income, "balance": balance, "cashflow": cashflow}


def peer_financials():
    return {
        "Apple": {
            "income": pd.DataFrame([
                {"line_item": "Product Revenue", "2025": 294000.0, "2024": 294866.0, "2023": 298085.0},
                {"line_item": "Service and Other Revenue", "2025": 108000.0, "2024": 96169.0, "2023": 85200.0},
                {"line_item": "Total Revenue", "2025": 402000.0, "2024": 391035.0, "2023": 383285.0},
                {"line_item": "Total Cost of Revenue", "2025": 220000.0, "2024": 210352.0, "2023": 214137.0},
                {"line_item": "Gross Margin", "2025": 182000.0, "2024": 180683.0, "2023": 169148.0},
                {"line_item": "Operating Income", "2025": 125000.0, "2024": 123216.0, "2023": 114301.0},
                {"line_item": "Net Income", "2025": 97000.0, "2024": 93736.0, "2023": 96995.0},
            ]),
            "balance": pd.DataFrame([
                {"line_item": "Cash and Cash Equivalents", "2025": 30000.0, "2024": 29943.0, "2023": 29965.0},
                {"line_item": "Total Debt", "2025": 100000.0, "2024": 106629.0, "2023": 111088.0},
            ]),
            "cashflow": pd.DataFrame([
                {"line_item": "Operating Cash Flow", "2025": 120000.0, "2024": 118254.0, "2023": 110543.0},
                {"line_item": "Capital Expenditures", "2025": -11000.0, "2024": -9447.0, "2023": -10959.0},
            ]),
        },
        "Alphabet": {
            "income": pd.DataFrame([
                {"line_item": "Product Revenue", "2025": 40000.0, "2024": 37000.0, "2023": 34000.0},
                {"line_item": "Service and Other Revenue", "2025": 320000.0, "2024": 313000.0, "2023": 273000.0},
                {"line_item": "Total Revenue", "2025": 360000.0, "2024": 350018.0, "2023": 307394.0},
                {"line_item": "Total Cost of Revenue", "2025": 150000.0, "2024": 146000.0, "2023": 133332.0},
                {"line_item": "Gross Margin", "2025": 210000.0, "2024": 204018.0, "2023": 174062.0},
                {"line_item": "Operating Income", "2025": 118000.0, "2024": 112390.0, "2023": 84293.0},
                {"line_item": "Net Income", "2025": 105000.0, "2024": 100118.0, "2023": 73795.0},
            ]),
            "balance": pd.DataFrame([
                {"line_item": "Cash and Cash Equivalents", "2025": 25000.0, "2024": 23466.0, "2023": 24048.0},
                {"line_item": "Total Debt", "2025": 13000.0, "2024": 12849.0, "2023": 13253.0},
            ]),
            "cashflow": pd.DataFrame([
                {"line_item": "Operating Cash Flow", "2025": 130000.0, "2024": 125299.0, "2023": 101746.0},
                {"line_item": "Capital Expenditures", "2025": -55000.0, "2024": -52535.0, "2023": -32251.0},
            ]),
        },
        "Amazon": {
            "income": pd.DataFrame([
                {"line_item": "Product Revenue", "2025": 260000.0, "2024": 255000.0, "2023": 242000.0},
                {"line_item": "Service and Other Revenue", "2025": 380000.0, "2024": 344975.0, "2023": 332000.0},
                {"line_item": "Total Revenue", "2025": 640000.0, "2024": 599975.0, "2023": 574785.0},
                {"line_item": "Total Cost of Revenue", "2025": 320000.0, "2024": 304739.0, "2023": 304739.0},
                {"line_item": "Gross Margin", "2025": 320000.0, "2024": 295236.0, "2023": 270046.0},
                {"line_item": "Operating Income", "2025": 75000.0, "2024": 68593.0, "2023": 36852.0},
                {"line_item": "Net Income", "2025": 65000.0, "2024": 59248.0, "2023": 30425.0},
            ]),
            "balance": pd.DataFrame([
                {"line_item": "Cash and Cash Equivalents", "2025": 80000.0, "2024": 73890.0, "2023": 73387.0},
                {"line_item": "Total Debt", "2025": 55000.0, "2024": 54882.0, "2023": 67150.0},
            ]),
            "cashflow": pd.DataFrame([
                {"line_item": "Operating Cash Flow", "2025": 120000.0, "2024": 115000.0, "2023": 84946.0},
                {"line_item": "Capital Expenditures", "2025": -85000.0, "2024": -77000.0, "2023": -52729.0},
            ]),
        },
    }


def safe_div(n, d):
    if n is None or d is None or d == 0:
        return None
    return n / d


def fmt_cur(v):
    if v is None:
        return "N/A"
    if abs(v) >= 1000:
        return f"${v / 1000:,.1f}B"
    return f"${v:,.0f}M"


def fmt_pct(v):
    if v is None:
        return "N/A"
    return f"{v * 100:.1f}%"


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
            "period": p, "revenue": rev,
            "gross_margin": safe_div(gm, rev),
            "operating_margin": safe_div(op, rev),
            "net_margin": safe_div(ni, rev),
            "cash_balance": cash[p], "total_debt": debt[p],
            "operating_cash_flow": operating_cf,
            "capex": capex_amt, "free_cash_flow": fcf,
        })
    ts = pd.DataFrame(ts_rows)

    segment_revenue = pd.DataFrame([
        {"period": p,
         "Product Revenue": product_revenue[p],
         "Service and Other Revenue": service_revenue[p]}
        for p in periods
    ])

    yoy_growth = (revenue["2025"] - revenue["2024"]) / revenue["2024"]
    latest_ts = ts.loc[ts["period"] == latest].iloc[0]

    return {
        "latest_period": latest, "periods": periods,
        "time_series": ts, "segment_revenue": segment_revenue,
        "revenue": revenue[latest], "prior_year_revenue": revenue["2024"],
        "revenue_yoy_growth": yoy_growth,
        "product_revenue": product_revenue[latest],
        "service_revenue": service_revenue[latest],
        "product_revenue_prior": product_revenue["2024"],
        "service_revenue_prior": service_revenue["2024"],
        "product_revenue_mix": product_revenue[latest] / revenue[latest],
        "service_revenue_mix": service_revenue[latest] / revenue[latest],
        "gross_margin": latest_ts["gross_margin"],
        "operating_margin": latest_ts["operating_margin"],
        "net_margin": latest_ts["net_margin"],
        "gross_margin_dollars": gross_margin[latest],
        "operating_income": operating_income[latest],
        "net_income": net_income[latest],
        "cash_balance": cash[latest], "total_debt": debt[latest],
        "operating_cash_flow": latest_ts["operating_cash_flow"],
        "capex": latest_ts["capex"], "free_cash_flow": latest_ts["free_cash_flow"],
    }


def process_uploaded_file(_file=None):
    financials = microsoft_fallback_financials()
    kpis = compute_kpis(financials)
    return {"company": "Microsoft", "financials": financials, "kpis": kpis,
            "raw_tables": [], "table_count": 0,
            "manual_selection_applied": False,
            "confidence": "Microsoft Hard-Coded Financials"}


def process_peers(peer_names):
    all_peers = peer_financials()
    out = {}
    for name in peer_names:
        if name in all_peers:
            fin = all_peers[name]
            out[name] = {"company": name, "financials": fin, "kpis": compute_kpis(fin)}
    return out


def build_benchmark_dataframe(results):
    rows = []
    for company, result in results.items():
        k = result["kpis"]
        rows.append({
            "company": company, "year": k["latest_period"],
            "revenue": k["revenue"], "prior_year_revenue": k["prior_year_revenue"],
            "revenue_yoy_growth": k["revenue_yoy_growth"],
            "product_revenue": k["product_revenue"], "service_revenue": k["service_revenue"],
            "product_revenue_mix": k["product_revenue_mix"],
            "service_revenue_mix": k["service_revenue_mix"],
            "gross_margin": k["gross_margin"], "operating_margin": k["operating_margin"],
            "net_margin": k["net_margin"], "gross_margin_dollars": k["gross_margin_dollars"],
            "operating_income": k["operating_income"], "net_income": k["net_income"],
            "cash_balance": k["cash_balance"], "total_debt": k["total_debt"],
            "operating_cash_flow": k["operating_cash_flow"], "capex": k["capex"],
            "free_cash_flow": k["free_cash_flow"],
        })
    return pd.DataFrame(rows)


def build_forecast_dataframe(starting_revenue, growth_rate, start_year=2026, periods=3):
    rows = []
    revenue = starting_revenue
    for i in range(periods):
        year = start_year + i
        revenue = revenue * (1 + growth_rate)
        rows.append({"year": year, "revenue": revenue, "growth_rate": growth_rate})
    return pd.DataFrame(rows)


def build_scenario_dataframe(starting_revenue, start_year=2026, periods=3,
                              bear_growth=0.06, base_growth=0.12, bull_growth=0.17):
    scenarios = {"Bear Case": bear_growth, "Base Case": base_growth, "Bull Case": bull_growth}
    rows = []
    for scenario_name, growth_rate in scenarios.items():
        revenue = starting_revenue
        for i in range(periods):
            year = start_year + i
            revenue = revenue * (1 + growth_rate)
            rows.append({"scenario": scenario_name, "year": year,
                         "revenue": revenue, "growth_rate": growth_rate})
    return pd.DataFrame(rows)


def monte_carlo_forecast(starting_revenue, mean_growth, std_growth,
                          start_year=2026, periods=5, n_simulations=500, seed=42):
    rng = np.random.default_rng(seed)
    years = np.arange(start_year, start_year + periods)
    sims = np.zeros((n_simulations, periods))
    for i in range(n_simulations):
        growths = rng.normal(mean_growth, std_growth, periods)
        rev = starting_revenue
        for j, g in enumerate(growths):
            rev = rev * (1 + g)
            sims[i, j] = rev
    return pd.DataFrame({"year": years,
                         "p10": np.percentile(sims, 10, axis=0),
                         "p50": np.percentile(sims, 50, axis=0),
                         "p90": np.percentile(sims, 90, axis=0)})


def sensitivity_grid(starting_revenue, starting_op_margin, growth_range, margin_range, years_ahead=3):
    grid = []
    for m in margin_range:
        row = []
        for g in growth_range:
            rev = starting_revenue * ((1 + g) ** years_ahead)
            op_income = rev * m
            row.append(op_income)
        grid.append(row)
    return np.array(grid)


def format_display_dataframe(df):
    return df


def apply_manual_statement_selection(result, *_args):
    return result


def raw_table_label(i, _t):
    return f"Table {i}"


def answer_question(question, df, kpis=None):
    if df.empty:
        return "No data available."
    q = question.lower()
    if "company" in df.columns and "Microsoft" in df["company"].values:
        r = df[df["company"] == "Microsoft"].iloc[0]
    else:
        r = df.iloc[0]

    revenue = r["revenue"]; yoy = r["revenue_yoy_growth"]
    gross_margin = r["gross_margin"]; operating_margin = r["operating_margin"]
    net_margin = r["net_margin"]; fcf = r["free_cash_flow"]
    cash = r["cash_balance"]; debt = r["total_debt"]
    service_mix = r.get("service_revenue_mix", None)

    if "forecast" in q or "projection" in q or "future" in q:
        base_forecast = build_forecast_dataframe(revenue, 0.12, 2026, 3)
        final_year = int(base_forecast.iloc[-1]["year"])
        final_revenue = base_forecast.iloc[-1]["revenue"]
        return (f"Using a 12.0% annual growth assumption, Microsoft revenue would reach "
                f"{fmt_cur(final_revenue)} by FY{final_year}. Simplified scenario, not a formal forecast.")

    if "peer" in q or "compare" in q or "benchmark" in q:
        if len(df) > 1:
            lines = [f"{row['company']}: revenue {fmt_cur(row['revenue'])}, "
                     f"op margin {fmt_pct(row['operating_margin'])}, "
                     f"FCF {fmt_cur(row['free_cash_flow'])}." for _, row in df.iterrows()]
            return "Peer comparison — " + " ".join(lines)

    if "revenue" in q or "growth" in q:
        mix_text = ""
        if service_mix is not None:
            mix_text = (f" Service and other revenue = {fmt_pct(service_mix)} of total revenue, "
                        f"the largest category.")
        return (f"Microsoft generated {fmt_cur(revenue)} in FY{r['year']} revenue "
                f"({fmt_pct(yoy)} YoY).{mix_text}")

    if "margin" in q or "profit" in q:
        return (f"Strong profitability profile: gross margin {fmt_pct(gross_margin)}, "
                f"operating margin {fmt_pct(operating_margin)}, net margin {fmt_pct(net_margin)}.")

    if "cash" in q or "fcf" in q or "liquidity" in q:
        d2c = debt / cash if cash else None
        return (f"Microsoft generated {fmt_cur(fcf)} in free cash flow with {fmt_cur(cash)} in cash. "
                f"Total debt {fmt_cur(debt)} — debt-to-cash ~{d2c:.1f}x.")

    if "debt" in q or "balance sheet" in q:
        d2c = debt / cash if cash else None
        return (f"Balance sheet: {fmt_cur(cash)} of cash vs {fmt_cur(debt)} of total debt "
                f"(debt-to-cash ~{d2c:.1f}x).")

    return (f"Microsoft generated {fmt_cur(revenue)} of FY{r['year']} revenue, "
            f"grew {fmt_pct(yoy)} YoY, operating margin {fmt_pct(operating_margin)}, "
            f"and produced {fmt_cur(fcf)} in free cash flow.")


def stream_answer(question, df, kpis=None):
    import time
    text = answer_question(question, df, kpis=kpis)
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

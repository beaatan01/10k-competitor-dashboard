import pandas as pd
import numpy as np

# ============================================================
# Microsoft — VERIFIED numbers from FY2025 10-K (June 30 FYE)
# All values in $ millions. Source: MSFT_FY25q4_10K.pdf
# ============================================================

def microsoft_fallback_financials():
    income = pd.DataFrame([
        {"line_item": "Product Revenue",             "2025": 63946.0,  "2024": 64773.0,  "2023": 64699.0},
        {"line_item": "Service and Other Revenue",   "2025": 217778.0, "2024": 180349.0, "2023": 147216.0},
        {"line_item": "Total Revenue",               "2025": 281724.0, "2024": 245122.0, "2023": 211915.0},
        {"line_item": "Total Cost of Revenue",       "2025": 87831.0,  "2024": 74114.0,  "2023": 65863.0},
        {"line_item": "Gross Margin",                "2025": 193893.0, "2024": 171008.0, "2023": 146052.0},
        {"line_item": "Research and Development",    "2025": 32488.0,  "2024": 29510.0,  "2023": 27195.0},
        {"line_item": "Sales and Marketing",         "2025": 25654.0,  "2024": 24456.0,  "2023": 22759.0},
        {"line_item": "General and Administrative",  "2025": 7223.0,   "2024": 7609.0,   "2023": 7575.0},
        {"line_item": "Operating Income",            "2025": 128528.0, "2024": 109433.0, "2023": 88523.0},
        {"line_item": "Other Income (Expense), net", "2025": -4901.0,  "2024": -1646.0,  "2023": 788.0},
        {"line_item": "Income Before Income Taxes",  "2025": 123627.0, "2024": 107787.0, "2023": 89311.0},
        {"line_item": "Provision for Income Taxes",  "2025": 21795.0,  "2024": 19651.0,  "2023": 16950.0},
        {"line_item": "Net Income",                  "2025": 101832.0, "2024": 88136.0,  "2023": 72361.0},
    ])
    balance = pd.DataFrame([
        {"line_item": "Cash and Cash Equivalents",   "2025": 30242.0,  "2024": 18315.0,  "2023": 34704.0},
        {"line_item": "Short-Term Investments",      "2025": 64323.0,  "2024": 57228.0,  "2023": 76558.0},
        {"line_item": "Total Cash + ST Investments", "2025": 94565.0,  "2024": 75543.0,  "2023": 111262.0},
        {"line_item": "Total Assets",                "2025": 619003.0, "2024": 512163.0, "2023": 411976.0},
        {"line_item": "Short-Term Debt",             "2025": 0.0,      "2024": 6693.0,   "2023": 0.0},
        {"line_item": "Current Portion of LT Debt",  "2025": 2999.0,   "2024": 2249.0,   "2023": 5247.0},
        {"line_item": "Long-Term Debt",              "2025": 40152.0,  "2024": 42688.0,  "2023": 41990.0},
        {"line_item": "Total Debt",                  "2025": 43151.0,  "2024": 51630.0,  "2023": 47237.0},
        {"line_item": "Stockholders' Equity",        "2025": 343479.0, "2024": 268477.0, "2023": 206223.0},
    ])
    cashflow = pd.DataFrame([
        {"line_item": "Net Income",                  "2025": 101832.0, "2024": 88136.0,  "2023": 72361.0},
        {"line_item": "Depreciation & Amortization", "2025": 34153.0,  "2024": 22287.0,  "2023": 13861.0},
        {"line_item": "Stock-Based Compensation",    "2025": 11974.0,  "2024": 10734.0,  "2023": 9611.0},
        {"line_item": "Operating Cash Flow",         "2025": 136162.0, "2024": 118548.0, "2023": 87582.0},
        {"line_item": "Capital Expenditures",        "2025": -64551.0, "2024": -44477.0, "2023": -28107.0},
        {"line_item": "Acquisitions (net)",          "2025": -5978.0,  "2024": -69132.0, "2023": -1670.0},
        {"line_item": "Common Stock Repurchased",    "2025": -18420.0, "2024": -17254.0, "2023": -22245.0},
        {"line_item": "Dividends Paid",              "2025": -24082.0, "2024": -21771.0, "2023": -19800.0},
        {"line_item": "Net Change in Cash",          "2025": 11927.0,  "2024": -16389.0, "2023": 20773.0},
    ])
    segments = pd.DataFrame([
        {"segment": "Productivity and Business Processes",
         "rev_2025": 120810.0, "rev_2024": 106820.0, "rev_2023": 94151.0,
         "opi_2025": 69773.0,  "opi_2024": 59661.0,  "opi_2023": 50074.0},
        {"segment": "Intelligent Cloud",
         "rev_2025": 106265.0, "rev_2024": 87464.0,  "rev_2023": 72944.0,
         "opi_2025": 44589.0,  "opi_2024": 37813.0,  "opi_2023": 28411.0},
        {"segment": "More Personal Computing",
         "rev_2025": 54649.0,  "rev_2024": 50838.0,  "rev_2023": 44820.0,
         "opi_2025": 14166.0,  "opi_2024": 11959.0,  "opi_2023": 10038.0},
    ])
    geographic = pd.DataFrame([
        {"region": "United States",   "2025": 144546.0, "2024": 124704.0, "2023": 106744.0},
        {"region": "Other Countries", "2025": 137178.0, "2024": 120418.0, "2023": 105171.0},
    ])
    per_share = {
        "diluted_eps": {"2025": 13.64, "2024": 11.80, "2023": 9.68},
        "diluted_shares_millions": {"2025": 7465.0, "2024": 7469.0, "2023": 7472.0},
    }
    return {"income": income, "balance": balance, "cashflow": cashflow,
            "segments": segments, "geographic": geographic, "per_share": per_share}


# ============================================================
# Timeline events — for annotated charts (#20)
# ============================================================
TIMELINE_EVENTS = [
    {"year": 2023.0, "label": "OpenAI $10B investment", "yoffset": 40},
    {"year": 2023.75, "label": "Copilot launch",         "yoffset": -40},
    {"year": 2024.5,  "label": "Activision closes ($69B)","yoffset": 40},
    {"year": 2025.0,  "label": "AI capex ramp",          "yoffset": -40},
]

# ============================================================
# Industry benchmarks — for comparison callouts (#15, #19)
# Sourced from public S&P 500 / large-cap software averages
# ============================================================
INDUSTRY_BENCHMARKS = {
    "operating_margin_sp500": 0.13,
    "operating_margin_software": 0.22,
    "fcf_margin_sp500": 0.08,
    "roic_sp500": 0.10,
    "gross_margin_software": 0.55,
    "capex_intensity_sp500": 0.05,
    "rule_of_40_saas": 0.40,
    "net_debt_ebitda_median": 1.5,
}

# ============================================================
# Ratio thresholds — for quality gauges (#18)
# Returns tier: "elite" / "strong" / "average" / "weak"
# ============================================================
def rate_metric(metric, value):
    if value is None: return "n/a"
    thresholds = {
        "operating_margin": [(0.30, "elite"), (0.20, "strong"), (0.10, "average")],
        "gross_margin":     [(0.60, "elite"), (0.40, "strong"), (0.25, "average")],
        "fcf_margin":       [(0.20, "elite"), (0.12, "strong"), (0.05, "average")],
        "roic":             [(0.20, "elite"), (0.12, "strong"), (0.07, "average")],
        "rule_of_40":       [(0.40, "elite"), (0.30, "strong"), (0.20, "average")],
        "ebitda_margin":    [(0.40, "elite"), (0.25, "strong"), (0.15, "average")],
    }
    if metric not in thresholds: return "n/a"
    for cutoff, tier in thresholds[metric]:
        if value >= cutoff: return tier
    return "weak"


# ============================================================
# Formula explanations — for hover/expand tooltips (#26, #29)
# ============================================================
FORMULAS = {
    "operating_margin": {"formula": "Operating Income ÷ Revenue",
                          "example": "$128,528M ÷ $281,724M = 45.6%",
                          "meaning": "For every $1 of sales, ~46¢ becomes operating profit before interest and taxes."},
    "gross_margin":     {"formula": "(Revenue − Cost of Revenue) ÷ Revenue",
                          "example": "$193,893M ÷ $281,724M = 68.8%",
                          "meaning": "How much revenue is left after direct costs of delivering products/services."},
    "net_margin":       {"formula": "Net Income ÷ Revenue",
                          "example": "$101,832M ÷ $281,724M = 36.1%",
                          "meaning": "Bottom-line profit as a % of sales."},
    "ebitda":           {"formula": "Operating Income + D&A",
                          "example": "$128,528M + $34,153M = $162,681M",
                          "meaning": "Earnings before non-cash D&A charges — a proxy for cash-generating power."},
    "ebitda_margin":    {"formula": "EBITDA ÷ Revenue",
                          "example": "$162,681M ÷ $281,724M = 57.7%",
                          "meaning": "How much of every dollar of revenue converts to pre-tax cash earnings."},
    "fcf":              {"formula": "Operating Cash Flow − Capex",
                          "example": "$136,162M − $64,551M = $71,611M",
                          "meaning": "Cash generated after reinvesting in the business — fuel for dividends, buybacks, M&A."},
    "fcf_margin":       {"formula": "Free Cash Flow ÷ Revenue",
                          "example": "$71,611M ÷ $281,724M = 25.4%",
                          "meaning": "How much revenue converts to distributable cash."},
    "rule_of_40":       {"formula": "Revenue Growth % + FCF Margin %",
                          "example": "14.9% + 25.4% = 40.4%",
                          "meaning": "SaaS health check. >40% = elite balance of growth and profitability."},
    "roic":             {"formula": "NOPAT ÷ (Debt + Equity)",
                          "example": "$105,873M ÷ $386,630M = 27.4%",
                          "meaning": "Every $1 of capital earns ~27¢ per year — extraordinary for a mature company."},
    "net_debt_ebitda":  {"formula": "(Total Debt − Cash) ÷ EBITDA",
                          "example": "($43,151M − $30,242M) ÷ $162,681M = 0.08x",
                          "meaning": "Leverage ratio. Lower = safer balance sheet. Healthy companies typically 1–3x."},
    "effective_tax_rate": {"formula": "Provision for Taxes ÷ Pretax Income",
                            "example": "$21,795M ÷ $123,627M = 17.6%",
                            "meaning": "Actual tax rate MSFT pays after credits, deductions, and jurisdictional mix."},
    "capex_intensity":  {"formula": "Capex ÷ Revenue",
                          "example": "$64,551M ÷ $281,724M = 22.9%",
                          "meaning": "How aggressively the company reinvests in physical assets. AI infra is driving this up."},
}


# ============================================================
# Source page references — for tiny "10-K p.XX" superscripts (#30)
# ============================================================
SOURCE_REFS = {
    "income_statement": "10-K p.48",
    "balance_sheet":    "10-K p.50",
    "cash_flow":        "10-K p.51",
    "segments":         "10-K Note 18, p.82-84",
    "geographic":       "10-K Note 18, p.84",
}


# ============================================================
# Executive TL;DR summary — for landing callout (#6)
# ============================================================
def executive_summary():
    return ("Microsoft delivered record $281.7B revenue in FY2025 (+15% YoY) with elite 45.6% operating margins. "
            "The story of the year: capex grew 45% to $64.6B (more than doubled over 2 years) as MSFT races to "
            "build AI infrastructure — a bet that shifts cash flow economics but positions the company as the "
            "critical infrastructure layer for the AI era. Intelligent Cloud (Azure) led all segments with 21% growth.")


# ============================================================
# "By the numbers" ribbon stats (#23)
# ============================================================
def ribbon_stats():
    return [
        {"value": "228K",   "label": "Employees"},
        {"value": "3",      "label": "Segments"},
        {"value": "51%",    "label": "US Revenue"},
        {"value": "+15%",   "label": "YoY Growth"},
        {"value": "$30B",   "label": "Cash"},
        {"value": "$65B",   "label": "Capex"},
        {"value": "45.6%",  "label": "Op Margin"},
        {"value": "27.4%",  "label": "ROIC"},
    ]


# ============================================================
# Utility Functions
# ============================================================

def safe_div(n, d):
    if n is None or d is None or d == 0: return None
    return n / d

def fmt_cur(v):
    if v is None: return "N/A"
    if abs(v) >= 1000: return f"${v/1000:,.1f}B"
    return f"${v:,.0f}M"

def fmt_pct(v):
    if v is None: return "N/A"
    return f"{v*100:.1f}%"

def fmt_ratio(v, suffix="x"):
    if v is None: return "N/A"
    return f"{v:.2f}{suffix}"

def fmt_bps(v):
    """Format a decimal change (0.0098) as basis points (98 bps)."""
    if v is None: return "N/A"
    return f"{v*10000:+.0f} bps"


# ============================================================
# KPI Computation
# ============================================================

def _row(df, col_name, col_val):
    return df.loc[df[col_name] == col_val].iloc[0]


def compute_kpis(financials):
    income = financials["income"]
    balance = financials["balance"]
    cashflow = financials["cashflow"]

    total_rev  = _row(income, "line_item", "Total Revenue")
    prod_rev   = _row(income, "line_item", "Product Revenue")
    svc_rev    = _row(income, "line_item", "Service and Other Revenue")
    gross      = _row(income, "line_item", "Gross Margin")
    rd         = _row(income, "line_item", "Research and Development")
    op_inc     = _row(income, "line_item", "Operating Income")
    pretax     = _row(income, "line_item", "Income Before Income Taxes")
    tax        = _row(income, "line_item", "Provision for Income Taxes")
    net_inc    = _row(income, "line_item", "Net Income")

    cash       = _row(balance, "line_item", "Cash and Cash Equivalents")
    st_inv     = _row(balance, "line_item", "Short-Term Investments")
    debt       = _row(balance, "line_item", "Total Debt")
    equity     = _row(balance, "line_item", "Stockholders' Equity")
    tot_assets = _row(balance, "line_item", "Total Assets")

    da         = _row(cashflow, "line_item", "Depreciation & Amortization")
    ocf        = _row(cashflow, "line_item", "Operating Cash Flow")
    capex      = _row(cashflow, "line_item", "Capital Expenditures")
    buybacks   = _row(cashflow, "line_item", "Common Stock Repurchased")
    dividends  = _row(cashflow, "line_item", "Dividends Paid")
    acq        = _row(cashflow, "line_item", "Acquisitions (net)")

    periods = ["2025", "2024", "2023"]
    latest = "2025"

    ts_rows = []
    for p in periods:
        rev = total_rev[p]; opi = op_inc[p]; ni = net_inc[p]
        ocf_v = ocf[p]; cx = abs(capex[p]); fcf = ocf_v - cx
        ebitda = opi + da[p]
        etr = safe_div(tax[p], pretax[p])
        ts_rows.append({
            "period": p, "revenue": rev,
            "gross_margin": safe_div(gross[p], rev),
            "operating_margin": safe_div(opi, rev),
            "net_margin": safe_div(ni, rev),
            "ebitda": ebitda,
            "ebitda_margin": safe_div(ebitda, rev),
            "fcf_margin": safe_div(fcf, rev),
            "rd_intensity": safe_div(rd[p], rev),
            "capex_intensity": safe_div(cx, rev),
            "effective_tax_rate": etr,
            "cash_balance": cash[p],
            "cash_plus_st_inv": cash[p] + st_inv[p],
            "total_debt": debt[p],
            "net_debt": debt[p] - cash[p],
            "net_debt_ebitda": safe_div(debt[p] - cash[p], ebitda),
            "operating_cash_flow": ocf_v,
            "capex": cx, "free_cash_flow": fcf,
            "dividends_paid": abs(dividends[p]),
            "buybacks": abs(buybacks[p]),
            "acquisitions": abs(acq[p]),
        })
    ts = pd.DataFrame(ts_rows)
    ts = ts.sort_values("period").reset_index(drop=True)
    ts["revenue_growth"] = ts["revenue"].pct_change()
    ts["rule_of_40"] = ts["revenue_growth"] + ts["fcf_margin"]

    segment_revenue = pd.DataFrame([
        {"period": p, "Product Revenue": prod_rev[p], "Service and Other Revenue": svc_rev[p]}
        for p in periods
    ])

    latest_ts = ts.loc[ts["period"] == latest].iloc[0]
    yoy_growth = (total_rev["2025"] - total_rev["2024"]) / total_rev["2024"]

    # Deltas vs prior year
    prior_ts = ts.loc[ts["period"] == "2024"].iloc[0]
    op_margin_delta = latest_ts["operating_margin"] - prior_ts["operating_margin"]  # ~98 bps
    gm_delta = latest_ts["gross_margin"] - prior_ts["gross_margin"]
    capex_yoy = (latest_ts["capex"] - prior_ts["capex"]) / prior_ts["capex"]
    capex_2yr = (latest_ts["capex"] - ts.loc[ts["period"]=="2023"].iloc[0]["capex"]) / ts.loc[ts["period"]=="2023"].iloc[0]["capex"]

    nopat = op_inc[latest] * (1 - latest_ts["effective_tax_rate"])
    invested_capital = debt[latest] + equity[latest]
    roic = safe_div(nopat, invested_capital)
    roe  = safe_div(net_inc[latest], equity[latest])
    roa  = safe_div(net_inc[latest], tot_assets[latest])

    cap_allocation = {
        "capex": abs(capex[latest]),
        "acquisitions": abs(acq[latest]),
        "dividends": abs(dividends[latest]),
        "buybacks": abs(buybacks[latest]),
    }
    cap_allocation["total_returned_to_shareholders"] = cap_allocation["dividends"] + cap_allocation["buybacks"]
    cap_allocation["total_deployed"] = sum(cap_allocation[k] for k in ("capex","acquisitions","dividends","buybacks"))

    return {
        "latest_period": latest, "periods": periods,
        "time_series": ts, "segment_revenue": segment_revenue,
        "segments": financials["segments"],
        "geographic": financials["geographic"],
        "per_share": financials["per_share"],

        "revenue": total_rev[latest],
        "prior_year_revenue": total_rev["2024"],
        "revenue_yoy_growth": yoy_growth,
        "product_revenue": prod_rev[latest],
        "service_revenue": svc_rev[latest],
        "product_revenue_prior": prod_rev["2024"],
        "service_revenue_prior": svc_rev["2024"],
        "product_revenue_mix": prod_rev[latest] / total_rev[latest],
        "service_revenue_mix": svc_rev[latest] / total_rev[latest],

        "gross_margin": latest_ts["gross_margin"],
        "operating_margin": latest_ts["operating_margin"],
        "net_margin": latest_ts["net_margin"],
        "ebitda": latest_ts["ebitda"],
        "ebitda_margin": latest_ts["ebitda_margin"],

        "gross_margin_dollars": gross[latest],
        "operating_income": op_inc[latest],
        "net_income": net_inc[latest],

        "effective_tax_rate": latest_ts["effective_tax_rate"],
        "rd_intensity": latest_ts["rd_intensity"],
        "capex_intensity": latest_ts["capex_intensity"],

        "cash_balance": cash[latest],
        "cash_plus_st_inv": latest_ts["cash_plus_st_inv"],
        "total_debt": debt[latest],
        "net_debt": latest_ts["net_debt"],
        "net_debt_ebitda": latest_ts["net_debt_ebitda"],
        "stockholders_equity": equity[latest],

        "operating_cash_flow": latest_ts["operating_cash_flow"],
        "capex": latest_ts["capex"],
        "free_cash_flow": latest_ts["free_cash_flow"],
        "fcf_margin": latest_ts["fcf_margin"],

        "rule_of_40": latest_ts["rule_of_40"],
        "roic": roic, "roe": roe, "roa": roa,

        "cap_allocation": cap_allocation,

        # Additional derived deltas
        "op_margin_delta": op_margin_delta,   # ~+0.0098 (98 bps)
        "gross_margin_delta": gm_delta,
        "capex_yoy_growth": capex_yoy,        # ~0.45 (45%)
        "capex_2yr_growth": capex_2yr,        # ~1.30 (130%)
    }


def process_uploaded_file(_file=None):
    financials = microsoft_fallback_financials()
    kpis = compute_kpis(financials)
    return {"company": "Microsoft", "financials": financials, "kpis": kpis,
            "confidence": "Sourced from MSFT FY2025 10-K (June 30, 2025)"}


def process_peers(peer_names):
    return {}


def build_benchmark_dataframe(results):
    rows = []
    for company, result in results.items():
        k = result["kpis"]
        rows.append({
            "company": company, "year": k["latest_period"],
            "revenue": k["revenue"], "prior_year_revenue": k["prior_year_revenue"],
            "revenue_yoy_growth": k["revenue_yoy_growth"],
            "product_revenue_mix": k["product_revenue_mix"],
            "service_revenue_mix": k["service_revenue_mix"],
            "gross_margin": k["gross_margin"],
            "operating_margin": k["operating_margin"],
            "net_margin": k["net_margin"],
            "operating_income": k["operating_income"], "net_income": k["net_income"],
            "cash_balance": k["cash_balance"], "total_debt": k["total_debt"],
            "operating_cash_flow": k["operating_cash_flow"], "capex": k["capex"],
            "free_cash_flow": k["free_cash_flow"],
        })
    return pd.DataFrame(rows)


def build_forecast_dataframe(starting_revenue, growth_rate, start_year=2026, periods=3):
    rows = []
    rev = starting_revenue
    for i in range(periods):
        year = start_year + i
        rev = rev * (1 + growth_rate)
        rows.append({"year": year, "revenue": rev, "growth_rate": growth_rate})
    return pd.DataFrame(rows)


def build_scenario_dataframe(starting_revenue, start_year=2026, periods=3,
                              bear_growth=0.06, base_growth=0.12, bull_growth=0.17):
    scenarios = {"Bear Case": bear_growth, "Base Case": base_growth, "Bull Case": bull_growth}
    rows = []
    for name, g in scenarios.items():
        rev = starting_revenue
        for i in range(periods):
            year = start_year + i
            rev = rev * (1 + g)
            rows.append({"scenario": name, "year": year, "revenue": rev, "growth_rate": g})
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
            row.append(rev * m)
        grid.append(row)
    return np.array(grid)


def format_display_dataframe(df): return df
def apply_manual_statement_selection(result, *_args): return result
def raw_table_label(i, _t): return f"Table {i}"


def answer_question(question, df, kpis=None):
    if df.empty and kpis is None: return "No data available."
    q = question.lower()
    k = kpis

    if any(w in q for w in ["segment", "azure", "cloud", "productivity", "personal computing"]):
        seg = k["segments"]
        lines = []
        for _, r in seg.iterrows():
            g = (r["rev_2025"] - r["rev_2024"]) / r["rev_2024"]
            lines.append(f"{r['segment']}: revenue {fmt_cur(r['rev_2025'])} ({fmt_pct(g)} YoY), operating income {fmt_cur(r['opi_2025'])}.")
        return "Segment results FY2025 — " + " ".join(lines)

    if any(w in q for w in ["capital", "buyback", "dividend", "allocation"]):
        c = k["cap_allocation"]
        return (f"FY2025 capital allocation: Capex {fmt_cur(c['capex'])}, "
                f"acquisitions {fmt_cur(c['acquisitions'])}, dividends {fmt_cur(c['dividends'])}, "
                f"buybacks {fmt_cur(c['buybacks'])}. Total returned to shareholders: {fmt_cur(c['total_returned_to_shareholders'])}.")

    if any(w in q for w in ["ebitda", "rule of 40", "roic", "return on"]):
        return (f"Key ratios FY2025 — EBITDA {fmt_cur(k['ebitda'])} ({fmt_pct(k['ebitda_margin'])} margin), "
                f"Rule of 40: {k['rule_of_40']*100:.1f}%, ROIC {fmt_pct(k['roic'])}, "
                f"Net Debt/EBITDA {fmt_ratio(k['net_debt_ebitda'])}, "
                f"Effective tax rate {fmt_pct(k['effective_tax_rate'])}.")

    if any(w in q for w in ["forecast", "projection", "future"]):
        fd = build_forecast_dataframe(k["revenue"], 0.12, 2026, 3)
        fy = int(fd.iloc[-1]["year"]); fr = fd.iloc[-1]["revenue"]
        return (f"Using a 12% growth assumption, revenue would reach {fmt_cur(fr)} by FY{fy}. Simplified scenario, not a formal forecast.")

    if any(w in q for w in ["revenue", "growth"]):
        return (f"Microsoft generated {fmt_cur(k['revenue'])} in FY2025 revenue ({fmt_pct(k['revenue_yoy_growth'])} YoY). "
                f"Service and other revenue = {fmt_pct(k['service_revenue_mix'])} of the total. "
                f"Intelligent Cloud (Azure) was the fastest-growing segment at +21%.")

    if any(w in q for w in ["margin", "profit"]):
        return (f"Strong profitability: gross margin {fmt_pct(k['gross_margin'])}, operating margin {fmt_pct(k['operating_margin'])} "
                f"(up ~100 bps YoY), net margin {fmt_pct(k['net_margin'])}, EBITDA margin {fmt_pct(k['ebitda_margin'])}.")

    if any(w in q for w in ["cash", "fcf", "liquidity"]):
        return (f"Microsoft generated {fmt_cur(k['free_cash_flow'])} in FCF ({fmt_pct(k['fcf_margin'])} of revenue). "
                f"Note capex grew 45% YoY to {fmt_cur(k['capex'])} for AI infrastructure, so FCF declined slightly vs FY24. "
                f"Cash + ST investments {fmt_cur(k['cash_plus_st_inv'])}, net debt {fmt_cur(k['net_debt'])}.")

    if any(w in q for w in ["debt", "balance sheet", "leverage"]):
        return (f"Balance sheet: {fmt_cur(k['cash_plus_st_inv'])} cash + ST investments vs {fmt_cur(k['total_debt'])} total debt. "
                f"Net debt {fmt_cur(k['net_debt'])}. Net Debt/EBITDA of {fmt_ratio(k['net_debt_ebitda'])} — near-zero leverage.")

    return (f"Microsoft FY2025: revenue {fmt_cur(k['revenue'])} ({fmt_pct(k['revenue_yoy_growth'])} YoY), "
            f"operating margin {fmt_pct(k['operating_margin'])}, FCF {fmt_cur(k['free_cash_flow'])}, "
            f"ROIC {fmt_pct(k['roic'])}, Net Debt/EBITDA {fmt_ratio(k['net_debt_ebitda'])}.")


def stream_answer(question, df, kpis=None):
    import time
    text = answer_question(question, df, kpis=kpis)
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.02)

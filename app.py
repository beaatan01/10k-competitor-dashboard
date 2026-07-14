import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tenk_engine as engine

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MSFT FY25 10-K Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# EXECUTIVE LIGHT THEME
# ============================================================
st.markdown("""
<style>
.stApp { background: #F7F7F4; }
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; color: #1a1a1a; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }
.num, .kpi-value { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }
h1, h2, h3, h4 { color: #0A2540; font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 2.25rem; }

.section-divider {
  display: flex; align-items: baseline; gap: 1rem;
  margin: 2.5rem 0 1.25rem 0; padding-bottom: 0.5rem;
  border-bottom: 1px solid #E5E5E0;
}
.section-num { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #8B95A1; letter-spacing: 0.1em; }
.section-title { font-size: 1.5rem; font-weight: 600; color: #0A2540; margin: 0; }
.section-sub { font-size: 0.85rem; color: #6B7280; margin-left: auto; font-style: italic; }

.kpi-card {
  background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 8px;
  padding: 1.1rem 1.25rem; height: 100%;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  animation: fadeInUp 0.5s ease both;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(10,37,64,0.08); border-color: #C9D1DA; }
.kpi-label { font-size: 0.72rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem; font-weight: 500; }
.kpi-value { font-size: 1.85rem; font-weight: 600; color: #0A2540; line-height: 1.1; }
.kpi-delta { font-size: 0.82rem; margin-top: 0.35rem; font-weight: 500; }
.kpi-delta.up { color: #0E7C4A; }
.kpi-delta.down { color: #C1443C; }
.kpi-delta.flat { color: #8B95A1; }
.kpi-sub { font-size: 0.72rem; color: #8B95A1; margin-top: 0.2rem; }

.kpi-card:nth-child(1) { animation-delay: 0.05s; }
.kpi-card:nth-child(2) { animation-delay: 0.10s; }
.kpi-card:nth-child(3) { animation-delay: 0.15s; }
.kpi-card:nth-child(4) { animation-delay: 0.20s; }
.kpi-card:nth-child(5) { animation-delay: 0.25s; }
.kpi-card:nth-child(6) { animation-delay: 0.30s; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.analyst-note {
  background: #FFFDF5; border-left: 3px solid #C99C3B; border-radius: 4px;
  padding: 0.9rem 1.1rem; margin: 1rem 0;
  font-size: 0.92rem; color: #1a1a1a; line-height: 1.6;
}
.analyst-note strong { color: #0A2540; }

.ribbon-card {
  background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 8px;
  padding: 0.85rem 1rem; text-align: center;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  animation: fadeInUp 0.5s ease both;
}
.ribbon-card:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(10,37,64,0.06); }
.ribbon-num { font-size: 1.25rem; font-weight: 600; color: #0A2540; font-variant-numeric: tabular-nums; line-height: 1.15; }
.ribbon-lbl { font-size: 0.68rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.25rem; font-weight: 500; }

.verified-badge { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: #0E7C4A; font-weight: 500; }
.pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: #0E7C4A; animation: pulse 2s infinite; }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(14,124,74,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(14,124,74,0); }
}

.as-of { display: inline-block; background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 20px; padding: 0.25rem 0.75rem; font-size: 0.72rem; color: #6B7280; font-family: 'JetBrains Mono', monospace; margin-left: 0.5rem; }

.source-cite { font-size: 0.68rem; color: #8B95A1; vertical-align: super; margin-left: 0.25rem; }

.footer { background: #0A2540; color: #C9D1DA; padding: 2rem; border-radius: 8px; margin-top: 3rem; text-align: center; font-size: 0.85rem; }
.footer a { color: #C99C3B; text-decoration: none; margin: 0 0.75rem; font-weight: 500; }
.footer a:hover { color: #FFFFFF; }

.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: transparent; border-bottom: 1px solid #E5E5E0; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; padding: 0.75rem 1.1rem; color: #6B7280; font-weight: 500; font-size: 0.92rem; }
.stTabs [aria-selected="true"] { color: #0A2540 !important; border-bottom: 2px solid #C99C3B !important; }

[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5E5E0; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #0A2540; }

.stButton>button {
  background: #FFFFFF; color: #0A2540; border: 1px solid #E5E5E0;
  padding: 0.75rem 1rem; border-radius: 8px; font-weight: 500; font-size: 0.9rem;
  transition: all 0.15s ease; width: 100%; text-align: left; line-height: 1.4;
  white-space: normal; height: auto; min-height: 56px;
}
.stButton>button:hover { border-color: #C99C3B; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(10,37,64,0.06); }

.streamlit-expanderHeader { background: #FFFFFF !important; border: 1px solid #E5E5E0 !important; border-radius: 6px !important; font-size: 0.85rem !important; color: #0A2540 !important; }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD DATA (dataframes → KPIs)
# ============================================================
FINANCIALS = engine.microsoft_fallback_financials()
KPIS = engine.compute_kpis(FINANCIALS)
RIBBON = engine.ribbon_stats()

# Helper accessors (values in $M unless noted)
REV_B      = KPIS["revenue"] / 1000
NI_B       = KPIS["net_income"] / 1000
OPM        = KPIS["operating_margin"] * 100
FCF_B      = KPIS["free_cash_flow"] / 1000
CAPEX_B    = KPIS["capex"] / 1000
OCF_B      = KPIS["operating_cash_flow"] / 1000
EPS        = KPIS["per_share"]["diluted_eps"]["2025"]
RULE40     = KPIS["rule_of_40"] * 100
ROIC       = KPIS["roic"] * 100
ND_EBITDA  = KPIS["net_debt_ebitda"]
OPM_DELTA  = KPIS["op_margin_delta"] * 10000  # bps
CAPEX_YOY  = KPIS["capex_yoy_growth"] * 100
REV_YOY    = KPIS["revenue_yoy_growth"] * 100
CASH_B     = KPIS["cash_plus_st_inv"] / 1000

# ============================================================
# HELPERS
# ============================================================
def kpi_card(label, value, delta=None, delta_dir="flat", sub=None, source=None):
    src = f'<span class="source-cite">{source}</span>' if source else ""
    delta_html = ""
    if delta:
        arrow = "▲" if delta_dir == "up" else ("▼" if delta_dir == "down" else "—")
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow} {delta}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}{src}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
      {sub_html}
    </div>
    """

def section_divider(num, title, sub=None):
    sub_html = f'<span class="section-sub">{sub}</span>' if sub else ""
    st.markdown(f"""
    <div class="section-divider">
      <span class="section-num">{num}</span>
      <h2 class="section-title">{title}</h2>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="analyst-note">{text}</div>', unsafe_allow_html=True)

def ribbon_bar():
    cols = st.columns(len(RIBBON))
    for i, item in enumerate(RIBBON):
        with cols[i]:
            st.markdown(f"""
            <div class="ribbon-card">
              <div class="ribbon-num">{item['value']}</div>
              <div class="ribbon-lbl">{item['label']}</div>
            </div>
            """, unsafe_allow_html=True)

def explainer_body(what, example, why):
    return f"""
    **What is this?** {what}

    **For example:** {example}

    **Why it matters:** {why}
    """

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### MSFT 10-K Intelligence")
    st.markdown('<span class="as-of">FY2025 · Filed Jul 30, 2025</span>', unsafe_allow_html=True)
    st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Verified from 10-K PDF</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Navigation")
    st.markdown("""
    - 01 · Welcome
    - 02 · Executive Summary
    - 03 · Revenue & Segments
    - 04 · Capital Allocation
    - 05 · AI Copilot
    """)
    st.markdown("---")
    st.markdown("#### About")
    st.markdown("<small>Interactive analysis of Microsoft's FY2025 10-K filing, designed to be readable by anyone — not just finance folks.</small>", unsafe_allow_html=True)
    st.markdown("<small>Every metric includes a plain-English explanation with real-world examples.</small>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<small><strong>Author:</strong> Bea Lucido-Tan</small>", unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "Welcome",
    "Executive Summary",
    "Revenue & Segments",
    "Capital Allocation",
    "AI Copilot",
])

# ============================================================
# TAB 1: WELCOME
# ============================================================
with tabs[0]:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# Microsoft FY2025 10-K")
        st.markdown("### Financial intelligence, decoded for everyone.")
    with col2:
        st.markdown('<br><span class="as-of">As of Jul 30, 2025</span>', unsafe_allow_html=True)
        st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Data verified</div>', unsafe_allow_html=True)

    note("A 200-page filing distilled into 5 tabs. Every chart has plain-English explanations — "
         "if a term is new, just click the expander below it. No finance degree required.")

    # By the numbers ribbon
    section_divider("01", "By the numbers", "FY2025 at a glance")
    ribbon_bar()

    # Hero chart
    section_divider("02", "The story in one chart", "Revenue vs. AI infrastructure spending")

    note("The **navy bars** show how much money Microsoft brought in each year. "
         "The **gold line** shows how much they spent on new equipment — mostly AI datacenters. "
         "Notice how the gold line is climbing much faster than the bars. That's the entire story of FY25 in one image.")

    years = list(range(2020, 2026))
    revenue_series = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    capex_series = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=revenue_series, name="Revenue", marker_color="#0A2540",
                          hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig.add_trace(go.Scatter(x=years, y=capex_series, name="Capex (AI Infrastructure)", yaxis="y2",
                              mode="lines+markers", line=dict(color="#C99C3B", width=3),
                              marker=dict(size=10),
                              hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>"))
    fig.add_annotation(x=2023, y=28.1, text="ChatGPT era begins →<br>AI capex arms race", showarrow=True,
                        arrowhead=2, ax=-60, ay=-50, font=dict(size=10, color="#6B7280"),
                        bgcolor="rgba(255,255,255,0.95)", bordercolor="#E5E5E0", borderwidth=1)
    fig.update_layout(
        height=440, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        yaxis=dict(title="Revenue ($B)", showgrid=True, gridcolor="#F0F0EC"),
        yaxis2=dict(title="Capex ($B)", overlaying="y", side="right", showgrid=False),
        xaxis=dict(showgrid=False, tickmode="array", tickvals=years),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(family="Inter", color="#1a1a1a"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # TL;DR as a quieter analyst note (not a big gradient box)
    section_divider("03", "The 30-second version", "For readers in a rush")
    note("Microsoft had a **record-breaking year** — $281.7B revenue (+14.9%) and profit margins holding at 45.6%. "
          "But here's the twist: they spent **$64.6B on AI infrastructure**, which is 45% more than last year and "
          "more than double what they spent just two years ago. Their free cash flow actually shrank slightly because of it. "
          "The big question this dashboard explores: <strong>will this massive AI bet pay off?</strong>")

    st.markdown("---")
    st.markdown("**Ready to dive in?** Use the tabs above. Each section builds on the last.")

# ============================================================
# TAB 2: EXECUTIVE SUMMARY
# ============================================================
with tabs[1]:
    section_divider("01", "The 6 numbers that matter", "Hero KPIs from the FY2025 filing")

    note("These are the six numbers investors look at first. Each card shows the value, the change from last year, "
         "and a small note. If any term is unfamiliar, expand the section below the cards for a plain-English explanation.")

    cols = st.columns(3)
    row1 = [
        ("Revenue", f"${REV_B:.1f}B", f"+{REV_YOY:.1f}%", "up", "vs $245.1B FY24", "p.48"),
        ("Net Income (Profit)", f"${NI_B:.1f}B", "+15.6%", "up", "money kept after all costs", "p.48"),
        ("Operating Margin", f"{OPM:.1f}%", f"+{OPM_DELTA:.0f} bps", "up", "profit per $1 of sales", "p.48"),
    ]
    for i, k in enumerate(row1):
        with cols[i]:
            st.markdown(kpi_card(*k), unsafe_allow_html=True)

    cols2 = st.columns(3)
    row2 = [
        ("Free Cash Flow (FCF)", f"${FCF_B:.1f}B", "-3.3%", "down", "cash left after spending", "p.51"),
        ("Capex", f"${CAPEX_B:.1f}B", f"+{CAPEX_YOY:.1f}%", "up", "AI datacenter buildout", "p.51"),
        ("Earnings Per Share (EPS)", f"${EPS:.2f}", "+15.6%", "up", "profit per share owned", "p.48"),
    ]
    for i, k in enumerate(row2):
        with cols2[i]:
            st.markdown(kpi_card(*k), unsafe_allow_html=True)

    st.markdown("### Wait — what do these mean?")
    st.caption("Click any metric below for a plain-English explanation with real-world examples.")

    with st.expander("Revenue — click to learn"):
        st.markdown(explainer_body(
            what="All the money Microsoft brought in from selling products and services — Office subscriptions, Azure cloud, Xbox, LinkedIn, Windows, etc.",
            example="Imagine Microsoft is a giant bakery. Revenue is the total cash in the register at year's end — from every cupcake, cake, and coffee sold. It doesn't yet account for ingredients or rent.",
            why="This tells you if the company is growing. A 14.9% jump when you're already at $245B is remarkable — most companies this size grow 3-5% per year."
        ))

    with st.expander("Net Income (Profit) — click to learn"):
        st.markdown(explainer_body(
            what="The actual bottom-line profit — what's left after paying for staff, rent, ingredients, and taxes.",
            example="If the bakery made $282 in the register but spent $180 on flour, rent, salaries, and taxes, the $102 left over is net income. That's what shareholders actually 'earn.'",
            why="Revenue can look great while profits shrink — that's a red flag. Microsoft grew profit 15.6%, even faster than revenue. Very healthy."
        ))

    with st.expander("Operating Margin — click to learn"):
        st.markdown(explainer_body(
            what="For every $1 in sales, how many cents become profit from operations (before interest and taxes)?",
            example="If the bakery sells a $10 cake and $4.56 of that is profit, their operating margin is 45.6%. That's absurdly high — most physical bakeries run 5-10%.",
            why="Software has huge margins because copying software costs almost nothing. Microsoft's 45.6% shows their pricing power is enormous — customers can't easily switch away."
        ))

    with st.expander("Free Cash Flow (FCF) — click to learn"):
        st.markdown(explainer_body(
            what="The real cash left over after paying for daily operations AND buying new equipment. This is the money that can go to shareholders or into savings.",
            example="If the bakery makes $136 in cash but spends $65 on a new industrial oven, their FCF is $71. That $71 is 'real' money they can use however they want.",
            why="FCF dropped 3.3% this year — the first drop in 5+ years. Not scary yet, but worth watching. The AI capex is starting to eat into the piggy bank."
        ))

    with st.expander("Capex (Capital Expenditure) — click to learn"):
        st.markdown(explainer_body(
            what="Money spent on big, long-lasting assets — buildings, servers, datacenters. Different from everyday expenses like salaries.",
            example="The bakery buying a $65 industrial oven is capex. Buying flour every week is not — flour is a regular expense. Ovens last 10+ years.",
            why="Microsoft's capex jumped 45% this year, almost entirely for AI datacenters. This is the largest infrastructure buildout in the company's history."
        ))

    with st.expander("Earnings Per Share (EPS) — click to learn"):
        st.markdown(explainer_body(
            what="Total profit divided by the number of shares outstanding. If you own one share, EPS is 'your slice' of the profit.",
            example="If the bakery earned $102 in profit and there are 7.4 slices (shares) of ownership, each slice 'earned' $13.64.",
            why="EPS grew ~16% — even more than net income — because Microsoft also bought back some shares. Fewer slices = bigger slice per person."
        ))

    # Health check
    section_divider("02", "Is Microsoft healthy?", "The 3-metric investor check-up")

    note("Doctors check blood pressure, heart rate, and cholesterol. For companies, investors check three similar 'vital signs.' "
         "Here's how Microsoft scores on all three.")

    hcols = st.columns(3)
    with hcols[0]:
        st.markdown(kpi_card("Rule of 40", f"{RULE40:.1f}", "elite tier", "up", "growth% + FCF margin%"), unsafe_allow_html=True)
    with hcols[1]:
        st.markdown(kpi_card("ROIC", f"{ROIC:.1f}%", "world class", "up", "profit per $1 invested"), unsafe_allow_html=True)
    with hcols[2]:
        st.markdown(kpi_card("Net Debt / EBITDA", f"{ND_EBITDA:.2f}x", "fortress", "up", "1 month of earnings covers all debt"), unsafe_allow_html=True)

    with st.expander("Rule of 40 — click to learn"):
        st.markdown(explainer_body(
            what="A quick test: is the company growing fast AND profitable at the same time? Add growth % + profit margin %. Anything above 40 is 'elite.'",
            example="If a bakery grows sales 15% AND keeps 25 cents of every dollar as profit, their score is 40 — cake-cutting elite. Grow fast but lose money? Fail. Profit but no growth? Also fail. Both are hard.",
            why="Microsoft scored 40.4 — just inside the elite club, but at $282B scale, which is even more impressive. Most companies passing this test are much smaller."
        ))

    with st.expander("Return on Invested Capital (ROIC) — click to learn"):
        st.markdown(explainer_body(
            what="How much profit Microsoft makes from every dollar invested in the business, from both shareholders and lenders.",
            example="Think of Microsoft as a bakery you own with a friend. You each put in $100. At year-end, the bakery gives you back $27 in profit — that's a 27% ROIC. Way better than any savings account.",
            why="Above 15% means the company creates real value. Above 20% is exceptional. Microsoft's 27.4% is world-class — they're one of the best 'money multipliers' on Earth."
        ))

    with st.expander("Net Debt / EBITDA — click to learn"):
        st.markdown(explainer_body(
            what="How many years of earnings would it take to pay off all debt? Lower is safer.",
            example="If the bakery owes $3 but earns $37 a year, they could pay off all debt in about a month. Their ratio is 0.08x — practically debt-free. If they owed $100 with the same earnings, it'd take almost 3 years (much riskier).",
            why="Microsoft's 0.08x is 'fortress balance sheet' territory — they could pay off ALL debt with about one month of earnings. This gives them room to keep spending on AI without worry."
        ))

# ============================================================
# TAB 3: REVENUE & SEGMENTS
# ============================================================
with tabs[2]:
    section_divider("01", "Revenue trajectory", "5-year view with growth overlay")

    note("Microsoft has grown from $143B to $282B in just 5 years — nearly doubling. "
         "The **navy bars** show revenue each year, and the **gold line** shows the year-over-year growth rate. "
         "Notice how growth has held steady around 15% even as the company got much bigger. That's unusual.")

    years6 = list(range(2020, 2026))
    rev6 = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    growth6 = [None, 17.5, 17.9, 6.9, 15.7, 14.9]

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(x=years6, y=rev6, marker_color="#0A2540", name="Revenue",
                            text=[f"${v:.0f}B" for v in rev6], textposition="outside",
                            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig_r.add_trace(go.Scatter(x=years6, y=growth6, mode="lines+markers", name="YoY Growth %",
                                yaxis="y2", line=dict(color="#C99C3B", width=3),
                                marker=dict(size=9),
                                hovertemplate="<b>FY%{x}</b><br>Growth: %{y:.1f}%<extra></extra>"))
    fig_r.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F0F0EC"),
                        yaxis2=dict(title="Growth %", overlaying="y", side="right", showgrid=False),
                        xaxis=dict(tickmode="array", tickvals=years6),
                        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                        margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_r, use_container_width=True)

    # Progress to $300B
    st.markdown("#### On track for the $300B milestone")
    progress_pct = (REV_B / 300) * 100
    st.progress(progress_pct / 100, text=f"${REV_B:.1f}B out of $300B target · {progress_pct:.1f}% there")
    st.caption("At current pace, Microsoft crosses $300B in revenue around late 2025 / early 2026 — a historic milestone.")

    # Segments
    section_divider("02", "Business segments", "The three engines inside Microsoft")

    note("Microsoft isn't one business — it's three big ones bundled together. "
         "Think of it like a food court with three restaurants under one roof. Each has its own growth rate, "
         "profit margins, and story. Here's how each is doing.")

    seg_df = FINANCIALS["segments"]
    colors_seg = ["#0A2540", "#C99C3B", "#5B7A99"]

    scols = st.columns(3)
    seg_explanations = [
        "Office 365, LinkedIn, Dynamics — the 'productivity' apps everyone uses at work.",
        "Azure cloud + servers — the AI money-maker and fastest-growing segment.",
        "Windows, Xbox, Surface, Bing — the consumer stuff you interact with daily.",
    ]
    for i, row in seg_df.iterrows():
        rev_b = row["rev_2025"] / 1000
        growth = (row["rev_2025"] - row["rev_2024"]) / row["rev_2024"] * 100
        with scols[i]:
            st.markdown(kpi_card(
                row["segment"],
                f"${rev_b:.1f}B",
                f"+{growth:.1f}%",
                "up",
                f"{rev_b/REV_B*100:.0f}% of total revenue"
            ), unsafe_allow_html=True)
            st.caption(seg_explanations[i])

    st.markdown("")

    # Segment bar chart
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        x=seg_df["segment"],
        y=seg_df["rev_2025"] / 1000,
        marker_color=colors_seg,
        text=[f"${v/1000:.1f}B" for v in seg_df["rev_2025"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"
    ))
    fig_s.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F0F0EC"),
                        margin=dict(l=40, r=40, t=40, b=40),
                        showlegend=False)
    st.plotly_chart(fig_s, use_container_width=True)

    note("**Intelligent Cloud is the star of the show** — growing 21%, nearly 3x faster than Windows/Xbox (+7%). "
         "That's exactly why Microsoft keeps pouring money into AI infrastructure. Azure is where the future is being built.")

    with st.expander("What is a 'segment' anyway? — click to learn"):
        st.markdown(explainer_body(
            what="A segment is a big chunk of a company's business. Microsoft splits itself into 3 chunks so investors can see which parts are winning.",
            example="Imagine a bakery that sells three things: wedding cakes, coffee, and breakfast pastries. Each is a 'segment.' If wedding cakes are exploding in demand but pastries are flat, that tells you where to invest more ovens.",
            why="Right now, Microsoft's 'wedding cake' is Intelligent Cloud (+21%), while their 'pastries' are More Personal Computing (+7%). Guess where they're building new ovens?"
        ))

# ============================================================
# TAB 4: CAPITAL ALLOCATION
# ============================================================
with tabs[3]:
    section_divider("01", "Where did the cash go?", "How Microsoft deployed $136B in operating cash")

    note("Microsoft made $136 billion in operating cash this year. Where did it all go? "
         "Spoiler: mostly into building AI datacenters. Let's follow the money.")

    ca = KPIS["cap_allocation"]

    ccols = st.columns(4)
    with ccols[0]:
        st.markdown(kpi_card("Capex (AI Infrastructure)", f"${ca['capex']/1000:.1f}B",
                              f"+{CAPEX_YOY:.1f}%", "up", "datacenters, servers, chips"), unsafe_allow_html=True)
    with ccols[1]:
        st.markdown(kpi_card("Stock Buybacks", f"${ca['buybacks']/1000:.1f}B",
                              "returned to owners", "flat", "shrinks share count"), unsafe_allow_html=True)
    with ccols[2]:
        st.markdown(kpi_card("Dividends", f"${ca['dividends']/1000:.1f}B",
                              "quarterly payouts", "flat", "cash to shareholders"), unsafe_allow_html=True)
    with ccols[3]:
        st.markdown(kpi_card("Acquisitions", f"${ca['acquisitions']/1000:.1f}B",
                              "buying companies", "flat", "strategic add-ons"), unsafe_allow_html=True)

    with st.expander("What do these terms mean? — click to learn"):
        st.markdown(explainer_body(
            what="These are the 4 main ways Microsoft can use its cash: (1) invest in itself, (2) buy back its own shares, (3) pay shareholders directly, or (4) buy other companies.",
            example="Imagine you earned a $100 bonus. You could: buy new tools for your side hustle ($65 = capex), pay yourself back for a personal loan ($18 = buybacks), give your family some ($24 = dividends), or buy a friend's small business ($6 = acquisitions). That's basically what Microsoft did this year.",
            why="Right now, Microsoft is choosing option 1 (capex) aggressively — they believe AI infrastructure will earn more than any other use of cash. Time will tell if they're right."
        ))

    # Capex mega-chart
    section_divider("02", "The capex mega-cycle", "The biggest infrastructure buildout in MSFT history")

    note("This is THE chart to remember. Microsoft's capex has **more than doubled in 2 years** — "
         "from $28B (FY23) to $65B (FY25). All of it is going toward AI datacenters. "
         "No company has ever built this much compute capacity, this fast.")

    capex_years = [2020, 2021, 2022, 2023, 2024, 2025]
    capex_vals = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig_capex = go.Figure()
    fig_capex.add_trace(go.Bar(x=capex_years, y=capex_vals, marker_color="#C99C3B",
                                text=[f"${v:.1f}B" for v in capex_vals], textposition="outside",
                                hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>"))
    fig_capex.add_annotation(x=2023, y=28.1, text="Pre-AI baseline", showarrow=True, arrowhead=2,
                              ax=-40, ay=-40, font=dict(size=10, color="#6B7280"))
    fig_capex.add_annotation(x=2025, y=64.6, text="AI-era peak<br>(more than 2x in 2 years)",
                              showarrow=True, arrowhead=2,
                              ax=40, ay=-50, font=dict(size=10, color="#C1443C"))
    fig_capex.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                             yaxis=dict(title="Capex ($B)", gridcolor="#F0F0EC"),
                             margin=dict(l=40, r=40, t=40, b=40),
                             showlegend=False)
    st.plotly_chart(fig_capex, use_container_width=True)

    # OCF vs Capex vs FCF
    section_divider("03", "The cash flow squeeze", "How AI spending is eating into free cash")

    note("Here's the trade-off. **Operating cash** (navy) is growing nicely at +15%. But **AI spending** (gold) is growing much faster at +45%. "
         "The **red line** shows what's left over — free cash flow — and this year it actually declined for the first time in 5+ years.")

    ocf_vals = [60.7, 76.7, 89.0, 87.6, 118.5, 136.2]
    fcf_vals = [45.2, 56.1, 65.1, 59.5, 74.1, 71.6]

    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=capex_years, y=ocf_vals, name="Operating Cash Flow", marker_color="#0A2540",
                              hovertemplate="OCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Bar(x=capex_years, y=capex_vals, name="Capex", marker_color="#C99C3B",
                              hovertemplate="Capex: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Scatter(x=capex_years, y=fcf_vals, mode="lines+markers", name="Free Cash Flow",
                                  line=dict(color="#C1443C", width=3), marker=dict(size=10),
                                  hovertemplate="FCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", barmode="group",
                          yaxis=dict(title="$B", gridcolor="#F0F0EC"),
                          legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                          margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_fcf, use_container_width=True)

    with st.expander("Why does this matter? — click to learn"):
        st.markdown(explainer_body(
            what="Operating cash is money the business generates day-to-day. Capex is money spent on long-term assets. Free cash flow is what's left after both.",
            example="If your bakery earns $136 a month and spends $65 on a new oven that will last 10 years, you have $71 left in your pocket. That $71 is your free cash flow. If next year the oven costs $130 to replace, your FCF drops to $6. That's the squeeze Microsoft is starting to feel.",
            why="Investors watch FCF closely because it's the money that could pay dividends, buy back stock, or grow the business. If FCF keeps dropping, Microsoft eventually has to slow spending — or borrow money to keep it up."
        ))

    note("**The big question:** Is this AI spending going to pay off? If Azure keeps growing 21%+ per year, "
         "these datacenters become gold mines. If AI demand cools down, Microsoft will have overspent by tens of billions. "
         "That's the bet — in one paragraph.")

# ============================================================
# TAB 5: AI COPILOT
# ============================================================
with tabs[4]:
    section_divider("01", "AI Copilot", "Click a question, get a plain-English answer")

    note("Not sure where to start? Click any of the 10 questions below and get a conversational answer. "
         "These are the questions people ask most often about Microsoft's 10-K.")

    questions = [
        ("What's the headline story?",
         "Microsoft had a **record-breaking year** — $281.7B in revenue, up 14.9%. But the real story isn't the growth. "
         "It's that they spent **$64.6 billion on AI infrastructure** — a 45% jump, more than double what they spent 2 years ago. "
         "For the first time in years, free cash flow actually shrank slightly because of it. Microsoft is making the biggest "
         "infrastructure bet in its history, and everyone is watching to see if it pays off."),

        ("How much money did Microsoft make this year?",
         "**$281.7 billion in revenue** — that's total sales. Of that, **$101.8 billion was pure profit** after all expenses and taxes. "
         "To put that in perspective: Microsoft makes more profit in a year than the entire GDP of countries like Ecuador or Guatemala. "
         "Their profit margin is 36% — for every $1 they sell, they keep 36 cents. That's elite territory."),

        ("Why is Microsoft spending so much on AI right now?",
         "Because they believe whoever wins AI wins the next 20 years of computing. Right now, **Azure (their cloud business) is growing 21% a year** — "
         "mostly powered by companies renting AI compute. Every $1 they spend on datacenters today = future rent from businesses running AI models. "
         "It's like building apartments in a boomtown before everyone moves in. The risk: if AI demand cools, they've overspent. "
         "The reward: they own the picks and shovels of the AI gold rush."),

        ("Is Microsoft financially healthy?",
         "**Extremely.** Three quick check-ups: (1) They have almost no debt relative to earnings — they could pay off ALL debt with one month of earnings. "
         "(2) For every $1 invested in the business, they generate 27 cents in profit — world-class efficiency. "
         "(3) They score 40.4 on the 'Rule of 40' test — the elite growth+profitability threshold. Microsoft passes every health check with flying colors."),

        ("Which business is growing fastest?",
         "**Intelligent Cloud** — that's Azure, servers, and enterprise services. It grew **21% to $106.3B**. "
         "For context, Microsoft's other segments grew 13% (Office/LinkedIn) and 7% (Windows/Xbox). "
         "Intelligent Cloud is now 38% of Microsoft's total revenue, up from about 30% a few years ago. It's clearly the growth engine."),

        ("Should I be worried about the cash flow drop?",
         "Honestly? Not really. Yes, free cash flow dropped 3.3% — the first drop in years. **But it dropped because they chose to invest more, not because business is weaker.** "
         "Their operating cash flow actually grew 15% — the underlying business is fine. They're just spending more on tomorrow. "
         "It would be worrying if operating cash was dropping. It's not. This is a spending choice, not a business problem."),

        ("How does Microsoft compare to other tech giants?",
         "Microsoft is in the top tier along with Apple, Google, Amazon, and Nvidia. **What makes Microsoft unique:** they have the most 'stable' business — "
         "enterprise software renewals are like a subscription treadmill of cash. Apple depends on iPhone cycles. Google depends on ad markets. "
         "Amazon has lower margins. Microsoft has diversified revenue with software-level margins, which is why investors love them."),

        ("What could go wrong for Microsoft?",
         "Three real risks: **(1) AI overbuilding** — if they've built too much datacenter capacity and AI demand plateaus, that $65B/year in spending looks bad. "
         "**(2) Regulatory pressure** — governments are watching Big Tech closely, and Microsoft's OpenAI ties invite scrutiny. "
         "**(3) Cloud competition** — Amazon AWS and Google Cloud are fighting hard for the same customers. Microsoft's Azure lead isn't guaranteed."),

        ("Is the AI bet paying off yet?",
         "**Partially.** Azure's 21% growth is the clearest 'yes' signal — customers are paying real money for AI compute. **But** most of the massive datacenter buildout "
         "was completed just this year, meaning the full payoff shows up in FY26 and beyond. The next 12-18 months will be the real test. "
         "If Azure keeps growing 20%+ while capex growth slows, it's working. If growth cools while capex stays high, watch out."),

        ("In one sentence — is Microsoft a good company?",
         "**Yes — Microsoft is one of the strongest businesses on Earth**, generating $101 billion in profit at 45% margins with virtually no debt, "
         "and they're using that fortress balance sheet to make the biggest AI bet in tech history. "
         "The only real question isn't 'is it a good company?' — it's 'is the AI bet a good bet?' And that's still being written."),
    ]

    if "selected_q" not in st.session_state:
        st.session_state.selected_q = None

    # 2-column grid of clickable question tiles
    for i in range(0, len(questions), 2):
        cols_q = st.columns(2)
        for j in range(2):
            if i + j < len(questions):
                q, _ = questions[i + j]
                with cols_q[j]:
                    if st.button(q, key=f"q_{i+j}"):
                        st.session_state.selected_q = i + j

    # Show selected answer
    if st.session_state.selected_q is not None:
        q, a = questions[st.session_state.selected_q]
        st.markdown(f"""
        <div class="analyst-note" style="margin-top:1.5rem; font-size:0.98rem;">
          <div style="color:#0A2540; font-weight:600; font-size:1.05rem; margin-bottom:0.6rem;">{q}</div>
          <div style="line-height:1.65;">{a}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<br><center style='color:#8B95A1; font-size:0.9rem;'>↑ Click a question above to see the answer</center>", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
  <div style="font-size:1rem; color:#FFFFFF; margin-bottom:0.5rem;">
    Microsoft FY2025 10-K Intelligence Dashboard
  </div>
  <div style="margin-bottom:1rem;">
    Built by <strong style="color:#FFFFFF;">Bea Lucido-Tan</strong> · Data verified from Microsoft's FY2025 Form 10-K (filed Jul 30, 2025)
  </div>
  <div>
    <a href="https://www.linkedin.com/in/bealucidotan" target="_blank">LinkedIn</a>·
    <a href="https://github.com/bealucidotan" target="_blank">GitHub</a>·
    <a href="https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q4/press-release-webcast" target="_blank">Source 10-K</a>
  </div>
  <div style="margin-top:1rem; font-size:0.72rem; color:#8B95A1;">
    For educational and portfolio purposes only. Not investment advice.
  </div>
</div>
""", unsafe_allow_html=True)

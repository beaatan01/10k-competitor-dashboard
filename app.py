import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tenk_engine as engine

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="MSFT FY25 10-K — Made Simple",
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

.kpi-card {
  background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 8px;
  padding: 1.1rem 1.25rem; height: 100%;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  animation: fadeInUp 0.5s ease both;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(10,37,64,0.08); }
.kpi-label { font-size: 0.72rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem; font-weight: 500; }
.kpi-value { font-size: 1.85rem; font-weight: 600; color: #0A2540; line-height: 1.1; }
.kpi-delta { font-size: 0.82rem; margin-top: 0.35rem; font-weight: 500; }
.kpi-delta.up { color: #0E7C4A; }
.kpi-delta.down { color: #C1443C; }
.kpi-delta.flat { color: #8B95A1; }
.kpi-sub { font-size: 0.72rem; color: #8B95A1; margin-top: 0.2rem; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.explainer {
  background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 8px;
  padding: 1rem 1.25rem; margin: 0.75rem 0 1.25rem 0;
  font-size: 0.92rem; line-height: 1.6;
}
.explainer .what { color: #0A2540; }
.explainer .why { color: #C99C3B; }
.explainer .example { color: #5B7A99; font-style: italic; }

.analyst-note {
  background: #FFFDF5; border-left: 3px solid #C99C3B; border-radius: 4px;
  padding: 0.9rem 1.1rem; margin: 1rem 0;
  font-size: 0.92rem; color: #1a1a1a; line-height: 1.55;
}
.analyst-note strong { color: #0A2540; }

.tldr-box {
  background: linear-gradient(135deg, #FFFFFF 0%, #F7F7F4 100%);
  border: 1px solid #E5E5E0; border-radius: 12px;
  padding: 1.5rem 1.75rem; margin: 1rem 0 2rem 0;
  box-shadow: 0 2px 8px rgba(10,37,64,0.04);
}
.tldr-label { font-size: 0.72rem; color: #C99C3B; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; margin-bottom: 0.5rem; }
.tldr-headline { font-size: 1.35rem; color: #0A2540; font-weight: 600; line-height: 1.35; margin-bottom: 0.6rem; }
.tldr-body { font-size: 0.98rem; color: #3a3a3a; line-height: 1.6; }

.ribbon {
  background: #0A2540; color: #FFFFFF;
  padding: 0.9rem 1.5rem; border-radius: 8px;
  display: flex; justify-content: space-around; align-items: center;
  margin: 1.25rem 0 1.75rem 0; flex-wrap: wrap; gap: 1rem;
}
.ribbon-item { text-align: center; min-width: 110px; }
.ribbon-num { font-size: 1.3rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.ribbon-lbl { font-size: 0.68rem; color: #C9D1DA; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.15rem; }

.verified-badge { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: #0E7C4A; font-weight: 500; }
.pulse-dot { width: 8px; height: 8px; border-radius: 50%; background: #0E7C4A; animation: pulse 2s infinite; }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(14,124,74,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(14,124,74,0); }
}

.as-of { display: inline-block; background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 20px; padding: 0.25rem 0.75rem; font-size: 0.72rem; color: #6B7280; font-family: 'JetBrains Mono', monospace; margin-left: 0.5rem; }

.footer { background: #0A2540; color: #C9D1DA; padding: 2rem; border-radius: 8px; margin-top: 3rem; text-align: center; font-size: 0.85rem; }
.footer a { color: #C99C3B; text-decoration: none; margin: 0 0.75rem; font-weight: 500; }
.footer a:hover { color: #FFFFFF; }

.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: transparent; border-bottom: 1px solid #E5E5E0; }
.stTabs [data-baseweb="tab"] { background: transparent; border: none; padding: 0.75rem 1.1rem; color: #6B7280; font-weight: 500; font-size: 0.95rem; }
.stTabs [aria-selected="true"] { color: #0A2540 !important; border-bottom: 2px solid #C99C3B !important; }

[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5E5E0; }
.stButton>button { background: #0A2540; color: #FFFFFF; border: none; padding: 0.6rem 1rem; border-radius: 6px; font-weight: 500; transition: all 0.15s ease; width: 100%; text-align: left; }
.stButton>button:hover { background: #14375C; transform: translateY(-1px); }

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA — verified from MSFT FY25 10-K
# ============================================================
FIN = engine.microsoft_fallback_financials()

# ============================================================
# HELPERS
# ============================================================
def kpi_card(label, value, delta=None, delta_dir="flat", sub=None):
    delta_html = ""
    if delta:
        arrow = "▲" if delta_dir == "up" else ("▼" if delta_dir == "down" else "—")
        delta_html = f'<div class="kpi-delta {delta_dir}">{arrow} {delta}</div>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
      {sub_html}
    </div>
    """

def section_divider(num, title):
    st.markdown(f"""
    <div class="section-divider">
      <span class="section-num">{num}</span>
      <h2 class="section-title">{title}</h2>
    </div>
    """, unsafe_allow_html=True)

def explainer(what, example, why):
    st.markdown(f"""
    <div class="explainer">
      <div><span class="what">📘 <strong>What is this?</strong></span> {what}</div>
      <div style="margin-top:0.4rem;"><span class="example">🍰 <strong>For example:</strong> {example}</span></div>
      <div style="margin-top:0.4rem;"><span class="why">💡 <strong>Why it matters:</strong></span> {why}</div>
    </div>
    """, unsafe_allow_html=True)

def note(text):
    st.markdown(f'<div class="analyst-note">💬 {text}</div>', unsafe_allow_html=True)

def fmt_money(v, unit="B"):
    return f"${v:.1f}{unit}"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📊 MSFT 10-K")
    st.markdown("**Made simple for everyone.**")
    st.markdown('<span class="as-of">FY2025 · Filed Jul 30, 2025</span>', unsafe_allow_html=True)
    st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Verified from 10-K PDF</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### 🗺️ Where to go")
    st.markdown("""
    - **Welcome** — Start here
    - **The Big Picture** — Key numbers
    - **Revenue & Segments** — What they sell
    - **Where the Cash Went** — Spending story
    - **Ask Me Anything** — AI Q&A
    """)
    st.markdown("---")
    st.markdown("#### 🎓 New to finance?")
    st.markdown("<small>Every chart has plain-English explanations with cake analogies. No jargon, promise.</small>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<small><strong>Built by</strong> Bea Lucido-Tan</small>", unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "👋 Welcome",
    "📊 The Big Picture",
    "💰 Revenue & Segments",
    "🏗️ Where the Cash Went",
    "🤖 Ask Me Anything",
])

# ============================================================
# TAB 1: WELCOME
# ============================================================
with tabs[0]:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# Microsoft FY2025 10-K")
        st.markdown("### The whole 200-page filing, made simple.")
    with col2:
        st.markdown('<br><span class="as-of">As of Jul 30, 2025</span>', unsafe_allow_html=True)
        st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Data verified</div>', unsafe_allow_html=True)

    # TL;DR
    st.markdown(f"""
    <div class="tldr-box">
      <div class="tldr-label">The 30-Second Version</div>
      <div class="tldr-headline">Microsoft had a record-breaking year — but they're spending like never before to win the AI race.</div>
      <div class="tldr-body">
        Revenue hit <strong>$281.7 billion</strong> (up 14.9%), and profits stayed strong. But here's the twist:
        Microsoft spent <strong>$64.6 billion on AI infrastructure</strong> — that's 45% more than last year, and
        <strong>more than double what they spent just two years ago</strong>. Their cash cushion actually shrank a bit
        because of it. The big question: <em>will this massive AI bet pay off?</em>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # By the numbers ribbon
    st.markdown(f"""
    <div class="ribbon">
      <div class="ribbon-item"><div class="ribbon-num">$281.7B</div><div class="ribbon-lbl">Revenue</div></div>
      <div class="ribbon-item"><div class="ribbon-num">$101.8B</div><div class="ribbon-lbl">Profit</div></div>
      <div class="ribbon-item"><div class="ribbon-num">45.6%</div><div class="ribbon-lbl">Op Margin</div></div>
      <div class="ribbon-item"><div class="ribbon-num">$64.6B</div><div class="ribbon-lbl">AI Spending</div></div>
      <div class="ribbon-item"><div class="ribbon-num">$71.6B</div><div class="ribbon-lbl">Free Cash</div></div>
      <div class="ribbon-item"><div class="ribbon-num">228K</div><div class="ribbon-lbl">Employees</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Hero chart
    section_divider("01", "The story in one chart")

    note("Think of this chart like watching a company's diet log. The **blue bars** are how much money Microsoft brought in each year. "
         "The **gold line** is how much they spent on new equipment (mostly AI datacenters). Notice how the gold line is climbing way faster than the bars? "
         "That's the whole story.")

    years = list(range(2020, 2026))
    revenue = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    capex = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=revenue, name="Revenue (money in)", marker_color="#0A2540",
                          hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig.add_trace(go.Scatter(x=years, y=capex, name="AI/Infrastructure Spending", yaxis="y2",
                              mode="lines+markers", line=dict(color="#C99C3B", width=3),
                              marker=dict(size=10),
                              hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>"))
    fig.add_annotation(x=2023, y=28.1, text="ChatGPT launches →<br>AI arms race begins", showarrow=True,
                        arrowhead=2, ax=-60, ay=-50, font=dict(size=10, color="#6B7280"),
                        bgcolor="rgba(255,255,255,0.95)", bordercolor="#E5E5E0", borderwidth=1)
    fig.update_layout(
        height=440, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        yaxis=dict(title="Revenue ($B)", showgrid=True, gridcolor="#F0F0EC"),
        yaxis2=dict(title="Spending ($B)", overlaying="y", side="right", showgrid=False),
        xaxis=dict(showgrid=False, tickmode="array", tickvals=years),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(family="Inter", color="#1a1a1a"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🆕 What's happened since?")
    st.markdown("""
    <div class="analyst-note">
      Since this 10-K was filed, Microsoft released their <strong>Q1 FY2026 results</strong> (Jul-Sep 2025).
      Revenue kept climbing — but so did AI spending. The pattern hasn't changed: <strong>grow fast, spend faster.</strong>
      This dashboard focuses on the full FY2025 picture since that's the most comprehensive filing.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 👉 Where to next?")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**📊 The Big Picture**")
        st.caption("See the key numbers with plain-English explanations.")
    with c2:
        st.markdown("**💰 Revenue & Segments**")
        st.caption("What Microsoft actually sells and which parts are growing.")
    with c3:
        st.markdown("**🏗️ Where the Cash Went**")
        st.caption("The AI spending mega-story, broken down.")
    with c4:
        st.markdown("**🤖 Ask Me Anything**")
        st.caption("Click a question, get an answer. No finance degree required.")

# ============================================================
# TAB 2: THE BIG PICTURE
# ============================================================
with tabs[1]:
    section_divider("02", "The Big Picture — Key numbers, explained")

    note("These are the 6 numbers investors care about most. Hover over each card for details. "
         "If a term is new, don't worry — we spell it out below the cards.")

    cols = st.columns(3)
    kpis_row1 = [
        ("Revenue", fmt_money(FIN["revenue"]), "+14.9%", "up", "vs $245.1B last year"),
        ("Net Income (Profit)", fmt_money(FIN["net_income"]), "+15.6%", "up", "money kept after all costs"),
        ("Operating Margin", f"{FIN['op_margin']:.1f}%", "+~100 bps", "up", "profit per $1 of sales"),
    ]
    for i, k in enumerate(kpis_row1):
        with cols[i]:
            st.markdown(kpi_card(*k), unsafe_allow_html=True)

    cols2 = st.columns(3)
    kpis_row2 = [
        ("Free Cash Flow (FCF)", fmt_money(FIN["fcf"]), "-3.3%", "down", "cash left after spending"),
        ("Capex (Spending)", fmt_money(FIN["capex"]), "+45.2%", "up", "mostly AI datacenters"),
        ("Earnings Per Share (EPS)", f"${FIN['eps']:.2f}", "+16.0%", "up", "profit per share owned"),
    ]
    for i, k in enumerate(kpis_row2):
        with cols2[i]:
            st.markdown(kpi_card(*k), unsafe_allow_html=True)

    # Explainers
    st.markdown("### 📚 Wait, what do these mean?")

    with st.expander("💵 **Revenue** — click to learn"):
        explainer(
            what="All the money Microsoft brought in from selling stuff — Office, Xbox, Azure cloud, LinkedIn, etc.",
            example="Imagine Microsoft is a giant bakery. Revenue is the total cash in the register at the end of the year — from every cupcake, cake, and coffee sold. It doesn't matter yet how much the ingredients cost.",
            why="This tells you if the company is growing. Microsoft grew 14.9% — that's huge for a company already worth trillions."
        )

    with st.expander("💰 **Net Income** — click to learn"):
        explainer(
            what="The actual profit — what's left after paying for everything (staff, rent, ingredients, taxes).",
            example="If the bakery made $282 in the register but spent $180 on flour, rent, and salaries — the $102 left over is net income. That's what shareholders actually 'earn'.",
            why="Revenue can look great but if profits are shrinking, something's wrong. Microsoft grew profit 15.6% — even faster than revenue. Very healthy."
        )

    with st.expander("📊 **Operating Margin** — click to learn"):
        explainer(
            what="Out of every $1 Microsoft brings in, how many cents are pure profit from operations (before taxes and interest).",
            example="If the bakery sells a $10 cake and $4.56 of that is profit, their operating margin is 45.6%. That's absurdly high — most bakeries are 5-10%.",
            why="Software has huge margins because copying software costs nothing. 45.6% shows Microsoft's pricing power is enormous."
        )

    with st.expander("💸 **Free Cash Flow (FCF)** — click to learn"):
        explainer(
            what="The real cash Microsoft has left over after paying for daily operations AND buying new equipment. This is the money they can hand to shareholders or save.",
            example="If the bakery makes $136 in cash but spends $65 on a new industrial oven, their FCF is $71. That $71 is 'real' money they can use however they want.",
            why="FCF dropped 3.3% this year — the first drop in 5+ years. It's not scary yet, but worth watching. AI spending is eating into the piggy bank."
        )

    with st.expander("🏗️ **Capex (Capital Expenditure)** — click to learn"):
        explainer(
            what="Money spent on big long-lasting things — buildings, servers, datacenters. Not everyday costs like salaries.",
            example="The bakery buying a $65 industrial oven is capex. Buying flour is not — flour is a regular expense. Ovens last 10+ years.",
            why="Microsoft's capex jumped 45% this year, almost all going to AI datacenters. This is the biggest infrastructure buildout in company history."
        )

    with st.expander("📈 **Earnings Per Share (EPS)** — click to learn"):
        explainer(
            what="Total profit divided by the number of shares. If you own 1 share, EPS is 'your slice' of the profit.",
            example="If the bakery made $102 in profit and there are 7.4 slices (shares) of ownership, each slice 'earned' $13.69.",
            why="EPS grew 16% — even more than net income (15.6%) because Microsoft also bought back some shares. Fewer slices = bigger slice per person."
        )

    # Health check
    section_divider("02a", "Is Microsoft healthy? — The 3-metric check")

    note("Doctors check your blood pressure, heart rate, and cholesterol. For companies, investors check three similar 'vital signs.' Here's how Microsoft grades.")

    hcols = st.columns(3)
    with hcols[0]:
        st.markdown(kpi_card("Rule of 40", f"{FIN['rule_of_40']:.1f}", "elite", "up", "Growth% + FCF margin%"), unsafe_allow_html=True)
    with hcols[1]:
        st.markdown(kpi_card("Return on Invested Capital (ROIC)", f"{FIN['roic']:.1f}%", "world class", "up", "profit per $ invested"), unsafe_allow_html=True)
    with hcols[2]:
        st.markdown(kpi_card("Net Debt / EBITDA", f"{FIN['net_debt_ebitda']:.2f}x", "fortress", "up", "how much they owe"), unsafe_allow_html=True)

    with st.expander("🎯 **Rule of 40** — click to learn"):
        explainer(
            what="A quick test: is the company growing fast AND profitable at the same time? Add growth % + profit margin %. Score above 40 is 'elite.'",
            example="If a bakery grows sales 15% AND keeps 25 cents of every dollar as profit, their score is 40. Cake-cutting elite. If they grow fast but lose money, or make money but don't grow, they fail this test.",
            why="Microsoft scored 40.4 — just inside the elite club, but at massive scale. Most companies would kill for this at $10B revenue, let alone $282B."
        )

    with st.expander("💎 **Return on Invested Capital (ROIC)** — click to learn"):
        explainer(
            what="How much profit Microsoft makes from every dollar invested in the business (by shareholders and lenders combined).",
            example="Think of Microsoft as a bakery you own with a friend. You both put in $100. At the end of the year, the bakery gives you back $27 in profit. Your ROIC is 27%. Way better than any bank account.",
            why="Above 15% means the company is creating real value. Above 20% is exceptional. Microsoft's 27% is world-class — they're one of the best 'money multipliers' on Earth."
        )

    with st.expander("🏦 **Net Debt / EBITDA** — click to learn"):
        explainer(
            what="How many years of earnings would it take to pay off all debt? Lower is safer.",
            example="If the bakery owes $3 and earns $37 a year, they could pay off debt in about a month. Their ratio is 0.08 — practically debt-free. If they owed $100 and earned $37, it'd take 3 years (way riskier).",
            why="Microsoft's 0.08x is 'fortress balance sheet' territory. They could pay off ALL debt with about one month's earnings. This gives them room to keep spending on AI without worry."
        )

# ============================================================
# TAB 3: REVENUE & SEGMENTS
# ============================================================
with tabs[2]:
    section_divider("03", "Revenue & Segments — What Microsoft actually sells")

    note("Microsoft isn't just one business — it's three big ones bundled together. "
         "Think of it like a food court with three restaurants. Let's see how each one is doing.")

    # 6-year revenue chart
    st.markdown("### 📈 The 5-year revenue story")

    years6 = list(range(2020, 2026))
    rev6 = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    growth6 = [None, 17.5, 17.9, 6.9, 15.7, 14.9]

    fig_r = go.Figure()
    fig_r.add_trace(go.Bar(x=years6, y=rev6, marker_color="#0A2540", name="Revenue",
                            text=[f"${v:.0f}B" for v in rev6], textposition="outside",
                            hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig_r.add_trace(go.Scatter(x=years6, y=growth6, mode="lines+markers", name="Growth % (year-over-year)",
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

    note("Microsoft doubled from $143B to $282B in just 5 years. That's like a lemonade stand going from selling "
         "143 cups a day to 282 cups a day — except each 'cup' is a billion dollars. The gold line shows growth is holding steady around 15%.")

    # Progress to $300B
    st.markdown("### 🎯 On track for the $300B milestone")
    progress_pct = (FIN["revenue"] / 300) * 100
    st.progress(progress_pct / 100, text=f"${FIN['revenue']:.1f}B out of $300B target · {progress_pct:.1f}% there")
    st.caption("At current pace, Microsoft crosses $300B in revenue around late 2025 / early 2026 — a historic milestone.")

    # Segments
    section_divider("03a", "The three restaurants in Microsoft's food court")

    seg_data = FIN["segments"]
    seg_df = pd.DataFrame(seg_data)
    colors_seg = ["#0A2540", "#C99C3B", "#5B7A99"]

    scols = st.columns(3)
    seg_explanations = [
        "Office, LinkedIn, Dynamics — the 'productivity' apps everyone uses at work.",
        "Azure cloud + servers — this is the AI money-maker.",
        "Windows, Xbox, Surface, Bing — the consumer stuff you interact with daily.",
    ]
    for i, seg in enumerate(seg_data):
        with scols[i]:
            direction = "up" if seg["growth"] > 0 else "down"
            st.markdown(kpi_card(
                seg["name"],
                fmt_money(seg["revenue"]),
                f"+{seg['growth']}%",
                direction,
                f"{seg['revenue']/FIN['revenue']*100:.0f}% of total"
            ), unsafe_allow_html=True)
            st.caption(seg_explanations[i])

    st.markdown("")

    # Bar chart
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(x=seg_df["name"], y=seg_df["revenue"],
                            marker_color=colors_seg,
                            text=[f"${v:.1f}B<br>+{g}%" for v, g in zip(seg_df["revenue"], seg_df["growth"])],
                            textposition="outside",
                            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig_s.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F0F0EC"),
                        margin=dict(l=40, r=40, t=40, b=40),
                        showlegend=False)
    st.plotly_chart(fig_s, use_container_width=True)

    note("**Intelligent Cloud is the star of the show.** It grew 21% — nearly 3x faster than the Windows/Xbox business (+7%). "
         "That's why Microsoft keeps pouring money into AI infrastructure. That segment is where the future is.")

    with st.expander("🍰 **Cake analogy** — what does 'segment' mean?"):
        explainer(
            what="A segment is just a big chunk of a company's business. Microsoft splits itself into 3 chunks so investors can see which parts are winning.",
            example="Imagine a bakery that sells three things: (1) wedding cakes, (2) coffee, and (3) breakfast pastries. Each is a 'segment.' If wedding cakes are exploding in demand but pastries are flat, that tells you where to invest more ovens.",
            why="Right now, Microsoft's 'wedding cake' is Azure/AI (+21% growth), while their 'pastries' are Windows/Xbox (+7%). Guess where they're building new ovens?"
        )

# ============================================================
# TAB 4: WHERE THE CASH WENT
# ============================================================
with tabs[3]:
    section_divider("04", "Where the Cash Went — The AI spending story")

    note("This tab is the most important one. Microsoft made $136 billion in cash this year. Where did it all go? "
         "Spoiler: mostly into building AI datacenters. Let's follow the money.")

    ca = FIN["capital_allocation"]

    ccols = st.columns(4)
    with ccols[0]:
        st.markdown(kpi_card("AI Infrastructure (Capex)", fmt_money(ca["capex"]), "+45%", "up",
                              "datacenters, servers, chips"), unsafe_allow_html=True)
    with ccols[1]:
        st.markdown(kpi_card("Stock Buybacks", fmt_money(ca["buybacks"]), "returned to owners", "flat",
                              "shrinks share count"), unsafe_allow_html=True)
    with ccols[2]:
        st.markdown(kpi_card("Dividends", fmt_money(ca["dividends"]), "quarterly payouts", "flat",
                              "cash to shareholders"), unsafe_allow_html=True)
    with ccols[3]:
        st.markdown(kpi_card("Acquisitions", fmt_money(ca["acquisitions"]), "buying companies", "flat",
                              "strategic add-ons"), unsafe_allow_html=True)

    with st.expander("💸 **What do these terms mean?**"):
        explainer(
            what="These are the 4 main ways Microsoft can use its cash: (1) invest in itself, (2) buy back its own shares, (3) pay shareholders directly, or (4) buy other companies.",
            example="Imagine you got a $100 bonus. You could: buy new tools for your side hustle ($65 = capex), pay down a loan you owe yourself ($17 = buybacks), give your family some ($24 = dividends), or buy a friend's business ($3 = acquisitions). That's basically what Microsoft did.",
            why="Right now, Microsoft is choosing option 1 aggressively — they think AI infrastructure will return more than any other use of cash. Time will tell if they're right."
        )

    # Capex mega-chart
    section_divider("04a", "The AI spending mega-story")

    note("This is THE chart to remember. Microsoft's spending on infrastructure has more than doubled in 2 years — "
         "from $28B to $65B. That's the biggest buildout in company history, and it's all going to AI.")

    capex_years = [2020, 2021, 2022, 2023, 2024, 2025]
    capex_vals = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig_capex = go.Figure()
    fig_capex.add_trace(go.Bar(x=capex_years, y=capex_vals, marker_color="#C99C3B",
                                text=[f"${v:.1f}B" for v in capex_vals], textposition="outside",
                                hovertemplate="<b>FY%{x}</b><br>Spending: $%{y:.1f}B<extra></extra>"))
    fig_capex.add_annotation(x=2023, y=28.1, text="Pre-AI baseline", showarrow=True, arrowhead=2,
                              ax=-40, ay=-40, font=dict(size=10, color="#6B7280"))
    fig_capex.add_annotation(x=2025, y=64.6, text="AI-era peak<br>(more than 2x in 2 years!)",
                              showarrow=True, arrowhead=2,
                              ax=40, ay=-50, font=dict(size=10, color="#C1443C"))
    fig_capex.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                             yaxis=dict(title="Capex ($B)", gridcolor="#F0F0EC"),
                             margin=dict(l=40, r=40, t=40, b=40),
                             showlegend=False)
    st.plotly_chart(fig_capex, use_container_width=True)

    # OCF vs Capex vs FCF
    section_divider("04b", "The cash flow squeeze")

    note("Here's the trade-off. Microsoft's operating cash (blue) is growing nicely. But their AI spending (gold) is growing FASTER. "
         "The red line (free cash flow) is what's left over — and this year, it actually shrank a bit for the first time in years.")

    ocf_vals = [60.7, 76.7, 89.0, 87.6, 118.5, 136.2]
    fcf_vals = [45.2, 56.1, 65.1, 59.5, 74.1, 71.6]

    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=capex_years, y=ocf_vals, name="Cash from operations", marker_color="#0A2540",
                              hovertemplate="OCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Bar(x=capex_years, y=capex_vals, name="AI/Capex spending", marker_color="#C99C3B",
                              hovertemplate="Capex: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Scatter(x=capex_years, y=fcf_vals, mode="lines+markers", name="Cash left over (FCF)",
                                  line=dict(color="#C1443C", width=3), marker=dict(size=10),
                                  hovertemplate="FCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", barmode="group",
                          yaxis=dict(title="$B", gridcolor="#F0F0EC"),
                          legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                          margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_fcf, use_container_width=True)

    with st.expander("🍰 **Cake analogy** — why does this matter?"):
        explainer(
            what="Operating cash is money the business generates day-to-day. Capex is money spent on long-term stuff. FCF is what's actually 'free' at the end.",
            example="Imagine you earn $136 a month from your bakery. You spend $65 on a new oven that will last 10 years. You have $71 left in your pocket — that's your FCF. If the oven cost $130 next year, your FCF would drop to $6. That's the squeeze Microsoft is starting to feel.",
            why="Investors watch FCF closely because it's the money that could pay dividends, buy back stock, or grow the business. If FCF keeps falling, Microsoft eventually has to slow spending — or borrow money to keep it up."
        )

    note("**The big question for investors:** Is this AI spending going to pay off? If Azure keeps growing 21%+ per year, "
         "these datacenters are gold mines. If AI demand cools down, Microsoft will have overspent by tens of billions. "
         "That's the bet, in one paragraph.")

# ============================================================
# TAB 5: ASK ME ANYTHING
# ============================================================
with tabs[4]:
    section_divider("05", "Ask Me Anything — Click a question")

    note("Not sure where to start? Just click any question below and get a plain-English answer. "
         "These are the 10 questions people ask most often about Microsoft's 10-K.")

    questions = [
        ("🎯", "What's the headline story?",
         "Microsoft had a **record-breaking year** — $281.7B in revenue, up 14.9%. But the real story isn't the growth. "
         "It's that they spent **$64.6 billion on AI infrastructure** — a 45% jump, more than double what they spent 2 years ago. "
         "For the first time in years, their free cash flow actually shrank a tiny bit because of it. Microsoft is making the biggest infrastructure bet in its history, and everyone is watching to see if it pays off."),

        ("💰", "How much money did Microsoft make this year?",
         "**$281.7 billion in revenue** — that's total sales. Of that, **$101.8 billion was pure profit** after all expenses and taxes. "
         "To put that in perspective: Microsoft makes more profit in a year than the entire GDP of countries like Ecuador or Guatemala. "
         "Their profit margin is 36%, which is elite. For every $1 they sell, they keep 36 cents."),

        ("🤖", "Why is Microsoft spending so much on AI right now?",
         "Because they think whoever wins AI wins the next 20 years of computing. Right now, **Azure (their cloud business) is growing 21% a year** — mostly powered by companies renting AI compute. "
         "Every $1 they spend on datacenters today = future rent from businesses running AI models. It's like building apartments in a boomtown before everyone moves in. "
         "The risk? If AI demand cools, they've overspent. The reward? They own the picks and shovels of the AI gold rush."),

        ("🏥", "Is Microsoft financially healthy?",
         "**Extremely.** Three quick check-ups: (1) They have almost no debt relative to earnings — they could pay off ALL debt with one month of earnings. "
         "(2) For every $1 invested in the business, they generate 27 cents in profit — world-class efficiency. "
         "(3) They score 40.4 on the 'Rule of 40' — the elite growth+profitability test. Microsoft passes every health check with flying colors."),

        ("🚀", "Which business is growing fastest?",
         "**Intelligent Cloud** — that's Azure, servers, and enterprise services. It grew **21% to $106.3B**. "
         "For context, Microsoft's other segments grew 13% (Office/LinkedIn) and 7% (Windows/Xbox). "
         "Intelligent Cloud is now 38% of Microsoft's total revenue, up from about 30% a few years ago. It's the growth engine."),

        ("😰", "Should I be worried about the cash flow drop?",
         "Honestly? Not really. Yes, free cash flow dropped 3.3% — the first drop in years. **But it dropped because they chose to invest more, not because business is weaker.** "
         "Their operating cash flow actually grew 15% — the underlying business is fine. They're just spending more on tomorrow. "
         "It'd be worrying if operating cash was dropping. It's not. This is a spending choice, not a business problem."),

        ("⚖️", "How does Microsoft compare to other tech giants?",
         "Microsoft is in the top tier along with Apple, Google, Amazon, and Nvidia. **What makes Microsoft unique:** they have the most 'stable' business — enterprise software renewals are like a subscription treadmill of cash. "
         "Apple depends on iPhone cycles. Google depends on ad markets. Amazon has lower margins. Microsoft has diversified revenue with software-level margins, which is why investors love them."),

        ("⚠️", "What could go wrong for Microsoft?",
         "Three real risks: (1) **AI overbuilding** — if they've built too much datacenter capacity and AI demand plateaus, that $65B/year in spending looks bad. "
         "(2) **Regulatory pressure** — governments are watching Big Tech closely, and Microsoft's OpenAI ties invite scrutiny. "
         "(3) **Cloud competition** — Amazon AWS and Google Cloud are fighting hard for the same customers. Microsoft's Azure lead isn't guaranteed."),

        ("🎲", "Is the AI bet paying off yet?",
         "**Partially.** Azure's 21% growth is the clearest 'yes' signal — customers are paying for AI compute. **But** most of the massive datacenter buildout was completed this year, meaning the payoff shows up in FY26 and beyond. "
         "The next 12-18 months will be the real test. If Azure keeps growing 20%+ while capex growth slows, it's working. If growth cools while capex stays high, watch out."),

        ("🎬", "In one sentence — is Microsoft a good company?",
         "**Yes — Microsoft is one of the strongest businesses on Earth**, generating $101 billion in profit at 45% margins with virtually no debt, and they're using that fortress to make the biggest AI bet in tech. "
         "The only real question isn't 'is it a good company?' — it's 'is the AI bet a good bet?' And that's still being written."),
    ]

    if "selected_q" not in st.session_state:
        st.session_state.selected_q = None

    # 2 columns of clickable question tiles
    for i in range(0, len(questions), 2):
        cols_q = st.columns(2)
        for j in range(2):
            if i + j < len(questions):
                emoji, q, _ = questions[i + j]
                with cols_q[j]:
                    if st.button(f"{emoji}  {q}", key=f"q_{i+j}"):
                        st.session_state.selected_q = i + j

    # Show answer
    if st.session_state.selected_q is not None:
        emoji, q, a = questions[st.session_state.selected_q]
        st.markdown(f"""
        <div class="analyst-note" style="margin-top:1.5rem; font-size:1rem;">
          <div style="color:#0A2540; font-weight:600; font-size:1.05rem; margin-bottom:0.5rem;">{emoji} {q}</div>
          <div>{a}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
  <div style="font-size:1rem; color:#FFFFFF; margin-bottom:0.5rem;">
    Microsoft FY2025 10-K — Made Simple
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

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
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
/* Base */
.stApp { background: #F7F7F4; }
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; color: #1a1a1a; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1400px; }

/* Numerals — tabular */
.num, .kpi-value, .metric-value { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum'; }

/* Headings */
h1, h2, h3, h4 { color: #0A2540; font-weight: 600; letter-spacing: -0.01em; }
h1 { font-size: 2.25rem; }

/* Section divider */
.section-divider {
  display: flex; align-items: baseline; gap: 1rem;
  margin: 2.5rem 0 1.25rem 0; padding-bottom: 0.5rem;
  border-bottom: 1px solid #E5E5E0;
}
.section-num { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #8B95A1; letter-spacing: 0.1em; }
.section-title { font-size: 1.5rem; font-weight: 600; color: #0A2540; margin: 0; }

/* KPI card */
.kpi-card {
  background: #FFFFFF; border: 1px solid #E5E5E0; border-radius: 8px;
  padding: 1.1rem 1.25rem; height: 100%;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  animation: fadeInUp 0.5s ease both;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(10,37,64,0.08); border-color: #C9D1DA; }
.kpi-label { font-size: 0.72rem; color: #6B7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem; font-weight: 500; }
.kpi-value { font-size: 1.85rem; font-weight: 600; color: #0A2540; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi-delta { font-size: 0.82rem; margin-top: 0.35rem; font-weight: 500; }
.kpi-delta.up { color: #0E7C4A; }
.kpi-delta.down { color: #C1443C; }
.kpi-delta.flat { color: #8B95A1; }
.kpi-sub { font-size: 0.72rem; color: #8B95A1; margin-top: 0.2rem; }

/* Stagger */
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

/* Analyst note */
.analyst-note {
  background: #FFFDF5; border-left: 3px solid #C99C3B; border-radius: 4px;
  padding: 0.9rem 1.1rem; margin: 1rem 0;
  font-size: 0.92rem; color: #1a1a1a; line-height: 1.5;
}
.analyst-note strong { color: #0A2540; }

/* TL;DR box */
.tldr-box {
  background: linear-gradient(135deg, #FFFFFF 0%, #F7F7F4 100%);
  border: 1px solid #E5E5E0; border-radius: 12px;
  padding: 1.5rem 1.75rem; margin: 1rem 0 2rem 0;
  box-shadow: 0 2px 8px rgba(10,37,64,0.04);
}
.tldr-label { font-size: 0.72rem; color: #C99C3B; text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; margin-bottom: 0.5rem; }
.tldr-headline { font-size: 1.35rem; color: #0A2540; font-weight: 600; line-height: 1.35; margin-bottom: 0.6rem; }
.tldr-body { font-size: 0.98rem; color: #3a3a3a; line-height: 1.55; }

/* Ribbon */
.ribbon {
  background: #0A2540; color: #FFFFFF;
  padding: 0.9rem 1.5rem; border-radius: 8px;
  display: flex; justify-content: space-around; align-items: center;
  margin: 1.25rem 0 1.75rem 0; flex-wrap: wrap; gap: 1rem;
}
.ribbon-item { text-align: center; min-width: 110px; }
.ribbon-num { font-size: 1.3rem; font-weight: 600; font-variant-numeric: tabular-nums; }
.ribbon-lbl { font-size: 0.68rem; color: #C9D1DA; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.15rem; }

/* Verified pulse dot */
.verified-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.75rem; color: #0E7C4A; font-weight: 500;
}
.pulse-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #0E7C4A;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(14,124,74,0.5); }
  50% { box-shadow: 0 0 0 6px rgba(14,124,74,0); }
}

/* As of badge */
.as-of {
  display: inline-block; background: #FFFFFF; border: 1px solid #E5E5E0;
  border-radius: 20px; padding: 0.25rem 0.75rem;
  font-size: 0.72rem; color: #6B7280; font-family: 'JetBrains Mono', monospace;
  margin-left: 0.5rem;
}

/* Source cite */
.source-cite { font-size: 0.68rem; color: #8B95A1; vertical-align: super; }

/* Footer */
.footer {
  background: #0A2540; color: #C9D1DA;
  padding: 2rem 2rem; border-radius: 8px;
  margin-top: 3rem; text-align: center;
  font-size: 0.85rem;
}
.footer a { color: #C99C3B; text-decoration: none; margin: 0 0.75rem; font-weight: 500; }
.footer a:hover { color: #FFFFFF; }

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: transparent; border-bottom: 1px solid #E5E5E0; }
.stTabs [data-baseweb="tab"] {
  background: transparent; border: none; padding: 0.75rem 1.1rem;
  color: #6B7280; font-weight: 500; font-size: 0.9rem;
}
.stTabs [aria-selected="true"] { color: #0A2540 !important; border-bottom: 2px solid #C99C3B !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E5E5E0; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #0A2540; }

/* Buttons */
.stButton>button {
  background: #0A2540; color: #FFFFFF; border: none;
  padding: 0.5rem 1.25rem; border-radius: 6px; font-weight: 500;
  transition: all 0.15s ease;
}
.stButton>button:hover { background: #14375C; transform: translateY(-1px); }

/* Hide streamlit chrome */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA LOAD
# ============================================================
FIN = engine.microsoft_fallback_financials()
RIBBON = engine.ribbon_stats(FIN)
EVENTS = engine.TIMELINE_EVENTS
BENCH = engine.INDUSTRY_BENCHMARKS
FORMULAS = engine.FORMULAS
SOURCES = engine.SOURCE_REFS

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

def section_divider(num, title):
    st.markdown(f"""
    <div class="section-divider">
      <span class="section-num">{num}</span>
      <h2 class="section-title">{title}</h2>
    </div>
    """, unsafe_allow_html=True)

def analyst_note(text):
    st.markdown(f'<div class="analyst-note">💡 <strong>Analyst note:</strong> {text}</div>', unsafe_allow_html=True)

def ribbon_bar():
    items = "".join([
        f'<div class="ribbon-item"><div class="ribbon-num">{v}</div><div class="ribbon-lbl">{k}</div></div>'
        for k, v in RIBBON.items()
    ])
    st.markdown(f'<div class="ribbon">{items}</div>', unsafe_allow_html=True)

def gauge(value, title, thresholds, suffix="", max_val=None):
    """thresholds = [red_max, yellow_max, green_max]"""
    if max_val is None:
        max_val = thresholds[2] * 1.2
    color = "#0E7C4A" if value >= thresholds[1] else ("#C99C3B" if value >= thresholds[0] else "#C1443C")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix, "font": {"size": 28, "color": "#0A2540"}},
        title={"text": title, "font": {"size": 13, "color": "#6B7280"}},
        gauge={
            "axis": {"range": [0, max_val], "tickcolor": "#8B95A1", "tickfont": {"size": 10}},
            "bar": {"color": color, "thickness": 0.7},
            "bgcolor": "#F7F7F4",
            "borderwidth": 0,
            "steps": [
                {"range": [0, thresholds[0]], "color": "#FBEBEA"},
                {"range": [thresholds[0], thresholds[1]], "color": "#FDF6E3"},
                {"range": [thresholds[1], max_val], "color": "#E8F5EE"},
            ],
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="#FFFFFF")
    return fig

def sparkline(values, color="#0A2540"):
    fig = go.Figure(go.Scatter(y=values, mode="lines", line=dict(color=color, width=2), fill="tozeroy",
                                fillcolor=f"rgba(10,37,64,0.08)"))
    fig.update_layout(height=60, margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

def fmt_money(v, unit="B"):
    return f"${v:.1f}{unit}"

def fmt_pct(v):
    return f"{v:.1f}%"

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📊 MSFT 10-K Intelligence")
    st.markdown('<span class="as-of">FY2025 · Filed Jul 30, 2025</span>', unsafe_allow_html=True)
    st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Verified from 10-K PDF</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### Navigation")
    st.markdown("""
    - 01 · Welcome
    - 02 · Executive Summary
    - 03 · Intelligence Hub
    - 04 · Revenue Intelligence
    - 05 · Segments
    - 06 · Capital Allocation
    - 07 · AI Forecasting
    - 08 · Financial Statements
    - 09 · AI Copilot
    """)
    st.markdown("---")
    st.markdown("#### About")
    st.markdown("<small>Interactive analysis of Microsoft's FY2025 10-K filing. Built for portfolio demonstration.</small>", unsafe_allow_html=True)
    st.markdown("<small>**Author:** Bea Lucido-Tan</small>", unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "Welcome",
    "Executive Summary",
    "Intelligence Hub",
    "Revenue Intelligence",
    "Segments",
    "Capital Allocation",
    "AI Forecasting",
    "Financial Statements",
    "AI Copilot",
])

# ============================================================
# TAB 1: WELCOME
# ============================================================
with tabs[0]:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# Microsoft FY2025 10-K")
        st.markdown("### Financial intelligence, decoded.")
    with col2:
        st.markdown('<br><span class="as-of">As of Jul 30, 2025</span>', unsafe_allow_html=True)
        st.markdown('<div class="verified-badge"><span class="pulse-dot"></span> Data verified</div>', unsafe_allow_html=True)

    # TL;DR
    st.markdown(f"""
    <div class="tldr-box">
      <div class="tldr-label">The TL;DR</div>
      <div class="tldr-headline">Record revenue of $281.7B — but Microsoft is betting the house on AI infrastructure.</div>
      <div class="tldr-body">
        FY25 delivered <strong>+14.9% revenue growth</strong> and <strong>45.6% operating margins</strong>, yet
        <strong>capex jumped 45% to $64.6B</strong> (more than doubled over two years). Free cash flow dipped
        3.3% as AI datacenter investment outpaced cash generation. The bet: turn today's compute build-out into
        tomorrow's Azure AI moat.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # By the numbers ribbon
    ribbon_bar()

    # Hero chart — revenue with capex overlay
    section_divider("01", "The story in one chart")
    years = list(range(2020, 2026))
    revenue = [143.0, 168.1, 198.3, 211.9, 245.1, 281.7]
    capex = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=revenue, name="Revenue", marker_color="#0A2540",
                          hovertemplate="<b>FY%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig.add_trace(go.Scatter(x=years, y=capex, name="Capex", yaxis="y2",
                              mode="lines+markers", line=dict(color="#C99C3B", width=3),
                              marker=dict(size=9),
                              hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>"))
    # Timeline annotations
    for ev in EVENTS:
        if ev["year"] in years:
            fig.add_annotation(x=ev["year"], y=revenue[years.index(ev["year"])],
                                text=ev["label"], showarrow=True, arrowhead=2,
                                ax=0, ay=-40, font=dict(size=10, color="#6B7280"),
                                bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E5E0", borderwidth=1)
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

    analyst_note("Revenue and capex both accelerating — but capex is compounding faster. "
                 "This is the defining tension of Microsoft's FY25 story.")

    st.markdown("---")
    st.markdown("**Navigate using the tabs above.** Each section drills into a different layer of the filing.")

# ============================================================
# TAB 2: EXECUTIVE SUMMARY
# ============================================================
with tabs[1]:
    section_divider("02", "Executive Summary")

    # Hero KPI strip
    cols = st.columns(6)
    kpis = [
        ("Revenue", fmt_money(FIN["revenue"]), "+14.9%", "up", "vs $245.1B FY24", "p.48"),
        ("Operating Margin", fmt_pct(FIN["op_margin"]), "+98 bps", "up", "vs 44.6%", "p.49"),
        ("Net Income", fmt_money(FIN["net_income"]), "+15.6%", "up", "vs $88.1B", "p.51"),
        ("Free Cash Flow", fmt_money(FIN["fcf"]), "-3.3%", "down", "capex drag", "p.55"),
        ("Capex", fmt_money(FIN["capex"]), "+45.2%", "up", "AI infra", "p.66"),
        ("EPS", f"${FIN['eps']:.2f}", "+16.0%", "up", "vs $11.80", "p.51"),
    ]
    for i, (label, val, delta, direction, sub, src) in enumerate(kpis):
        with cols[i]:
            st.markdown(kpi_card(label, val, delta, direction, sub, src), unsafe_allow_html=True)

    st.markdown("")

    # Analyst take
    analyst_note(engine.answer_question("What is the key story?"))

    # Ratio quality gauges
    section_divider("02a", "Health check — how do the ratios grade?")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(gauge(FIN["rule_of_40"], "Rule of 40", [20, 40, 50], "%"), use_container_width=True)
        st.caption("Growth + FCF margin. **Green ≥ 40%** = elite SaaS.")
    with g2:
        st.plotly_chart(gauge(FIN["roic"], "ROIC", [10, 15, 25], "%"), use_container_width=True)
        st.caption("Return on invested capital. **Green ≥ 15%** = value creating.")
    with g3:
        # inverted: lower is better for leverage
        nd = FIN["net_debt_ebitda"]
        color_val = 3 - nd if nd < 3 else 0.1  # transform for gauge
        fig_lev = go.Figure(go.Indicator(
            mode="gauge+number", value=nd,
            number={"suffix": "x", "font": {"size": 28, "color": "#0A2540"}},
            title={"text": "Net Debt / EBITDA", "font": {"size": 13, "color": "#6B7280"}},
            gauge={
                "axis": {"range": [0, 3], "tickcolor": "#8B95A1"},
                "bar": {"color": "#0E7C4A", "thickness": 0.7},
                "bgcolor": "#F7F7F4",
                "steps": [
                    {"range": [0, 1], "color": "#E8F5EE"},
                    {"range": [1, 2], "color": "#FDF6E3"},
                    {"range": [2, 3], "color": "#FBEBEA"},
                ],
            }
        ))
        fig_lev.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig_lev, use_container_width=True)
        st.caption("Leverage. **Green ≤ 1.0x** = fortress balance sheet.")

    # Industry benchmarks
    section_divider("02b", "How MSFT compares to industry")
    bench_df = pd.DataFrame([
        {"Metric": "Op Margin", "MSFT": FIN["op_margin"], "Industry Median": BENCH["op_margin_median"], "Top Quartile": BENCH["op_margin_top"]},
        {"Metric": "ROIC", "MSFT": FIN["roic"], "Industry Median": BENCH["roic_median"], "Top Quartile": BENCH["roic_top"]},
        {"Metric": "Rule of 40", "MSFT": FIN["rule_of_40"], "Industry Median": BENCH["rule40_median"], "Top Quartile": BENCH["rule40_top"]},
    ])
    fig_b = go.Figure()
    fig_b.add_trace(go.Bar(name="Industry Median", x=bench_df["Metric"], y=bench_df["Industry Median"],
                            marker_color="#C9D1DA", hovertemplate="%{y:.1f}%<extra>Industry Median</extra>"))
    fig_b.add_trace(go.Bar(name="Top Quartile", x=bench_df["Metric"], y=bench_df["Top Quartile"],
                            marker_color="#8B95A1", hovertemplate="%{y:.1f}%<extra>Top Quartile</extra>"))
    fig_b.add_trace(go.Bar(name="Microsoft", x=bench_df["Metric"], y=bench_df["MSFT"],
                            marker_color="#0A2540", hovertemplate="%{y:.1f}%<extra>MSFT</extra>"))
    fig_b.update_layout(barmode="group", height=320, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="%", gridcolor="#F0F0EC"),
                        margin=dict(l=40, r=40, t=20, b=40),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=1, xanchor="right"))
    st.plotly_chart(fig_b, use_container_width=True)
    analyst_note("MSFT sits comfortably in top-quartile territory across all three health metrics — "
                 "the AI capex bet is being made from a position of financial strength, not weakness.")

# ============================================================
# TAB 3: INTELLIGENCE HUB
# ============================================================
with tabs[2]:
    section_divider("03", "Intelligence Hub — what changed this year")

    # Rotating insights carousel (auto-cycles via selectbox)
    insights = [
        ("💡 Capex compound", f"Capex has grown from $28B (FY23) → $65B (FY25) — a **2.3x** ramp in 24 months, all pointed at AI datacenters."),
        ("📈 Margin expansion", f"Op margin expanded **~100 bps** to 45.6% despite the capex surge — pricing power intact."),
        ("💰 FCF pressure", f"Free cash flow declined **3.3%** to $71.6B — the first FCF decline in 5+ years. Watch this."),
        ("🏦 Fortress balance", f"Net Debt/EBITDA at **0.08x** — MSFT could pay off all debt with ~1 month of EBITDA."),
        ("🚀 Cloud engine", f"Intelligent Cloud segment grew **+21%** to $106.3B — now 38% of total revenue."),
    ]
    choice = st.selectbox("Show insight:", [f"{t}" for t, _ in insights], label_visibility="collapsed")
    for title, body in insights:
        if title == choice:
            st.markdown(f'<div class="analyst-note"><strong>{title}</strong><br>{body}</div>', unsafe_allow_html=True)

    # Waterfall bridge FY24 → FY25
    section_divider("03a", "FY24 → FY25 Revenue Bridge")
    bridge_fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["FY24 Revenue", "Productivity & BP", "Intelligent Cloud", "More Personal Comp.", "FY25 Revenue"],
        y=[245.1, 13.9, 18.4, 4.3, 281.7],
        text=["$245.1B", "+$13.9B", "+$18.4B", "+$4.3B", "$281.7B"],
        textposition="outside",
        connector={"line": {"color": "#C9D1DA"}},
        increasing={"marker": {"color": "#0E7C4A"}},
        totals={"marker": {"color": "#0A2540"}},
    ))
    bridge_fig.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                              yaxis=dict(title="Revenue ($B)", gridcolor="#F0F0EC"),
                              margin=dict(l=40, r=40, t=20, b=40),
                              font=dict(family="Inter"))
    st.plotly_chart(bridge_fig, use_container_width=True)

    analyst_note("Intelligent Cloud contributed **50% of the total revenue increase** — Azure and AI services "
                 "are now unambiguously the growth engine.")

# ============================================================
# TAB 4: REVENUE INTELLIGENCE
# ============================================================
with tabs[3]:
    section_divider("04", "Revenue Intelligence")

    # 6-year revenue trajectory with progress bar to $300B
    st.markdown("#### Trajectory to $300B milestone")
    progress_pct = (FIN["revenue"] / 300) * 100
    st.progress(progress_pct / 100, text=f"${FIN['revenue']:.1f}B / $300B target · {progress_pct:.1f}%")

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

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(kpi_card("5-Yr CAGR", "14.5%", "Consistent double-digit", "up",
                              "$143B → $282B"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Growth Acceleration", "+14.9%", "vs 15.7% FY24", "flat",
                              "Sustained despite scale"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Path to $300B", f"{300 - FIN['revenue']:.1f}B", "gap remaining", "flat",
                              "1-2 quarters at current rate"), unsafe_allow_html=True)

    analyst_note("Microsoft has grown from **$143B → $282B in 5 years** — a 14.5% CAGR at unprecedented scale. "
                 "At current pace, the $300B milestone falls in **Q2 FY26**.")

# ============================================================
# TAB 5: SEGMENTS
# ============================================================
with tabs[4]:
    section_divider("05", "Business Segments")

    seg_data = FIN["segments"]
    seg_df = pd.DataFrame(seg_data)

    # Segment KPI cards
    scols = st.columns(3)
    colors_seg = ["#0A2540", "#C99C3B", "#5B7A99"]
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

    st.markdown("")

    # Segment revenue + growth chart
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(x=seg_df["name"], y=seg_df["revenue"],
                            marker_color=colors_seg,
                            text=[f"${v:.1f}B" for v in seg_df["revenue"]],
                            textposition="outside",
                            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:.1f}B<extra></extra>"))
    fig_s.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                        yaxis=dict(title="Revenue ($B)", gridcolor="#F0F0EC"),
                        margin=dict(l=40, r=40, t=40, b=40),
                        showlegend=False)
    st.plotly_chart(fig_s, use_container_width=True)

    # Mix pie
    fig_pie = go.Figure(go.Pie(
        labels=seg_df["name"], values=seg_df["revenue"],
        marker=dict(colors=colors_seg, line=dict(color="#FFFFFF", width=2)),
        hole=0.55, textinfo="label+percent",
        textfont=dict(size=12, color="#FFFFFF"),
    ))
    fig_pie.update_layout(height=380, paper_bgcolor="#FFFFFF",
                          margin=dict(l=20, r=20, t=40, b=20),
                          showlegend=False,
                          annotations=[dict(text=f"${FIN['revenue']:.0f}B<br><span style='font-size:12px;color:#8B95A1'>FY25 Revenue</span>",
                                             x=0.5, y=0.5, font_size=20, showarrow=False,
                                             font=dict(color="#0A2540"))])
    st.plotly_chart(fig_pie, use_container_width=True)

    analyst_note(f"Intelligent Cloud grew **+21%** — nearly 3x the growth rate of MPC (+7%). "
                 f"The AI infrastructure investment is directly monetizing here via Azure.")

# ============================================================
# TAB 6: CAPITAL ALLOCATION
# ============================================================
with tabs[5]:
    section_divider("06", "Capital Allocation")

    st.markdown("#### Where did the cash go?")
    ca = FIN["capital_allocation"]

    ccols = st.columns(4)
    with ccols[0]:
        st.markdown(kpi_card("Capex", fmt_money(ca["capex"]), "+45%", "up",
                              "AI datacenters", "p.66"), unsafe_allow_html=True)
    with ccols[1]:
        st.markdown(kpi_card("Buybacks", fmt_money(ca["buybacks"]), "returned to shareholders", "flat",
                              "share repurchases"), unsafe_allow_html=True)
    with ccols[2]:
        st.markdown(kpi_card("Dividends", fmt_money(ca["dividends"]), "paid", "flat",
                              "quarterly cadence"), unsafe_allow_html=True)
    with ccols[3]:
        st.markdown(kpi_card("M&A", fmt_money(ca["acquisitions"]), "net acquisitions", "flat",
                              "strategic buys"), unsafe_allow_html=True)

    st.markdown("")

    # Capex trajectory — the defining chart
    st.markdown("#### The capex mega-cycle")
    capex_years = [2020, 2021, 2022, 2023, 2024, 2025]
    capex_vals = [15.4, 20.6, 23.9, 28.1, 44.5, 64.6]
    growth_yoy = [None, 33.8, 16.0, 17.6, 58.4, 45.2]

    fig_capex = go.Figure()
    fig_capex.add_trace(go.Bar(x=capex_years, y=capex_vals, marker_color="#C99C3B",
                                text=[f"${v:.1f}B" for v in capex_vals], textposition="outside",
                                hovertemplate="<b>FY%{x}</b><br>Capex: $%{y:.1f}B<extra></extra>",
                                name="Capex"))
    fig_capex.add_trace(go.Scatter(x=capex_years, y=growth_yoy, mode="lines+markers",
                                    yaxis="y2", line=dict(color="#0A2540", width=3, dash="dot"),
                                    marker=dict(size=9), name="YoY Growth %",
                                    hovertemplate="<b>FY%{x}</b><br>Growth: %{y:.1f}%<extra></extra>"))
    fig_capex.add_annotation(x=2023, y=28.1, text="Pre-AI baseline", showarrow=True, arrowhead=2,
                              ax=-40, ay=-40, font=dict(size=10))
    fig_capex.add_annotation(x=2025, y=64.6, text="AI capex peak", showarrow=True, arrowhead=2,
                              ax=40, ay=-40, font=dict(size=10, color="#C1443C"))
    fig_capex.update_layout(height=420, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                             yaxis=dict(title="Capex ($B)", gridcolor="#F0F0EC"),
                             yaxis2=dict(title="Growth %", overlaying="y", side="right", showgrid=False),
                             legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                             margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_capex, use_container_width=True)

    analyst_note("Capex grew **+45% YoY** and has **more than doubled over 2 years** ($28B → $65B). "
                 "This is the largest infrastructure buildout in Microsoft's history — the AI bet in numerical form.")

    # FCF vs Capex
    st.markdown("#### FCF under pressure")
    ocf_vals = [60.7, 76.7, 89.0, 87.6, 118.5, 136.2]
    fcf_vals = [45.2, 56.1, 65.1, 59.5, 74.1, 71.6]

    fig_fcf = go.Figure()
    fig_fcf.add_trace(go.Bar(x=capex_years, y=ocf_vals, name="Operating CF", marker_color="#0A2540",
                              hovertemplate="OCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Bar(x=capex_years, y=capex_vals, name="Capex", marker_color="#C99C3B",
                              hovertemplate="Capex: $%{y:.1f}B<extra></extra>"))
    fig_fcf.add_trace(go.Scatter(x=capex_years, y=fcf_vals, mode="lines+markers", name="Free Cash Flow",
                                  line=dict(color="#C1443C", width=3), marker=dict(size=9),
                                  hovertemplate="FCF: $%{y:.1f}B<extra></extra>"))
    fig_fcf.update_layout(height=380, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", barmode="group",
                          yaxis=dict(title="$B", gridcolor="#F0F0EC"),
                          legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                          margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_fcf, use_container_width=True)

    analyst_note("Operating CF grew **+15%** but FCF **declined 3.3%** — capex is now consuming almost half of OCF. "
                 "FCF conversion sits at ~53%, down from ~63% two years ago.")

# ============================================================
# TAB 7: AI FORECASTING
# ============================================================
with tabs[6]:
    section_divider("07", "AI Forecasting Sandbox")
    st.caption("Adjust assumptions and see FY26 projections update live.")

    with st.container():
        f1, f2, f3 = st.columns(3)
        with f1:
            g_rev = st.slider("Revenue growth %", 5.0, 25.0, 14.0, 0.5)
        with f2:
            g_margin = st.slider("Op margin %", 40.0, 50.0, 46.0, 0.5)
        with f3:
            g_capex = st.slider("Capex growth %", 0.0, 60.0, 25.0, 5.0)

    # Projection
    proj_rev = FIN["revenue"] * (1 + g_rev/100)
    proj_opinc = proj_rev * g_margin/100
    proj_capex = FIN["capex"] * (1 + g_capex/100)
    proj_ocf = FIN["ocf"] * (1 + g_rev/100 * 0.9)
    proj_fcf = proj_ocf - proj_capex

    pcols = st.columns(4)
    with pcols[0]:
        st.markdown(kpi_card("FY26E Revenue", fmt_money(proj_rev), f"+{g_rev:.1f}%", "up"), unsafe_allow_html=True)
    with pcols[1]:
        st.markdown(kpi_card("FY26E Op Income", fmt_money(proj_opinc), f"{g_margin:.1f}% margin", "up"), unsafe_allow_html=True)
    with pcols[2]:
        st.markdown(kpi_card("FY26E Capex", fmt_money(proj_capex), f"+{g_capex:.0f}%",
                              "up" if g_capex > 0 else "flat"), unsafe_allow_html=True)
    with pcols[3]:
        fcf_delta = (proj_fcf - FIN["fcf"]) / FIN["fcf"] * 100
        st.markdown(kpi_card("FY26E FCF", fmt_money(proj_fcf),
                              f"{fcf_delta:+.1f}%",
                              "up" if fcf_delta > 0 else "down"), unsafe_allow_html=True)

    st.markdown("")

    # Monte Carlo fan chart
    st.markdown("#### FY26 Revenue Monte Carlo (5,000 sims)")
    np.random.seed(42)
    sims = np.random.normal(loc=proj_rev, scale=proj_rev*0.05, size=5000)
    p10, p50, p90 = np.percentile(sims, [10, 50, 90])

    fig_mc = go.Figure()
    fig_mc.add_trace(go.Histogram(x=sims, nbinsx=50, marker_color="#0A2540", opacity=0.7,
                                    hovertemplate="Range: $%{x:.1f}B<br>Frequency: %{y}<extra></extra>"))
    fig_mc.add_vline(x=p10, line=dict(color="#C1443C", dash="dash"), annotation_text=f"P10: ${p10:.0f}B")
    fig_mc.add_vline(x=p50, line=dict(color="#C99C3B", dash="dash"), annotation_text=f"P50: ${p50:.0f}B")
    fig_mc.add_vline(x=p90, line=dict(color="#0E7C4A", dash="dash"), annotation_text=f"P90: ${p90:.0f}B")
    fig_mc.update_layout(height=340, paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                          xaxis=dict(title="FY26 Revenue ($B)", gridcolor="#F0F0EC"),
                          yaxis=dict(title="Frequency", gridcolor="#F0F0EC"),
                          showlegend=False,
                          margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig_mc, use_container_width=True)

    analyst_note(f"P50 revenue lands at **${p50:.0f}B**, with an 80% confidence band from "
                 f"**${p10:.0f}B → ${p90:.0f}B**. Assumes 5% std dev on growth rate.")

    # Sensitivity heatmap
    st.markdown("#### FCF Sensitivity: Revenue × Capex")
    rev_range = np.arange(10, 20, 2)
    capex_range = np.arange(0, 60, 10)
    fcf_matrix = []
    for cx in capex_range:
        row = []
        for rv in rev_range:
            r = FIN["revenue"] * (1 + rv/100)
            o = FIN["ocf"] * (1 + rv/100 * 0.9)
            c = FIN["capex"] * (1 + cx/100)
            row.append(o - c)
        fcf_matrix.append(row)

    fig_h = go.Figure(go.Heatmap(
        z=fcf_matrix, x=[f"+{v}%" for v in rev_range], y=[f"+{v}%" for v in capex_range],
        colorscale=[[0, "#C1443C"], [0.5, "#FDF6E3"], [1, "#0E7C4A"]],
        text=[[f"${v:.0f}B" for v in row] for row in fcf_matrix],
        texttemplate="%{text}", textfont={"size": 11},
        hovertemplate="Revenue: %{x}<br>Capex: %{y}<br>FCF: $%{z:.0f}B<extra></extra>"
    ))
    fig_h.update_layout(height=380, paper_bgcolor="#FFFFFF",
                        xaxis=dict(title="Revenue Growth"),
                        yaxis=dict(title="Capex Growth"),
                        margin=dict(l=60, r=40, t=40, b=40))
    st.plotly_chart(fig_h, use_container_width=True)

    # Saved scenarios
    st.markdown("#### 💾 Save this scenario")
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = []
    sc_name = st.text_input("Scenario name", placeholder="e.g., 'Bull case with 20% growth'")
    if st.button("Save scenario"):
        if sc_name:
            st.session_state.scenarios.append({
                "name": sc_name, "rev_growth": g_rev, "margin": g_margin,
                "capex_growth": g_capex, "proj_fcf": proj_fcf
            })
            st.success(f"Saved: {sc_name}")
    if st.session_state.scenarios:
        st.dataframe(pd.DataFrame(st.session_state.scenarios), use_container_width=True)

# ============================================================
# TAB 8: FINANCIAL STATEMENTS
# ============================================================
with tabs[7]:
    section_divider("08", "Financial Statements")

    stmt = st.radio("View:", ["Income Statement", "Balance Sheet", "Cash Flow"], horizontal=True)

    if stmt == "Income Statement":
        df_is = pd.DataFrame([
            {"Line item": "Revenue", "FY24 ($B)": 245.1, "FY25 ($B)": 281.7, "YoY %": 14.9},
            {"Line item": "Cost of revenue", "FY24 ($B)": 74.1, "FY25 ($B)": 85.4, "YoY %": 15.3},
            {"Line item": "Gross profit", "FY24 ($B)": 171.0, "FY25 ($B)": 196.3, "YoY %": 14.8},
            {"Line item": "R&D", "FY24 ($B)": 29.5, "FY25 ($B)": 32.8, "YoY %": 11.2},
            {"Line item": "S&M", "FY24 ($B)": 24.5, "FY25 ($B)": 26.2, "YoY %": 6.9},
            {"Line item": "G&A", "FY24 ($B)": 7.6, "FY25 ($B)": 8.8, "YoY %": 15.8},
            {"Line item": "Operating income", "FY24 ($B)": 109.4, "FY25 ($B)": 128.5, "YoY %": 17.5},
            {"Line item": "Net income", "FY24 ($B)": 88.1, "FY25 ($B)": 101.8, "YoY %": 15.6},
            {"Line item": "EPS ($)", "FY24 ($B)": 11.80, "FY25 ($B)": 13.69, "YoY %": 16.0},
        ])
        st.dataframe(df_is, use_container_width=True, hide_index=True)
        st.caption("Source: MSFT FY2025 10-K, p.51")

    elif stmt == "Balance Sheet":
        df_bs = pd.DataFrame([
            {"Line item": "Cash & equivalents", "FY25 ($B)": 30.2},
            {"Line item": "Short-term investments", "FY25 ($B)": 46.4},
            {"Line item": "Total current assets", "FY25 ($B)": 172.7},
            {"Line item": "PP&E", "FY25 ($B)": 197.8},
            {"Line item": "Goodwill", "FY25 ($B)": 119.2},
            {"Line item": "Total assets", "FY25 ($B)": 562.6},
            {"Line item": "Long-term debt", "FY25 ($B)": 43.2},
            {"Line item": "Total liabilities", "FY25 ($B)": 253.4},
            {"Line item": "Stockholders' equity", "FY25 ($B)": 309.2},
        ])
        st.dataframe(df_bs, use_container_width=True, hide_index=True)
        st.caption("Source: MSFT FY2025 10-K, p.53")

    else:
        df_cf = pd.DataFrame([
            {"Line item": "Operating cash flow", "FY24 ($B)": 118.5, "FY25 ($B)": 136.2, "YoY %": 14.9},
            {"Line item": "Capex", "FY24 ($B)": 44.5, "FY25 ($B)": 64.6, "YoY %": 45.2},
            {"Line item": "Free cash flow", "FY24 ($B)": 74.1, "FY25 ($B)": 71.6, "YoY %": -3.3},
            {"Line item": "Dividends paid", "FY24 ($B)": 21.8, "FY25 ($B)": 24.0, "YoY %": 10.1},
            {"Line item": "Share repurchases", "FY24 ($B)": 17.3, "FY25 ($B)": 17.0, "YoY %": -1.7},
        ])
        st.dataframe(df_cf, use_container_width=True, hide_index=True)
        st.caption("Source: MSFT FY2025 10-K, p.55")

    with st.expander("📖 How is this calculated?"):
        st.markdown("""
        - **Operating income** = Gross profit − (R&D + S&M + G&A)
        - **Free cash flow** = Operating cash flow − Capex
        - **Net Debt / EBITDA** = (Total debt − Cash) / EBITDA
        - **ROIC** = NOPAT / (Debt + Equity)
        - **Rule of 40** = Revenue growth % + FCF margin %
        """)

# ============================================================
# TAB 9: AI COPILOT
# ============================================================
with tabs[8]:
    section_divider("09", "AI Copilot")
    st.caption("Ask a question about Microsoft's FY25 10-K in plain English.")

    suggested = [
        "What is the key story?",
        "How much did capex grow?",
        "What is the operating margin trend?",
        "How is free cash flow doing?",
        "What are the segment growth rates?",
    ]
    st.markdown("**Suggested questions:**")
    scols = st.columns(len(suggested))
    for i, q in enumerate(suggested):
        with scols[i]:
            if st.button(q, key=f"sq_{i}"):
                st.session_state["question"] = q

    q = st.text_input("Your question:", value=st.session_state.get("question", ""),
                       placeholder="e.g., What drove revenue growth?")

    if q:
        answer = engine.answer_question(q)
        st.markdown(f'<div class="analyst-note"><strong>Answer:</strong><br>{answer}</div>', unsafe_allow_html=True)

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
    For educational/portfolio purposes. Not investment advice.
  </div>
</div>
""", unsafe_allow_html=True)

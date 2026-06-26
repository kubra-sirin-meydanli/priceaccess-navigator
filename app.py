import streamlit as st
import plotly.graph_objects as go
from load_data import load_prices, load_assumptions
from engine import run_cascade, prices as engine_prices, baskets
from impact import compute_impact
from narrative import generate_narrative

# --- PAGE CONFIG ---
st.set_page_config(page_title="PriceAccess Navigator", layout="wide")

# --- SESSION STATE ---
if "results" not in st.session_state:
    st.session_state.results = None
if "trigger_market" not in st.session_state:
    st.session_state.trigger_market = None
if "new_price" not in st.session_state:
    st.session_state.new_price = None
if "narrative" not in st.session_state:
    st.session_state.narrative = None

# --- CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: #f0ede8;
    }

    #MainMenu, footer, header { visibility: hidden; }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }

    /* Hide radio buttons, show only labels as pills */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row !important;
        gap: 4px;
        align-items: center;
        background-color: #f0ede8;
        padding: 14px 48px;
        border-bottom: 0.5px solid #e0ddd6;
        position: sticky;
        top: 0;
        z-index: 100;
    }

    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        padding: 8px 20px !important;
        border-radius: 30px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        color: #888884 !important;
        background: none !important;
        border: none !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }

    div[role="radiogroup"] label:has(input:checked) {
        background-color: #1a1a18 !important;
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    div[role="radiogroup"] label:hover:not(:has(input:checked)) {
        color: #1a1a18 !important;
    }

    /* Hide the actual radio circles */
    div[role="radiogroup"] input[type="radio"] {
        display: none !important;
    }

    /* Hide streamlit's default radio container label */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }

    /* Hero section */
    .hero {
        padding: 4rem 4rem 2.5rem 4rem;
        background-color: #f0ede8;
    }
    .hero-step {
        font-size: 13px;
        color: #888884;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 42px;
        font-weight: 400;
        color: #1a1a18;
        line-height: 1.15;
        margin-bottom: 14px;
        letter-spacing: -0.3px;
    }
    .hero-subtitle {
        font-size: 15px;
        color: #555553;
        line-height: 1.6;
        max-width: 520px;
    }

    /* Content area */
    .content {
        padding: 2rem 4rem 4rem 4rem;
        background-color: #ffffff;
        min-height: 60vh;
    }

    /* Section label */
    .section-label {
        font-size: 10px;
        font-weight: 600;
        color: #bbb9b4;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 12px;
        margin-top: 0;
        display: block;
    }

    /* Table */
    .price-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .price-table th {
        text-align: left;
        font-size: 10px;
        font-weight: 600;
        color: #888884;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 9px 10px;
        background-color: #f9f8f5;
        border-bottom: 0.5px solid #e8e6e1;
    }
    .price-table th.right { text-align: right; }
    .price-table td {
        padding: 10px 10px;
        border-bottom: 0.5px solid #f0ede8;
        color: #555553;
        vertical-align: middle;
        font-size: 13px;
    }
    .price-table td.right { text-align: right; }
    .price-table td.market { font-weight: 500; color: #1a1a18; }
    .price-table td.price { font-weight: 500; color: #1a1a18; text-align: right; }
    .price-table td.affected { color: #c0392b; font-weight: 500; }
    .price-table td.delta-neg { color: #c0392b; text-align: right; }
    .price-table td.neutral { color: #999896; text-align: right; }
    .price-table tr.total-row td {
        font-weight: 600;
        color: #1a1a18;
        border-top: 0.5px solid #e8e6e1;
        border-bottom: none;
        padding-top: 12px;
        background-color: #f9f8f5;
    }
    .price-table tr.total-row td.delta-neg { color: #c0392b; }

    /* Pill */
    .pill {
        display: inline-block;
        font-size: 10px;
        padding: 3px 9px;
        border-radius: 20px;
        background: #f0ede8;
        color: #888884;
        border: 0.5px solid #e0ddd6;
    }
    .pill-warning {
        background: #fdf3e3;
        color: #9a6200;
        border: 0.5px solid #f5dfa0;
    }

    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 28px;
    }
    .metric-card {
        background: #f9f8f5;
        border-radius: 8px;
        padding: 16px 18px;
    }
    .metric-label {
        font-size: 11px;
        color: #999896;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 400;
        color: #1a1a18;
        line-height: 1;
    }
    .metric-value-neg { color: #c0392b; }
    .metric-sub {
        font-size: 11px;
        color: #999896;
        margin-top: 4px;
    }

    /* Narrative */
    .narrative-box {
        background: #f9f8f5;
        border-radius: 8px;
        padding: 24px 28px;
        font-size: 13px;
        color: #2C2C2A;
        line-height: 1.8;
        margin-top: 16px;
        white-space: pre-line;
    }

    /* Button */
    .stButton > button {
        background-color: #1a1a18 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 10px 28px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }
    .stButton > button:hover {
        background-color: #333330 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-size: 11px !important;
        color: #888884 !important;
        font-weight: 500 !important;
    }

    /* Input labels */
    .stSelectbox label, .stNumberInput label {
        font-size: 11px !important;
        color: #888884 !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    .stMarkdown p { margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# --- NAV BAR ---
step = st.radio(
    "nav",
    ["1. Where are we today?", "2. What are we modelling?", "3. What is the impact?"],
    horizontal=True,
    label_visibility="hidden"
)

# ─────────────────────────────────────────
# STEP 1
# ─────────────────────────────────────────
if step == "1. Where are we today?":

    st.markdown("""
    <div class="hero">
        <p class="hero-step">Step 1</p>
        <p class="hero-title">Where are we today?</p>
        <p class="hero-subtitle">Current list prices and IRP basket roles across all 6 markets. These are the baseline prices the cascade starts from.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content">', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Current list prices</span>', unsafe_allow_html=True)

    st.markdown("""
    <table class="price-table">
        <thead>
            <tr>
                <th style="width:8%">Market</th>
                <th>Regulatory anchor</th>
                <th class="right">IRP basket role</th>
                <th class="right">List price (€)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="market">DE</td>
                <td>AMNOG · G-BA</td>
                <td class="right"><span class="pill">Free pricing · not referenced</span></td>
                <td class="price">1,164</td>
            </tr>
            <tr>
                <td class="market">FR</td>
                <td>CEPS · HAS</td>
                <td class="right"><span class="pill pill-warning">Referenced by NL · MIN rule</span></td>
                <td class="price">620</td>
            </tr>
            <tr>
                <td class="market">NL</td>
                <td>ZIN · WGP</td>
                <td class="right"><span class="pill">Inbound only · MIN(ES, FR)</span></td>
                <td class="price">582</td>
            </tr>
            <tr>
                <td class="market">UK</td>
                <td>NICE · free pricing</td>
                <td class="right"><span class="pill">Free pricing · not referenced</span></td>
                <td class="price">700</td>
            </tr>
            <tr>
                <td class="market">ES</td>
                <td>CIPM · Ministerio</td>
                <td class="right"><span class="pill pill-warning">Referenced by FR · NL</span></td>
                <td class="price">560</td>
            </tr>
            <tr>
                <td class="market">TR</td>
                <td>TİTCK · SGK · sabit kur</td>
                <td class="right"><span class="pill">Inbound only · isolated</span></td>
                <td class="price">195</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Commercial assumptions</span>', unsafe_allow_html=True)

    with st.expander("Defaults loaded · Vol Y1: 3,000–12,000 units · GTN: 12–30% · GM: 68–73% · Growth: 3–5% · Lag: 0–2 years"):
        st.markdown("""
        <table class="price-table">
            <thead>
                <tr>
                    <th style="width:8%">Market</th>
                    <th class="right">Vol Y1 (units)</th>
                    <th class="right">GTN%</th>
                    <th class="right">GM%</th>
                    <th class="right">YoY growth%</th>
                    <th class="right">Transmission lag</th>
                </tr>
            </thead>
            <tbody>
                <tr><td class="market">DE</td><td class="right">12,000</td><td class="right">15%</td><td class="right">72%</td><td class="right">5%</td><td class="right">Year 1</td></tr>
                <tr><td class="market">FR</td><td class="right">9,000</td><td class="right">22%</td><td class="right">70%</td><td class="right">4%</td><td class="right">Year 2</td></tr>
                <tr><td class="market">NL</td><td class="right">4,000</td><td class="right">18%</td><td class="right">71%</td><td class="right">4%</td><td class="right">Year 3</td></tr>
                <tr><td class="market">UK</td><td class="right">8,000</td><td class="right">12%</td><td class="right">73%</td><td class="right">5%</td><td class="right">Year 1</td></tr>
                <tr><td class="market">ES</td><td class="right">6,000</td><td class="right">18%</td><td class="right">70%</td><td class="right">4%</td><td class="right">Year 1</td></tr>
                <tr><td class="market">TR</td><td class="right">3,000</td><td class="right">30%</td><td class="right">68%</td><td class="right">3%</td><td class="right">Year 1</td></tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)
        st.caption("Transmission lag: year from which cascade price takes effect.")

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# STEP 2
# ─────────────────────────────────────────
elif step == "2. What are we modelling?":

    st.markdown("""
    <div class="hero">
        <p class="hero-step">Step 2</p>
        <p class="hero-title">What are we modelling?</p>
        <p class="hero-subtitle">Define the mandatory price cut — trigger market, regulatory cause, and new list price.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content">', unsafe_allow_html=True)
    st.markdown('<span class="section-label">Cascade inputs</span>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        trigger_market = st.selectbox("Trigger market", ["ES", "DE", "FR", "NL", "UK", "TR"])
    with col2:
        trigger_type = st.selectbox("Mandatory trigger", ["CIPM price cut", "CEPS price cut", "AMNOG outcome", "TİTCK revision"])
    with col3:
        new_price = st.number_input("New list price (€)", min_value=0.0, value=400.0, step=10.0)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Run cascade →", type="primary"):
        with st.spinner("Running cascade..."):
            rows = compute_impact(trigger_market, new_price)
            st.session_state.results = rows
            st.session_state.trigger_market = trigger_market
            st.session_state.new_price = new_price
            st.session_state.narrative = None
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# STEP 3
# ─────────────────────────────────────────
elif step == "3. What is the impact?":

    st.markdown("""
    <div class="hero">
        <p class="hero-step">Step 3</p>
        <p class="hero-title">What is the impact?</p>
        <p class="hero-subtitle">Price transmission across IRP baskets · 3-year commercial impact · affected markets highlighted in red.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content">', unsafe_allow_html=True)

    if st.session_state.results is None:
        st.info("Run the cascade in Step 2 to see results here.")
    else:
        rows = st.session_state.results
        trigger_market = st.session_state.trigger_market
        new_price = st.session_state.new_price

        # Totals
        total_ns_asis = sum(r["ns_asis"] for r in rows)
        total_gm_asis = sum(r["gm_asis"] for r in rows)
        total_ns_after = sum(r["ns_after"] for r in rows)
        total_gm_after = sum(r["gm_after"] for r in rows)
        total_delta_ns = sum(r["delta_ns"] for r in rows)
        total_delta_gm = sum(r["delta_gm"] for r in rows)
        total_delta_ns_pct = round(total_delta_ns / total_ns_asis * 100, 1)
        total_delta_gm_pct = round(total_delta_gm / total_gm_asis * 100, 1)
        affected = [r["market"] for r in rows if r["delta_ns"] != 0]

        # Trigger market price drop %
        from_price = [r for r in rows if r["market"] == trigger_market][0]
        prices_loaded = load_prices()
        original_price = prices_loaded[trigger_market]
        price_drop_pct = round((new_price - original_price) / original_price * 100, 1)

        # Metric cards
        st.markdown('<span class="section-label">Portfolio impact — 3-year summary</span>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <p class="metric-label">Markets affected</p>
                <p class="metric-value">{len(affected)} / 6</p>
                <p class="metric-sub">{' · '.join(affected)}</p>
            </div>
            <div class="metric-card">
                <p class="metric-label">Max price drop</p>
                <p class="metric-value metric-value-neg">{price_drop_pct}%</p>
                <p class="metric-sub">{trigger_market} · €{original_price:,.0f} → €{new_price:,.0f}</p>
            </div>
            <div class="metric-card">
                <p class="metric-label">Δ Net sales 3Y</p>
                <p class="metric-value metric-value-neg">−€{abs(total_delta_ns):,.0f}</p>
                <p class="metric-sub">{total_delta_ns_pct}% vs as-is portfolio</p>
            </div>
            <div class="metric-card">
                <p class="metric-label">Δ Gross margin 3Y</p>
                <p class="metric-value metric-value-neg">−€{abs(total_delta_gm):,.0f}</p>
                <p class="metric-sub">{total_delta_gm_pct}% vs as-is portfolio</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Unified table
        st.markdown('<span class="section-label">Market-by-market breakdown</span>', unsafe_allow_html=True)

        table_rows = ""
        for r in rows:
            is_affected = r["delta_ns"] != 0
            mkt_class = "affected" if is_affected else "market"
            delta_class = "delta-neg" if is_affected else "neutral"
            dash = "—"
            table_rows += f"""
            <tr>
                <td class="{mkt_class}">{r['market']}</td>
                <td class="right">€{r['ns_asis']:,.0f}</td>
                <td class="right">€{r['gm_asis']:,.0f}</td>
                <td class="right">€{r['ns_after']:,.0f}</td>
                <td class="right">€{r['gm_after']:,.0f}</td>
                <td class="{delta_class}">{"−€{:,.0f}".format(abs(r['delta_ns'])) if is_affected else dash}</td>
                <td class="{delta_class}">{"{}%".format(r['delta_ns_pct']) if is_affected else dash}</td>
                <td class="{delta_class}">{"−€{:,.0f}".format(abs(r['delta_gm'])) if is_affected else dash}</td>
                <td class="{delta_class}">{"{}%".format(r['delta_gm_pct']) if is_affected else dash}</td>
            </tr>"""

        st.markdown(f"""
        <table class="price-table">
            <thead>
                <tr>
                    <th rowspan="2" style="width:7%;vertical-align:bottom;">Market</th>
                    <th colspan="2" class="right" style="border-bottom:none;padding-bottom:2px;">As is — 3Y</th>
                    <th colspan="2" class="right" style="border-bottom:none;padding-bottom:2px;">After change — 3Y</th>
                    <th colspan="4" class="right" style="border-bottom:none;padding-bottom:2px;color:#c0392b;">Delta — value at risk</th>
                </tr>
                <tr>
                    <th class="right">NS 3Y</th>
                    <th class="right">GM 3Y</th>
                    <th class="right">NS 3Y</th>
                    <th class="right">GM 3Y</th>
                    <th class="right">ΔNS</th>
                    <th class="right">ΔNS%</th>
                    <th class="right">ΔGM</th>
                    <th class="right">ΔGM%</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
                <tr class="total-row">
                    <td>Total</td>
                    <td class="right">€{total_ns_asis:,.0f}</td>
                    <td class="right">€{total_gm_asis:,.0f}</td>
                    <td class="right">€{total_ns_after:,.0f}</td>
                    <td class="right">€{total_gm_after:,.0f}</td>
                    <td class="delta-neg">−€{abs(total_delta_ns):,.0f}</td>
                    <td class="delta-neg">{total_delta_ns_pct}%</td>
                    <td class="delta-neg">−€{abs(total_delta_gm):,.0f}</td>
                    <td class="delta-neg">{total_delta_gm_pct}%</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

        # Chart
        st.markdown('<span class="section-label" style="display:block;margin-top:28px;">3-year impact by market</span>', unsafe_allow_html=True)
        chart_metric = st.radio("View", ["Net sales", "Gross margin"], horizontal=True, label_visibility="collapsed", key="chart_toggle")

        markets = [r["market"] for r in rows]
        if chart_metric == "Net sales":
            asis_vals = [r["ns_asis"] for r in rows]
            after_vals = [r["ns_after"] for r in rows]
            y_label = "Net Sales 3Y (€)"
        else:
            asis_vals = [r["gm_asis"] for r in rows]
            after_vals = [r["gm_after"] for r in rows]
            y_label = "Gross Margin 3Y (€)"

        after_colors = ["#c0392b" if m in affected else "#c8c4bc" for m in markets]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="As is",
            x=markets,
            y=asis_vals,
            marker_color="#1a1a18",
            opacity=0.15,
        ))
        fig.add_trace(go.Bar(
            name="After change",
            x=markets,
            y=after_vals,
            marker_color=after_colors,
        ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=12, color="#555553"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=32, b=0),
            yaxis=dict(title=y_label, gridcolor="#f0ede8", gridwidth=0.5),
            xaxis=dict(title=""),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)

        # AI Narrative
        st.markdown('<span class="section-label" style="display:block;margin-top:8px;">AI narrative summary</span>', unsafe_allow_html=True)
        st.caption("Plain-English leadership memo · powered by Claude API · one deliberate click")

        if st.session_state.narrative:
            st.markdown(f'<div class="narrative-box">{st.session_state.narrative}</div>', unsafe_allow_html=True)

        if st.button("Generate summary →", type="primary"):
            with st.spinner("Generating narrative..."):
                narrative = generate_narrative(trigger_market, new_price, rows)
                st.session_state.narrative = narrative
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
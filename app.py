import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from impact import compute_impact
from narrative import generate_narrative

st.set_page_config(page_title="PriceAccess Navigator", layout="wide")

# ── static baseline prices (used in Step 3 metric cards) ──────
BASELINES = {"DE": 1164, "FR": 620, "NL": 582, "UK": 700, "ES": 560, "TR": 195}
TRIGGERS  = {
    "DE": "AMNOG outcome",   "FR": "CEPS price cut",  "NL": "ZIN · WGP review",
    "UK": "NICE appraisal",  "ES": "CIPM price cut",  "TR": "TİTCK revision",
}

# ── default commercial assumptions ────────────────────────────
DEFAULT_ASSUMPTIONS = pd.DataFrame([
    {"Market": "DE", "Vol Y1": 12000, "GTN%": 15.0, "GM%": 72.0, "YoY growth%": 5.0, "Lag (years)": 0},
    {"Market": "FR", "Vol Y1":  9000, "GTN%": 22.0, "GM%": 70.0, "YoY growth%": 4.0, "Lag (years)": 1},
    {"Market": "NL", "Vol Y1":  4000, "GTN%": 18.0, "GM%": 71.0, "YoY growth%": 4.0, "Lag (years)": 2},
    {"Market": "UK", "Vol Y1":  8000, "GTN%": 12.0, "GM%": 73.0, "YoY growth%": 5.0, "Lag (years)": 0},
    {"Market": "ES", "Vol Y1":  6000, "GTN%": 18.0, "GM%": 70.0, "YoY growth%": 4.0, "Lag (years)": 0},
    {"Market": "TR", "Vol Y1":  3000, "GTN%": 30.0, "GM%": 68.0, "YoY growth%": 3.0, "Lag (years)": 0},
])

# ── session defaults ───────────────────────────────────────────
for k, v in {"results": None, "trigger_market": "ES", "new_price": 400.0, "narrative": None, "prev_mode": "Demo data"}.items():
    if k not in st.session_state:
        st.session_state[k] = v
if "assumptions_df" not in st.session_state:
    st.session_state.assumptions_df = DEFAULT_ASSUMPTIONS.copy()


def _on_mode_change():
    """on_change callback for the mode segmented control.
    Runs before the next script rerun, so session_state modifications are legal here.
    Reverts Upload Excel (not yet built) to whichever valid mode was active before.
    """
    val = st.session_state.input_mode_seg
    if val is None or val == "Upload Excel":
        st.session_state.input_mode_seg = st.session_state.prev_mode
    else:
        st.session_state.prev_mode = val


def df_to_assumptions(df: pd.DataFrame) -> dict:
    """Convert the editable DataFrame to the dict format compute_impact expects."""
    return {
        row["Market"]: {
            "vol_y1":                int(row["Vol Y1"]),
            "gtn_pct":               row["GTN%"] / 100.0,
            "gm_pct":                row["GM%"] / 100.0,
            "vol_growth_pct":        row["YoY growth%"] / 100.0,
            "transmission_lag_years": int(row["Lag (years)"]),
        }
        for _, row in df.iterrows()
    }


# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
hr { display: none !important; }

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background-color: #f5f4f0;
}
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Remove lateral padding from Streamlit's outer shell so nav reaches full page width */
[data-testid="stMain"],
section.main { padding-left: 0 !important; padding-right: 0 !important; }

/* Kill Streamlit's default inter-element gap; our padding controls spacing */
[data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stMarkdownContainer"] > * { margin-top: 0 !important; margin-bottom: 0 !important; }

/* ── NAV PILLS ── */
div[role="radiogroup"] {
    display: flex;
    flex-direction: row !important;
    align-items: center;
    background-color: #f5f4f0;
    padding: 10px 48px;
    border-bottom: 0.5px solid #e0ddd6;
    position: sticky;
    top: 0;
    z-index: 100;
    width: 100%;
    box-sizing: border-box;
    gap: 0;
}
div[role="radiogroup"] label {
    flex: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 8px 20px !important;
    border-radius: 30px !important;
    cursor: pointer !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    color: #999896 !important;
    background: none !important;
    border: none !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
    text-align: center !important;
}
div[role="radiogroup"] label:has(input:checked) {
    background-color: #1a1a18 !important;
    color: #ffffff !important;
    font-weight: 500 !important;
}
/* Cascade white to every child of the selected pill —
   Streamlit's emotion CSS can override parent color on inner <p>/<div> */
div[role="radiogroup"] label:has(input:checked) p,
div[role="radiogroup"] label:has(input:checked) span,
div[role="radiogroup"] label:has(input:checked) div { color: #ffffff !important; }
div[role="radiogroup"] label:hover:not(:has(input:checked)) { color: #1a1a18 !important; }
/* Hide the native radio input */
div[role="radiogroup"] input[type="radio"] { display: none !important; }
div[role="radiogroup"] svg                 { display: none !important; }
/* Recolor the SELECTED indicator dot to near-black so it blends with the dark pill.
   input:checked still works as a CSS hook even when the input is display:none —
   the sibling + child combinators target the visual indicator div sitting next to it. */
div[role="radiogroup"] input[type="radio"]:checked + div { border-color: #2a2a28 !important; }
div[role="radiogroup"] input[type="radio"]:checked + div > div { background-color: #2a2a28 !important; }
div[data-testid="stRadio"] > label { display: none !important; }

/* ── IN-CONTENT RADIOS (mode toggle, chart toggle) ── */
div[data-testid="element-container"]:not(:first-child) div[role="radiogroup"] {
    position: static !important;
    padding: 3px !important;
    background-color: #eceae6 !important;
    border-bottom: none !important;
    border-radius: 8px !important;
    width: fit-content !important;
    z-index: auto !important;
}
div[data-testid="element-container"]:not(:first-child) div[role="radiogroup"] label {
    flex: 0 !important;
    padding: 5px 15px !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    color: #888884 !important;
    font-weight: 400 !important;
    justify-content: flex-start !important;
}
div[data-testid="element-container"]:not(:first-child) div[role="radiogroup"] label:has(input:checked) {
    background-color: #ffffff !important;
    color: #1a1a18 !important;
    font-weight: 500 !important;
}

/* ── LAYOUT ── */
.hero { padding: 36px 48px 24px 48px; background-color: #f5f4f0; }
.hero-step { font-size: 10px; font-weight: 600; color: #bbb9b4; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
.hero-title { font-size: 34px; font-weight: 400; color: #1a1a18; line-height: 1.15; margin-bottom: 10px; letter-spacing: -0.3px; }
.hero-sub { font-size: 14px; color: #444442; line-height: 1.65; max-width: 480px; }
.content { padding: 28px 48px 32px 48px; background-color: #ffffff; }
.sl { display: block; font-size: 10px; font-weight: 600; color: #bbb9b4; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px; margin-top: 0; }

/* ── TABLE ── */
.t { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: auto; border-top: 0.5px solid #e8e6e1; }
.t th { text-align: left; font-size: 10px; font-weight: 600; color: #888886; text-transform: uppercase; letter-spacing: 0.05em; padding: 9px 12px; background-color: #f9f8f5; border-bottom: 0.5px solid #e8e6e1; white-space: nowrap; }
.t th.r { text-align: right; }
.t td { padding: 10px 12px; border-bottom: 0.5px solid #f0ede8; color: #3d3d3b; font-size: 13px; vertical-align: middle; }
.t td.r { text-align: right; }
.t td.m  { font-weight: 500; color: #1a1a18; }
.t td.p  { font-weight: 500; color: #1a1a18; text-align: right; }
.t td.aff { color: #8C3B2A; font-weight: 500; }
.t td.neg { color: #8C3B2A; text-align: right; }
.t td.neu { color: #c8c4bc; text-align: right; }
.t tr.tot td { font-weight: 600; color: #1a1a18; border-top: 0.5px solid #e8e6e1; border-bottom: none; padding-top: 12px; background-color: #f9f8f5; }
.t tr.tot td.neg { color: #8C3B2A; }

/* ── PILLS ── */
.pill   { display: inline-block; font-size: 10px; padding: 4px 10px; border-radius: 20px; background: #f0ede8; color: #999896; border: 0.5px solid #e0ddd6; white-space: nowrap; }
.pill-w { background: #fdf3e3; color: #9a6200; border: 0.5px solid #f5dfa0; }

/* ── STEP 2: SEGMENTED CONTROL ── */
div[data-testid="stSegmentedControl"] {
    padding: 20px 48px 20px 48px !important;
}
/* Hide the auto-generated label (we use label_visibility="hidden" too) */
div[data-testid="stSegmentedControl"] > label { display: none !important; }
/* Upload Excel: visually muted; pointer-events left ON so Python can detect
   the click and revert via session_state + st.rerun() */
div[data-testid="stSegmentedControl"] button:last-of-type {
    opacity: 0.38 !important;
    cursor: not-allowed !important;
}
/* Run button: white background, left-aligned with content area */
.stButton {
    background-color: #ffffff !important;
    padding: 16px 0 28px 48px !important;
}
/* Edit manually: constrain st.columns() to content width with white background */
[data-testid="stHorizontalBlock"] {
    padding: 0 48px 24px 48px !important;
    background-color: #ffffff !important;
}

/* ── METRIC CARDS ── */
.mg { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 28px; }
.mc { background: #f9f8f5; border-radius: 8px; padding: 16px 18px; }
.ml { font-size: 10px; color: #999896; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.mv   { font-size: 26px; font-weight: 400; color: #1a1a18; line-height: 1; }
.mv-r { color: #8C3B2A; }
.ms   { font-size: 11px; color: #999896; margin-top: 5px; }

/* ── NARRATIVE ── */
.narr { background: #f9f8f5; border-radius: 8px; padding: 22px 26px; font-size: 13px; color: #2C2C2A; line-height: 1.8; margin-top: 12px; white-space: pre-line; }

/* ── BUTTONS ── */
.stButton > button {
    border-radius: 30px !important; font-size: 13px !important;
    font-weight: 500 !important; border: none !important; padding: 10px 28px !important;
}
button[kind="primary"],
button[data-testid="baseButton-primary"] { background-color: #1a1a18 !important; color: #ffffff !important; }
button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover { background-color: #333330 !important; }
button[kind="secondary"],
button[data-testid="baseButton-secondary"] {
    background-color: transparent !important; color: #888884 !important;
    border: 0.5px solid #e0ddd6 !important;
}

/* ── ASSUMPTIONS EDITOR SECTION ── */
.assump-hd {
    display: block; background: #ffffff;
    padding: 24px 48px 6px 48px;
    font-size: 10px; font-weight: 600; color: #bbb9b4;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.assump-note {
    display: block; background: #ffffff;
    padding: 0 48px 24px 48px;
    font-size: 11px; color: #888884;
}
/* Data editor sits inside the expander — expander details already give 48px padding,
   so zero out any extra margin to avoid double-indentation */
[data-testid="stExpander"] [data-testid="stDataFrame"],
[data-testid="stExpander"] [data-testid="stDataEditor"] { margin: 0 0 12px 0 !important; }

/* ── EXPANDER (unused in Step 1 now, kept for safety) ── */
[data-testid="stExpander"] {
    border: none !important; border-bottom: 0.5px solid #e8e6e1 !important;
    border-radius: 0 !important; box-shadow: none !important; background: #ffffff !important;
}
[data-testid="stExpander"] summary { font-size: 11px !important; color: #888884 !important; padding: 13px 48px !important; background: #ffffff !important; }
[data-testid="stExpanderDetails"] { padding: 0 48px 20px 48px !important; }
[data-testid="stExpander"] details > div { padding: 0 48px 20px 48px !important; }

/* ── INPUT LABELS ── */
.stSelectbox label, .stNumberInput label, .stFileUploader label {
    font-size: 10px !important; color: #999896 !important;
    font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important;
}
.stMarkdown p { margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)

# ── NAV ───────────────────────────────────────────────────────
step = st.radio(
    "nav",
    ["1  Where are we today?", "2  What are we modelling?", "3  What is the impact?"],
    horizontal=True,
    label_visibility="hidden",
)

# ─────────────────────────────────────────────────────────────
# STEP 1
# ─────────────────────────────────────────────────────────────
if step == "1  Where are we today?":

    # Hero + IRP table in one block so the divs actually wrap content
    st.markdown("""
    <div class="hero">
      <p class="hero-step">Step 1</p>
      <p class="hero-title">Where are we today?</p>
      <p class="hero-sub">Current list prices and IRP basket roles across all six markets. These are the baseline prices the cascade starts from.</p>
    </div>
    <div class="content">
      <span class="sl">Current prices &amp; IRP basket roles</span>
      <table class="t">
        <colgroup>
          <col style="width:70px">
          <col>
          <col style="width:220px">
          <col style="width:120px">
        </colgroup>
        <thead>
          <tr>
            <th>Market</th>
            <th>Regulatory anchor</th>
            <th>IRP basket role</th>
            <th class="r">List price (€)</th>
          </tr>
        </thead>
        <tbody>
          <tr><td class="m">DE</td><td>AMNOG · G-BA</td><td><span class="pill">Free pricing · not referenced</span></td><td class="p">1,164</td></tr>
          <tr><td class="m">FR</td><td>CEPS · HAS</td><td><span class="pill pill-w">Referenced by NL · MIN rule</span></td><td class="p">620</td></tr>
          <tr><td class="m">NL</td><td>ZIN · WGP</td><td><span class="pill">Inbound only · MIN(ES, FR)</span></td><td class="p">582</td></tr>
          <tr><td class="m">UK</td><td>NICE · free pricing</td><td><span class="pill">Free pricing · not referenced</span></td><td class="p">700</td></tr>
          <tr><td class="m">ES</td><td>CIPM · Ministerio</td><td><span class="pill pill-w">Referenced by FR · NL</span></td><td class="p">560</td></tr>
          <tr><td class="m">TR</td><td>TİTCK · SGK · sabit kur</td><td><span class="pill">Inbound only · isolated</span></td><td class="p">195</td></tr>
        </tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)

    # Assumptions section header + note
    st.markdown("""
    <span class="assump-hd">Commercial assumptions</span>
    <span class="assump-note">Editable — adjust to override demo defaults. Changes apply when you run the cascade in Step 2.</span>
    """, unsafe_allow_html=True)

    col_cfg = {
        "Market":      st.column_config.TextColumn("Market",     disabled=True, width="small"),
        "Vol Y1":      st.column_config.NumberColumn("Vol Y1",   min_value=0,   max_value=200000, step=500,  format="%d",   width="medium"),
        "GTN%":        st.column_config.NumberColumn("GTN%",     min_value=0.0, max_value=100.0,  step=0.5,  format="%.1f", width="small"),
        "GM%":         st.column_config.NumberColumn("GM%",      min_value=0.0, max_value=100.0,  step=0.5,  format="%.1f", width="small"),
        "YoY growth%": st.column_config.NumberColumn("YoY gr%",  min_value=0.0, max_value=50.0,   step=0.5,  format="%.1f", width="small"),
        "Lag (years)": st.column_config.NumberColumn("Lag (yrs)", min_value=0,  max_value=10,     step=1,    format="%d",   width="small"),
    }

    with st.expander("6 markets · click to edit", expanded=False):
        edited = st.data_editor(
            st.session_state.assumptions_df,
            column_config=col_cfg,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
        )
        st.session_state.assumptions_df = edited

# ─────────────────────────────────────────────────────────────
# STEP 2
# ─────────────────────────────────────────────────────────────
elif step == "2  What are we modelling?":
    st.markdown("""
    <div class="hero">
      <p class="hero-step">Step 2</p>
      <p class="hero-title">What are we modelling?</p>
      <p class="hero-sub">Choose a mode, select the trigger market, and set the new list price.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.segmented_control(
        "input_mode",
        ["Demo data", "Edit manually", "Upload Excel"],
        default="Demo data",
        label_visibility="hidden",
        key="input_mode_seg",
        on_change=_on_mode_change,
    )
    # _on_mode_change already ran before this rerun and corrected session_state;
    # the widget return value reflects the corrected state. Guard None defensively.
    if mode is None:
        mode = st.session_state.get("prev_mode", "Demo data")

    st.markdown("""
    <div style="padding: 0 48px 16px 48px; font-size: 11px; color: #c0bdb8; letter-spacing: 0.02em;">
      Upload Excel — coming soon
    </div>
    """, unsafe_allow_html=True)

    custom_assumptions = df_to_assumptions(st.session_state.assumptions_df)

    if mode == "Demo data":
        # Label + table in one block inside .content so sl margin-bottom fires
        # and the table top border (from .t) reads as a distinct element start
        st.markdown("""
        <div class="content">
          <span class="sl">Scenario — Spain CIPM mandatory cut (golden test case)</span>
          <table class="t" style="max-width:520px;">
            <colgroup><col><col style="width:180px"></colgroup>
            <thead><tr><th>Parameter</th><th class="r">Value</th></tr></thead>
            <tbody>
              <tr><td class="m">Trigger market</td><td class="p">ES</td></tr>
              <tr><td class="m">Regulatory trigger</td><td class="r">CIPM mandatory price cut</td></tr>
              <tr><td class="m">Current list price</td><td class="p">€560</td></tr>
              <tr><td class="m">New list price</td><td class="p">€400</td></tr>
              <tr><td class="m">Price reduction</td><td class="neg">−28.6%</td></tr>
            </tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Run cascade →", type="primary"):
            with st.spinner("Running cascade..."):
                st.session_state.results = compute_impact("ES", 400.0, custom_assumptions)
                st.session_state.trigger_market = "ES"
                st.session_state.new_price = 400.0
                st.session_state.narrative = None
            st.rerun()

    elif mode == "Edit manually":
        st.markdown("""
        <div style="background:#ffffff; padding: 20px 48px 0 48px;">
          <span class="sl">Cascade inputs</span>
        </div>
        """, unsafe_allow_html=True)
        markets = ["ES", "DE", "FR", "NL", "UK", "TR"]
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            trigger_market = st.selectbox(
                "Trigger market",
                markets,
                index=markets.index(st.session_state.trigger_market),
            )
        with col2:
            st.text_input(
                "Mandatory trigger",
                value=TRIGGERS[trigger_market],
                disabled=True,
            )
        with col3:
            st.text_input(
                "Current price (€)",
                value=f"€{BASELINES[trigger_market]:,}",
                disabled=True,
            )
        with col4:
            new_price = st.number_input(
                "New list price (€)",
                min_value=0.0,
                value=float(st.session_state.new_price),
                step=10.0,
            )
        if st.button("Run cascade →", type="primary"):
            with st.spinner("Running cascade..."):
                st.session_state.results = compute_impact(trigger_market, new_price, custom_assumptions)
                st.session_state.trigger_market = trigger_market
                st.session_state.new_price = new_price
                st.session_state.narrative = None
            st.rerun()

# ─────────────────────────────────────────────────────────────
# STEP 3
# ─────────────────────────────────────────────────────────────
elif step == "3  What is the impact?":
    st.markdown("""
    <div class="hero">
      <p class="hero-step">Step 3</p>
      <p class="hero-title">What is the impact?</p>
      <p class="hero-sub">Price transmission across IRP baskets · 3-year commercial impact · affected markets in red.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="content">', unsafe_allow_html=True)

    if st.session_state.results is None:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#bbb9b4;">
          <p style="font-size:13px;">Run the cascade in Step 2 to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        rows = st.session_state.results
        trigger_market = st.session_state.trigger_market
        new_price = st.session_state.new_price

        total_ns_asis  = sum(r["ns_asis"]  for r in rows)
        total_gm_asis  = sum(r["gm_asis"]  for r in rows)
        total_ns_after = sum(r["ns_after"] for r in rows)
        total_gm_after = sum(r["gm_after"] for r in rows)
        total_delta_ns = sum(r["delta_ns"] for r in rows)
        total_delta_gm = sum(r["delta_gm"] for r in rows)
        total_dns_pct  = round(total_delta_ns / total_ns_asis * 100, 1)
        total_dgm_pct  = round(total_delta_gm / total_gm_asis * 100, 1)
        affected       = [r["market"] for r in rows if r["delta_ns"] != 0]

        original_price = BASELINES[trigger_market]
        price_drop_pct = round((new_price - original_price) / original_price * 100, 1)

        # Metric cards
        st.markdown('<span class="sl">Portfolio impact — 3-year summary</span>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="mg">
          <div class="mc">
            <p class="ml">Markets affected</p>
            <p class="mv">{len(affected)} / 6</p>
            <p class="ms">{' · '.join(affected) if affected else 'None'}</p>
          </div>
          <div class="mc">
            <p class="ml">Max price drop</p>
            <p class="mv mv-r">{price_drop_pct}%</p>
            <p class="ms">{trigger_market} · €{original_price:,} → €{new_price:,.0f}</p>
          </div>
          <div class="mc">
            <p class="ml">Δ Net sales 3Y</p>
            <p class="mv mv-r">−€{abs(total_delta_ns):,.0f}</p>
            <p class="ms">{total_dns_pct}% vs as-is portfolio</p>
          </div>
          <div class="mc">
            <p class="ml">Δ Gross margin 3Y</p>
            <p class="mv mv-r">−€{abs(total_delta_gm):,.0f}</p>
            <p class="ms">{total_dgm_pct}% vs as-is portfolio</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Unified table
        st.markdown('<span class="sl">Market-by-market breakdown</span>', unsafe_allow_html=True)
        trows = ""
        for r in rows:
            aff = r["delta_ns"] != 0
            mc  = "aff" if aff else "m"
            dc  = "neg" if aff else "neu"
            trows += (
                f"<tr>"
                f"<td class='{mc}'>{r['market']}</td>"
                f"<td class='r'>€{r['ns_asis']:,.0f}</td>"
                f"<td class='r'>€{r['gm_asis']:,.0f}</td>"
                f"<td class='r'>€{r['ns_after']:,.0f}</td>"
                f"<td class='r'>€{r['gm_after']:,.0f}</td>"
                f"<td class='{dc}'>{'−€{:,.0f}'.format(abs(r['delta_ns'])) if aff else '—'}</td>"
                f"<td class='{dc}'>{'{}%'.format(r['delta_ns_pct']) if aff else '—'}</td>"
                f"<td class='{dc}'>{'−€{:,.0f}'.format(abs(r['delta_gm'])) if aff else '—'}</td>"
                f"<td class='{dc}'>{'{}%'.format(r['delta_gm_pct']) if aff else '—'}</td>"
                f"</tr>"
            )

        st.markdown(f"""
        <table class="t">
          <thead>
            <tr>
              <th rowspan="2" style="width:7%;vertical-align:bottom;">Market</th>
              <th colspan="2" class="r" style="border-bottom:none;padding-bottom:2px;">As is — 3Y</th>
              <th colspan="2" class="r" style="border-bottom:none;padding-bottom:2px;">After change — 3Y</th>
              <th colspan="4" class="r" style="border-bottom:none;padding-bottom:2px;color:#8C3B2A;">Delta — value at risk</th>
            </tr>
            <tr>
              <th class="r">NS 3Y</th><th class="r">GM 3Y</th>
              <th class="r">NS 3Y</th><th class="r">GM 3Y</th>
              <th class="r">ΔNS</th><th class="r">ΔNS%</th>
              <th class="r">ΔGM</th><th class="r">ΔGM%</th>
            </tr>
          </thead>
          <tbody>
            {trows}
            <tr class="tot">
              <td>Total</td>
              <td class="r">€{total_ns_asis:,.0f}</td>
              <td class="r">€{total_gm_asis:,.0f}</td>
              <td class="r">€{total_ns_after:,.0f}</td>
              <td class="r">€{total_gm_after:,.0f}</td>
              <td class="neg">−€{abs(total_delta_ns):,.0f}</td>
              <td class="neg">{total_dns_pct}%</td>
              <td class="neg">−€{abs(total_delta_gm):,.0f}</td>
              <td class="neg">{total_dgm_pct}%</td>
            </tr>
          </tbody>
        </table>
        """, unsafe_allow_html=True)

        # Chart
        st.markdown('<span class="sl" style="display:block;margin-top:28px;">3-year impact by market</span>', unsafe_allow_html=True)

        chart_metric = st.radio(
            "chart_metric",
            ["Net sales", "Gross margin"],
            horizontal=True,
            label_visibility="hidden",
            key="chart_toggle",
        )

        markets_list = [r["market"] for r in rows]
        if chart_metric == "Net sales":
            asis_vals  = [r["ns_asis"]  for r in rows]
            after_vals = [r["ns_after"] for r in rows]
            y_label    = "Net Sales 3Y (€)"
        else:
            asis_vals  = [r["gm_asis"]  for r in rows]
            after_vals = [r["gm_after"] for r in rows]
            y_label    = "Gross Margin 3Y (€)"

        after_colors = ["#8C3B2A" if m in affected else "#c8c4bc" for m in markets_list]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="As is",        x=markets_list, y=asis_vals,  marker_color="#1a1a18", opacity=0.15))
        fig.add_trace(go.Bar(name="After change",  x=markets_list, y=after_vals, marker_color=after_colors))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=12, color="#555553"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=32, b=0),
            yaxis=dict(title=y_label, gridcolor="#f0ede8", gridwidth=0.5),
            xaxis=dict(title=""),
            height=300,
        )
        st.plotly_chart(fig, use_container_width=True)

        # AI narrative
        st.markdown('<span class="sl" style="display:block;margin-top:4px;">AI narrative summary</span>', unsafe_allow_html=True)
        st.caption("Plain-English leadership memo · powered by Claude API · one deliberate click")

        if st.session_state.narrative:
            st.markdown(f'<div class="narr">{st.session_state.narrative}</div>', unsafe_allow_html=True)

        if st.button("Generate summary →", type="primary"):
            with st.spinner("Generating narrative..."):
                st.session_state.narrative = generate_narrative(trigger_market, new_price, rows)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

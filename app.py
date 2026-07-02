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
    <div style='background-color:#f0ede8;padding:16px 20px;border-radius:4px;margin-bottom:8px;width:100%;box-sizing:border-box;'>
      <p style='font-size:11px;font-weight:600;color:#999896;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;'>STEP 1</p>
      <p style='font-size:16px;font-weight:600;color:#1a1a18;margin:0 0 4px;'>Where are we today?</p>
      <p style='font-size:13px;color:#555553;margin:0;'>Current list prices and IRP basket roles across all six markets — the baseline the cascade starts from.</p>
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
<div style='background-color:#f0ede8;padding:16px 20px;border-radius:4px;margin-bottom:8px;width:100%;box-sizing:border-box;'>
  <p style='font-size:11px;font-weight:600;color:#999896;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;'>STEP 2</p>
  <p style='font-size:16px;font-weight:600;color:#1a1a18;margin:0 0 4px;'>What are we modelling?</p>
  <p style='font-size:13px;color:#555553;margin:0;'>Choose a mode, select the trigger market, and set the new list price.</p>
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
    try:
        st.markdown("""
<div style='background-color:#f0ede8;padding:16px 20px;border-radius:4px;margin-bottom:8px;width:100%;box-sizing:border-box;'>
  <p style='font-size:11px;font-weight:600;color:#999896;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;'>STEP 3</p>
  <p style='font-size:16px;font-weight:600;color:#1a1a18;margin:0 0 4px;'>What is the impact?</p>
  <p style='font-size:13px;color:#555553;margin:0;'>Price transmission across IRP baskets · 3-year commercial impact · affected markets in red.</p>
</div>
""", unsafe_allow_html=True)

        if st.session_state["results"] is None:
            st.info("Run the cascade above to see results.")
        else:
            rows          = st.session_state["results"]
            trigger_market = st.session_state["trigger_market"]
            new_price      = st.session_state["new_price"]

            # Spacer: white gap between grey hero and metric cards
            st.markdown('<div style="height:28px;background:#ffffff;"></div>', unsafe_allow_html=True)

            # B) Metric cards — all aggregates computed before any widget call
            markets_affected = len([r for r in rows if r["delta_ns"] != 0])
            total_count      = len(rows)
            total_ns_delta   = sum(r["delta_ns"] for r in rows)
            total_gm_delta   = sum(r["delta_gm"] for r in rows)
            max_drop         = min(r["delta_ns_pct"] for r in rows)

            def fmt_eur_m(val):
                sign = "-" if val < 0 else ""
                return f"{sign}€{abs(val) / 1_000_000:.1f}M"

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Markets affected",      f"{markets_affected} / {total_count}")
            with c2:
                st.metric("Total NS delta (3Y)",   fmt_eur_m(total_ns_delta))
            with c3:
                st.metric("Total GM delta (3Y)",   fmt_eur_m(total_gm_delta))
            with c4:
                st.metric("Max single-market drop", f"{max_drop:.1f}%")

            # C) Placeholders — steps 2 / 3 / 4 will replace these blocks
            # Note: st.markdown('---') is invisible because hr { display:none } is in global CSS.
            # Using a border-top div as the visual divider instead — same appearance.

            # --- Table: market-by-market cascade results (step 2) ---

            # Totals for total row
            total_ns_asis_t  = sum(r["ns_asis"]  for r in rows)
            total_ns_after_t = sum(r["ns_after"] for r in rows)
            total_delta_ns_t = sum(r["delta_ns"] for r in rows)
            total_delta_ns_pct_t = round((total_delta_ns_t / total_ns_asis_t) * 100, 1) if total_ns_asis_t else 0.0

            # Build tbody rows
            rows_html = ""
            for r in rows:
                list_delta_pct = ((r["list_after"] - r["list_asis"]) / r["list_asis"]) * 100
                is_affected = r["delta_ns"] != 0

                if is_affected:
                    row_bg     = "#FEF4F4"
                    row_bdr    = "border-bottom:0.5px solid #FBDADA;"
                    mkt_s      = "font-weight:600;color:#791F1F;"
                    l_asis_s   = "color:#999896;"
                    l_after_s  = "font-weight:600;color:#791F1F;"
                    l_delta_s  = "color:#791F1F;"
                    ns_asis_s  = "color:#999896;"
                    ns_after_s = "font-weight:600;color:#791F1F;"
                    dns_abs_s  = "color:#791F1F;"
                    dns_pct_s  = "color:#791F1F;"
                    l_delta_v  = f"{list_delta_pct:.1f}%"
                    dns_abs_v  = (f"-€{abs(r['delta_ns']) / 1_000_000:.1f}M"
                                  if r["delta_ns"] < 0
                                  else f"€{r['delta_ns'] / 1_000_000:.1f}M")
                    dns_pct_v  = f"{r['delta_ns_pct']:.1f}%"
                else:
                    row_bg     = "#ffffff"
                    row_bdr    = "border-bottom:0.5px solid #e0ddd6;"
                    mkt_s      = "color:#555553;"
                    l_asis_s   = "color:#999896;"
                    l_after_s  = "color:#999896;"
                    l_delta_s  = "color:#cccccc;"
                    ns_asis_s  = "color:#999896;"
                    ns_after_s = "color:#999896;"
                    dns_abs_s  = "color:#cccccc;"
                    dns_pct_s  = "color:#cccccc;"
                    l_delta_v  = "—"
                    dns_abs_v  = "—"
                    dns_pct_v  = "—"

                rows_html += (
                    f'<tr style="background:{row_bg};{row_bdr}">'
                    f'<td style="padding:8px 10px;{mkt_s}">{r["market"]}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{l_asis_s}border-left:0.5px solid #e0ddd6;">{int(r["list_asis"])}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{l_after_s}">{int(r["list_after"])}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{l_delta_s}">{l_delta_v}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{ns_asis_s}border-left:0.5px solid #e0ddd6;">{r["ns_asis"] / 1_000_000:.1f}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{ns_after_s}">{r["ns_after"] / 1_000_000:.1f}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{dns_abs_s}">{dns_abs_v}</td>'
                    f'<td style="padding:8px 10px;text-align:right;{dns_pct_s}">{dns_pct_v}</td>'
                    f'</tr>'
                )

            # Total row
            if total_delta_ns_t < 0:
                t_abs   = f"-€{abs(total_delta_ns_t) / 1_000_000:.1f}M"
                t_color = "#791F1F"
            else:
                t_abs   = f"€{total_delta_ns_t / 1_000_000:.1f}M"
                t_color = "#1a1a18"
            t_pct_color = "#791F1F" if total_delta_ns_t < 0 else "#1a1a18"

            total_row_html = (
                f'<tr style="background:#f5f3ee;border-top:1px solid #cccccc;font-weight:600;">'
                f'<td style="padding:8px 10px;color:#1a1a18;">Total</td>'
                f'<td style="padding:8px 10px;border-left:0.5px solid #e0ddd6;"></td>'
                f'<td style="padding:8px 10px;"></td>'
                f'<td style="padding:8px 10px;"></td>'
                f'<td style="padding:8px 10px;text-align:right;color:#999896;border-left:0.5px solid #e0ddd6;">{total_ns_asis_t / 1_000_000:.1f}</td>'
                f'<td style="padding:8px 10px;text-align:right;color:#1a1a18;">{total_ns_after_t / 1_000_000:.1f}</td>'
                f'<td style="padding:8px 10px;text-align:right;color:{t_color};">{t_abs}</td>'
                f'<td style="padding:8px 10px;text-align:right;color:{t_pct_color};">{total_delta_ns_pct_t:.1f}%</td>'
                f'</tr>'
            )

            table_html = f"""
<div style="border-top:0.5px solid #e8e6e1;margin-top:8px;"></div>
<div style="padding:20px 48px 16px 48px;background:#ffffff;overflow-x:auto;">
  <p style="font-size:12px;color:#999896;margin:0 0 10px 0;">Based on commercial assumptions set in step 1 · edit above and re-run to recalculate</p>
  <div style="overflow-x:auto;margin-bottom:4px;">
    <table style="width:100%;border-collapse:collapse;font-size:12px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;table-layout:fixed;border:0.5px solid #e0ddd6;">
      <colgroup>
        <col style="width:12.5%"><col style="width:12.5%"><col style="width:12.5%"><col style="width:12.5%">
        <col style="width:12.5%"><col style="width:12.5%"><col style="width:12.5%"><col style="width:12.5%">
      </colgroup>
      <thead>
        <tr style="background:#f0ede8;">
          <th rowspan="2" style="padding:8px 10px;text-align:left;font-size:11px;font-weight:500;color:#999896;vertical-align:bottom;border-top:0.5px solid #e0ddd6;border-bottom:0.5px solid #e0ddd6;">Market</th>
          <th colspan="3" style="padding:6px 10px;text-align:center;font-size:11px;font-weight:500;color:#1a1a18;border-left:0.5px solid #e0ddd6;border-bottom:3px solid #e0ddd6;">List price (EUR)</th>
          <th colspan="4" style="padding:6px 10px;text-align:center;font-size:11px;font-weight:500;color:#1a1a18;border-left:0.5px solid #e0ddd6;border-bottom:3px solid #e0ddd6;">Net sales 3Y (EUR M)</th>
        </tr>
        <tr style="background:#f0ede8;border-bottom:0.5px solid #e0ddd6;">
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;border-left:0.5px solid #e0ddd6;">As is</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;">After</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;">Δ%</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;border-left:0.5px solid #e0ddd6;">As is</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;">After</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;">Δ abs</th>
          <th style="padding:6px 10px;text-align:right;font-size:11px;font-weight:500;color:#999896;">Δ%</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
        {total_row_html}
      </tbody>
    </table>
  </div>
  <p style="font-size:10px;color:#999896;margin:4px 0 0 0;">* TR list price shown as EUR equivalent (fixed rate 1 EUR = 36.5 TRY, illustrative) · FR and NL reflect new price from Y2 onwards (transmission lag 1 year)</p>
</div>"""

            st.markdown(table_html, unsafe_allow_html=True)

            # --- Chart: NS/GM toggle bar chart (step 3) ---
            st.markdown(
                '<div style="border-top:0.5px solid #e8e6e1;margin-top:4px;"></div>',
                unsafe_allow_html=True,
            )

            hdr_left, hdr_right = st.columns([3, 1])
            with hdr_left:
                st.markdown(
                    "<p style='font-size:14px; font-weight:600; color:#555553; margin:0; padding-top:6px;'>"
                    "3-year delta by market"
                    "</p>",
                    unsafe_allow_html=True,
                )
            with hdr_right:
                chart_metric = st.segmented_control(
                    label="metric_toggle",
                    options=["Net sales", "Gross margin"],
                    default="Net sales",
                    label_visibility="collapsed",
                )

            if chart_metric == "Net sales":
                deltas = [r["delta_ns"] / 1_000_000 for r in rows]
                pcts   = [r["delta_ns_pct"] for r in rows]
            else:
                deltas = [r["delta_gm"] / 1_000_000 for r in rows]
                pcts   = [r["delta_gm_pct"] for r in rows]

            markets     = [r["market"] for r in rows]
            is_affected = [r["delta_ns"] != 0 for r in rows]
            bar_colors  = ["#F09595" if affected else "#D3D1C7" for affected in is_affected]

            # Shared y-axis max across both metrics so toggling never rescales
            y_max = max(
                max(abs(r["delta_ns"]) for r in rows),
                max(abs(r["delta_gm"]) for r in rows),
            ) / 1_000_000

            bar_y       = [abs(d) for d in deltas]
            bar_texts   = []
            text_colors = []
            for i, affected in enumerate(is_affected):
                if affected:
                    val  = deltas[i]
                    pct  = pcts[i]
                    sign = "-" if val < 0 else "+"
                    bar_texts.append(
                        f"{sign}€{abs(val):.1f}M<br><span style='font-size:10px'>{pct:.1f}%</span>"
                    )
                    text_colors.append("#791F1F")
                else:
                    bar_texts.append("0.0M")
                    text_colors.append("#999896")

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=markets,
                y=bar_y,
                marker_color=bar_colors,
                text=bar_texts,
                textposition="outside",
                textfont=dict(size=11, color=text_colors),
                hovertemplate="%{x}: %{y:.1f}M<extra></extra>",
                cliponaxis=False,
            ))
            fig.update_layout(
                height=300,
                margin=dict(t=40, b=0, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
                    size=12,
                ),
                xaxis=dict(
                    showgrid=False,
                    showline=False,
                    tickfont=dict(size=12, color="#555553"),
                ),
                yaxis=dict(
                    showgrid=False,
                    showline=False,
                    showticklabels=False,
                    zeroline=False,
                    range=[0, y_max * 1.3],
                ),
                showlegend=False,
                bargap=0.4,
            )
            st.plotly_chart(fig, config={"displayModeBar": False})

            # --- Narrative: AI narrative strip (step 4) ---
            st.divider()

            _narr_left, _narr_right = st.columns([4, 1], vertical_alignment="center")
            with _narr_left:
                st.markdown(
                    "<p style='font-size:13px;font-weight:500;color:#1a1a18;margin:0;'>✦ AI narrative</p>"
                    "<p style='font-size:11px;color:#999896;margin:2px 0 0;'>Leadership-ready memo · Pyramid Principle · generated by Claude</p>",
                    unsafe_allow_html=True,
                )
            with _narr_right:
                generate_clicked = st.button(
                    "Generate", key="generate_narrative_btn", type="primary"
                )

            if generate_clicked:
                with st.spinner("Generating narrative..."):
                    try:
                        st.session_state["narrative"] = generate_narrative(
                            trigger_market, new_price, rows
                        )
                    except Exception as e:
                        st.error(f"Could not generate narrative: {e}")
                        st.session_state["narrative"] = None

            if st.session_state.get("narrative"):
                _lines = [l.strip() for l in st.session_state["narrative"].strip().split("\n") if l.strip()]
                _html = []
                for _line in _lines:
                    if _line.startswith("**") and _line.endswith("**"):
                        _html.append(f"<p style='font-size:15px;font-weight:700;color:#1a1a18;margin:10px 0 6px;'>{_line[2:-2]}</p>")
                    elif _line.startswith("- "):
                        _html.append(f"<p style='font-size:14px;color:#555553;margin:6px 0 6px 12px;'>• {_line[2:]}</p>")
                    else:
                        _html.append(f"<p style='font-size:14px;color:#555553;margin:3px 0;'>{_line}</p>")
                st.markdown(
                    f"<div style='padding: 8px 0 0 16px;'>{''.join(_html)}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='height: 40px;'></div>",
                    unsafe_allow_html=True,
                )

    except Exception:
        st.error("Could not render results. Check session state.")

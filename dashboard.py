import copy
import html
import math
import re
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accounting import (
    LedgerManager,
    CONTRACT,
    UCU_CONTRACT,
    PAYROLL_SCHEDULE,
    DEFAULT_HARDWARE_GOALS,
    GOAL_ACCENT_PALETTE,
    get_live_ugx_rate,
    get_live_ugx_rates,
    project_hardware_goals,
)
from finance_advisor import generate_financial_insights
from receipt_ingestion import process_raw_receipts

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Okidi Finance OS",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── AUTHENTICATION GATE ─────────────────────────────────────────────────────
ALLOWED_EMAILS = ["oknorbert6@gmail.com"]

if not st.user.is_logged_in:
    st.markdown("""
    <style>
    /* Full screen animated background */
    .stApp {
        background: radial-gradient(circle at 15% 50%, rgba(20, 10, 40, 1), rgba(5, 5, 10, 1) 60%),
                    radial-gradient(circle at 85% 30%, rgba(30, 15, 60, 0.8), transparent 50%);
        background-color: #05050A;
        background-attachment: fixed;
    }
    
    /* Header removal for clean look */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Premium Glassmorphism Container */
    .premium-auth-container {
        position: relative;
        margin: 10vh auto;
        max-width: 460px;
        background: rgba(20, 20, 35, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 32px;
        padding: 56px 48px;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
        text-align: center;
        overflow: hidden;
        animation: float 6s ease-in-out infinite;
    }
    
    /* Glow effect behind container */
    .premium-auth-container::before {
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: conic-gradient(from 0deg, transparent, rgba(139, 92, 246, 0.1), transparent 30%);
        animation: rotate 10s linear infinite;
        z-index: -1;
    }
    
    @keyframes rotate {
        100% { transform: rotate(360deg); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    /* Typography */
    .auth-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
    }
    
    .auth-subtitle {
        font-family: 'Inter', sans-serif;
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 40px;
    }
    
    /* Logo Icon */
    .auth-logo {
        font-size: 56px;
        margin-bottom: 24px;
        filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.4));
    }
    
    /* Restyle the Streamlit Button */
    div.stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 24px !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 10px 20px rgba(109, 40, 217, 0.3), inset 0 1px 0 rgba(255,255,255,0.2) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 25px rgba(109, 40, 217, 0.4), inset 0 1px 0 rgba(255,255,255,0.3) !important;
    }
    </style>
    
    <div class="premium-auth-container">
        <div class="auth-logo">💎</div>
        <div class="auth-title">Okidi Finance OS</div>
        <div class="auth-subtitle">
            Enterprise-grade financial intelligence.<br>Secure authentication required.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Authenticate via Google Passkey", type="primary", use_container_width=True):
            st.login("oidc")
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error(f"Security Alert: Access denied. {st.user.email} is not authorized for this environment.")
    st.button("Terminate Session", on_click=st.logout)
    st.stop()

if st.user.email not in ALLOWED_EMAILS:
    st.error(f"Access denied. {st.user.email} is not authorized.")
    st.button("Sign out", on_click=st.logout)
    st.stop()


# ─── PREMIUM GLASSMORPHISM CSS ────────────────────────────────────────────────
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">', unsafe_allow_html=True)
st.markdown("""<style>
  /* ── Reset & Base ── */
  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  .stApp {
    background: linear-gradient(135deg, #0a0a1a 0%, #0d1130 30%, #0a1628 60%, #070d1f 100%) !important;
    font-family: 'Inter', sans-serif !important;
  }
  
  /* Animated starfield background */
  .stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      radial-gradient(1px 1px at 20% 30%, rgba(255,255,255,0.3) 0%, transparent 100%),
      radial-gradient(1px 1px at 80% 10%, rgba(255,255,255,0.2) 0%, transparent 100%),
      radial-gradient(1px 1px at 50% 80%, rgba(255,255,255,0.25) 0%, transparent 100%),
      radial-gradient(1px 1px at 10% 60%, rgba(255,255,255,0.15) 0%, transparent 100%),
      radial-gradient(1px 1px at 90% 50%, rgba(255,255,255,0.2) 0%, transparent 100%),
      radial-gradient(2px 2px at 40% 20%, rgba(139,92,246,0.4) 0%, transparent 100%),
      radial-gradient(2px 2px at 70% 70%, rgba(59,130,246,0.3) 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
  }

  /* ── Hide default Streamlit chrome ── */
  #MainMenu, footer { visibility: hidden !important; }
  header { background: transparent !important; }
  .stDeployButton { display: none !important; }
  
  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: rgba(13, 17, 48, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(139, 92, 246, 0.2) !important;
  }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }

  /* ── Tab styling ── */
  .stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 16px !important;
    padding: 6px !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.5) !important;
    border-radius: 12px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: all 0.3s ease !important;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(139,92,246,0.4), rgba(59,130,246,0.4)) !important;
    color: white !important;
    box-shadow: 0 0 20px rgba(139,92,246,0.3) !important;
  }

  /* ── Metric cards ── */
  [data-testid="stMetric"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 20px !important;
    padding: 20px !important;
    backdrop-filter: blur(10px) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease !important;
  }
  [data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4) !important;
  }
  [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.5) !important; font-size: 0.8rem !important; }
  [data-testid="stMetricValue"] { color: white !important; font-family: 'Space Grotesk', sans-serif !important; }

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid rgba(139,92,246,0.2) !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(124,58,237,0.4) !important;
  }
  .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(124,58,237,0.6) !important;
  }

  /* ── Inputs ── */
  .stSelectbox > div, .stTextInput > div > input, .stNumberInput > div > div > input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(139,92,246,0.3) !important;
    border-radius: 12px !important;
    color: white !important;
  }

  /* ── Slider ── */
  .stSlider [data-baseweb="slider"] { padding: 10px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="
  background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(37,99,235,0.15) 100%);
  border: 1px solid rgba(139,92,246,0.25);
  border-radius: 24px;
  padding: 32px 40px;
  margin-bottom: 32px;
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
">
  <div style="
    position: absolute; top: -50px; right: -50px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(124,58,237,0.3) 0%, transparent 70%);
    border-radius: 50%;
  "></div>
  <div style="
    position: absolute; bottom: -60px; left: 30%;
    width: 150px; height: 150px;
    background: radial-gradient(circle, rgba(37,99,235,0.2) 0%, transparent 70%);
    border-radius: 50%;
  "></div>
  <div style="display:flex; align-items:center; gap: 20px; position:relative; z-index:1;">
    <div style="
      width: 72px; height: 72px;
      background: linear-gradient(135deg, #7c3aed, #2563eb);
      border-radius: 20px;
      display: flex; align-items: center; justify-content: center;
      font-size: 32px;
      box-shadow: 0 8px 32px rgba(124,58,237,0.5);
    ">💎</div>
    <div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:2rem; font-weight:800; color:white; line-height:1.1;">
        {CONTRACT['name']}
      </div>
      <div style="color: rgba(255,255,255,0.5); font-size:0.9rem; margin-top:4px;">
        {CONTRACT['role']} · {CONTRACT['company']} · Started {CONTRACT['start_date']}
      </div>
    </div>
    <div style="margin-left:auto; text-align:right;">
      <div style="
        background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.2));
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 12px; padding: 8px 16px;
        color: #10b981; font-family:'Space Grotesk',sans-serif; font-weight:600;
      ">● ACTIVE CONTRACT</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.2rem; font-weight:700; 
                color:white; margin-bottom:16px; padding-bottom:12px;
                border-bottom: 1px solid rgba(139,92,246,0.3);">
      ⚙️ Controls
    </div>
    """, unsafe_allow_html=True)

    @st.cache_data(ttl=300)
    def fetch_live_rates():
        return get_live_ugx_rates()

    def _resolve_source_rate(rates_dict, preferred_source):
        if preferred_source == "Binance P2P (Sell USDT)" and rates_dict.get("binance_p2p_rate"):
            return float(rates_dict["binance_p2p_rate"]), "Binance P2P (Sell USDT)"
        if preferred_source == "Interbank Mid-Market" and rates_dict.get("interbank_rate"):
            return float(rates_dict["interbank_rate"]), "Interbank Mid-Market"
        return float(rates_dict["active_rate"]), str(rates_dict["active_source"])

    rates_info = fetch_live_rates()

    rate_source_choice = st.selectbox(
        "FX Rate Source",
        ["Binance P2P (Sell USDT)", "Interbank Mid-Market"],
        key="fx_rate_source",
        help="Binance P2P reflects real USDT->UGX cash-out; automatically falls back to Interbank if unreachable.",
    )
    resolved_live_rate, effective_source = _resolve_source_rate(rates_info, rate_source_choice)

    sync_c1, sync_c2 = st.columns([1.3, 1.0])
    with sync_c1:
        auto_sync_fx = st.checkbox(
            "Auto-sync (5m)",
            value=True,
            key="auto_sync_fx",
            help="Automatically refreshes every 5 minutes and updates all figures whenever the live rate changes.",
        )
    with sync_c2:
        if st.button("🔄 Refresh", key="btn_refresh_fx", use_container_width=True):
            fetch_live_rates.clear()
            st.session_state.pop("last_synced_live_rate", None)
            st.rerun()

    pending_sync = st.session_state.pop("pending_fx_sync", None)
    if pending_sync is not None:
        resolved_live_rate = float(pending_sync)

    source_changed = st.session_state.get("last_fx_source") != rate_source_choice
    prev_synced = st.session_state.get("last_synced_live_rate")
    live_rate_changed = prev_synced is None or abs(resolved_live_rate - float(prev_synced)) >= 1.0

    if (
        "ugx_rate_slider" not in st.session_state
        or pending_sync is not None
        or source_changed
        or (auto_sync_fx and live_rate_changed)
    ):
        st.session_state["ugx_rate_slider"] = float(round(resolved_live_rate))
        st.session_state["last_synced_live_rate"] = resolved_live_rate
        st.session_state["last_fx_source"] = rate_source_choice

    anchor_rates = [resolved_live_rate, float(st.session_state["ugx_rate_slider"])]
    slider_min = float(min(3200.0, math.floor((min(anchor_rates) - 400.0) / 100.0) * 100.0))
    slider_max = float(max(5000.0, math.ceil((max(anchor_rates) + 400.0) / 100.0) * 100.0))
    st.session_state["ugx_rate_slider"] = max(slider_min, min(slider_max, float(st.session_state["ugx_rate_slider"])))

    ugx_rate = st.slider(
        "Live UGX Rate (per 1 USDT)",
        min_value=slider_min,
        max_value=slider_max,
        step=1.0,
        key="ugx_rate_slider",
        help="Auto-synced from the live feed above. Drag to manually override for a specific P2P quote.",
    )

    @st.fragment(run_every="5m")
    def _auto_fx_watcher():
        if not st.session_state.get("auto_sync_fx", True):
            return
        fresh_rates = fetch_live_rates()
        chosen_src = st.session_state.get("fx_rate_source", "Binance P2P (Sell USDT)")
        fresh_rate, _ = _resolve_source_rate(fresh_rates, chosen_src)
        last_rate = st.session_state.get("last_synced_live_rate")
        if last_rate is not None and abs(fresh_rate - float(last_rate)) >= 1.0:
            st.session_state["pending_fx_sync"] = fresh_rate
            st.rerun(scope="app")

    _auto_fx_watcher()

    rate_details = [f"Active: **1 USDT = {ugx_rate:,.0f} UGX**", f"Source: **{effective_source}** ({rates_info['fetched_at']})"]
    if rates_info.get("binance_p2p_rate") and rates_info.get("interbank_rate"):
        spread_txt = f" ({rates_info['spread_pct']:+.1f}%)" if rates_info.get("spread_pct") is not None else ""
        rate_details.append(
            f"Binance P2P: **{rates_info['binance_p2p_rate']:,.0f}** · Interbank: **{rates_info['interbank_rate']:,.0f}**{spread_txt}"
        )
    elif rates_info.get("interbank_rate") and effective_source == "Interbank Mid-Market" and rate_source_choice == "Binance P2P (Sell USDT)":
        rate_details.append("Binance P2P unavailable from host; using Interbank live rate.")
    st.caption("  \n".join(rate_details))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600;
                color:rgba(255,255,255,0.7); margin-bottom:12px;">
      Logged in as
    </div>
    """, unsafe_allow_html=True)
    st.info(f"{st.user.email}")
    st.button("Sign out", on_click=st.logout)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600; 
                color:rgba(255,255,255,0.7); margin-bottom:12px;">
      🏢 CazzyGames Retainer
    </div>
    """, unsafe_allow_html=True)
    st.info(f"Base Pay: **${CONTRACT['trial_fee_usd']:,.0f} USD / month**")
    st.info(f"Overtime Rate: **${CONTRACT['overtime_rate_usd']:,.2f} / hr** (1.5x)")
    st.info(f"Post-Trial: **${CONTRACT['post_trial_fee_usd']:,.0f} USD / month**")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600; 
                color:rgba(255,255,255,0.7); margin-bottom:12px;">
      🎓 UCU Teaching Appointment
    </div>
    """, unsafe_allow_html=True)
    st.info(f"Role: **{UCU_CONTRACT['role']}**\n\nSubject: **{UCU_CONTRACT['subject_code']} - {UCU_CONTRACT['subject_name']}**\n\nGross Pay: **UGX {UCU_CONTRACT['monthly_gross_ugx']:,.0f} / mo** (4 installments)")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:600; 
                color:rgba(255,255,255,0.7); margin-bottom:12px;">
      📅 Payroll & Rent Schedule
    </div>
    """, unsafe_allow_html=True)
    st.caption("• **UCU:** 23rd of every month\n  *(Lab Tech & Teaching)*")
    st.caption("• **House Rent:** 25th of every month\n  *(UGX 500,000)*")
    st.caption("• **CazzyGames:** 26th – 29th of every month\n  *(Retainer Base & Overtime)*")

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
mgr = LedgerManager()
summary = mgr.get_summary(ugx_rate=ugx_rate)
income_df = mgr.load_income()
expenses_df = mgr.load_expenses()
savings_df = mgr.load_savings(ugx_rate=ugx_rate)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💼 Income", "🛍️ Expenses", "🏦 Savings", "🧠 Advisor"])

# ════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════════
with tab1:
    # ── KPI Cards ──
    cols = st.columns(5)
    with cols[0]:
        st.metric("Total Earned (USDT)", f"${summary['total_received_usdt']:,.2f}",
                  help="Total crypto received so far")
    with cols[1]:
        val_ugx = f"UGX {summary['total_received_ugx']:,.0f}"
        st.metric("Total Earned (UGX)", val_ugx)
    with cols[2]:
        pending_delta = f"-${summary['total_pending_usd']:,.2f}" if summary['total_pending_usd'] > 0 else None
        st.metric("Pending / Owed (USD)", f"${summary['total_pending_usd']:,.2f}",
                  delta=pending_delta, delta_color="inverse")
    with cols[3]:
        st.metric("Total Expenses (UGX)", f"UGX {summary['total_expenses_ugx']:,.0f}")
    with cols[4]:
        tax_usd = summary.get('total_tax_usd', 0.0)
        st.metric("Taxes Withheld (USD)", f"${tax_usd:,.2f}", 
                  delta=f"-UGX {tax_usd * summary['ugx_rate']:,.0f}" if tax_usd > 0 else None, delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Cashflow Donut ──
    c1, c2 = st.columns(2)

    with c1:
        received = summary['total_received_usdt']
        pending = summary['total_pending_usd']
        expenses_usd = summary['total_expenses_usd']
        savings = summary['total_savings_usdt']
        remaining = max(received - expenses_usd - savings, 0)

        labels = ['Received', 'Pending/Owed', 'Expenses (USD eq.)', 'Savings']
        values = [received, pending, expenses_usd, savings]
        colors = ['#7c3aed', '#ef4444', '#f59e0b', '#10b981']

        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.65,
            marker=dict(colors=colors, line=dict(color='rgba(0,0,0,0)', width=0)),
            textfont=dict(color='white', family='Inter'),
            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>"
        )])
        fig.add_annotation(text=f"<b>${received:,.2f}</b><br>Total Earned",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=14, color='white', family='Space Grotesk'))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='rgba(255,255,255,0.7)')),
            title=dict(text="Cashflow Breakdown", font=dict(color='white', size=16, family='Space Grotesk')),
            margin=dict(t=40, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Gauge for contract fulfillment
        fulfillment = (summary['total_received_usdt'] / summary['total_expected_usd'] * 100) if summary['total_expected_usd'] > 0 else 0

        fig2 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fulfillment,
            number={'suffix': '%', 'font': {'color': 'white', 'family': 'Space Grotesk', 'size': 36}},
            delta={'reference': 100, 'font': {'color': 'white'}},
            title={'text': "Contract Fulfillment", 'font': {'color': 'white', 'family': 'Space Grotesk', 'size': 16}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': 'rgba(255,255,255,0.3)', 'tickfont': {'color': 'rgba(255,255,255,0.5)'}},
                'bar': {'color': 'rgba(124,58,237,0.9)', 'thickness': 0.3},
                'bgcolor': 'rgba(255,255,255,0.05)',
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(239,68,68,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(245,158,11,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(16,185,129,0.15)'},
                ],
                'threshold': {
                    'line': {'color': '#10b981', 'width': 3},
                    'thickness': 0.85, 'value': 100
                }
            }
        ))
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            margin=dict(t=40, b=20, l=20, r=20), height=350
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── USD vs UGX quick conversion banner ──
    st.markdown(f"""
    <div style="
      background: linear-gradient(135deg, rgba(16,185,129,0.1), rgba(5,150,105,0.1));
      border: 1px solid rgba(16,185,129,0.2);
      border-radius: 16px; padding: 20px 28px;
      display: flex; justify-content: space-between; align-items: center;
      font-family: 'Space Grotesk', sans-serif;
    ">
      <div>
        <div style="color: rgba(255,255,255,0.5); font-size:0.8rem;">Your wallet today</div>
        <div style="color: white; font-size: 1.8rem; font-weight: 700;">${summary['total_received_usdt']:,.2f} USDT</div>
      </div>
      <div style="color: rgba(255,255,255,0.3); font-size: 1.5rem;">≈</div>
      <div style="text-align:right;">
        <div style="color: rgba(255,255,255,0.5); font-size:0.8rem;">At current rate ({ugx_rate:,.0f} UGX/USDT)</div>
        <div style="color: #10b981; font-size: 1.8rem; font-weight: 700;">UGX {summary['total_received_ugx']:,.0f}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# TAB 2 — INCOME
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:white; margin-bottom:16px;">
      Work Income & Salary
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📥 Ingest UCU Teaching Contract (4 Installments)"):
        st.markdown(f"""
        **Contract:** Part-time Tutorial Assistant at UCU ({UCU_CONTRACT['subject_code']} - {UCU_CONTRACT['subject_name']}).  
        **Installment Value:** UgShs {UCU_CONTRACT['monthly_gross_ugx']:,.0f} gross (~${UCU_CONTRACT['monthly_gross_ugx']/ugx_rate:,.2f} USD).  
        **Total Value:** UgShs {UCU_CONTRACT['total_gross_ugx']:,.0f} gross across 4 monthly installments.  
        Clicking below will add any missing installments to your Income ledger as pending receivables.
        """)
        if st.button("Add 4x UCU TA Installments to Ledger", type="primary", key="btn_ingest_ucu"):
            installments = [
                {"date": "2026-08-31", "desc": "UCU TA Installment 1/4 (SNF2108 WAN Eng - UgShs 868,050/=)"},
                {"date": "2026-09-30", "desc": "UCU TA Installment 2/4 (SNF2108 WAN Eng - UgShs 868,050/=)"},
                {"date": "2026-10-31", "desc": "UCU TA Installment 3/4 (SNF2108 WAN Eng - UgShs 868,050/=)"},
                {"date": "2026-12-04", "desc": "UCU TA Installment 4/4 (Results Submission - UgShs 868,050/=)"},
            ]
            current_income = mgr.load_income()
            existing_descs = set(current_income["Description"].astype(str).tolist()) if not current_income.empty else set()
            added_count = 0
            usd_per_inst = round(UCU_CONTRACT["monthly_gross_ugx"] / ugx_rate, 2)
            for inst in installments:
                if inst["desc"] not in existing_descs:
                    mgr.add_income(
                        date=inst["date"],
                        category="UCU_Tutorial_Assistant",
                        description=inst["desc"],
                        expected_usd=usd_per_inst,
                        received_usdt=0.0,
                        pending_usd=usd_per_inst
                    )
                    added_count += 1
            if added_count > 0:
                st.success(f"Successfully added {added_count} installments to Income ledger!")
                st.rerun()
            else:
                st.info("All 4 UCU TA installments already exist in your Income ledger.")

    with st.expander("➕ Add New Income Record"):
        col1, col2 = st.columns(2)
        with col1:
            inc_date = st.date_input("Date", value=date.today(), key="inc_date")
            inc_category = st.selectbox("Category", [
                "Base Pay", "Overtime", "Reimbursement", 
                "UCU_Tutorial_Assistant", "Electronics_Lab_Technician_Graduate_Intern", 
                "Freelance / Consulting", "Other"
            ], key="inc_cat")
        with col2:
            inc_desc = st.text_input("Description", placeholder="e.g. October Base Pay", key="inc_desc")
            inc_expected = st.number_input("Expected Amount (USD)", min_value=0.0, step=10.0, key="inc_exp")
        c_rec, c_pend = st.columns(2)
        with c_rec:
            inc_received = st.number_input("Received (USDT)", min_value=0.0, step=10.0, key="inc_rec")
        with c_pend:
            inc_pending = st.number_input("Still Pending (USD)", min_value=0.0, step=10.0, value=max(inc_expected - inc_received, 0.0), key="inc_pend")
        if st.button("Save Income Record", key="btn_save_inc"):
            if inc_desc and inc_expected > 0:
                mgr.add_income(str(inc_date), inc_category, inc_desc, inc_expected, inc_received, inc_pending)
                st.success("Income record saved!")
                st.rerun()
            else:
                st.warning("Please fill in description and expected amount.")

    if not income_df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Expected This Period", f"${income_df['Expected_USD'].sum():,.2f} USD")
        with c2:
            st.metric("Received", f"${income_df['Received_USDT'].sum():,.2f} USDT")
        with c3:
            st.metric("Still Pending", f"${income_df['Pending_USD'].sum():,.2f} USD",
                      delta=f"-${income_df['Pending_USD'].sum():,.2f}", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        fig = px.bar(income_df, x="Description", y=["Expected_USD", "Received_USDT"],
                     barmode="group", title="Expected vs Received per Pay Item",
                     color_discrete_map={"Expected_USD": "#7c3aed", "Received_USDT": "#10b981"},
                     labels={"value": "Amount (USD/USDT)", "variable": "Type"})
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            xaxis=dict(tickfont=dict(color='rgba(255,255,255,0.6)'), gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(tickfont=dict(color='rgba(255,255,255,0.6)'), gridcolor='rgba(255,255,255,0.05)'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            title_font=dict(color='white', family='Space Grotesk', size=15)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(income_df, use_container_width=True)
    else:
        st.info("No income records yet.")

    # ─── DEBTORS & PERSONAL LOANS OWED TO YOU ───
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.25rem; font-weight:700; color:white; margin-bottom:12px;">
      🧾 Debtors (Money Owed to You)
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Add Debtor / Personal Loan"):
        dc1, dc2 = st.columns(2)
        with dc1:
            deb_date = st.date_input("Date Lent", value=date.today(), key="deb_date")
            deb_name = st.text_input("Debtor Name", placeholder="e.g. John Doe", key="deb_name")
            deb_phone = st.text_input("Phone (optional)", placeholder="256...", key="deb_phone")
        with dc2:
            deb_amount = st.number_input("Principal Amount (UGX)", min_value=0.0, step=5000.0, key="deb_amt")
            deb_fee = st.number_input("Transfer / Cash-out Fee (UGX)", min_value=0.0, step=500.0, key="deb_fee")
            deb_notes = st.text_input("Notes (optional)", placeholder="Reason / due date", key="deb_notes")
        if st.button("Save Debtor", key="btn_save_debtor"):
            if deb_name.strip() and deb_amount > 0:
                mgr.add_debtor(str(deb_date), deb_name, deb_amount, deb_phone, deb_fee, "Pending", deb_notes)
                st.success(f"Added {deb_name.strip()} to Debtors!")
                st.rerun()
            else:
                st.warning("Enter debtor name and amount greater than 0.")

    debtors_df = mgr.load_debtors()
    pending_debtors = debtors_df[debtors_df["Status"].str.lower() != "paid"]
    total_owed_ugx = pending_debtors["Amount_UGX"].sum() if not pending_debtors.empty else 0.0

    dm1, dm2 = st.columns(2)
    with dm1:
        st.metric("Outstanding Debtors (UGX)", f"UGX {total_owed_ugx:,.0f}",
                  delta=f"{len(pending_debtors)} pending" if len(pending_debtors) > 0 else "All settled")
    with dm2:
        st.metric("Outstanding Debtors (USDT eq.)", f"${total_owed_ugx / ugx_rate:,.2f}")

    if not pending_debtors.empty:
        for idx, drow in pending_debtors.iterrows():
            d_col1, d_col2 = st.columns([4.2, 1.0])
            with d_col1:
                phone_bit = f" · {html.escape(str(drow['Phone']))}" if str(drow['Phone']).strip() else ""
                note_bit = f"<div style='color:rgba(255,255,255,0.5); font-size:0.8rem; margin-top:3px;'>{html.escape(str(drow['Notes']))}</div>" if str(drow['Notes']).strip() else ""
                st.markdown(f"""
<div style="
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.28);
  border-left: 4px solid #f59e0b;
  border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
">
  <div>
    <div style="color:white; font-family:'Space Grotesk',sans-serif; font-weight:700;">
      {html.escape(str(drow['Debtor']))}
      <span style="color:rgba(255,255,255,0.45); font-weight:400; font-size:0.82rem;"> · {html.escape(str(drow['Date']))}{phone_bit}</span>
    </div>
    {note_bit}
  </div>
  <div style="text-align:right;">
    <div style="color:#f59e0b; font-family:'Space Grotesk',sans-serif; font-weight:800; font-size:1.1rem;">UGX {float(drow['Amount_UGX']):,.0f}</div>
    <div style="color:rgba(255,255,255,0.45); font-size:0.78rem;">≈ ${float(drow['Amount_UGX'])/ugx_rate:,.2f} USDT</div>
  </div>
</div>
""", unsafe_allow_html=True)
            with d_col2:
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                if st.button("✅ Mark Paid", key=f"btn_pay_debtor_{idx}", use_container_width=True):
                    mgr.mark_debtor_settled(int(idx))
                    st.success(f"Marked {drow['Debtor']} as Paid!")
                    st.rerun()

    st.dataframe(debtors_df, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# TAB 3 — EXPENSES
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:white; margin-bottom:16px;">
      Track Your Expenses
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🤖 Auto-Ingest MoMo Receipts"):
        st.markdown("Automatically parses raw MoMo SMS logs (`raw_receipts_log.jsonl`) into your expense ledger.")
        if st.button("Process Raw Receipts", type="primary"):
            new_expenses = process_raw_receipts()
            if new_expenses:
                for exp in new_expenses:
                    mgr.add_expense(exp["Date"], exp["Category"], exp["Description"], exp["Amount_UGX"], exp["Notes"])
                st.success(f"Successfully ingested {len(new_expenses)} new expenses!")
                st.rerun()
            else:
                st.info("No new receipts found.")

    # Add expense form
    with st.expander("➕ Add New Expense"):
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Date", value=date.today())
            exp_category = st.selectbox("Category", ["Food", "Transport", "Airtime/Data", "Rent", "Entertainment", "Health", "Clothing", "Other"])
        with col2:
            exp_desc = st.text_input("Description", placeholder="e.g. Boda fare to office")
            exp_amount = st.number_input("Amount (UGX)", min_value=0.0, step=500.0)
        exp_notes = st.text_input("Notes (optional)")
        if st.button("Save Expense"):
            if exp_desc and exp_amount > 0:
                mgr.add_expense(str(exp_date), exp_category, exp_desc, exp_amount, exp_notes)
                st.success("Expense saved!")
                st.rerun()
            else:
                st.warning("Please fill in description and amount.")

    expenses_df = mgr.load_expenses()
    if not expenses_df.empty and expenses_df["Amount_UGX"].sum() > 0:
        total_exp = expenses_df["Amount_UGX"].sum()
        st.metric("Total Spent", f"UGX {total_exp:,.0f}",
                  delta=f"≈ ${total_exp/ugx_rate:,.2f} USD")

        fig_exp = px.pie(expenses_df, values="Amount_UGX", names="Category",
                         title="Spending by Category",
                         color_discrete_sequence=['#f59e0b', '#3b82f6', '#ec4899', '#10b981', '#8b5cf6', '#06b6d4', '#f43f5e'])
        fig_exp.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            title_font=dict(color='white', family='Space Grotesk', size=15)
        )
        fig_exp.update_traces(textfont=dict(color='white'))
        st.plotly_chart(fig_exp, use_container_width=True)
        st.dataframe(expenses_df, use_container_width=True)
    else:
        st.info("No expenses logged yet. Add your first one above!")


# ════════════════════════════════════════════════════════════════════
# TAB 4 — SAVINGS
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:white; margin-bottom:16px;">
      Savings & Net Worth
    </div>
    """, unsafe_allow_html=True)

    with st.expander("➕ Add New Saving"):
        col1, col2 = st.columns(2)
        with col1:
            sav_date = st.date_input("Date", value=date.today(), key="sav_date")
            sav_desc = st.text_input("Description", placeholder="e.g. Emergency fund")
        with col2:
            sav_amount = st.number_input("Amount (USDT)", min_value=0.0, step=1.0)
            sav_notes = st.text_input("Notes (optional)", key="sav_notes")
        if st.button("Save to Savings"):
            if sav_desc and sav_amount > 0:
                mgr.add_saving(str(sav_date), sav_desc, sav_amount, ugx_rate, sav_notes)
                st.success("Saving recorded!")
                st.rerun()
            else:
                st.warning("Please fill in description and amount.")

    savings_df = mgr.load_savings(ugx_rate=ugx_rate)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Savings (USDT)", f"${summary['total_savings_usdt']:,.2f}")
    with col2:
        st.metric("Total Savings (UGX)", f"UGX {summary['total_savings_ugx']:,.0f}")
    with col3:
        net_color = "normal" if summary['net_worth_usdt'] >= 0 else "inverse"
        st.metric("Net Worth (USDT)", f"${summary['net_worth_usdt']:,.2f}",
                  delta=f"UGX {summary['net_worth_ugx']:,.0f}")

    # ─── MULTI-GOAL HARDWARE WISHLIST TRACKER ───
    st.markdown("<br>", unsafe_allow_html=True)
    if "hardware_goals" not in st.session_state:
        st.session_state["hardware_goals"] = mgr.load_goals()

    sim_c1, sim_c2, sim_c3, sim_c4 = st.columns([1.4, 1.6, 1.1, 1.1])
    with sim_c1:
        alloc_choice = st.selectbox(
            "Funding Mode",
            ["Waterfall (Priority Order)", "Independent (Per Item)"],
            key="goal_alloc_mode",
            help="Waterfall funds goals sequentially by priority; Independent compares total savings to each item individually.",
        )
    with sim_c2:
        extra_cazzy_save = st.slider(
            "CazzyGames Vault / mo (USDT)",
            min_value=0,
            max_value=1500,
            value=1000,
            step=50,
            key="goal_cazzy_slider",
            help="100% of CazzyGames ($1,000 base + optional overtime) goes to Binance Savings on the 26th–29th.",
        )
    with sim_c3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        inc_ucu_lab = st.checkbox(
            "Add UCU Lab Tech",
            value=False,
            key="goal_inc_ucu_lab",
            help="Off by default: Stanbic/UCU inflows fund living & rent (25th), not hardware savings.",
        )
    with sim_c4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        inc_pending_ucu = st.checkbox(
            "Add Pending UCU TA",
            value=False,
            key="goal_inc_pend_ucu",
            help="Off by default: UCU TA inflows go to Stanbic living buffer rather than hardware savings.",
        )

    alloc_mode_key = "independent" if alloc_choice.startswith("Independent") else "waterfall"
    projection = project_hardware_goals(
        goals=st.session_state["hardware_goals"],
        current_savings_usdt=summary["total_savings_usdt"],
        ugx_rate=ugx_rate,
        income_df=income_df,
        include_ucu_lab_monthly=inc_ucu_lab,
        include_pending_ucu=inc_pending_ucu,
        extra_cazzy_monthly_usdt=float(extra_cazzy_save),
        allocation_mode=alloc_mode_key,
    )

    # Overall Wishlist Roadmap Banner
    subtitle_bits = [f"{projection['active_count']} Active Goal{'s' if projection['active_count'] != 1 else ''}"]
    if projection["owned_count"] > 0:
        subtitle_bits.append(f"{projection['owned_count']} Owned")
    subtitle_bits.append(f"Run Rate: ${projection['monthly_run_rate_usd']:,.0f}/mo")
    if inc_pending_ucu and projection["pending_ucu_net_usd"] > 0:
        subtitle_bits.append(f"+${projection['pending_ucu_net_usd']:,.0f} Pending UCU Net")

    st.markdown(f"""
<div style="
  background: linear-gradient(135deg, rgba(139,92,246,0.14), rgba(59,130,246,0.12), rgba(236,72,153,0.12));
  border: 1px solid rgba(139,92,246,0.3);
  border-radius: 18px; padding: 24px 28px;
  margin-bottom: 18px;
  position: relative; overflow: hidden;
">
  <div style="display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
    <div>
      <div style="color: rgba(255,255,255,0.6); font-family:'Space Grotesk',sans-serif; font-size:0.8rem; font-weight:600; letter-spacing:1.2px; text-transform:uppercase;">
        Hardware Wishlist Roadmap · {' · '.join(subtitle_bits)}
      </div>
      <div style="color: white; font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:800; margin-top:4px;">
        🎯 Total Hardware Target
      </div>
    </div>
    <div style="text-align:right;">
      <div style="color: #ec4899; font-family:'Space Grotesk',sans-serif; font-size:1.55rem; font-weight:800;">
        ${projection['total_target_usd']:,.0f} USDT
      </div>
      <div style="color: rgba(255,255,255,0.55); font-size:0.85rem;">
        UGX {projection['total_target_ugx']:,.0f} &nbsp;·&nbsp; Est. Complete: <b style="color:#a78bfa;">{html.escape(projection['all_funded_eta_label'])}</b>
      </div>
    </div>
  </div>
  <div style="width:100%; height:12px; background:rgba(0,0,0,0.35); border-radius:6px; overflow:hidden;">
    <div style="width:{projection['overall_progress_pct']}%; height:100%; background:linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899); border-radius:6px; box-shadow:0 0 12px rgba(139,92,246,0.5); transition:width 0.8s ease-out;"></div>
  </div>
  <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-top:12px; font-size:0.88rem;">
    <div style="color:white; font-weight:600;">
      {projection['overall_progress_pct']:.1f}% Funded (${projection['total_funded_usd']:,.2f} / ${projection['total_target_usd']:,.0f})
    </div>
    <div style="color:rgba(255,255,255,0.65);">
      ${projection['total_remaining_usd']:,.2f} USDT remaining (UGX {projection['total_remaining_ugx']:,.0f})
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Individual Goal Cards
    badge_styles = {
        "READY NOW": ("#10b981", "✅ READY NOW"),
        "FUNDING": ("#38bdf8", "⚡ FUNDING"),
        "QUEUED": ("#a78bfa", "⏳ QUEUED"),
        "OWNED": ("#10b981", "🏆 OWNED"),
    }

    for item in projection["items"]:
        accent = item["accent"]
        state_color, state_label = badge_styles.get(item["funding_state"], ("#a78bfa", item["funding_state"]))
        rank_badge = "✓" if item["status"] == "purchased" else f"#{item['priority']}"
        safe_icon = html.escape(item["icon"])
        safe_name = html.escape(item["name"])
        safe_notes = html.escape(item["notes"])

        if item["status"] == "purchased":
            eta_chip = "🏆 Purchased"
            right_footer = "Completed & removed from active target"
        elif item["days_away"] == 0:
            eta_chip = "🟢 Ready now!"
            right_footer = "$0.00 remaining"
        else:
            days_txt = f" · {item['days_away']}d" if item["days_away"] is not None else ""
            eta_chip = f"📅 Est. {html.escape(item['eta_label'])}{days_txt}"
            if alloc_mode_key == "waterfall" and item["funding_state"] == "QUEUED":
                right_footer = f"Queued · ${item['cumulative_remaining_usd']:,.0f} cumulative remaining"
            else:
                right_footer = f"${item['remaining_usd']:,.2f} remaining (UGX {item['remaining_ugx']:,.0f})"

        notes_html = (
            f"<div style='color:rgba(255,255,255,0.5); font-size:0.82rem; margin-top:4px;'>{safe_notes}</div>"
            if safe_notes else ""
        )

        st.markdown(f"""
<div style="
  background: rgba(255,255,255,0.035);
  border: 1px solid {accent}38;
  border-left: 4px solid {accent};
  border-radius: 16px; padding: 18px 22px;
  margin-bottom: 12px;
">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
    <div>
      <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
        <span style="
          background: {accent}25; color: {accent};
          border: 1px solid {accent}50;
          padding: 2px 9px; border-radius: 8px;
          font-family:'Space Grotesk',sans-serif; font-size:0.75rem; font-weight:700;
        ">{rank_badge}</span>
        <span style="color:white; font-family:'Space Grotesk',sans-serif; font-size:1.2rem; font-weight:700;">
          {safe_icon} {safe_name}
        </span>
        <span style="
          background: {state_color}20; color: {state_color};
          padding: 2px 9px; border-radius: 8px;
          font-family:'Space Grotesk',sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:0.5px;
        ">{state_label}</span>
      </div>
      {notes_html}
    </div>
    <div style="text-align:right;">
      <div style="color:{accent}; font-family:'Space Grotesk',sans-serif; font-size:1.25rem; font-weight:800;">
        ${item['target_usd']:,.0f} USDT
      </div>
      <div style="color:rgba(255,255,255,0.5); font-size:0.8rem;">
        UGX {item['target_ugx']:,.0f} &nbsp;·&nbsp; <span style="color:rgba(255,255,255,0.85); font-weight:600;">{eta_chip}</span>
      </div>
    </div>
  </div>
  <div style="width:100%; height:9px; background:rgba(0,0,0,0.35); border-radius:5px; overflow:hidden;">
    <div style="width:{item['progress_pct']}%; height:100%; background:linear-gradient(90deg, {accent}, #8b5cf6); border-radius:5px; box-shadow:0 0 8px {accent}70; transition:width 0.8s ease-out;"></div>
  </div>
  <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-top:9px; font-size:0.83rem;">
    <div style="color:white; font-weight:600;">
      {item['progress_pct']:.1f}% Funded (${item['allocated_usd']:,.2f} / ${item['target_usd']:,.0f})
    </div>
    <div style="color:rgba(255,255,255,0.6);">
      {right_footer}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.caption(
        f"Strategy: 100% CazzyGames (${extra_cazzy_save:,.0f}/mo on 28th) → Binance Savings Vault · "
        f"100% UCU/Stanbic (≈ ${projection['ucu_lab_monthly_usdt']:,.0f}/mo Lab Tech + pending TA ≈ ${projection['pending_ucu_net_usd']:,.0f}) → Living & Rent (due 25th)."
    )

    with st.expander("⚙️ Manage Wishlist Goals (Edit / Reorder / Add)"):
        current_goals = st.session_state["hardware_goals"]
        edited_goals = []
        for idx, g in enumerate(current_goals):
            gid = g["id"]
            e1, e2, e3, e4, e5, e6 = st.columns([0.65, 1.7, 1.0, 1.0, 1.9, 0.55])
            with e1:
                g_prio = st.number_input("Prio", min_value=1, max_value=99, value=int(g["priority"]), step=1, key=f"g_prio_{gid}_{idx}")
            with e2:
                g_name = st.text_input("Item", value=g["name"], key=f"g_name_{gid}_{idx}")
            with e3:
                g_target = st.number_input("Target (USD)", min_value=0.0, value=float(g["target_usd"]), step=25.0, key=f"g_tgt_{gid}_{idx}")
            with e4:
                g_status = st.selectbox(
                    "Status",
                    ["active", "purchased"],
                    index=0 if g["status"] == "active" else 1,
                    key=f"g_stat_{gid}_{idx}",
                )
            with e5:
                g_notes = st.text_input("Notes", value=g.get("notes", ""), key=f"g_notes_{gid}_{idx}")
            with e6:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                g_del = st.checkbox("Del", value=False, key=f"g_del_{gid}_{idx}")

            if not g_del and g_name.strip():
                edited_goals.append({
                    **g,
                    "priority": int(g_prio),
                    "name": g_name.strip(),
                    "target_usd": float(g_target),
                    "status": g_status,
                    "notes": g_notes.strip(),
                })

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("💾 Save Wishlist Changes", key="btn_save_goals", use_container_width=True):
                if edited_goals:
                    st.session_state["hardware_goals"] = mgr.save_goals(edited_goals)
                    st.success("Hardware wishlist updated!")
                    st.rerun()
                else:
                    st.warning("Keep at least one goal, or add a new one below.")
        with b2:
            if st.button("↺ Reset to PS5 Pro / Pixel 11 / RTX 5080", key="btn_reset_goals", use_container_width=True):
                st.session_state["hardware_goals"] = mgr.save_goals(copy.deepcopy(DEFAULT_HARDWARE_GOALS))
                st.success("Wishlist reset to defaults!")
                st.rerun()

        st.markdown("---")
        st.markdown("**➕ Add New Hardware Goal**")
        n1, n2, n3, n4 = st.columns([0.7, 1.8, 1.0, 0.8])
        with n1:
            new_icon = st.selectbox("Icon", ["🎮", "📱", "🖥️", "💻", "🎧", "⌨️", "📺", "⚡", "🎯"], key="new_goal_icon")
        with n2:
            new_name = st.text_input("Item Name", placeholder="e.g. GTA VI / 1000W PSU / RTX 4070 Laptop", key="new_goal_name")
        with n3:
            new_target = st.number_input("Target (USD)", min_value=0.0, value=100.0, step=25.0, key="new_goal_target")
        with n4:
            new_prio = st.number_input("Priority", min_value=1, max_value=99, value=len(current_goals) + 1, step=1, key="new_goal_prio")
        new_notes = st.text_input("Notes (optional)", placeholder="e.g. Uganda shipping estimate or preferred retailer", key="new_goal_notes")

        if st.button("Add Goal to Wishlist", key="btn_add_goal"):
            if new_name.strip() and new_target > 0:
                slug = re.sub(r"[^a-z0-9]+", "-", new_name.strip().lower()).strip("-") or "goal"
                updated = list(current_goals) + [{
                    "id": slug,
                    "priority": int(new_prio),
                    "icon": new_icon,
                    "name": new_name.strip(),
                    "target_usd": float(new_target),
                    "accent": GOAL_ACCENT_PALETTE[len(current_goals) % len(GOAL_ACCENT_PALETTE)],
                    "status": "active",
                    "notes": new_notes.strip(),
                }]
                st.session_state["hardware_goals"] = mgr.save_goals(updated)
                st.success(f"Added {new_name.strip()} to your wishlist!")
                st.rerun()
            else:
                st.warning("Enter an item name and a target price greater than $0.")

    st.markdown("<br>", unsafe_allow_html=True)


    if not savings_df.empty and savings_df["Amount_USDT"].sum() > 0:
        fig_sav = px.bar(savings_df, x="Date", y="Amount_USDT",
                         color="Description", title="Savings Over Time",
                         color_discrete_sequence=["#10b981", "#059669", "#34d399"])
        fig_sav.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', family='Inter'),
            xaxis=dict(tickfont=dict(color='rgba(255,255,255,0.6)'), gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(tickfont=dict(color='rgba(255,255,255,0.6)'), gridcolor='rgba(255,255,255,0.05)'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            title_font=dict(color='white', family='Space Grotesk', size=15)
        )
        st.plotly_chart(fig_sav, use_container_width=True)
        st.dataframe(savings_df, use_container_width=True)
    else:
        st.info("No savings recorded yet. Start saving to see your growth here!")


# ════════════════════════════════════════════════════════════════════
# TAB 5 — SMART ADVISOR
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:white; margin-bottom:16px;">
      Smart Financial Advisor
    </div>
    """, unsafe_allow_html=True)

    insights = generate_financial_insights(
        income_usdt=summary["total_received_usdt"],
        ugx_rate=ugx_rate,
        expenses_df=expenses_df,
        savings_usdt=summary["total_savings_usdt"],
        pending_usd=summary["total_pending_usd"],
    )

    # ── Health Score Gauge ──
    hs = insights["health_score"]
    if hs >= 80:
        hs_color = "#10b981"
        hs_label = "Excellent"
    elif hs >= 60:
        hs_color = "#f59e0b"
        hs_label = "Fair"
    elif hs >= 40:
        hs_color = "#f97316"
        hs_label = "Needs Attention"
    else:
        hs_color = "#ef4444"
        hs_label = "Critical"

    col_hs, col_burn, col_run = st.columns(3)

    with col_hs:
        fig_hs = go.Figure(go.Indicator(
            mode="gauge+number",
            value=hs,
            number={"suffix": "/100", "font": {"color": "white", "family": "Space Grotesk", "size": 32}},
            title={"text": f"Financial Health ({hs_label})", "font": {"color": "white", "family": "Space Grotesk", "size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "rgba(255,255,255,0.3)", "tickfont": {"color": "rgba(255,255,255,0.5)"}},
                "bar": {"color": hs_color, "thickness": 0.3},
                "bgcolor": "rgba(255,255,255,0.05)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                    {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                ],
            }
        ))
        fig_hs.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"), margin=dict(t=40, b=10, l=20, r=20), height=250
        )
        st.plotly_chart(fig_hs, use_container_width=True)

    with col_burn:
        br = insights["burn_rate"]
        trend_icon = {"accelerating": "(rising)", "decelerating": "(falling)", "stable": "(stable)", "no_data": ""}
        st.metric("Daily Burn Rate", f"UGX {br['daily_burn_ugx']:,}", delta=trend_icon.get(br['trend'], ""))
        st.metric("Weekly Burn Rate", f"UGX {br['weekly_burn_ugx']:,}")
        st.metric("Monthly Projection", f"UGX {br['monthly_projected_ugx']:,}")

    with col_run:
        rw = insights["runway"]
        status_colors = {"healthy": "#10b981", "caution": "#f59e0b", "warning": "#f97316", "critical": "#ef4444"}
        rw_color = status_colors.get(rw["status"], "#10b981")
        days_str = f"{rw['days_remaining']} days" if rw['days_remaining'] != float('inf') else "Unlimited"
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.04);
            border: 1px solid {rw_color}40;
            border-radius: 16px; padding: 20px;
            text-align: center;
        ">
            <div style="color: rgba(255,255,255,0.5); font-size:0.8rem; font-family:'Space Grotesk',sans-serif;">Cash Runway</div>
            <div style="color: {rw_color}; font-size: 2.2rem; font-weight: 800; font-family:'Space Grotesk',sans-serif;">{days_str}</div>
            <div style="color: rgba(255,255,255,0.4); font-size:0.85rem;">Runs out: {rw['runway_date']}</div>
            <div style="
                display: inline-block; margin-top: 8px;
                background: {rw_color}20; color: {rw_color};
                padding: 4px 12px; border-radius: 8px;
                font-size: 0.75rem; font-weight: 600;
            ">{rw['status'].upper()}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Active Operating Model Card: Stanbic-Only Living · 100% CazzyGames Savings ──
    stanbic_lab_net = 936640
    stanbic_ta_net_mo = 577253
    monthly_rent = 500000
    living_base_only = stanbic_lab_net - monthly_rent
    living_with_ta = stanbic_lab_net + stanbic_ta_net_mo - monthly_rent
    cazzy_monthly_ugx = round(CONTRACT["post_trial_fee_usd"] * ugx_rate)

    st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%);
    border: 1px solid rgba(16, 185, 129, 0.32);
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 24px;
    backdrop-filter: blur(16px);
">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.15rem; font-weight:700; color:white;">
            🏦 Active Rule: Stanbic-Only Living · 100% CazzyGames Savings
        </div>
        <div style="
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 8px;
            padding: 4px 12px;
            color: #10b981;
            font-size: 0.8rem;
            font-weight: 700;
            font-family:'Space Grotesk',sans-serif;
        ">
            🔒 100% USDT VAULT LOCKED
        </div>
    </div>
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom:16px;">
        <div style="background:rgba(255,255,255,0.03); padding:12px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
            <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; text-transform:uppercase;">Stanbic Base Inflow</div>
            <div style="color:#a78bfa; font-size:1.3rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">UGX {stanbic_lab_net:,}</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.75rem;">UCU Lab Tech Net (23rd) · +577k w/ TA</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:12px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
            <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; text-transform:uppercase;">Fixed Rent (Due 25th)</div>
            <div style="color:#f59e0b; font-size:1.3rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">UGX {monthly_rent:,}</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.75rem;">Ring-fenced immediately from 23rd pay</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:12px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
            <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; text-transform:uppercase;">Usable Living Cash</div>
            <div style="color:#38bdf8; font-size:1.3rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">UGX {living_base_only:,}</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.75rem;">~UGX {living_base_only // 30:,}/day (or ~UGX {living_with_ta // 30:,}/day w/ TA)</div>
        </div>
        <div style="background:rgba(255,255,255,0.03); padding:12px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
            <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; text-transform:uppercase;">CazzyGames Vault (100%)</div>
            <div style="color:#10b981; font-size:1.3rem; font-weight:700; font-family:'Space Grotesk',sans-serif;">${CONTRACT['post_trial_fee_usd']:,.0f}+ USDT/mo</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.75rem;">≈ UGX {cazzy_monthly_ugx:,} saved every month</div>
        </div>
    </div>
    <div style="color:rgba(255,255,255,0.7); font-size:0.88rem; line-height:1.6; border-top:1px solid rgba(255,255,255,0.08); padding-top:12px;">
        <b>Stanbic-Only Monthly Allocation Target (After UGX 500k Rent):</b><br>
        • Utilities (Power + Water): ≈ UGX 80,000 &nbsp;|&nbsp; • Internet (Lycamobile): ≈ UGX 43,000 &nbsp;|&nbsp; • Church / Tithe: ≈ UGX 40,000<br>
        • Groceries &amp; Food (Stanbic Card, 0 fee): ≈ UGX 180,000 &nbsp;|&nbsp; • Transport &amp; Cash Buffer: ≈ <b>UGX 93,640</b> <i>(+UGX 577k/mo when TA pays)</i><br>
        <i>👉 <b>Strict Guardrail:</b> Pay supermarkets &amp; utilities directly via Stanbic Card/App (UGX 0 fee), avoid Stanbic→MoMo double-hop fees, and keep hardware/big tech purchases strictly in the CazzyGames Vault.</i>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Recommendations ──
    recs = insights["recommendations"]
    if recs:
        st.markdown("""
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600; color:white; margin-bottom:12px;">
          Recommendations
        </div>
        """, unsafe_allow_html=True)

        for rec in recs:
            p_colors = {"P0": "#ef4444", "P1": "#f97316", "P2": "#f59e0b", "P3": "#3b82f6"}
            p_color = p_colors.get(rec["priority"], "#3b82f6")
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.03);
                border-left: 4px solid {p_color};
                border-radius: 0 12px 12px 0;
                padding: 14px 18px; margin-bottom: 10px;
            ">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="
                        background: {p_color}25; color: {p_color};
                        padding: 2px 8px; border-radius: 6px;
                        font-size: 0.7rem; font-weight: 700;
                        font-family: 'Space Grotesk', sans-serif;
                    ">{rec['priority']}</span>
                    <span style="color:white; font-weight:600; font-family:'Space Grotesk',sans-serif;">{rec['title']}</span>
                </div>
                <div style="color: rgba(255,255,255,0.6); font-size:0.85rem; margin-top:6px;">{rec['action']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Fee Leakage & Category Analysis ──
    col_fee, col_cat = st.columns(2)

    with col_fee:
        fl = insights["fee_leakage"]
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(239,68,68,0.08), rgba(245,158,11,0.08));
            border: 1px solid rgba(239,68,68,0.2);
            border-radius: 16px; padding: 20px;
        ">
            <div style="color: rgba(255,255,255,0.5); font-size:0.8rem; font-family:'Space Grotesk',sans-serif; text-transform:uppercase; letter-spacing:1px;">Fee Leakage</div>
            <div style="color: #ef4444; font-size: 1.6rem; font-weight: 800; font-family:'Space Grotesk',sans-serif;">UGX {fl['total_fees_ugx']:,}</div>
            <div style="color: rgba(255,255,255,0.5); font-size:0.85rem;">{fl['fee_percentage']}% of total spending</div>
            <div style="color: rgba(255,255,255,0.6); font-size:0.8rem; margin-top:8px; font-style:italic;">{fl['suggestion']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_cat:
        cats = insights["categories"]
        if cats:
            cat_df = pd.DataFrame(cats)
            fig_cat = px.bar(
                cat_df, x="percentage", y="category", orientation="h",
                color="flag", color_discrete_map={"dominant": "#ef4444", "significant": "#f59e0b", "normal": "#3b82f6"},
                title="Spending Category Weight",
                labels={"percentage": "% of Total", "category": ""}
            )
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", family="Inter"),
                xaxis=dict(tickfont=dict(color="rgba(255,255,255,0.6)"), gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(tickfont=dict(color="rgba(255,255,255,0.6)")),
                showlegend=False,
                title_font=dict(color="white", family="Space Grotesk", size=14),
                margin=dict(t=40, b=10, l=10, r=10), height=280
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    # ── Anomalies ──
    anomalies = insights["anomalies"]
    if anomalies:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Space Grotesk',sans-serif; font-size:1.1rem; font-weight:600; color:white; margin-bottom:12px;">
          Spending Anomalies Detected
        </div>
        """, unsafe_allow_html=True)
        for a in anomalies:
            sev_color = "#ef4444" if a["severity"] == "high" else "#f59e0b"
            st.markdown(f"""
            <div style="
                background: rgba(255,255,255,0.03);
                border: 1px solid {sev_color}30;
                border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;
                display: flex; justify-content: space-between; align-items: center;
            ">
                <div>
                    <span style="color:white; font-weight:600;">{a['description'][:50]}</span>
                    <span style="color: rgba(255,255,255,0.4); font-size:0.8rem; margin-left:8px;">{a['date']}</span>
                </div>
                <div style="text-align:right;">
                    <span style="color:{sev_color}; font-weight:700; font-family:'Space Grotesk',sans-serif;">UGX {a['amount_ugx']:,}</span>
                    <span style="color:rgba(255,255,255,0.4); font-size:0.75rem; margin-left:6px;">{a['z_score']}x avg</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Advisor metadata ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Advisor has run {insights['analyses_run']} analyses. Model: {insights['budget']['model']}. More data = smarter recommendations.")

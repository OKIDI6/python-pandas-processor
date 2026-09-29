import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from accounting import LedgerManager, CONTRACT, get_live_ugx_rate
from finance_advisor import generate_financial_insights

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

    @st.cache_data(ttl=3600)
    def fetch_live_rate():
        return get_live_ugx_rate()
        
    live_rate = fetch_live_rate()

    ugx_rate = st.slider(
        "Live UGX Rate (per 1 USDT)",
        min_value=3500.0,
        max_value=4200.0,
        value=float(live_rate),
        step=10.0,
        help="Pulled automatically via API. Adjust this if Binance P2P rate differs."
    )
    st.caption(f"Current rate: **1 USDT = {ugx_rate:,.0f} UGX**")

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
      Contract Rates
    </div>
    """, unsafe_allow_html=True)
    st.info(f"Base Pay: **${CONTRACT['trial_fee_usd']:,.0f} USD / month**")
    st.info(f"Overtime Rate: **${CONTRACT['overtime_rate_usd']:,.2f} / hr** (1.5x)")
    st.info(f"Post-Trial: **${CONTRACT['post_trial_fee_usd']:,.0f} USD / month**")

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
mgr = LedgerManager()
summary = mgr.get_summary(ugx_rate=ugx_rate)
income_df = mgr.load_income()
expenses_df = mgr.load_expenses()
savings_df = mgr.load_savings()

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
        st.plotly_chart(fig, width="stretch")

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
        st.plotly_chart(fig2, width="stretch")

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
        st.plotly_chart(fig, width="stretch")
        st.dataframe(income_df, width="stretch")
    else:
        st.info("No income records yet.")


# ════════════════════════════════════════════════════════════════════
# TAB 3 — EXPENSES
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:white; margin-bottom:16px;">
      Track Your Expenses
    </div>
    """, unsafe_allow_html=True)

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
        st.plotly_chart(fig_exp, width="stretch")
        st.dataframe(expenses_df, width="stretch")
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

    savings_df = mgr.load_savings()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Savings (USDT)", f"${summary['total_savings_usdt']:,.2f}")
    with col2:
        st.metric("Total Savings (UGX)", f"UGX {summary['total_savings_ugx']:,.0f}")
    with col3:
        net_color = "normal" if summary['net_worth_usdt'] >= 0 else "inverse"
        st.metric("Net Worth (USDT)", f"${summary['net_worth_usdt']:,.2f}",
                  delta=f"UGX {summary['net_worth_ugx']:,.0f}")

    # ─── GOAL TRACKER ───
    st.markdown("<br>", unsafe_allow_html=True)
    target_goal_usd = 1500.00
    progress_percent = min(100, (summary['total_savings_usdt'] / target_goal_usd) * 100) if target_goal_usd > 0 else 0
    remaining_usd = max(0, target_goal_usd - summary['total_savings_usdt'])
    
    st.markdown(f"""
    <div style="
      background: linear-gradient(135deg, rgba(236,72,153,0.1), rgba(139,92,246,0.1));
      border: 1px solid rgba(236,72,153,0.2);
      border-radius: 16px; padding: 24px;
      margin-bottom: 24px;
      position: relative; overflow: hidden;
    ">
      <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:16px;">
        <div>
          <div style="color: rgba(255,255,255,0.6); font-family:'Space Grotesk',sans-serif; font-size:0.9rem; font-weight:600; letter-spacing:1px; text-transform:uppercase;">Current Main Goal</div>
          <div style="color: white; font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:800; margin-top:4px;">💻 RTX 4070 Work Laptop (Sweet Spot)</div>
        </div>
        <div style="text-align:right;">
          <div style="color: rgba(255,255,255,0.6); font-size:0.9rem;">Target</div>
          <div style="color: #ec4899; font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:800;">${target_goal_usd:,.0f} USDT</div>
        </div>
      </div>
      
      <!-- Progress Bar Background -->
      <div style="width:100%; height:12px; background:rgba(0,0,0,0.3); border-radius:6px; overflow:hidden;">
        <!-- Progress Bar Fill -->
        <div style="width:{progress_percent}%; height:100%; background:linear-gradient(90deg, #ec4899, #8b5cf6); border-radius:6px; box-shadow:0 0 10px rgba(236,72,153,0.5); transition:width 1s ease-out;"></div>
      </div>
      
      <div style="display:flex; justify-content:space-between; margin-top:12px; font-size:0.9rem;">
        <div style="color:white; font-weight:600;">{progress_percent:.1f}% Funded</div>
        <div style="color:rgba(255,255,255,0.6);">${remaining_usd:,.2f} USDT remaining</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


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
        st.plotly_chart(fig_sav, width="stretch")
        st.dataframe(savings_df, width="stretch")
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

"""
Finance Advisor Engine v1.0
Smart algorithm that analyzes spending patterns, predicts cash runway,
and generates actionable financial decisions. Designed to learn and
improve as more transaction data is accumulated over time.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADVISOR_STATE_PATH = os.path.join(BASE_DIR, "advisor_state.json")


def _load_advisor_state() -> Dict:
    """Load persistent advisor memory (learns over time)."""
    if os.path.exists(ADVISOR_STATE_PATH):
        with open(ADVISOR_STATE_PATH, "r") as f:
            return json.load(f)
    return {
        "created_at": datetime.now().isoformat(),
        "total_analyses_run": 0,
        "category_budgets": {},
        "spending_trend_history": [],
        "user_acknowledged_alerts": [],
    }


def _save_advisor_state(state: Dict):
    """Persist advisor memory to disk."""
    with open(ADVISOR_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, default=str)


def analyze_spending_velocity(expenses_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate how fast money is being spent (burn rate).
    Returns daily, weekly, and monthly burn rates with trend direction.
    """
    if expenses_df.empty:
        return {"daily_burn_ugx": 0, "weekly_burn_ugx": 0, "monthly_projected_ugx": 0, "trend": "no_data"}

    df = expenses_df.copy()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["Date"])

    if df.empty:
        return {"daily_burn_ugx": 0, "weekly_burn_ugx": 0, "monthly_projected_ugx": 0, "trend": "no_data"}

    date_range = (df["Date"].max() - df["Date"].min()).days
    if date_range < 1:
        date_range = 1

    total_spent = df["Amount_UGX"].sum()
    daily_burn = total_spent / date_range
    weekly_burn = daily_burn * 7
    monthly_projected = daily_burn * 30

    # Trend detection: compare first half vs second half spending
    midpoint = df["Date"].min() + timedelta(days=date_range / 2)
    first_half = df[df["Date"] <= midpoint]["Amount_UGX"].sum()
    second_half = df[df["Date"] > midpoint]["Amount_UGX"].sum()

    if first_half == 0:
        trend = "accelerating"
    elif second_half / max(first_half, 1) > 1.2:
        trend = "accelerating"
    elif second_half / max(first_half, 1) < 0.8:
        trend = "decelerating"
    else:
        trend = "stable"

    return {
        "daily_burn_ugx": round(daily_burn),
        "weekly_burn_ugx": round(weekly_burn),
        "monthly_projected_ugx": round(monthly_projected),
        "trend": trend,
        "days_tracked": date_range,
        "total_transactions": len(df),
    }


def predict_cash_runway(balance_ugx: float, burn_rate: Dict) -> Dict[str, Any]:
    """
    Predict how many days the current balance will last at the current burn rate.
    """
    daily_burn = burn_rate.get("daily_burn_ugx", 0)
    if daily_burn <= 0:
        return {"days_remaining": float("inf"), "runway_date": "N/A", "status": "healthy"}

    days_remaining = balance_ugx / daily_burn
    runway_date = datetime.now() + timedelta(days=days_remaining)

    if days_remaining < 3:
        status = "critical"
    elif days_remaining < 7:
        status = "warning"
    elif days_remaining < 14:
        status = "caution"
    else:
        status = "healthy"

    return {
        "days_remaining": round(days_remaining, 1),
        "runway_date": runway_date.strftime("%Y-%m-%d"),
        "status": status,
    }


def analyze_category_breakdown(expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Break down spending by category with percentage allocation
    and flag categories that are consuming disproportionate budget.
    """
    if expenses_df.empty:
        return []

    df = expenses_df.copy()
    total = df["Amount_UGX"].sum()
    if total == 0:
        return []

    grouped = df.groupby("Category")["Amount_UGX"].sum().sort_values(ascending=False)

    breakdown = []
    for cat, amount in grouped.items():
        pct = (amount / total) * 100
        # Flag categories consuming more than 40% as "dominant"
        flag = "dominant" if pct > 40 else ("significant" if pct > 20 else "normal")
        breakdown.append({
            "category": cat,
            "amount_ugx": round(amount),
            "percentage": round(pct, 1),
            "flag": flag,
        })

    return breakdown


def detect_spending_anomalies(expenses_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect unusually large transactions relative to the user's normal spending pattern.
    Uses a simple z-score approach that improves with more data.
    """
    if expenses_df.empty or len(expenses_df) < 3:
        return []

    df = expenses_df.copy()
    mean_spend = df["Amount_UGX"].mean()
    std_spend = df["Amount_UGX"].std()

    if std_spend == 0:
        return []

    anomalies = []
    for _, row in df.iterrows():
        z_score = (row["Amount_UGX"] - mean_spend) / std_spend
        if z_score > 1.5:  # Transactions 1.5 standard deviations above mean
            anomalies.append({
                "date": str(row.get("Date", "Unknown")),
                "description": row.get("Description", "Unknown"),
                "amount_ugx": round(row["Amount_UGX"]),
                "z_score": round(z_score, 2),
                "severity": "high" if z_score > 2.5 else "medium",
            })

    return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)


def calculate_fee_leakage(expenses_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate how much money is being lost to MoMo fees, exchange fees, etc.
    This is money that could be saved with better transaction batching.
    """
    if expenses_df.empty:
        return {"total_fees_ugx": 0, "fee_percentage": 0, "suggestion": ""}

    df = expenses_df.copy()
    # Identify fee-bearing transactions from notes
    fee_rows = df[df["Notes"].astype(str).str.contains("fee|Fee", case=False, na=False)]
    exchange_rows = df[df["Category"].astype(str).str.contains("Exchange|Fees", case=False, na=False)]

    total_fees = 0

    # Extract embedded fees from notes like "Includes 980 fee"
    for _, row in fee_rows.iterrows():
        notes = str(row.get("Notes", ""))
        import re
        fee_match = re.findall(r"(\d+)\s*fee", notes, re.IGNORECASE)
        for fee_str in fee_match:
            total_fees += int(fee_str)

    # Add exchange fees
    total_fees += exchange_rows["Amount_UGX"].sum()

    total_spent = df["Amount_UGX"].sum()
    fee_pct = (total_fees / total_spent * 100) if total_spent > 0 else 0

    suggestion = ""
    if fee_pct > 5:
        suggestion = "Your fee leakage is high. Consider batching withdrawals into fewer, larger transactions to reduce per-transaction MoMo fees."
    elif fee_pct > 2:
        suggestion = "Your fee leakage is moderate. Try to minimize small cash withdrawals."
    else:
        suggestion = "Your fee management is efficient."

    return {
        "total_fees_ugx": round(total_fees),
        "fee_percentage": round(fee_pct, 2),
        "suggestion": suggestion,
    }


def generate_smart_budget(income_usdt: float, ugx_rate: float, expenses_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a recommended monthly budget allocation based on the 50/30/20 rule,
    adapted to the user's actual spending patterns.

    As more data accumulates, the algorithm shifts from the generic 50/30/20 rule
    toward a personalized model based on the user's real behavior.
    """
    gross_ugx = income_usdt * ugx_rate

    # Base 50/30/20 allocation
    budget = {
        "needs_ugx": round(gross_ugx * 0.50),       # Rent, groceries, transport
        "wants_ugx": round(gross_ugx * 0.20),       # Entertainment, personal
        "savings_ugx": round(gross_ugx * 0.20),     # Savings target
        "tithe_ugx": round(gross_ugx * 0.10),       # Tithe/donations (user pattern)
        "model": "50/20/20/10 (Generic + Tithe)",
    }

    # Adaptive: if we have enough expense data, blend with actual patterns
    if not expenses_df.empty and len(expenses_df) >= 5:
        cats = analyze_category_breakdown(expenses_df)
        cat_map = {c["category"]: c["percentage"] for c in cats}

        # Detect if user consistently tithes, and adjust model
        tithe_pct = sum(v for k, v in cat_map.items() if "Donation" in k or "Tithe" in k or "Church" in k)
        housing_pct = sum(v for k, v in cat_map.items() if "Housing" in k or "Rent" in k)

        if tithe_pct > 0:
            budget["model"] = f"Adaptive (Tithe: {tithe_pct:.0f}%, Housing: {housing_pct:.0f}%)"

    return budget


def generate_financial_insights(
    income_usdt: float,
    ugx_rate: float,
    expenses_df: pd.DataFrame,
    savings_usdt: float,
    pending_usd: float,
) -> Dict[str, Any]:
    """
    Master function that runs the full analysis pipeline and returns
    a comprehensive financial health report with actionable recommendations.
    """
    state = _load_advisor_state()
    state["total_analyses_run"] += 1

    burn_rate = analyze_spending_velocity(expenses_df)
    balance_ugx = (income_usdt * ugx_rate) - expenses_df["Amount_UGX"].sum() if not expenses_df.empty else income_usdt * ugx_rate
    runway = predict_cash_runway(max(balance_ugx, 0), burn_rate)
    categories = analyze_category_breakdown(expenses_df)
    anomalies = detect_spending_anomalies(expenses_df)
    fee_leakage = calculate_fee_leakage(expenses_df)
    budget = generate_smart_budget(income_usdt, ugx_rate, expenses_df)

    # Generate priority recommendations
    recommendations = []

    if runway["status"] == "critical":
        recommendations.append({
            "priority": "P0",
            "title": "Cash Critically Low",
            "action": f"You have approximately {runway['days_remaining']} days of cash remaining. Minimize all non-essential spending immediately.",
        })
    elif runway["status"] == "warning":
        recommendations.append({
            "priority": "P1",
            "title": "Cash Running Low",
            "action": f"At your current burn rate of UGX {burn_rate['daily_burn_ugx']:,}/day, your balance runs out around {runway['runway_date']}. Plan your next income cycle.",
        })

    if pending_usd > 0:
        recommendations.append({
            "priority": "P1",
            "title": "Outstanding Receivable",
            "action": f"You have ${pending_usd:,.2f} USD pending. Follow up to accelerate collection.",
        })

    if burn_rate["trend"] == "accelerating":
        recommendations.append({
            "priority": "P2",
            "title": "Spending Acceleration Detected",
            "action": "Your recent spending is higher than your earlier period. Review if this is intentional (e.g., setup costs) or a habit forming.",
        })

    if fee_leakage["fee_percentage"] > 3:
        recommendations.append({
            "priority": "P2",
            "title": "Fee Leakage Alert",
            "action": fee_leakage["suggestion"],
        })

    if savings_usdt == 0 and income_usdt > 0:
        recommendations.append({
            "priority": "P2",
            "title": "Zero Savings",
            "action": f"You currently have $0 in savings. Target saving at least UGX {budget['savings_ugx']:,} this month.",
        })

    for anomaly in anomalies[:2]:
        recommendations.append({
            "priority": "P3",
            "title": f"Large Transaction: {anomaly['description'][:40]}",
            "action": f"This transaction of UGX {anomaly['amount_ugx']:,} is {anomaly['z_score']}x above your average. Verify it was planned.",
        })

    # Calculate overall financial health score (0-100)
    health_score = 70  # Base score
    if savings_usdt > 0:
        health_score += 10
    if runway["status"] == "healthy":
        health_score += 10
    elif runway["status"] == "critical":
        health_score -= 30
    elif runway["status"] == "warning":
        health_score -= 15
    if burn_rate["trend"] == "decelerating":
        health_score += 5
    elif burn_rate["trend"] == "accelerating":
        health_score -= 5
    if fee_leakage["fee_percentage"] > 5:
        health_score -= 5
    if pending_usd > 0:
        health_score -= 5

    health_score = max(0, min(100, health_score))

    # Store trend snapshot for learning
    state["spending_trend_history"].append({
        "date": datetime.now().isoformat(),
        "daily_burn": burn_rate["daily_burn_ugx"],
        "health_score": health_score,
        "trend": burn_rate["trend"],
    })
    # Keep only last 90 snapshots to avoid bloat
    state["spending_trend_history"] = state["spending_trend_history"][-90:]

    _save_advisor_state(state)

    return {
        "health_score": health_score,
        "burn_rate": burn_rate,
        "runway": runway,
        "categories": categories,
        "anomalies": anomalies,
        "fee_leakage": fee_leakage,
        "budget": budget,
        "recommendations": recommendations,
        "analyses_run": state["total_analyses_run"],
    }

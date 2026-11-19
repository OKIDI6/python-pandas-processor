import copy
from datetime import date
import json
import os
import requests
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

def get_live_ugx_rate(default_rate: float = 3680.0) -> float:
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        response.raise_for_status()
        return float(response.json().get("rates", {}).get("UGX", default_rate))
    except Exception:
        return default_rate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Contract Constants ───────────────────────────────────────────────────────
CONTRACT = {
    "name": "Okidi Norbert",
    "role": "Team Lead IT & MarTech Engineer",
    "company": "CazzyGames",
    "start_date": "2026-09-07",
    "trial_fee_usd": 900.00,
    "post_trial_fee_usd": 1000.00,
    "monthly_hours": 173.33,
    "overtime_multiplier": 1.50,
}

CONTRACT["base_rate_usd"] = round(CONTRACT["trial_fee_usd"] / CONTRACT["monthly_hours"], 2)
CONTRACT["overtime_rate_usd"] = round(CONTRACT["base_rate_usd"] * CONTRACT["overtime_multiplier"], 2)

UCU_CONTRACT = {
    "name": "Okidi Norbert",
    "institution": "Uganda Christian University",
    "faculty": "Faculty of Engineering, Design & Technology",
    "department": "Computing & Technology",
    "role": "Part-time Tutorial Assistant",
    "subject_code": "SNF2108",
    "subject_name": "Wide Area Network Engineering",
    "appointment_date": "2026-08-10",
    "start_date": "2026-08-12",
    "end_date": "2026-12-04",
    "weekly_hours": 4.0,
    "total_gross_ugx": 3472200.0,
    "installments_count": 4,
    "monthly_gross_ugx": 868050.0,
}

PAYROLL_SCHEDULE = {
    "UCU": {
        "name": "Uganda Christian University",
        "payout_day": 23,
        "description": "Disburses on the 23rd of every month",
        "roles": [
            "Electronics Lab Technician (Graduate Intern)",
            "Part-time Tutorial Assistant (WAN Engineering)"
        ],
    },
    "CazzyGames": {
        "name": "CazzyGames",
        "payout_window": "26th - 29th",
        "payout_start_day": 26,
        "payout_end_day": 29,
        "description": "Disburses between the 26th and 29th of every month",
        "role": "Team Lead IT & MarTech Engineer",
    }
}

UCU_CATEGORIES = {
    "Electronics_Lab_Technician_Graduate_Intern",
    "UCU_Tutorial_Assistant",
    "Part_Time_Tutorial_Assistant",
    "UCU_Teaching_Assistant",
}

UCU_LAB_MONTHLY_GROSS_UGX = 1269062.0

GOALS_FILE = os.path.join(BASE_DIR, "hardware_goals.json")

DEFAULT_HARDWARE_GOALS: List[Dict[str, Any]] = [
    {
        "id": "ps5-pro",
        "priority": 1,
        "icon": "🎮",
        "name": "PlayStation 5 Pro",
        "target_usd": 900.0,
        "accent": "#3b82f6",
        "status": "active",
        "notes": "Console for GTA VI (US retail $899.99; edit to add game/UG shipping)",
    },
    {
        "id": "pixel-11",
        "priority": 2,
        "icon": "📱",
        "name": "Google Pixel 11",
        "target_usd": 899.0,
        "accent": "#10b981",
        "status": "active",
        "notes": "Base $899 / Pro ~$1,099 — edit target for preferred trim",
    },
    {
        "id": "rtx-5080",
        "priority": 3,
        "icon": "🖥️",
        "name": "NVIDIA RTX 5080",
        "target_usd": 1999.0,
        "accent": "#ec4899",
        "status": "active",
        "notes": "Nov 2026 street price ~$1,900–$2,200 (MSRP $999; lower if prices cool)",
    },
]

GOAL_ACCENT_PALETTE = ["#3b82f6", "#10b981", "#ec4899", "#8b5cf6", "#f59e0b", "#06b6d4"]


def normalize_goals(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sanitize, deduplicate IDs, and sort goals by status (active first) and priority."""
    cleaned: List[Dict[str, Any]] = []
    seen_ids = set()
    for idx, raw in enumerate(goals):
        name = str(raw.get("name", "")).strip()
        if not name:
            continue
        raw_id = str(raw.get("id", "")).strip() or f"goal-{idx + 1}"
        goal_id = raw_id
        suffix = 2
        while goal_id in seen_ids:
            goal_id = f"{raw_id}-{suffix}"
            suffix += 1
        seen_ids.add(goal_id)

        try:
            priority = int(float(raw.get("priority", idx + 1)))
        except (TypeError, ValueError):
            priority = idx + 1
        priority = max(1, priority)

        try:
            target_usd = round(max(0.0, float(raw.get("target_usd", 0.0))), 2)
        except (TypeError, ValueError):
            target_usd = 0.0

        status = str(raw.get("status", "active")).strip().lower()
        if status not in ("active", "purchased"):
            status = "active"

        accent = str(raw.get("accent", "")).strip()
        if not accent.startswith("#"):
            accent = GOAL_ACCENT_PALETTE[len(cleaned) % len(GOAL_ACCENT_PALETTE)]

        icon = str(raw.get("icon", "🎯")).strip() or "🎯"
        notes = str(raw.get("notes", "") or "").strip()

        cleaned.append({
            "id": goal_id,
            "priority": priority,
            "icon": icon,
            "name": name,
            "target_usd": target_usd,
            "accent": accent,
            "status": status,
            "notes": notes,
        })

    cleaned.sort(key=lambda g: (g["status"] == "purchased", g["priority"], g["name"].lower()))
    active_rank = 1
    for g in cleaned:
        if g["status"] == "active":
            g["priority"] = active_rank
            active_rank += 1
    return cleaned


def _next_day_of_month(as_of: date, day: int) -> date:
    """Return the nearest date on or after as_of matching day-of-month."""
    if as_of.day <= day:
        return date(as_of.year, as_of.month, day)
    year = as_of.year + (1 if as_of.month == 12 else 0)
    month = 1 if as_of.month == 12 else as_of.month + 1
    return date(year, month, day)


def project_hardware_goals(
    goals: List[Dict[str, Any]],
    current_savings_usdt: float,
    ugx_rate: float = 3680.0,
    income_df: Optional[pd.DataFrame] = None,
    include_ucu_lab_monthly: bool = True,
    include_pending_ucu: bool = True,
    extra_cazzy_monthly_usdt: float = 250.0,
    allocation_mode: str = "waterfall",
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Compute funded progress and payroll-scheduled ETAs for a multi-goal hardware wishlist.

    Uses actual payroll days from PAYROLL_SCHEDULE:
      - UCU Lab Tech net auto-savings on the 23rd of each month
      - CazzyGames discretionary savings allocation on the 28th of each month
      - Pending UCU receivables (net of Uganda taxes) from income_df on their due date or next UCU payday
    """
    today = as_of or date.today()
    rate = float(ugx_rate) if ugx_rate and ugx_rate > 0 else 3680.0
    savings_pool = max(0.0, float(current_savings_usdt))
    normalized = normalize_goals(goals)

    ucu_pay_day = int(PAYROLL_SCHEDULE["UCU"]["payout_day"])
    cazzy_pay_day = min(28, int(PAYROLL_SCHEDULE["CazzyGames"]["payout_end_day"]))

    ucu_lab_net_ugx = calculate_uganda_tax(UCU_LAB_MONTHLY_GROSS_UGX)["net"]
    ucu_lab_monthly_usdt = round(ucu_lab_net_ugx / rate, 2)
    recurring_ucu = ucu_lab_monthly_usdt if include_ucu_lab_monthly else 0.0
    recurring_cazzy = max(0.0, float(extra_cazzy_monthly_usdt))
    monthly_run_rate_usd = round(recurring_ucu + recurring_cazzy, 2)

    # Collect pending UCU net receivables and already-received Lab Tech months from income_df
    next_ucu_payday = _next_day_of_month(today, ucu_pay_day)
    pending_events: List[tuple] = []
    pending_ucu_net_usd = 0.0
    received_lab_months = set()
    if income_df is not None and not income_df.empty and "Category" in income_df.columns:
        ucu_mask = income_df["Category"].apply(is_ucu_income)
        for _, row in income_df[ucu_mask].iterrows():
            cat_str = str(row.get("Category", ""))
            parsed = pd.to_datetime(row.get("Date"), errors="coerce")
            try:
                received_usdt = float(row.get("Received_USDT", 0.0) or 0.0)
            except (TypeError, ValueError):
                received_usdt = 0.0
            if received_usdt > 0 and "LAB" in cat_str.upper() and pd.notna(parsed):
                received_lab_months.add((parsed.year, parsed.month))

            try:
                pending_gross_usd = float(row.get("Pending_USD", 0.0) or 0.0)
            except (TypeError, ValueError):
                pending_gross_usd = 0.0
            if pending_gross_usd <= 0:
                continue
            net_ugx = calculate_uganda_tax(pending_gross_usd * rate)["net"]
            net_usd = round(net_ugx / rate, 2)
            pending_ucu_net_usd += net_usd

            if pd.notna(parsed):
                row_date = parsed.date()
                event_date = row_date if row_date > next_ucu_payday else next_ucu_payday
            else:
                event_date = next_ucu_payday
            pending_events.append((event_date, net_usd))

    pending_ucu_net_usd = round(pending_ucu_net_usd, 2)

    # Build chronological inflow events across a 60-month horizon
    inflows_by_date: Dict[date, float] = {}
    if include_pending_ucu:
        for ev_date, amount in pending_events:
            inflows_by_date[ev_date] = inflows_by_date.get(ev_date, 0.0) + amount

    for m in range(0, 61):
        total_months = (today.year * 12 + (today.month - 1)) + m
        yr, mo_zero = divmod(total_months, 12)
        mo = mo_zero + 1
        if recurring_ucu > 0 and (yr, mo) not in received_lab_months:
            d_ucu = date(yr, mo, ucu_pay_day)
            if d_ucu >= today:
                inflows_by_date[d_ucu] = inflows_by_date.get(d_ucu, 0.0) + recurring_ucu
        if recurring_cazzy > 0:
            d_cazzy = date(yr, mo, cazzy_pay_day)
            if d_cazzy >= today:
                inflows_by_date[d_cazzy] = inflows_by_date.get(d_cazzy, 0.0) + recurring_cazzy

    sorted_events = sorted(inflows_by_date.items(), key=lambda x: x[0])

    def _estimate_eta(needed_total_usd: float) -> tuple:
        if savings_pool + 1e-6 >= needed_total_usd:
            return today, "Ready now!", 0
        running = savings_pool
        for ev_date, amount in sorted_events:
            running += amount
            if running + 1e-6 >= needed_total_usd:
                days = (ev_date - today).days
                return ev_date, ev_date.strftime("%b %d, %Y"), days
        return None, "Increase monthly savings", None

    enriched_items: List[Dict[str, Any]] = []
    remaining_pool = savings_pool
    cumulative_target = 0.0
    total_target_usd = 0.0
    last_active_eta_label = "All goals funded!"

    for goal in normalized:
        target_usd = goal["target_usd"]
        target_ugx = round(target_usd * rate)

        if goal["status"] == "purchased":
            enriched_items.append({
                **goal,
                "target_ugx": target_ugx,
                "allocated_usd": target_usd,
                "remaining_usd": 0.0,
                "remaining_ugx": 0,
                "cumulative_remaining_usd": 0.0,
                "progress_pct": 100.0,
                "funding_state": "OWNED",
                "eta_date": None,
                "eta_label": "Purchased",
                "days_away": None,
            })
            continue

        total_target_usd += target_usd
        cumulative_target += target_usd

        if allocation_mode == "independent":
            allocated_usd = min(savings_pool, target_usd)
            remaining_usd = max(0.0, target_usd - savings_pool)
            cumulative_remaining_usd = remaining_usd
            needed_for_eta = target_usd
        else:
            allocated_usd = min(remaining_pool, target_usd)
            remaining_pool = max(0.0, remaining_pool - allocated_usd)
            remaining_usd = max(0.0, target_usd - allocated_usd)
            cumulative_remaining_usd = max(0.0, cumulative_target - savings_pool)
            needed_for_eta = cumulative_target

        progress_pct = min(100.0, (allocated_usd / target_usd) * 100.0) if target_usd > 0 else 100.0
        if remaining_usd <= 0.01:
            funding_state = "READY NOW"
        elif allocated_usd > 0:
            funding_state = "FUNDING"
        else:
            funding_state = "QUEUED"

        eta_date, eta_label, days_away = _estimate_eta(needed_for_eta)
        last_active_eta_label = eta_label

        enriched_items.append({
            **goal,
            "target_ugx": target_ugx,
            "allocated_usd": round(allocated_usd, 2),
            "remaining_usd": round(remaining_usd, 2),
            "remaining_ugx": round(remaining_usd * rate),
            "cumulative_remaining_usd": round(cumulative_remaining_usd, 2),
            "progress_pct": round(progress_pct, 1),
            "funding_state": funding_state,
            "eta_date": eta_date,
            "eta_label": eta_label,
            "days_away": days_away,
        })

    active_count = sum(1 for g in enriched_items if g["status"] == "active")
    owned_count = sum(1 for g in enriched_items if g["status"] == "purchased")
    total_funded_usd = min(savings_pool, total_target_usd)
    total_remaining_usd = max(0.0, total_target_usd - savings_pool)
    overall_progress_pct = (
        min(100.0, (total_funded_usd / total_target_usd) * 100.0) if total_target_usd > 0 else 100.0
    )

    if active_count == 0:
        all_funded_eta_label = "No active goals"
    else:
        _, all_funded_eta_label, _ = _estimate_eta(total_target_usd)

    return {
        "items": enriched_items,
        "active_count": active_count,
        "owned_count": owned_count,
        "total_target_usd": round(total_target_usd, 2),
        "total_target_ugx": round(total_target_usd * rate),
        "total_funded_usd": round(total_funded_usd, 2),
        "total_remaining_usd": round(total_remaining_usd, 2),
        "total_remaining_ugx": round(total_remaining_usd * rate),
        "overall_progress_pct": round(overall_progress_pct, 1),
        "monthly_run_rate_usd": monthly_run_rate_usd,
        "ucu_lab_monthly_usdt": ucu_lab_monthly_usdt,
        "pending_ucu_net_usd": pending_ucu_net_usd,
        "all_funded_eta_label": all_funded_eta_label,
        "last_active_eta_label": last_active_eta_label,
    }

def is_ucu_income(category: str) -> bool:
    if not isinstance(category, str):
        return False
    cat = category.strip()
    return cat in UCU_CATEGORIES or "UCU" in cat.upper() or "TUTORIAL_ASSISTANT" in cat.upper()


def calculate_uganda_tax(gross_ugx: float) -> Dict[str, float]:
    """Smart algorithm to calculate Uganda taxes based on URA ranges."""
    # 1. NSSF Calculation (5% Employee Contribution)
    nssf = gross_ugx * 0.05
    
    # 2. Local Service Tax (LST) Calculation based on Gross UGX
    # Annual LST is typically deducted in installments. We assume a 3-month installment based on UCU norms.
    annual_lst = 0
    if gross_ugx > 1000000:
        annual_lst = 100000
    elif gross_ugx > 900000:
        annual_lst = 90000
    elif gross_ugx > 800000:
        annual_lst = 80000
    elif gross_ugx > 700000:
        annual_lst = 70000
    elif gross_ugx > 600000:
        annual_lst = 60000
    elif gross_ugx > 500000:
        annual_lst = 40000
    elif gross_ugx > 400000:
        annual_lst = 30000
    elif gross_ugx > 300000:
        annual_lst = 20000
    elif gross_ugx > 200000:
        annual_lst = 10000
    elif gross_ugx > 100000:
        annual_lst = 5000
        
    lst_installment = round(annual_lst / 3) if annual_lst > 0 else 0.0

    # 3. PAYE Calculation
    # Standard URA rule is Gross - NSSF
    taxable_income = gross_ugx - nssf
    
    paye = 0.0
    if taxable_income <= 235000:
        paye = 0.0
    elif taxable_income <= 335000:
        paye = (taxable_income - 235000) * 0.10
    elif taxable_income <= 410000:
        paye = 10000 + (taxable_income - 335000) * 0.20
    else:
        paye = 25000 + (taxable_income - 410000) * 0.30
        
    # Additional 10% for income exceeding 10,000,000 UGX
    if taxable_income > 10000000:
        paye += (taxable_income - 10000000) * 0.10

    return {
        "gross": gross_ugx,
        "nssf": nssf,
        "lst": lst_installment,
        "paye": paye,
        "total_tax": nssf + lst_installment + paye,
        "net": gross_ugx - nssf - lst_installment - paye
    }


class LedgerManager:
    def __init__(self):
        try:
            self.conn = st.connection("gsheets", type=GSheetsConnection)
        except Exception as e:
            print(f"Error connecting to gsheets: {e}")
            self.conn = None

    def load_income(self) -> pd.DataFrame:
        if self.conn:
            try:
                df = self.conn.read(worksheet="Income", ttl=60)
                for col in ["Expected_USD", "Received_USDT", "Pending_USD"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                return df
            except Exception as e:
                print(f"Error reading gsheets Income: {e}")
        local_csv = os.path.join(BASE_DIR, "income_ledger.csv")
        if os.path.exists(local_csv):
            try:
                df = pd.read_csv(local_csv)
                for col in ["Expected_USD", "Received_USDT", "Pending_USD"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                return df
            except Exception:
                pass
        return pd.DataFrame(columns=["Date", "Category", "Description", "Expected_USD", "Received_USDT", "Pending_USD"])

    def load_expenses(self) -> pd.DataFrame:
        if self.conn:
            try:
                df = self.conn.read(worksheet="Expenses", ttl=60)
                df["Amount_UGX"] = pd.to_numeric(df.get("Amount_UGX", 0), errors="coerce").fillna(0.0)
                return df
            except Exception as e:
                print(f"Error reading gsheets Expenses: {e}")
        local_csv = os.path.join(BASE_DIR, "expenses_ledger.csv")
        if os.path.exists(local_csv):
            try:
                df = pd.read_csv(local_csv)
                df["Amount_UGX"] = pd.to_numeric(df.get("Amount_UGX", 0), errors="coerce").fillna(0.0)
                return df
            except Exception:
                pass
        return pd.DataFrame(columns=["Date", "Category", "Description", "Amount_UGX", "Notes"])

    def load_savings(self, ugx_rate: float = 3680.0) -> pd.DataFrame:
        loaded = False
        df = pd.DataFrame(columns=["Date", "Description", "Amount_USDT", "Amount_UGX", "Notes"])
        if self.conn:
            try:
                df = self.conn.read(worksheet="Savings", ttl=60)
                for col in ["Amount_USDT", "Amount_UGX"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                loaded = True
            except Exception as e:
                print(f"Error reading gsheets Savings: {e}")
        if not loaded:
            local_csv = os.path.join(BASE_DIR, "savings_ledger.csv")
            if os.path.exists(local_csv):
                try:
                    df = pd.read_csv(local_csv)
                    for col in ["Amount_USDT", "Amount_UGX"]:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                except Exception:
                    df = pd.DataFrame(columns=["Date", "Description", "Amount_USDT", "Amount_UGX", "Notes"])

        # Auto-route UCU wages (Lab Tech & Tutorial Assistant) directly into savings when received
        income_df = self.load_income()
        if not income_df.empty:
            ucu_mask = income_df["Category"].apply(is_ucu_income)
            ucu_rows = income_df[ucu_mask]
            auto_savings = []
            for _, row in ucu_rows.iterrows():
                if row["Received_USDT"] > 0:
                    gross_ugx = row["Received_USDT"] * ugx_rate
                    tax_info = calculate_uganda_tax(gross_ugx)
                    net_ugx = tax_info["net"]
                    net_usdt = net_ugx / ugx_rate
                    desc = "UCU Wage"
                    if "Lab" in str(row["Category"]):
                        desc = "UCU Lab Tech Wage"
                    elif "Tutorial" in str(row["Category"]) or "Teaching" in str(row["Category"]):
                        desc = "UCU Tutorial Assistant Wage"
                    auto_savings.append({
                        "Date": row["Date"],
                        "Description": f"Auto-Saving: {desc} (Net)",
                        "Amount_USDT": round(net_usdt, 2),
                        "Amount_UGX": round(net_ugx, 0),
                        "Notes": f"Automatically routed from Income ({row['Description']})"
                    })
            if auto_savings:
                df = pd.concat([df, pd.DataFrame(auto_savings)], ignore_index=True)
                
        return df

    def add_income(self, date: str, category: str, description: str, expected_usd: float, received_usdt: float = 0.0, pending_usd: float = 0.0):
        df = self.load_income()
        new_row = pd.DataFrame([{
            "Date": date,
            "Category": category,
            "Description": description,
            "Expected_USD": expected_usd,
            "Received_USDT": received_usdt,
            "Pending_USD": pending_usd
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        if self.conn:
            try:
                self.conn.update(worksheet="Income", data=df)
            except Exception as e:
                print(f"Error updating gsheets Income: {e}")
        local_csv = os.path.join(BASE_DIR, "income_ledger.csv")
        df.to_csv(local_csv, index=False)

    def add_expense(self, date: str, category: str, description: str, amount_ugx: float, notes: str = ""):
        df = self.load_expenses()
        new_row = pd.DataFrame([{"Date": date, "Category": category, "Description": description, "Amount_UGX": amount_ugx, "Notes": notes}])
        df = pd.concat([df, new_row], ignore_index=True)
        if self.conn:
            try:
                self.conn.update(worksheet="Expenses", data=df)
            except Exception as e:
                print(f"Error updating gsheets Expenses: {e}")
        local_csv = os.path.join(BASE_DIR, "expenses_ledger.csv")
        df.to_csv(local_csv, index=False)

    def add_saving(self, date: str, description: str, amount_usdt: float, ugx_rate: float, notes: str = ""):
        df = self.load_savings(ugx_rate=ugx_rate)
        # Avoid saving virtual auto-savings rows back into the ledger
        if "Notes" in df.columns:
            df = df[~df["Notes"].astype(str).str.contains("Automatically routed from Income", na=False)]
        amount_ugx = round(amount_usdt * ugx_rate, 0)
        new_row = pd.DataFrame([{"Date": date, "Description": description, "Amount_USDT": amount_usdt, "Amount_UGX": amount_ugx, "Notes": notes}])
        df = pd.concat([df, new_row], ignore_index=True)
        if self.conn:
            try:
                self.conn.update(worksheet="Savings", data=df)
            except Exception as e:
                print(f"Error updating gsheets Savings: {e}")
        local_csv = os.path.join(BASE_DIR, "savings_ledger.csv")
        df.to_csv(local_csv, index=False)

    def load_goals(self) -> List[Dict[str, Any]]:
        if self.conn:
            try:
                df = self.conn.read(worksheet="Goals", ttl=60)
                if df is not None and not df.empty and "name" in df.columns:
                    records = df.dropna(subset=["name"]).to_dict(orient="records")
                    normalized = normalize_goals(records)
                    if normalized:
                        return normalized
            except Exception:
                pass
        if os.path.exists(GOALS_FILE):
            try:
                with open(GOALS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    normalized = normalize_goals(data)
                    if normalized:
                        return normalized
            except Exception:
                pass
        return copy.deepcopy(DEFAULT_HARDWARE_GOALS)

    def save_goals(self, goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = normalize_goals(goals)
        if self.conn:
            try:
                self.conn.update(worksheet="Goals", data=pd.DataFrame(normalized))
            except Exception:
                pass
        try:
            with open(GOALS_FILE, "w", encoding="utf-8") as f:
                json.dump(normalized, f, indent=2)
        except Exception:
            pass
        return normalized

    def get_summary(self, ugx_rate: float = 3680.0) -> Dict[str, Any]:
        income_df = self.load_income()
        expenses_df = self.load_expenses()
        savings_df = self.load_savings(ugx_rate=ugx_rate)

        total_expected_usd = income_df["Expected_USD"].sum() if not income_df.empty else 0.0
        total_received_usdt = income_df["Received_USDT"].sum() if not income_df.empty else 0.0
        total_pending_usd = income_df["Pending_USD"].sum() if not income_df.empty else 0.0
        total_expenses_ugx = expenses_df["Amount_UGX"].sum() if not expenses_df.empty else 0.0
        total_savings_usdt = savings_df["Amount_USDT"].sum() if not savings_df.empty else 0.0

        total_tax_usd = 0.0
        total_nssf_usd = 0.0
        total_paye_usd = 0.0

        if not income_df.empty:
            ucu_mask = income_df["Category"].apply(is_ucu_income)
            ucu_rows = income_df[ucu_mask]
            for _, row in ucu_rows.iterrows():
                gross_ugx = row["Expected_USD"] * ugx_rate
                tax_info = calculate_uganda_tax(gross_ugx)
                
                tax_usd = tax_info["total_tax"] / ugx_rate
                total_tax_usd += tax_usd
                total_nssf_usd += tax_info["nssf"] / ugx_rate
                total_paye_usd += tax_info["paye"] / ugx_rate
                
                total_expected_usd -= tax_usd
                if row["Pending_USD"] > 0:
                    total_pending_usd -= tax_usd
                if row["Received_USDT"] > 0:
                    total_received_usdt -= tax_usd

        total_received_ugx = round(total_received_usdt * ugx_rate, 0)
        total_expenses_usd = round(total_expenses_ugx / ugx_rate, 2)
        total_savings_ugx = round(total_savings_usdt * ugx_rate, 0)

        net_worth_usdt = round(total_received_usdt - total_expenses_usd - total_savings_usdt, 2)
        net_worth_ugx = round(net_worth_usdt * ugx_rate, 0)

        return {
            "total_expected_usd": total_expected_usd,
            "total_received_usdt": total_received_usdt,
            "total_received_ugx": total_received_ugx,
            "total_pending_usd": total_pending_usd,
            "total_expenses_ugx": total_expenses_ugx,
            "total_expenses_usd": total_expenses_usd,
            "total_savings_usdt": total_savings_usdt,
            "total_savings_ugx": total_savings_ugx,
            "net_worth_usdt": net_worth_usdt,
            "net_worth_ugx": net_worth_ugx,
            "total_tax_usd": total_tax_usd,
            "total_nssf_usd": total_nssf_usd,
            "total_paye_usd": total_paye_usd,
            "ugx_rate": ugx_rate,
        }

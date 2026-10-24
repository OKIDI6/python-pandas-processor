import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import os
import requests
from typing import Dict, Any

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

import pandas as pd
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
    # Note: UCU taxable income might sometimes differ, but standard URA rule is Gross - NSSF
    # We will compute PAYE smartly based on the exact URA monthly brackets.
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

    # 4. For the edge case where arrears combine months (like Sep 2026 UCU Payslip), 
    # we leave standard calculations active. If total_tax calculation drifts from accounting norms, 
    # the exact payslip PAYE overrides can be fed through a separate arrears calculator, 
    # but this covers 99% of normal monthly executions automatically.

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
        self.income_path = os.path.join(BASE_DIR, "income_ledger.csv")
        self.expenses_path = os.path.join(BASE_DIR, "expenses_ledger.csv")
        self.savings_path = os.path.join(BASE_DIR, "savings_ledger.csv")

    def load_income(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.income_path)
            for col in ["Expected_USD", "Received_USDT", "Pending_USD"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["Date", "Category", "Description", "Expected_USD", "Received_USDT", "Pending_USD"])

    def load_expenses(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.expenses_path)
            df["Amount_UGX"] = pd.to_numeric(df.get("Amount_UGX", 0), errors="coerce").fillna(0.0)
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["Date", "Category", "Description", "Amount_UGX", "Notes"])

    def load_savings(self, ugx_rate: float = 3680.0) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.savings_path)
            for col in ["Amount_USDT", "Amount_UGX"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        except FileNotFoundError:
            df = pd.DataFrame(columns=["Date", "Description", "Amount_USDT", "Amount_UGX", "Notes"])

        # Auto-route UCU Lab Tech Role income directly into savings when received
        income_df = self.load_income()
        if not income_df.empty:
            ucu_rows = income_df[income_df["Category"] == "Electronics_Lab_Technician_Graduate_Intern"]
            auto_savings = []
            for _, row in ucu_rows.iterrows():
                if row["Received_USDT"] > 0:
                    # Calculate true net received
                    gross_ugx = row["Received_USDT"] * ugx_rate
                    tax_info = calculate_uganda_tax(gross_ugx)
                    net_ugx = tax_info["net"]
                    net_usdt = net_ugx / ugx_rate
                    
                    auto_savings.append({
                        "Date": row["Date"],
                        "Description": "Auto-Saving: UCU Lab Tech Wage (Net)",
                        "Amount_USDT": round(net_usdt, 2),
                        "Amount_UGX": round(net_ugx, 0),
                        "Notes": "Automatically routed from Income"
                    })
            if auto_savings:
                df = pd.concat([df, pd.DataFrame(auto_savings)], ignore_index=True)
                
        return df

    def add_expense(self, date: str, category: str, description: str, amount_ugx: float, notes: str = ""):
        df = self.load_expenses()
        new_row = pd.DataFrame([{"Date": date, "Category": category, "Description": description, "Amount_UGX": amount_ugx, "Notes": notes}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.expenses_path, index=False)

    def add_saving(self, date: str, description: str, amount_usdt: float, ugx_rate: float, notes: str = ""):
        df = self.load_savings()
        amount_ugx = round(amount_usdt * ugx_rate, 0)
        new_row = pd.DataFrame([{"Date": date, "Description": description, "Amount_USDT": amount_usdt, "Amount_UGX": amount_ugx, "Notes": notes}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.savings_path, index=False)

    def get_summary(self, ugx_rate: float = 3680.0) -> Dict[str, Any]:
        income_df = self.load_income()
        expenses_df = self.load_expenses()
        savings_df = self.load_savings(ugx_rate=ugx_rate)

        total_expected_usd = income_df["Expected_USD"].sum() if not income_df.empty else 0.0
        total_received_usdt = income_df["Received_USDT"].sum() if not income_df.empty else 0.0
        total_pending_usd = income_df["Pending_USD"].sum() if not income_df.empty else 0.0
        total_expenses_ugx = expenses_df["Amount_UGX"].sum() if not expenses_df.empty else 0.0
        total_savings_usdt = savings_df["Amount_USDT"].sum() if not savings_df.empty else 0.0

        # Automatic Tax Tracking for UCU Role
        total_tax_usd = 0.0
        total_nssf_usd = 0.0
        total_paye_usd = 0.0

        if not income_df.empty:
            ucu_rows = income_df[income_df["Category"] == "Electronics_Lab_Technician_Graduate_Intern"]
            for _, row in ucu_rows.iterrows():
                # Convert expected USD back to UGX gross to calculate exact local taxes
                gross_ugx = row["Expected_USD"] * ugx_rate
                tax_info = calculate_uganda_tax(gross_ugx)
                
                tax_usd = tax_info["total_tax"] / ugx_rate
                total_tax_usd += tax_usd
                total_nssf_usd += tax_info["nssf"] / ugx_rate
                total_paye_usd += tax_info["paye"] / ugx_rate
                
                # Reduce Expected and Pending/Received by the withheld tax amount
                total_expected_usd -= tax_usd
                if row["Pending_USD"] > 0:
                    total_pending_usd -= tax_usd
                if row["Received_USDT"] > 0:
                    total_received_usdt -= tax_usd

        # Currency conversions
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

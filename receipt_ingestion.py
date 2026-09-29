import json
import re
import pandas as pd
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIPTS_FILE = os.path.join(BASE_DIR, "raw_receipts_log.jsonl")

def parse_momo_receipt(raw_text: str):
    """
    Parses a single MTN MoMo SMS receipt into a structured dictionary.
    Returns None if the message is not a valid/completed transaction.
    """
    raw_text = raw_text.strip()
    
    # 1. Payment to an individual or merchant (Format A: You have paid UGX XXXX to YYY on YYYY-MM-DD...)
    match_paid_a = re.search(r"You have paid UGX\s+([\d,]+)\s+to\s+(.*?)\s+on\s+(\d{4}-\d{2}-\d{2})", raw_text, re.IGNORECASE)
    if match_paid_a:
        amount = float(match_paid_a.group(1).replace(",", ""))
        recipient = match_paid_a.group(2).strip()
        date_str = match_paid_a.group(3)
        return {"type": "expense", "amount_ugx": amount, "recipient": recipient, "date": date_str, "raw": raw_text}

    # 2. Payment to merchant (Format B: You have paid YYY XXXX UGX XXXX. Fee:...)
    match_paid_b = re.search(r"You have paid\s+(.*?)\s+(?:\d+\s+)?UGX\s+([\d,]+)\.\s+Fee:", raw_text, re.IGNORECASE)
    if match_paid_b:
        recipient = match_paid_b.group(1).strip()
        amount = float(match_paid_b.group(2).replace(",", ""))
        # For this format, date isn't always explicit in the short message, 
        # but usually there's another SMS. We will extract date from timestamp if needed, 
        # but let's just return what we have.
        return {"type": "expense", "amount_ugx": amount, "recipient": recipient, "date": None, "raw": raw_text}

    # 3. Withdrawal
    match_withdraw = re.search(r"You have withdrawn UGX\s*(?:UGX\s*)?([\d,]+)\s+from\s+(.*?)\s+on\s+(\d{4}-\d{2}-\d{2})", raw_text, re.IGNORECASE)
    if match_withdraw:
        amount = float(match_withdraw.group(1).replace(",", ""))
        agent = match_withdraw.group(2).strip()
        date_str = match_withdraw.group(3)
        return {"type": "expense", "amount_ugx": amount, "recipient": f"Cash Withdrawal: {agent}", "date": date_str, "raw": raw_text}

    # 4. Received money
    match_received = re.search(r"You have received UGX\s+([\d,]+)\s+from\s+(.*?)\s+on\s+(\d{4}-\d{2}-\d{2})", raw_text, re.IGNORECASE)
    if match_received:
        amount = float(match_received.group(1).replace(",", ""))
        sender = match_received.group(2).strip()
        date_str = match_received.group(3)
        return {"type": "income", "amount_ugx": amount, "sender": sender, "date": date_str, "raw": raw_text}

    return None

def categorize_expense(recipient: str) -> str:
    """Basic keyword matching for categorization."""
    recipient_lower = recipient.lower()
    if any(word in recipient_lower for word in ["supermarket", "mart", "store", "food", "cafe", "restaurant", "bistro"]):
        return "Food"
    if any(word in recipient_lower for word in ["uber", "safeboda", "fuel", "taxi", "transport", "boda"]):
        return "Transport"
    if any(word in recipient_lower for word in ["airtel", "mtn", "data", "airtime"]):
        return "Airtime/Data"
    if any(word in recipient_lower for word in ["church", "watoto", "tithe", "offering", "donation"]):
        return "Other"
    if "withdrawal" in recipient_lower:
        return "Other" # Cash could be anything
    return "Other"

def process_raw_receipts():
    """
    Reads raw_receipts_log.jsonl, parses the receipts, and returns a list of processed expenses.
    """
    if not os.path.exists(RECEIPTS_FILE):
        return []

    processed_expenses = []
    unprocessed_lines = []

    with open(RECEIPTS_FILE, "r") as f:
        lines = f.readlines()

    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            raw_text = data.get("raw_text", "")
            timestamp = data.get("timestamp", "")
            
            parsed = parse_momo_receipt(raw_text)
            
            if parsed and parsed["type"] == "expense":
                # Fallback to timestamp date if regex didn't catch it
                date_str = parsed["date"]
                if not date_str:
                    try:
                        date_str = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
                    except Exception:
                        date_str = datetime.now().strftime("%Y-%m-%d")
                
                category = categorize_expense(parsed["recipient"])
                description = f"MoMo: {parsed['recipient']}"
                
                processed_expenses.append({
                    "Date": date_str,
                    "Category": category,
                    "Description": description,
                    "Amount_UGX": parsed["amount_ugx"],
                    "Notes": "Auto-ingested from MoMo SMS"
                })
            elif parsed and parsed["type"] == "income":
                # Handle income if needed, for now we will just keep it or log it
                pass
            else:
                # Could not parse or it's a request/info message, ignore or keep
                pass
                
        except json.JSONDecodeError:
            pass

    # Empty the file to prevent duplicate processing
    with open(RECEIPTS_FILE, "w") as f:
        pass

    return processed_expenses

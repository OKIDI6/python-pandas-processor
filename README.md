# Okidi Finance OS

Personal finance dashboard and AI-powered financial advisor for Okidi Norbert.

## Features

- Multi-role income tracking (CazzyGames Team Lead IT + UCU Lab Technician)
- Dynamic Uganda tax calculation (NSSF, LST, PAYE)
- Live USD/UGX exchange rate via API
- Expense tracking with Mobile Money SMS parser
- Crypto-to-fiat conversion logging
- Smart Financial Advisor with:
  - Spending velocity analysis (daily/weekly/monthly burn rate)
  - Cash runway prediction
  - Spending anomaly detection (z-score)
  - Fee leakage tracking
  - Adaptive budgeting (learns from your behavior)
  - Prioritized recommendations (P0-P3)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Authentication

This app uses Google OIDC for authentication. Configure `.streamlit/secrets.toml`:

```toml
[auth]
redirect_uri = "https://YOUR_TUNNEL_URL/oauth2callback"
cookie_secret = "GENERATE_A_RANDOM_SECRET"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

## Run

```bash
streamlit run dashboard.py --server.port 8501
```

## Data Files

| File | Purpose |
|---|---|
| income_ledger.csv | Income records |
| expenses_ledger.csv | Expense records |
| savings_ledger.csv | Savings records |
| crypto_conversions.csv | USDT to UGX conversion log |
| raw_receipts_log.jsonl | Raw MoMo SMS data (AI training) |
| advisor_state.json | Advisor learning memory |

## Security

- Google OIDC login required (email whitelisted)
- Secrets stored in .streamlit/secrets.toml (gitignored)
- Exposed via Cloudflare Tunnel (encrypted end-to-end)

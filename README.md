# ☕ Coffee Price Tracker - GiaNongSan

Automated coffee bean price scraping from international and Vietnamese domestic markets with Telegram notifications.

## 🎯 Features

- **International Prices**: Arabica (NYC) & Robusta (London) via **Chocaphe.vn**.
- **Market Financials**: Gold Futures & USD/VND Exchange Rate via **Yahoo Finance**.
- **Domestic Prices**: Real-time prices from **Chocaphe.vn** (Dak Lak, Lam Dong, Gia Lai, Dak Nong).
- **Telegram Notifications**: Daily reports with price changes and trends.
- **GitHub Actions**: Automated scheduling (9AM & 3PM Vietnam time).
- **Reliability**: Parallel scraping, retry logic, and fallback strategies.

## 📊 Data Sources

| Market | Source | Update Freq | Status |
|--------|--------|-------------|--------|
| **International** | Chocaphe.vn (Intl) | Real-time (Price only) | ✅ Active |
| **Financials** | Yahoo Finance (VND=X, GC=F) | ~10 mins delayed | ✅ Active |
| **Domestic** | Chocaphe.vn (Domestic) | Real-time | ✅ Active |

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Telegram Bot Token & Chat ID
- GitHub account (for automation)

### 2. Local Setup

```bash
# Clone
git clone https://github.com/maxsaigon/coffee-price.git
cd coffee-price

# Install dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

### 3. Usage

**Run as a python module:**

```bash
# 1. Test data fetching (prints to console, no telegram)
python -m src.main test

# 2. Run manual update (sends telegram)
python -m src.main update
```

## 🤖 GitHub Actions Automation

The project includes a pre-configured workflow `.github/workflows/coffee_tracker.yml` that runs automatically.

### Setup Steps:

1. Go to your GitHub Repository -> **Settings** -> **Secrets and variables** -> **Actions**.
2. Add the following **Repository secrets**:
   - `TELEGRAM_BOT_TOKEN`: Your bot token.
   - `TELEGRAM_CHAT_ID`: Your target chat ID.

### Schedule:
- **Morning Update**: 09:00 AM (Vietnam Time)
- **Afternoon Update**: 15:00 PM (Vietnam Time)

## 📁 Project Structure

```text
gianongsan/
├── src/
│   ├── main.py                # Entry point
│   ├── config.py              # Configuration
│   ├── providers/             # Data Fetchers
│   │   ├── chocaphe_scraper.py# Chocaphe.vn (Intl & Domestic)
│   │   └── financial_provider.py # Yahoo Finance (Gold/USD)
│   └── services/              # Notification Services
├── .github/workflows/         # Automation workflows
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## 🛡️ License

MIT License.

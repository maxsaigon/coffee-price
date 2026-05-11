# ☕ Coffee Price Tracker - GiaNongSan

Automated coffee bean price scraping from international and Vietnamese domestic markets with Telegram notifications.

## 🎯 Features

- **International Prices**: Arabica (NYC) & Robusta (London) via **Chocaphe.vn**.
- **Market Financials**: Vietnamese gold prices via **vang.today**, XAU/USD cross-check via **gold-api.com**, and USD/VND via **ExchangeRate-API**.
- **Domestic Prices**: Real-time prices from **Chocaphe.vn** (Dak Lak, Lam Dong, Gia Lai, Dak Nong).
- **Telegram Notifications**: Daily reports with price changes and trends.
- **GitHub Actions**: Automated scheduling (8AM & 3PM Vietnam time).
- **Reliability**: Parallel scraping, retry logic, and fallback strategies.

## 📊 Data Sources

| Market | Source | Update Freq | Status |
|--------|--------|-------------|--------|
| **International** | Chocaphe.vn (Intl) | Real-time (Price only) | ✅ Active |
| **Financials** | vang.today + gold-api.com + ExchangeRate-API | ~5-30 mins delayed | ✅ Active |
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
- **Morning Update**: 08:00 AM Vietnam time (`01:00 UTC`)
- **Afternoon Update**: 15:00 Vietnam time (`08:00 UTC`)

GitHub Actions cron uses UTC and may start a scheduled workflow a few minutes late during busy periods. The app formats report timestamps with `Asia/Ho_Chi_Minh` so Telegram messages show GMT+7 time.

## 📁 Project Structure

```text
gianongsan/
├── src/
│   ├── main.py                # Entry point
│   ├── config.py              # Configuration
│   ├── providers/             # Data Fetchers
│   │   ├── chocaphe_scraper.py# Chocaphe.vn (Intl & Domestic)
│   │   └── financial_provider.py # Gold/USD/VND providers
│   └── services/              # Notification Services
├── .github/workflows/         # Automation workflows
├── requirements.txt           # Dependencies
└── README.md                  # Documentation
```

## 🛡️ License

MIT License.

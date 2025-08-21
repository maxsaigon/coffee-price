# ☕ Coffee Price Tracker - GiaNongSan

Automated coffee bean price scraping from international markets with Telegram notifications. Designed for Vietnamese coffee market analysis.

## 🎯 Features

- **Automated Price Scraping**: Robusta (London) & Arabica (NYC) futures from Investing.com
- **Telegram Notifications**: Daily price reports in Vietnamese 
- **GitHub Actions Scheduling**: Runs automatically at 8AM & 5PM Vietnam time
- **Multiple Fallback Strategies**: Handles anti-bot protection
- **Currency Conversion**: USD to VND conversion for local market
- **Error Handling**: Robust error detection and notification system

## 📊 Market Data Sources

| Coffee Type | Exchange | Symbol | Unit | Update Frequency |
|------------|----------|--------|------|------------------|
| Robusta | London Commodity Exchange | LCF | USD/tonne | Real-time |
| Arabica | Intercontinental Exchange (ICE) | KC | cents/lb | Real-time |

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Telegram Bot Token
- GitHub repository (for automation)

### 2. Setup Telegram Bot

1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token (format: `123456:ABC-DEF...`)
3. Add bot to your channel/group
4. Get chat ID (use [@userinfobot](https://t.me/userinfobot))

### 3. Local Development

```bash
# Clone and setup

pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your tokens

# Test system
python main.py test

# Send test notification
python main.py notify-test

# Run price update
python main.py update
```

### 4. GitHub Actions Deployment

1. **Add Repository Secrets:**
   - `TELEGRAM_BOT_TOKEN`: Your bot token
   - `TELEGRAM_CHAT_ID`: Target chat ID

2. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Setup coffee price tracker"
   git push origin main
   ```

3. **Automatic Scheduling:**
   - 8:00 AM Vietnam time (1:00 AM UTC)
   - 5:00 PM Vietnam time (10:00 AM UTC)

## 📁 Project Structure

```
gianongsan/
├── main.py                           # Entry point
├── investing_coffee_scraper.py       # Core scraper
├── telegram_bot.py                   # Telegram integration
├── config.py                         # Configuration management
├── requirements.txt                  # Dependencies
├── test_scraper.py                   # Testing utilities
├── .github/workflows/
│   └── coffee_tracker.yml           # GitHub Actions workflow
├── README.md                         # This file
└── .env.example                      # Environment template
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - | ✅ |
| `TELEGRAM_CHAT_ID` | Target chat/channel ID | - | ✅ |
| `SCRAPER_TIMEOUT` | Request timeout (seconds) | 15 | ❌ |
| `SCRAPER_MAX_RETRIES` | Max retry attempts | 3 | ❌ |
| `USD_TO_VND_RATE` | Exchange rate for conversion | 24000 | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |

### Sample .env File

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890

# Scraper Settings
SCRAPER_TIMEOUT=20
SCRAPER_MAX_RETRIES=3
USD_TO_VND_RATE=24500

# Logging
LOG_LEVEL=INFO
```

## 🤖 Usage Commands

```bash
# Show configuration
python main.py config

# Run system test
python main.py test

# Send test notification  
python main.py notify-test

# Run price update (main function)
python main.py update

# Show help
python main.py help
```

## 📱 Telegram Message Format

```
☕ BÁO GIÁ CÀ PHÊ QUỐC TẾ
📅 21/08/2025 15:30 (GMT+7)

🌱 ROBUSTA (London)
💰 Giá: $4,247.00/tấn
💸 VND: 101,928,000/tấn
📈 Thay đổi: +12.00 (+0.28%)

☕ ARABICA (New York)  
💰 Giá: 245.50 cents/lb
💰 USD: $5,411.23/tấn
💸 VND: 129,869,520/tấn
📈 Thay đổi: -3.25 (-1.31%)

✅ Tất cả dữ liệu cập nhật thành công

🔗 Nguồn: Investing.com
🤖 Tự động cập nhật bởi GiaNongSan Bot
```

## 🛡️ Error Handling

### Fallback Strategies

1. **Primary**: Standard requests with headers
2. **Cloudflare Bypass**: Uses cloudscraper
3. **JavaScript Rendering**: Selenium WebDriver (last resort)

### Error Notifications

- Automatic error alerts to Telegram
- Detailed logging for debugging
- GitHub Actions failure notifications

## 📈 Monitoring & Logs

### GitHub Actions

- ✅ Successful runs logged in Actions tab
- ❌ Failed runs upload logs as artifacts
- 📊 Daily health check reports

### Local Logs

```bash
# View recent logs
tail -f coffee_tracker.log

# Check specific errors
grep ERROR coffee_tracker.log
```

## 🔧 Troubleshooting

### Common Issues

**Bot not sending messages:**
```bash
# Check bot token and chat ID
python main.py config

# Test connection
python main.py test
```

**Scraping failures:**
```bash
# Check if sites are accessible
curl -I https://www.investing.com/commodities/london-coffee

# Test with fallback methods
python test_scraper.py
```

**GitHub Actions not running:**
- Check repository secrets are set
- Verify workflow file is in `.github/workflows/`
- Check Actions tab for error messages

### Anti-Bot Protection

If scraping is blocked:

1. **Enable Cloudscraper** (automatic fallback)
2. **Use rotating proxies** (manual setup required)
3. **Switch to Selenium** (slower but more reliable)

## 🌟 Advanced Features

### Custom Scheduling

Modify `.github/workflows/coffee_tracker.yml`:

```yaml
schedule:
  - cron: '0 1 * * *'    # 8AM Vietnam
  - cron: '0 6 * * *'    # 1PM Vietnam  
  - cron: '0 10 * * *'   # 5PM Vietnam
```

### Additional Markets

Extend `config.py` to add more coffee sources:

```python
'vietnam_domestic': {
    'url': 'https://example-vietnam-coffee-site.com',
    'name': 'Vietnam Domestic Coffee',
    'unit': 'VND/kg',
    'symbol': 'VN-CF'
}
```

### Price Alerts

Add threshold monitoring in `telegram_bot.py`:

```python
def check_price_alerts(self, price_data):
    # Alert if price changes > 5%
    # Alert if price reaches certain thresholds
    pass
```

## 📄 License

MIT License - Feel free to use for commercial or personal projects.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-market`)
3. Commit changes (`git commit -am 'Add new market source'`)
4. Push to branch (`git push origin feature/new-market`)
5. Create Pull Request

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **Email**: your-email@example.com

---

**Made with ☕ for the Vietnamese coffee community**# coffee-price

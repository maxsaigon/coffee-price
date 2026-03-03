# 🚀 Coffee Price Tracker - Setup Guide

Complete guide to deploy the automated coffee price scraper with GitHub Actions.

## 📋 Prerequisites

- GitHub account
- Telegram account
- Basic knowledge of GitHub Actions and environment variables

## 🤖 Step 1: Create Telegram Bot

### 1.1 Create Bot via BotFather

1. Open Telegram and search for `@BotFather`
2. Start conversation and send `/newbot`
3. Choose a name: ` `
4. Choose a username: `your_coffee_bot` (must end with 'bot')
5. Save the **Bot Token** (format: `123456:ABC-DEF...`)

### 1.2 Get Chat ID

**Option A: For Personal Chat**
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response

**Option B: For Group/Channel**
1. Add bot to your group/channel
2. Make bot an admin (for channels)
3. Send a message in the group
4. Use the same URL to get chat ID (will be negative for groups)

**Option C: Use @userinfobot**
1. Forward a message from your target chat to `@userinfobot`
2. It will show the chat ID

## 📂 Step 2: Fork and Setup Repository

### 2.1 Fork Repository
```bash
# Fork this repository to your GitHub account
# Then clone it locally
git clone https://github.com/YOUR_USERNAME/coffee-price-tracker.git
cd coffee-price-tracker/gianongsan
```

### 2.2 Test Locally (Optional)
```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your tokens
nano .env
```

Add your tokens to `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=-1001234567890
```

Test the system:
```bash
# Test configuration
python main.py config

# Test scraper (may fail due to anti-bot protection)
python main.py test

# Test Telegram bot (requires valid tokens)
python main.py notify-test
```

## ⚙️ Step 3: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TELEGRAM_CHAT_ID` | Your chat/channel ID | `-1001234567890` |

## 📅 Step 4: Enable GitHub Actions

### 4.1 Enable Actions
1. Go to **Actions** tab in your repository
2. Click **I understand my workflows, go ahead and enable them**

### 4.2 Verify Workflow File
Check that `.github/workflows/coffee_tracker.yml` exists with correct content:

```yaml
name: Coffee Price Tracker

on:
  schedule:
    - cron: '0 1 * * *'   # 8AM Vietnam (1AM UTC)
    - cron: '0 8 * * *'  # 3PM Vietnam (8AM UTC)
  workflow_dispatch:
```

### 4.3 Manual Test Run
1. Go to **Actions** tab
2. Click **Coffee Price Tracker** workflow
3. Click **Run workflow** button
4. Select `test` command and run

## 🔧 Step 5: Troubleshooting

### 5.1 Common Issues

**❌ "Bot token is invalid"**
- Check TELEGRAM_BOT_TOKEN secret is correct
- Ensure no extra spaces in token

**❌ "Chat not found"**
- Verify TELEGRAM_CHAT_ID is correct
- For groups, ensure bot is added and has admin rights
- Chat ID should be negative for groups

**❌ "Scraping failed"**
- This is expected due to anti-bot protection
- The system will use fallback methods
- Consider adding proxy rotation for production

**❌ "GitHub Actions not running"**
- Check repository secrets are set
- Verify workflow file syntax
- Check Actions tab for error messages

### 5.2 Anti-Bot Protection Solutions

If scraping consistently fails:

1. **Enable Selenium fallback** (automatic in code)
2. **Use proxy rotation** (requires manual setup)
3. **Switch to alternative data sources**

### 5.3 Logs and Monitoring

- **GitHub Actions**: Check Actions tab for run logs
- **Failed runs**: Download artifacts for detailed logs
- **Telegram**: Bot will send error notifications

## 📊 Step 6: Verify Setup

### 6.1 Manual Test
```bash
# Trigger manual run
# Go to Actions → Coffee Price Tracker → Run workflow
```

### 6.2 Expected Output
Bot should send message like:
```
☕ BÁO GIÁ CÀ PHÊ QUỐC TẾ
📅 21/08/2025 15:30 (GMT+7)

🌱 ROBUSTA (London)
💰 Giá: $4,247.00/tấn
💸 VND: 101,928,000/tấn
📈 Thay đổi: +12.00 (+0.28%)

✅ Tất cả dữ liệu cập nhật thành công
```

### 6.3 Schedule Verification
- 8:00 AM Vietnam time (1:00 AM UTC)
- 3:00 PM Vietnam time (8:00 AM UTC)

## 🛠️ Step 7: Customization

### 7.1 Change Schedule
Edit `.github/workflows/coffee_tracker.yml`:
```yaml
schedule:
  - cron: '0 0 * * *'    # 7AM Vietnam
  - cron: '0 2 * * *'    # 9AM Vietnam
  - cron: '0 9 * * *'    # 4PM Vietnam
```

### 7.2 Add More Coffee Types
Edit `config.py` to add new sources:
```python
'vietnam_domestic': {
    'url': 'https://vietnam-coffee-site.com',
    'name': 'Vietnam Coffee',
    'unit': 'VND/kg'
}
```

### 7.3 Change Currency Rate
Add to repository secrets:
```
USD_TO_VND_RATE=25000
```

## 📱 Step 8: Advanced Features

### 8.1 Multiple Channels
Create separate workflows for different audiences:
- General public channel
- Trader-focused group
- Internal team notifications

### 8.2 Price Alerts
Modify `telegram_bot.py` to add threshold alerts:
```python
if price_change > 5:  # 5% change
    send_alert_message()
```

### 8.3 Historical Data
The system automatically stores price history in SQLite database for future analysis.

## 🔐 Security Notes

- Never commit tokens to repository
- Use GitHub secrets for all sensitive data
- Regularly rotate bot tokens
- Monitor for unauthorized access

## 📞 Support

If you encounter issues:

1. **Check GitHub Actions logs** for detailed error messages
2. **Test locally** with your environment file
3. **Verify Telegram setup** with manual message tests
4. **Review scraper logs** for anti-bot protection issues

## ✅ Final Checklist

- [ ] Telegram bot created and token saved
- [ ] Chat ID obtained (negative for groups)
- [ ] Repository forked and cloned
- [ ] GitHub secrets configured
- [ ] GitHub Actions enabled
- [ ] Manual test run successful
- [ ] Bot sends messages to correct chat
- [ ] Schedule verified (8AM & 3PM Vietnam time)
- [ ] Error handling working (bot notifies on failures)

## 🎉 Success!

Your coffee price tracker is now fully automated and will:
- ✅ Run twice daily automatically
- ✅ Send price updates to Telegram
- ✅ Handle errors gracefully
- ✅ Store historical data
- ✅ Work without server costs

**Made with ☕ for the Vietnamese coffee community**
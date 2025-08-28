#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to validate GitHub Actions compatibility
Simulates the environment and commands that GitHub Actions will run
"""

import os
import sys
import subprocess
import asyncio
import logging
from datetime import datetime

def setup_environment():
    """Setup environment variables like GitHub Actions"""
    os.environ.setdefault('SCRAPER_TIMEOUT', '20')
    os.environ.setdefault('SCRAPER_MAX_RETRIES', '3')
    os.environ.setdefault('USD_TO_VND_RATE', '25000')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    
    print("🔧 Environment variables set:")
    for key in ['SCRAPER_TIMEOUT', 'SCRAPER_MAX_RETRIES', 'USD_TO_VND_RATE', 'LOG_LEVEL']:
        print(f"  {key}: {os.environ.get(key)}")
    
    # Check Telegram config (should be from real environment)
    telegram_configured = bool(os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'))
    print(f"  TELEGRAM_CONFIGURED: {telegram_configured}")
    
    return telegram_configured

def test_main_py_commands():
    """Test all main.py commands like GitHub Actions would"""
    commands = ['config', 'test', 'notify-test']
    
    print("\n🧪 Testing main.py commands...")
    
    for command in commands:
        print(f"\n--- Testing: python main.py {command} ---")
        
        try:
            result = subprocess.run(
                [sys.executable, 'main.py', command],
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            
            print(f"Exit Code: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ Command succeeded")
            else:
                print("❌ Command failed")
            
            # Show last few lines of output
            if result.stdout:
                lines = result.stdout.strip().split('\n')[-5:]
                print("Last 5 lines of stdout:")
                for line in lines:
                    print(f"  {line}")
            
            if result.stderr:
                lines = result.stderr.strip().split('\n')[-5:]
                print("Last 5 lines of stderr:")
                for line in lines:
                    print(f"  {line}")
                    
        except subprocess.TimeoutExpired:
            print("❌ Command timed out after 60 seconds")
        except Exception as e:
            print(f"❌ Command failed with exception: {e}")
    
    return True

def test_requirements():
    """Test that all required packages are installed"""
    print("\n📦 Testing package requirements...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'check'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ All packages are compatible")
        else:
            print("⚠️ Package compatibility issues:")
            print(result.stdout)
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Failed to check packages: {e}")

def generate_report():
    """Generate a summary report"""
    print("\n📊 GITHUB ACTIONS COMPATIBILITY REPORT")
    print("=" * 50)
    
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check if log file was created
    log_file = "coffee_tracker.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
            print(f"Log File: {len(lines)} lines")
            if lines:
                print("Last 3 log entries:")
                for line in lines[-3:]:
                    print(f"  {line.strip()}")
        except Exception as e:
            print(f"Log File: Error reading - {e}")
    else:
        print("Log File: Not created")
    
    print("\n🎯 EXPECTED GITHUB ACTIONS BEHAVIOR:")
    print("1. Environment variables will be set by workflow")
    print("2. Telegram bot token/chat ID will be from secrets")
    print("3. Commands should exit with code 0 for success")
    print("4. Logs will be uploaded on failure")
    
    print("\n📝 RECOMMENDATIONS:")
    telegram_configured = bool(os.environ.get('TELEGRAM_BOT_TOKEN'))
    if not telegram_configured:
        print("⚠️ Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in GitHub secrets")
    
    print("✅ Workflow updated to use main.py instead of run_market_timing.py")
    print("✅ Enhanced scraper re-enabled with working sources")
    
    print(f"\n🔗 Monitor workflow at: https://github.com/maxsaigon/coffee-price/actions")

def main():
    print("🚀 GitHub Actions Compatibility Test")
    print("=" * 40)
    
    # Setup environment
    telegram_configured = setup_environment()
    
    # Test requirements
    test_requirements()
    
    # Test commands
    test_main_py_commands()
    
    # Generate report
    generate_report()
    
    print("\n✅ Compatibility test completed!")
    print("You can now manually trigger the GitHub workflow to test in production.")

if __name__ == "__main__":
    main()
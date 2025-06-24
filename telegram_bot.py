#!/usr/bin/env python3
"""
Quick launcher for Telegram Meme Coin Bot
Handles setup and environment checking
"""

import os
import sys
import subprocess
import time
import logging
logging.basicConfig(level=logging.INFO)
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# something like this
updater = Updater(token=TOKEN, use_context=True)

from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required_packages = [
        'telegram',
        'requests',
        'flask'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_bot_token():
    """Check if Telegram bot token is set"""
    token = os.getenv('7655098236:AAE1UZCEomdUkRZpycUKRSGZ6-YONBBleFg')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        print("\n🔧 To set your bot token:")
        print("   1. Create a bot with @BotFather on Telegram")
        print("   2. Copy the bot token")
        print("   3. Set environment variable:")
        print("      export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("\n   Or create a .env file with:")
        print("      TELEGRAM_BOT_TOKEN=your_token_here")
        return False
    
    # Basic token format check
    if not token.count(':') == 1 or len(token) < 35:
        print("⚠️  Bot token format looks incorrect")
        print("   Token should be in format: 1234567890:ABC-DEF1234567890")
        return False
    
    return True

def check_bot_files():
    """Check if required bot files exist"""
    required_files = ['bot.py', 'telegram_bot.py']
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def test_api_connectivity():
    """Test DexScreener API connectivity"""
    try:
        import requests
        response = requests.get('https://api.dexscreener.com/latest/dex/search?q=test', timeout=5)
        if response.status_code == 200:
            print("✅ API connectivity test passed")
            return True
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return True  # Still allow to continue
    except Exception as e:
        print(f"⚠️  API test failed: {e}")
        print("   Bot will still work, but might have limited functionality")
        return True  # Allow to continue

def create_env_file():
    """Create a sample .env file"""
    env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional Settings
DEFAULT_MAX_RESULTS=7
DEFAULT_MIN_SCORE=0.0
QUICK_SCAN_RESULTS=3
QUICK_SCAN_MIN_SCORE=5.0

# Cache Settings
RESULTS_CACHE_MINUTES=10
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_content)
    
    print("📝 Created .env.example file")
    print("   Copy it to .env and add your bot token")

def main():
    """Main launcher function"""
    print("🚀 Telegram Meme Coin Bot Launcher")
    print("=" * 50)
    
    # Check requirements
    print("🔍 Checking requirements...")
    if not check_requirements():
        print("\n❌ Please install missing packages first")
        return False
    
    print("✅ All packages installed")
    
    # Check bot files
    print("\n🔍 Checking bot files...")
    if not check_bot_files():
        print("\n❌ Missing required bot files")
        return False
    
    print("✅ Bot files found")
    
    # Check bot token
    print("\n🔍 Checking bot token...")
    if not check_bot_token():
        print("\n💡 Creating example .env file...")
        create_env_file()
        return False
    
    print("✅ Bot token configured")
    
    # Test API
    print("\n🔍 Testing API connectivity...")
    test_api_connectivity()
    
    # All checks passed
    print("\n" + "=" * 50)
    print("✅ All checks passed! Starting bot...")
    print("📱 Your bot is now ready for users!")
    print("🔗 Find your bot on Telegram and send /start")
    print("=" * 50)
    
    try:
        # Import and run the bot
        from telegram_bot import main as run_telegram_bot
        run_telegram_bot()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        print("Check the logs above for more details")

def install_requirements():
    """Install requirements automatically"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def quick_setup():
    """Quick setup wizard"""
    print("\n🧙‍♂️ Quick Setup Wizard")
    print("=" * 30)
    
    # Install requirements if needed
    if not check_requirements():
        print("📦 Would you like to install requirements automatically? (y/n): ", end="")
        if input().lower().startswith('y'):
            if not install_requirements():
                return False
        else:
            return False
    
    # Set up bot token if needed
    if not check_bot_token():
        print("\n🤖 Let's set up your Telegram bot token:")
        print("1. Go to @BotFather on Telegram")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the bot token you receive")
        print("\n🔑 Enter your bot token: ", end="")
        token = input().strip()
        
        if token:
            # Create .env file
            with open('.env', 'w') as f:
                f.write(f"TELEGRAM_BOT_TOKEN={token}\n")
            print("✅ Bot token saved to .env file")
            
            # Set environment variable for current session
            os.environ['TELEGRAM_BOT_TOKEN'] = token
        else:
            print("❌ No token provided")
            return False
    
    return True

if __name__ == "__main__":
    print("🎯 Choose an option:")
    print("1. Quick Start (run with current setup)")
    print("2. Setup Wizard (guided setup)")
    print("3. Check Status Only")
    print("\nEnter choice (1-3): ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        main()
    elif choice == "2":
        if quick_setup():
            print("\n🚀 Setup complete! Starting bot...")
            time.sleep(1)
            main()
        else:
            print("❌ Setup failed. Please fix issues and try again.")
    elif choice == "3":
        print("\n🔍 System Status Check:")
        print("-" * 30)
        check_requirements()
        check_bot_files()  
        check_bot_token()
        test_api_connectivity()
        print("\n✅ Status check complete")
    else:
        print("❌ Invalid choice. Please run again and choose 1, 2, or 3.")
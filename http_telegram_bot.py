#!/usr/bin/env python3
"""
No-Library Telegram Bot for Meme Coin Detection
Uses only requests library - no telegram dependencies
"""

import os
import json
import time
import threading
import requests
from datetime import datetime
from bot import MemeCoinBot

class SimpleTelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.meme_bot = MemeCoinBot()
        self.active_scans = {}
        self.last_update_id = 0
        
    def send_message(self, chat_id, text, buttons=None):
        """Send message via Telegram API"""
        url = f"{self.base_url}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        
        if buttons:
            data["reply_markup"] = json.dumps({"inline_keyboard": buttons})
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Send error: {e}")
            return None

    def edit_message(self, chat_id, message_id, text):
        """Edit existing message"""
        url = f"{self.base_url}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Edit error: {e}")

    def get_updates(self, offset=None):
        """Get new messages"""
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": 5}
        if offset:
            params["offset"] = offset
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Update error: {e}")
            return None

    def handle_start(self, chat_id):
        """Handle /start command"""
        text = """🚀 **Meme Coin Detective Bot**

I find high-potential meme coins!

**Commands:**
• `/quick` - Fast scan (3 coins)
• `/scan` - Full scan (7 coins)
• `/help` - Show help

Try `/quick` to get started!"""

        buttons = [[{"text": "🚀 Quick Scan", "callback_data": "quick"}]]
        self.send_message(chat_id, text, buttons)

    def handle_quick(self, chat_id, user_id):
        """Handle /quick command"""
        self.start_scan(chat_id, user_id, 3, "Quick")

    def handle_scan(self, chat_id, user_id):
        """Handle /scan command"""
        self.start_scan(chat_id, user_id, 7, "Full")

    def start_scan(self, chat_id, user_id, count, scan_type):
        """Start a scan"""
        if user_id in self.active_scans:
            self.send_message(chat_id, "⏳ Scan already running!")
            return

        response = self.send_message(
            chat_id,
            f"🔍 **{scan_type} Scan Starting...**\n⏱️ Takes 30-60 seconds..."
        )
        
        if not response or not response.get("ok"):
            return

        message_id = response["result"]["message_id"]
        
        self.active_scans[user_id] = {
            'start_time': datetime.now(),
            'chat_id': chat_id,
            'message_id': message_id
        }

        # Start background scan
        thread = threading.Thread(
            target=self.run_scan,
            args=(user_id, chat_id, message_id, count),
            daemon=True
        )
        thread.start()

    def run_scan(self, user_id, chat_id, message_id, count):
        """Run scan in background"""
        try:
            print(f"Starting scan for user {user_id}")
            
            # Update progress
            self.edit_message(chat_id, message_id, "🔄 **Analyzing market data...**")
            
            # Run actual scan
            results = self.meme_bot.get_top_coins(count)
            
            print(f"Scan complete: {len(results)} results")
            
            # Send results
            self.send_results(chat_id, message_id, results)
            
        except Exception as e:
            print(f"Scan failed: {e}")
            self.edit_message(chat_id, message_id, f"❌ Scan failed: {e}")
        finally:
            if user_id in self.active_scans:
                del self.active_scans[user_id]

    def send_results(self, chat_id, message_id, results):
        """Send scan results"""
        if not results:
            self.edit_message(chat_id, message_id, "❌ No coins found!")
            return

        # Create summary
        summary = f"🎯 **Found {len(results)} coins:**\n\n"
        
        for i, coin in enumerate(results[:5], 1):
            symbol = coin.get('symbol', 'UNKNOWN')
            score = coin.get('final_score', 0)
            
            if score >= 8: emoji = "🔥"
            elif score >= 6: emoji = "⭐"
            else: emoji = "⚠️"
            
            summary += f"{emoji} **#{i} {symbol}** - {score:.1f}/10\n"
            
            metrics = coin.get('key_metrics', {})
            mc = metrics.get('market_cap', 0)
            pc = metrics.get('price_change_24h', 0)
            
            if mc > 0:
                summary += f"   💰 ${mc:,.0f}"
            if pc != 0:
                summary += f" | 📊 {pc:+.1f}%"
            summary += "\n\n"

        summary += "Use `/scan` for more analysis!"
        
        self.edit_message(chat_id, message_id, summary)
        
        # Send details for top 3
        time.sleep(1)
        for i, coin in enumerate(results[:3], 1):
            self.send_coin_detail(chat_id, coin, i)

    def send_coin_detail(self, chat_id, coin, rank):
        """Send detailed coin info"""
        symbol = coin.get('symbol', 'UNKNOWN')
        score = coin.get('final_score', 0)
        
        if score >= 8: emoji, status = "🔥", "EXCELLENT"
        elif score >= 6: emoji, status = "⭐", "GOOD"
        else: emoji, status = "⚠️", "MODERATE"
        
        metrics = coin.get('key_metrics', {})
        scores = coin.get('component_scores', {})
        
        detail = f"""
{emoji} **#{rank} {symbol}** - {status}
**Score: {score:.1f}/10**

📊 **Metrics:**
💰 MC: ${metrics.get('market_cap', 0):,.0f}
📈 Vol: ${metrics.get('volume_24h', 0):,.0f}
📊 24h: {metrics.get('price_change_24h', 0):+.1f}%

🔍 **Scores:**
📊 Volume: {scores.get('volume', 0):.1f}/10
📈 Price: {scores.get('price', 0):.1f}/10
👥 Holders: {scores.get('holder', 0):.1f}/10
🛡️ Safety: {scores.get('safety', 0):.1f}/10
        """.strip()
        
        self.send_message(chat_id, detail)
        time.sleep(0.5)

    def handle_callback(self, chat_id, user_id, callback_data, message_id):
        """Handle button clicks"""
        if callback_data == "quick":
            if user_id in self.active_scans:
                self.edit_message(chat_id, message_id, "⏳ Already scanning!")
                return
            
            self.edit_message(chat_id, message_id, "🔍 **Quick Scan Starting...**")
            
            self.active_scans[user_id] = {
                'start_time': datetime.now(),
                'chat_id': chat_id,
                'message_id': message_id
            }
            
            thread = threading.Thread(
                target=self.run_scan,
                args=(user_id, chat_id, message_id, 3),
                daemon=True
            )
            thread.start()

    def process_update(self, update):
        """Process incoming update"""
        try:
            # Regular messages
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"]
                text = msg.get("text", "")
                
                if text.startswith("/start"):
                    self.handle_start(chat_id)
                elif text.startswith("/quick"):
                    self.handle_quick(chat_id, user_id)
                elif text.startswith("/scan"):
                    self.handle_scan(chat_id, user_id)
                elif text.startswith("/help"):
                    self.send_message(chat_id, 
                        "🤖 **Commands:**\n"
                        "• `/quick` - Fast scan\n"
                        "• `/scan` - Full scan\n"
                        "• `/start` - Welcome\n\n"
                        "Scans take 30-60 seconds!")
                else:
                    self.send_message(chat_id, "Try `/help` for commands!")
            
            # Button clicks
            elif "callback_query" in update:
                cb = update["callback_query"]
                chat_id = cb["message"]["chat"]["id"]
                user_id = cb["from"]["id"]
                message_id = cb["message"]["message_id"]
                callback_data = cb["data"]
                
                self.handle_callback(chat_id, user_id, callback_data, message_id)
                
        except Exception as e:
            print(f"Process error: {e}")

    def run(self):
        """Main bot loop"""
        print("🚀 Simple Telegram Bot Starting...")
        print("📱 Ready for users!")
        print("🔗 @Crypto_To_The_StarBot")
        print("-" * 30)
        
        while True:
            try:
                response = self.get_updates(self.last_update_id + 1)
                
                if response and response.get("ok"):
                    updates = response.get("result", [])
                    
                    for update in updates:
                        self.last_update_id = update["update_id"]
                        self.process_update(update)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n👋 Bot stopped")
                break
            except Exception as e:
                print(f"Main loop error: {e}")
                time.sleep(5)

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Set TELEGRAM_BOT_TOKEN first!")
        return
    
    try:
        bot = SimpleTelegramBot(token)
        bot.run()
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()
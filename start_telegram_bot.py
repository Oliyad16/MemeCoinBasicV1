#!/usr/bin/env python3
"""
Telegram Bot for Meme Coin Detection
Allows users to trigger scans and receive results via Telegram
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

# Import your existing bot
from bot import MemeCoinBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramMemeCoinBot:
    def __init__(self, telegram_token: str):
        self.telegram_token = telegram_token
        self.meme_bot = MemeCoinBot()
        self.active_scans = {}  # Track active scans per user
        self.user_settings = {}  # Store user preferences
        self.scan_results_cache = {}  # Cache recent results
        
        # Create application
        self.application = Application.builder().token(telegram_token).build()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("scan", self.scan_command))
        self.application.add_handler(CommandHandler("quick", self.quick_scan_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("results", self.last_results_command))
        
        # Callback handlers for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Initialize user settings
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                'notifications': True,
                'min_score': 6.0,
                'max_results': 5,
                'auto_alerts': False
            }
        
        welcome_text = f"""
🚀 **Welcome to Meme Coin Detective Bot!** 

Hello {username}! I help you find high-potential meme coins using advanced analysis.

**Quick Commands:**
• `/scan` - Full detailed analysis (top 7 coins)
• `/quick` - Fast scan (top 3 coins)
• `/settings` - Configure your preferences
• `/status` - Check current scan status
• `/results` - Get your last scan results
• `/help` - Show all commands

**What I analyze:**
📊 Volume spikes and momentum
💰 Market cap and liquidity
📈 Price movements and patterns
👥 Holder distribution
⚡ Real-time safety checks

Ready to find the next moonshot? Try `/quick` for a fast scan!
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Quick Scan", callback_data="quick_scan")],
            [InlineKeyboardButton("📊 Full Analysis", callback_data="full_scan")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **Meme Coin Detective Bot Commands**

**Scanning Commands:**
• `/scan` - Full analysis of trending meme coins
• `/quick` - Quick scan (faster, fewer results)

**Information Commands:**
• `/status` - Check if a scan is currently running
• `/results` - Get your most recent scan results
• `/settings` - Configure scan parameters

**Scan Parameters:**
You can customize scans with parameters:
• `/scan 10` - Get top 10 results
• `/scan 5 7.0` - Get 5 results with min score 7.0

**What the scores mean:**
• **8-10**: 🔥 Excellent potential, strong momentum
• **6-8**: ⭐ Good potential, worth watching
• **4-6**: ⚠️ Moderate potential, higher risk
• **0-4**: ❌ Poor potential, avoid

**Analysis Components:**
• **Volume Score**: Trading activity and spikes
• **Price Score**: Momentum and trend patterns  
• **Holder Score**: Distribution and growth
• **Safety Score**: Liquidity and risk factors

**Tips:**
• Scans take 30-60 seconds to complete
• Results are cached for 10 minutes
• Set alerts in `/settings` for automatic notifications
• Always DYOR (Do Your Own Research)!

Need help? Just type your question!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command with optional parameters"""
        user_id = update.effective_user.id
        
        # Check if user already has an active scan
        if user_id in self.active_scans:
            await update.message.reply_text(
                "⏳ You already have a scan running! Please wait for it to complete.\n"
                "Use `/status` to check progress."
            )
            return
        
        # Parse parameters
        args = context.args
        max_results = 7
        min_score = 0.0
        
        try:
            if len(args) >= 1:
                max_results = min(int(args[0]), 15)  # Max 15 results
            if len(args) >= 2:
                min_score = float(args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid parameters. Usage: `/scan [max_results] [min_score]`\n"
                "Example: `/scan 5 6.0`"
            )
            return
        
        # Start scan
        await self._start_scan(update, user_id, max_results, min_score, full_analysis=True)

    async def quick_scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quick command for fast scanning"""
        user_id = update.effective_user.id
        
        if user_id in self.active_scans:
            await update.message.reply_text("⏳ Scan already running! Use `/status` to check progress.")
            return
        
        # Quick scan with fewer results and higher score threshold
        await self._start_scan(update, user_id, max_results=3, min_score=5.0, full_analysis=False)

    async def _start_scan(self, update: Update, user_id: int, max_results: int, min_score: float, full_analysis: bool):
        """Start a meme coin scan"""
        scan_type = "Full Analysis" if full_analysis else "Quick Scan"
        
        # Send initial message
        loading_message = await update.message.reply_text(
            f"🔍 Starting {scan_type}...\n"
            f"📊 Looking for top {max_results} coins (min score: {min_score})\n"
            f"⏱️ This will take 30-60 seconds..."
        )
        
        # Mark scan as active
        self.active_scans[user_id] = {
            'start_time': datetime.now(),
            'message_id': loading_message.message_id,
            'chat_id': update.effective_chat.id,
            'max_results': max_results,
            'min_score': min_score,
            'full_analysis': full_analysis
        }
        
        # Run scan in background
        threading.Thread(
            target=self._run_scan_background,
            args=(user_id, update.effective_chat.id, loading_message.message_id)
        ).start()

    def _run_scan_background(self, user_id: int, chat_id: int, message_id: int):
        """Run the actual scan in background thread"""
        try:
            scan_info = self.active_scans[user_id]
            max_results = scan_info['max_results']
            min_score = scan_info['min_score']
            
            # Update progress
            asyncio.create_task(self._update_scan_progress(chat_id, message_id, "🔄 Fetching trending tokens..."))
            
            # Run the scan
            results = self.meme_bot.get_top_coins(max_results * 2)  # Get more to filter
            
            # Filter by minimum score
            filtered_results = [r for r in results if r.get('final_score', 0) >= min_score][:max_results]
            
            # Cache results
            self.scan_results_cache[user_id] = {
                'results': filtered_results,
                'timestamp': datetime.now(),
                'scan_params': scan_info
            }
            
            # Send results
            asyncio.create_task(self._send_scan_results(user_id, chat_id, message_id, filtered_results))
            
        except Exception as e:
            logger.error(f"Scan failed for user {user_id}: {e}")
            asyncio.create_task(self._send_scan_error(chat_id, message_id, str(e)))
        finally:
            # Remove from active scans
            if user_id in self.active_scans:
                del self.active_scans[user_id]

    async def _update_scan_progress(self, chat_id: int, message_id: int, text: str):
        """Update scan progress message"""
        try:
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text
            )
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    async def _send_scan_results(self, user_id: int, chat_id: int, message_id: int, results: List[Dict]):
        """Send scan results to user"""
        try:
            if not results:
                await self.application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text="❌ No coins found matching your criteria.\n"
                         "Try lowering the minimum score or running `/quick` for broader results."
                )
                return
            
            # Create results summary
            summary_text = f"🎯 **Scan Complete!** Found {len(results)} promising coins:\n\n"
            
            for i, coin in enumerate(results[:5], 1):  # Show first 5 in summary
                symbol = coin.get('symbol', 'UNKNOWN')
                score = coin.get('final_score', 0)
                market_cap = coin.get('key_metrics', {}).get('market_cap', 0)
                price_change = coin.get('key_metrics', {}).get('price_change_24h', 0)
                
                # Score emoji
                if score >= 8: score_emoji = "🔥"
                elif score >= 6: score_emoji = "⭐"
                elif score >= 4: score_emoji = "⚠️"
                else: score_emoji = "❌"
                
                # Price change emoji
                if price_change > 0: price_emoji = "📈"
                else: price_emoji = "📉"
                
                summary_text += f"{score_emoji} **#{i} {symbol}** - Score: {score}/10\n"
                summary_text += f"   💰 MC: ${market_cap:,.0f} | {price_emoji} 24h: {price_change:+.1f}%\n\n"
            
            # Add action buttons
            keyboard = [
                [InlineKeyboardButton(f"📊 View Details ({len(results)} coins)", callback_data=f"details_{user_id}")],
                [InlineKeyboardButton("🔄 New Scan", callback_data="quick_scan"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=summary_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Failed to send results: {e}")
            await self._send_scan_error(chat_id, message_id, str(e))

    async def _send_scan_error(self, chat_id: int, message_id: int, error: str):
        """Send scan error message"""
        try:
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ Scan failed: {error}\n\n"
                     f"This might be due to:\n"
                     f"• API rate limits\n"
                     f"• Network connectivity issues\n"
                     f"• High server load\n\n"
                     f"Please try again in a few minutes."
            )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = update.effective_user.id
        
        if data == "quick_scan":
            await self._handle_quick_scan_button(query, user_id)
        elif data == "full_scan":
            await self._handle_full_scan_button(query, user_id)
        elif data == "settings":
            await self._handle_settings_button(query, user_id)
        elif data.startswith("details_"):
            target_user_id = int(data.split("_")[1])
            await self._handle_details_button(query, target_user_id)
        elif data.startswith("coin_"):
            coin_index = int(data.split("_")[1])
            await self._handle_coin_details(query, user_id, coin_index)

    async def _handle_quick_scan_button(self, query, user_id: int):
        """Handle quick scan button press"""
        if user_id in self.active_scans:
            await query.edit_message_text("⏳ Scan already running!")
            return
        
        await query.edit_message_text("🔍 Starting Quick Scan...\n⏱️ This will take 30-60 seconds...")
        
        self.active_scans[user_id] = {
            'start_time': datetime.now(),
            'message_id': query.message.message_id,
            'chat_id': query.message.chat_id,
            'max_results': 3,
            'min_score': 5.0,
            'full_analysis': False
        }
        
        threading.Thread(
            target=self._run_scan_background,
            args=(user_id, query.message.chat_id, query.message.message_id)
        ).start()

    async def _handle_details_button(self, query, user_id: int):
        """Handle details button press"""
        if user_id not in self.scan_results_cache:
            await query.edit_message_text("❌ No recent results found. Please run a new scan.")
            return
        
        results = self.scan_results_cache[user_id]['results']
        await self._send_detailed_results(query, results)

    async def _send_detailed_results(self, query, results: List[Dict]):
        """Send detailed results for each coin"""
        for i, coin in enumerate(results):
            symbol = coin.get('symbol', 'UNKNOWN')
            score = coin.get('final_score', 0)
            
            # Create detailed message
            detail_text = self._format_coin_details(coin, i + 1)
            
            # Create coin-specific keyboard
            keyboard = []
            if coin.get('dex_url'):
                keyboard.append([InlineKeyboardButton("🔗 View on DexScreener", url=coin['dex_url'])])
            
            if i < len(results) - 1:
                keyboard.append([InlineKeyboardButton(f"➡️ Next Coin ({results[i+1].get('symbol', 'UNKNOWN')})", 
                                                    callback_data=f"coin_{i+1}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            await query.message.reply_text(
                detail_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )

    def _format_coin_details(self, coin: Dict, rank: int) -> str:
        """Format detailed coin information"""
        symbol = coin.get('symbol', 'UNKNOWN')
        score = coin.get('final_score', 0)
        
        # Score emoji and status
        if score >= 8: 
            score_emoji = "🔥"
            status = "EXCELLENT"
        elif score >= 6: 
            score_emoji = "⭐"
            status = "GOOD"
        elif score >= 4: 
            score_emoji = "⚠️"
            status = "MODERATE"
        else: 
            score_emoji = "❌"
            status = "POOR"
        
        # Get metrics
        metrics = coin.get('key_metrics', {})
        scores = coin.get('component_scores', {})
        
        market_cap = metrics.get('market_cap', 0)
        volume_24h = metrics.get('volume_24h', 0)
        liquidity = metrics.get('liquidity', 0)
        price_change = metrics.get('price_change_24h', 0)
        
        # Format the message
        text = f"""
{score_emoji} **#{rank} {symbol}** - {status}
**Overall Score: {score}/10**

📊 **Key Metrics:**
💰 Market Cap: ${market_cap:,.0f}
📈 24h Volume: ${volume_24h:,.0f}
💧 Liquidity: ${liquidity:,.0f}
📊 24h Change: {price_change:+.1f}%

🔍 **Component Scores:**
📊 Volume: {scores.get('volume', 0):.1f}/10
📈 Price: {scores.get('price', 0):.1f}/10  
👥 Holders: {scores.get('holder', 0):.1f}/10
🛡️ Safety: {scores.get('safety', 0):.1f}/10

⚠️ **Risk Flags:**
{self._format_risk_flags(coin.get('risk_flags', []))}

⏰ Next Check: {coin.get('next_check_minutes', 60)} minutes
        """
        
        return text.strip()

    def _format_risk_flags(self, risk_flags: List[str]) -> str:
        """Format risk flags for display"""
        if not risk_flags:
            return "✅ No major risks detected"
        
        return "\n".join([f"• {flag}" for flag in risk_flags])

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if user_id not in self.active_scans:
            # Check for recent results
            if user_id in self.scan_results_cache:
                cache_entry = self.scan_results_cache[user_id]
                time_ago = datetime.now() - cache_entry['timestamp']
                
                if time_ago.total_seconds() < 600:  # 10 minutes
                    minutes_ago = int(time_ago.total_seconds() / 60)
                    results_count = len(cache_entry['results'])
                    
                    text = f"✅ **Last scan completed {minutes_ago} minutes ago**\n"
                    text += f"📊 Found {results_count} coins\n"
                    text += f"Use `/results` to view them again."
                else:
                    text = "💤 No active scans. Use `/scan` or `/quick` to start!"
            else:
                text = "💤 No active scans. Use `/scan` or `/quick` to start!"
        else:
            scan_info = self.active_scans[user_id]
            elapsed = datetime.now() - scan_info['start_time']
            elapsed_seconds = int(elapsed.total_seconds())
            
            text = f"🔄 **Scan in progress...**\n"
            text += f"⏱️ Running for {elapsed_seconds} seconds\n"
            text += f"📊 Looking for {scan_info['max_results']} coins\n"
            text += f"🎯 Min score: {scan_info['min_score']}"
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def last_results_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /results command"""
        user_id = update.effective_user.id
        
        if user_id not in self.scan_results_cache:
            await update.message.reply_text(
                "❌ No recent results found.\n"
                "Use `/scan` or `/quick` to run a new analysis!"
            )
            return
        
        cache_entry = self.scan_results_cache[user_id]
        time_ago = datetime.now() - cache_entry['timestamp']
        
        if time_ago.total_seconds() > 3600:  # 1 hour
            await update.message.reply_text(
                "⏰ Your last results are more than 1 hour old.\n"
                "Use `/scan` to get fresh data!"
            )
            return
        
        results = cache_entry['results']
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        summary_text = f"📊 **Your Last Scan Results** ({minutes_ago} min ago)\n\n"
        
        for i, coin in enumerate(results[:3], 1):  # Show top 3
            symbol = coin.get('symbol', 'UNKNOWN')
            score = coin.get('final_score', 0)
            
            if score >= 8: emoji = "🔥"
            elif score >= 6: emoji = "⭐"
            else: emoji = "⚠️"
            
            summary_text += f"{emoji} {symbol}: {score}/10\n"
        
        if len(results) > 3:
            summary_text += f"\n+ {len(results) - 3} more coins...\n"
        
        keyboard = [[InlineKeyboardButton("📊 View Full Details", callback_data=f"details_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            summary_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, {})
        
        settings_text = f"""
⚙️ **Your Settings**

🎯 Min Score Threshold: {settings.get('min_score', 6.0)}
📊 Max Results: {settings.get('max_results', 5)}
🔔 Notifications: {'✅ Enabled' if settings.get('notifications', True) else '❌ Disabled'}
⚡ Auto Alerts: {'✅ Enabled' if settings.get('auto_alerts', False) else '❌ Disabled'}

**How to modify:**
• `/set_score 7.5` - Set minimum score
• `/set_results 10` - Set max results  
• `/toggle_notifications` - Enable/disable notifications
• `/toggle_alerts` - Enable/disable auto alerts

Current settings affect your scans and notifications.
        """
        
        await update.message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        message_text = update.message.text.lower()
        
        # Simple keyword responses
        if any(word in message_text for word in ['hello', 'hi', 'hey']):
            await update.message.reply_text(
                "👋 Hello! Ready to find some meme coins?\n"
                "Use `/quick` for a fast scan or `/scan` for detailed analysis!"
            )
        elif any(word in message_text for word in ['help', 'how', 'what']):
            await update.message.reply_text(
                "🤖 I help you find promising meme coins!\n"
                "Try `/help` for all commands or `/quick` to get started."
            )
        elif any(word in message_text for word in ['moon', 'pump', 'rocket']):
            await update.message.reply_text(
                "🚀 Looking for moonshots? Let me scan for you!\n"
                "Use `/scan` for the best analysis."
            )
        else:
            await update.message.reply_text(
                "🤔 I'm not sure what you mean. Try `/help` to see what I can do!"
            )

    def run(self):
        """Start the Telegram bot"""
        logger.info("Starting Telegram Meme Coin Bot...")
        self.application.run_polling(drop_pending_updates=True)

def main():
    """Main function to run the Telegram bot"""
    # Get token from environment variable
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not telegram_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set your bot token:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # Create and run bot
    bot = TelegramMemeCoinBot(telegram_token)
    
    print("🚀 Telegram Meme Coin Bot starting...")
    print("📱 Users can now interact with your bot on Telegram!")
    print("🔧 Make sure to set the bot token as an environment variable")
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    main()
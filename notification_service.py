#!/usr/bin/env python3
"""
Notification Service - Multi-Channel Alerts
Sends notifications via Telegram, Browser, and Console
"""

import os
import logging
from typing import Dict, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.telegram_enabled = bool(self.telegram_token and self.telegram_chat_id)

        # Store recent notifications to avoid spam
        self.recent_notifications = []
        self.max_recent = 50

        if self.telegram_enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    def send_exit_alert(self, investment: Dict, action: str, signals: List[Dict]):
        """Send exit alert for an investment"""
        symbol = investment.get("symbol", "UNKNOWN")

        # Create message
        message = self._format_exit_message(investment, action, signals)

        # Send via all channels
        self._send_console(message, action)

        if self.telegram_enabled:
            self._send_telegram(message, action)

        # Store for web notifications
        self._store_web_notification(investment, action, message)

        logger.info(f"Sent {action} alert for {symbol}")

    def _format_exit_message(self, investment: Dict, action: str, signals: List[Dict]) -> str:
        """Format exit message"""
        symbol = investment.get("symbol", "UNKNOWN")
        time_held = investment.get("time_held_minutes", 0)
        profit_pct = investment.get("profit_loss_pct", 0)

        # Action header
        if action == "SELL_NOW":
            header = f"🔴 SELL NOW - {symbol}"
        elif action == "TAKE_PROFIT":
            header = f"💰 TAKE PROFIT - {symbol}"
        elif action == "WARNING":
            header = f"⚠️ WARNING - {symbol}"
        else:
            header = f"📊 UPDATE - {symbol}"

        # Build message
        lines = [header, ""]

        # Time and profit
        hours = int(time_held // 60)
        mins = int(time_held % 60)
        time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        lines.append(f"⏱️ Time Held: {time_str}")
        lines.append(f"📈 P/L: {profit_pct:+.1f}%")
        lines.append("")

        # Signals
        if signals:
            lines.append("🚨 Signals:")
            for signal in signals:
                lines.append(f"  • {signal['message']}")
            lines.append("")

        # Action recommendation
        if action == "SELL_NOW":
            lines.append("⚡ ACTION: Consider exiting this position immediately!")
        elif action == "TAKE_PROFIT":
            lines.append("💵 ACTION: Consider taking profits or setting stop-loss!")
        elif action == "WARNING":
            lines.append("👀 ACTION: Monitor this position closely!")

        return "\n".join(lines)

    def _send_console(self, message: str, action: str):
        """Send notification to console (always works)"""
        try:
            print("\n" + "="*60)
            print(message)
            print("="*60 + "\n")
        except Exception as e:
            logger.error(f"Console notification failed: {e}")

    def _send_telegram(self, message: str, action: str):
        """Send notification via Telegram"""
        try:
            import requests

            # Add urgency indicator
            if action == "SELL_NOW":
                message = "🚨 URGENT ALERT 🚨\n\n" + message

            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Telegram notification sent successfully")
            else:
                logger.warning(f"Telegram notification failed: {response.status_code}")

        except ImportError:
            logger.warning("Requests library not available for Telegram notifications")
        except Exception as e:
            logger.error(f"Telegram notification error: {e}")

    def _store_web_notification(self, investment: Dict, action: str, message: str):
        """Store notification for web UI"""
        try:
            notification = {
                "id": str(int(datetime.now().timestamp() * 1000)),
                "investment_id": investment.get("id"),
                "symbol": investment.get("symbol"),
                "action": action,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "read": False
            }

            self.recent_notifications.append(notification)

            # Keep only last N notifications
            if len(self.recent_notifications) > self.max_recent:
                self.recent_notifications = self.recent_notifications[-self.max_recent:]

        except Exception as e:
            logger.error(f"Error storing web notification: {e}")

    def get_recent_notifications(self, limit: int = 10) -> List[Dict]:
        """Get recent notifications for web UI"""
        return self.recent_notifications[-limit:][::-1]  # Most recent first

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        for notif in self.recent_notifications:
            if notif["id"] == notification_id:
                notif["read"] = True
                return True
        return False

    def send_test_notification(self, channel: str = "all"):
        """Send a test notification"""
        test_message = f"""
🧪 TEST NOTIFICATION

This is a test alert from your Meme Coin Bot!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Channel: {channel}

If you see this, notifications are working! 🎉
        """

        if channel in ["all", "console"]:
            self._send_console(test_message, "TEST")

        if channel in ["all", "telegram"] and self.telegram_enabled:
            self._send_telegram(test_message, "TEST")

        logger.info(f"Test notification sent via {channel}")

    def send_profit_milestone(self, investment: Dict, milestone: str):
        """Send notification when profit milestone reached"""
        symbol = investment.get("symbol")
        profit_pct = investment.get("profit_loss_pct", 0)

        message = f"""
🎉 PROFIT MILESTONE - {symbol}

You've reached {milestone}!

Current Profit: {profit_pct:+.1f}%
Time Held: {investment.get("time_held_minutes", 0):.0f} minutes

💡 TIP: Consider taking some profits to secure gains!
        """

        self._send_console(message, "PROFIT_MILESTONE")

        if self.telegram_enabled:
            self._send_telegram(message, "PROFIT_MILESTONE")

    def is_telegram_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return self.telegram_enabled

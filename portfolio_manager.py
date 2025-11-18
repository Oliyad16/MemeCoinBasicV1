#!/usr/bin/env python3
"""
Portfolio Manager - Track Your Invested Coins
Manages portfolio storage, updates, and retrieval
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, portfolio_file: str = "portfolio.json"):
        self.portfolio_file = portfolio_file
        self.portfolio = self._load_portfolio()

    def _load_portfolio(self) -> Dict:
        """Load portfolio from JSON file"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio: {e}")
                return {"investments": [], "alerts": []}
        else:
            return {"investments": [], "alerts": []}

    def _save_portfolio(self):
        """Save portfolio to JSON file"""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.portfolio, f, indent=2)
            logger.info(f"Portfolio saved successfully")
        except Exception as e:
            logger.error(f"Error saving portfolio: {e}")

    def add_investment(self, coin_data: Dict, investment_amount: float = 0) -> bool:
        """Add a new coin to track"""
        try:
            # Check if already tracking this coin
            address = coin_data.get('address')
            if self.is_tracking(address):
                logger.warning(f"Already tracking coin: {address}")
                return False

            investment = {
                "id": str(int(time.time() * 1000)),  # Unique ID
                "symbol": coin_data.get('symbol'),
                "address": address,
                "dex_url": coin_data.get('dex_url'),

                # Entry metrics
                "entry_time": datetime.now().isoformat(),
                "entry_price": coin_data.get('key_metrics', {}).get('price_change_24h', 0),
                "entry_market_cap": coin_data.get('key_metrics', {}).get('market_cap', 0),
                "entry_volume": coin_data.get('key_metrics', {}).get('volume_24h', 0),
                "entry_liquidity": coin_data.get('key_metrics', {}).get('liquidity', 0),
                "entry_score": coin_data.get('final_score', 0),

                # Component scores at entry
                "entry_component_scores": coin_data.get('component_scores', {}),

                # Investment tracking
                "investment_amount": investment_amount,
                "status": "watching",  # watching, profit, danger, exited

                # Current metrics (will be updated by monitor)
                "current_price": None,
                "current_market_cap": None,
                "current_volume": None,
                "current_liquidity": None,
                "current_score": None,

                # Performance tracking
                "price_change_pct": 0,
                "profit_loss_pct": 0,
                "time_held_minutes": 0,
                "peak_profit_pct": 0,

                # Exit signals
                "exit_signals": [],
                "last_alert_time": None,
            }

            self.portfolio["investments"].append(investment)
            self._save_portfolio()
            logger.info(f"Added {investment['symbol']} to portfolio")
            return True

        except Exception as e:
            logger.error(f"Error adding investment: {e}")
            return False

    def remove_investment(self, investment_id: str) -> bool:
        """Remove a coin from tracking"""
        try:
            original_length = len(self.portfolio["investments"])
            self.portfolio["investments"] = [
                inv for inv in self.portfolio["investments"]
                if inv["id"] != investment_id
            ]

            if len(self.portfolio["investments"]) < original_length:
                self._save_portfolio()
                logger.info(f"Removed investment {investment_id}")
                return True
            else:
                logger.warning(f"Investment {investment_id} not found")
                return False

        except Exception as e:
            logger.error(f"Error removing investment: {e}")
            return False

    def is_tracking(self, address: str) -> bool:
        """Check if already tracking this coin"""
        return any(inv["address"] == address for inv in self.portfolio["investments"])

    def get_all_investments(self) -> List[Dict]:
        """Get all tracked investments"""
        return self.portfolio["investments"]

    def get_investment(self, investment_id: str) -> Optional[Dict]:
        """Get a specific investment by ID"""
        for inv in self.portfolio["investments"]:
            if inv["id"] == investment_id:
                return inv
        return None

    def update_investment(self, investment_id: str, updates: Dict) -> bool:
        """Update an investment's current metrics"""
        try:
            for inv in self.portfolio["investments"]:
                if inv["id"] == investment_id:
                    inv.update(updates)

                    # Calculate time held
                    entry_time = datetime.fromisoformat(inv["entry_time"])
                    time_held = (datetime.now() - entry_time).total_seconds() / 60
                    inv["time_held_minutes"] = round(time_held, 1)

                    self._save_portfolio()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating investment: {e}")
            return False

    def add_alert(self, investment_id: str, alert_type: str, message: str, urgency: str = "medium"):
        """Add an alert for an investment"""
        try:
            alert = {
                "id": str(int(time.time() * 1000)),
                "investment_id": investment_id,
                "alert_type": alert_type,  # "exit_now", "take_profit", "warning"
                "message": message,
                "urgency": urgency,  # "critical", "high", "medium", "low"
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            }

            self.portfolio["alerts"].append(alert)
            self._save_portfolio()
            logger.info(f"Added alert: {alert_type} for investment {investment_id}")

        except Exception as e:
            logger.error(f"Error adding alert: {e}")

    def get_active_alerts(self) -> List[Dict]:
        """Get all unacknowledged alerts"""
        return [alert for alert in self.portfolio["alerts"] if not alert["acknowledged"]]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged"""
        try:
            for alert in self.portfolio["alerts"]:
                if alert["id"] == alert_id:
                    alert["acknowledged"] = True
                    self._save_portfolio()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False

    def get_portfolio_summary(self) -> Dict:
        """Get summary statistics of portfolio"""
        investments = self.portfolio["investments"]

        if not investments:
            return {
                "total_investments": 0,
                "watching": 0,
                "in_profit": 0,
                "in_danger": 0,
                "avg_profit_pct": 0,
                "total_alerts": len(self.get_active_alerts())
            }

        watching = sum(1 for inv in investments if inv["status"] == "watching")
        in_profit = sum(1 for inv in investments if inv["status"] == "profit")
        in_danger = sum(1 for inv in investments if inv["status"] == "danger")

        profits = [inv.get("profit_loss_pct", 0) for inv in investments if inv.get("profit_loss_pct")]
        avg_profit = sum(profits) / len(profits) if profits else 0

        return {
            "total_investments": len(investments),
            "watching": watching,
            "in_profit": in_profit,
            "in_danger": in_danger,
            "avg_profit_pct": round(avg_profit, 2),
            "total_alerts": len(self.get_active_alerts())
        }

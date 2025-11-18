#!/usr/bin/env python3
"""
Exit Signal Detection - Smart Exit Logic
Analyzes when to exit a position based on multiple indicators
"""

import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExitSignalDetector:
    def __init__(self):
        # Thresholds for different exit signals
        self.CRITICAL_LOSS_PCT = -15  # Sell immediately if down 15%
        self.STOP_LOSS_PCT = -10      # Strong sell signal at -10%
        self.WARNING_LOSS_PCT = -5    # Warning at -5%

        self.VOLUME_DROP_CRITICAL = -50  # Volume dropped 50%
        self.LIQUIDITY_DROP_CRITICAL = -30  # Liquidity dropped 30% (rug pull!)

        self.TAKE_PROFIT_2X = 100   # 2x gain
        self.TAKE_PROFIT_5X = 400   # 5x gain
        self.TAKE_PROFIT_10X = 900  # 10x gain

    def analyze_exit_signals(self, investment: Dict, current_data: Dict) -> Tuple[str, List[Dict], str]:
        """
        Analyze if should exit this investment
        Returns: (action, signals, status)
        action: "SELL_NOW", "TAKE_PROFIT", "HOLD", "WARNING"
        signals: List of signal dicts with reasons
        status: "danger", "profit", "watching"
        """

        signals = []
        entry_metrics = self._extract_entry_metrics(investment)
        current_metrics = self._extract_current_metrics(current_data)

        # Calculate price change
        price_change_pct = self._calculate_price_change(investment, current_data)

        # 1. CRITICAL SELL SIGNALS (Exit immediately!)
        critical_signals = self._check_critical_signals(
            entry_metrics, current_metrics, price_change_pct
        )
        if critical_signals:
            signals.extend(critical_signals)
            return "SELL_NOW", signals, "danger"

        # 2. TAKE PROFIT SIGNALS (Consider selling)
        profit_signals = self._check_profit_signals(
            entry_metrics, current_metrics, price_change_pct
        )
        if profit_signals:
            signals.extend(profit_signals)
            return "TAKE_PROFIT", signals, "profit"

        # 3. WARNING SIGNALS (Monitor closely)
        warning_signals = self._check_warning_signals(
            entry_metrics, current_metrics, price_change_pct
        )
        if warning_signals:
            signals.extend(warning_signals)
            return "WARNING", signals, "watching"

        # 4. All good - HOLD
        return "HOLD", [], "watching"

    def _extract_entry_metrics(self, investment: Dict) -> Dict:
        """Extract entry metrics from investment"""
        return {
            "market_cap": investment.get("entry_market_cap", 0),
            "volume": investment.get("entry_volume", 0),
            "liquidity": investment.get("entry_liquidity", 0),
            "score": investment.get("entry_score", 0),
            "component_scores": investment.get("entry_component_scores", {})
        }

    def _extract_current_metrics(self, current_data: Dict) -> Dict:
        """Extract current metrics from live data"""
        key_metrics = current_data.get("key_metrics", {})
        return {
            "market_cap": key_metrics.get("market_cap", 0),
            "volume": key_metrics.get("volume_24h", 0),
            "liquidity": key_metrics.get("liquidity", 0),
            "score": current_data.get("final_score", 0),
            "component_scores": current_data.get("component_scores", {}),
            "price_change_1h": key_metrics.get("price_change_1h", 0),
            "price_change_24h": key_metrics.get("price_change_24h", 0)
        }

    def _calculate_price_change(self, investment: Dict, current_data: Dict) -> float:
        """Calculate price change since entry"""
        # Use market cap as proxy for price if we don't have direct price
        entry_mc = investment.get("entry_market_cap", 0)
        current_mc = current_data.get("key_metrics", {}).get("market_cap", 0)

        if entry_mc > 0 and current_mc > 0:
            return ((current_mc - entry_mc) / entry_mc) * 100
        else:
            # Fallback to 24h price change
            return current_data.get("key_metrics", {}).get("price_change_24h", 0)

    def _check_critical_signals(self, entry: Dict, current: Dict, price_change: float) -> List[Dict]:
        """Check for CRITICAL exit signals - SELL NOW!"""
        signals = []

        # 1. MASSIVE LOSS
        if price_change <= self.CRITICAL_LOSS_PCT:
            signals.append({
                "type": "CRITICAL_LOSS",
                "severity": "critical",
                "message": f"🔴 SELL NOW! Price down {price_change:.1f}% from entry",
                "value": price_change
            })

        # 2. LIQUIDITY CRASH (Rug pull warning!)
        if entry["liquidity"] > 0:
            liquidity_change = ((current["liquidity"] - entry["liquidity"]) / entry["liquidity"]) * 100
            if liquidity_change <= self.LIQUIDITY_DROP_CRITICAL:
                signals.append({
                    "type": "LIQUIDITY_CRASH",
                    "severity": "critical",
                    "message": f"🚨 RUG PULL WARNING! Liquidity dropped {abs(liquidity_change):.1f}%",
                    "value": liquidity_change
                })

        # 3. VOLUME DEATH
        if entry["volume"] > 0:
            volume_change = ((current["volume"] - entry["volume"]) / entry["volume"]) * 100
            if volume_change <= self.VOLUME_DROP_CRITICAL:
                signals.append({
                    "type": "VOLUME_DEATH",
                    "severity": "critical",
                    "message": f"🔴 Volume collapsed {abs(volume_change):.1f}% - No buyers!",
                    "value": volume_change
                })

        # 4. HEAVY DUMP (1h price movement)
        price_1h = current.get("price_change_1h", 0)
        if price_1h < -20:
            signals.append({
                "type": "HEAVY_DUMP",
                "severity": "critical",
                "message": f"🔴 Heavy dumping! Down {abs(price_1h):.1f}% in last hour",
                "value": price_1h
            })

        return signals

    def _check_profit_signals(self, entry: Dict, current: Dict, price_change: float) -> List[Dict]:
        """Check for TAKE PROFIT signals"""
        signals = []

        # 1. MAJOR PROFIT MILESTONES
        if price_change >= self.TAKE_PROFIT_10X:
            signals.append({
                "type": "PROFIT_10X",
                "severity": "high",
                "message": f"🎉 10x PROFIT! Up {price_change:.1f}% - Consider taking profits!",
                "value": price_change
            })
        elif price_change >= self.TAKE_PROFIT_5X:
            signals.append({
                "type": "PROFIT_5X",
                "severity": "high",
                "message": f"💰 5x PROFIT! Up {price_change:.1f}% - Consider taking some profit!",
                "value": price_change
            })
        elif price_change >= self.TAKE_PROFIT_2X:
            signals.append({
                "type": "PROFIT_2X",
                "severity": "medium",
                "message": f"✅ 2x PROFIT! Up {price_change:.1f}% - Good time to secure gains!",
                "value": price_change
            })

        # 2. PROFIT WITH MOMENTUM TURNING
        if price_change > 50:  # In profit
            price_1h = current.get("price_change_1h", 0)
            if price_1h < -5:  # But momentum turning negative
                signals.append({
                    "type": "MOMENTUM_REVERSAL",
                    "severity": "medium",
                    "message": f"⚠️ Up {price_change:.1f}% total, but momentum turning negative (1h: {price_1h:.1f}%)",
                    "value": price_change
                })

        return signals

    def _check_warning_signals(self, entry: Dict, current: Dict, price_change: float) -> List[Dict]:
        """Check for WARNING signals - monitor closely"""
        signals = []

        # 1. MODERATE LOSS
        if self.WARNING_LOSS_PCT <= price_change < self.STOP_LOSS_PCT:
            signals.append({
                "type": "MODERATE_LOSS",
                "severity": "medium",
                "message": f"⚠️ Down {abs(price_change):.1f}% - Monitor closely",
                "value": price_change
            })

        # 2. SCORE DROPPING
        if entry["score"] > 0:
            score_change = current["score"] - entry["score"]
            if score_change < -2:  # Score dropped more than 2 points
                signals.append({
                    "type": "SCORE_DROP",
                    "severity": "medium",
                    "message": f"⚠️ Quality score dropped {abs(score_change):.1f} points",
                    "value": score_change
                })

        # 3. VOLUME DECLINING
        if entry["volume"] > 0:
            volume_change = ((current["volume"] - entry["volume"]) / entry["volume"]) * 100
            if -50 < volume_change < -20:  # Volume down 20-50%
                signals.append({
                    "type": "VOLUME_DECLINING",
                    "severity": "low",
                    "message": f"⚠️ Volume declining ({volume_change:.1f}%)",
                    "value": volume_change
                })

        return signals

    def get_action_color(self, action: str) -> str:
        """Get color code for action"""
        colors = {
            "SELL_NOW": "red",
            "TAKE_PROFIT": "green",
            "WARNING": "yellow",
            "HOLD": "blue"
        }
        return colors.get(action, "gray")

    def get_action_emoji(self, action: str) -> str:
        """Get emoji for action"""
        emojis = {
            "SELL_NOW": "🔴",
            "TAKE_PROFIT": "💰",
            "WARNING": "⚠️",
            "HOLD": "✅"
        }
        return emojis.get(action, "📊")

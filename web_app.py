#!/usr/bin/env python3
"""
Flask Web Backend for Meme Coin Detection Bot
Provides REST API and web interface
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime
from typing import Dict
import logging
import requests

# Import your existing bot
from bot import MemeCoinBot

# Import portfolio modules
from portfolio_manager import PortfolioManager
from exit_signals import ExitSignalDetector
from notification_service import NotificationService

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
bot = MemeCoinBot()
portfolio_manager = PortfolioManager()
exit_detector = ExitSignalDetector()
notification_service = NotificationService()

current_scan_status = {"status": "idle", "message": "", "progress": 0}
last_results = []
scan_lock = threading.Lock()
monitoring_active = False
monitoring_thread = None

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

@app.route('/portfolio')
def portfolio():
    """Serve the portfolio page"""
    return render_template('portfolio.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start a new meme coin scan"""
    global current_scan_status
    
    with scan_lock:
        if current_scan_status["status"] == "scanning":
            return jsonify({"error": "Scan already in progress"}), 400
        
        # Get parameters from request
        data = request.get_json() or {}
        max_coins = data.get('max_coins', 7)
        min_score = data.get('min_score', 0)
        max_age_days = data.get('max_age_days', 30)
        
        # Start scan in background thread
        thread = threading.Thread(target=run_scan, args=(max_coins, min_score, max_age_days))
        thread.start()
        
        return jsonify({"message": "Scan started", "status": "scanning"})

@app.route('/api/status')
def get_status():
    """Get current scan status"""
    return jsonify(current_scan_status)

@app.route('/api/results')
def get_results():
    """Get latest scan results"""
    return jsonify({
        "results": last_results,
        "timestamp": datetime.now().isoformat(),
        "count": len(last_results)
    })

def run_scan(max_coins, min_score, max_age_days):
    """Run the actual scan in background"""
    global current_scan_status, last_results
    
    try:
        current_scan_status = {"status": "scanning", "message": "Initializing scan...", "progress": 10}
        
        # Update status during scan
        current_scan_status["message"] = "Fetching trending tokens..."
        current_scan_status["progress"] = 25
        
        # Run the actual bot scan
        results = bot.get_top_coins(max_coins)
        
        current_scan_status["message"] = "Analyzing tokens..."
        current_scan_status["progress"] = 75
        
        # Filter by minimum score
        filtered_results = [r for r in results if r.get('final_score', 0) >= min_score]
        
        current_scan_status["message"] = "Finalizing results..."
        current_scan_status["progress"] = 90
        
        # Store results
        last_results = filtered_results
        
        current_scan_status = {
            "status": "complete", 
            "message": f"Found {len(filtered_results)} coins", 
            "progress": 100
        }
        
        logger.info(f"Scan completed. Found {len(filtered_results)} coins.")
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        current_scan_status = {
            "status": "error", 
            "message": f"Scan failed: {str(e)}", 
            "progress": 0
        }

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_version": "1.0.0"
    })

# ==================== PORTFOLIO API ENDPOINTS ====================

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    """Add a coin to portfolio tracking"""
    try:
        data = request.get_json()
        investment_amount = data.get('investment_amount', 0)

        success = portfolio_manager.add_investment(data, investment_amount)

        if success:
            # Start monitoring thread if not already running
            start_monitoring_thread()
            return jsonify({"success": True, "message": "Added to portfolio"})
        else:
            return jsonify({"success": False, "message": "Already tracking this coin"}), 400

    except Exception as e:
        logger.error(f"Error adding to portfolio: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/portfolio/remove/<investment_id>', methods=['DELETE'])
def remove_from_portfolio(investment_id):
    """Remove a coin from portfolio tracking"""
    try:
        success = portfolio_manager.remove_investment(investment_id)

        if success:
            return jsonify({"success": True, "message": "Removed from portfolio"})
        else:
            return jsonify({"success": False, "message": "Investment not found"}), 404

    except Exception as e:
        logger.error(f"Error removing from portfolio: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/portfolio/list')
def list_portfolio():
    """Get all tracked investments"""
    try:
        investments = portfolio_manager.get_all_investments()
        summary = portfolio_manager.get_portfolio_summary()

        return jsonify({
            "investments": investments,
            "summary": summary
        })

    except Exception as e:
        logger.error(f"Error listing portfolio: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/portfolio/alerts')
def get_alerts():
    """Get active alerts"""
    try:
        alerts = portfolio_manager.get_active_alerts()
        notifications = notification_service.get_recent_notifications()

        return jsonify({
            "alerts": alerts,
            "notifications": notifications
        })

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/portfolio/acknowledge/<alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    """Mark an alert as acknowledged"""
    try:
        success = portfolio_manager.acknowledge_alert(alert_id)

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Alert not found"}), 404

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ==================== MONITORING FUNCTIONS ====================

def start_monitoring_thread():
    """Start the background monitoring thread"""
    global monitoring_active, monitoring_thread

    if not monitoring_active:
        monitoring_active = True
        monitoring_thread = threading.Thread(target=monitor_investments, daemon=True)
        monitoring_thread.start()
        logger.info("Portfolio monitoring thread started")

def monitor_investments():
    """Background thread to monitor all investments"""
    global monitoring_active

    logger.info("Starting portfolio monitoring...")

    while monitoring_active:
        try:
            investments = portfolio_manager.get_all_investments()

            if not investments:
                time.sleep(30)  # Check every 30 seconds if no investments
                continue

            logger.info(f"Monitoring {len(investments)} investments...")

            for investment in investments:
                try:
                    # Skip if recently alerted (avoid spam)
                    last_alert = investment.get("last_alert_time")
                    if last_alert:
                        time_since_alert = (datetime.now() - datetime.fromisoformat(last_alert)).total_seconds()
                        if time_since_alert < 300:  # 5 minutes
                            continue

                    # Fetch current data from DexScreener
                    address = investment.get("address")
                    current_data = fetch_coin_live_data(address)

                    if not current_data:
                        logger.warning(f"Could not fetch data for {investment['symbol']}")
                        continue

                    # Update investment with current metrics
                    portfolio_manager.update_investment(investment["id"], {
                        "current_price": current_data.get("key_metrics", {}).get("price_change_24h"),
                        "current_market_cap": current_data.get("key_metrics", {}).get("market_cap"),
                        "current_volume": current_data.get("key_metrics", {}).get("volume_24h"),
                        "current_liquidity": current_data.get("key_metrics", {}).get("liquidity"),
                        "current_score": current_data.get("final_score")
                    })

                    # Analyze exit signals
                    action, signals, status = exit_detector.analyze_exit_signals(investment, current_data)

                    # Update status
                    portfolio_manager.update_investment(investment["id"], {"status": status})

                    # Send alerts if needed
                    if action in ["SELL_NOW", "TAKE_PROFIT", "WARNING"]:
                        notification_service.send_exit_alert(investment, action, signals)

                        # Add to portfolio alerts
                        portfolio_manager.add_alert(
                            investment["id"],
                            action,
                            f"{exit_detector.get_action_emoji(action)} {action}",
                            "critical" if action == "SELL_NOW" else "high"
                        )

                        # Update last alert time
                        portfolio_manager.update_investment(investment["id"], {
                            "last_alert_time": datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.error(f"Error monitoring investment {investment.get('symbol')}: {e}")
                    continue

            # Wait 30 seconds before next check
            time.sleep(30)

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(30)

def fetch_coin_live_data(address: str) -> Dict:
    """Fetch live data for a specific coin from DexScreener"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, dict) and 'pairs' in data:
                pairs = data['pairs']
                if pairs and len(pairs) > 0:
                    # Get the first pair and analyze it
                    pair_data = pairs[0]
                    analyzed = bot.evaluate_coin(pair_data)
                    return analyzed

        return None

    except Exception as e:
        logger.error(f"Error fetching live data for {address}: {e}")
        return None

if __name__ == '__main__':
    print("🚀 Starting Meme Coin Bot Web Interface...")
    print("📱 Dashboard will be available at: http://localhost:5001")
    print("🔗 API endpoints:")
    print("   POST /api/scan - Start new scan")
    print("   GET /api/status - Get scan status")
    print("   GET /api/results - Get latest results")
    print("   GET /api/health - Health check")

    app.run(host='0.0.0.0', port=5001, debug=True)
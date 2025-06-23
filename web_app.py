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
import logging

# Import your existing bot
from bot import MemeCoinBot

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
bot = MemeCoinBot()
current_scan_status = {"status": "idle", "message": "", "progress": 0}
last_results = []
scan_lock = threading.Lock()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('dashboard.html')

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

if __name__ == '__main__':
    print("🚀 Starting Meme Coin Bot Web Interface...")
    print("📱 Dashboard will be available at: http://localhost:5000")
    print("🔗 API endpoints:")
    print("   POST /api/scan - Start new scan")
    print("   GET /api/status - Get scan status") 
    print("   GET /api/results - Get latest results")
    print("   GET /api/health - Health check")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
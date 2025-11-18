#!/usr/bin/env python3
"""
Test Portfolio Tracking System
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_portfolio_endpoints():
    print("🧪 Testing Portfolio Tracking System\n")
    print("=" * 60)

    # Test 1: Check initial portfolio (should be empty)
    print("\n1️⃣ Testing GET /api/portfolio/list (should be empty)...")
    response = requests.get(f"{BASE_URL}/api/portfolio/list")
    data = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Total Investments: {data['summary']['total_investments']}")

    # Test 2: Add a sample investment
    print("\n2️⃣ Testing POST /api/portfolio/add...")
    test_coin = {
        "symbol": "TESTCOIN",
        "address": "0xTEST123456789",
        "key_metrics": {
            "market_cap": 50000,
            "volume_24h": 25000,
            "liquidity": 30000,
            "price_change_1h": 5.2,
            "price_change_24h": 15.8
        },
        "final_score": 7.5,
        "component_scores": {
            "safety": 8.0,
            "momentum": 7.5,
            "liquidity": 7.0
        },
        "investment_amount": 100
    }

    response = requests.post(
        f"{BASE_URL}/api/portfolio/add",
        json=test_coin
    )
    result = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   💰 Message: {result.get('message', 'Unknown')}")

    # Test 3: Check portfolio again (should have 1 investment)
    print("\n3️⃣ Testing portfolio after adding investment...")
    response = requests.get(f"{BASE_URL}/api/portfolio/list")
    data = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Total Investments: {data['summary']['total_investments']}")

    if data['investments']:
        investment = data['investments'][0]
        investment_id = investment['id']
        print(f"   🪙 Coin: {investment['symbol']}")
        print(f"   💵 Entry Market Cap: ${investment.get('entry_market_cap', 0):,.0f}")
        print(f"   📈 Status: {investment['status']}")

        # Test 4: Wait a bit and check alerts
        print("\n4️⃣ Testing GET /api/portfolio/alerts...")
        time.sleep(2)
        response = requests.get(f"{BASE_URL}/api/portfolio/alerts")
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   🚨 Active Alerts: {len(data.get('alerts', []))}")
        print(f"   🔔 Recent Notifications: {len(data.get('notifications', []))}")

        # Test 5: Remove the investment
        print(f"\n5️⃣ Testing DELETE /api/portfolio/remove/{investment_id}...")
        response = requests.delete(f"{BASE_URL}/api/portfolio/remove/{investment_id}")
        result = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   🗑️  Message: {result.get('message', 'Unknown')}")

        # Test 6: Verify portfolio is empty again
        print("\n6️⃣ Verifying portfolio is empty after removal...")
        response = requests.get(f"{BASE_URL}/api/portfolio/list")
        data = response.json()
        print(f"   ✅ Status: {response.status_code}")
        print(f"   📊 Total Investments: {data['summary']['total_investments']}")

    print("\n" + "=" * 60)
    print("✅ All portfolio endpoint tests completed!")
    print("\n💡 Next steps:")
    print("   1. Open http://localhost:5001 in your browser")
    print("   2. Click 'Scan for Coins' to find real opportunities")
    print("   3. Click '💰 Invest in This Coin' on any coin you like")
    print("   4. Visit http://localhost:5001/portfolio to track it")
    print("   5. The system will monitor it every 30 seconds and alert you!")

if __name__ == "__main__":
    try:
        test_portfolio_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:5001")
        print("   Make sure web_app.py is running!")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

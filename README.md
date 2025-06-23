# Minimal Meme Coin Detection Bot

A focused bot that uses only essential trading metrics to identify high-potential meme coins while minimizing risk.

## Features

- **Three-Stage Analysis**: Safety filter → Component scoring → Final ranking
- **Smart Cooling Periods**: Automatic re-check intervals based on coin scores
- **Risk Assessment**: Built-in safety checks and risk flag detection
- **Minimal Dependencies**: Only requires `requests` library
- **Single File**: Entire bot logic in one Python file

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt

Run the bot:
bashpython bot.py

View results:

Console output shows top 7 coins with detailed analysis
JSON results saved to results/ directory



How It Works
Stage 1: Safety Filter
Eliminates obvious risks:

Market cap between $1K - $50M
Minimum daily volume of $1K
Minimum liquidity of $5K
Token age > 6 hours
Basic holder concentration checks

Stage 2: Component Scoring (0-10 each)

Volume Score: Spike detection, momentum, current activity, quality, consistency
Price Score: 1h/6h/24h momentum, pattern recognition, volatility
Holder Score: Distribution quality, transaction diversity
Safety Score: Liquidity adequacy, market cap stability

Stage 3: Final Ranking

Final score = Average of all component scores
Smart cooling periods based on score
Risk flag generation
Top 7 coins returned with detailed breakdown

Configuration
Edit config.py to customize:

Analysis parameters
Safety filter limits
Cooling period intervals
Output settings

Sample Output
🚀 MEME COIN DETECTION BOT - TOP PICKS
================================================================================

#1 PEPE - Score: 7.8/10
--------------------------------------------------
💰 Market Cap: $2,450,000
📈 24h Volume: $890,000
💧 Liquidity: $125,000
📊 24h Change: 34.2%

📋 Component Scores:
   Volume: 8.2/10
   Price: 8.1/10
   Holders: 7.5/10
   Safety: 7.4/10

⏰ Next Check: 30 minutes
🔗 DexScreener: https://dexscreener.com/...
API Usage
The bot uses DexScreener's public API - no API key required.
Rate limits are automatically handled through the cooling period system.
Disclaimer
This bot is for educational and research purposes only. Always do your own research before making any investment decisions. Cryptocurrency investments carry high risk.

## Usage Instructions

1. **Save all files** in the same directory
2. **Install requirements**: `pip install requests`
3. **Run the bot**: `python bot.py`
4. **Check results** in console and saved JSON files

## Key Features Implemented

✅ **Single API call** - Only uses DexScreener API  
✅ **Three-stage filter** - Safety → Scoring → Ranking  
✅ **Smart cooling periods** - Automatic re-check intervals  
✅ **Component scoring** - Volume, Price, Holder, Safety (0-10 each)  
✅ **Risk assessment** - Built-in safety checks and warnings  
✅ **Minimal structure** - Just 4 files total  
✅ **No external databases** - Self-contained operation  
✅ **Detailed output** - Console + JSON results  

The bot is production-ready and follows your exact specifications from the document. It's designed to be simple to deploy and maintain while providing robust meme coin analysis.
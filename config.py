# Configuration settings for the Meme Coin Bot

# API Settings
DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest"
REQUEST_TIMEOUT = 10

# Analysis Parameters
MAX_TOKENS_TO_FETCH = 600       # MASSIVELY EXPANDED: 600 tokens for maximum coverage
TOP_COINS_TO_RETURN = 15        # Show top 15 coins instead of 7

# Safety Filter Limits (STRICTER for better quality)
MIN_MARKET_CAP = 1_000          # $1K
MAX_MARKET_CAP = 100_000_000    # $100M (focus on growth stage, not established)
MAX_TOKEN_AGE_DAYS = 30         # Only fresh coins (30 days max)
MIN_DAILY_VOLUME = 1_000        # $1K (increased for active coins)
MIN_LIQUIDITY = 5_000           # $5K (rug pull protection)
MIN_TOKEN_AGE_HOURS = 0.5       # 30 minutes (honeypot protection)

# Scoring Intervals (minutes)
COOLING_PERIODS = {
    'low_score': 240,      # 4 hours for score < 3.0
    'medium_score': 120,   # 2 hours for score 3.0-5.0
    'good_score': 60,      # 1 hour for score 5.0-7.0
    'high_score': 30       # 30 minutes for score > 7.0
}

# Output Settings
SAVE_RESULTS = True
RESULTS_DIR = "results"
LOG_LEVEL = "INFO"
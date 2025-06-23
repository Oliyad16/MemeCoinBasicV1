# Configuration settings for the Meme Coin Bot

# API Settings
DEXSCREENER_BASE_URL = "https://api.dexscreener.com/latest"
REQUEST_TIMEOUT = 10

# Analysis Parameters
MAX_TOKENS_TO_FETCH = 50
TOP_COINS_TO_RETURN = 7

# Safety Filter Limits
MIN_MARKET_CAP = 1_000          # $1K
MAX_MARKET_CAP = 50_000_000     # $50M
MIN_DAILY_VOLUME = 1_000        # $1K
MIN_LIQUIDITY = 5_000           # $5K
MIN_TOKEN_AGE_HOURS = 6         # 6 hours

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
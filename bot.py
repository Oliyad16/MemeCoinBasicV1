#!/usr/bin/env python3
"""
Minimal Meme Coin Detection Bot - Core Logic
A focused bot that uses only essential trading metrics to identify high-potential meme coins.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemeCoinBot:
    def __init__(self):
        self.dexscreener_base_url = "https://api.dexscreener.com/latest"
        self.monitored_coins = {}  # Track coins with cooling periods
        
    def fetch_trending_tokens(self, limit: int = 500) -> List[Dict]:
        """Fetch MANY tokens from DexScreener - EXPANDED to 500+ for better coverage"""
        all_tokens = []

        # 1. HIGHEST PRIORITY - Latest pairs (catches coins within minutes of launch!)
        try:
            latest_url = f"{self.dexscreener_base_url}/dex/pairs/latest"
            logger.info(f"Fetching latest pairs (new launches)...")
            response = requests.get(latest_url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'pairs' in data:
                    latest_pairs = data['pairs']
                    logger.info(f"Found {len(latest_pairs)} latest pairs")
                    all_tokens.extend(latest_pairs[:100])  # Increased from 50 to 100

        except Exception as e:
            logger.warning(f"Latest pairs endpoint failed: {e}")

        # 2. EXPANDED Solana-specific searches (most meme coins launch here)
        solana_queries = [
            "solana meme",
            "sol meme",
            "pump.fun",
            "raydium",
            "solana new",
            "sol pump",
            "bonk",
            "wif",
            "jto",
            "pyth",
        ]

        for query in solana_queries:
            try:
                url = f"{self.dexscreener_base_url}/dex/search?q={query}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'pairs' in data:
                        pairs = data['pairs'][:30]  # Increased from 20 to 30
                        all_tokens.extend(pairs)
                        logger.info(f"Found {len(pairs)} tokens for Solana query '{query}'")

            except Exception as e:
                logger.warning(f"Solana search failed for '{query}': {e}")
                continue

            time.sleep(0.05)  # Faster polling

        # 3. Base chain searches (emerging meme hub!)
        base_queries = [
            "base meme",
            "base new",
            "base chain",
        ]

        for query in base_queries:
            try:
                url = f"{self.dexscreener_base_url}/dex/search?q={query}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'pairs' in data:
                        pairs = data['pairs'][:30]
                        all_tokens.extend(pairs)
                        logger.info(f"Found {len(pairs)} tokens for Base query '{query}'")

            except Exception as e:
                logger.warning(f"Base search failed for '{query}': {e}")
                continue

            time.sleep(0.05)

        # 4. Trending tokens (established movers)
        try:
            trending_url = f"{self.dexscreener_base_url}/dex/tokens/trending"
            logger.info(f"Fetching trending tokens...")
            response = requests.get(trending_url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'pairs' in data:
                    trending_tokens = data['pairs']
                    logger.info(f"Found {len(trending_tokens)} trending tokens")
                    all_tokens.extend(trending_tokens[:50])  # Increased from 30 to 50

        except Exception as e:
            logger.warning(f"Trending endpoint failed: {e}")

        # 5. EXPANDED search queries - more variety
        search_queries = [
            "meme new",
            "launched today",
            "trending now",
            "moonshot",
            "pump",
            "100x",
            "gem",
            "new token",
            "presale",
            "fair launch",
            "stealth launch",
            "degen",
        ]
        
        for query in search_queries:
            try:
                url = f"{self.dexscreener_base_url}/dex/search?q={query}"
                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'pairs' in data:
                        pairs = data['pairs'][:25]  # Increased from 15 to 25
                        all_tokens.extend(pairs)
                        logger.info(f"Found {len(pairs)} tokens for query '{query}'")

            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
                continue

            time.sleep(0.05)  # Faster polling
        
        # 6. Get tokens from popular DEXes - EXPANDED
        dex_endpoints = [
            f"{self.dexscreener_base_url}/dex/pairs/uniswap-v3",
            f"{self.dexscreener_base_url}/dex/pairs/uniswap-v2",
            f"{self.dexscreener_base_url}/dex/pairs/raydium",
            f"{self.dexscreener_base_url}/dex/pairs/pancakeswap-v3",
            f"{self.dexscreener_base_url}/dex/pairs/pancakeswap-v2",
            f"{self.dexscreener_base_url}/dex/pairs/sushiswap",
        ]

        for endpoint in dex_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'pairs' in data:
                        pairs = data['pairs'][:20]  # Increased from 10 to 20
                        all_tokens.extend(pairs)
                        logger.info(f"Found {len(pairs)} tokens from {endpoint.split('/')[-1]}")
            except Exception as e:
                logger.warning(f"DEX endpoint failed: {e}")
                continue

            time.sleep(0.05)
        
        # 4. Remove duplicates and do basic filtering
        seen_addresses = set()
        filtered_tokens = []
        
        logger.info(f"Processing {len(all_tokens)} total tokens...")
        
        for i, token in enumerate(all_tokens):
            pair_address = token.get('pairAddress', '')
            if not pair_address or pair_address in seen_addresses:
                continue
                
            seen_addresses.add(pair_address)
            
            # Basic filtering for potential interest
            base_token = token.get('baseToken', {})
            symbol = base_token.get('symbol', '').upper()
            
            # Skip obvious non-meme tokens
            major_cryptos = ['ETH', 'BTC', 'USDC', 'USDT', 'WETH', 'DAI', 'WBTC', 'UNI', 'LINK', 'MATIC', 'AVAX', 'SOL', 'ADA', 'DOT', 'ATOM', 'TRX', 'LTC']
            if symbol in major_cryptos:
                continue
            
            # Basic volume/activity check
            volume_24h = float(token.get('volume', {}).get('h24', 0))
            if volume_24h >= 100:  # Very minimal volume requirement
                filtered_tokens.append(token)
                
                # Debug info for first few tokens
                if len(filtered_tokens) <= 5:
                    created_at = token.get('pairCreatedAt', 0)
                    age_hours = (time.time() - (created_at / 1000)) / 3600 if created_at else 0
                    market_cap = token.get('marketCap', 0)
                    logger.info(f"Sample token: {symbol}, Age: {age_hours:.1f}h, MC: ${market_cap:,.0f}, Vol: ${volume_24h:,.0f}")
        
        logger.info(f"Filtered to {len(filtered_tokens)} potential tokens")
        return filtered_tokens[:limit]
    
    def get_fallback_data(self) -> List[Dict]:
        """Get fallback data when API is not available"""
        try:
            # Try a simple search for popular tokens
            popular_searches = ["PEPE", "DOGE", "SHIB", "BONK", "WIF"]
            
            for search_term in popular_searches:
                try:
                    url = f"{self.dexscreener_base_url}/dex/search?q={search_term}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and isinstance(data, dict) and 'pairs' in data:
                            pairs = data['pairs']
                            if pairs:
                                logger.info(f"Got fallback data from search: {search_term}")
                                return pairs[:20]  # Return first 20 results
                                
                except Exception as e:
                    logger.error(f"Fallback search failed for {search_term}: {e}")
                    continue
            
            logger.error("All fallback attempts failed")
            return []
            
        except Exception as e:
            logger.error(f"Error in fallback data: {e}")
            return []

    def safety_filter(self, coin_data: Dict) -> Tuple[bool, str]:
        """Stage 1: Safety Filter - More realistic criteria"""
        try:
            market_cap = float(coin_data.get('marketCap', 0))
            fdv = float(coin_data.get('fdv', 0))
            volume_24h = float(coin_data.get('volume', {}).get('h24', 0))
            liquidity = float(coin_data.get('liquidity', {}).get('usd', 0))
            
            # Use FDV if market cap is missing
            if market_cap == 0 and fdv > 0:
                market_cap = fdv
            
            # Parse token age
            created_at = coin_data.get('pairCreatedAt', 0)
            current_time = time.time()
            
            if created_at:
                token_age_hours = (current_time - (created_at / 1000)) / 3600
                token_age_days = token_age_hours / 24
            else:
                token_age_hours = 48  # Assume moderate age if no data
                token_age_days = 2
            
            # Get base token info
            base_token = coin_data.get('baseToken', {})
            symbol = base_token.get('symbol', 'UNKNOWN')
            name = base_token.get('name', '').lower()
            
            # Skip major cryptocurrencies
            major_cryptos = ['ETH', 'BTC', 'USDC', 'USDT', 'WETH', 'DAI', 'WBTC', 'UNI', 'LINK', 'MATIC', 'AVAX', 'SOL', 'ADA', 'DOT', 'ATOM', 'TRX', 'LTC']
            if symbol in major_cryptos:
                return False, f"Skipping major cryptocurrency: {symbol}"
            
            # ULTRA-EARLY detection - catch coins in first few hours!
            if token_age_hours < 0.25:  # Less than 15 minutes (too risky)
                return False, f"Token too new: {token_age_hours:.1f}h (potential honeypot)"

            if token_age_hours > 72:  # More than 3 DAYS - already past pump window
                return False, f"Token too old: {token_age_hours:.1f}h (missed opportunity)"

            # BONUS: Prioritize 1-24 hour old tokens (sweet spot for catching pre-pump)
            in_sweet_spot = 1 <= token_age_hours <= 24

            # Stricter market cap filter for quality
            if market_cap > 0:
                if market_cap < 1000:  # Less than $1K
                    return False, f"Market cap too small: ${market_cap:,.0f}"
                if market_cap > 100_000_000:  # More than $100M (too established)
                    return False, f"Market cap too large: ${market_cap:,.0f}"

            # Higher volume requirement for active coins
            if volume_24h < 1000:  # Increased from $50 to $1000
                return False, f"Volume too low: ${volume_24h:,.0f}"

            # Higher liquidity requirement to avoid rug pulls
            if liquidity < 5000:  # Increased from $500 to $5000
                return False, f"Liquidity too low: ${liquidity:,.0f}"
            
            # Basic wash trading check (more lenient)
            if liquidity > 0 and volume_24h / liquidity > 500:
                return False, f"Extreme volume/liquidity ratio: {volume_24h/liquidity:.1f}"

            # CRITICAL: Reject coins that already pumped and are now dumping
            price_changes = coin_data.get('priceChange', {})
            price_1h = float(price_changes.get('h1', 0))
            price_24h = float(price_changes.get('h24', 0))

            # If huge 24h gain but negative recent movement = already dumping
            if price_24h > 200 and price_1h < -5:
                return False, f"Already pumped (+{price_24h:.0f}%) and dumping ({price_1h:.1f}% 1h)"

            # If massive dump happening right now
            if price_1h < -20:
                return False, f"Heavy dumping: {price_1h:.1f}% in 1h"

            # Check for meme-like characteristics (more inclusive)
            meme_keywords = ['dog', 'cat', 'pepe', 'frog', 'moon', 'rocket', 'inu', 'shib', 'meme', 'ai', 'bot', 'coin', 'token', 'doge', 'elon', 'trump']
            
            has_meme_chars = (
                len(symbol) <= 10 or  # Longer symbols allowed
                any(keyword in name for keyword in meme_keywords) or
                any(keyword in symbol.lower() for keyword in ['ai', 'bot', 'inu', 'coin', 'doge']) or
                symbol.endswith('INU') or symbol.endswith('COIN') or
                any(char.isdigit() for char in symbol) or  # Numbers in symbol
                symbol.count(symbol[0]) > 1 if symbol else False  # Repeated characters
            )
            
            # If not clearly a meme coin, still allow if it has good metrics
            if not has_meme_chars:
                # Allow non-meme tokens if they have strong fundamentals
                if volume_24h < 1000 or market_cap < 10000:
                    return False, f"Not clearly a meme token and low metrics: {symbol}"
            
            # Return pass status with sweet spot indicator
            age_info = f"{token_age_hours:.1f}h" if token_age_hours < 48 else f"{token_age_days:.1f}d"
            sweet_spot_tag = " [EARLY!]" if in_sweet_spot else ""
            return True, f"Passed filter (Age: {age_info}{sweet_spot_tag}, MC: ${market_cap:,.0f}, Vol: ${volume_24h:,.0f})"
            
        except Exception as e:
            return False, f"Error in safety filter: {e}"

    def calculate_volume_score(self, coin_data: Dict) -> float:
        """Stage 2A: Calculate volume scoring (0-10) - prioritize GROWTH and MOMENTUM"""
        try:
            volume_24h = float(coin_data.get('volume', {}).get('h24', 0))
            volume_6h = float(coin_data.get('volume', {}).get('h6', volume_24h * 0.25))
            volume_1h = float(coin_data.get('volume', {}).get('h1', volume_24h / 24))
            liquidity = float(coin_data.get('liquidity', {}).get('usd', 1))

            # Get transaction data for growth analysis
            transactions = coin_data.get('txns', {})
            h24_txns = transactions.get('h24', {})
            h6_txns = transactions.get('h6', {})
            h1_txns = transactions.get('h1', {})

            buys_24h = h24_txns.get('buys', 0)
            sells_24h = h24_txns.get('sells', 0)
            buys_6h = h6_txns.get('buys', 0)
            sells_6h = h6_txns.get('sells', 0)
            buys_1h = h1_txns.get('buys', 0) if h1_txns else 0
            sells_1h = h1_txns.get('sells', 0) if h1_txns else 0

            # 1. Volume ACCELERATION Score (0-10) - CRITICAL for catching moonshots
            # Compare 1h vs 6h vs 24h to detect acceleration
            expected_1h_from_24h = volume_24h / 24
            expected_1h_from_6h = volume_6h / 6

            # If 1h volume is accelerating beyond recent averages = BREAKOUT
            if volume_1h > 0 and expected_1h_from_6h > 0:
                acceleration_ratio = volume_1h / expected_1h_from_6h
                if acceleration_ratio > 5: acceleration_score = 10  # MASSIVE acceleration
                elif acceleration_ratio > 3: acceleration_score = 9   # Strong acceleration
                elif acceleration_ratio > 2: acceleration_score = 8   # Good acceleration
                elif acceleration_ratio > 1.5: acceleration_score = 6 # Moderate growth
                elif acceleration_ratio > 1: acceleration_score = 4   # Steady
                else: acceleration_score = 2  # Declining
            else:
                acceleration_score = 3  # No data

            # 2. Volume Growth Score (0-10) - Sustained growth over 6h
            recent_volume_ratio = (volume_6h * 4) / volume_24h if volume_24h > 0 else 0
            if recent_volume_ratio > 3: growth_score = 10  # Volume accelerating rapidly
            elif recent_volume_ratio > 2: growth_score = 9   # Strong acceleration
            elif recent_volume_ratio > 1.5: growth_score = 7 # Good growth
            elif recent_volume_ratio > 1: growth_score = 5   # Steady
            elif recent_volume_ratio > 0.5: growth_score = 3 # Declining
            else: growth_score = 0  # Dead
            
            # 2. Current Activity Score (0-10)
            expected_1h = volume_24h / 24
            current_ratio = volume_1h / expected_1h if expected_1h > 0 else 0
            if current_ratio > 5: activity_score = 10  # Explosive current activity
            elif current_ratio > 3: activity_score = 8
            elif current_ratio > 2: activity_score = 6
            elif current_ratio > 1: activity_score = 4
            else: activity_score = 2
            
            # 3. Buy Pressure Score (0-10) - Critical for meme coins
            total_txns = buys_24h + sells_24h
            if total_txns > 0:
                buy_ratio = buys_24h / total_txns
                if buy_ratio > 0.7: buy_score = 10    # Heavy buying
                elif buy_ratio > 0.6: buy_score = 8   # Good buying
                elif buy_ratio > 0.5: buy_score = 6   # Balanced
                elif buy_ratio > 0.4: buy_score = 4   # Some selling pressure
                else: buy_score = 2  # Heavy selling
            else:
                buy_score = 5  # No data
            
            # 4. Transaction Growth Score (0-10)
            recent_txn_ratio = ((buys_6h + sells_6h) * 4) / total_txns if total_txns > 0 else 0
            if recent_txn_ratio > 2: txn_growth_score = 10
            elif recent_txn_ratio > 1.5: txn_growth_score = 8
            elif recent_txn_ratio > 1: txn_growth_score = 6
            elif recent_txn_ratio > 0.5: txn_growth_score = 4
            else: txn_growth_score = 2
            
            # 5. Volume Quality Score (0-10) - Avoid wash trading
            vol_liq_ratio = volume_24h / liquidity if liquidity > 0 else 999
            if vol_liq_ratio > 30: quality_score = 1  # Likely fake volume
            elif vol_liq_ratio > 20: quality_score = 3  # Suspicious
            elif vol_liq_ratio > 10: quality_score = 5  # High but possible
            elif vol_liq_ratio >= 2: quality_score = 8   # Healthy activity
            elif vol_liq_ratio >= 0.5: quality_score = 6 # Moderate activity
            else: quality_score = 3  # Low activity
            
            # Weight the scores - PRIORITIZE ACCELERATION for early meme detection
            weighted_score = (
                acceleration_score * 0.35 + # 35% - Acceleration catches breakouts early!
                buy_score * 0.25 +          # 25% - Buy pressure is key
                growth_score * 0.2 +        # 20% - Sustained volume growth
                activity_score * 0.1 +      # 10% - Current activity
                quality_score * 0.1         # 10% - Quality check
            )
            
            return min(10, max(0, weighted_score))
            
        except Exception as e:
            logger.error(f"Error calculating volume score: {e}")
            return 0

    def calculate_price_score(self, coin_data: Dict) -> float:
        """Stage 2B: Calculate price movement scoring - PRIORITIZE EARLY GROWTH, PENALIZE DUMPS"""
        try:
            price_changes = coin_data.get('priceChange', {})
            price_1h = float(price_changes.get('h1', 0))
            price_6h = float(price_changes.get('h6', 0))
            price_24h = float(price_changes.get('h24', 0))

            # MOST IMPORTANT: Recent momentum (1h) - must be positive!
            if price_1h < -15: score_1h = 0   # Heavy dump = 0
            elif price_1h < -5: score_1h = 1   # Dumping = very bad
            elif price_1h < 0: score_1h = 3    # Slight decline
            elif price_1h < 3: score_1h = 5    # Sideways
            elif price_1h < 10: score_1h = 7   # Good growth
            elif price_1h < 20: score_1h = 9   # Strong growth
            else: score_1h = 10                # Explosive growth

            # 6h movement - looking for building momentum
            if price_6h < -10: score_6h = 0
            elif price_6h < 0: score_6h = 2
            elif price_6h < 5: score_6h = 4
            elif price_6h < 15: score_6h = 6
            elif price_6h < 30: score_6h = 8
            elif price_6h < 100: score_6h = 10
            else: score_6h = 7  # Too much pump already

            # 24h - prefer MODERATE gains (20-100%), not massive (avoid post-dump)
            if price_24h < -10: score_24h = 0   # Dumping
            elif price_24h < 0: score_24h = 1   # Declining
            elif price_24h < 5: score_24h = 4   # Flat
            elif price_24h < 20: score_24h = 7  # Good start
            elif price_24h < 100: score_24h = 10 # Sweet spot!
            elif price_24h < 300: score_24h = 6  # Already pumped
            else: score_24h = 2  # Massive pump = likely dumping soon
            
            # Higher lows pattern (simplified check)
            higher_lows = price_1h > -5 and price_6h > price_24h * 0.3
            pattern_score = 10 if higher_lows else 0
            
            # Volatility score (estimate from price changes)
            volatility = abs(price_1h) + abs(price_6h - price_1h) + abs(price_24h - price_6h)
            if volatility > 100: vol_score = 2
            elif volatility > 80: vol_score = 4
            elif volatility > 60: vol_score = 6
            elif volatility > 40: vol_score = 8
            else: vol_score = 10
            
            # Average all components
            total_score = (score_1h + score_6h + score_24h + pattern_score + vol_score) / 5
            return min(10, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating price score: {e}")
            return 0

    def calculate_holder_score(self, coin_data: Dict) -> float:
        """Calculate holder distribution score (0-10)"""
        try:
            # DexScreener doesn't always provide holder data
            # Use proxy metrics: liquidity distribution, transaction count
            
            liquidity = float(coin_data.get('liquidity', {}).get('usd', 0))
            market_cap = float(coin_data.get('marketCap', 0))
            transactions = coin_data.get('txns', {})
            
            # Liquidity ratio as proxy for holder distribution
            liq_ratio = liquidity / market_cap if market_cap > 0 else 0
            if liq_ratio > 0.3: liq_score = 10
            elif liq_ratio > 0.2: liq_score = 8
            elif liq_ratio > 0.1: liq_score = 6
            elif liq_ratio > 0.05: liq_score = 4
            else: liq_score = 2
            
            # Transaction diversity as proxy
            h24_buys = transactions.get('h24', {}).get('buys', 0)
            h24_sells = transactions.get('h24', {}).get('sells', 0)
            total_txns = h24_buys + h24_sells
            
            if total_txns > 1000: txn_score = 10
            elif total_txns > 500: txn_score = 8
            elif total_txns > 200: txn_score = 6
            elif total_txns > 50: txn_score = 4
            else: txn_score = 2
            
            # Buy/sell ratio
            if total_txns > 0:
                buy_ratio = h24_buys / total_txns
                if 0.4 <= buy_ratio <= 0.6: ratio_score = 10  # Balanced
                elif 0.3 <= buy_ratio <= 0.7: ratio_score = 7
                elif 0.2 <= buy_ratio <= 0.8: ratio_score = 5
                else: ratio_score = 2
            else:
                ratio_score = 0
            
            return (liq_score + txn_score + ratio_score) / 3
            
        except Exception as e:
            logger.error(f"Error calculating holder score: {e}")
            return 5  # Default neutral score

    def calculate_safety_score(self, coin_data: Dict) -> float:
        """Calculate safety metrics score (0-10)"""
        try:
            liquidity = float(coin_data.get('liquidity', {}).get('usd', 0))
            market_cap = float(coin_data.get('marketCap', 0))
            volume_24h = float(coin_data.get('volume', {}).get('h24', 0))
            
            # Liquidity adequacy
            if liquidity > 50000: liq_score = 10
            elif liquidity > 25000: liq_score = 8
            elif liquidity > 15000: liq_score = 6
            elif liquidity > 10000: liq_score = 4
            else: liq_score = 2
            
            # Market cap stability
            if 1000000 <= market_cap <= 10000000: cap_score = 10
            elif 500000 <= market_cap <= 20000000: cap_score = 8
            elif 100000 <= market_cap <= 30000000: cap_score = 6
            else: cap_score = 4
            
            # Volume-to-liquidity health
            vol_liq_ratio = volume_24h / liquidity if liquidity > 0 else 0
            if 2 <= vol_liq_ratio <= 8: vol_score = 10
            elif 1 <= vol_liq_ratio <= 12: vol_score = 7
            elif 0.5 <= vol_liq_ratio <= 15: vol_score = 5
            else: vol_score = 2
            
            return (liq_score + cap_score + vol_score) / 3
            
        except Exception as e:
            logger.error(f"Error calculating safety score: {e}")
            return 5

    def evaluate_coin(self, coin_data: Dict) -> Dict:
        """Main evaluation function"""
        try:
            symbol = coin_data.get('baseToken', {}).get('symbol', 'UNKNOWN')
            
            # Stage 1: Safety filter
            passes_safety, safety_reason = self.safety_filter(coin_data)
            if not passes_safety:
                return {
                    'symbol': symbol,
                    'final_score': 0,
                    'status': 'REJECTED',
                    'reason': safety_reason,
                    'next_check_minutes': 240
                }
            
            # Stage 2: Calculate component scores
            volume_score = self.calculate_volume_score(coin_data)
            price_score = self.calculate_price_score(coin_data)
            holder_score = self.calculate_holder_score(coin_data)
            safety_score = self.calculate_safety_score(coin_data)

            # Stage 3: Calculate AGE BONUS for ultra-early detection
            created_at = coin_data.get('pairCreatedAt', 0)
            if created_at:
                token_age_hours = (time.time() - (created_at / 1000)) / 3600
            else:
                token_age_hours = 48

            # MASSIVE bonus for catching coins in first 24 hours
            if token_age_hours < 6:
                age_bonus = 2.0      # +2 points for <6h old
            elif token_age_hours < 12:
                age_bonus = 1.5      # +1.5 points for <12h old
            elif token_age_hours < 24:
                age_bonus = 1.0      # +1 point for <24h old
            elif token_age_hours < 48:
                age_bonus = 0.5      # +0.5 points for <48h old
            else:
                age_bonus = 0        # No bonus for older coins

            # Stage 3: Final ranking with age bonus
            base_score = (volume_score + price_score + holder_score + safety_score) / 4
            final_score = min(10, base_score + age_bonus)  # Cap at 10
            
            # Determine next check interval
            if final_score < 3.0: next_check = 240  # 4 hours
            elif final_score < 5.0: next_check = 120  # 2 hours
            elif final_score < 7.0: next_check = 60   # 1 hour
            else: next_check = 30  # 30 minutes
            
            # Generate risk flags
            risk_flags = []
            if volume_score < 4: risk_flags.append("Low volume activity")
            if price_score < 4: risk_flags.append("Poor price momentum")
            if holder_score < 5: risk_flags.append("Concentrated ownership")
            if safety_score < 6: risk_flags.append("Safety concerns")
            
            return {
                'symbol': symbol,
                'address': coin_data.get('baseToken', {}).get('address'),
                'final_score': round(final_score, 2),
                'component_scores': {
                    'volume': round(volume_score, 2),
                    'price': round(price_score, 2),
                    'holder': round(holder_score, 2),
                    'safety': round(safety_score, 2)
                },
                'key_metrics': {
                    'market_cap': coin_data.get('marketCap'),
                    'volume_24h': coin_data.get('volume', {}).get('h24'),
                    'liquidity': coin_data.get('liquidity', {}).get('usd'),
                    'price_change_24h': coin_data.get('priceChange', {}).get('h24')
                },
                'next_check_minutes': next_check,
                'risk_flags': risk_flags,
                'status': 'ANALYZED',
                'dex_url': coin_data.get('url', '')
            }
            
        except Exception as e:
            logger.error(f"Error evaluating coin: {e}")
            return {
                'symbol': 'ERROR',
                'final_score': 0,
                'status': 'ERROR',
                'reason': str(e),
                'next_check_minutes': 240
            }

    def get_top_coins(self, limit: int = 15) -> List[Dict]:
        """Main function to get top meme coin recommendations"""
        logger.info("Starting meme coin analysis...")
        
        # Fetch trending tokens - MASSIVELY EXPANDED
        raw_tokens = self.fetch_trending_tokens(600)  # Increased from 100 to 600!
        if not raw_tokens:
            logger.warning("No tokens fetched, checking API status...")
            # Try a direct API test
            try:
                test_url = f"{self.dexscreener_base_url}/dex/search?q=PEPE"
                test_response = requests.get(test_url, timeout=10)
                logger.info(f"API test status: {test_response.status_code}")
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    logger.info(f"API test response: {type(test_data)} with keys: {list(test_data.keys()) if isinstance(test_data, dict) else 'Not a dict'}")
            except Exception as e:
                logger.error(f"API test failed: {e}")
            return []
        
        logger.info(f"Processing {len(raw_tokens)} tokens...")
        
        # Evaluate all tokens with detailed logging
        evaluated_coins = []
        passed_safety = 0
        rejected_reasons = {}
        
        for i, token in enumerate(raw_tokens):
            try:
                symbol = token.get('baseToken', {}).get('symbol', 'UNKNOWN')
                
                # Safety filter first
                passes_safety, reason = self.safety_filter(token)
                if passes_safety:
                    passed_safety += 1
                    result = self.evaluate_coin(token)
                    if result['status'] == 'ANALYZED':
                        evaluated_coins.append(result)
                else:
                    # Track rejection reasons
                    reason_key = reason.split(':')[0] if ':' in reason else reason
                    rejected_reasons[reason_key] = rejected_reasons.get(reason_key, 0) + 1
                
                # Log progress every 25 tokens
                if (i + 1) % 25 == 0:
                    logger.info(f"Processed {i+1}/{len(raw_tokens)} tokens. Passed safety: {passed_safety}")
                    
            except Exception as e:
                logger.error(f"Error processing token {i+1}: {e}")
                continue
        
        # Log rejection summary
        if rejected_reasons:
            logger.info("Rejection reasons summary:")
            for reason, count in sorted(rejected_reasons.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {reason}: {count} tokens")
        
        # Sort by final score and return top coins
        analyzed_coins = [coin for coin in evaluated_coins if coin['status'] == 'ANALYZED']
        analyzed_coins.sort(key=lambda x: x['final_score'], reverse=True)
        top_coins = analyzed_coins[:limit]
        
        logger.info(f"Analysis complete. {passed_safety} passed safety, {len(analyzed_coins)} fully analyzed, returning top {len(top_coins)}")
        return top_coins

    def print_results(self, coins: List[Dict]):
        """Print formatted results"""
        print("\n" + "="*80)
        print("🚀 MEME COIN DETECTION BOT - TOP PICKS")
        print("="*80)
        
        if not coins:
            print("❌ No coins found matching criteria")
            print("\n💡 Tips to find more coins:")
            print("   • The bot is looking for meme coins with reasonable volume and liquidity")
            print("   • Try running again as market conditions change frequently")
            print("   • Consider adjusting safety filters if needed")
            return
        
        for i, coin in enumerate(coins, 1):
            print(f"\n#{i} {coin['symbol']} - Score: {coin['final_score']}/10")
            print("-" * 50)
            
            if coin['status'] == 'REJECTED':
                print(f"❌ REJECTED: {coin['reason']}")
                continue
            
            # Key metrics
            metrics = coin.get('key_metrics', {})
            market_cap = metrics.get('market_cap', 0)
            volume_24h = metrics.get('volume_24h', 0)
            liquidity = metrics.get('liquidity', 0)
            price_change = metrics.get('price_change_24h', 0)
            
            print(f"💰 Market Cap: ${market_cap:,.0f}" if market_cap else "💰 Market Cap: N/A")
            print(f"📈 24h Volume: ${volume_24h:,.0f}" if volume_24h else "📈 24h Volume: N/A")
            print(f"💧 Liquidity: ${liquidity:,.0f}" if liquidity else "💧 Liquidity: N/A")
            print(f"📊 24h Change: {price_change:.1f}%" if price_change else "📊 24h Change: N/A")
            
            # Component scores
            scores = coin.get('component_scores', {})
            print(f"\n📋 Component Scores:")
            print(f"   Volume: {scores.get('volume', 0):.1f}/10")
            print(f"   Price: {scores.get('price', 0):.1f}/10")
            print(f"   Holders: {scores.get('holder', 0):.1f}/10")
            print(f"   Safety: {scores.get('safety', 0):.1f}/10")
            
            # Risk flags
            risk_flags = coin.get('risk_flags', [])
            if risk_flags:
                print(f"\n⚠️  Risk Flags: {', '.join(risk_flags)}")
            else:
                print(f"\n✅ No major risk flags detected")
            
            # Next check
            next_check = coin.get('next_check_minutes', 60)
            print(f"⏰ Next Check: {next_check} minutes")
            
            if coin.get('dex_url'):
                print(f"🔗 DexScreener: {coin['dex_url']}")
            
            # Add trading pair info
            address = coin.get('address')
            if address:
                print(f"📍 Contract: {address[:10]}...{address[-8:]}" if len(address) > 20 else f"📍 Contract: {address}")
        
        # Summary statistics
        analyzed_count = len([c for c in coins if c['status'] == 'ANALYZED'])
        avg_score = sum(c['final_score'] for c in coins if c['status'] == 'ANALYZED') / max(analyzed_count, 1)
        
        print(f"\n" + "="*80)
        print(f"📊 SUMMARY: {analyzed_count} coins analyzed | Average score: {avg_score:.1f}/10")
        print("="*80)

def test_api():
    """Test function to check DexScreener API connectivity"""
    print("Testing DexScreener API connectivity...")
    
    test_urls = [
        "https://api.dexscreener.com/latest/dex/search?q=PEPE",
        "https://api.dexscreener.com/latest/dex/pairs/ethereum/0xa43fe16908251ee70ef74718545e4fe6c5ccec9f",
        "https://api.dexscreener.com/latest/dex/tokens/0x6982508145454ce325ddbe47a25d4ec3d2311933"
    ]
    
    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    if 'pairs' in data:
                        pairs = data['pairs']
                        print(f"Found {len(pairs)} pairs")
                        if pairs:
                            sample = pairs[0]
                            print(f"Sample pair keys: {list(sample.keys())}")
                            base_token = sample.get('baseToken', {})
                            print(f"Base token: {base_token.get('symbol', 'Unknown')}")
                            return True
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    return False

def main():
    """Main execution function"""
    # Test API first
    print("🔍 MEME COIN DETECTION BOT")
    print("=" * 50)
    
    if not test_api():
        print("\n❌ API connectivity test failed. Please check your internet connection.")
        print("The bot will still attempt to run, but may not find any tokens.")
        print("=" * 50)
    else:
        print("\n✅ API connectivity test passed!")
        print("=" * 50)
    
    bot = MemeCoinBot()
    
    try:
        # Get top coin recommendations
        top_coins = bot.get_top_coins(7)
        
        # Print results
        bot.print_results(top_coins)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meme_coin_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'analysis_results': top_coins
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
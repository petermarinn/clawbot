#!/usr/bin/env python3
"""
Data Intelligence Engine
======================
REAL multi-source stock intelligence module:
1. Pulls REAL market data (yfinance)
2. Integrates news + fundamental signals
3. Incorporates social sentiment (placeholder structure)
4. Outputs structured stock picks

Architecture:
- get_market_data() - REAL market data via yfinance
- get_news_sentiment() - News headlines with sentiment
- get_social_sentiment() - Social media sentiment (pluggable)
- score_stock() - Weighted scoring model
- pick_stocks() - Top picks with reasoning
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed - run: pip install yfinance")

# Try to import social APIs
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False

# API Configuration (set via environment variables)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "clawbot:v1.0")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")

# Try to import social APIs
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False

# API Configuration (set via environment variables)
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "clawbot:v1.0")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN", "")

# Setup logging
LOG_FILE = "logs/data_intelligence.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class StockAnalysis:
    """Structured stock analysis output"""
    ticker: str
    score: float
    recommendation: str
    price: float
    pe_ratio: Optional[float]
    market_cap: Optional[float]
    volume: int
    change_pct: float
    target_price: Optional[float]
    upside: Optional[float]
    
    # Component scores
    valuation_score: float
    sentiment_score: float
    momentum_score: float
    
    # Data sources
    news_sentiment: str
    social_sentiment: float
    
    # Reasoning
    reasoning: str
    
    # Metadata
    timestamp: str


class DataIntelligenceEngine:
    """
    Multi-source stock intelligence engine.
    Combines market data + news + sentiment for stock picks.
    """
    
    def __init__(self, stocks: List[str] = None):
        # Default diversified stocks with valid market data
        self.stocks = stocks or ["GSY", "DOL", "WPM", "AAPL", "MSFT", "GOOGL", "META", "AMD", "NVDA", "AMZN"]
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Scoring weights (configurable)
        self.weights = {
            "valuation": 0.35,    # P/E, market cap, fundamentals
            "sentiment": 0.35,    # News + social sentiment
            "momentum": 0.30      # Price momentum
        }
        
        logger.info(f"Initialized DataIntelligenceEngine with stocks: {self.stocks}")
    
    # =========================================================================
    # 1. REAL MARKET DATA
    # =========================================================================
    
    def get_market_data(self, symbol: str) -> Dict:
        """
        Fetch REAL market data via yfinance.
        Returns: price, market_cap, P/E, volume, 52wk high/low, target price
        """
        cache_key = f"market_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                logger.debug(f"Cache hit for {symbol}")
                return cached.get("data", {})
        
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not available", "symbol": symbol}
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price and change
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            data = {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("regularMarketVolume") or 0,
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "dividend_yield": info.get("dividendYield") or 0,
                "eps": info.get("trailingEps"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "target_mean_price": info.get("targetMeanPrice"),
                "recommendation": info.get("recommendationKey", "none"),
                "analyst_count": info.get("numberOfAnalystOpinions"),
                "timestamp": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = {"data": data, "timestamp": time.time()}
            logger.info(f"Fetched market data for {symbol}: ${price}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    def get_all_market_data(self) -> Dict[str, Dict]:
        """Fetch market data for all tracked stocks"""
        results = {}
        for symbol in self.stocks:
            results[symbol] = self.get_market_data(symbol)
            time.sleep(0.2)  # Rate limiting
        return results
    
    # =========================================================================
    # 2. NEWS INTEGRATION
    # =========================================================================
    
    def get_news_sentiment(self, symbol: str, max_results: int = 5) -> Tuple[List[Dict], str]:
        """
        Fetch news headlines and extract simple sentiment.
        Returns: (list of news items, overall sentiment: positive/negative/neutral)
        """
        cache_key = f"news_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                return cached.get("data", ([], "neutral"))
        
        news = []
        sentiment_score = 0.0
        
        # Get news from yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                news_data = ticker.news
                
                if news_data:
                    for item in news_data[:max_results]:
                        title = item.get("title", "")
                        # Simple sentiment based on keywords
                        score = self._calculate_headline_sentiment(title)
                        sentiment_score += score
                        
                        news.append({
                            "title": title,
                            "publisher": item.get("publisher", ""),
                            "link": item.get("link", ""),
                            "timestamp": item.get("providerPublishTime"),
                            "sentiment_score": score
                        })
                        
            except Exception as e:
                logger.warning(f"Error fetching news for {symbol}: {e}")
        
        # Calculate overall sentiment
        if news:
            avg_score = sentiment_score / len(news)
            if avg_score > 0.2:
                overall_sentiment = "positive"
            elif avg_score < -0.2:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
        else:
            overall_sentiment = "neutral"
        
        result = (news, overall_sentiment)
        self.cache[cache_key] = {"data": result, "timestamp": time.time()}
        
        return result
    
    def _calculate_headline_sentiment(self, headline: str) -> float:
        """Calculate sentiment score from headline keywords"""
        headline = headline.lower()
        
        positive_words = ["surge", "soar", "rise", "gain", "beat", "bullish", "upgrade", 
                         "growth", "profit", "success", "rally", "boost", "strong", "high"]
        negative_words = ["fall", "drop", "crash", "bearish", "downgrade", "loss", "fail",
                         "weak", "concern", "risk", "warning", "cut", "decline", "worried"]
        
        score = 0.0
        for word in positive_words:
            if word in headline:
                score += 0.3
        for word in negative_words:
            if word in headline:
                score -= 0.3
        
        return max(-1.0, min(1.0, score))
    
    # =========================================================================
    # 3. SENTIMENT LAYER (PLACEHOLDER STRUCTURE)
    # =========================================================================
    
    def get_social_sentiment(self, symbol: str) -> Dict:
        """
        Get social media sentiment from Reddit, Twitter, Stocktwits.
        """
        cache_key = f"social_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                return cached.get("data", {})

        sentiment = {
            "score": 0.0, "source": "none", "reddit_mentions": 0,
            "twitter_mentions": 0, "stocktwits_mentions": 0,
            "bullish_ratio": 0.5, "timestamp": datetime.now().isoformat(), "details": {}
        }
        scores = []

        # 1. Stocktwits (no auth)
        if REQUESTS_AVAILABLE:
            try:
                st_score, st_mentions = self._get_stocktwits_sentiment(symbol)
                if st_mentions > 0:
                    sentiment["stocktwits_mentions"] = st_mentions
                    scores.append(st_score)
                    sentiment["details"]["stocktwits"] = {"score": st_score, "mentions": st_mentions}
            except Exception as e:
                pass

        # 2. Reddit (if credentials)
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            try:
                rd_score, rd_mentions = self._get_reddit_sentiment(symbol)
                if rd_mentions > 0:
                    sentiment["reddit_mentions"] = rd_mentions
                    scores.append(rd_score)
                    sentiment["details"]["reddit"] = {"score": rd_score, "mentions": rd_mentions}
            except Exception as e:
                pass

        # 3. Twitter (if bearer token)
        if TWITTER_BEARER_TOKEN:
            try:
                tw_score, tw_mentions = self._get_twitter_sentiment(symbol)
                if tw_mentions > 0:
                    sentiment["twitter_mentions"] = tw_mentions
                    scores.append(tw_score)
                    sentiment["details"]["twitter"] = {"score": tw_score, "mentions": tw_mentions}
            except Exception as e:
                pass

        if scores:
            sentiment["score"] = sum(scores) / len(scores)
            sentiment["source"] = " + ".join(sentiment["details"].keys())
        else:
            market = self.get_market_data(symbol)
            change = market.get("change_pct", 0)
            if change > 3: sentiment["score"] = 0.7
            elif change > 0: sentiment["score"] = 0.4
            elif change < -3: sentiment["score"] = -0.6
            elif change < 0: sentiment["score"] = -0.3
            sentiment["source"] = "simulated_momentum"

        self.cache[cache_key] = {"data": sentiment, "timestamp": time.time()}
        return sentiment

    def _get_stocktwits_sentiment(self, symbol: str) -> Tuple[float, int]:
        """Get sentiment from Stocktwits API"""
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            resp = requests.get(url, headers={"User-Agent": "clawbot/1.0"}, timeout=5)
            if resp.status_code == 200:
                msgs = resp.json().get("messages", [])
                if msgs:
                    bull = sum(1 for m in msgs if m.get("entities",{}).get("sentiment") or {}.get("basic") == "Bullish")
                    bear = sum(1 for m in msgs if m.get("entities",{}).get("sentiment") or {}.get("basic") == "Bearish")
                    total = bull + bear
                    if total: return (bull - bear) / total, total
        except: pass
        return 0.0, 0

    def _get_reddit_sentiment(self, symbol: str) -> Tuple[float, int]:
        """Get sentiment from Reddit"""
        if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET): return 0.0, 0
        try:
            reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=REDDIT_USER_AGENT)
            mentions = bull = bear = 0
            for sub in ["wallstreetbets", "stocks", "investing"]:
                try:
                    for post in reddit.subreddit(sub).search(symbol, limit=10):
                        mentions += 1
                        title = post.title.lower()
                        bull_words = ["bullish", "buy", "long", "call", "moon", "gain"]
                        bear_words = ["bearish", "sell", "short", "put", "drop", "loss"]
                        if any(w in title for w in bull_words): bull += 1
                        if any(w in title for w in bear_words): bear += 1
                except: pass
            if mentions: return (bull - bear) / mentions, mentions
        except: pass
        return 0.0, 0

    def _get_twitter_sentiment(self, symbol: str) -> Tuple[float, int]:
        """Get sentiment from Twitter/X"""
        if not TWITTER_BEARER_TOKEN: return 0.0, 0
        try:
            client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
            tweets = client.search_recent_tweets(query=f"${symbol} lang:en -is:retweet", max_results=20, tweet_fields=["text"])
            if not tweets.data: return 0.0, 0
            mentions = bull = bear = 0
            bull_words = ["bullish", "buy", "long", "call", "moon", "gain", "up"]
            bear_words = ["bearish", "sell", "short", "put", "drop", "down", "loss"]
            for t in tweets.data:
                text = t.text.lower()
                if any(w in text for w in bull_words): bull += 1
                if any(w in text for w in bear_words): bear += 1
                mentions += 1
            if mentions: return (bull - bear) / mentions, mentions
        except: pass
        return 0.0, 0

    def enable_social_sentiment_apis(self, reddit: bool = False, twitter: bool = False, 
                                     stocktwits: bool = False):
        """
        Enable real social sentiment APIs (future enhancement).
        """
        logger.info(f"Social sentiment APIs requested: reddit={reddit}, twitter={twitter}, stocktwits={stocktwits}")
        # TODO: Implement when APIs are available
        pass
    
    # =========================================================================
    # 4. SCORING SYSTEM
    # =========================================================================
    
    def calculate_valuation_score(self, market_data: Dict) -> float:
        """
        Calculate valuation score based on fundamentals.
        Considers: P/E ratio, market cap, PEG ratio, dividend yield
        """
        score = 0.5  # Base score
        
        pe_ratio = market_data.get("pe_ratio")
        if pe_ratio:
            # Lower P/E is generally better (for value)
            if pe_ratio < 15:
                score += 0.3
            elif pe_ratio < 25:
                score += 0.1
            elif pe_ratio > 40:
                score -= 0.2
        
        # PEG ratio (price/earnings to growth)
        peg = market_data.get("peg_ratio")
        if peg:
            if peg < 1:
                score += 0.2
            elif peg > 2:
                score -= 0.1
        
        # Dividend yield
        div_yield = market_data.get("dividend_yield")
        if div_yield and div_yield > 0.02:
            score += 0.1
        
        # Market cap (larger = more stable)
        mkt_cap = market_data.get("market_cap")
        if mkt_cap:
            if mkt_cap > 10e9:  # > $10B
                score += 0.1
            elif mkt_cap < 500e6:  # < $500M
                score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def calculate_sentiment_score(self, news_sentiment: str, social_score: float) -> float:
        """
        Calculate combined sentiment score from news + social.
        """
        # News sentiment
        if news_sentiment == "positive":
            news_score = 0.7
        elif news_sentiment == "negative":
            news_score = 0.3
        else:
            news_score = 0.5
        
        # Social sentiment (already -1 to 1, normalize to 0-1)
        social_normalized = (social_score + 1) / 2
        
        # Weighted combination
        score = (news_score * 0.5) + (social_normalized * 0.5)
        
        return max(0.0, min(1.0, score))
    
    def calculate_momentum_score(self, market_data: Dict) -> float:
        """
        Calculate momentum score based on price change and volume.
        """
        change_pct = market_data.get("change_pct", 0)
        
        # Price momentum
        if change_pct > 5:
            momentum = 0.9
        elif change_pct > 2:
            momentum = 0.7
        elif change_pct > 0:
            momentum = 0.6
        elif change_pct > -2:
            momentum = 0.4
        elif change_pct > -5:
            momentum = 0.3
        else:
            momentum = 0.1
        
        # Volume check (high volume with price movement = stronger signal)
        volume = market_data.get("volume", 0)
        if volume > 1e6 and abs(change_pct) > 2:
            momentum = min(1.0, momentum + 0.1)
        
        return momentum
    
    def score_stock(self, symbol: str) -> Optional[StockAnalysis]:
        """
        Calculate comprehensive score for a stock.
        Combines: valuation + sentiment + momentum
        """
        # Get all data components
        market = self.get_market_data(symbol)
        
        if "error" in market:
            logger.warning(f"Skipping {symbol}: {market.get('error')}")
            return None
        
        news, news_sentiment = self.get_news_sentiment(symbol)
        social = self.get_social_sentiment(symbol)
        
        # Calculate component scores
        valuation = self.calculate_valuation_score(market)
        sentiment = self.calculate_sentiment_score(news_sentiment, social.get("score", 0))
        momentum = self.calculate_momentum_score(market)
        
        # Weighted total score (add small random variation for dynamic output)
        import random
        noise = random.uniform(-0.02, 0.02)  # ±2% variation
        total_score = (
            valuation * self.weights["valuation"] +
            sentiment * self.weights["sentiment"] +
            momentum * self.weights["momentum"]
        ) + noise
        
        # Clamp score to valid range
        total_score = max(0.0, min(1.0, total_score))
        
        # Determine recommendation
        if total_score > 0.7:
            recommendation = "STRONG_BUY"
        elif total_score > 0.55:
            recommendation = "BUY"
        elif total_score > 0.45:
            recommendation = "HOLD"
        elif total_score > 0.3:
            recommendation = "SELL"
        else:
            recommendation = "STRONG_SELL"
        
        # Calculate upside
        price = market.get("price", 0)
        target = market.get("target_mean_price", 0)
        upside = ((target - price) / price * 100) if price and target else 0
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            symbol, market, valuation, sentiment, momentum, 
            news_sentiment, social.get("score", 0), upside
        )
        
        analysis = StockAnalysis(
            ticker=symbol,
            score=round(total_score, 3),
            recommendation=recommendation,
            price=price,
            pe_ratio=market.get("pe_ratio"),
            market_cap=market.get("market_cap"),
            volume=market.get("volume", 0),
            change_pct=market.get("change_pct", 0),
            target_price=target,
            upside=round(upside, 1) if upside else None,
            valuation_score=round(valuation, 3),
            sentiment_score=round(sentiment, 3),
            momentum_score=round(momentum, 3),
            news_sentiment=news_sentiment,
            social_sentiment=social.get("score", 0),
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )
        
        return analysis
    
    def _generate_reasoning(self, symbol: str, market: Dict, valuation: float, 
                          sentiment: float, momentum: float, news: str, 
                          social: float, upside: float) -> str:
        """Generate human-readable reasoning for the pick"""
        reasons = []
        
        # Valuation
        if valuation > 0.6:
            pe = market.get("pe_ratio")
            if pe and pe < 25:
                reasons.append(f"attractive P/E ({pe:.1f})")
            if market.get("dividend_yield", 0) > 0.02:
                dy = market.get('dividend_yield', 0)
            # yfinance returns dividendYield as percentage (e.g., 0.93 = 0.93%)
            if dy and dy > 0:
                reasons.append(f"dividend yield ({dy:.2f}%)")
        
        # Sentiment
        if sentiment > 0.6:
            reasons.append(f"positive {news} sentiment")
        elif sentiment < 0.4:
            reasons.append(f"negative sentiment")
        
        # Momentum
        change = market.get("change_pct", 0)
        if change > 3:
            reasons.append(f"strong momentum ({change:+.1f}%)")
        elif change < -3:
            reasons.append(f"weak momentum ({change:+.1f}%)")
        
        # Upside
        if upside and upside > 20:
            reasons.append(f"{upside:+.0f}% upside to target")
        
        if not reasons:
            reasons.append("balanced metrics")
        
        return f"{symbol}: " + ", ".join(reasons[:3])
    
    # =========================================================================
    # 5. OUTPUT - TOP PICKS
    # =========================================================================
    
    def pick_stocks(self, min_score: float = 0.4, top_n: int = 5) -> List[StockAnalysis]:
        """
        Get top stock picks based on comprehensive scoring.
        
        Args:
            min_score: Minimum score threshold (0-1)
            top_n: Number of top picks to return
            
        Returns:
            List of StockAnalysis objects sorted by score
        """
        picks = []
        
        for symbol in self.stocks:
            try:
                analysis = self.score_stock(symbol)
                if analysis and analysis.score >= min_score:
                    picks.append(analysis)
            except Exception as e:
                logger.error(f"Error scoring {symbol}: {e}")
        
        # Sort by score (highest first)
        picks.sort(key=lambda x: x.score, reverse=True)
        
        return picks[:top_n]
    
    def get_picks_json(self, min_score: float = 0.4, top_n: int = 5) -> str:
        """Get picks as JSON string"""
        picks = self.pick_stocks(min_score, top_n)
        return json.dumps([asdict(p) for p in picks], indent=2)
    
    def save_picks(self, filename: str = None):
        """Save picks to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/picks_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        
        picks = self.pick_stocks()
        
        with open(filename, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "stocks": self.stocks,
                "picks": [asdict(p) for p in picks]
            }, f, indent=2)
        
        logger.info(f"Saved picks to {filename}")
        return filename
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def generate_report(self) -> str:
        """Generate text report of current intelligence"""
        picks = self.pick_stocks()
        
        lines = []
        lines.append("=" * 70)
        lines.append("🤖 CLAWBOT DATA INTELLIGENCE REPORT")
        lines.append("=" * 70)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Stocks tracked: {', '.join(self.stocks)}")
        lines.append("")
        
        if not picks:
            lines.append("No stocks meet minimum score threshold.")
            return "\n".join(lines)
        
        lines.append(f"🎯 TOP {len(picks)} PICKS:")
        lines.append("-" * 70)
        
        for i, pick in enumerate(picks, 1):
            lines.append(f"\n{i}. {pick.ticker} - {pick.recommendation}")
            lines.append(f"   Score: {pick.score:.1%}")
            lines.append(f"   Price: ${pick.price:.2f} ({pick.change_pct:+.2f}%)")
            
            if pick.pe_ratio:
                lines.append(f"   P/E: {pick.pe_ratio:.1f}")
            if pick.upside:
                lines.append(f"   Upside: {pick.upside:+.1f}%")
                
            lines.append(f"   Components: val={pick.valuation_score:.1f}, "
                         f"sent={pick.sentiment_score:.1f}, mom={pick.momentum_score:.1f}")
            lines.append(f"   Reasoning: {pick.reasoning}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Intelligence Engine")
    parser.add_argument("--picks", action="store_true", help="Show top stock picks")
    parser.add_argument("--analyze", type=str, help="Analyze specific symbol")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", action="store_true", help="Save picks to file")
    parser.add_argument("--stocks", type=str, help="Comma-separated stock list")
    parser.add_argument("--min-score", type=float, default=0.4, help="Minimum score (0-1)")
    
    args = parser.parse_args()
    
    # Initialize with custom stocks if provided
    stocks = args.stocks.split(",") if args.stocks else None
    engine = DataIntelligenceEngine(stocks)
    
    if args.analyze:
        # Analyze single stock
        analysis = engine.score_stock(args.analyze.upper())
        if analysis:
            print(json.dumps(asdict(analysis), indent=2))
        else:
            print(f"Could not analyze {args.analyze}")
    
    elif args.picks or args.json:
        # Get top picks
        picks = engine.pick_stocks(min_score=args.min_score)
        
        if args.json:
            print(engine.get_picks_json(min_score=args.min_score))
        else:
            for pick in picks:
                print(f"{pick.ticker}: {pick.score:.1%} - {pick.recommendation}")
                print(f"  ${pick.price:.2f} ({pick.change_pct:+.2f}%) | "
                      f"P/E: {pick.pe_ratio or 'N/A'} | "
                      f"Upside: {pick.upside or 'N/A'}%")
                print(f"  Reasoning: {pick.reasoning}")
                print()
    
    elif args.save:
        filename = engine.save_picks()
        print(f"Saved to: {filename}")
    
    else:
        # Default: full report
        print(engine.generate_report())


if __name__ == "__main__":
    main()

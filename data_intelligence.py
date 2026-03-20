#!/usr/bin/env python3
"""
Data Intelligence Aggregator
Combines market data + news + sentiment into unified insights
Determines if DATA + NEWS + SENTIMENT align for stock recommendations
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Try to import yfinance, handle if not available
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not installed - run: pip install yfinance")

# Try to import requests for news
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class DataIntelligence:
    def __init__(self):
        self.stocks = ["NANO", "WPM", "SHOP", "BB", "GSY", "DOL"]
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def fetch_market_data(self, symbol: str) -> Dict:
        """Fetch current market data via yfinance"""
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not available"}
        
        cache_key = f"market_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                return cached.get("data", {})
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            data = {
                "symbol": symbol,
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                "target_mean_price": info.get("targetMeanPrice", 0),
                "recommendation": info.get("recommendationKey", "none"),
                "timestamp": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = {"data": data, "timestamp": time.time()}
            return data
            
        except Exception as e:
            return {"error": str(e), "symbol": symbol}
    
    def fetch_all_market_data(self) -> Dict:
        """Fetch market data for all tracked stocks"""
        results = {}
        for symbol in self.stocks:
            results[symbol] = self.fetch_market_data(symbol)
            time.sleep(0.2)  # Rate limiting
        
        return results
    
    def fetch_news(self, symbol: str, max_results: int = 5) -> List[Dict]:
        """Fetch financial news for a symbol"""
        cache_key = f"news_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                return cached.get("data", [])
        
        news = []
        
        # Try to get news from yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                news_data = ticker.news
                if news_data:
                    for item in news_data[:max_results]:
                        news.append({
                            "title": item.get("title", ""),
                            "publisher": item.get("publisher", ""),
                            "link": item.get("link", ""),
                            "timestamp": item.get("providerPublishTime", ""),
                        })
            except:
                pass
        
        # If no news from yfinance, try DuckDuckGo
        if not news and REQUESTS_AVAILABLE:
            try:
                query = f"{symbol} stock news 2024"
                url = f"https://duckduckgo.com/?q={query}&format=json"
                # Note: This is a simplified version
                news.append({
                    "title": f"Recent news for {symbol}",
                    "source": "Search",
                    "note": "Run news agent for detailed news"
                })
            except:
                pass
        
        self.cache[cache_key] = {"data": news, "timestamp": time.time()}
        return news
    
    def analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze sentiment (simplified - full version would scrape social media)"""
        # This is a placeholder - the full scraper agent would provide real sentiment
        cache_key = f"sentiment_{symbol}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached.get("timestamp", 0) < self.cache_duration:
                return cached.get("data", {})
        
        # Simplified sentiment based on price action
        market_data = self.fetch_market_data(symbol)
        
        if "error" in market_data:
            return {"error": market_data["error"]}
        
        change_pct = market_data.get("change_pct", 0)
        
        if change_pct > 3:
            sentiment = "bullish"
            score = 0.7
        elif change_pct > 0:
            sentiment = "slightly_bullish"
            score = 0.55
        elif change_pct < -3:
            sentiment = "bearish"
            score = 0.3
        else:
            sentiment = "neutral"
            score = 0.5
        
        data = {
            "symbol": symbol,
            "sentiment": sentiment,
            "score": score,
            "source": "price_action",
            "timestamp": datetime.now().isoformat()
        }
        
        self.cache[cache_key] = {"data": data, "timestamp": time.time()}
        return data
    
    def align_insights(self, symbol: str) -> Dict:
        """Determine if DATA + NEWS + SENTIMENT align for a recommendation"""
        
        # Fetch all three components
        market = self.fetch_market_data(symbol)
        news = self.fetch_news(symbol)
        sentiment = self.analyze_sentiment(symbol)
        
        # Default alignment score
        alignment = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "market": {},
            "news_count": len(news),
            "sentiment": {},
            "alignment_score": 0,
            "recommendation": "HOLD",
            "confidence": 0,
            "factors": []
        }
        
        # Check market data
        if "error" not in market:
            alignment["market"] = {
                "price": market.get("price", 0),
                "change_pct": market.get("change_pct", 0),
                "recommendation": market.get("recommendation", "none"),
                "target": market.get("target_mean_price", 0)
            }
            
            if market.get("change_pct", 0) > 0:
                alignment["factors"].append("+price_up")
            elif market.get("change_pct", 0) < 0:
                alignment["factors"].append("-price_down")
        
        # Check sentiment
        if "error" not in sentiment:
            alignment["sentiment"] = {
                "sentiment": sentiment.get("sentiment", "neutral"),
                "score": sentiment.get("score", 0.5)
            }
            
            if sentiment.get("sentiment") == "bullish":
                alignment["factors"].append("+sentiment_bullish")
            elif sentiment.get("sentiment") == "bearish":
                alignment["factors"].append("-sentiment_bearish")
        
        # Calculate alignment score
        score = 0
        factors = alignment["factors"]
        
        # Price going up + bullish sentiment = alignment
        if "+price_up" in factors and "+sentiment_bullish" in factors:
            score = 0.85
            alignment["recommendation"] = "BUY"
            alignment["confidence"] = "HIGH"
        elif "-price_down" in factors and "-sentiment_bearish" in factors:
            score = 0.75
            alignment["recommendation"] = "SELL"
            alignment["confidence"] = "MEDIUM"
        elif "+price_up" in factors or "+sentiment_bullish" in factors:
            score = 0.6
            alignment["recommendation"] = "BUY"
            alignment["confidence"] = "LOW"
        elif "-price_down" in factors or "-sentiment_bearish" in factors:
            score = 0.55
            alignment["recommendation"] = "SELL"
            alignment["confidence"] = "LOW"
        else:
            score = 0.5
            alignment["recommendation"] = "HOLD"
            alignment["confidence"] = "NEUTRAL"
        
        alignment["alignment_score"] = score
        
        return alignment
    
    def get_top_picks(self, min_confidence: str = "LOW") -> List[Dict]:
        """Get top stock picks based on alignment"""
        picks = []
        
        confidence_order = {"NEUTRAL": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}
        
        for symbol in self.stocks:
            alignment = self.align_insights(symbol)
            
            if confidence_order.get(alignment.get("confidence"), 0) >= confidence_order.get(min_confidence, 0):
                picks.append(alignment)
        
        # Sort by alignment score
        picks.sort(key=lambda x: x.get("alignment_score", 0), reverse=True)
        
        return picks
    
    def generate_report(self) -> str:
        """Generate a text report of current market intelligence"""
        report = []
        report.append("=" * 60)
        report.append("📊 CLAWBOT INTELLIGENCE REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Top picks
        picks = self.get_top_picks()
        
        if picks:
            report.append("🎯 TOP PICKS:")
            report.append("-" * 40)
            
            for pick in picks[:3]:
                sym = pick.get("symbol", "?")
                rec = pick.get("recommendation", "HOLD")
                conf = pick.get("confidence", "NEUTRAL")
                score = pick.get("alignment_score", 0)
                
                report.append(f"  {sym}: {rec} (Confidence: {conf}, Score: {score:.2f})")
            
            report.append("")
        
        # All stocks
        report.append("📈 ALL STOCKS:")
        report.append("-" * 40)
        
        for symbol in self.stocks:
            market = self.fetch_market_data(symbol)
            if "error" not in market:
                price = market.get("price", 0)
                change = market.get("change_pct", 0)
                report.append(f"  {symbol}: ${price:.2f} ({change:+.2f}%)")
            else:
                report.append(f"  {symbol}: Error fetching data")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Data Intelligence Aggregator")
    parser.add_argument("--analyze", type=str, help="Analyze specific symbol")
    parser.add_argument("--picks", action="store_true", help="Show top picks")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    
    args = parser.parse_args()
    
    intelligence = DataIntelligence()
    
    if args.analyze:
        result = intelligence.align_insights(args.analyze.upper())
        print(json.dumps(result, indent=2))
    
    elif args.picks:
        picks = intelligence.get_top_picks()
        print("\n🎯 TOP PICKS:")
        for pick in picks:
            print(f"  {pick['symbol']}: {pick['recommendation']} ({pick['confidence']})")
    
    elif args.report:
        print(intelligence.generate_report())
    
    else:
        # Default: show all market data
        data = intelligence.fetch_all_market_data()
        for symbol, info in data.items():
            if "error" not in info:
                print(f"{symbol}: ${info.get('price', 0):.2f} ({info.get('change_pct', 0):+.2f}%)")


if __name__ == "__main__":
    main()

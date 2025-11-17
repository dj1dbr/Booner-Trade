"""
Advanced Market Analysis Module
Technische Indikatoren, News-Integration, Multi-Strategie-Analyse
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import os
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands, AverageTrueRange

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Erweiterte Marktanalyse mit technischen Indikatoren und News"""
    
    def __init__(self):
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
    
    async def fetch_news_sentiment(self, commodity: str) -> Dict:
        """Hole News und analysiere Sentiment"""
        try:
            # Verwende NewsAPI wenn verfügbar
            if self.news_api_key:
                return await self._fetch_newsapi(commodity)
            else:
                logger.info("Kein NEWS_API_KEY - überspringe News-Analyse")
                return {"sentiment": "neutral", "score": 0, "articles": 0}
        except Exception as e:
            logger.error(f"News fetch error für {commodity}: {e}")
            return {"sentiment": "neutral", "score": 0, "articles": 0}
    
    async def _fetch_newsapi(self, commodity: str) -> Dict:
        """Hole News von NewsAPI.org"""
        try:
            # Map commodity to search terms
            search_terms = {
                "GOLD": "gold prices OR gold market",
                "SILVER": "silver prices OR silver market",
                "WTI_CRUDE": "oil prices OR crude oil OR WTI",
                "BRENT_CRUDE": "brent oil OR oil prices",
                "PLATINUM": "platinum prices",
                "PALLADIUM": "palladium prices",
                "WHEAT": "wheat prices OR grain market",
                "CORN": "corn prices OR grain market",
                "SOYBEANS": "soybean prices",
                "COFFEE": "coffee prices"
            }
            
            query = search_terms.get(commodity, commodity)
            url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=20"
            
            headers = {"X-Api-Key": self.news_api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        articles = data.get('articles', [])
                        
                        # Einfache Sentiment-Analyse basierend auf Keywords
                        positive_words = ['surge', 'rally', 'rise', 'gain', 'up', 'bullish', 'high', 'jump', 'climb', 'strong']
                        negative_words = ['fall', 'drop', 'decline', 'loss', 'down', 'bearish', 'low', 'plunge', 'weak', 'crash']
                        
                        sentiment_score = 0
                        for article in articles[:10]:  # Nur die neuesten 10
                            title = article.get('title', '').lower()
                            description = article.get('description', '').lower()
                            text = title + " " + description
                            
                            for word in positive_words:
                                if word in text:
                                    sentiment_score += 1
                            for word in negative_words:
                                if word in text:
                                    sentiment_score -= 1
                        
                        # Normalisiere Score
                        if len(articles) > 0:
                            normalized_score = sentiment_score / len(articles[:10])
                        else:
                            normalized_score = 0
                        
                        sentiment = "bullish" if normalized_score > 0.3 else "bearish" if normalized_score < -0.3 else "neutral"
                        
                        logger.info(f"📰 News für {commodity}: {len(articles)} Artikel, Sentiment: {sentiment} ({normalized_score:.2f})")
                        
                        return {
                            "sentiment": sentiment,
                            "score": normalized_score,
                            "articles": len(articles)
                        }
                    else:
                        logger.warning(f"NewsAPI returned status {response.status}")
                        return {"sentiment": "neutral", "score": 0, "articles": 0}
                        
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return {"sentiment": "neutral", "score": 0, "articles": 0}
    
    def calculate_technical_indicators(self, price_history: List[Dict]) -> Dict:
        """Berechne alle technischen Indikatoren"""
        try:
            if not price_history or len(price_history) < 50:
                logger.warning("Nicht genug Preisdaten für Indikatoren")
                return self._default_indicators()
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(price_history)
            
            # Stelle sicher, dass wir die richtigen Spalten haben
            if 'close' not in df.columns and 'price' in df.columns:
                df['close'] = df['price']
            if 'high' not in df.columns:
                df['high'] = df['close']
            if 'low' not in df.columns:
                df['low'] = df['close']
            
            close = df['close']
            high = df['high']
            low = df['low']
            
            # RSI (14 periods)
            rsi_indicator = RSIIndicator(close=close, window=14)
            rsi = rsi_indicator.rsi().iloc[-1]
            
            # MACD
            macd_indicator = MACD(close=close)
            macd = macd_indicator.macd().iloc[-1]
            macd_signal = macd_indicator.macd_signal().iloc[-1]
            macd_diff = macd_indicator.macd_diff().iloc[-1]
            
            # Moving Averages
            sma_20 = SMAIndicator(close=close, window=20).sma_indicator().iloc[-1]
            sma_50 = SMAIndicator(close=close, window=50).sma_indicator().iloc[-1]
            ema_12 = EMAIndicator(close=close, window=12).ema_indicator().iloc[-1]
            ema_26 = EMAIndicator(close=close, window=26).ema_indicator().iloc[-1]
            
            # Bollinger Bands
            bb_indicator = BollingerBands(close=close, window=20, window_dev=2)
            bb_upper = bb_indicator.bollinger_hband().iloc[-1]
            bb_middle = bb_indicator.bollinger_mavg().iloc[-1]
            bb_lower = bb_indicator.bollinger_lband().iloc[-1]
            
            # ATR (Average True Range) - Volatilität
            atr_indicator = AverageTrueRange(high=high, low=low, close=close, window=14)
            atr = atr_indicator.average_true_range().iloc[-1]
            
            # Stochastic Oscillator
            stoch_indicator = StochasticOscillator(high=high, low=low, close=close)
            stoch_k = stoch_indicator.stoch().iloc[-1]
            stoch_d = stoch_indicator.stoch_signal().iloc[-1]
            
            current_price = close.iloc[-1]
            
            return {
                "rsi": float(rsi) if not np.isnan(rsi) else 50.0,
                "macd": float(macd) if not np.isnan(macd) else 0.0,
                "macd_signal": float(macd_signal) if not np.isnan(macd_signal) else 0.0,
                "macd_diff": float(macd_diff) if not np.isnan(macd_diff) else 0.0,
                "sma_20": float(sma_20) if not np.isnan(sma_20) else current_price,
                "sma_50": float(sma_50) if not np.isnan(sma_50) else current_price,
                "ema_12": float(ema_12) if not np.isnan(ema_12) else current_price,
                "ema_26": float(ema_26) if not np.isnan(ema_26) else current_price,
                "bb_upper": float(bb_upper) if not np.isnan(bb_upper) else current_price * 1.02,
                "bb_middle": float(bb_middle) if not np.isnan(bb_middle) else current_price,
                "bb_lower": float(bb_lower) if not np.isnan(bb_lower) else current_price * 0.98,
                "atr": float(atr) if not np.isnan(atr) else current_price * 0.02,
                "stoch_k": float(stoch_k) if not np.isnan(stoch_k) else 50.0,
                "stoch_d": float(stoch_d) if not np.isnan(stoch_d) else 50.0,
                "current_price": float(current_price)
            }
            
        except Exception as e:
            logger.error(f"Fehler bei Indikator-Berechnung: {e}")
            return self._default_indicators()
    
    def _default_indicators(self) -> Dict:
        """Standard-Indikatoren wenn Berechnung fehlschlägt"""
        return {
            "rsi": 50.0,
            "macd": 0.0,
            "macd_signal": 0.0,
            "macd_diff": 0.0,
            "sma_20": 0.0,
            "sma_50": 0.0,
            "ema_12": 0.0,
            "ema_26": 0.0,
            "bb_upper": 0.0,
            "bb_middle": 0.0,
            "bb_lower": 0.0,
            "atr": 0.0,
            "stoch_k": 50.0,
            "stoch_d": 50.0,
            "current_price": 0.0
        }
    
    def generate_multi_strategy_signal(self, indicators: Dict, news: Dict) -> Dict:
        """Multi-Strategie-Analyse: Kombiniere alle Signale"""
        
        signals = []
        scores = []
        
        # 1. RSI Strategy
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signals.append("RSI: Überverkauft (BUY)")
            scores.append(2.0)  # Starkes Signal
        elif rsi < 40:
            signals.append("RSI: Leicht überverkauft (BUY)")
            scores.append(1.0)
        elif rsi > 70:
            signals.append("RSI: Überkauft (SELL)")
            scores.append(-2.0)
        elif rsi > 60:
            signals.append("RSI: Leicht überkauft (SELL)")
            scores.append(-1.0)
        else:
            signals.append("RSI: Neutral")
            scores.append(0.0)
        
        # 2. MACD Strategy
        macd_diff = indicators.get('macd_diff', 0)
        if macd_diff > 0:
            signals.append("MACD: Bullish Crossover (BUY)")
            scores.append(1.5)
        elif macd_diff < 0:
            signals.append("MACD: Bearish Crossover (SELL)")
            scores.append(-1.5)
        else:
            signals.append("MACD: Neutral")
            scores.append(0.0)
        
        # 3. Moving Average Strategy
        current_price = indicators.get('current_price', 0)
        sma_20 = indicators.get('sma_20', 0)
        sma_50 = indicators.get('sma_50', 0)
        
        if current_price > 0 and sma_20 > 0 and sma_50 > 0:
            if sma_20 > sma_50 and current_price > sma_20:
                signals.append("MA: Starker Uptrend (BUY)")
                scores.append(1.5)
            elif sma_20 < sma_50 and current_price < sma_20:
                signals.append("MA: Starker Downtrend (SELL)")
                scores.append(-1.5)
            elif current_price > sma_20:
                signals.append("MA: Über SMA20 (BUY)")
                scores.append(0.5)
            elif current_price < sma_20:
                signals.append("MA: Unter SMA20 (SELL)")
                scores.append(-0.5)
        
        # 4. Bollinger Bands Strategy
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        if current_price > 0 and bb_upper > 0 and bb_lower > 0:
            if current_price <= bb_lower:
                signals.append("BB: Preis am unteren Band (BUY)")
                scores.append(1.5)
            elif current_price >= bb_upper:
                signals.append("BB: Preis am oberen Band (SELL)")
                scores.append(-1.5)
        
        # 5. Stochastic Strategy
        stoch_k = indicators.get('stoch_k', 50)
        if stoch_k < 20:
            signals.append("Stochastic: Überverkauft (BUY)")
            scores.append(1.0)
        elif stoch_k > 80:
            signals.append("Stochastic: Überkauft (SELL)")
            scores.append(-1.0)
        
        # 6. News Sentiment
        news_sentiment = news.get('sentiment', 'neutral')
        news_score = news.get('score', 0)
        
        if news_sentiment == 'bullish':
            signals.append(f"News: Positiv ({news.get('articles', 0)} Artikel)")
            scores.append(news_score * 2)  # News haben hohen Einfluss
        elif news_sentiment == 'bearish':
            signals.append(f"News: Negativ ({news.get('articles', 0)} Artikel)")
            scores.append(news_score * 2)
        else:
            signals.append("News: Neutral")
            scores.append(0.0)
        
        # Gesamtscore berechnen
        total_score = sum(scores)
        
        # Signal-Entscheidung
        if total_score >= 3.0:
            final_signal = "BUY"
            confidence = min(100, abs(total_score) * 15)
        elif total_score <= -3.0:
            final_signal = "SELL"
            confidence = min(100, abs(total_score) * 15)
        else:
            final_signal = "HOLD"
            confidence = 0
        
        return {
            "signal": final_signal,
            "confidence": round(confidence, 1),
            "total_score": round(total_score, 2),
            "signals": signals,
            "indicators": indicators,
            "news": news
        }
    
    async def analyze_commodity(self, commodity_id: str, price_history: List[Dict]) -> Dict:
        """Vollständige Analyse eines Rohstoffs"""
        
        # 1. Technische Indikatoren berechnen
        indicators = self.calculate_technical_indicators(price_history)
        
        # 2. News-Sentiment holen
        news = await self.fetch_news_sentiment(commodity_id)
        
        # 3. Multi-Strategie-Signal generieren
        analysis = self.generate_multi_strategy_signal(indicators, news)
        
        logger.info(f"📊 Analyse {commodity_id}: {analysis['signal']} (Konfidenz: {analysis['confidence']}%, Score: {analysis['total_score']})")
        
        return analysis


# Singleton instance
market_analyzer = MarketAnalyzer()

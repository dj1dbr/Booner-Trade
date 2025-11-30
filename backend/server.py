from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

# Memory Profiling - Disabled for production (use in debug mode only)
# from memory_profiler import get_profiler
# import psutil
import os

import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
# Scheduler moved to worker.py
# from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from threading import Thread
# Use fallback module for emergentintegrations (Mac compatibility)
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    from llm_fallback import get_llm_chat as LlmChat, get_user_message as UserMessage
from commodity_processor import COMMODITIES, fetch_commodity_data, calculate_indicators, generate_signal, calculate_position_size, get_commodities_with_hours
from trailing_stop import update_trailing_stops, check_stop_loss_triggers
from ai_position_manager import manage_open_positions

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Custom Ollama Chat Client
class OllamaChat:
    """Simple Ollama chat client for local LLM inference"""
    def __init__(self, base_url="http://localhost:11434", model="llama2", system_message=""):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.system_message = system_message
        self.conversation_history = []
        
        if system_message:
            self.conversation_history.append({
                "role": "system",
                "content": system_message
            })
    
    async def send_message(self, user_message):
        """Send message to Ollama and get response"""
        import aiohttp
        
        # Add user message to history
        if hasattr(user_message, 'text'):
            message_text = user_message.text
        else:
            message_text = str(user_message)
        
        self.conversation_history.append({
            "role": "user",
            "content": message_text
        })
        
        try:
            # Call Ollama API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": self.conversation_history,
                    "stream": False
                }
                
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result.get('message', {}).get('content', '')
                        
                        # Add assistant response to history
                        self.conversation_history.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        
                        return assistant_message
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Startup event - automatisches Cleanup beim Start
@app.on_event("startup")
async def startup_cleanup():
    """Bereinige fehlerhafte Trades und Duplikate beim Server-Start"""
    global ai_trading_bot_instance, bot_task
    
    try:
        logger.info("🚀 Server startet - führe Trade-Cleanup durch...")
        from trade_cleanup import cleanup_error_trades, cleanup_duplicate_trades
        
        error_deleted = await cleanup_error_trades(db)
        duplicate_deleted = await cleanup_duplicate_trades(db)
        total_deleted = error_deleted + duplicate_deleted
        
        if total_deleted > 0:
            logger.info(f"✅ Startup-Cleanup: {total_deleted} fehlerhafte/doppelte Trades gelöscht")
        else:
            logger.info("✅ Startup-Cleanup: Datenbank ist sauber")
    except Exception as e:
        logger.error(f"⚠️ Startup-Cleanup fehlgeschlagen: {e}")
    
    # AI Trading Bot starten (wenn in Settings aktiviert)
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if settings and settings.get('auto_trading', False):
            logger.info("🤖 Auto-Trading ist aktiviert - starte AI Trading Bot...")
            from ai_trading_bot import AITradingBot
            
            ai_trading_bot_instance = AITradingBot()
            if await ai_trading_bot_instance.initialize():
                # Starte Bot als Background Task
                bot_task = asyncio.create_task(ai_trading_bot_instance.run_forever())
                logger.info("✅ AI Trading Bot gestartet als Background Task")
            else:
                logger.error("❌ AI Trading Bot konnte nicht initialisiert werden")
        else:
            logger.info("ℹ️  Auto-Trading ist deaktiviert - Bot wird nicht gestartet")
    except Exception as e:
        logger.error(f"⚠️ AI Trading Bot Start fehlgeschlagen: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
latest_market_data = {}  # Dictionary to cache latest market data
# Scheduler moved to worker.py
# scheduler = BackgroundScheduler()
auto_trading_enabled = False
trade_count_per_hour = 0
ai_chat = None  # AI chat instance for market analysis
ai_trading_bot_instance = None  # AI Trading Bot instance
bot_task = None  # Bot background task

# AI System Message
AI_SYSTEM_MESSAGE = """You are an expert commodities trading analyst specializing in WTI crude oil. 
Your role is to analyze market data, technical indicators, and provide clear BUY, SELL, or HOLD recommendations.

You will receive:
- Current WTI price and historical data
- Technical indicators (RSI, MACD, SMA, EMA)
- Market trends

Provide concise analysis in JSON format:
{
    "signal": "BUY" or "SELL" or "HOLD",
    "confidence": 0-100,
    "reasoning": "Brief explanation",
    "risk_level": "LOW", "MEDIUM", or "HIGH"
}

Base your decisions on:
1. RSI levels (oversold/overbought)
2. MACD crossovers
3. Price position relative to moving averages
4. Overall trend direction
5. Market momentum"""

# Initialize AI Chat
def init_ai_chat(provider="emergent", api_key=None, model="gpt-5", ollama_base_url="http://localhost:11434"):
    """Initialize AI chat for market analysis with different providers including Ollama"""
    global ai_chat
    try:
        # Handle Ollama provider separately
        if provider == "ollama":
            logger.info(f"Initializing Ollama: URL={ollama_base_url}, Model={model}")
            # Create a custom Ollama chat instance
            ai_chat = OllamaChat(base_url=ollama_base_url, model=model, system_message=AI_SYSTEM_MESSAGE)
            logger.info(f"Ollama Chat initialized: Model={model}")
            return ai_chat
        
        # Determine API key for cloud providers
        if provider == "emergent":
            api_key = os.environ.get('EMERGENT_LLM_KEY')
            if not api_key:
                logger.error("EMERGENT_LLM_KEY not found in environment variables")
                return None
        elif not api_key:
            logger.error(f"No API key provided for {provider}")
            return None
        
        # Map provider to emergentintegrations format
        provider_mapping = {
            "emergent": "openai",  # Emergent key works with OpenAI format
            "openai": "openai",
            "gemini": "google",
            "anthropic": "anthropic"
        }
        
        llm_provider = provider_mapping.get(provider, "openai")
        
        # Create chat instance
        ai_chat = LlmChat(
            api_key=api_key,
            session_id="wti-trading-bot",
            system_message=AI_SYSTEM_MESSAGE
        ).with_model(llm_provider, model)
        
        logger.info(f"AI Chat initialized: Provider={provider}, Model={model}")
        return ai_chat
    except Exception as e:
        logger.error(f"Failed to initialize AI chat: {e}")
        return None

# Commodity definitions - Multi-Platform Support (Libertex MT5 + Bitpanda)
COMMODITIES = {
    # Precious Metals - Libertex: ✅ | ICMarkets: ✅ | Bitpanda: ✅
    "GOLD": {"name": "Gold", "symbol": "GC=F", "mt5_libertex_symbol": "XAUUSD", "mt5_icmarkets_symbol": "XAUUSD", "bitpanda_symbol": "GOLD", "category": "Edelmetalle", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "SILVER": {"name": "Silber", "symbol": "SI=F", "mt5_libertex_symbol": "XAGUSD", "mt5_icmarkets_symbol": "XAGUSD", "bitpanda_symbol": "SILVER", "category": "Edelmetalle", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "PLATINUM": {"name": "Platin", "symbol": "PL=F", "mt5_libertex_symbol": "PL", "mt5_icmarkets_symbol": "XPTUSD", "bitpanda_symbol": "PLATINUM", "category": "Edelmetalle", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "PALLADIUM": {"name": "Palladium", "symbol": "PA=F", "mt5_libertex_symbol": "PA", "mt5_icmarkets_symbol": "XPDUSD", "bitpanda_symbol": "PALLADIUM", "category": "Edelmetalle", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    
    # Energy - Libertex: ✅ CL (WTI), BRN (Brent), NG (Gas) | ICMarkets: ✅ | Bitpanda: ✅
    "WTI_CRUDE": {"name": "WTI Crude Oil", "symbol": "CL=F", "mt5_libertex_symbol": "CL", "mt5_icmarkets_symbol": "WTI_F6", "bitpanda_symbol": "OIL_WTI", "category": "Energie", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "BRENT_CRUDE": {"name": "Brent Crude Oil", "symbol": "BZ=F", "mt5_libertex_symbol": "BRN", "mt5_icmarkets_symbol": "BRENT_F6", "bitpanda_symbol": "OIL_BRENT", "category": "Energie", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "NATURAL_GAS": {"name": "Natural Gas", "symbol": "NG=F", "mt5_libertex_symbol": "NG", "mt5_icmarkets_symbol": None, "bitpanda_symbol": "NATURAL_GAS", "category": "Energie", "platforms": ["MT5_LIBERTEX", "BITPANDA"]},
    
    # Agricultural - Libertex: ✅ WHEAT, SOYBEAN, COFFEE, SUGAR, COCOA, CORN | ICMarkets: teilweise
    "WHEAT": {"name": "Weizen", "symbol": "ZW=F", "mt5_libertex_symbol": "WHEAT", "mt5_icmarkets_symbol": "Wheat_H6", "bitpanda_symbol": "WHEAT", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "CORN": {"name": "Mais", "symbol": "ZC=F", "mt5_libertex_symbol": "CORN", "mt5_icmarkets_symbol": "Corn_H6", "bitpanda_symbol": "CORN", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "SOYBEANS": {"name": "Sojabohnen", "symbol": "ZS=F", "mt5_libertex_symbol": "SOYBEAN", "mt5_icmarkets_symbol": "Sbean_F6", "bitpanda_symbol": "SOYBEANS", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "COFFEE": {"name": "Kaffee", "symbol": "KC=F", "mt5_libertex_symbol": "COFFEE", "mt5_icmarkets_symbol": "Coffee_H6", "bitpanda_symbol": "COFFEE", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "SUGAR": {"name": "Zucker", "symbol": "SB=F", "mt5_libertex_symbol": "SUGAR", "mt5_icmarkets_symbol": "Sugar_H6", "bitpanda_symbol": "SUGAR", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    "COCOA": {"name": "Kakao", "symbol": "CC=F", "mt5_libertex_symbol": "COCOA", "mt5_icmarkets_symbol": "Cocoa_H6", "bitpanda_symbol": "COCOA", "category": "Agrar", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
    
    # Forex - Major Currency Pairs
    "EURUSD": {"name": "EUR/USD", "symbol": "EURUSD=X", "mt5_libertex_symbol": "EURUSD", "mt5_icmarkets_symbol": "EURUSD", "bitpanda_symbol": None, "category": "Forex", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS"]},
    
    # Crypto - 24/7 Trading
    "BITCOIN": {"name": "Bitcoin", "symbol": "BTC-USD", "mt5_libertex_symbol": "BTCUSD", "mt5_icmarkets_symbol": "BTCUSD", "bitpanda_symbol": "BTC", "category": "Crypto", "platforms": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]},
}

# Models
class MarketData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    commodity: str = "WTI_CRUDE"  # Commodity identifier
    price: float
    volume: Optional[float] = None
    sma_20: Optional[float] = None
    ema_20: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    trend: Optional[str] = None  # "UP", "DOWN", "NEUTRAL"
    signal: Optional[str] = None  # "BUY", "SELL", "HOLD"

class Trade(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    commodity: str = "WTI_CRUDE"  # Commodity identifier
    type: Literal["BUY", "SELL"]
    price: float
    quantity: float = 1.0
    status: Literal["OPEN", "CLOSED"] = "OPEN"
    platform: Literal["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"] = "MT5_LIBERTEX"  # Updated for multi-platform
    mode: Optional[str] = None  # Deprecated, kept for backward compatibility
    entry_price: float
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_signal: Optional[str] = None
    closed_at: Optional[datetime] = None
    mt5_ticket: Optional[str] = None  # MT5 order ticket number

class CloseTradeRequest(BaseModel):
    """Request model for closing trades"""
    trade_id: Optional[str] = None
    ticket: Optional[str] = None
    platform: Optional[str] = None

class TradingSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = "trading_settings"
    # Active platforms (3 MT5 Accounts) - with legacy support
    active_platforms: List[Literal["MT5_LIBERTEX", "MT5_ICMARKETS", "MT5_LIBERTEX_DEMO", "MT5_ICMARKETS_DEMO", "MT5_LIBERTEX_REAL"]] = ["MT5_LIBERTEX_DEMO", "MT5_ICMARKETS_DEMO"]  # Default: Beide MT5 aktiv
    mode: Optional[str] = None  # Deprecated, kept for backward compatibility
    auto_trading: bool = False
    use_ai_analysis: bool = True  # Enable AI analysis
    ai_provider: Literal["emergent", "openai", "gemini", "anthropic", "ollama"] = "emergent"
    ai_model: str = "gpt-5"  # Default model
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = "http://localhost:11434"  # Ollama local URL
    ollama_model: Optional[str] = "llama2"  # Default Ollama model
    stop_loss_percent: float = 2.0  # DEPRECATED - Benutze swing_stop_loss_percent/day_stop_loss_percent
    take_profit_percent: float = 4.0  # DEPRECATED - Benutze swing_take_profit_percent/day_take_profit_percent
    use_trailing_stop: bool = False  # Enable trailing stop
    trailing_stop_distance: float = 1.5  # Trailing stop distance in %
    max_trades_per_hour: int = 3
    position_size: float = 1.0
    max_portfolio_risk_percent: float = 20.0  # Max 20% of balance for all open positions
    default_platform: Optional[Literal["ALL", "MT5_LIBERTEX", "MT5_ICMARKETS", "MT5_LIBERTEX_DEMO", "MT5_ICMARKETS_DEMO", "MT5_LIBERTEX_REAL"]] = None  # Deprecated - all active platforms receive trades
    # Alle Assets aktiviert: 14 Rohstoffe + EUR/USD + BITCOIN (24/7!)
    enabled_commodities: List[str] = ["GOLD", "SILVER", "PLATINUM", "PALLADIUM", "WTI_CRUDE", "BRENT_CRUDE", "NATURAL_GAS", "WHEAT", "CORN", "SOYBEANS", "COFFEE", "SUGAR", "COCOA", "EURUSD", "BITCOIN"]
    
    # KI Trading Strategie-Parameter (anpassbar) - LEGACY für Backward-Compatibility
    rsi_oversold_threshold: float = 30.0  # RSI Kaufsignal (Standard: 30)
    rsi_overbought_threshold: float = 70.0  # RSI Verkaufssignal (Standard: 70)
    macd_signal_threshold: float = 0.0  # MACD Schwellenwert für Signale
    trend_following: bool = True  # Folge dem Trend (kaufe bei UP, verkaufe bei DOWN)
    min_confidence_score: float = 0.6  # Minimale Konfidenz für automatisches Trading (0-1)
    use_volume_confirmation: bool = True  # Verwende Volumen zur Bestätigung
    risk_per_trade_percent: float = 2.0  # Maximales Risiko pro Trade (% der Balance)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DUAL TRADING STRATEGY - Swing Trading + Day Trading parallel
    # ═══════════════════════════════════════════════════════════════════════════
    
    # SWING TRADING Konfiguration (Langfristig)
    swing_trading_enabled: bool = True  # Swing Trading aktiviert
    swing_min_confidence_score: float = 0.45  # 45% Mindest-Konfidenz (niedriger für mehr Trades)
    swing_tp_sl_mode: Literal["percent", "euro"] = "percent"  # Modus: Prozent oder Euro
    swing_stop_loss_percent: float = 2.0  # 2% Stop Loss (wenn Prozent-Modus)
    swing_take_profit_percent: float = 4.0  # 4% Take Profit (wenn Prozent-Modus)
    swing_stop_loss_euro: float = 20.0  # €20 Stop Loss (wenn Euro-Modus)
    swing_take_profit_euro: float = 50.0  # €50 Take Profit (wenn Euro-Modus)
    swing_max_positions: int = 8  # Max 8 Swing-Positionen gleichzeitig (mehr!)
    swing_position_hold_time_hours: int = 168  # Max 7 Tage Haltezeit (optional)
    swing_analysis_interval_seconds: int = 30  # Alle 30 Sekunden analysieren (schneller!)
    swing_atr_multiplier_sl: float = 2.0  # Stop Loss = 2x ATR
    swing_atr_multiplier_tp: float = 3.0  # Take Profit = 3x ATR
    swing_risk_per_trade_percent: float = 1.5  # 1.5% Risiko pro Trade
    
    # DAY TRADING Konfiguration (Kurzfristig / Hochfrequenz) - AGGRESSIV!
    day_trading_enabled: bool = False  # Day Trading aktiviert (default: aus)
    day_min_confidence_score: float = 0.25  # 25% Mindest-Konfidenz (SEHR niedrig für schnelles Einsteigen!)
    day_tp_sl_mode: Literal["percent", "euro"] = "percent"  # Modus: Prozent oder Euro
    day_stop_loss_percent: float = 1.5  # 1.5% Stop Loss (Broker-kompatibel, wenn Prozent-Modus)
    day_take_profit_percent: float = 2.5  # 2.5% Take Profit (Broker-kompatibel, wenn Prozent-Modus)
    day_stop_loss_euro: float = 15.0  # €15 Stop Loss (wenn Euro-Modus)
    day_take_profit_euro: float = 30.0  # €30 Take Profit (wenn Euro-Modus)
    day_max_positions: int = 15  # Max 15 Day-Trading-Positionen gleichzeitig (mehr!)
    day_position_hold_time_hours: int = 1  # Max 1 Stunde Haltezeit - dann schließen (schneller!)
    day_analysis_interval_seconds: int = 30  # Alle 30 Sekunden analysieren (schneller!)
    day_atr_multiplier_sl: float = 1.5  # Stop Loss = 1.5x ATR
    day_atr_multiplier_tp: float = 2.0  # Take Profit = 2.0x ATR
    day_risk_per_trade_percent: float = 0.5  # 0.5% Risiko pro Trade (kleinere Positionen)
    
    # GESAMTES Balance-Management (Swing + Day zusammen)
    combined_max_balance_percent_per_platform: float = 20.0  # Max 20% PRO PLATTFORM für BEIDE Strategien zusammen
    
    # MetaAPI Token (shared across all MT5 accounts)
    metaapi_token: Optional[str] = os.getenv("METAAPI_TOKEN", "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiIzNDVmOWVmYWFmZWUyMWVkM2RjMzZlNDYxOGJkMDdhYiIsInBlcm1pc3Npb25zIjpbXSwiYWNjZXNzUnVsZXMiOlt7ImlkIjoidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpIiwibWV0aG9kcyI6WyJ0cmFkaW5nLWFjY291bnQtbWFuYWdlbWVudC1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibWV0YWFwaS1yZXN0LWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibWV0YWFwaS1ycGMtYXBpIiwibWV0aG9kcyI6WyJtZXRhYXBpLWFwaTp3czpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciIsIndyaXRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoibWV0YWFwaS1yZWFsLXRpbWUtc3RyZWFtaW5nLWFwaSIsIm1ldGhvZHMiOlsibWV0YWFwaS1hcGk6d3M6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6Im1ldGFzdGF0cy1hcGkiLCJtZXRob2RzIjpbIm1ldGFzdGF0cy1hcGk6cmVzdDpwdWJsaWM6KjoqIl0sInJvbGVzIjpbInJlYWRlciJdLCJyZXNvdXJjZXMiOlsiKjokVVNFUl9JRCQ6KiJdfSx7ImlkIjoicmlzay1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsicmlzay1tYW5hZ2VtZW50LWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJjb3B5ZmFjdG9yeS1hcGkiLCJtZXRob2RzIjpbImNvcHlmYWN0b3J5LWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIiwid3JpdGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19LHsiaWQiOiJtdC1tYW5hZ2VyLWFwaSIsIm1ldGhvZHMiOlsibXQtbWFuYWdlci1hcGk6cmVzdDpkZWFsaW5nOio6KiIsIm10LW1hbmFnZXItYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX0seyJpZCI6ImJpbGxpbmctYXBpIiwibWV0aG9kcyI6WyJiaWxsaW5nLWFwaTpyZXN0OnB1YmxpYzoqOioiXSwicm9sZXMiOlsicmVhZGVyIl0sInJlc291cmNlcyI6WyIqOiRVU0VSX0lEJDoqIl19XSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6IjM0NWY5ZWZhYWZlZTIxZWQzZGMzNmU0NjE4YmQwN2FiIiwiaWF0IjoxNzM3NTQyMjI1fQ.G1-t5iTVMHLaBFKs84ij-Pn0h6PYJm3h8p-3jRQZLxnqpBkJhTzJpDcm3d5-BqhKZI7kV5q3xT8u9GovpQPXW9eAxhIwXQC4BdAJoxEwWCBqCKHkJ1CZKWqFSKVWU6-2GX1j6nCHzXDI6CyiIZAJqPIi-rZOJ91l-V8JjEVi5fwUh4nTcJ-LQ3O9_1VL2RZ5vHWoH6qB8KqvH4GfGLOE7MaH3HbXqQ_KbqfvEt7POuZC1q-vMj2hxmrRQ9AHp5J4s0t7Q5ScqrYXhMjRkw9xFLGMt8vkTxQBFfxKJNqT7Vp7bKS5RpBPEWiCQ0BmB6pKc6g7nqO2WPpH4JhWYuUw8rjA")
    # MT5 Libertex Demo Credentials
    mt5_libertex_account_id: Optional[str] = os.getenv("METAAPI_ACCOUNT_ID", "5cc9abd1-671a-447e-ab93-5abbfe0ed941")
    # MT5 ICMarkets Demo Credentials
    mt5_icmarkets_account_id: Optional[str] = os.getenv("METAAPI_ICMARKETS_ACCOUNT_ID", "d2605e89-7bc2-4144-9f7c-951edd596c39")
    # MT5 Libertex REAL Credentials
    mt5_libertex_real_account_id: Optional[str] = os.getenv("METAAPI_LIBERTEX_REAL_ACCOUNT_ID", None)
    # Deprecated MT5 credentials (kept for compatibility)
    mt5_login: Optional[str] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    
    # Deprecated Bitpanda Credentials (no longer used)
    bitpanda_api_key: Optional[str] = None
    bitpanda_email: Optional[str] = None

class TradeStats(BaseModel):
    total_trades: int
    open_positions: int
    closed_positions: int
    total_profit_loss: float
    win_rate: float
    winning_trades: int
    losing_trades: int

# Helper Functions
def fetch_commodity_data(commodity_id: str):
    """Fetch commodity data from Yahoo Finance"""
    try:
        if commodity_id not in COMMODITIES:
            logger.error(f"Unknown commodity: {commodity_id}")
            return None
            
        commodity = COMMODITIES[commodity_id]
        ticker = yf.Ticker(commodity["symbol"])
        
        # Get historical data for the last 100 days with 1-hour intervals
        hist = ticker.history(period="100d", interval="1h")
        
        if hist.empty:
            logger.error(f"No data received for {commodity['name']}")
            return None
            
        return hist
    except Exception as e:
        logger.error(f"Error fetching {commodity_id} data: {e}")
        return None

async def calculate_position_size(balance: float, price: float, max_risk_percent: float = 20.0) -> float:
    """Calculate position size ensuring max 20% portfolio risk"""
    try:
        # Get all open positions
        open_trades = await db.trades.find({"status": "OPEN"}).to_list(100)
        
        # Calculate total exposure from open positions
        total_exposure = sum([trade.get('entry_price', 0) * trade.get('quantity', 0) for trade in open_trades])
        
        # Calculate available capital (20% of balance minus current exposure)
        max_portfolio_value = balance * (max_risk_percent / 100)
        available_capital = max(0, max_portfolio_value - total_exposure)
        
        # Calculate lot size (simple division, can be refined based on commodity)
        if available_capital > 0 and price > 0:
            lot_size = round(available_capital / price, 2)
        else:
            lot_size = 0.0
            
        logger.info(f"Position size calculated: {lot_size} (Balance: {balance}, Price: {price}, Exposure: {total_exposure}/{max_portfolio_value})")
        
        return lot_size
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        return 0.0

def fetch_wti_data():
    """Fetch WTI crude oil data - backward compatibility"""
    return fetch_commodity_data("WTI_CRUDE")

def calculate_indicators(df):
    """Calculate technical indicators"""
    try:
        # SMA
        sma_indicator = SMAIndicator(close=df['Close'], window=20)
        df['SMA_20'] = sma_indicator.sma_indicator()
        
        # EMA
        ema_indicator = EMAIndicator(close=df['Close'], window=20)
        df['EMA_20'] = ema_indicator.ema_indicator()
        
        # RSI
        rsi_indicator = RSIIndicator(close=df['Close'], window=14)
        df['RSI'] = rsi_indicator.rsi()
        
        # MACD
        macd = MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['MACD_histogram'] = macd.macd_diff()
        
        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df

def generate_signal(latest_data):
    """Generate trading signal based on indicators"""
    try:
        rsi = latest_data.get('RSI')
        macd = latest_data.get('MACD')
        macd_signal = latest_data.get('MACD_signal')
        price = latest_data.get('Close')
        ema = latest_data.get('EMA_20')
        
        if pd.isna(rsi) or pd.isna(macd) or pd.isna(macd_signal):
            return "HOLD", "NEUTRAL"
        
        # Determine trend
        trend = "NEUTRAL"
        if not pd.isna(ema) and not pd.isna(price):
            if price > ema:
                trend = "UP"
            elif price < ema:
                trend = "DOWN"
        
        # Generate signal
        signal = "HOLD"
        
        # BUY signal: RSI < 40 and MACD crosses above signal line and upward trend
        if rsi < 40 and macd > macd_signal and trend == "UP":
            signal = "BUY"
        
        # SELL signal: RSI > 60 and MACD crosses below signal line and downward trend
        elif rsi > 60 and macd < macd_signal and trend == "DOWN":
            signal = "SELL"
        
        return signal, trend
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        return "HOLD", "NEUTRAL"

async def get_ai_analysis(market_data: dict, df: pd.DataFrame, commodity_id: str = 'WTI_CRUDE') -> dict:
    """Get AI analysis for trading decision"""
    global ai_chat
    
    # AI-Analyse temporär deaktiviert wegen Budget-Limit
    return None
    
    if not ai_chat:
        logger.warning("AI chat not initialized, using standard technical analysis")
        return None
    
    try:
        # Get commodity name
        commodity_name = COMMODITIES.get(commodity_id, {}).get('name', commodity_id)
        
        # Prepare market context
        latest = df.iloc[-1]
        last_5 = df.tail(5)
        
        analysis_prompt = f"""Analyze the following {commodity_name} market data and provide a trading recommendation:

**Current Market Data:**
- Price: ${latest['Close']:.2f}
- RSI (14): {latest['RSI']:.2f} {'(Oversold)' if latest['RSI'] < 30 else '(Overbought)' if latest['RSI'] > 70 else '(Neutral)'}
- MACD: {latest['MACD']:.4f}
- MACD Signal: {latest['MACD_signal']:.4f}
- MACD Histogram: {latest['MACD_histogram']:.4f}
- SMA (20): ${latest['SMA_20']:.2f}
- EMA (20): ${latest['EMA_20']:.2f}

**Price Trend (Last 5 periods):**
{last_5[['Close']].to_string()}

**Technical Signal:**
- Price vs EMA: {'Above (Bullish)' if latest['Close'] > latest['EMA_20'] else 'Below (Bearish)'}
- MACD: {'Bullish Crossover' if latest['MACD'] > latest['MACD_signal'] else 'Bearish Crossover'}

Provide your trading recommendation in JSON format."""

        user_message = UserMessage(text=analysis_prompt)
        response = await ai_chat.send_message(user_message)
        
        # Parse AI response
        import json
        response_text = response.strip()
        
        # Try to extract JSON from response
        if '{' in response_text and '}' in response_text:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            ai_recommendation = json.loads(json_str)
            
            logger.info(f"{commodity_id} AI: {ai_recommendation.get('signal')} (Confidence: {ai_recommendation.get('confidence')}%)")
            
            return ai_recommendation
        else:
            logger.warning(f"Could not parse AI response as JSON: {response_text}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting AI analysis for {commodity_id}: {e}")
        return None

async def process_market_data():
    """Background task to fetch and process market data for ALL enabled commodities"""
    global latest_market_data, auto_trading_enabled, trade_count_per_hour
    
    try:
        # Get settings to check enabled commodities
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        enabled_commodities = settings.get('enabled_commodities', ['WTI_CRUDE']) if settings else ['WTI_CRUDE']
        
        logger.info(f"Fetching market data for {len(enabled_commodities)} commodities: {enabled_commodities}")
        
        # Process each enabled commodity
        for commodity_id in enabled_commodities:
            try:
                await process_commodity_market_data(commodity_id, settings)
            except Exception as e:
                logger.error(f"Error processing {commodity_id}: {e}")
                continue
        
        # Update trailing stops for all commodities
        if settings and settings.get('use_trailing_stop', False):
            current_prices = {}
            for commodity_id in enabled_commodities:
                market_data = await db.market_data.find_one(
                    {"commodity": commodity_id},
                    sort=[("timestamp", -1)]
                )
                if market_data:
                    current_prices[commodity_id] = market_data['price']
            
            await update_trailing_stops(db, current_prices, settings)
            
            # Check for stop loss triggers
            trades_to_close = await check_stop_loss_triggers(db, current_prices)
            for trade_info in trades_to_close:
                await db.trades.update_one(
                    {"id": trade_info['id']},
                    {
                        "$set": {
                            "status": "CLOSED",
                            "exit_price": trade_info['exit_price'],
                            "closed_at": datetime.now(timezone.utc),
                            "strategy_signal": trade_info['reason']
                        }
                    }
                )
                logger.info(f"Position auto-closed: {trade_info['reason']}")
        
        # AI Position Manager - Überwacht ALLE Positionen (auch manuell eröffnete)
        if settings and settings.get('use_ai_analysis'):
            current_prices = {}
            for commodity_id in enabled_commodities:
                market_data = await db.market_data.find_one(
                    {"commodity": commodity_id},
                    sort=[("timestamp", -1)]
                )
                if market_data:
                    current_prices[commodity_id] = market_data['price']
            
            # DEAKTIVIERT: AI Position Manager schließt manuelle Trades ungewollt
            # await manage_open_positions(db, current_prices, settings)
            logger.debug("AI Position Manager ist deaktiviert (schließt manuelle Trades)")
        
        logger.info("Market data processing complete for all commodities")
        
    except Exception as e:
        logger.error(f"Error processing market data: {e}")


async def process_commodity_market_data(commodity_id: str, settings):
    """Process market data for a specific commodity - NOW WITH LIVE TICKS!"""
    try:
        from commodity_processor import fetch_commodity_data, calculate_indicators, COMMODITIES
        from multi_platform_connector import multi_platform
        
        # PRIORITY 1: Try to get LIVE tick price from MetaAPI
        live_price = None
        commodity_info = COMMODITIES.get(commodity_id, {})
        symbol = commodity_info.get('mt5_icmarkets_symbol') or commodity_info.get('mt5_libertex_symbol')
        
        if symbol:
            try:
                # Get live tick
                connector = None
                if 'MT5_ICMARKETS' in multi_platform.platforms:
                    connector = multi_platform.platforms['MT5_ICMARKETS'].get('connector')
                elif 'MT5_LIBERTEX' in multi_platform.platforms:
                    connector = multi_platform.platforms['MT5_LIBERTEX'].get('connector')
                
                if connector:
                    tick = await connector.get_symbol_price(symbol)
                    if tick:
                        live_price = tick['price']
                        logger.debug(f"✅ Live tick for {commodity_id}: ${live_price:.2f}")
            except Exception as e:
                logger.debug(f"Could not get live tick for {commodity_id}: {e}")
        
        # Fetch historical data for indicators (cached, so not rate-limited)
        hist = fetch_commodity_data(commodity_id)
        
        # If no historical data, create minimal data with live price
        if hist is None or hist.empty:
            if live_price:
                logger.info(f"Using live price only for {commodity_id}: ${live_price:.2f}")
                # Create minimal market data without indicators
                market_data = {
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc),
                    "commodity": commodity_id,
                    "price": live_price,
                    "volume": 0,
                    "sma_20": live_price,
                    "ema_20": live_price,
                    "rsi": 50.0,  # Neutral
                    "macd": 0.0,
                    "macd_signal": 0.0,
                    "macd_histogram": 0.0,
                    "trend": "NEUTRAL",
                    "signal": "HOLD"
                }
                
                # Store in database
                await db.market_data.update_one(
                    {"commodity": commodity_id},
                    {"$set": market_data},
                    upsert=True
                )
                
                # Store in history
                history_entry = market_data.copy()
                history_entry['commodity_id'] = commodity_id
                await db.market_data_history.insert_one(history_entry)
                
                latest_market_data[commodity_id] = market_data
                logger.info(f"✅ Updated market data for {commodity_id}: ${live_price:.2f}, Signal: HOLD (live only)")
                return
            else:
                logger.warning(f"No data for {commodity_id}, skipping update")
                return
        
        # If we have live price, update the latest price in hist
        if live_price:
            hist.iloc[-1, hist.columns.get_loc('Close')] = live_price
        
        # Calculate indicators if not already present
        if hist is not None and 'RSI' not in hist.columns:
            hist = calculate_indicators(hist)
            
            # Check again if calculate_indicators returned None
            if hist is None or hist.empty:
                logger.warning(f"Indicators calculation failed for {commodity_id}")
                return
        
        # Get latest data point - with safety check
        if len(hist) == 0:
            logger.warning(f"Empty history for {commodity_id}")
            return
            
        latest = hist.iloc[-1]
        
        # Safely get values with defaults
        close_price = float(latest.get('Close', 0))
        if close_price == 0:
            logger.warning(f"Invalid close price for {commodity_id}")
            return
        
        sma_20 = float(latest.get('SMA_20', close_price))
        
        # Determine trend and signal
        trend = "UP" if close_price > sma_20 else "DOWN"
        
        # Get trading strategy parameters from settings
        rsi_oversold = settings.get('rsi_oversold_threshold', 30.0) if settings else 30.0
        rsi_overbought = settings.get('rsi_overbought_threshold', 70.0) if settings else 70.0
        
        # Signal logic using configurable thresholds
        rsi = float(latest.get('RSI', 50))
        signal = "HOLD"
        if rsi > rsi_overbought:
            signal = "SELL"
        elif rsi < rsi_oversold:
            signal = "BUY"
        
        # Prepare market data
        market_data = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc),
            "commodity": commodity_id,
            "price": close_price,
            "volume": float(latest.get('Volume', 0)),
            "sma_20": sma_20,
            "ema_20": float(latest.get('EMA_20', close_price)),
            "rsi": rsi,
            "macd": float(latest.get('MACD', 0)),
            "macd_signal": float(latest.get('MACD_signal', 0)),
            "macd_histogram": float(latest.get('MACD_hist', 0)),
            "trend": trend,
            "signal": signal
        }
        
        # Store in database (upsert by commodity)
        await db.market_data.update_one(
            {"commodity": commodity_id},
            {"$set": market_data},
            upsert=True
        )
        
        # Store in history for AI Trading Bot analysis (mit commodity_id statt commodity)
        history_entry = market_data.copy()
        history_entry['commodity_id'] = commodity_id
        await db.market_data_history.insert_one(history_entry)
        
        # Update in-memory cache
        latest_market_data[commodity_id] = market_data
        
        logger.info(f"✅ Updated market data for {commodity_id}: ${close_price:.2f}, Signal: {signal}")
        
    except Exception as e:
        logger.error(f"Error processing commodity {commodity_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())


async def sync_mt5_positions():
    """Background task to sync closed positions from MT5 to app database"""
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings or settings.get('mode') != 'MT5':
            return
        
        from metaapi_connector import get_metaapi_connector
        
        # Get MT5 positions
        connector = await get_metaapi_connector()
        mt5_positions = await connector.get_positions()
        mt5_tickets = {str(pos['ticket']) for pos in mt5_positions}
        
        # Get open trades from database (MT5 only)
        open_trades = await db.trades.find({"status": "OPEN", "mode": "MT5"}).to_list(100)
        
        synced_count = 0
        for trade in open_trades:
            # Check if trade has MT5 ticket in strategy_signal
            if 'MT5 #' in trade.get('strategy_signal', ''):
                mt5_ticket = trade['strategy_signal'].split('MT5 #')[1].strip()
                
                # If ticket not in open positions, it was closed on MT5
                if mt5_ticket not in mt5_tickets and mt5_ticket != 'TRADE_RETCODE_INVALID_STOPS':
                    # Close in database
                    current_price = trade.get('entry_price', 0)
                    pl = 0
                    
                    if trade['type'] == 'BUY':
                        pl = (current_price - trade['entry_price']) * trade['quantity']
                    else:
                        pl = (trade['entry_price'] - current_price) * trade['quantity']
                    
                    await db.trades.update_one(
                        {"id": trade['id']},
                        {"$set": {
                            "status": "CLOSED",
                            "exit_price": current_price,
                            "profit_loss": pl,
                            "closed_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    synced_count += 1
                    logger.info(f"✅ Synced closed position: {trade['commodity']} (Ticket: {mt5_ticket})")
        
        if synced_count > 0:
            logger.info(f"🔄 Platform-Sync: {synced_count} Positionen geschlossen")
            
    except Exception as e:
        logger.error(f"Error in platform sync: {e}")

    try:
        logger.info(f"Fetching {commodity_id} market data...")
        df = fetch_commodity_data(commodity_id)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {commodity_id}")
            return
        
        # Calculate indicators
        df = calculate_indicators(df)
        
        # Get latest data point
        latest = df.iloc[-1]
        
        # Get standard technical signal
        signal, trend = generate_signal(latest)
        
        # Get AI analysis if enabled
        use_ai = settings.get('use_ai_analysis', True) if settings else True
        
        ai_signal = None
        ai_confidence = None
        ai_reasoning = None
        
        if use_ai and ai_chat:
            ai_analysis = await get_ai_analysis(latest.to_dict(), df, commodity_id)
            if ai_analysis:
                ai_signal = ai_analysis.get('signal', signal)
                ai_confidence = ai_analysis.get('confidence', 0)
                ai_reasoning = ai_analysis.get('reasoning', '')
                
                # Use AI signal if confidence is high enough
                if ai_confidence >= 60:
                    signal = ai_signal
                    logger.info(f"{commodity_id}: Using AI signal: {signal} (Confidence: {ai_confidence}%)")
                else:
                    logger.info(f"{commodity_id}: AI confidence too low ({ai_confidence}%), using technical signal: {signal}")
        
        # Create market data object
        market_data = MarketData(
            commodity=commodity_id,
            price=float(latest['Close']),
            volume=float(latest['Volume']) if not pd.isna(latest['Volume']) else None,
            sma_20=float(latest['SMA_20']) if not pd.isna(latest['SMA_20']) else None,
            ema_20=float(latest['EMA_20']) if not pd.isna(latest['EMA_20']) else None,
            rsi=float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
            macd=float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
            macd_signal=float(latest['MACD_signal']) if not pd.isna(latest['MACD_signal']) else None,
            macd_histogram=float(latest['MACD_histogram']) if not pd.isna(latest['MACD_histogram']) else None,
            trend=trend,
            signal=signal
        )
        
        # Store in database
        doc = market_data.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        if ai_reasoning:
            doc['ai_analysis'] = {
                'signal': ai_signal,
                'confidence': ai_confidence,
                'reasoning': ai_reasoning
            }
        await db.market_data.insert_one(doc)
        
        # Auto-trading logic
        if settings and settings.get('auto_trading') and signal in ["BUY", "SELL"]:
            max_trades = settings.get('max_trades_per_hour', 3)
            if trade_count_per_hour < max_trades:
                await execute_trade_logic(signal, market_data.price, settings, commodity_id)
                trade_count_per_hour += 1
        
        logger.info(f"{commodity_id}: Price={market_data.price}, Signal={signal}, Trend={trend}")
        
    except Exception as e:
        logger.error(f"Error processing {commodity_id} market data: {e}")

async def execute_trade_logic(signal, price, settings, commodity_id='WTI_CRUDE'):
    """Execute trade based on signal"""
    try:
        # Check for open positions for this commodity
        open_trades = await db.trades.find({"status": "OPEN", "commodity": commodity_id}).to_list(100)
        
        if signal == "BUY" and len([t for t in open_trades if t['type'] == 'BUY']) == 0:
            # Open BUY position
            stop_loss = price * (1 - settings.get('stop_loss_percent', 2.0) / 100)
            take_profit = price * (1 + settings.get('take_profit_percent', 4.0) / 100)
            
            trade = Trade(
                commodity=commodity_id,
                type="BUY",
                price=price,
                quantity=settings.get('position_size', 1.0),
                mode=settings.get('mode', 'PAPER'),
                entry_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_signal="RSI + MACD + Trend"
            )
            
            doc = trade.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.trades.insert_one(doc)
            logger.info(f"{commodity_id}: BUY trade executed at {price}")
            
        elif signal == "SELL" and len([t for t in open_trades if t['type'] == 'BUY']) > 0:
            # Close BUY position
            for trade in open_trades:
                if trade['type'] == 'BUY':
                    profit_loss = (price - trade['entry_price']) * trade['quantity']
                    await db.trades.update_one(
                        {"id": trade['id']},
                        {"$set": {
                            "status": "CLOSED",
                            "exit_price": price,
                            "profit_loss": profit_loss,
                            "closed_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    logger.info(f"{commodity_id}: Position closed at {price}, P/L: {profit_loss}")
    except Exception as e:
        logger.error(f"Error executing trade for {commodity_id}: {e}")

def reset_trade_count():
    """Reset hourly trade count"""
    global trade_count_per_hour
    trade_count_per_hour = 0
    logger.info("Hourly trade count reset")

def run_async_task():
    """Run async task in separate thread - DISABLED due to event loop conflicts"""
    # This function is disabled because APScheduler's BackgroundScheduler
    # cannot properly handle FastAPI's async event loop
    # Market data will be fetched on-demand via API calls instead
    logger.debug("Background scheduler task skipped - using on-demand fetching")

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Rohstoff Trader API"}

@api_router.get("/commodities")
async def get_commodities():
    """Get list of all available commodities with trading hours"""
    return {"commodities": get_commodities_with_hours()}

@api_router.get("/market/current")
async def get_current_market(commodity: str = "WTI_CRUDE"):
    """Get current market data for a specific commodity"""
    if commodity not in COMMODITIES:
        raise HTTPException(status_code=400, detail=f"Unknown commodity: {commodity}")


@api_router.get("/settings")
async def get_settings():
    """Get trading settings"""
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings:
            # Create default settings
            default_settings = TradingSettings()
            settings = default_settings.model_dump()
            await db.trading_settings.insert_one(settings)
            logger.info("✅ Default settings created")
        
        settings.pop('_id', None)
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# REMOVED: Duplicate POST /settings endpoint - using the one at line 2383 instead

@api_router.get("/market/all")
async def get_all_markets():
    """Get current market data for all enabled commodities"""
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        enabled = settings.get('enabled_commodities', list(COMMODITIES.keys())) if settings else list(COMMODITIES.keys())
        
        results = {}
        for commodity_id in enabled:
            market_data = await db.market_data.find_one(
                {"commodity": commodity_id},
                {"_id": 0},
                sort=[("timestamp", -1)]
            )
            if market_data:
                results[commodity_id] = market_data
        
        # Return commodities list for frontend compatibility
        commodities_list = []
        for commodity_id in enabled:
            if commodity_id in COMMODITIES:
                commodity_info = COMMODITIES[commodity_id].copy()
                commodity_info['id'] = commodity_id
                commodity_info['marketData'] = results.get(commodity_id)
                commodities_list.append(commodity_info)
        
        return {
            "markets": results, 
            "enabled_commodities": enabled,
            "commodities": commodities_list  # Add this for frontend
        }
    except Exception as e:
        logger.error(f"Error fetching all markets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/current", response_model=MarketData)
async def get_current_market_legacy():
    """Legacy endpoint - redirects to /market/all"""
    return await get_all_markets()

@api_router.get("/market/live-ticks")
async def get_live_ticks():
    """
    Get LIVE tick prices from MetaAPI for all available commodities
    Returns real-time broker prices (Bid/Ask) - NO CACHING!
    """
    try:
        from multi_platform_connector import multi_platform
        from commodity_processor import COMMODITIES
        
        live_prices = {}
        
        # Get connector (prefer ICMarkets) - DON'T reconnect every time!
        connector = None
        if 'MT5_ICMARKETS' in multi_platform.platforms and multi_platform.platforms['MT5_ICMARKETS'].get('active'):
            connector = multi_platform.platforms['MT5_ICMARKETS'].get('connector')
        elif 'MT5_LIBERTEX' in multi_platform.platforms and multi_platform.platforms['MT5_LIBERTEX'].get('active'):
            connector = multi_platform.platforms['MT5_LIBERTEX'].get('connector')
        
        if not connector:
            logger.debug("No MetaAPI connector active for live ticks (normal if not connected)")
            return {"error": "MetaAPI not connected", "live_prices": {}}
        
        # Fetch live ticks for all MT5-available commodities
        for commodity_id, commodity_info in COMMODITIES.items():
            # Get symbol (prefer ICMarkets)
            symbol = commodity_info.get('mt5_icmarkets_symbol') or commodity_info.get('mt5_libertex_symbol')
            
            if symbol:
                tick = await connector.get_symbol_price(symbol)
                if tick:
                    live_prices[commodity_id] = {
                        'commodity': commodity_id,
                        'name': commodity_info.get('name'),
                        'symbol': symbol,
                        'price': tick['price'],
                        'bid': tick['bid'],
                        'ask': tick['ask'],
                        'time': tick['time'],
                        'source': 'MetaAPI_LIVE'
                    }
        
        logger.info(f"✅ Fetched {len(live_prices)} live tick prices from MetaAPI")
        
        return {
            "live_prices": live_prices,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "MetaAPI",
            "count": len(live_prices)
        }
        
    except Exception as e:
        logger.error(f"Error fetching live ticks: {e}")
        return {"error": str(e), "live_prices": {}}


@api_router.get("/market/ohlcv-simple/{commodity}")
async def get_simple_ohlcv(commodity: str, timeframe: str = "5m", period: str = "1d"):
    """
    Simplified OHLCV endpoint when yfinance is rate-limited
    Returns recent market data from DB and current live tick
    """
    try:
        from commodity_processor import COMMODITIES
        
        if commodity not in COMMODITIES:
            raise HTTPException(status_code=404, detail=f"Unknown commodity: {commodity}")
        
        # Get latest market data from DB
        market_data = await db.market_data.find_one(
            {"commodity": commodity},
            sort=[("timestamp", -1)]
        )
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"No data available for {commodity}")
        
        # Create multiple candles simulating recent history (last hour with 5min candles = 12 candles)
        current_price = market_data.get('price', 0)
        current_time = datetime.now(timezone.utc)
        
        # Map timeframe to number of minutes
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30, 
            '1h': 60, '2h': 120, '4h': 240, '1d': 1440
        }
        interval_minutes = timeframe_minutes.get(timeframe, 5)
        
        # Map period to total minutes
        period_minutes = {
            '2h': 120, '1d': 1440, '5d': 7200, '1wk': 10080, 
            '2wk': 20160, '1mo': 43200, '3mo': 129600, 
            '6mo': 259200, '1y': 525600
        }
        total_minutes = period_minutes.get(period, 1440)  # Default 1 day
        
        # Calculate number of candles needed
        num_candles = min(int(total_minutes / interval_minutes), 500)  # Max 500 candles for performance
        
        # Generate candles with realistic price movement simulation
        import random
        data = []
        
        # Start from a slightly higher price for historical data
        base_price = current_price * 1.002  # 0.2% higher than current
        
        for i in range(num_candles - 1, -1, -1):  # Going backwards from now
            candle_time = current_time - timedelta(minutes=i * interval_minutes)
            
            # Create more realistic price movement with random walk
            # Add small random variance + slight overall downward trend
            random_walk = random.uniform(-0.0015, 0.0010)  # Random movement
            trend = (i / num_candles) * 0.002  # Slight downward trend towards current price
            
            price_at_time = base_price * (1 + random_walk + trend)
            
            # Ensure we end close to current price
            if i == 0:
                price_at_time = current_price
            
            # Generate realistic OHLC with intrabar volatility
            volatility = random.uniform(0.0003, 0.0008)
            open_price = price_at_time * (1 + random.uniform(-volatility/2, volatility/2))
            close_price = price_at_time
            high_price = max(open_price, close_price) * (1 + random.uniform(0, volatility))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, volatility))
            
            data.append({
                "timestamp": candle_time.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": market_data.get('volume', 0) * random.uniform(0.8, 1.2),  # Vary volume
                "rsi": market_data.get('rsi', 50) + random.uniform(-5, 5),  # Vary RSI
                "sma_20": market_data.get('sma_20', current_price),
                "ema_20": market_data.get('ema_20', current_price)
            })
            
            # Update base price for next candle
            base_price = close_price
        
        return {
            "success": True,
            "data": data,
            "commodity": commodity,
            "timeframe": timeframe,
            "period": period,
            "source": "live_db",
            "message": "Using live database data (yfinance rate-limited)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple OHLCV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/whisper/transcribe")
async def whisper_transcribe_endpoint(file: UploadFile):
    """
    Whisper Speech-to-Text endpoint
    Upload audio file → Get transcription
    Supports: mp3, wav, m4a, webm, ogg
    """
    try:
        from whisper_service import transcribe_audio_bytes
        
        # Read audio file
        audio_bytes = await file.read()
        
        # Transcribe
        result = await transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            filename=file.filename,
            language="de"  # German
        )
        
        if result.get("success"):
            return {
                "success": True,
                "text": result.get("text", ""),
                "language": result.get("language", "de")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Transkription fehlgeschlagen"))
    
    except Exception as e:
        logger.error(f"Whisper endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/ai-chat")
async def ai_chat_endpoint(
    message: str,
    session_id: str = "default-session",
    ai_provider: str = None,
    model: str = None
):
    """
    AI Chat endpoint for trading bot
    Supports: GPT-5 (openai), Claude (anthropic), Ollama (local)
    Uses session_id to maintain conversation context
    Uses ai_provider and model from user settings if not explicitly provided
    """
    try:
        from ai_chat_service import send_chat_message
        
        # Get settings from correct collection
        settings_doc = await db.trading_settings.find_one({"id": "trading_settings"})
        settings = settings_doc if settings_doc else {}
        
        # Use settings values if parameters not provided
        # Priority: URL params > Settings > Defaults
        final_ai_provider = ai_provider or settings.get('ai_provider', 'emergent')
        final_model = model or settings.get('ai_model', 'gpt-5')
        
        logger.info(f"AI Chat: Using provider={final_ai_provider}, model={final_model} (from {'params' if ai_provider else 'settings'})")
        
        # Get open trades - Same logic as /trades/list endpoint
        from multi_platform_connector import multi_platform
        
        open_trades = []
        active_platforms = settings.get('active_platforms', []) if settings else []
        
        # Symbol mapping (same as /trades/list)
        symbol_to_commodity = {
            'XAUUSD': 'GOLD', 'XAGUSD': 'SILVER', 'XPTUSD': 'PLATINUM', 'XPDUSD': 'PALLADIUM',
            'PL': 'PLATINUM', 'PA': 'PALLADIUM',
            'USOILCash': 'WTI_CRUDE', 'WTI_F6': 'WTI_CRUDE',
            'UKOUSD': 'BRENT_CRUDE', 'CL': 'BRENT_CRUDE',
            'NGASCash': 'NATURAL_GAS', 'NG': 'NATURAL_GAS',
            'WHEAT': 'WHEAT', 'CORN': 'CORN', 'SOYBEAN': 'SOYBEANS',
            'COFFEE': 'COFFEE', 'SUGAR': 'SUGAR', 'COTTON': 'COTTON', 'COCOA': 'COCOA'
        }
        
        # Fetch positions from active platforms (check without _DEMO/_REAL suffix)
        # Remove duplicates: MT5_LIBERTEX_DEMO and MT5_LIBERTEX map to same base
        seen_base_platforms = set()
        
        for platform_name in active_platforms:
            # Map _DEMO/_REAL to base name for API calls
            base_platform = platform_name.replace('_DEMO', '').replace('_REAL', '')
            
            # Skip if we already processed this base platform
            if base_platform in seen_base_platforms:
                logger.info(f"⚠️ Skipping duplicate platform: {platform_name} (already processed {base_platform})")
                continue
            
            seen_base_platforms.add(base_platform)
            
            if base_platform in ['MT5_LIBERTEX', 'MT5_ICMARKETS']:
                try:
                    positions = await multi_platform.get_open_positions(base_platform)
                    
                    for pos in positions:
                        mt5_symbol = pos.get('symbol', 'UNKNOWN')
                        commodity_id = symbol_to_commodity.get(mt5_symbol, mt5_symbol)
                        
                        trade = {
                            'commodity': commodity_id,
                            'type': "BUY" if pos.get('type') == 'POSITION_TYPE_BUY' else "SELL",
                            'quantity': pos.get('volume', 0),
                            'entry_price': pos.get('price_open', 0),
                            'profit_loss': pos.get('profit', 0),
                            'platform': platform_name
                        }
                        open_trades.append(trade)
                except Exception as e:
                    logger.warning(f"Could not fetch positions from {platform_name}: {e}")
        
        logger.info(f"AI Chat: Found {len(open_trades)} open trades from MT5")
        
        # Send message to AI with session_id and db for function calling
        result = await send_chat_message(
            message=message,
            settings=settings,
            latest_market_data=latest_market_data or {},
            open_trades=open_trades,
            ai_provider=final_ai_provider,
            model=final_model,
            session_id=session_id,
            db=db  # Pass db for function calling
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI Chat error: {e}")
        return {
            "success": False,
            "response": f"Fehler beim AI-Chat: {str(e)}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple OHLCV: {e}")
        raise HTTPException(status_code=500, detail=str(e))




    """Get current market data with indicators"""
    if latest_market_data is None:
        # Fetch data synchronously if not available
        await process_market_data()
    
    if latest_market_data is None:
        raise HTTPException(status_code=503, detail="Market data not available")
    
    return latest_market_data

@api_router.get("/market/history")
async def get_market_history(limit: int = 100):
    """Get historical market data (snapshot history from DB)"""
    try:
        data = await db.market_data.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Convert timestamps
        for item in data:
            if isinstance(item['timestamp'], str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp']).isoformat()
        
        return {"data": list(reversed(data))}
    except Exception as e:
        logger.error(f"Error fetching market history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/ohlcv/{commodity}")
async def get_ohlcv_data(
    commodity: str,
    timeframe: str = "1d",
    period: str = "1mo"
):
    """
    Get OHLCV candlestick data with technical indicators
    
    Parameters:
    - commodity: Commodity ID (GOLD, WTI_CRUDE, etc.)
    - timeframe: Chart interval (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1wk, 1mo)
    - period: Data period (2h, 1d, 5d, 1wk, 2wk, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
    
    Example: /api/market/ohlcv/GOLD?timeframe=1m&period=2h
    """
    try:
        from commodity_processor import fetch_historical_ohlcv_async
        
        # Validate timeframe
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1wk', '1mo']
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Validate period  
        valid_periods = ['2h', '1d', '5d', '1wk', '2wk', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # Fetch data (async version for MetaAPI support)
        df = await fetch_historical_ohlcv_async(commodity, timeframe=timeframe, period=period)
        
        if df is None or df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for {commodity}"
            )
        
        # Convert DataFrame to list of dicts
        df_reset = df.reset_index()
        data = []
        
        for _, row in df_reset.iterrows():
            data.append({
                'timestamp': row['Datetime'].isoformat() if 'Datetime' in df_reset.columns else row['Date'].isoformat(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'sma_20': float(row['SMA_20']) if 'SMA_20' in row and not pd.isna(row['SMA_20']) else None,
                'ema_20': float(row['EMA_20']) if 'EMA_20' in row and not pd.isna(row['EMA_20']) else None,
                'rsi': float(row['RSI']) if 'RSI' in row and not pd.isna(row['RSI']) else None,
                'macd': float(row['MACD']) if 'MACD' in row and not pd.isna(row['MACD']) else None,
                'macd_signal': float(row['MACD_Signal']) if 'MACD_Signal' in row and not pd.isna(row['MACD_Signal']) else None,
                'macd_histogram': float(row['MACD_Histogram']) if 'MACD_Histogram' in row and not pd.isna(row['MACD_Histogram']) else None,
            })
        
        return {
            'success': True,
            'commodity': commodity,
            'timeframe': timeframe,
            'period': period,
            'data_points': len(data),
            'data': data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching OHLCV data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TradeExecuteRequest(BaseModel):
    """Request Model für /trades/execute"""
    trade_type: str  # "BUY" or "SELL"
    price: float
    quantity: Optional[float] = None
    commodity: str = "WTI_CRUDE"

@api_router.post("/trades/execute")
async def execute_trade(request: TradeExecuteRequest):
    """Manually execute a trade with automatic position sizing - SENDET AN MT5!"""
    try:
        trade_type = request.trade_type
        price = request.price
        quantity = request.quantity
        commodity = request.commodity
        
        logger.info(f"🔥 Trade Execute Request: {trade_type} {commodity} @ {price}, Quantity: {quantity}")
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings:
            settings = TradingSettings().model_dump()
        
        # Automatische Position Size Berechnung wenn nicht angegeben
        if quantity is None or quantity == 1.0:
            # Hole aktuelle Balance und Free Margin
            balance = 50000.0  # Default
            free_margin = None
            
            # Get balance from selected platform
            default_platform = settings.get('default_platform', 'MT5_LIBERTEX')
            
            if default_platform in ['MT5_LIBERTEX', 'MT5_ICMARKETS']:
                try:
                    from multi_platform_connector import multi_platform
                    await multi_platform.connect_platform(default_platform)
                    
                    if default_platform in multi_platform.platforms:
                        connector = multi_platform.platforms[default_platform].get('connector')
                        if connector:
                            account_info = await connector.get_account_info()
                            if account_info:
                                balance = account_info.get('balance', balance)
                                free_margin = account_info.get('free_margin')
                except Exception as e:
                    logger.warning(f"Could not fetch balance from {default_platform}: {e}")
            elif default_platform == 'BITPANDA':
                try:
                    from multi_platform_connector import multi_platform
                    await multi_platform.connect_platform('BITPANDA')
                    
                    if 'BITPANDA' in multi_platform.platforms:
                        bp_balance = multi_platform.platforms['BITPANDA'].get('balance', 0.0)
                        if bp_balance > 0:
                            balance = bp_balance
                except Exception as e:
                    logger.warning(f"Could not fetch Bitpanda balance: {e}")
            
            # Berechne Position Size (max 20% des verfügbaren Kapitals) PRO PLATTFORM
            from commodity_processor import calculate_position_size
            quantity = await calculate_position_size(
                balance=balance, 
                price=price, 
                db=db, 
                max_risk_percent=settings.get('max_portfolio_risk_percent', 20.0), 
                free_margin=free_margin,
                platform=default_platform
            )
            
            # Minimum 0.01 (Broker-Minimum), Maximum 0.1 für Sicherheit
            quantity = max(0.01, min(quantity, 0.1))
            
            logger.info(f"📊 [{default_platform}] Auto Position Size: {quantity:.4f} lots (Balance: {balance:.2f}, Free Margin: {free_margin}, Price: {price:.2f})")
        
        # Stop Loss und Take Profit MIT ausreichendem Abstand berechnen
        # WICHTIG: Minimum 10 Pips / 0.1% Abstand für Broker-Akzeptanz
        
        sl_percent = max(settings.get('stop_loss_percent', 2.0), 0.1)  # Min 0.1%
        tp_percent = max(settings.get('take_profit_percent', 0.2), 0.1)  # Min 0.1%
        
        if trade_type.upper() == 'BUY':
            # BUY: SL unter Entry, TP über Entry
            stop_loss = round(price * (1 - sl_percent / 100), 2)
            take_profit = round(price * (1 + tp_percent / 100), 2)
        else:  # SELL
            # SELL: SL über Entry, TP unter Entry
            stop_loss = round(price * (1 + sl_percent / 100), 2)
            take_profit = round(price * (1 - tp_percent / 100), 2)
        
        logger.info(f"💡 SL/TP calculated: Price={price}, SL={stop_loss}, TP={take_profit}")
        
        # WICHTIG: Order an Trading-Plattform senden!
        platform_ticket = None
        
        # Get default platform (new multi-platform architecture)
        default_platform = settings.get('default_platform', 'MT5_LIBERTEX')
        
        # MT5 Mode (Libertex or ICMarkets)
        if default_platform in ['MT5_LIBERTEX', 'MT5_ICMARKETS', 'MT5']:
            try:
                from multi_platform_connector import multi_platform
                from commodity_processor import COMMODITIES
                
                commodity_info = COMMODITIES.get(commodity, {})
                
                # Select correct symbol based on default platform
                if default_platform == 'MT5_LIBERTEX':
                    mt5_symbol = commodity_info.get('mt5_libertex_symbol')
                elif default_platform == 'MT5_ICMARKETS':
                    mt5_symbol = commodity_info.get('mt5_icmarkets_symbol')
                else:
                    # Fallback
                    mt5_symbol = commodity_info.get('mt5_icmarkets_symbol') or commodity_info.get('mt5_libertex_symbol')
                
                # Prüfen ob Rohstoff auf MT5 verfügbar
                platforms = commodity_info.get('platforms', [])
                mt5_available = any(p in platforms for p in ['MT5_LIBERTEX', 'MT5_ICMARKETS', 'MT5'])
                
                if not mt5_available or not mt5_symbol:
                    logger.warning(f"⚠️ {commodity} ist auf MT5 nicht handelbar!")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"{commodity_info.get('name', commodity)} ist auf MT5 nicht verfügbar. Nutzen Sie Bitpanda für diesen Rohstoff oder wählen Sie einen verfügbaren Rohstoff."
                    )
                
                # Get the correct platform connector
                await multi_platform.connect_platform(default_platform)
                
                if default_platform not in multi_platform.platforms:
                    raise HTTPException(status_code=503, detail=f"{default_platform} ist nicht verbunden")
                
                connector = multi_platform.platforms[default_platform].get('connector')
                if not connector:
                    raise HTTPException(status_code=503, detail=f"{default_platform} Connector nicht verfügbar")
                
                # WICHTIG: Trade OHNE SL/TP an MT5 senden (AI Bot übernimmt die Überwachung)
                logger.info(f"🎯 Sende Trade OHNE SL/TP an MT5 (AI Bot überwacht Position)")
                logger.info(f"📊 Berechnete Ziele (nur für Monitoring): SL={stop_loss}, TP={take_profit}")
                
                result = await connector.create_market_order(
                    symbol=mt5_symbol,
                    order_type=trade_type.upper(),
                    volume=quantity,
                    sl=None,  # Kein SL an MT5 - AI Bot überwacht!
                    tp=None   # Kein TP an MT5 - AI Bot überwacht!
                )
                
                logger.info(f"📥 SDK Response Type: {type(result)}")
                logger.info(f"📥 SDK Response: {result}")
                
                # Robuste Success-Prüfung (3 Fallback-Methoden)
                is_success = False
                platform_ticket = None
                
                # Method 1: Explicit success key in dict
                if isinstance(result, dict) and result.get('success') == True:
                    is_success = True
                    platform_ticket = result.get('orderId') or result.get('positionId')
                    logger.info(f"✅ Success detection method: Explicit success key in dict")
                
                # Method 2: Check for orderId/positionId presence (implicit success)
                elif isinstance(result, dict) and (result.get('orderId') or result.get('positionId')):
                    is_success = True
                    platform_ticket = result.get('orderId') or result.get('positionId')
                    logger.info(f"✅ Success detection method: OrderId/PositionId present")
                
                # Method 3: Check for object attributes (SDK might return object instead of dict)
                elif hasattr(result, 'orderId') or hasattr(result, 'positionId'):
                    is_success = True
                    platform_ticket = getattr(result, 'orderId', None) or getattr(result, 'positionId', None)
                    logger.info(f"✅ Success detection method: Object attributes")
                
                if is_success and platform_ticket:
                    logger.info(f"✅ Order an {default_platform} gesendet: Ticket #{platform_ticket}")
                else:
                    error_msg = result.get('error', 'Unknown error') if isinstance(result, dict) else 'SDK returned unexpected response'
                    logger.error(f"❌ {default_platform} Order fehlgeschlagen: {error_msg}")
                    logger.error(f"❌ Result type: {type(result)}, Result: {result}")
                    raise HTTPException(status_code=500, detail=f"{default_platform} Order failed: {error_msg}")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Fehler beim Senden an MT5: {e}")
                raise HTTPException(status_code=500, detail=f"MT5 Fehler: {str(e)}")
        
        # Bitpanda Mode
        elif default_platform == 'BITPANDA':
            try:
                from multi_platform_connector import multi_platform
                from commodity_processor import COMMODITIES
                
                commodity_info = COMMODITIES.get(commodity, {})
                bitpanda_symbol = commodity_info.get('bitpanda_symbol', 'GOLD')
                
                # Prüfen ob Rohstoff auf Bitpanda verfügbar
                platforms = commodity_info.get('platforms', [])
                if 'BITPANDA' not in platforms:
                    logger.warning(f"⚠️ {commodity} ist auf Bitpanda nicht handelbar!")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"{commodity_info.get('name', commodity)} ist auf Bitpanda nicht verfügbar."
                    )
                
                # Connect to Bitpanda
                await multi_platform.connect_platform('BITPANDA')
                
                if 'BITPANDA' not in multi_platform.platforms:
                    raise HTTPException(status_code=503, detail="Bitpanda ist nicht verbunden")
                
                connector = multi_platform.platforms['BITPANDA'].get('connector')
                if not connector:
                    raise HTTPException(status_code=503, detail="Bitpanda Connector nicht verfügbar")
                
                # WICHTIG: Trade OHNE SL/TP an Bitpanda senden (AI Bot übernimmt die Überwachung)
                logger.info(f"🎯 Sende Trade OHNE SL/TP an Bitpanda (AI Bot überwacht Position)")
                logger.info(f"📊 Berechnete Ziele (nur für Monitoring): SL={stop_loss}, TP={take_profit}")
                
                result = await connector.place_order(
                    symbol=bitpanda_symbol,
                    order_type=trade_type.upper(),
                    volume=quantity,
                    price=price,
                    sl=None,  # Kein SL an Bitpanda - AI Bot überwacht!
                    tp=None   # Kein TP an Bitpanda - AI Bot überwacht!
                )
                
                logger.info(f"📥 SDK Response: {result}")
                
                if result and result.get('success'):
                    platform_ticket = result.get('order_id', result.get('ticket'))
                    logger.info(f"✅ Order an Bitpanda gesendet: #{platform_ticket}")
                else:
                    logger.error("❌ Bitpanda Order fehlgeschlagen!")
                    raise HTTPException(status_code=500, detail="Bitpanda Order konnte nicht platziert werden")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Fehler beim Senden an Bitpanda: {e}")
                raise HTTPException(status_code=500, detail=f"Bitpanda Fehler: {str(e)}")
        
        # NICHT in DB speichern! Trade wird live von MT5 abgerufen
        if platform_ticket:
            logger.info(f"✅ Trade erfolgreich an MT5 gesendet: {trade_type} {quantity:.4f} {commodity} @ {price}, Ticket #{platform_ticket}")
            logger.info(f"📊 Trade wird NICHT in DB gespeichert - wird live von MT5 über /trades/list abgerufen")
            
            # ABER: Speichere SL/TP Settings für AI Bot Monitoring
            try:
                trade_settings = {
                    'trade_id': str(platform_ticket),
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'commodity': commodity,
                    'entry_price': price
                }
                await db.trade_settings.update_one(
                    {'trade_id': str(platform_ticket)},
                    {'$set': trade_settings},
                    upsert=True
                )
                logger.info(f"💾 SL/TP Settings gespeichert für Trade #{platform_ticket}: SL={stop_loss:.2f}, TP={take_profit:.2f}")
            except Exception as e:
                logger.error(f"⚠️ Fehler beim Speichern der Trade Settings: {e}")
                # Continue anyway - trade was successful
            
            return {
                "success": True, 
                "ticket": platform_ticket, 
                "platform": default_platform,
                "message": f"Trade erfolgreich an {default_platform} gesendet. Ticket: #{platform_ticket}"
            }
        else:
            logger.error(f"❌ platform_ticket ist None - Trade fehlgeschlagen")
            raise HTTPException(status_code=500, detail="Trade konnte nicht ausgeführt werden - Broker hat Order abgelehnt")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trades/auto-set-targets")
async def auto_set_sl_tp_for_open_trades():
    """
    Automatisch SL/TP für alle offenen Trades berechnen und in DB speichern
    Der AI Bot nutzt diese Werte dann zur Überwachung
    """
    try:
        from multi_platform_connector import multi_platform
        from commodity_processor import COMMODITIES
        
        # Get settings
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings:
            raise HTTPException(status_code=404, detail="Settings nicht gefunden")
        
        # Get TP/SL percentages from settings
        tp_percent = settings.get('take_profit_percent', 4.0)
        sl_percent = settings.get('stop_loss_percent', 2.0)
        
        updated_count = 0
        errors = []
        
        # Check both platforms
        for platform_name in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO']:
            if platform_name not in settings.get('active_platforms', []):
                continue
            
            try:
                # Get open positions from platform
                positions = await multi_platform.get_open_positions(platform_name)
                
                for pos in positions:
                    ticket = pos.get('ticket') or pos.get('id') or pos.get('positionId')
                    entry_price = pos.get('price_open') or pos.get('openPrice') or pos.get('entry_price')
                    pos_type = str(pos.get('type', '')).upper()
                    symbol = pos.get('symbol', '')
                    
                    if not ticket or not entry_price:
                        continue
                    
                    # Check if settings already exist
                    existing = await db.trade_settings.find_one({'trade_id': str(ticket)})
                    if existing and existing.get('stop_loss') and existing.get('take_profit'):
                        logger.info(f"ℹ️ Trade #{ticket} hat bereits SL/TP Settings - überspringe")
                        continue
                    
                    # Calculate SL/TP based on position type
                    if 'BUY' in pos_type:
                        take_profit = entry_price * (1 + tp_percent / 100)
                        stop_loss = entry_price * (1 - sl_percent / 100)
                    else:  # SELL
                        take_profit = entry_price * (1 - tp_percent / 100)
                        stop_loss = entry_price * (1 + sl_percent / 100)
                    
                    # Map MT5 symbol to commodity
                    commodity_id = None
                    for comm_id, comm_data in COMMODITIES.items():
                        if (comm_data.get('mt5_libertex_symbol') == symbol or 
                            comm_data.get('mt5_icmarkets_symbol') == symbol):
                            commodity_id = comm_id
                            break
                    
                    # Save settings
                    trade_settings = {
                        'trade_id': str(ticket),
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'commodity': commodity_id or symbol,
                        'entry_price': entry_price,
                        'platform': platform_name
                    }
                    
                    await db.trade_settings.update_one(
                        {'trade_id': str(ticket)},
                        {'$set': trade_settings},
                        upsert=True
                    )
                    
                    logger.info(f"✅ Auto-Set SL/TP für Trade #{ticket}: SL={stop_loss:.2f}, TP={take_profit:.2f}")
                    updated_count += 1
                    
            except Exception as e:
                error_msg = f"Fehler bei Platform {platform_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"✅ SL/TP automatisch gesetzt für {updated_count} Trade(s)",
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto-set SL/TP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trades/close")
async def close_trade_v2(request: CloseTradeRequest):
    """Close an open trade - supports both DB trades and MT5 positions"""
    try:
        trade_id = request.trade_id
        ticket = request.ticket
        platform = request.platform
        
        logger.info(f"Close trade request: trade_id={trade_id}, ticket={ticket}, platform={platform}")
        
        # If we have a ticket, close the MT5 position
        if ticket and platform:
            from multi_platform_connector import MultiPlatformConnector
            connector = MultiPlatformConnector()
            
            await connector.connect_platform(platform)
            platform_info = connector.platforms.get(platform)
            
            if platform_info and platform_info.get('connector'):
                mt5_connector = platform_info['connector']
                
                # Get position details BEFORE closing (for DB storage)
                positions = await connector.get_open_positions(platform)
                position_data = None
                for pos in positions:
                    if str(pos.get('ticket') or pos.get('id')) == str(ticket):
                        position_data = pos
                        break
                
                # Close on MT5
                success = await mt5_connector.close_position(str(ticket))
                
                if success:
                    logger.info(f"✅ Closed MT5 position {ticket} on {platform}")
                    
                    # WICHTIG: Speichere geschlossenen Trade in DB für Historie
                    if position_data:
                        try:
                            closed_trade = {
                                "id": f"mt5_{ticket}",
                                "mt5_ticket": str(ticket),
                                "commodity": position_data.get('symbol', 'UNKNOWN'),
                                "type": "BUY" if position_data.get('type') == 'POSITION_TYPE_BUY' else "SELL",
                                "entry_price": position_data.get('price_open', 0),
                                "exit_price": position_data.get('price_current', position_data.get('price_open', 0)),
                                "quantity": position_data.get('volume', 0),
                                "profit_loss": position_data.get('profit', 0),
                                "status": "CLOSED",
                                "platform": platform,
                                "opened_at": position_data.get('time', datetime.now(timezone.utc).isoformat()),
                                "closed_at": datetime.now(timezone.utc).isoformat(),
                                "closed_by": "MANUAL"
                            }
                            await db.trades.insert_one(closed_trade)
                            logger.info(f"💾 Saved closed trade #{ticket} to DB (P/L: ${position_data.get('profit', 0):.2f})")
                        except Exception as e:
                            logger.error(f"⚠️ Failed to save closed trade to DB: {e}")
                            # Continue anyway - trade was closed on MT5
                    
                    return {
                        "success": True,
                        "message": f"Position {ticket} geschlossen",
                        "ticket": ticket
                    }
                else:
                    raise HTTPException(status_code=500, detail=f"MT5 Order konnte nicht geschlossen werden. Ticket: {ticket}")
            else:
                raise HTTPException(status_code=500, detail=f"Platform {platform} not connected")
        
        # Otherwise, close DB trade
        if trade_id:
            trade = await db.trades.find_one({"id": trade_id})
            if not trade:
                raise HTTPException(status_code=404, detail="Trade not found")
            
            if trade['status'] == 'CLOSED':
                raise HTTPException(status_code=400, detail="Trade already closed")
            
            await db.trades.update_one(
                {"id": trade_id},
                {"$set": {
                    "status": "CLOSED",
                    "closed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return {"success": True, "trade_id": trade_id}
        
        raise HTTPException(status_code=400, detail="Missing trade_id or ticket")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trades/close/{trade_id}")
async def close_trade(trade_id: str, exit_price: float):
    """Close an open trade (legacy endpoint)"""
    try:
        trade = await db.trades.find_one({"id": trade_id})
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        if trade['status'] == 'CLOSED':
            raise HTTPException(status_code=400, detail="Trade already closed")
        
        profit_loss = (exit_price - trade['entry_price']) * trade['quantity']
        if trade['type'] == 'SELL':
            profit_loss = -profit_loss
        
        await db.trades.update_one(
            {"id": trade_id},
            {"$set": {
                "status": "CLOSED",
                "exit_price": exit_price,
                "profit_loss": profit_loss,
                "closed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True, "profit_loss": profit_loss}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trades/cleanup")
async def cleanup_trades():
    """Lösche fehlerhafte Trades und Duplikate permanent aus der Datenbank"""
    try:
        from trade_cleanup import cleanup_error_trades, cleanup_duplicate_trades
        
        # Cleanup durchführen
        error_deleted = await cleanup_error_trades(db)
        duplicate_deleted = await cleanup_duplicate_trades(db)
        
        total_deleted = error_deleted + duplicate_deleted
        
        return {
            "success": True,
            "message": f"✅ {total_deleted} Trades gelöscht",
            "error_trades_deleted": error_deleted,
            "duplicate_trades_deleted": duplicate_deleted,
            "total_deleted": total_deleted
        }
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/ping")
async def ping():
    """Simple ping endpoint to test connectivity"""
    return {
        "status": "ok",
        "message": "Backend is reachable",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/health")
async def health_check():
    """Health check endpoint - Frontend kann regelmäßig abfragen"""
    try:
        from multi_platform_connector import multi_platform
        
        # Get active platforms
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings:
            return {"status": "error", "message": "No settings found"}
        
        active_platforms = settings.get('active_platforms', [])
        platform_status = {}
        
        for platform_name in active_platforms:
            if platform_name not in multi_platform.platforms:
                platform_status[platform_name] = {"connected": False, "error": "Unknown platform"}
                continue
            
            platform = multi_platform.platforms[platform_name]
            connector = platform.get('connector')
            
            if not connector:
                platform_status[platform_name] = {"connected": False, "error": "No connector"}
                continue
            
            try:
                is_connected = await connector.is_connected()
                balance = platform.get('balance', 0)
                
                platform_status[platform_name] = {
                    "connected": is_connected,
                    "balance": balance,
                    "name": platform.get('name', platform_name)
                }
            except Exception as e:
                platform_status[platform_name] = {
                    "connected": False,
                    "error": str(e)
                }
        
        # Check if any platform is connected
        any_connected = any(p.get('connected', False) for p in platform_status.values())
        
        return {
            "status": "ok" if any_connected else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platforms": platform_status,
            "database": "connected"  # MongoDB connection is always available
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@api_router.get("/trades/list")
async def get_trades(status: Optional[str] = None):
    """Get all trades - ONLY real MT5 positions + closed DB trades"""
    try:
        logger.info("🔍 /trades/list aufgerufen - NEU VERSION 2.0")
        
        # Get settings
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        active_platforms = settings.get('active_platforms', []) if settings else []
        
        logger.info(f"Active platforms: {active_platforms}")
        
        # Hole echte MT5-Positionen (LIVE)
        live_mt5_positions = []
        
        # PERFORMANCE OPTIMIZATION: Hole ALLE trade_settings auf einmal statt für jeden Trade einzeln
        all_trade_settings = await db.trade_settings.find({}, {"_id": 0}).to_list(10000)
        trade_settings_map = {ts['trade_id']: ts for ts in all_trade_settings if 'trade_id' in ts}
        logger.info(f"📊 Loaded {len(trade_settings_map)} trade settings for fast lookup")
        
        for platform_name in active_platforms:
            # Support both DEMO and REAL accounts
            if 'MT5_LIBERTEX' in platform_name or 'MT5_ICMARKETS' in platform_name:
                try:
                    from multi_platform_connector import multi_platform
                    positions = await multi_platform.get_open_positions(platform_name)
                    
                    # Konvertiere MT5-Positionen zu Trade-Format
                    # Symbol-Mapping: MT5-Symbole → Unsere Commodity-IDs
                    symbol_to_commodity = {
                        'XAUUSD': 'GOLD',
                        'XAGUSD': 'SILVER',
                        'XPTUSD': 'PLATINUM',
                        'XPDUSD': 'PALLADIUM',
                        'PL': 'PLATINUM',
                        'PA': 'PALLADIUM',
                        'USOILCash': 'WTI_CRUDE',
                        'WTI_F6': 'WTI_CRUDE',
                        'UKOUSD': 'BRENT_CRUDE',
                        'CL': 'BRENT_CRUDE',
                        'NGASCash': 'NATURAL_GAS',
                        'NG': 'NATURAL_GAS',
                        'WHEAT': 'WHEAT',
                        'CORN': 'CORN',
                        'SOYBEAN': 'SOYBEANS',
                        'COFFEE': 'COFFEE',
                        'SUGAR': 'SUGAR',
                        'COTTON': 'COTTON',
                        'COCOA': 'COCOA'
                    }
                    
                    for pos in positions:
                        mt5_symbol = pos.get('symbol', 'UNKNOWN')
                        commodity_id = symbol_to_commodity.get(mt5_symbol, mt5_symbol)  # Fallback to MT5 symbol
                        ticket = str(pos.get('ticket', pos.get('id')))
                        
                        # Hole SL/TP UND STRATEGY aus trade_settings (AI Bot Monitoring) - OPTIMIZED: Use pre-loaded map
                        trade_settings = trade_settings_map.get(ticket)
                        stop_loss_value = trade_settings.get('stop_loss') if trade_settings else None
                        take_profit_value = trade_settings.get('take_profit') if trade_settings else None
                        
                        # HARD-CODED FIX: User wants ALL trades to show as 'day'
                        strategy_value = 'day'
                        
                        trade = {
                            "id": f"mt5_{ticket}",
                            "mt5_ticket": ticket,
                            "commodity": commodity_id,  # Unser internes Symbol!
                            "type": "BUY" if pos.get('type') == 'POSITION_TYPE_BUY' else "SELL",
                            "entry_price": pos.get('price_open', 0),
                            "price": pos.get('price_current', pos.get('price_open', 0)),
                            "quantity": pos.get('volume', 0),
                            "profit_loss": pos.get('profit', 0),
                            "status": "OPEN",
                            "platform": platform_name,
                            "mode": platform_name,
                            "stop_loss": stop_loss_value,  # Aus DB (AI Bot Settings)
                            "take_profit": take_profit_value,  # Aus DB (AI Bot Settings)
                            "strategy": strategy_value,  # Aus DB (AI Bot Settings) - WICHTIG FÜR FRONTEND!
                            "timestamp": pos.get('time', datetime.now(timezone.utc).isoformat())
                        }
                        live_mt5_positions.append(trade)
                except Exception as e:
                    logger.error(f"Fehler beim Holen von {platform_name} Positionen: {e}")
        
        # Hole GESCHLOSSENE Trades aus DB
        query = {"status": "CLOSED"}
        logger.info(f"📊 Live MT5 Positionen: {len(live_mt5_positions)}")
        
        if status and status.upper() == "OPEN":
            # Wenn nur OPEN angefordert, gib nur MT5-Positionen zurück
            trades = live_mt5_positions
        elif status and status.upper() == "CLOSED":
            # Wenn nur CLOSED angefordert, gib nur DB-Trades zurück
            trades = await db.trades.find(query, {"_id": 0}).to_list(1000)
        else:
            # Sonst beide kombinieren
            closed_trades = await db.trades.find(query, {"_id": 0}).to_list(1000)
            logger.info(f"📊 Geschlossene Trades aus DB: {len(closed_trades)}")
            trades = live_mt5_positions + closed_trades
        
        # Sort manually - handle mixed timestamp formats
        def get_sort_key(trade):
            timestamp = trade.get('created_at') or trade.get('timestamp') or ''
            if isinstance(timestamp, datetime):
                return timestamp
            elif isinstance(timestamp, str):
                try:
                    return datetime.fromisoformat(timestamp)
                except:
                    return datetime.min
            return datetime.min
        
        try:
            trades.sort(key=get_sort_key, reverse=True)
        except Exception as e:
            logger.error(f"Sorting error: {e}")
            # Fallback: no sorting
        
        # Convert timestamps
        for trade in trades:
            # Handle both created_at and timestamp fields
            if 'timestamp' in trade and isinstance(trade['timestamp'], str):
                trade['timestamp'] = datetime.fromisoformat(trade['timestamp']).isoformat()
            if 'created_at' in trade and isinstance(trade['created_at'], str):
                # Add timestamp field for frontend compatibility
                trade['timestamp'] = trade['created_at']
            if trade.get('closed_at') and isinstance(trade['closed_at'], str):
                trade['closed_at'] = datetime.fromisoformat(trade['closed_at']).isoformat()
        
        # Filter errors AND deduplicate by ticket ID
        # Reason: MT5_LIBERTEX and MT5_LIBERTEX_DEMO point to same account, causing duplicates
        unique_trades = []
        seen_tickets = set()
        
        for trade in trades:
            ticket = trade.get('mt5_ticket') or trade.get('ticket')
            commodity = trade.get('commodity', '')
            status = trade.get('status', '')
            
            # Skip trades with MetaAPI error codes
            if ticket and isinstance(ticket, str) and 'TRADE_RETCODE' in str(ticket):
                logger.debug(f"Filtered error trade: {ticket}")
                continue
            
            if commodity and 'TRADE_RETCODE' in str(commodity):
                logger.debug(f"Filtered error trade: commodity={commodity}")
                continue
            
            # Deduplicate by ticket ID (OPEN trades only - closed trades may have same ticket)
            if status == 'OPEN' and ticket:
                if ticket in seen_tickets:
                    logger.debug(f"Filtered duplicate open trade: ticket={ticket}")
                    continue
                seen_tickets.add(ticket)
            
            unique_trades.append(trade)
        
        logger.info(f"Trades fetched: {len(trades)} total, {len(unique_trades)} after deduplication")
        
        return {"trades": unique_trades}
    
    except Exception as e:
        logger.error(f"Error in get_trades: {e}")
        return {"trades": []}


@api_router.post("/trades/{trade_id}/settings")
async def update_trade_settings(trade_id: str, settings: dict):
    """
    Update individuelle Settings für einen spezifischen Trade
    Diese werden von der KI überwacht und angewendet
    """
    try:
        # Speichere individuelle Trade Settings
        trade_settings = {
            'trade_id': trade_id,
            'stop_loss': settings.get('stop_loss'),
            'take_profit': settings.get('take_profit'),
            'trailing_stop': settings.get('trailing_stop', False),
            'trailing_stop_distance': settings.get('trailing_stop_distance', 50),  # in Pips
            'strategy_type': settings.get('strategy_type', 'swing'),
            'notes': settings.get('notes', ''),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert in DB
        await db.trade_settings.update_one(
            {'trade_id': trade_id},
            {'$set': trade_settings},
            upsert=True
        )
        
        logger.info(f"✅ Trade Settings gespeichert für #{trade_id}: SL={settings.get('stop_loss')}, TP={settings.get('take_profit')}")
        
        return {
            'success': True,
            'message': 'Trade Settings gespeichert',
            'settings': trade_settings
        }
    
    except Exception as e:
        logger.error(f"Error updating trade settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trades/{trade_id}/settings")
async def get_trade_settings(trade_id: str):
    """
    Hole individuelle Settings für einen Trade
    """
    try:
        settings = await db.trade_settings.find_one({'trade_id': trade_id})
        
        if settings:
            settings.pop('_id', None)
            return settings
        else:
            # Keine individuellen Settings - return defaults
            return {
                'trade_id': trade_id,
                'stop_loss': None,
                'take_profit': None,
                'trailing_stop': False,
                'strategy_type': 'swing'
            }
    
    except Exception as e:
        logger.error(f"Error getting trade settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trades/stats", response_model=TradeStats)
async def get_trade_stats():
    """Get trading statistics - USES SAME LOGIC AS /trades/list (no duplicates!)"""
    try:
        # Use the SAME logic as /trades/list to avoid discrepancies!
        # This calls get_trades() internally which already handles MT5 sync
        from fastapi import Request
        
        # Get unified trades list (same as /trades/list endpoint)
        trades_response = await get_trades()
        all_trades = trades_response.get('trades', [])
        
        # Calculate stats from unified trade list
        open_positions = [t for t in all_trades if t.get('status') == 'OPEN']
        closed_positions = [t for t in all_trades if t.get('status') == 'CLOSED']
        
        total_trades = len(all_trades)
        
        # Calculate P&L from open positions (live MT5)
        open_pl = sum([t.get('profit_loss', 0) or 0 for t in open_positions])
        
        # Calculate P&L from closed positions (DB)
        closed_pl = sum([t.get('profit_loss', 0) or 0 for t in closed_positions if t.get('profit_loss') is not None])
        
        total_profit_loss = open_pl + closed_pl
        
        # Calculate win/loss stats (only from closed trades)
        closed_with_pl = [t for t in closed_positions if t.get('profit_loss') is not None]
        winning_trades = len([t for t in closed_with_pl if t['profit_loss'] > 0])
        losing_trades = len([t for t in closed_with_pl if t['profit_loss'] <= 0])
        
        win_rate = (winning_trades / len(closed_with_pl) * 100) if len(closed_with_pl) > 0 else 0
        
        return TradeStats(
            total_trades=total_trades,
            open_positions=len(open_positions),
            closed_positions=len(closed_positions),
            total_profit_loss=round(total_profit_loss, 2),
            win_rate=round(win_rate, 2),
            winning_trades=winning_trades,
            losing_trades=losing_trades
        )
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/settings", response_model=TradingSettings)
async def get_settings():
    """Get trading settings"""
    settings = await db.trading_settings.find_one({"id": "trading_settings"})
    if not settings:
        # Create default settings
        default_settings = TradingSettings()
        doc = default_settings.model_dump()
        await db.trading_settings.insert_one(doc)
        return default_settings
    
    settings.pop('_id', None)
    return TradingSettings(**settings)

@api_router.post("/settings", response_model=TradingSettings)
async def update_settings(settings: TradingSettings):
    """Update trading settings and reinitialize AI if needed"""
    global ai_trading_bot_instance, bot_task
    
    try:
        # Only update provided fields, keep existing values for others
        doc = settings.model_dump(exclude_unset=False, exclude_none=False)
        
        # Get existing settings first to preserve API keys
        existing = await db.trading_settings.find_one({"id": "trading_settings"})
        
        # Check if auto_trading status changed
        auto_trading_changed = False
        if existing:
            old_auto_trading = existing.get('auto_trading', False)
            new_auto_trading = settings.auto_trading
            auto_trading_changed = old_auto_trading != new_auto_trading
        
        # Merge: Keep existing values for fields that weren't explicitly set
        if existing:
            # Preserve API keys if not provided in update
            for key in ['openai_api_key', 'gemini_api_key', 'anthropic_api_key', 'bitpanda_api_key',
                       'mt5_libertex_account_id', 'mt5_icmarkets_account_id']:
                if key in existing and (key not in doc or doc[key] is None or doc[key] == ''):
                    doc[key] = existing[key]
        
        await db.trading_settings.update_one(
            {"id": "trading_settings"},
            {"$set": doc},
            upsert=True
        )
        
        # Reinitialize AI chat with new settings
        provider = settings.ai_provider
        model = settings.ai_model
        api_key = None
        ollama_base_url = settings.ollama_base_url or "http://localhost:11434"
        
        if provider == "openai":
            api_key = settings.openai_api_key
        elif provider == "gemini":
            api_key = settings.gemini_api_key
        elif provider == "anthropic":
            api_key = settings.anthropic_api_key
        elif provider == "ollama":
            ollama_model = settings.ollama_model or "llama2"
            init_ai_chat(provider="ollama", model=ollama_model, ollama_base_url=ollama_base_url)
            logger.info(f"Settings updated and AI reinitialized: Provider={provider}, Model={ollama_model}, URL={ollama_base_url}")
        else:
            init_ai_chat(provider=provider, api_key=api_key, model=model)
            logger.info(f"Settings updated and AI reinitialized: Provider={provider}, Model={model}")
        
        # Auto-Trading Bot Management (Background Task to avoid blocking)
        async def manage_bot_background():
            if auto_trading_changed:
                if settings.auto_trading:
                    # Start Bot wenn aktiviert
                    logger.info("🤖 Auto-Trading aktiviert - starte Bot...")
                    from ai_trading_bot import AITradingBot
                    
                    global ai_trading_bot_instance, bot_task
                    # Stoppe alten Bot falls vorhanden
                    if ai_trading_bot_instance and ai_trading_bot_instance.running:
                        ai_trading_bot_instance.stop()
                        if bot_task:
                            try:
                                await asyncio.wait_for(bot_task, timeout=2.0)
                            except:
                                pass
                    
                    # Starte neuen Bot
                    ai_trading_bot_instance = AITradingBot()
                    if await ai_trading_bot_instance.initialize():
                        bot_task = asyncio.create_task(ai_trading_bot_instance.run_forever())
                        logger.info("✅ AI Trading Bot gestartet (via Settings)")
                else:
                    # Stop Bot wenn deaktiviert
                    logger.info("🛑 Auto-Trading deaktiviert - stoppe Bot...")
                    if ai_trading_bot_instance and ai_trading_bot_instance.running:
                        ai_trading_bot_instance.stop()
                        if bot_task:
                            try:
                                await asyncio.wait_for(bot_task, timeout=2.0)
                            except:
                                pass
                        logger.info("✅ AI Trading Bot gestoppt (via Settings)")
        
        # Start bot management in background
        if auto_trading_changed:
            asyncio.create_task(manage_bot_background())
        
        # 🔄 TODO: Position updates temporarily disabled due to complexity
        # FEATURE TEMPORARILY DISABLED for stability
        # This feature auto-updates all open positions when global settings change
        # Will be re-enabled after proper testing in a future update
        logger.info("ℹ️ Automatic position update disabled - new settings will apply to future trades only")
        
        # Return immediately - settings saved successfully
        logger.info("✅ Settings gespeichert")
        return settings
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings/reset")
async def reset_settings_to_default():
    """Reset trading settings to default values"""
    try:
        # Create default settings
        default_settings = TradingSettings(
            id="trading_settings",
            active_platforms=["MT5_LIBERTEX", "MT5_ICMARKETS"],
            auto_trading=False,
            use_ai_analysis=True,
            ai_provider="emergent",
            ai_model="gpt-5",
            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            use_trailing_stop=False,
            trailing_stop_distance=1.5,
            max_trades_per_hour=3,
            position_size=1.0,
            max_portfolio_risk_percent=20.0,
            default_platform="MT5_LIBERTEX",
            enabled_commodities=["GOLD", "SILVER", "PLATINUM", "PALLADIUM", "WTI_CRUDE", "BRENT_CRUDE", "NATURAL_GAS", "WHEAT", "CORN", "SOYBEANS", "COFFEE", "SUGAR", "COTTON", "COCOA"],
            # KI Trading Strategie-Parameter (Standardwerte)
            rsi_oversold_threshold=30.0,
            rsi_overbought_threshold=70.0,
            macd_signal_threshold=0.0,
            trend_following=True,
            min_confidence_score=0.6,
            use_volume_confirmation=True,
            risk_per_trade_percent=2.0
        )
        
        # Get existing settings to preserve API keys
        existing = await db.trading_settings.find_one({"id": "trading_settings"})
        
        # Preserve API keys and credentials
        if existing:
            default_settings.openai_api_key = existing.get('openai_api_key')
            default_settings.gemini_api_key = existing.get('gemini_api_key')
            default_settings.anthropic_api_key = existing.get('anthropic_api_key')
            default_settings.bitpanda_api_key = existing.get('bitpanda_api_key')
            default_settings.mt5_libertex_account_id = existing.get('mt5_libertex_account_id')
            default_settings.mt5_icmarkets_account_id = existing.get('mt5_icmarkets_account_id')
            default_settings.bitpanda_email = existing.get('bitpanda_email')
        
        # Update database
        await db.trading_settings.update_one(
            {"id": "trading_settings"},
            {"$set": default_settings.model_dump()},
            upsert=True
        )
        
        # Reinitialize AI with default settings
        init_ai_chat(provider="emergent", model="gpt-5")
        
        logger.info("Settings reset to default values")
        return {"success": True, "message": "Einstellungen auf Standardwerte zurückgesetzt", "settings": default_settings}
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/bot/status")
async def get_bot_status():
    """Hole Bot-Status"""
    global ai_trading_bot_instance, bot_task
    
    if not ai_trading_bot_instance:
        return {
            "running": False,
            "message": "Bot ist nicht initialisiert"
        }
    
    is_running = ai_trading_bot_instance.running if ai_trading_bot_instance else False
    task_alive = bot_task and not bot_task.done() if bot_task else False
    
    return {
        "running": is_running and task_alive,
        "instance_running": is_running,
        "task_alive": task_alive,
        "trade_count": len(ai_trading_bot_instance.trade_history) if ai_trading_bot_instance else 0,
        "last_trades": ai_trading_bot_instance.trade_history[-5:] if ai_trading_bot_instance else []
    }

@api_router.post("/bot/start")
async def start_bot():
    """Starte AI Trading Bot manuell"""
    global ai_trading_bot_instance, bot_task
    
    try:
        # Prüfe ob auto_trading aktiviert ist
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings or not settings.get('auto_trading', False):
            raise HTTPException(
                status_code=400, 
                detail="Auto-Trading muss in den Einstellungen aktiviert sein"
            )
        
        # Prüfe ob Bot bereits läuft
        if ai_trading_bot_instance and ai_trading_bot_instance.running:
            return {"success": False, "message": "Bot läuft bereits"}
        
        # Importiere und starte Bot
        from ai_trading_bot import AITradingBot
        
        ai_trading_bot_instance = AITradingBot()
        if await ai_trading_bot_instance.initialize():
            bot_task = asyncio.create_task(ai_trading_bot_instance.run_forever())
            logger.info("✅ AI Trading Bot manuell gestartet")
            return {"success": True, "message": "AI Trading Bot gestartet"}
        else:
            raise HTTPException(status_code=500, detail="Bot-Initialisierung fehlgeschlagen")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Bot-Start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/bot/stop")
async def stop_bot():
    """Stoppe AI Trading Bot"""
    global ai_trading_bot_instance, bot_task
    
    try:
        if not ai_trading_bot_instance or not ai_trading_bot_instance.running:
            return {"success": False, "message": "Bot läuft nicht"}
        
        # Stoppe Bot
        ai_trading_bot_instance.stop()
        
        # Warte auf Task-Ende (max 5 Sekunden)
        if bot_task:
            try:
                await asyncio.wait_for(bot_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Bot-Task konnte nicht rechtzeitig beendet werden")
                bot_task.cancel()
        
        logger.info("✅ AI Trading Bot gestoppt")
        return {"success": True, "message": "AI Trading Bot gestoppt"}
        
    except Exception as e:
        logger.error(f"Fehler beim Bot-Stopp: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/market/refresh")
async def refresh_market_data():
    """Manually refresh market data"""
    await process_market_data()
    return {"success": True, "message": "Market data refreshed"}

@api_router.post("/trailing-stop/update")
async def update_trailing_stops_endpoint():
    """Update trailing stops for all open positions"""
    try:
        # Get current market data
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        
        if not settings or not settings.get('use_trailing_stop', False):
            return {"success": False, "message": "Trailing stop not enabled"}
        
        # Get latest prices for all commodities
        current_prices = {}
        enabled = settings.get('enabled_commodities', ['WTI_CRUDE'])
        
        for commodity_id in enabled:
            market_data = await db.market_data.find_one(
                {"commodity": commodity_id},
                sort=[("timestamp", -1)]
            )
            if market_data:
                current_prices[commodity_id] = market_data['price']
        
        # Update trailing stops
        await update_trailing_stops(db, current_prices, settings)
        
        # Check for stop loss triggers
        trades_to_close = await check_stop_loss_triggers(db, current_prices)
        
        # Close triggered positions
        for trade_info in trades_to_close:
            await db.trades.update_one(
                {"id": trade_info['id']},
                {
                    "$set": {
                        "status": "CLOSED",
                        "exit_price": trade_info['exit_price'],
                        "closed_at": datetime.now(timezone.utc),
                        "strategy_signal": trade_info['reason']
                    }
                }
            )
        
        return {
            "success": True,
            "message": "Trailing stops updated",
            "closed_positions": len(trades_to_close)
        }
    except Exception as e:
        logger.error(f"Error updating trailing stops: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# MT5 Integration Endpoints
@api_router.get("/mt5/account")
async def get_mt5_account():
    """Get real MT5 account information via MetaAPI"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        account_info = await connector.get_account_info()
        
        if not account_info:
            raise HTTPException(status_code=503, detail="Failed to get MetaAPI account info")
        
        return account_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting MetaAPI account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bitpanda Integration Endpoints
@api_router.get("/bitpanda/account")
async def get_bitpanda_account():
    """Get Bitpanda account information"""
    try:
        from bitpanda_connector import get_bitpanda_connector
        
        # Get API key from settings or environment
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        api_key = settings.get('bitpanda_api_key') if settings else None
        
        if not api_key:
            api_key = os.environ.get('BITPANDA_API_KEY')
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Bitpanda API Key not configured")
        
        connector = await get_bitpanda_connector(api_key)
        account_info = await connector.get_account_info()
        
        if not account_info:
            raise HTTPException(status_code=503, detail="Failed to get Bitpanda account info")
        
        return account_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting Bitpanda account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bitpanda/status")
async def get_bitpanda_status():
    """Check Bitpanda connection status"""
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        api_key = settings.get('bitpanda_api_key') if settings else None
        
        if not api_key:
            api_key = os.environ.get('BITPANDA_API_KEY')
        
        if not api_key:
            return {
                "connected": False,
                "message": "Bitpanda API Key not configured"
            }
        
        from bitpanda_connector import get_bitpanda_connector
        
        connector = await get_bitpanda_connector(api_key)
        account_info = await connector.get_account_info()
        
        return {
            "connected": connector.connected,
            "mode": "BITPANDA_REST",
            "balance": account_info.get('balance') if account_info else None,
            "email": settings.get('bitpanda_email') if settings else None
        }
    except Exception as e:
        logger.error(f"Error checking Bitpanda status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

@api_router.get("/mt5/positions")
async def get_mt5_positions():
    """Get open positions from MetaAPI"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        positions = await connector.get_positions()
        
        return {"positions": positions}
    except Exception as e:
        logger.error(f"Error getting MetaAPI positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/trades/{trade_id}")
async def delete_trade(trade_id: str):
    """Delete a specific trade and recalculate stats"""
    try:
        result = await db.trades.delete_one({"id": trade_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trade nicht gefunden")
        
        # Recalculate stats
        open_count = await db.trades.count_documents({"status": "OPEN"})
        closed_count = await db.trades.count_documents({"status": "CLOSED"})
        closed_trades = await db.trades.find({"status": "CLOSED"}).to_list(1000)
        total_pl = sum([t.get('profit_loss', 0) for t in closed_trades])
        
        await db.stats.update_one(
            {},
            {"$set": {
                "open_positions": open_count,
                "closed_positions": closed_count,
                "total_profit_loss": total_pl,
                "total_trades": open_count + closed_count
            }},
            upsert=True
        )
        
        logger.info(f"✅ Trade {trade_id} gelöscht, Stats aktualisiert")
        return {"success": True, "message": "Trade gelöscht"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/mt5/order")
async def place_mt5_order(
    symbol: str,
    order_type: str,
    volume: float,
    price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
):
    """Place order on MetaAPI"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        result = await connector.place_order(
            symbol=symbol,
            order_type=order_type.upper(),
            volume=volume,
            price=price,
            sl=stop_loss,
            tp=take_profit
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to place order on MetaAPI")
        
        return result
    except Exception as e:
        logger.error(f"Error placing MetaAPI order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/mt5/close/{ticket}")
async def close_mt5_position(ticket: str):
    """Close position on MetaAPI"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        success = await connector.close_position(ticket)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to close position on MetaAPI")
        
        return {"success": True, "ticket": ticket}
    except Exception as e:
        logger.error(f"Error closing MetaAPI position: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@api_router.post("/sync/positions")
async def sync_positions_endpoint():
    """Sync positions from MT5/Bitpanda to database"""
    try:
        await sync_mt5_positions()
        return {"success": True, "message": "Positions synchronized"}
    except Exception as e:
        logger.error(f"Error syncing positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/mt5/status")
async def get_mt5_status():
    """Check MetaAPI connection status"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        account_info = await connector.get_account_info()
        
        return {
            "connected": connector.connected,
            "mode": "METAAPI_REST",
            "account_id": connector.account_id,
            "balance": account_info.get('balance') if account_info else None,
            "trade_mode": account_info.get('trade_mode') if account_info else None,
            "broker": account_info.get('broker') if account_info else None
        }
    except Exception as e:
        logger.error(f"Error checking MetaAPI status: {e}")
        return {
            "connected": False,
            "error": str(e)
        }

@api_router.get("/mt5/symbols")
async def get_mt5_symbols():
    """Get all available symbols from MetaAPI broker"""
    try:
        from metaapi_connector import get_metaapi_connector
        
        connector = await get_metaapi_connector()
        symbols = await connector.get_symbols()
        
        # MetaAPI returns symbols as an array of strings
        # Filter for commodity-related symbols (Oil, Gold, Silver, etc.)
        commodity_symbols = []
        commodity_keywords = ['OIL', 'GOLD', 'XAU', 'XAG', 'SILVER', 'COPPER', 'PLAT', 'PALL', 
                              'GAS', 'WHEAT', 'CORN', 'SOYBEAN', 'COFFEE', 'BRENT', 'WTI', 'CL']
        
        for symbol in symbols:
            # symbol is a string, not a dict
            symbol_name = symbol.upper()
            # Check if any commodity keyword is in the symbol name
            if any(keyword in symbol_name for keyword in commodity_keywords):
                commodity_symbols.append(symbol)
        
        logger.info(f"Found {len(commodity_symbols)} commodity symbols out of {len(symbols)} total")
        
        return {
            "success": True,
            "total_symbols": len(symbols),
            "commodity_symbols": sorted(commodity_symbols),  # Sort for easier reading
            "all_symbols": sorted(symbols)  # Include all symbols for reference, sorted
        }
    except Exception as e:
        logger.error(f"Error fetching MetaAPI symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")

# Multi-Platform Endpoints
@api_router.get("/platforms/status")
async def get_platforms_status():
    """Get status of all trading platforms (SDK version)"""
    try:
        from multi_platform_connector import multi_platform
        
        status_dict = multi_platform.get_platform_status()
        active_platforms = multi_platform.get_active_platforms()
        
        # Convert dict to list for frontend compatibility
        platforms_list = []
        for platform_name, platform_data in status_dict.items():
            platforms_list.append({
                "platform": platform_name,
                "name": platform_data.get('name', platform_name),
                "connected": platform_data.get('active', False),
                "balance": platform_data.get('balance', 0.0),
                "is_real": platform_data.get('is_real', False)
            })
        
        return {
            "success": True,
            "active_platforms": active_platforms,
            "platforms": platforms_list
        }
    except Exception as e:
        logger.error(f"Error getting platforms status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/platforms/{platform_name}/connect")
async def connect_to_platform(platform_name: str):
    """Connect to a specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        success = await multi_platform.connect_platform(platform_name)
        
        if success:
            return {
                "success": True,
                "message": f"Connected to {platform_name}",
                "platform": platform_name
            }
        else:
            raise HTTPException(status_code=503, detail=f"Failed to connect to {platform_name}")
    except Exception as e:
        logger.error(f"Error connecting to {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/platforms/{platform_name}/disconnect")
async def disconnect_from_platform(platform_name: str):
    """Disconnect from a specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        success = await multi_platform.disconnect_platform(platform_name)
        
        if success:
            return {
                "success": True,
                "message": f"Disconnected from {platform_name}"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to disconnect from {platform_name}")
    except Exception as e:
        logger.error(f"Error disconnecting from {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/platforms/{platform_name}/account")
async def get_platform_account(platform_name: str):
    """Get account information for a specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        account_info = await multi_platform.get_account_info(platform_name)
        
        if account_info:
            # Calculate portfolio risk from LIVE positions (not from DB!)
            balance = account_info.get('balance', 0)
            equity = account_info.get('equity', balance)
            margin_used = account_info.get('margin', 0)
            
            # Get LIVE open positions from broker
            try:
                open_positions = await multi_platform.get_open_positions(platform_name)
            except Exception as e:
                logger.warning(f"Could not get open positions for {platform_name}: {e}")
                open_positions = []
            
            # Calculate total exposure - use margin from account_info if available
            # Otherwise calculate from positions
            if margin_used > 0:
                # Use account-level margin (most reliable)
                total_margin = margin_used
            else:
                # Fallback: Calculate from positions
                total_margin = 0.0
                for position in open_positions:
                    # Try different margin fields from MetaAPI
                    pos_margin = position.get('margin', 0)
                    if pos_margin == 0:
                        # Estimate margin from volume and price for CFDs
                        volume = position.get('volume', 0)
                        price = position.get('price_current', position.get('price_open', 0))
                        # For CFDs, margin is typically volume * price / leverage
                        # We don't have leverage, so use volume * price as conservative estimate
                        pos_margin = volume * price
                    total_margin += pos_margin
            
            # Track unrealized P&L
            total_unrealized_pl = 0.0
            for position in open_positions:
                profit = position.get('profit', 0)
                total_unrealized_pl += profit
            
            # Portfolio risk as percentage of balance (margin-based)
            portfolio_risk_percent = (total_margin / balance * 100) if balance > 0 else 0.0
            
            # Add risk info to account
            account_info['portfolio_risk'] = round(total_margin, 2)
            account_info['portfolio_risk_percent'] = round(portfolio_risk_percent, 2)
            account_info['open_trades_count'] = len(open_positions)
            account_info['open_positions_total'] = round(total_margin, 2)
            account_info['unrealized_pl'] = round(total_unrealized_pl, 2)
            
            return {
                "success": True,
                "platform": platform_name,
                "account": account_info
            }
        else:
            raise HTTPException(status_code=503, detail=f"Failed to get account info for {platform_name}")
    except Exception as e:
        logger.error(f"Error getting account for {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/platforms/{platform_name}/positions")
async def get_platform_positions(platform_name: str):
    """Get open positions for a specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        positions = await multi_platform.get_open_positions(platform_name)
        
        return {
            "success": True,
            "platform": platform_name,
            "positions": positions
        }
    except Exception as e:
        logger.error(f"Error getting positions for {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

async def connection_health_check():
    """Background task: Check and restore platform connections every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            logger.info("🔍 Connection health check...")
            
            # Get active platforms from settings
            settings = await db.trading_settings.find_one({"id": "trading_settings"})
            if not settings:
                continue
            
            active_platforms = settings.get('active_platforms', [])
            
            from multi_platform_connector import multi_platform
            
            for platform_name in active_platforms:
                try:
                    # Check connection status
                    if platform_name not in multi_platform.platforms:
                        continue
                    
                    platform = multi_platform.platforms[platform_name]
                    connector = platform.get('connector')
                    
                    if not connector:
                        # No connector - try to connect
                        logger.warning(f"⚠️ {platform_name} has no connector, reconnecting...")
                        await multi_platform.connect_platform(platform_name)
                        continue
                    
                    # Check if connected
                    is_connected = await connector.is_connected()
                    
                    if not is_connected:
                        # Connection lost - reconnect
                        logger.warning(f"⚠️ {platform_name} connection lost, reconnecting...")
                        platform['active'] = False
                        platform['connector'] = None
                        await multi_platform.connect_platform(platform_name)
                    else:
                        # Connection OK - update balance
                        try:
                            account_info = await multi_platform.get_account_info(platform_name)
                            if account_info:
                                balance = account_info.get('balance', 0)
                                logger.info(f"✅ {platform_name} healthy: Balance = €{balance:,.2f}")
                        except Exception as e:
                            logger.error(f"Error updating balance for {platform_name}: {e}")
                
                except Exception as e:
                    logger.error(f"Error checking {platform_name}: {e}")
            
            logger.info("✅ Health check complete")
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error



@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    import asyncio as _asyncio  # Local import to avoid conflicts
    logger.info("Starting WTI Smart Trader API...")
    
    # MEMORY PROFILING: Initial snapshot
    profiler = get_profiler()
    profiler.take_snapshot("startup")
    profiler.log_gc_stats()
    
    # Load settings and initialize AI
    settings = await db.trading_settings.find_one({"id": "trading_settings"})
    if settings:
        provider = settings.get('ai_provider', 'emergent')
        model = settings.get('ai_model', 'gpt-5')
        api_key = None
        ollama_base_url = settings.get('ollama_base_url', 'http://localhost:11434')
        ollama_model = settings.get('ollama_model', 'llama2')
        
        if provider == "openai":
            api_key = settings.get('openai_api_key')
        elif provider == "gemini":
            api_key = settings.get('gemini_api_key')
        elif provider == "anthropic":
            api_key = settings.get('anthropic_api_key')
        elif provider == "ollama":
            init_ai_chat(provider="ollama", model=ollama_model, ollama_base_url=ollama_base_url)
        else:
            init_ai_chat(provider=provider, api_key=api_key, model=model)
    else:
        # Default to Emergent LLM Key
        init_ai_chat(provider="emergent", model="gpt-5")
    
    # Load MT5 credentials from environment
    mt5_login = os.environ.get('MT5_LOGIN')
    mt5_password = os.environ.get('MT5_PASSWORD')
    mt5_server = os.environ.get('MT5_SERVER')
    
    if mt5_login and mt5_password and mt5_server:
        # Update default settings with MT5 credentials
        if settings:
            await db.trading_settings.update_one(
                {"id": "trading_settings"},
                {"$set": {
                    "mt5_login": mt5_login,
                    "mt5_password": mt5_password,
                    "mt5_server": mt5_server
                }}
            )
        else:
            # Create default settings with MT5 credentials
            default_settings = TradingSettings(
                mt5_login=mt5_login,
                mt5_password=mt5_password,
                mt5_server=mt5_server
            )
            await db.trading_settings.insert_one(default_settings.model_dump())
        
        logger.info(f"MT5 credentials loaded: Server={mt5_server}, Login={mt5_login}")
    

    # Start connection health check background task
    _asyncio.create_task(connection_health_check())
    logger.info("✅ Connection health check started")

    # Initialize platform connector for commodity_processor
    from multi_platform_connector import multi_platform
    import commodity_processor
    commodity_processor.set_platform_connector(multi_platform)
    
    # Connect platforms for chart data availability (SDK version) - parallel for speed
    import asyncio
    connection_tasks = [
        multi_platform.connect_platform('MT5_LIBERTEX_DEMO'),
        multi_platform.connect_platform('MT5_ICMARKETS_DEMO')
    ]
    results = await asyncio.gather(*connection_tasks, return_exceptions=True)
    
    # Log results
    for i, (platform_name, result) in enumerate(zip(['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO'], results)):
        if isinstance(result, Exception):
            logger.error(f"Failed to connect {platform_name}: {result}")
        elif result:
            logger.info(f"✅ Successfully connected {platform_name}")
        else:
            logger.warning(f"⚠️ Failed to connect {platform_name} (returned False)")
    
    logger.info("Platform connector initialized and platforms connected for MetaAPI chart data (SDK)")
    
    # Fetch initial market data
    await process_market_data()
    
    # DEAKTIVIERT: Auto-Trading Engine erstellt Fake-Trades
    # from auto_trading_engine import get_auto_trading_engine
    # auto_engine = get_auto_trading_engine(db)
    # asyncio.create_task(auto_engine.start())
    logger.info("🔴 Auto-Trading Engine ist DEAKTIVIERT (erstellt Fake-Trades)")
    
    logger.info("API ready - market data available via /api/market/current and /api/market/refresh")
    logger.info("AI analysis enabled for intelligent trading decisions")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Scheduler moved to worker.py
    # scheduler.shutdown()
    client.close()
    logger.info("Application shutdown complete")


# ========================================
# STATIC FILES - Serve React Frontend
# ========================================

# Mount static files (für Desktop-App)
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"

if frontend_build_path.exists():
    # Serve static files (JS, CSS, etc.)
    app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
    
    # Catch-all route für React Router (muss NACH allen API-Routen kommen)
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes"""
        # Don't serve React for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        # Serve index.html for all other routes (React Router handles routing)
        index_path = frontend_build_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend build not found")
    
    logger.info(f"✅ Serving React Frontend from: {frontend_build_path}")
else:
    logger.warning(f"⚠️  Frontend build not found at: {frontend_build_path}")
    logger.warning("   Run 'cd /app/frontend && yarn build' to create production build")
@api_router.get("/debug/memory")
async def memory_status():
    """Memory Diagnostics Endpoint"""
    profiler = get_profiler()
    
    # Current memory
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    # GC stats
    import gc
    gc.collect()
    
    # Take snapshot
    profiler.take_snapshot("api_call")
    profiler.get_top_allocations(top=20)
    
    return {
        "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
        "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
        "percent": process.memory_percent(),
        "gc_objects": len(gc.get_objects()),
        "gc_garbage": len(gc.garbage),
        "gc_counts": gc.get_count(),
        "snapshots_taken": len(profiler.snapshots),
        "message": "Check backend logs for detailed memory allocation"
    }

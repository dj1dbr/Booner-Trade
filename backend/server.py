from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import yfinance as yf
import pandas as pd
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import logging
import uuid
import asyncio

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Booner-Trade API", description="KI-gestützte Multi-Plattform Trading API mit autonomem Trading Bot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.rohstoff_trading

# Pydantic Models
class Commodity(BaseModel):
    id: str
    name: str
    symbol: str
    category: str
    platforms: List[str] = []

class TradingSettings(BaseModel):
    id: str = "trading_settings"
    mode: str = "MT5_LIBERTEX"  # Default platform
    default_platform: str = "MT5_LIBERTEX"  # For compatibility
    active_platforms: List[str] = []  # User-selected platforms
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    news_api_key: Optional[str] = None
    ai_provider: str = "emergent"
    ai_model: str = "gpt-5"
    use_ai_analysis: bool = True
    enabled_commodities: List[str] = []
    stop_loss_percent: float = 2.0
    take_profit_percent: float = 4.0
    risk_per_trade_percent: float = 2.0
    max_portfolio_risk_percent: float = 20.0
    confidence_threshold: int = 60
    auto_trading: bool = False
    min_confidence_percent: Optional[float] = 60.0  # Default-Wert setzen
    
    # Dual Trading Strategy Parameters
    swing_trading_enabled: bool = True
    swing_min_confidence_score: float = 0.6
    swing_stop_loss_percent: float = 2.0
    swing_take_profit_percent: float = 4.0
    swing_atr_multiplier_sl: float = 2.0
    swing_atr_multiplier_tp: float = 3.0
    swing_max_positions: int = 5
    swing_max_balance_percent: float = 80.0
    swing_max_hold_days: int = 7
    swing_analysis_interval_minutes: int = 10
    
    day_trading_enabled: bool = False
    day_min_confidence_score: float = 0.4
    day_stop_loss_percent: float = 0.5
    day_take_profit_percent: float = 0.8
    day_atr_multiplier_sl: float = 1.0
    day_atr_multiplier_tp: float = 1.5
    day_max_positions: int = 10
    day_max_balance_percent: float = 20.0
    day_max_hold_hours: int = 2
    day_analysis_interval_minutes: int = 1

class Trade(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    commodity: str
    type: str
    price: float
    quantity: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: str = "MT5_LIBERTEX"
    platform: str = "MT5_LIBERTEX"
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy_signal: Optional[str] = None
    ai_confidence: Optional[float] = None
    mt5_ticket: Optional[str] = None
    status: str = "OPEN"
    pnl: Optional[float] = None
    closed_at: Optional[datetime] = None
    close_reason: Optional[str] = None
    strategy_type: Optional[str] = None  # "swing" or "day"

class MarketData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    commodity: str
    price: float
    volume: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sma_20: Optional[float] = None
    ema_20: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    trend: Optional[str] = None
    signal: Optional[str] = None
    ai_signal: Optional[str] = None
    ai_confidence: Optional[float] = None

class TradeExecuteRequest(BaseModel):
    commodity: str
    trade_type: str
    price: float
    quantity: float = 1.0

class CloseTradeRequest(BaseModel):
    trade_id: Optional[str] = None
    ticket: Optional[str] = None
    platform: str = "MT5_LIBERTEX"

class BotStatusResponse(BaseModel):
    running: bool
    instance_running: bool
    task_alive: bool
    trade_count: Optional[int] = None

# Router
from fastapi import APIRouter
api_router = APIRouter(prefix="/api")

@app.get("/")
async def root():
    return {"message": "Booner-Trade API Running", "status": "ok"}

@api_router.get("/commodities", response_model=List[Commodity])
async def get_commodities():
    """Get all available commodities"""
    from commodity_processor import COMMODITIES
    return [
        Commodity(
            id=k,
            name=v['name'],
            symbol=v['symbol'],
            category=v.get('category', 'Commodity'),
            platforms=v.get('platforms', [])
        )
        for k, v in COMMODITIES.items()
    ]

@api_router.get("/settings")
async def get_settings():
    """Get trading settings"""
    settings = await db.trading_settings.find_one({"id": "trading_settings"})
    if not settings:
        default_settings = TradingSettings()
        settings = default_settings.model_dump()
        await db.trading_settings.insert_one(settings)
    
    settings.pop('_id', None)
    return settings

@api_router.post("/settings")
async def update_settings(settings: TradingSettings):
    """Update trading settings"""
    settings_dict = settings.model_dump()
    
    await db.trading_settings.update_one(
        {"id": "trading_settings"},
        {"$set": settings_dict},
        upsert=True
    )
    
    # Bot automatisch starten/stoppen basierend auf auto_trading
    try:
        from ai_trading_bot import bot_manager
        if settings.auto_trading:
            if not bot_manager.is_running():
                await bot_manager.start()
                logger.info("🤖 Bot automatisch gestartet (auto_trading=True)")
        else:
            if bot_manager.is_running():
                await bot_manager.stop()
                logger.info("🛑 Bot automatisch gestoppt (auto_trading=False)")
    except ImportError:
        logger.warning("Bot Manager nicht verfügbar - auto_trading ignoriert")
    
    return {"success": True, "message": "Settings updated"}

@api_router.get("/market/all")
async def get_all_market_data():
    """Get latest market data for all commodities"""
    markets_dict = {}
    
    from commodity_processor import COMMODITIES
    for commodity_id in COMMODITIES.keys():
        data = await db.market_data.find_one(
            {"commodity": commodity_id},
            sort=[("timestamp", -1)]
        )
        if data:
            data.pop('_id', None)
            markets_dict[commodity_id] = data
    
    return {"markets": markets_dict}

@api_router.get("/market/live-ticks")
async def get_live_ticks():
    """Get live tick prices from MetaAPI platforms"""
    try:
        from multi_platform_connector import multi_platform
        from commodity_processor import COMMODITIES
        
        live_prices = {}
        
        # Try to get live prices from connected platforms
        for platform_name in ['MT5_LIBERTEX', 'MT5_ICMARKETS']:
            try:
                await multi_platform.connect_platform(platform_name)
                
                if platform_name in multi_platform.platforms:
                    connector = multi_platform.platforms[platform_name].get('connector')
                    if connector:
                        # Get prices for each commodity
                        for commodity_id, commodity_info in COMMODITIES.items():
                            # Get the right symbol for this platform
                            if platform_name == 'MT5_LIBERTEX':
                                symbol = commodity_info.get('mt5_libertex_symbol')
                            else:
                                symbol = commodity_info.get('mt5_icmarkets_symbol')
                            
                            if symbol:
                                try:
                                    price_info = await connector.get_symbol_price(symbol)
                                    if price_info:
                                        live_prices[commodity_id] = {
                                            'price': price_info.get('ask', price_info.get('price', 0)),
                                            'bid': price_info.get('bid', 0),
                                            'ask': price_info.get('ask', 0),
                                            'time': price_info.get('time', datetime.now(timezone.utc).isoformat()),
                                            'symbol': symbol,
                                            'platform': platform_name
                                        }
                                        break  # Found price, no need to check other platforms
                                except:
                                    continue
            except:
                continue
        
        return {"live_prices": live_prices}
    
    except Exception as e:
        logger.error(f"Error getting live ticks: {e}")
        return {"live_prices": {}}

@api_router.get("/market/current")
async def get_current_market_data():
    """Get current market data (alias for /market/all)"""
    return await get_all_market_data()

@api_router.get("/market/history")
async def get_market_history(limit: int = 50):
    """Get historical market data entries"""
    try:
        cursor = db.market_data.find().sort("timestamp", -1).limit(limit)
        history = await cursor.to_list(length=limit)
        
        for item in history:
            item.pop('_id', None)
        
        return history
    except Exception as e:
        logger.error(f"Error getting market history: {e}")
        return []

@api_router.post("/market/refresh")
async def refresh_market_data():
    """Manually refresh market data for all commodities"""
    try:
        from commodity_processor import COMMODITIES
        
        refreshed = []
        for commodity_id in COMMODITIES.keys():
            try:
                # Trigger analysis which updates market data
                result = await analyze_commodity(commodity_id)
                refreshed.append(commodity_id)
            except:
                continue
        
        return {"success": True, "refreshed": refreshed}
    except Exception as e:
        logger.error(f"Error refreshing market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/market/{commodity_id}")
async def get_market_data(commodity_id: str, period: str = "1d"):
    """Get market data for a specific commodity"""
    from commodity_processor import COMMODITIES
    
    if commodity_id not in COMMODITIES:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    commodity = COMMODITIES[commodity_id]
    
    period_map = {
        "1d": "1d",
        "5d": "5d",
        "1mo": "1mo",
        "3mo": "3mo",
        "6mo": "6mo",
        "1y": "1y",
        "2y": "2y",
        "5y": "5y",
        "max": "max"
    }
    
    yf_period = period_map.get(period, "1d")
    
    try:
        ticker = yf.Ticker(commodity['symbol'])
        df = ticker.history(period=yf_period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        df = df.reset_index()
        
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                "date": row['Date'].isoformat(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": float(row['Volume']) if not pd.isna(row['Volume']) else 0
            })
        
        latest = df.iloc[-1]
        
        return {
            "commodity": commodity_id,
            "name": commodity['name'],
            "symbol": commodity['symbol'],
            "current_price": float(latest['Close']),
            "chart_data": chart_data,
            "period": period
        }
    
    except Exception as e:
        logger.error(f"Error fetching market data for {commodity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/market/{commodity_id}/analyze")
async def analyze_commodity(commodity_id: str):
    """Analyze a commodity and generate trading signal with AI"""
    from commodity_processor import COMMODITIES
    
    if commodity_id not in COMMODITIES:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    commodity = COMMODITIES[commodity_id]
    
    try:
        ticker = yf.Ticker(commodity['symbol'])
        df = ticker.history(period="3mo")
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        latest = df.iloc[-1]
        
        trend = "NEUTRAL"
        if latest['Close'] > latest['SMA_20'] and latest['RSI'] < 70:
            trend = "BULLISH"
        elif latest['Close'] < latest['SMA_20'] and latest['RSI'] > 30:
            trend = "BEARISH"
        
        signal = "HOLD"
        if latest['RSI'] < 30 and latest['MACD'] > latest['MACD_signal']:
            signal = "BUY"
        elif latest['RSI'] > 70 and latest['MACD'] < latest['MACD_signal']:
            signal = "SELL"
        
        # AI Analysis
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        use_ai = settings.get('use_ai_analysis', True) if settings else True
        ai_chat = settings.get('ai_provider') if settings else None
        
        ai_signal = signal
        ai_confidence = 0
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
        
        # Auto-Execute Trade if signal is strong (optional)
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if settings and settings.get('auto_trading'):
            if signal in ['BUY', 'SELL']:
                await execute_trade_logic(signal, market_data.price, settings, commodity_id)
        
        return market_data
    
    except Exception as e:
        logger.error(f"Error analyzing {commodity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/market/ohlcv/{commodity_id}")
async def get_market_ohlcv(commodity_id: str, timeframe: str = "1d", period: str = "1mo"):
    """Get OHLCV (candlestick) data for charts"""
    from commodity_processor import COMMODITIES
    
    if commodity_id not in COMMODITIES:
        raise HTTPException(status_code=404, detail="Commodity not found")
    
    commodity = COMMODITIES[commodity_id]
    
    try:
        ticker = yf.Ticker(commodity['symbol'])
        df = ticker.history(period=period)
        
        if df.empty:
            return {"success": False, "data": [], "error": "No data available"}
        
        df = df.reset_index()
        
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                "time": row['Date'].isoformat(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": float(row['Volume']) if not pd.isna(row['Volume']) else 0
            })
        
        return {"success": True, "data": chart_data, "commodity": commodity_id}
    
    except Exception as e:
        logger.error(f"Error fetching OHLCV data for {commodity_id}: {e}")
        return {"success": False, "data": [], "error": str(e)}

@api_router.get("/market/ohlcv-simple/{commodity_id}")
async def get_market_ohlcv_simple(commodity_id: str, timeframe: str = "1d", period: str = "1mo"):
    """Simple OHLCV endpoint using yfinance - fallback when MetaAPI quota exceeded"""
    return await get_market_ohlcv(commodity_id, timeframe, period)

async def execute_trade_logic(signal, price, settings, commodity_id='WTI_CRUDE'):
    """Auto-execute trade based on signal"""
    try:
        quantity = 0.01
        
        trade_type = "BUY" if signal == "BUY" else "SELL"
        
        sl_percent = settings.get('stop_loss_percent', 2.0)
        tp_percent = settings.get('take_profit_percent', 0.2)
        
        if trade_type == 'BUY':
            stop_loss = price * (1 - sl_percent / 100)
            take_profit = price * (1 + tp_percent / 100)
        else:
            stop_loss = price * (1 + sl_percent / 100)
            take_profit = price * (1 - tp_percent / 100)
        
        trade = Trade(
            commodity=commodity_id,
            type=trade_type,
            price=price,
            quantity=quantity,
            mode=settings.get('mode', 'MT5_LIBERTEX'),
            platform=settings.get('default_platform', 'MT5_LIBERTEX'),
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy_signal=f"Auto-{signal}",
            status="OPEN"
        )
        
        doc = trade.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.trades.insert_one(doc)
        
        logger.info(f"Auto-executed {trade_type} for {commodity_id} @ {price}")
    
    except Exception as e:
        logger.error(f"Error auto-executing trade: {e}")

async def get_ai_analysis(latest_data, df, commodity_id):
    """Get AI analysis for trading signal"""
    try:
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings:
            return None
        
        provider = settings.get('ai_provider', 'emergent')
        model = settings.get('ai_model', 'gpt-5')
        
        if provider != 'emergent':
            return None
        
        prompt = f"""
You are a professional commodity trader. Analyze this market data and provide a trading recommendation.

Commodity: {commodity_id}
Current Price: {latest_data['Close']}
RSI: {latest_data.get('RSI', 'N/A')}
MACD: {latest_data.get('MACD', 'N/A')}
SMA_20: {latest_data.get('SMA_20', 'N/A')}

Provide your analysis in JSON format:
{{
  "signal": "BUY" or "SELL" or "HOLD",
  "confidence": 0-100,
  "reasoning": "Brief explanation"
}}
"""
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting AI analysis: {e}")
        return None

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
                        detail=f"{commodity_info.get('name', commodity)} ist auf MT5 nicht verfügbar. Nutzen Sie eine andere Plattform für diesen Rohstoff oder wählen Sie einen verfügbaren Rohstoff."
                    )
                
                # Get the correct platform connector
                await multi_platform.connect_platform(default_platform)
                
                if default_platform not in multi_platform.platforms:
                    raise HTTPException(status_code=503, detail=f"{default_platform} ist nicht verbunden")
                
                connector = multi_platform.platforms[default_platform].get('connector')
                if not connector:
                    raise HTTPException(status_code=503, detail=f"{default_platform} Connector nicht verfügbar")
                
                # ⚡ IMMER OHNE MT5 SL/TP - KI ÜBERWACHT ALLES!
                logger.info(f"💡 Öffne Trade OHNE MT5 SL/TP - KI übernimmt Überwachung!")
                logger.info(f"📊 KI wird überwachen: SL={stop_loss}, TP={take_profit}")
                
                result = await connector.create_market_order(
                    symbol=mt5_symbol,
                    order_type=trade_type.upper(),
                    volume=quantity,
                    sl=None,  # IMMER None - KI überwacht!
                    tp=None   # IMMER None - KI überwacht!
                )
                
                # ROBUSTERE ERFOLGSPRÜFUNG
                logger.info(f"📥 SDK Response Type: {type(result)}")
                logger.info(f"📥 SDK Response: {result}")
                
                # Erfolg prüfen: Entweder result['success'] == True ODER result hat orderId/positionId
                success = False
                if result:
                    # Methode 1: Expliziter success key
                    if isinstance(result, dict) and result.get('success') == True:
                        success = True
                    # Methode 2: Vorhandensein von orderId oder positionId (impliziter Erfolg)
                    elif isinstance(result, dict) and (result.get('orderId') or result.get('positionId')):
                        success = True
                        logger.info(f"✅ Trade erfolgreich (implizit via orderId/positionId)")
                    # Methode 3: Result ist ein Objekt mit Attributen
                    elif hasattr(result, 'orderId') or hasattr(result, 'positionId'):
                        success = True
                        logger.info(f"✅ Trade erfolgreich (Object mit orderId/positionId)")
                
                if success:
                    # SDK gibt orderId/positionId zurück
                    if isinstance(result, dict):
                        platform_ticket = result.get('orderId') or result.get('positionId')
                    else:
                        platform_ticket = getattr(result, 'orderId', None) or getattr(result, 'positionId', None)
                    
                    logger.info(f"✅ Order an {default_platform} gesendet: Ticket #{platform_ticket}")
                else:
                    # Fehlerfall
                    if isinstance(result, dict):
                        error_msg = result.get('error', 'Unknown error')
                    else:
                        error_msg = 'SDK returned unexpected format'
                    
                    logger.error(f"❌ {default_platform} Order fehlgeschlagen: {error_msg}")
                    raise HTTPException(status_code=500, detail=f"{default_platform} Order failed: {error_msg}")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ Fehler beim Senden an MT5: {e}", exc_info=True)
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
                
                result = await connector.place_order(
                    symbol=bitpanda_symbol,
                    order_type=trade_type.upper(),
                    volume=quantity,
                    price=price,
                    sl=stop_loss,
                    tp=take_profit
                )
                
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
        
        # Nur speichern wenn Order erfolgreich
        if platform_ticket:
            trade = Trade(
                commodity=commodity,
                type=trade_type.upper(),
                price=price,
                quantity=quantity,
                mode=default_platform,
                platform=default_platform,
                entry_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_signal=f"Manual - {default_platform} #{platform_ticket}",
                mt5_ticket=str(platform_ticket),  # ← WICHTIG!
                status="OPEN"  # Explizit setzen
            )
            
            doc = trade.model_dump()
            doc['timestamp'] = doc['timestamp'].isoformat()
            await db.trades.insert_one(doc)
            
            logger.info(f"✅ Trade gespeichert: {trade_type} {quantity:.4f} {commodity} @ {price}")
            
            # MongoDB _id entfernen für JSON Response
            doc.pop('_id', None)
            
            return {"success": True, "trade": doc, "ticket": platform_ticket, "platform": default_platform}
        else:
            logger.error(f"❌ Trade fehlgeschlagen: platform_ticket ist None")
            raise HTTPException(status_code=500, detail="Trade konnte nicht ausgeführt werden - Broker hat Order abgelehnt. Prüfen Sie ob der Markt geöffnet ist.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing manual trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/trades/close")
async def close_trade_v2(request: CloseTradeRequest):
    """Close an open trade - supports both DB trades and MT5 positions"""
    try:
        trade_id = request.trade_id
        ticket = request.ticket
        platform = request.platform
        
        logger.info(f"Close trade request: trade_id={trade_id}, ticket={ticket}, platform={platform}")
        
        # Close on Trading Platform
        if platform in ['MT5_LIBERTEX', 'MT5_ICMARKETS']:
            try:
                from multi_platform_connector import multi_platform
                await multi_platform.connect_platform(platform)
                
                if platform not in multi_platform.platforms:
                    raise HTTPException(status_code=503, detail=f"{platform} ist nicht verbunden")
                
                connector = multi_platform.platforms[platform].get('connector')
                if not connector:
                    raise HTTPException(status_code=503, detail=f"{platform} Connector nicht verfügbar")
                
                # Close position on MT5
                success = await connector.close_position(ticket)
                
                if not success:
                    logger.error(f"Failed to close position {ticket} on {platform}")
                    raise HTTPException(status_code=500, detail=f"Failed to close position on {platform}")
                
                logger.info(f"✅ Position {ticket} closed on {platform}")
                
            except Exception as e:
                logger.error(f"Error closing position on {platform}: {e}")
                raise HTTPException(status_code=500, detail=f"Error closing position: {str(e)}")
        
        # Update trade in database
        if trade_id:
            result = await db.trades.update_one(
                {"id": trade_id},
                {
                    "$set": {
                        "status": "CLOSED",
                        "closed_at": datetime.now(timezone.utc).isoformat(),
                        "close_reason": "Manual close"
                    }
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"Trade {trade_id} not found in database")
        
        return {"success": True, "message": "Trade closed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trades/list")
async def list_trades():
    """List all trades: OPEN from MT5 live, CLOSED from database"""
    try:
        from multi_platform_connector import multi_platform
        
        all_trades = []
        
        # 1. Get OPEN positions from MT5 platforms (LIVE data)
        for platform_name in ['MT5_LIBERTEX', 'MT5_ICMARKETS']:
            try:
                if platform_name in multi_platform.platforms:
                    connector = multi_platform.platforms[platform_name].get('connector')
                    if connector:
                        positions = await connector.get_positions()
                        
                        # Convert MT5 positions to trade format
                        for pos in positions:
                            all_trades.append({
                                'id': pos.get('positionId') or pos.get('ticket'),
                                'commodity': pos.get('symbol', 'UNKNOWN'),
                                'type': pos.get('type', '').replace('POSITION_TYPE_', ''),
                                'price': pos.get('openPrice') or pos.get('price_open'),
                                'quantity': pos.get('volume'),
                                'timestamp': pos.get('time') or pos.get('openTime'),
                                'platform': platform_name,
                                'entry_price': pos.get('openPrice') or pos.get('price_open'),
                                'current_price': pos.get('currentPrice') or pos.get('price_current'),
                                'stop_loss': pos.get('stopLoss') or pos.get('sl'),
                                'take_profit': pos.get('takeProfit') or pos.get('tp'),
                                'mt5_ticket': str(pos.get('positionId') or pos.get('ticket')),
                                'status': 'OPEN',
                                'pnl': pos.get('profit') or pos.get('unrealizedProfit'),
                                'swap': pos.get('swap'),
                                'magic': pos.get('magic')
                            })
            except Exception as e:
                logger.error(f"Error fetching positions from {platform_name}: {e}")
        
        # 2. Get CLOSED trades from database
        closed_trades = await db.trades.find({'status': 'CLOSED'}).to_list(length=None)
        
        for trade in closed_trades:
            trade.pop('_id', None)
            if isinstance(trade.get('timestamp'), str):
                pass
            elif hasattr(trade.get('timestamp'), 'isoformat'):
                trade['timestamp'] = trade['timestamp'].isoformat()
            
            if isinstance(trade.get('closed_at'), str):
                pass
            elif trade.get('closed_at') and hasattr(trade['closed_at'], 'isoformat'):
                trade['closed_at'] = trade['closed_at'].isoformat()
            
            all_trades.append(trade)
        
        logger.info(f"📊 Returning {len(all_trades)} trades: {sum(1 for t in all_trades if t.get('status') == 'OPEN')} open, {len(closed_trades)} closed")
        
        return {"trades": all_trades, "count": len(all_trades)}
    
    except Exception as e:
        logger.error(f"Error listing trades: {e}")
        return {"trades": [], "count": 0}

@api_router.get("/trades/stats")
async def get_trade_stats():
    """Get trading statistics"""
    try:
        # Get all trades
        all_trades = await db.trades.find().to_list(length=None)
        
        # Calculate stats
        total_trades = len(all_trades)
        open_trades = [t for t in all_trades if t.get('status') == 'OPEN']
        closed_trades = [t for t in all_trades if t.get('status') == 'CLOSED']
        
        # Calculate P&L for closed trades
        total_pnl = sum([t.get('pnl', 0) for t in closed_trades if t.get('pnl')])
        
        # Win rate
        winning_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        
        # Platform breakdown
        platform_stats = {}
        for trade in all_trades:
            platform = trade.get('platform', 'UNKNOWN')
            if platform not in platform_stats:
                platform_stats[platform] = {'total': 0, 'open': 0, 'closed': 0}
            platform_stats[platform]['total'] += 1
            if trade.get('status') == 'OPEN':
                platform_stats[platform]['open'] += 1
            else:
                platform_stats[platform]['closed'] += 1
        
        return {
            'total_trades': total_trades,
            'open_trades': len(open_trades),
            'closed_trades': len(closed_trades),
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'platform_stats': platform_stats
        }
    
    except Exception as e:
        logger.error(f"Error getting trade stats: {e}")
        return {
            'total_trades': 0,
            'open_trades': 0,
            'closed_trades': 0,
            'total_pnl': 0,
            'win_rate': 0,
            'platform_stats': {}
        }


# Multi-Platform Endpoints
@api_router.get("/platforms/status")
async def get_platforms_status():
    """Get connection status of all platforms - FAST version using cached data"""
    try:
        from multi_platform_connector import multi_platform
        
        platforms = []
        
        # MT5 Libertex - Check if already connected
        try:
            if 'MT5_LIBERTEX' in multi_platform.platforms:
                connector = multi_platform.platforms['MT5_LIBERTEX'].get('connector')
                if connector and hasattr(connector, '_cached_account_info'):
                    # Use cached account info for fast response
                    account_info = connector._cached_account_info
                    platforms.append({
                        'name': 'MT5_LIBERTEX',
                        'connected': True,
                        'balance': account_info.get('balance', 0) if account_info else 0,
                        'equity': account_info.get('equity', 0) if account_info else 0,
                        'leverage': account_info.get('leverage', 0) if account_info else 0,
                        'free_margin': account_info.get('free_margin', 0) if account_info else 0
                    })
                else:
                    # Try quick account fetch with timeout
                    try:
                        account_info = await asyncio.wait_for(connector.get_account_info(), timeout=3.0)
                        platforms.append({
                            'name': 'MT5_LIBERTEX',
                            'connected': True,
                            'balance': account_info.get('balance', 0) if account_info else 0,
                            'equity': account_info.get('equity', 0) if account_info else 0,
                            'leverage': account_info.get('leverage', 0) if account_info else 0,
                            'free_margin': account_info.get('free_margin', 0) if account_info else 0
                        })
                    except:
                        platforms.append({'name': 'MT5_LIBERTEX', 'connected': False, 'balance': 0})
            else:
                platforms.append({'name': 'MT5_LIBERTEX', 'connected': False, 'balance': 0})
        except Exception as e:
            logger.error(f"Error getting MT5_LIBERTEX status: {e}")
            platforms.append({'name': 'MT5_LIBERTEX', 'connected': False, 'error': str(e), 'balance': 0})
        
        # MT5 ICMarkets - Check if already connected
        try:
            if 'MT5_ICMARKETS' in multi_platform.platforms:
                connector = multi_platform.platforms['MT5_ICMARKETS'].get('connector')
                if connector and hasattr(connector, '_cached_account_info'):
                    # Use cached account info for fast response
                    account_info = connector._cached_account_info
                    platforms.append({
                        'name': 'MT5_ICMARKETS',
                        'connected': True,
                        'balance': account_info.get('balance', 0) if account_info else 0,
                        'equity': account_info.get('equity', 0) if account_info else 0,
                        'leverage': account_info.get('leverage', 0) if account_info else 0,
                        'free_margin': account_info.get('free_margin', 0) if account_info else 0
                    })
                else:
                    # Try quick account fetch with timeout
                    try:
                        account_info = await asyncio.wait_for(connector.get_account_info(), timeout=3.0)
                        platforms.append({
                            'name': 'MT5_ICMARKETS',
                            'connected': True,
                            'balance': account_info.get('balance', 0) if account_info else 0,
                            'equity': account_info.get('equity', 0) if account_info else 0,
                            'leverage': account_info.get('leverage', 0) if account_info else 0,
                            'free_margin': account_info.get('free_margin', 0) if account_info else 0
                        })
                    except:
                        platforms.append({'name': 'MT5_ICMARKETS', 'connected': False, 'balance': 0})
            else:
                platforms.append({'name': 'MT5_ICMARKETS', 'connected': False, 'balance': 0})
        except Exception as e:
            logger.error(f"Error getting MT5_ICMARKETS status: {e}")
            platforms.append({'name': 'MT5_ICMARKETS', 'connected': False, 'error': str(e), 'balance': 0})
        
        return {'platforms': platforms}
        
    except Exception as e:
        logger.error(f"Error getting platforms status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/platforms/{platform_name}/account")
async def get_platform_account(platform_name: str):
    """Get account info for specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        await multi_platform.connect_platform(platform_name)
        
        if platform_name not in multi_platform.platforms:
            raise HTTPException(status_code=404, detail=f"Platform {platform_name} not found or not connected")
        
        connector = multi_platform.platforms[platform_name].get('connector')
        if not connector:
            raise HTTPException(status_code=503, detail=f"{platform_name} Connector not available")
        
        account_info = await connector.get_account_info()
        
        if not account_info:
            raise HTTPException(status_code=503, detail=f"Could not retrieve account info from {platform_name}")
        
        return {'account': account_info, 'platform': platform_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account info for {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/platforms/{platform_name}/positions")
async def get_platform_positions(platform_name: str):
    """Get open positions for specific platform"""
    try:
        from multi_platform_connector import multi_platform
        
        await multi_platform.connect_platform(platform_name)
        
        if platform_name not in multi_platform.platforms:
            raise HTTPException(status_code=404, detail=f"Platform {platform_name} not found")
        
        connector = multi_platform.platforms[platform_name].get('connector')
        if not connector:
            raise HTTPException(status_code=503, detail=f"{platform_name} Connector not available")
        
        positions = await connector.get_positions()
        
        return {'positions': positions, 'platform': platform_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting positions for {platform_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bot Management Endpoints
@api_router.get("/bot/status", response_model=BotStatusResponse)
async def get_bot_status():
    """Get AI Trading Bot status"""
    try:
        from ai_trading_bot import bot_manager
        
        is_running = bot_manager.is_running()
        instance_running = bot_manager.bot is not None
        task_alive = bot_manager.bot_task is not None and not bot_manager.bot_task.done() if bot_manager.bot_task else False
        
        # Get trade count
        trade_count = await db.trades.count_documents({"status": "OPEN"})
        
        return BotStatusResponse(
            running=is_running,
            instance_running=instance_running,
            task_alive=task_alive,
            trade_count=trade_count
        )
    except ImportError:
        # Bot manager not available
        trade_count = await db.trades.count_documents({"status": "OPEN"})
        return BotStatusResponse(
            running=False,
            instance_running=False,
            task_alive=False,
            trade_count=trade_count
        )

@api_router.post("/bot/start")
async def start_bot():
    """Start AI Trading Bot"""
    try:
        from ai_trading_bot import bot_manager
        
        # Check if auto_trading is enabled
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        if not settings or not settings.get('auto_trading', False):
            raise HTTPException(
                status_code=400, 
                detail="Auto-Trading ist deaktiviert. Bitte aktivieren Sie Auto-Trading in den Einstellungen."
            )
        
        if bot_manager.is_running():
            return {"success": False, "message": "Bot läuft bereits"}
        
        await bot_manager.start()
        return {"success": True, "message": "AI Trading Bot gestartet"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Bot Manager nicht verfügbar")

@api_router.post("/bot/stop")
async def stop_bot():
    """Stop AI Trading Bot"""
    try:
        from ai_trading_bot import bot_manager
        
        if not bot_manager.is_running():
            return {"success": False, "message": "Bot läuft nicht"}
        
        await bot_manager.stop()
        return {"success": True, "message": "AI Trading Bot gestoppt"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Bot Manager nicht verfügbar")

# AI Chat Endpoint
@api_router.post("/ai-chat")
async def ai_chat(request: dict):
    """AI Chat endpoint"""
    try:
        message = request.get('message', '')
        session_id = request.get('session_id', 'default')
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Get settings for AI provider/model
        settings = await db.trading_settings.find_one({"id": "trading_settings"})
        
        # Priority: URL params > User Settings > Defaults
        provider = request.get('provider') or (settings.get('ai_provider') if settings else None) or 'emergent'
        model = request.get('model') or (settings.get('ai_model') if settings else None) or 'gpt-5'
        
        logger.info(f"AI Chat: Using provider={provider}, model={model} (from settings)")
        
        # Get AI response
        from ai_chat_service import get_ai_response
        response = await get_ai_response(
            message=message,
            session_id=session_id,
            provider=provider,
            model=model,
            db=db
        )
        
        return {"response": response, "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🚀 Booner-Trade API Starting...")
    
    # Initialize default settings
    settings = await db.trading_settings.find_one({"id": "trading_settings"})
    if not settings:
        default_settings = TradingSettings()
        await db.trading_settings.insert_one(default_settings.model_dump())
        logger.info("✅ Default settings initialized")
    
    # Start AI Trading Bot if auto_trading is enabled
    # Note: Bot manager temporarily disabled for stability
    # if settings and settings.get('auto_trading', False):
    #     try:
    #         from ai_trading_bot import bot_manager
    #         await bot_manager.start()
    #         logger.info("🤖 AI Trading Bot auto-started (auto_trading=True)")
    #     except Exception as e:
    #         logger.warning(f"Could not start bot manager: {e}")
    
    logger.info("✅ Booner-Trade API Ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Booner-Trade API...")
    
    # Stop bot
    # try:
    #     from ai_trading_bot import bot_manager
    #     if bot_manager.is_running():
    #         await bot_manager.stop()
    # except Exception as e:
    #     logger.warning(f"Could not stop bot manager: {e}")
    
    logger.info("✅ Shutdown complete")
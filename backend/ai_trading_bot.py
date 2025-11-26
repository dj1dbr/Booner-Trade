"""
AI Trading Bot - Vollautomatische KI-gesteuerte Trading-Plattform
Überwacht, analysiert, öffnet und schließt Positionen AUTOMATISCH

Features:
- Multi-Strategie-Analyse (RSI, MACD, MA, Bollinger Bands, Stochastic)
- News-Integration & Sentiment-Analyse
- LLM-basierte Entscheidungsfindung (GPT-5)
- Automatisches Position-Management
- Risk Management & Portfolio-Balance
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AITradingBot:
    """KI-gesteuerter Trading Bot - übernimmt ALLE Trading-Entscheidungen
    
    DUAL TRADING STRATEGY:
    - Swing Trading: Langfristig, größere Positionen, 80% Balance
    - Day Trading: Kurzfristig, kleinere Positionen, 20% Balance
    """
    
    def __init__(self):
        self.running = False
        self.mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        self.db_name = os.getenv('DB_NAME', 'test_database')
        self.client = None
        self.db = None
        self.settings = None
        self.market_data = {}
        self.market_analyzer = None
        self.llm_chat = None
        self.trade_history = []  # Für Lernzwecke
        self.last_analysis_time_swing = {}  # Pro Commodity für Swing Trading
        self.last_analysis_time_day = {}  # Pro Commodity für Day Trading
        
    async def initialize(self):
        """Initialisiere Bot"""
        logger.info("🤖 AI Trading Bot wird initialisiert...")
        
        # Reload .env für API-Keys
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        # DB Connection
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        # Load Settings
        self.settings = await self.db.trading_settings.find_one({"id": "trading_settings"})
        if not self.settings:
            logger.error("❌ Settings nicht gefunden!")
            return False
        
        # Market Analyzer initialisieren (mit neu geladenen ENV vars)
        from market_analysis import MarketAnalyzer
        self.market_analyzer = MarketAnalyzer()
        
        # LLM Chat für KI-Entscheidungen initialisieren (optional)
        try:
            from ai_chat_service import get_ai_chat_instance
            ai_provider = self.settings.get('ai_provider', 'emergent')
            ai_model = self.settings.get('ai_model', 'gpt-5')
            self.llm_chat = await get_ai_chat_instance(
                self.settings, 
                ai_provider, 
                ai_model, 
                session_id="ai_trading_bot"
            )
            logger.info(f"✅ LLM initialisiert: {ai_provider}/{ai_model}")
        except Exception as e:
            logger.warning(f"⚠️  LLM nicht verfügbar: {e}")
            self.llm_chat = None
        
        logger.info(f"✅ Bot initialisiert | Auto-Trading: {self.settings.get('auto_trading', False)}")
        return True
    
    async def run_forever(self):
        """Hauptschleife - läuft kontinuierlich"""
        self.running = True
        logger.info("🚀 AI Trading Bot gestartet - läuft kontinuierlich!")
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🤖 Bot Iteration #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"{'='*60}")
                
                # Reload settings (könnte sich ändern)
                self.settings = await self.db.trading_settings.find_one({"id": "trading_settings"})
                
                if not self.settings.get('auto_trading', False):
                    logger.warning("⚠️  Auto-Trading ist DEAKTIVIERT in Settings")
                    await asyncio.sleep(30)
                    continue
                
                # 1. Marktdaten aktualisieren
                await self.fetch_market_data()
                
                # 2. ALLE offenen Positionen überwachen
                await self.monitor_open_positions()
                
                # 3. SWING TRADING: KI-Analyse für neue Swing-Trades (alle 10 Min)
                if self.settings.get('swing_trading_enabled', True):
                    await self.analyze_and_open_trades(strategy="swing")
                
                # 4. DAY TRADING: KI-Analyse für neue Day-Trades (jede Minute)
                if self.settings.get('day_trading_enabled', False):
                    await self.analyze_and_open_trades(strategy="day")
                
                # 5. Automatisches Schließen alter Day-Trading-Positionen (Time-Based Exit)
                if self.settings.get('day_trading_enabled', False):
                    await self.close_expired_day_trades()
                
                # 6. Kurze Pause (alle 10 Sekunden)
                logger.info("✅ Iteration abgeschlossen, warte 10 Sekunden...")
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Fehler in Bot-Iteration: {e}", exc_info=True)
                await asyncio.sleep(30)
    
    async def fetch_market_data(self):
        """Hole aktuelle Marktdaten"""
        try:
            # Hole Marktdaten aus market_data Collection (werden von server.py gespeichert)
            # Das Feld heißt "commodity" nicht "commodity_id"
            market_docs = await self.db.market_data.find({}).to_list(100)
            
            self.market_data = {}
            for doc in market_docs:
                # Versuche beide Feldnamen
                commodity_id = doc.get('commodity_id') or doc.get('commodity')
                if commodity_id:
                    self.market_data[commodity_id] = doc
            
            logger.info(f"📊 Marktdaten aktualisiert: {len(self.market_data)} Rohstoffe")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Marktdaten: {e}")
    
    async def monitor_open_positions(self):
        """🤖 KI ÜBERWACHT SL/TP - schließt automatisch bei Ziel!"""
        logger.info("👀 KI überwacht offene Positionen und prüft SL/TP...")
        
        try:
            from multi_platform_connector import multi_platform
            
            # Strategy-spezifische Settings werden dynamisch pro Position geladen
            
            platforms = ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO']
            total_positions = 0
            closed_positions = 0
            
            for platform in platforms:
                if platform not in self.settings.get('active_platforms', []):
                    continue
                
                try:
                    positions = await multi_platform.get_open_positions(platform)
                    total_positions += len(positions)
                    
                    for pos in positions:
                        # Extrahiere Daten
                        entry_price = pos.get('price_open') or pos.get('openPrice') or pos.get('entry_price')
                        current_price = pos.get('price_current') or pos.get('currentPrice') or pos.get('price')
                        pos_type = str(pos.get('type', '')).upper()
                        symbol = pos.get('symbol', '')
                        ticket = pos.get('ticket') or pos.get('id') or pos.get('positionId')
                        profit = pos.get('profit', 0)
                        quantity = pos.get('volume', 0) or pos.get('quantity', 0) or pos.get('size', 0)
                        
                        if not entry_price or not current_price or not ticket:
                            continue
                        
                        # Hole Strategie aus DB Trade (falls vorhanden)
                        db_trade = await self.db.trades.find_one({"mt5_ticket": str(ticket), "status": "OPEN"})
                        strategy = db_trade.get('strategy', 'swing') if db_trade else 'swing'
                        
                        # 🎯 INDIVIDUELLE TRADE SETTINGS haben Priorität!
                        individual_settings = await self.db.trade_settings.find_one({'trade_id': str(ticket)})
                        
                        if individual_settings and (individual_settings.get('stop_loss') or individual_settings.get('take_profit')):
                            # Nutze individuelle Settings vom User
                            stop_loss_price = individual_settings.get('stop_loss')
                            take_profit_price = individual_settings.get('take_profit')
                            logger.info(f"🎯 Nutze individuelle Settings für #{ticket}: SL={stop_loss_price}, TP={take_profit_price}")
                        elif not individual_settings:
                            # 🚨 KEINE SETTINGS GEFUNDEN - AUTOMATISCH ERSTELLEN!
                            logger.warning(f"⚠️ Trade #{ticket} hat keine SL/TP Settings - erstelle automatisch...")
                            
                            # Berechne SL/TP basierend auf Settings
                            tp_percent = self.settings.get('take_profit_percent', 4.0)
                            sl_percent = self.settings.get('stop_loss_percent', 2.0)
                            
                            if 'BUY' in pos_type:
                                stop_loss_price = entry_price * (1 - sl_percent / 100)
                                take_profit_price = entry_price * (1 + tp_percent / 100)
                            else:  # SELL
                                stop_loss_price = entry_price * (1 + sl_percent / 100)
                                take_profit_price = entry_price * (1 - tp_percent / 100)
                            
                            # Speichere in DB
                            try:
                                await self.db.trade_settings.insert_one({
                                    'trade_id': str(ticket),
                                    'stop_loss': stop_loss_price,
                                    'take_profit': take_profit_price,
                                    'created_at': datetime.now(timezone.utc).isoformat(),
                                    'entry_price': entry_price,
                                    'platform': platform,
                                    'created_by': 'AI_MONITOR_AUTO'
                                })
                                logger.info(f"✅ Auto-created SL/TP für #{ticket}: SL={stop_loss_price:.2f}, TP={take_profit_price:.2f}")
                            except Exception as e:
                                logger.error(f"❌ Fehler beim Auto-Create SL/TP: {e}")
                                # Verwende berechnete Werte trotzdem
                        else:
                            # ⚡ IMMER aus Settings berechnen - KI nutzt AKTUELLE Settings!
                            if strategy == 'day':
                                tp_pct = self.settings.get('day_take_profit_percent', 2.5)
                                sl_pct = self.settings.get('day_stop_loss_percent', 1.5)
                            else:  # swing
                                tp_pct = self.settings.get('swing_take_profit_percent', 4.0)
                                sl_pct = self.settings.get('swing_stop_loss_percent', 2.0)
                            
                            # Berechne SL/TP basierend auf Entry-Preis und Settings
                            if 'BUY' in pos_type:
                                take_profit_price = entry_price * (1 + tp_pct / 100)
                                stop_loss_price = entry_price * (1 - sl_pct / 100)
                            else:  # SELL
                                take_profit_price = entry_price * (1 - tp_pct / 100)
                                stop_loss_price = entry_price * (1 + sl_pct / 100)
                        
                        logger.debug(f"🤖 KI überwacht {symbol}: Entry={entry_price:.2f}, SL={stop_loss_price:.2f}, TP={take_profit_price:.2f}")
                        
                        # Prüfe ob SL oder TP erreicht
                        if 'BUY' in pos_type:
                            tp_reached = current_price >= take_profit_price
                            sl_reached = current_price <= stop_loss_price
                        else:  # SELL
                            tp_reached = current_price <= take_profit_price
                            sl_reached = current_price >= stop_loss_price
                        
                        # 🤖 KI-ENTSCHEIDUNG: Position schließen bei SL oder TP
                        should_close = False
                        close_reason = ""
                        
                        if tp_reached:
                            should_close = True
                            close_reason = f"✅ TAKE PROFIT erreicht (Target: {take_profit_price:.2f}, Aktuell: {current_price:.2f})"
                        elif sl_reached:
                            should_close = True
                            close_reason = f"🛑 STOP LOSS erreicht (SL: {stop_loss_price:.2f}, Aktuell: {current_price:.2f})"
                        
                        # Position schließen wenn nötig
                        if should_close:
                            reason = "TAKE PROFIT" if tp_reached else "STOP LOSS"
                            profit_loss = profit if profit else (current_price - entry_price) * quantity if 'BUY' in pos_type else (entry_price - current_price) * quantity
                            
                            logger.info("")
                            logger.info("="*60)
                            logger.info(f"🤖 KI-ÜBERWACHUNG: {reason} ERREICHT!")
                            logger.info("="*60)
                            logger.info(f"📊 Symbol: {symbol} ({pos_type})")
                            logger.info(f"📍 Entry: €{entry_price:.2f}")
                            logger.info(f"📍 Aktuell: €{current_price:.2f}")
                            logger.info(f"🎯 Target: €{take_profit_price if tp_reached else stop_loss_price:.2f}")
                            logger.info(f"💰 P&L: €{profit_loss:.2f}")
                            logger.info("🚀 Aktion: Position wird bei MT5 geschlossen...")
                            logger.info("="*60)
                            
                            # SCHLIESSE POSITION!
                            success = await multi_platform.close_position(platform, str(ticket))
                            
                            if success:
                                logger.info(f"✅ Position {ticket} automatisch geschlossen!")
                                closed_positions += 1
                                
                                # WICHTIG: Speichere geschlossenen Trade in DB für Historie & Statistiken
                                try:
                                    closed_trade = {
                                        "id": f"mt5_{ticket}",
                                        "mt5_ticket": str(ticket),
                                        "commodity": symbol,
                                        "type": "BUY" if 'BUY' in pos_type else "SELL",
                                        "entry_price": entry_price,
                                        "exit_price": current_price,
                                        "quantity": quantity,
                                        "profit_loss": profit,
                                        "status": "CLOSED",
                                        "platform": platform,
                                        "opened_at": opened_at if opened_at else datetime.now(timezone.utc).isoformat(),
                                        "closed_at": datetime.now(timezone.utc).isoformat(),
                                        "close_reason": close_reason,
                                        "closed_by": "AI_BOT"
                                    }
                                    await self.db.trades.insert_one(closed_trade)
                                    logger.info(f"💾 Saved closed trade #{ticket} to DB (P/L: €{profit:.2f})")
                                except Exception as e:
                                    logger.error(f"⚠️ Failed to save closed trade to DB: {e}")
                            else:
                                logger.error(f"❌ Fehler beim Schließen von Position {ticket}")
                        
                except Exception as e:
                    logger.error(f"Fehler bei {platform}: {e}")
            
            logger.info(f"📊 Monitoring abgeschlossen: {total_positions} Positionen überwacht, {closed_positions} geschlossen")
            
        except Exception as e:
            logger.error(f"Fehler beim Monitoring: {e}", exc_info=True)
    
    async def analyze_and_open_trades(self, strategy="swing"):
        """KI analysiert Markt und öffnet neue Positionen - DUAL STRATEGY
        
        Args:
            strategy: "swing" für Swing Trading, "day" für Day Trading
        """
        strategy_name = "Swing Trading" if strategy == "swing" else "Day Trading"
        logger.info(f"🧠 KI analysiert Markt für neue {strategy_name} Möglichkeiten...")
        
        try:
            # Strategie-spezifische Parameter laden
            if strategy == "swing":
                max_positions = self.settings.get('swing_max_positions', 5)
                min_confidence = self.settings.get('swing_min_confidence_score', 0.6) * 100
                analysis_interval = self.settings.get('swing_analysis_interval_seconds', 60)
                last_analysis_dict = self.last_analysis_time_swing
            else:  # day trading
                max_positions = self.settings.get('day_max_positions', 10)
                min_confidence = self.settings.get('day_min_confidence_score', 0.4) * 100
                analysis_interval = self.settings.get('day_analysis_interval_seconds', 60)
                last_analysis_dict = self.last_analysis_time_day
            
            # KORRIGIERT: 20% PRO PLATTFORM für BEIDE Strategien ZUSAMMEN
            combined_max_balance_percent = self.settings.get('combined_max_balance_percent_per_platform', 20.0)
            
            # Prüfe aktuelle Positionen für diese Strategie
            current_positions = await self.get_strategy_positions(strategy)
            if len(current_positions) >= max_positions:
                logger.info(f"ℹ️  {strategy_name}: Max Positionen erreicht ({len(current_positions)}/{max_positions})")
                return
            
            # Prüfe GESAMTE Balance-Auslastung (Swing + Day zusammen) PRO Plattform
            total_balance_usage = await self.calculate_combined_balance_usage_per_platform()
            if total_balance_usage >= combined_max_balance_percent:
                logger.warning(f"⚠️  {strategy_name}: GESAMT Balance-Limit erreicht ({total_balance_usage:.1f}% >= {combined_max_balance_percent}% PRO Plattform)")
                return
            
            # Hole aktivierte Commodities aus Settings
            enabled_commodities = self.settings.get('enabled_commodities', [])
            if not enabled_commodities:
                logger.info("ℹ️  Keine aktivierten Commodities in Settings")
                return
            
            # Analysiere jeden Commodity
            analyzed_count = 0
            skipped_count = 0
            for commodity_id in enabled_commodities:
                # Rate Limiting: Respektiere analysis_interval
                last_check = last_analysis_dict.get(commodity_id)
                time_since_last = (datetime.now() - last_check).seconds if last_check else 999999
                
                if last_check and time_since_last < analysis_interval:
                    skipped_count += 1
                    logger.debug(f"{strategy_name}: {commodity_id} übersprungen (erst vor {time_since_last}s analysiert, Intervall: {analysis_interval}s)")
                    continue
                
                last_analysis_dict[commodity_id] = datetime.now()
                
                # Hole Preishistorie
                price_history = await self.get_price_history(commodity_id)
                if len(price_history) < 20:
                    logger.info(f"ℹ️  {strategy_name}: {commodity_id} - Nicht genug Preisdaten ({len(price_history)}/20)")
                    continue
                
                # Vollständige Marktanalyse
                analysis = await self.market_analyzer.analyze_commodity(commodity_id, price_history)
                analyzed_count += 1
                
                signal = analysis.get('signal', 'HOLD')
                confidence = analysis.get('confidence', 0)
                
                # Nur bei hoher Konfidenz handeln
                if signal in ['BUY', 'SELL'] and confidence >= min_confidence:
                    logger.info(f"🎯 {strategy_name} Signal: {commodity_id} {signal} (Konfidenz: {confidence}%)")
                    
                    # Optional: LLM Final Decision
                    if self.llm_chat and self.settings.get('use_llm_confirmation', False):
                        llm_decision = await self.ask_llm_for_decision(commodity_id, analysis)
                        if not llm_decision:
                            logger.info(f"🤖 LLM lehnt Trade ab: {commodity_id}")
                            continue
                    
                    # Trade ausführen mit Strategie-Tag!
                    await self.execute_ai_trade(commodity_id, signal, analysis, strategy=strategy)
                else:
                    if signal != 'HOLD':
                        logger.info(f"ℹ️  {strategy_name}: {commodity_id} {signal} aber Konfidenz zu niedrig ({confidence:.1f}% < {min_confidence:.1f}%)")
            
            logger.info(f"📊 {strategy_name} Analyse: {analyzed_count} analysiert, {skipped_count} übersprungen (Rate Limit)")
            
        except Exception as e:
            logger.error(f"Fehler bei der {strategy_name} KI-Analyse: {e}", exc_info=True)
    
    async def get_price_history(self, commodity_id: str, days: int = 7) -> List[Dict]:
        """Hole Preishistorie für technische Analyse"""
        try:
            # Hole die letzten N Tage aus market_data_history Collection
            cutoff_date = datetime.now() - timedelta(days=days)
            
            history = await self.db.market_data_history.find({
                "commodity_id": commodity_id,
                "timestamp": {"$gte": cutoff_date}
            }).sort("timestamp", 1).to_list(length=None)
            
            if not history:
                logger.warning(f"Keine Preishistorie für {commodity_id}")
                return []
            
            # Konvertiere zu Format für Indikatoren
            price_data = []
            for item in history:
                price_data.append({
                    'timestamp': item.get('timestamp'),
                    'price': item.get('price', 0),
                    'close': item.get('price', 0),
                    'high': item.get('high', item.get('price', 0)),
                    'low': item.get('low', item.get('price', 0)),
                })
            
            return price_data
            
        except Exception as e:
            logger.error(f"Fehler beim Laden der Preishistorie: {e}")
            return []
    
    
    async def get_strategy_positions(self, strategy: str) -> List[Dict]:
        """Hole alle offenen Positionen für eine bestimmte Strategie"""
        try:
            # Suche in DB nach Trades mit strategy-Tag
            trades = await self.db.trades.find({
                "status": "OPEN",
                "strategy": strategy
            }).to_list(length=100)
            
            return trades
        except Exception as e:
            logger.error(f"Fehler beim Laden der {strategy} Positionen: {e}")
            return []
    
    async def calculate_combined_balance_usage_per_platform(self) -> float:
        """KORRIGIERT: Berechne kombinierte Balance-Auslastung (Swing + Day) PRO Plattform
        
        Returns:
            Höchste Auslastung über alle aktiven Plattformen in Prozent
        """
        try:
            from multi_platform_connector import multi_platform
            
            max_usage_percent = 0.0
            
            # Prüfe jede aktive Plattform separat
            for platform in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO']:
                if platform not in self.settings.get('active_platforms', []):
                    continue
                
                # Hole Balance dieser Plattform
                account_info = await multi_platform.get_account_info(platform)
                if not account_info:
                    continue
                
                platform_balance = account_info.get('balance', 0)
                if platform_balance <= 0:
                    continue
                
                # Hole ALLE offenen Positionen (Swing + Day) auf dieser Plattform
                all_positions = await self.db.trades.find({
                    "status": "OPEN",
                    "platform": platform
                }).to_list(length=100)
                
                # Berechne genutztes Kapital
                used_capital = 0.0
                for pos in all_positions:
                    entry_price = pos.get('entry_price', 0)
                    quantity = pos.get('quantity', 0)
                    used_capital += (entry_price * quantity)
                
                # Prozent dieser Plattform-Balance
                usage_percent = (used_capital / platform_balance) * 100
                
                logger.debug(f"{platform}: {usage_percent:.1f}% genutzt (€{used_capital:.2f} von €{platform_balance:.2f})")
                
                # Höchste Auslastung merken
                if usage_percent > max_usage_percent:
                    max_usage_percent = usage_percent
            
            return min(max_usage_percent, 100.0)
            
        except Exception as e:
            logger.error(f"Fehler bei kombinierten Balance-Berechnung: {e}")
            return 0.0
    
    async def close_expired_day_trades(self):
        """Schließe Day-Trading-Positionen die zu lange offen sind"""
        try:
            max_hold_time = self.settings.get('day_position_hold_time_hours', 2)
            cutoff_time = datetime.now() - timedelta(hours=max_hold_time)
            
            # Hole alle Day-Trading-Positionen
            day_positions = await self.get_strategy_positions("day")
            
            closed_count = 0
            for pos in day_positions:
                opened_at = pos.get('opened_at')
                if not opened_at:
                    continue
                
                # Prüfe Alter
                if opened_at < cutoff_time:
                    ticket = pos.get('mt5_ticket')
                    platform = pos.get('platform')
                    
                    if ticket and platform:
                        from multi_platform_connector import multi_platform
                        
                        logger.info(f"⏰ Schließe abgelaufenen Day-Trade: {pos.get('commodity_id')} (Ticket: {ticket}, Alter: {(datetime.now() - opened_at).seconds // 60} Min)")
                        
                        success = await multi_platform.close_position(platform, str(ticket))
                        if success:
                            closed_count += 1
                            
                            # Update DB
                            await self.db.trades.update_one(
                                {"mt5_ticket": str(ticket)},
                                {"$set": {
                                    "status": "CLOSED",
                                    "closed_at": datetime.now(),
                                    "close_reason": f"Time-Based Exit: Max {max_hold_time}h erreicht",
                                    "closed_by": "AI_BOT_TIMER"
                                }}
                            )
            
            if closed_count > 0:
                logger.info(f"✅ {closed_count} abgelaufene Day-Trades geschlossen")
                
        except Exception as e:
            logger.error(f"Fehler beim Schließen abgelaufener Day-Trades: {e}")

    async def calculate_portfolio_risk(self) -> float:
        """Berechne aktuelles Portfolio-Risiko in Prozent"""
        try:
            from multi_platform_connector import multi_platform
            
            # Hole alle offenen Positionen
            all_positions = []
            for platform in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO']:
                if platform in self.settings.get('active_platforms', []):
                    positions = await multi_platform.get_open_positions(platform)
                    all_positions.extend(positions)
            
            if not all_positions:
                return 0.0
            
            # Hole Account-Balance
            total_balance = 0.0
            for platform in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO']:
                if platform in self.settings.get('active_platforms', []):
                    account_info = await multi_platform.get_account_info(platform)
                    if account_info:
                        total_balance += account_info.get('balance', 0)
            
            if total_balance <= 0:
                return 100.0  # Safety: Wenn keine Balance, maximales Risiko
            
            # Berechne offenes Risiko (basierend auf Stop Loss)
            total_risk = 0.0
            for pos in all_positions:
                volume = pos.get('volume', 0)
                entry_price = pos.get('openPrice') or pos.get('price_open') or pos.get('entry_price', 0)
                stop_loss = pos.get('stopLoss') or pos.get('sl', 0)
                
                if entry_price and stop_loss:
                    # Risiko = Differenz * Volume
                    risk_per_unit = abs(entry_price - stop_loss)
                    position_risk = risk_per_unit * volume
                    total_risk += position_risk
            
            # Risiko in Prozent der Balance
            risk_percent = (total_risk / total_balance) * 100
            
            return min(risk_percent, 100.0)
            
        except Exception as e:
            logger.error(f"Fehler bei Portfolio-Risiko-Berechnung: {e}")
            return 0.0
    
    async def ask_llm_for_decision(self, commodity_id: str, analysis: Dict) -> bool:
        """Frage LLM ob Trade ausgeführt werden soll - MIT VOLLSTÄNDIGEM KONTEXT"""
        try:
            if not self.llm_chat:
                return True  # Default: Ja, wenn LLM nicht verfügbar
            
            # Extrahiere alle verfügbaren Daten
            indicators = analysis.get('indicators', {})
            news = analysis.get('news', {})
            economic = analysis.get('economic_events', {})
            market_sentiment = analysis.get('market_sentiment', {})
            sr_levels = analysis.get('support_resistance', {})
            
            prompt = f"""
Du bist ein professioneller Commodities Trading Analyst. Analysiere folgende KOMPLETTE Marktlage für {commodity_id}:

═══════════════════════════════════════════════
TRADING SIGNAL ANFRAGE
═══════════════════════════════════════════════

📊 SIGNAL-ZUSAMMENFASSUNG:
• Signal: {analysis.get('signal')}
• Konfidenz: {analysis.get('confidence')}%
• Multi-Strategie Score: {analysis.get('total_score')}

📈 TECHNISCHE INDIKATOREN:
• RSI: {indicators.get('rsi', 0):.1f} (Überverkauft <30, Überkauft >70)
• MACD: {indicators.get('macd_diff', 0):.3f} (Positiv=Bullish, Negativ=Bearish)
• Aktueller Preis: ${indicators.get('current_price', 0):.2f}
• SMA 20: ${indicators.get('sma_20', 0):.2f}
• SMA 50: ${indicators.get('sma_50', 0):.2f}
• EMA 12: ${indicators.get('ema_12', 0):.2f}
• Bollinger Bands: ${indicators.get('bb_lower', 0):.2f} - ${indicators.get('bb_upper', 0):.2f}
• ATR (Volatilität): {indicators.get('atr', 0):.2f}
• Stochastic: {indicators.get('stoch_k', 0):.1f}

📰 NEWS & SENTIMENT:
• News-Sentiment: {news.get('sentiment', 'neutral')}
• Sentiment Score: {news.get('score', 0):.2f}
• Anzahl Artikel: {news.get('articles', 0)}
• Quelle: {news.get('source', 'none')}

📅 ECONOMIC CALENDAR (heute):
• Gesamt Events: {economic.get('total_events', 0)}
• High-Impact Events: {economic.get('high_impact', 0)}
{"• ⚠️ WICHTIGE EVENTS HEUTE - Vorsicht!" if economic.get('high_impact', 0) > 0 else "• Keine kritischen Events"}

🌍 MARKT-STIMMUNG:
• Sentiment: {market_sentiment.get('sentiment', 'neutral')}
• SPY RSI: {market_sentiment.get('rsi', 50):.1f}

📊 SUPPORT & RESISTANCE:
• Support Level: ${sr_levels.get('support', 0):.2f}
• Resistance Level: ${sr_levels.get('resistance', 0):.2f}
• Aktueller Preis: ${sr_levels.get('current_price', 0):.2f}

🎯 STRATEGIE-SIGNALE:
{chr(10).join(['• ' + sig for sig in analysis.get('signals', [])])}

═══════════════════════════════════════════════
DEINE AUFGABE
═══════════════════════════════════════════════

Analysiere ALLE oben genannten Faktoren und entscheide:
• Sind die technischen Signale stark genug?
• Unterstützt das News-Sentiment den Trade?
• Gibt es Economic Events die dagegen sprechen?
• Ist die Markt-Stimmung günstig?
• Sind wir nahe Support/Resistance Levels?

WICHTIG:
• Nur bei SEHR STARKEN und KLAREN Signalen JA sagen
• Bei Zweifeln oder gemischten Signalen NEIN sagen
• Economic Events mit hohem Impact = eher NEIN
• Konfidenz unter 70% = genau prüfen

Antworte NUR mit: JA oder NEIN
(Optional: kurze Begründung in 1 Satz)
"""
            
            from emergentintegrations.llm.chat import UserMessage
            response_obj = await self.llm_chat.send_message(UserMessage(text=prompt))
            response = response_obj.text if hasattr(response_obj, 'text') else str(response_obj)
            
            decision = 'ja' in response.lower() or 'yes' in response.lower()
            logger.info(f"🤖 LLM Entscheidung für {commodity_id}: {'✅ JA' if decision else '❌ NEIN'}")
            logger.info(f"   LLM Begründung: {response[:200]}")
            
            return decision
            
        except Exception as e:
            logger.error(f"LLM Entscheidung fehlgeschlagen: {e}")
            return True  # Default: Ja bei Fehler
    
    async def execute_ai_trade(self, commodity_id: str, direction: str, analysis: Dict, strategy="swing"):
        """Führe Trade aus mit Risk Management - DUAL STRATEGY AWARE
        
        Args:
            strategy: "swing" für Swing Trading, "day" für Day Trading
        """
        try:
            from multi_platform_connector import multi_platform
            import commodity_processor
            
            strategy_name = "Swing Trading" if strategy == "swing" else "Day Trading"
            logger.info(f"🚀 Führe {strategy_name} Trade aus: {commodity_id} {direction}")
            
            # ⏰ WICHTIG: Prüfe Handelszeiten
            if not commodity_processor.is_market_open(commodity_id):
                next_open = commodity_processor.get_next_market_open(commodity_id)
                logger.warning(f"⏰ Markt für {commodity_id} ist geschlossen. Nächste Öffnung: {next_open}")
                return
            
            # Hole Commodity-Info aus dem COMMODITIES dict
            commodity = commodity_processor.COMMODITIES.get(commodity_id)
            if not commodity:
                logger.error(f"Commodity {commodity_id} nicht gefunden")
                return
            
            # Bestimme Platform
            active_platforms = self.settings.get('active_platforms', [])
            if not active_platforms:
                logger.error("Keine aktiven Plattformen")
                return
            
            # Wähle Platform mit verfügbarem Symbol - GLEICHMÄSSIGE VERTEILUNG
            platform = None
            symbol = None
            
            # Prüfe, auf welchen Plattformen das Symbol verfügbar ist
            available_platforms = []
            
            for p in active_platforms:
                if 'MT5_LIBERTEX' in p and commodity.get('mt5_libertex_symbol'):
                    available_platforms.append({
                        'platform': p,
                        'symbol': commodity.get('mt5_libertex_symbol'),
                        'name': 'Libertex'
                    })
                elif 'MT5_ICMARKETS' in p and commodity.get('mt5_icmarkets_symbol'):
                    available_platforms.append({
                        'platform': p,
                        'symbol': commodity.get('mt5_icmarkets_symbol'),
                        'name': 'ICMarkets'
                    })
            
            if not available_platforms:
                logger.warning(f"⚠️  {commodity_id}: Kein verfügbares Symbol auf aktiven Plattformen")
                return
            
            # INTELLIGENTE LOAD BALANCING: Balance-gewichtete Plattform-Auswahl
            from multi_platform_connector import multi_platform
            
            platform_usage = {}
            
            for plat_info in available_platforms:
                try:
                    # Hole Account Info für Balance
                    account_info = await multi_platform.get_account_info(plat_info['platform'])
                    balance = account_info.get('balance', 0) if account_info else 0
                    
                    if balance <= 0:
                        platform_usage[plat_info['platform']] = 100.0  # Vermeide Plattform ohne Balance
                        continue
                    
                    # Berechne genutzte Balance (alle offenen Positionen)
                    positions = await multi_platform.get_open_positions(plat_info['platform'])
                    used_capital = 0
                    
                    for pos in positions:
                        # Geschätztes genutztes Kapital: Volume * Entry Price * Contract Size (100 für Forex, 1000 für Commodities)
                        volume = pos.get('volume', 0)
                        price = pos.get('price_open', 0)
                        # Vereinfacht: Nutze Margin oder schätze basierend auf Position
                        used_capital += volume * price * 100  # Konservativer Schätzwert
                    
                    # Berechne Nutzungs-Prozentsatz
                    usage_percent = (used_capital / balance) * 100
                    platform_usage[plat_info['platform']] = {
                        'usage_percent': usage_percent,
                        'balance': balance,
                        'used_capital': used_capital,
                        'positions_count': len(positions)
                    }
                    
                    logger.debug(f"📊 {plat_info['name']}: {usage_percent:.1f}% genutzt (€{used_capital:.2f} / €{balance:.2f}, {len(positions)} Positionen)")
                    
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen von {plat_info['platform']}: {e}")
                    platform_usage[plat_info['platform']] = {'usage_percent': 100.0}  # Vermeide fehlerhafte Plattform
            
            # Wähle Plattform mit NIEDRIGSTER Nutzung (mehr verfügbares Kapital)
            selected = min(available_platforms, 
                          key=lambda x: platform_usage.get(x['platform'], {}).get('usage_percent', 100.0))
            platform = selected['platform']
            symbol = selected['symbol']
            
            usage_info = platform_usage.get(platform, {})
            logger.info(
                f"✅ {commodity_id} → {selected['name']} "
                f"(Symbol: {symbol}, "
                f"Nutzung: {usage_info.get('usage_percent', 0):.1f}%, "
                f"Balance: €{usage_info.get('balance', 0):,.2f}, "
                f"Positionen: {usage_info.get('positions_count', 0)})"
            )
            
            # Risk Management: Positionsgröße berechnen
            account_info = await multi_platform.get_account_info(platform)
            if not account_info:
                logger.error(f"Account-Info nicht verfügbar für {platform}")
                return
            
            balance = account_info.get('balance', 0)
            if balance <= 0:
                logger.error("Balance ist 0 oder negativ")
                return
            
            # Strategie-spezifische Parameter
            if strategy == "swing":
                risk_per_trade = self.settings.get('swing_risk_per_trade_percent', 2.0)
                atr_multiplier_sl = self.settings.get('swing_atr_multiplier_sl', 2.0)
                atr_multiplier_tp = self.settings.get('swing_atr_multiplier_tp', 3.0)
            else:  # day trading
                risk_per_trade = self.settings.get('day_risk_per_trade_percent', 1.0)
                atr_multiplier_sl = self.settings.get('day_atr_multiplier_sl', 1.0)
                atr_multiplier_tp = self.settings.get('day_atr_multiplier_tp', 1.5)
            
            risk_amount = balance * (risk_per_trade / 100)
            
            # Stop Loss und Take Profit basierend auf ATR
            atr = analysis.get('indicators', {}).get('atr', 0)
            current_price = analysis.get('indicators', {}).get('current_price', 0)
            
            if not current_price or not atr:
                logger.error("Preis oder ATR nicht verfügbar")
                return
            
            # Stop Loss und Take Profit mit Strategie-spezifischen Multiplikatoren
            sl_distance = atr * atr_multiplier_sl
            tp_distance = atr * atr_multiplier_tp
            
            if direction == 'BUY':
                stop_loss = current_price - sl_distance
                take_profit = current_price + tp_distance
            else:  # SELL
                stop_loss = current_price + sl_distance
                take_profit = current_price - tp_distance
            
            # Positionsgröße (konservativ)
            volume = min(0.01, risk_amount / (sl_distance * 100))  # Beginne mit Mini-Lots
            volume = max(0.01, volume)  # Mindestens 0.01
            
            # Symbol wurde bereits oben ausgewählt
            
            logger.info(f"📊 Trade-Parameter:")
            logger.info(f"   Platform: {platform}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Direction: {direction}")
            logger.info(f"   Volume: {volume}")
            logger.info(f"   Entry: {current_price:.2f}")
            logger.info(f"   Stop Loss: {stop_loss:.2f}")
            logger.info(f"   Take Profit: {take_profit:.2f}")
            logger.info(f"   Risk: €{risk_amount:.2f} ({risk_per_trade}%)")
            
            # ⚡ IMMER OHNE MT5 SL/TP - KI ÜBERWACHT ALLES!
            logger.info(f"💡 Öffne Trade OHNE MT5 SL/TP - KI übernimmt komplette Überwachung!")
            logger.info(f"📊 KI wird überwachen: SL={stop_loss:.2f}, TP={take_profit:.2f}")
            
            result = await multi_platform.execute_trade(
                platform_name=platform,
                symbol=symbol,
                action=direction,
                volume=volume,
                stop_loss=None,  # IMMER None - KI überwacht!
                take_profit=None # IMMER None - KI überwacht!
            )
            
            if result and result.get('success'):
                ticket = result.get('ticket')
                logger.info(f"✅ AI-Trade erfolgreich ausgeführt: {commodity_id} {direction}")
                logger.info(f"   Ticket: {ticket}")
                
                # Speichere in DB mit Strategy-Tag
                await self.db.trades.insert_one({
                    "commodity_id": commodity_id,
                    "commodity_name": commodity.get('name'),
                    "platform": platform,
                    "type": direction,
                    "quantity": volume,
                    "entry_price": current_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "mt5_ticket": ticket,
                    "status": "OPEN",
                    "opened_at": datetime.now(),
                    "opened_by": "AI_BOT",
                    "strategy": strategy,  # WICHTIG: Tag für Dual-Strategy-Tracking!
                    "analysis": analysis,  # Speichere komplette Analyse
                    "confidence": analysis.get('confidence', 0)
                })
                
                # WICHTIG: Speichere SL/TP auch in trade_settings für Monitor
                try:
                    await self.db.trade_settings.update_one(
                        {'trade_id': str(ticket)},
                        {'$set': {
                            'trade_id': str(ticket),
                            'stop_loss': stop_loss,
                            'take_profit': take_profit,
                            'created_at': datetime.now(timezone.utc).isoformat(),
                            'commodity': commodity_id,
                            'entry_price': current_price,
                            'platform': platform,
                            'strategy': strategy,
                            'created_by': 'AI_BOT'
                        }},
                        upsert=True
                    )
                    logger.info(f"💾 SL/TP Settings gespeichert für AI-Trade #{ticket}")
                except Exception as e:
                    logger.error(f"⚠️ Fehler beim Speichern der Trade Settings: {e}")
                
                # Für Lernzwecke
                self.trade_history.append({
                    "commodity": commodity_id,
                    "direction": direction,
                    "timestamp": datetime.now(),
                    "confidence": analysis.get('confidence', 0)
                })
                
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                logger.error(f"❌ Trade fehlgeschlagen: {error}")
            
        except Exception as e:
            logger.error(f"Fehler bei Trade-Execution: {e}", exc_info=True)
    
    def stop(self):
        """Stoppe Bot"""
        logger.info("🛑 Bot wird gestoppt...")
        self.running = False
        if self.client:
            self.client.close()

async def main():
    """Hauptfunktion"""
    bot = AITradingBot()
    
    if await bot.initialize():
        try:
            await bot.run_forever()
        except KeyboardInterrupt:
            logger.info("\n⚠️  Bot manuell gestoppt (Ctrl+C)")
        finally:
            bot.stop()
    else:
        logger.error("❌ Bot konnte nicht initialisiert werden")

# Bot Manager für FastAPI Integration
class BotManager:
    def __init__(self):
        self.bot = None
        self.bot_task = None
        
    def is_running(self):
        return self.bot is not None and self.bot.running
    
    async def start(self):
        if self.is_running():
            logger.warning("Bot läuft bereits")
            return False
        
        self.bot = AITradingBot()
        if await self.bot.initialize():
            self.bot_task = asyncio.create_task(self.bot.run_forever())
            logger.info("✅ Bot Manager gestartet")
            return True
        return False
    
    async def stop(self):
        if self.bot:
            self.bot.stop()
            if self.bot_task:
                self.bot_task.cancel()
            self.bot = None
            self.bot_task = None
            logger.info("✅ Bot Manager gestoppt")

# Global bot manager instance
bot_manager = BotManager()

if __name__ == "__main__":
    asyncio.run(main())

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
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AITradingBot:
    """KI-gesteuerter Trading Bot - übernimmt ALLE Trading-Entscheidungen"""
    
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
        self.last_analysis_time = {}  # Pro Commodity
        
    async def initialize(self):
        """Initialisiere Bot"""
        logger.info("🤖 AI Trading Bot wird initialisiert...")
        
        # DB Connection
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client[self.db_name]
        
        # Load Settings
        self.settings = await self.db.trading_settings.find_one({"id": "trading_settings"})
        if not self.settings:
            logger.error("❌ Settings nicht gefunden!")
            return False
        
        # Market Analyzer initialisieren
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
                
                # 3. KI-Analyse für neue Trades
                await self.analyze_and_open_trades()
                
                # 4. Kurze Pause (alle 10 Sekunden)
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
        """Überwache ALLE offenen Positionen und schließe bei Ziel"""
        logger.info("👀 Überwache offene Positionen...")
        
        try:
            from multi_platform_connector import multi_platform
            
            # Hole Settings
            tp_percent = self.settings.get('take_profit_percent', 0.2)
            sl_percent = self.settings.get('stop_loss_percent', 2.0)
            
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
                        
                        if not entry_price or not current_price or not ticket:
                            continue
                        
                        # Berechne Targets
                        if 'BUY' in pos_type:
                            take_profit_price = entry_price * (1 + tp_percent / 100)
                            stop_loss_price = entry_price * (1 - sl_percent / 100)
                            
                            tp_reached = current_price >= take_profit_price
                            sl_reached = current_price <= stop_loss_price
                        else:  # SELL
                            take_profit_price = entry_price * (1 - tp_percent / 100)
                            stop_loss_price = entry_price * (1 + sl_percent / 100)
                            
                            tp_reached = current_price <= take_profit_price
                            sl_reached = current_price >= stop_loss_price
                        
                        # KI-Entscheidung: Schließen?
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
                            logger.warning(f"🤖 KI-ENTSCHEIDUNG: Position schließen!")
                            logger.warning(f"   Symbol: {symbol} | Ticket: {ticket}")
                            logger.warning(f"   Grund: {close_reason}")
                            logger.warning(f"   Profit: {profit:.2f}€")
                            
                            # SCHLIESSE POSITION!
                            success = await multi_platform.close_position(platform, str(ticket))
                            
                            if success:
                                logger.info(f"✅ Position {ticket} automatisch geschlossen!")
                                closed_positions += 1
                                
                                # Speichere in DB für History
                                await self.db.trades.update_one(
                                    {"mt5_ticket": str(ticket)},
                                    {"$set": {
                                        "status": "CLOSED",
                                        "closed_at": datetime.now(),
                                        "profit_loss": profit,
                                        "close_reason": close_reason,
                                        "closed_by": "AI_BOT"
                                    }},
                                    upsert=False
                                )
                            else:
                                logger.error(f"❌ Fehler beim Schließen von Position {ticket}")
                        
                except Exception as e:
                    logger.error(f"Fehler bei {platform}: {e}")
            
            logger.info(f"📊 Monitoring abgeschlossen: {total_positions} Positionen überwacht, {closed_positions} geschlossen")
            
        except Exception as e:
            logger.error(f"Fehler beim Monitoring: {e}", exc_info=True)
    
    async def analyze_and_open_trades(self):
        """KI analysiert Markt und öffnet neue Positionen"""
        logger.info("🧠 KI analysiert Markt für neue Trade-Möglichkeiten...")
        
        try:
            # Prüfe Portfolio-Risiko
            max_portfolio_risk = self.settings.get('max_portfolio_risk_percent', 20.0)
            
            # Prüfe aktuelles Portfolio-Risiko
            current_risk = await self.calculate_portfolio_risk()
            if current_risk >= max_portfolio_risk:
                logger.warning(f"⚠️  Portfolio-Risiko zu hoch: {current_risk:.1f}% >= {max_portfolio_risk}% - keine neuen Trades")
                return
            
            # Hole aktivierte Commodities aus Settings
            enabled_commodities = self.settings.get('enabled_commodities', [])
            if not enabled_commodities:
                logger.info("ℹ️  Keine aktivierten Commodities in Settings")
                return
            
            # Analysiere jeden Commodity
            for commodity_id in enabled_commodities:
                # Rate Limiting: Max 1 Analyse alle 5 Minuten pro Commodity
                last_check = self.last_analysis_time.get(commodity_id)
                if last_check and (datetime.now() - last_check).seconds < 300:
                    continue
                
                self.last_analysis_time[commodity_id] = datetime.now()
                
                # Hole Preishistorie
                price_history = await self.get_price_history(commodity_id)
                if len(price_history) < 50:
                    logger.warning(f"⚠️  {commodity_id}: Nicht genug Preisdaten ({len(price_history)})")
                    continue
                
                # Vollständige Marktanalyse
                analysis = await self.market_analyzer.analyze_commodity(commodity_id, price_history)
                
                signal = analysis.get('signal', 'HOLD')
                confidence = analysis.get('confidence', 0)
                
                # Nur bei hoher Konfidenz handeln
                min_confidence = self.settings.get('min_confidence_percent', 60.0)
                
                if signal in ['BUY', 'SELL'] and confidence >= min_confidence:
                    logger.info(f"🎯 Starkes Signal: {commodity_id} {signal} (Konfidenz: {confidence}%)")
                    
                    # Optional: LLM Final Decision
                    if self.llm_chat and self.settings.get('use_llm_confirmation', False):
                        llm_decision = await self.ask_llm_for_decision(commodity_id, analysis)
                        if not llm_decision:
                            logger.info(f"🤖 LLM lehnt Trade ab: {commodity_id}")
                            continue
                    
                    # Trade ausführen!
                    await self.execute_ai_trade(commodity_id, signal, analysis)
                else:
                    if signal != 'HOLD':
                        logger.info(f"ℹ️  {commodity_id}: {signal} aber Konfidenz zu niedrig ({confidence}% < {min_confidence}%)")
            
        except Exception as e:
            logger.error(f"Fehler bei der KI-Analyse: {e}", exc_info=True)
    
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
        """Frage LLM ob Trade ausgeführt werden soll"""
        try:
            if not self.llm_chat:
                return True  # Default: Ja, wenn LLM nicht verfügbar
            
            prompt = f"""
Basierend auf folgender Marktanalyse für {commodity_id}, soll der Trade ausgeführt werden?

Signal: {analysis.get('signal')}
Konfidenz: {analysis.get('confidence')}%
Score: {analysis.get('total_score')}

Indikatoren:
- RSI: {analysis.get('indicators', {}).get('rsi', 0):.1f}
- MACD: {analysis.get('indicators', {}).get('macd_diff', 0):.3f}
- Preis vs SMA20: {analysis.get('indicators', {}).get('current_price', 0):.2f} vs {analysis.get('indicators', {}).get('sma_20', 0):.2f}

News Sentiment: {analysis.get('news', {}).get('sentiment', 'neutral')}

Strategie-Signale:
{chr(10).join(analysis.get('signals', []))}

Antworte nur mit JA oder NEIN.
"""
            
            from emergentintegrations.llm.chat import UserMessage
            response_obj = await self.llm_chat.send_message(UserMessage(text=prompt))
            response = response_obj.text if hasattr(response_obj, 'text') else str(response_obj)
            
            decision = 'ja' in response.lower() or 'yes' in response.lower()
            logger.info(f"🤖 LLM Entscheidung für {commodity_id}: {'✅ JA' if decision else '❌ NEIN'}")
            
            return decision
            
        except Exception as e:
            logger.error(f"LLM Entscheidung fehlgeschlagen: {e}")
            return True  # Default: Ja bei Fehler
    
    async def execute_ai_trade(self, commodity_id: str, direction: str, analysis: Dict):
        """Führe Trade aus mit Risk Management"""
        try:
            from multi_platform_connector import multi_platform
            from commodity_processor import commodity_processor
            
            logger.info(f"🚀 Führe AI-Trade aus: {commodity_id} {direction}")
            
            # Hole Commodity-Info
            commodity = commodity_processor.get_commodity_by_id(commodity_id)
            if not commodity:
                logger.error(f"Commodity {commodity_id} nicht gefunden")
                return
            
            # Bestimme Platform
            active_platforms = self.settings.get('active_platforms', [])
            if not active_platforms:
                logger.error("Keine aktiven Plattformen")
                return
            
            # Wähle erste verfügbare Platform für diesen Commodity
            platform = None
            for p in active_platforms:
                if p in commodity.get('platforms', []):
                    platform = p
                    break
            
            if not platform:
                logger.error(f"Keine verfügbare Platform für {commodity_id}")
                return
            
            # Risk Management: Positionsgröße berechnen
            account_info = await multi_platform.get_account_info(platform)
            if not account_info:
                logger.error(f"Account-Info nicht verfügbar für {platform}")
                return
            
            balance = account_info.get('balance', 0)
            if balance <= 0:
                logger.error("Balance ist 0 oder negativ")
                return
            
            # Positionsgröße = (Balance * RisikoProTrade%) / (StopLoss * ContractSize)
            risk_per_trade = self.settings.get('risk_per_trade_percent', 2.0)
            risk_amount = balance * (risk_per_trade / 100)
            
            # Stop Loss und Take Profit basierend auf ATR
            atr = analysis.get('indicators', {}).get('atr', 0)
            current_price = analysis.get('indicators', {}).get('current_price', 0)
            
            if not current_price or not atr:
                logger.error("Preis oder ATR nicht verfügbar")
                return
            
            # Stop Loss: 2 x ATR
            sl_distance = atr * 2
            # Take Profit: 3 x ATR (Risk:Reward = 1:1.5)
            tp_distance = atr * 3
            
            if direction == 'BUY':
                stop_loss = current_price - sl_distance
                take_profit = current_price + tp_distance
            else:  # SELL
                stop_loss = current_price + sl_distance
                take_profit = current_price - tp_distance
            
            # Positionsgröße (konservativ)
            volume = min(0.01, risk_amount / (sl_distance * 100))  # Beginne mit Mini-Lots
            volume = max(0.01, volume)  # Mindestens 0.01
            
            # Bestimme Symbol für Platform
            symbol = None
            if platform == 'MT5_LIBERTEX_DEMO':
                symbol = commodity.get('mt5_libertex_symbol')
            elif platform == 'MT5_ICMARKETS_DEMO':
                symbol = commodity.get('mt5_icmarkets_symbol')
            
            if not symbol:
                logger.error(f"Kein Symbol für {commodity_id} auf {platform}")
                return
            
            logger.info(f"📊 Trade-Parameter:")
            logger.info(f"   Platform: {platform}")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Direction: {direction}")
            logger.info(f"   Volume: {volume}")
            logger.info(f"   Entry: {current_price:.2f}")
            logger.info(f"   Stop Loss: {stop_loss:.2f}")
            logger.info(f"   Take Profit: {take_profit:.2f}")
            logger.info(f"   Risk: €{risk_amount:.2f} ({risk_per_trade}%)")
            
            # Trade ausführen!
            result = await multi_platform.execute_trade(
                platform_name=platform,
                symbol=symbol,
                action=direction,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            if result and result.get('success'):
                logger.info(f"✅ AI-Trade erfolgreich ausgeführt: {commodity_id} {direction}")
                logger.info(f"   Ticket: {result.get('ticket')}")
                
                # Speichere in DB
                await self.db.trades.insert_one({
                    "commodity_id": commodity_id,
                    "commodity_name": commodity.get('name'),
                    "platform": platform,
                    "type": direction,
                    "quantity": volume,
                    "entry_price": current_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "mt5_ticket": result.get('ticket'),
                    "status": "OPEN",
                    "opened_at": datetime.now(),
                    "opened_by": "AI_BOT",
                    "analysis": analysis,  # Speichere komplette Analyse
                    "confidence": analysis.get('confidence', 0)
                })
                
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

if __name__ == "__main__":
    asyncio.run(main())

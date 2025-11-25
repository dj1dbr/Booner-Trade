"""
AI Chat Service for Trading Bot
Supports: GPT-5, Claude, and Ollama (local)
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize chat instance (will be set on first use)
_chat_instance = None

def get_trading_context(settings, latest_market_data, open_trades):
    """Generate context about current trading state"""
    
    # Extract settings properly (handle both dict and None)
    auto_trading = settings.get('auto_trading', False) if settings else False
    use_ai = settings.get('use_ai_analysis', False) if settings else False
    swing_enabled = settings.get('swing_trading_enabled', True) if settings else True
    day_enabled = settings.get('day_trading_enabled', False) if settings else False
    swing_confidence = settings.get('swing_min_confidence_score', 0.6) if settings else 0.6
    day_confidence = settings.get('day_min_confidence_score', 0.4) if settings else 0.4
    max_balance_per_platform = settings.get('combined_max_balance_percent_per_platform', 20) if settings else 20
    
    context = f"""
Du bist ein intelligenter Trading-Assistent für die Rohstoff-Trading-Plattform mit DUAL TRADING STRATEGY.

AKTUELLE TRADING-EINSTELLUNGEN:
- Auto-Trading: {'✅ AKTIV' if auto_trading else '❌ INAKTIV'}
- AI-Analyse: {'✅ AKTIV' if use_ai else '❌ INAKTIV'}

DUAL TRADING STRATEGY (NEU!):
📈 Swing Trading: {'✅ AKTIV' if swing_enabled else '❌ INAKTIV'} (Langfristig, {swing_confidence*100:.0f}% Min. Confidence)
⚡ Day Trading: {'✅ AKTIV' if day_enabled else '❌ INAKTIV'} (Kurzfristig, {day_confidence*100:.0f}% Min. Confidence, Max 2h Haltezeit)

⚠️ WICHTIG: Beide Strategien zusammen nutzen maximal {max_balance_per_platform:.0f}% der Balance PRO Plattform!

MARKTDATEN (Live):
"""
    
    # Add market hours info
    from commodity_processor import is_market_open, get_next_market_open
    context += "\n⏰ HANDELSZEITEN (wichtig für Trading-Entscheidungen):\n"
    context += "- Edelmetalle (Gold, Silber, Platin, Palladium): 24/5 (So 22:00 - Fr 21:00 UTC)\n"
    context += "- Energie (WTI, Brent, Gas): 24/5 (So 22:00 - Fr 21:00 UTC)\n"
    context += "- Agrar (Weizen, Mais, Soja, etc.): Mo-Fr 08:30-20:00 UTC\n"
    context += "- Forex (EUR/USD): 24/5 (So 22:00 - Fr 21:00 UTC)\n"
    context += "- Crypto (Bitcoin): 24/7\n\n"
    
    # Add market data for ALL available commodities
    if latest_market_data:
        commodity_count = 0
        for commodity_id, data in latest_market_data.items():
            if isinstance(data, dict) and 'price' in data:
                price = data.get('price', 0)
                signal = data.get('signal', 'HOLD')
                rsi = data.get('rsi', 50)
                market_status = "🟢 OFFEN" if is_market_open(commodity_id) else "🔴 GESCHLOSSEN"
                context += f"\n{commodity_id} {market_status}: ${price:.2f}, Signal: {signal}, RSI: {rsi:.1f}"
                commodity_count += 1
        
        if commodity_count == 0:
            context += "\n(Keine Marktdaten verfügbar)"
    
    context += f"\n\nOFFENE TRADES: {len(open_trades)}"
    if open_trades:
        # Get SL/TP percentages from settings
        sl_percent = settings.get('stop_loss_percent', 0.5)
        tp_percent = settings.get('take_profit_percent', 0.2)
        
        context += "\n"
        for i, trade in enumerate(open_trades[:10], 1):  # Show up to 10 trades with numbers
            commodity = trade.get('commodity', trade.get('symbol', 'UNKNOWN'))
            trade_type = trade.get('type', 'UNKNOWN')
            quantity = trade.get('quantity', trade.get('volume', 0))
            entry = trade.get('entry_price', trade.get('openPrice', trade.get('price', 0)))
            current = trade.get('price', entry)
            profit = trade.get('profit_loss', trade.get('profit', trade.get('unrealizedProfit', 0)))
            stop_loss = trade.get('stop_loss', trade.get('sl'))
            take_profit = trade.get('take_profit', trade.get('tp'))
            
            # Calculate recommended SL/TP based on settings
            if trade_type == 'SELL':
                recommended_sl = entry * (1 + sl_percent / 100)
                recommended_tp = entry * (1 - tp_percent / 100)
            else:  # BUY
                recommended_sl = entry * (1 - sl_percent / 100)
                recommended_tp = entry * (1 + tp_percent / 100)
            
            # Format SL/TP info with recommendations
            if stop_loss:
                sl_text = f"${stop_loss:.2f}"
            else:
                sl_text = f"NICHT GESETZT (Empfohlen: ${recommended_sl:.2f} bei {sl_percent}%)"
            
            if take_profit:
                tp_text = f"${take_profit:.2f}"
            else:
                tp_text = f"NICHT GESETZT (Empfohlen: ${recommended_tp:.2f} bei {tp_percent}%)"
            
            context += f"{i}. {commodity} {trade_type}\n"
            context += f"   Menge: {quantity}, Entry: ${entry:.2f}, Aktuell: ${current:.2f}\n"
            context += f"   P/L: ${profit:.2f}\n"
            context += f"   Stop Loss: {sl_text}\n"
            context += f"   Take Profit: {tp_text}\n"
    else:
        context += "\n(Keine offenen Trades)"
    
    context += """

DEINE ROLLE & ANWEISUNGEN:
- Antworte KURZ und PRÄZISE (max 3-4 Sätze, außer bei detaillierten Analysen)
- Bei Fragen zu offenen Trades: Zeige KONKRET welche Trades offen sind (Rohstoff, Typ, Menge, Entry, P/L)
- Wenn Stop Loss/Take Profit "NICHT GESETZT" ist: SAGE DAS KLAR! Der Trade hat KEINE automatischen Exit-Limits
- Bei Fragen "Wann steigt Trade aus?": Wenn SL/TP nicht gesetzt → Sage: "KEIN automatischer Exit gesetzt"
- Wenn der Benutzer "Ja" oder "OK" sagt, führe die vorher vorgeschlagene Aktion aus
- Erkenne Kontext aus vorherigen Nachrichten
- KEINE vagen Antworten! Nutze die konkreten Daten aus dem Kontext oben
- Bei "Wie viele Trades" → Gib die EXAKTE Zahl und liste sie auf
- Bei Fragen wie "Wann tradest du?" → Erkläre KURZ die Entry-Bedingungen basierend auf aktuellen Signalen
- Nutze die AKTUELLEN Settings (siehe oben) - nicht raten!
- Wenn Auto-Trading AKTIV ist, sage das klar
- Antworte auf DEUTSCH

Du kannst:
1. Marktanalysen geben (basierend auf RSI, Signalen)
2. Erklären, warum Trades ausgeführt/nicht ausgeführt wurden
3. Trading-Empfehlungen geben
4. Settings überprüfen und erklären
"""
    
    return context


async def get_ai_chat_instance(settings, ai_provider="openai", model="gpt-5", session_id="default-session"):
    """Get or create AI chat instance with session context"""
    global _chat_instance
    
    try:
        if ai_provider == "ollama":
            # Ollama support for local AI
            import aiohttp
            
            # Get Ollama base URL from settings
            ollama_base_url = settings.get('ollama_base_url', 'http://localhost:11434')
            ollama_model = settings.get('ollama_model', 'llama3')
            
            logger.info(f"🏠 Initializing Ollama: {ollama_base_url} with model {ollama_model}")
            
            class OllamaChat:
                def __init__(self, base_url, model):
                    self.base_url = base_url
                    self.model = model or "llama3"
                    self.history = []
                
                async def send_message(self, message):
                    self.history.append({"role": "user", "content": message})
                    
                    try:
                        async with aiohttp.ClientSession() as session:
                            payload = {
                                "model": self.model,
                                "messages": self.history,
                                "stream": False
                            }
                            
                            logger.info(f"🔄 Sending request to Ollama: {self.base_url}/api/chat")
                            
                            async with session.post(
                                f"{self.base_url}/api/chat", 
                                json=payload,
                                timeout=aiohttp.ClientTimeout(total=60)
                            ) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    assistant_msg = result.get('message', {}).get('content', '')
                                    self.history.append({"role": "assistant", "content": assistant_msg})
                                    logger.info(f"✅ Ollama response received")
                                    return assistant_msg
                                else:
                                    error_text = await response.text()
                                    logger.error(f"❌ Ollama error: {response.status} - {error_text}")
                                    return f"Fehler: Ollama Server antwortet mit Fehler {response.status}. Bitte prüfen Sie, ob Ollama läuft: `ollama serve`"
                    except aiohttp.ClientConnectorError:
                        logger.error(f"❌ Ollama nicht erreichbar: {self.base_url}")
                        return f"❌ Fehler: Ollama nicht erreichbar unter {self.base_url}.\n\n🔧 Lösungen:\n1. Starten Sie Ollama: `ollama serve`\n2. Prüfen Sie, ob Ollama läuft: `ollama list`\n3. Testen Sie manuell: `curl {self.base_url}/api/tags`"
                    except Exception as e:
                        logger.error(f"❌ Ollama Fehler: {e}")
                        return f"Fehler bei Ollama-Anfrage: {str(e)}"
            
            return OllamaChat(ollama_base_url, ollama_model)
        
        else:
            # Use Emergentintegrations for GPT-5/Claude (with fallback)
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
            except ImportError:
                from llm_fallback import get_llm_chat, get_user_message
                LlmChat = get_llm_chat
                UserMessage = get_user_message
            
            # Get API key based on provider
            # Priority: Settings API Keys > Emergent LLM Key (for emergent provider)
            api_key = None
            
            if ai_provider.lower() == "emergent":
                # Use Emergent LLM Key (universal key)
                api_key = os.getenv('EMERGENT_LLM_KEY')
                if not api_key:
                    raise Exception("EMERGENT_LLM_KEY not found. Please add balance or switch to another provider.")
            elif ai_provider.lower() == "openai":
                # Use OpenAI API key from settings or fallback to emergent
                api_key = settings.get('openai_api_key') or os.getenv('EMERGENT_LLM_KEY')
            elif ai_provider.lower() in ["gemini", "google"]:
                # Use Gemini API key from settings
                api_key = settings.get('gemini_api_key')
                if not api_key:
                    raise Exception("Gemini API Key nicht gefunden! Bitte in Einstellungen eintragen oder zu Emergent wechseln.")
            elif ai_provider.lower() in ["anthropic", "claude"]:
                # Use Anthropic API key from settings or fallback to emergent
                api_key = settings.get('anthropic_api_key') or os.getenv('EMERGENT_LLM_KEY')
            elif ai_provider.lower() == "ollama":
                # Ollama doesn't need API key
                api_key = "ollama-local"
            else:
                # Default to Emergent LLM Key
                api_key = os.getenv('EMERGENT_LLM_KEY')
            
            if not api_key:
                raise Exception(f"Kein API-Key für Provider '{ai_provider}' gefunden. Bitte in Einstellungen eintragen.")
            
            logger.info(f"Using API key for provider: {ai_provider} (from {'settings' if ai_provider != 'emergent' and settings.get(f'{ai_provider}_api_key') else 'environment'})")
            
            # Determine provider and model
            provider_map = {
                "openai": ("openai", model or "gpt-5"),
                "anthropic": ("anthropic", model or "claude-4-sonnet-20250514"),
                "claude": ("anthropic", "claude-4-sonnet-20250514"),
                "gemini": ("gemini", model or "gemini-2.5-pro"),
                "google": ("gemini", model or "gemini-2.5-pro"),
                "emergent": ("openai", model or "gpt-5")  # Emergent uses OpenAI-compatible format
            }
            
            provider, model_name = provider_map.get(ai_provider.lower(), ("openai", "gpt-5"))
            
            # Dynamic system message based on auto-trading status
            auto_trading_active = settings.get('auto_trading', False)
            
            if auto_trading_active:
                system_message = """Du bist ein intelligenter Trading-Assistent für Rohstoffe mit AKTIVER TRADE-AUSFÜHRUNG.

✅ AUTO-TRADING IST AKTIV! Du kannst Trades direkt ausführen!

VERFÜGBARE FUNKTIONEN:
1. execute_trade - Platziert einen Trade
2. close_trade - Schließt einen Trade per ID
3. close_all_trades - Schließt ALLE offenen Trades
4. close_trades_by_symbol - Schließt alle Trades eines Symbols (z.B. "GOLD")
5. get_open_positions - Zeigt alle offenen Positionen
6. update_stop_loss - Passt Stop Loss an

WENN USER SAGT:
- "Kaufe WTI" → Nutze execute_trade(symbol="WTI_CRUDE", direction="BUY")
- "Schließe alle Positionen" → Nutze close_all_trades()
- "Schließe Gold" → Nutze close_trades_by_symbol(symbol="GOLD")
- "Zeige Positionen" → Nutze get_open_positions()

WICHTIG:
- Antworte auf Deutsch, klar und direkt
- Führe Trades sofort aus wenn User bestätigt
- Bestätige nach Ausführung: "✅ Trade ausgeführt: LONG WTI @58.48"
- Bei Fragen IMMER erst analysieren, dann Empfehlung, dann auf Bestätigung warten"""
            else:
                system_message = """Du bist ein intelligenter Trading-Assistent für Rohstoffe.

⚠️ AUTO-TRADING IST INAKTIV - Du kannst nur beraten, keine Trades ausführen!

Du kannst:
1. Marktanalysen durchführen
2. Trading-Signale identifizieren
3. Trade-Empfehlungen geben mit Entry, SL und TP

Wenn der User "Ja" sagt oder deine Empfehlung bestätigt:
- Erkläre: "⚠️ Auto-Trading ist inaktiv. Bitte platziere manuell im Dashboard."
- Gib die genauen Parameter: Symbol, Richtung, Entry, SL, TP
- Erkläre wie: "Gehe zum Dashboard → [Symbol] → Klicke BUY/SELL"

NIEMALS sagen: "Ich platziere jetzt..." wenn Auto-Trading inaktiv ist!
Antworte auf Deutsch, präzise und ehrlich."""
            
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,  # Use dynamic session_id from parameter
                system_message=system_message
            ).with_model(provider, model_name)
            
            logger.info(f"✅ AI Chat initialized: {provider}/{model_name}")
            return chat
            
    except Exception as e:
        logger.error(f"Error initializing AI chat: {e}")
        raise


async def handle_trading_actions(user_message: str, ai_response: str, db, settings: dict, latest_market_data: dict) -> str:
    """
    Parse user message and AI response for trading actions
    Simple keyword-based detection for MVP
    """
    from ai_trading_functions import FUNCTION_MAP
    
    user_lower = user_message.lower()
    
    try:
        # Close all positions
        if any(keyword in user_lower for keyword in ['schließe alle', 'close all', 'alle positionen schließen']):
            result = await FUNCTION_MAP['close_all_trades'](db)
            return result.get('message', 'Aktion ausgeführt')
        
        # Close specific symbol
        for symbol in ['gold', 'silver', 'wti', 'brent', 'platin', 'palladium']:
            if f'schließe {symbol}' in user_lower or f'close {symbol}' in user_lower:
                symbol_map = {
                    'gold': 'GOLD', 'silver': 'SILVER', 
                    'wti': 'WTI_CRUDE', 'brent': 'BRENT_CRUDE',
                    'platin': 'PLATINUM', 'palladium': 'PALLADIUM'
                }
                result = await FUNCTION_MAP['close_trades_by_symbol'](db, symbol_map.get(symbol, symbol.upper()))
                return result.get('message', 'Aktion ausgeführt')
        
        # Show positions
        if any(keyword in user_lower for keyword in ['zeige positionen', 'show positions', 'offene trades']):
            result = await FUNCTION_MAP['get_open_positions'](db)
            return result.get('message', 'Aktion ausgeführt')
        
        # Buy/Sell detection
        for direction in ['buy', 'kaufe', 'long', 'sell', 'verkaufe', 'short']:
            if direction in user_lower:
                # Extract symbol
                for symbol_key, symbol_value in {
                    'gold': 'GOLD', 'silver': 'SILVER', 'silber': 'SILVER',
                    'wti': 'WTI_CRUDE', 'öl': 'WTI_CRUDE', 'oil': 'WTI_CRUDE',
                    'brent': 'BRENT_CRUDE', 'platin': 'PLATINUM', 'platinum': 'PLATINUM',
                    'palladium': 'PALLADIUM', 'kupfer': 'COPPER', 'copper': 'COPPER'
                }.items():
                    if symbol_key in user_lower:
                        trade_direction = 'BUY' if direction in ['buy', 'kaufe', 'long'] else 'SELL'
                        result = await FUNCTION_MAP['execute_trade'](
                            db=db,
                            settings=settings,
                            symbol=symbol_value,
                            direction=trade_direction
                        )
                        return result.get('message', 'Trade ausgeführt')
        
        return None
        
    except Exception as e:
        logger.error(f"Error in trading actions: {e}")
        return None


async def send_chat_message(message: str, settings: dict, latest_market_data: dict, open_trades: list, ai_provider: str = "openai", model: str = None, session_id: str = "default-session", db=None):
    """Send a message to the AI and get response with session context and function calling"""
    try:
        # Get AI chat instance with session_id
        chat = await get_ai_chat_instance(settings, ai_provider, model, session_id)
        
        # Only add trading context for non-confirmation messages
        # Short messages like "Ja", "OK", "Nein" are likely confirmations
        is_confirmation = message.strip().lower() in ['ja', 'ok', 'okay', 'yes', 'nein', 'no', 'nope']
        
        # Check if auto-trading is active for function calling
        auto_trading_active = settings.get('auto_trading', False)
        
        if is_confirmation:
            # For confirmations, send message as-is without context
            full_message = message
        else:
            # Add trading context for new questions
            context = get_trading_context(settings, latest_market_data, open_trades)
            full_message = f"{context}\n\nBENUTZER FRAGE: {message}"
        
        # Send message based on provider type
        if ai_provider == "ollama":
            # Ollama
            response = await chat.send_message(full_message)
        else:
            # Emergentintegrations - send_message is async (with fallback)
            try:
                from emergentintegrations.llm.chat import UserMessage
            except ImportError:
                from llm_fallback import get_user_message
                UserMessage = get_user_message
            user_msg = UserMessage(text=full_message)
            
            # send_message returns AssistantMessage - await it!
            response_obj = await chat.send_message(user_msg)
            
            # Extract text from response
            if hasattr(response_obj, 'text'):
                response = response_obj.text
            elif isinstance(response_obj, str):
                response = response_obj
            else:
                response = str(response_obj)
        
        logger.info(f"✅ AI Response generated (length: {len(response)})")
        
        # Function calling: Check if user wants to execute trades (only if auto-trading active and db available)
        if auto_trading_active and db is not None:
            action_result = await handle_trading_actions(message, response, db, settings, latest_market_data)
            if action_result:
                # Append action result to response
                response = f"{response}\n\n{action_result}"
        
        return {
            "success": True,
            "response": response,
            "provider": ai_provider,
            "model": model or "default"
        }
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return {
            "success": False,
            "response": f"Fehler: {str(e)}",
            "provider": ai_provider
        }

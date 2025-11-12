"""
AI Trading Functions - Function calling interface for AI Chat
Allows AI to execute trades when Auto-Trading is active
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Available functions that AI can call
AVAILABLE_FUNCTIONS = {
    "execute_trade": {
        "name": "execute_trade",
        "description": "Platziert einen neuen Trade auf der gewählten Plattform",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Rohstoff-Symbol (GOLD, SILVER, WTI_CRUDE, BRENT_CRUDE, etc.)",
                    "enum": ["GOLD", "SILVER", "PLATINUM", "PALLADIUM", "WTI_CRUDE", "BRENT_CRUDE", 
                             "NATURAL_GAS", "COPPER", "WHEAT", "CORN", "SOYBEANS", "COFFEE", "SUGAR", "COTTON"]
                },
                "direction": {
                    "type": "string",
                    "description": "Trade-Richtung",
                    "enum": ["BUY", "SELL"]
                },
                "quantity": {
                    "type": "number",
                    "description": "Positionsgröße (wird basierend auf Risiko berechnet wenn nicht angegeben)"
                },
                "stop_loss": {
                    "type": "number",
                    "description": "Stop Loss Preis"
                },
                "take_profit": {
                    "type": "number",
                    "description": "Take Profit Preis"
                },
                "platform": {
                    "type": "string",
                    "description": "Trading-Plattform",
                    "enum": ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]
                }
            },
            "required": ["symbol", "direction"]
        }
    },
    "close_trade": {
        "name": "close_trade",
        "description": "Schließt einen spezifischen Trade anhand der Trade-ID",
        "parameters": {
            "type": "object",
            "properties": {
                "trade_id": {
                    "type": "string",
                    "description": "Die ID des zu schließenden Trades"
                }
            },
            "required": ["trade_id"]
        }
    },
    "close_all_trades": {
        "name": "close_all_trades",
        "description": "Schließt ALLE offenen Trades auf allen Plattformen",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "close_trades_by_symbol": {
        "name": "close_trades_by_symbol",
        "description": "Schließt alle Trades für ein bestimmtes Symbol (z.B. alle Gold-Trades)",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Rohstoff-Symbol (GOLD, SILVER, WTI_CRUDE, etc.)"
                }
            },
            "required": ["symbol"]
        }
    },
    "get_open_positions": {
        "name": "get_open_positions",
        "description": "Holt alle aktuell offenen Positionen mit Details",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    "update_stop_loss": {
        "name": "update_stop_loss",
        "description": "Aktualisiert den Stop Loss für einen Trade",
        "parameters": {
            "type": "object",
            "properties": {
                "trade_id": {
                    "type": "string",
                    "description": "Die ID des Trades"
                },
                "new_stop_loss": {
                    "type": "number",
                    "description": "Neuer Stop Loss Preis"
                }
            },
            "required": ["trade_id", "new_stop_loss"]
        }
    }
}


async def execute_trade(db, settings: Dict, symbol: str, direction: str, 
                       quantity: float = None, stop_loss: float = None, 
                       take_profit: float = None, platform: str = None) -> Dict[str, Any]:
    """
    Execute a trade via AI command
    """
    try:
        # Determine platform
        if not platform:
            active_platforms = settings.get('active_platforms', [])
            platform = active_platforms[0] if active_platforms else 'MT5_LIBERTEX'
        
        # Get current price from latest market data
        from server import latest_market_data
        commodity_data = latest_market_data.get(symbol, {})
        current_price = commodity_data.get('price', 0)
        
        if not current_price:
            return {
                "success": False,
                "error": f"Kein aktueller Preis für {symbol} verfügbar"
            }
        
        # Calculate quantity if not provided (2% risk default)
        if not quantity:
            account_balance = 10000  # Default, should fetch from platform
            risk_percent = 2.0
            risk_amount = account_balance * (risk_percent / 100)
            
            if stop_loss:
                price_diff = abs(current_price - stop_loss)
                quantity = risk_amount / price_diff if price_diff > 0 else 0.01
            else:
                quantity = 0.01  # Minimum
        
        # Create trade in database
        trade = {
            "id": str(uuid.uuid4()),
            "commodity": symbol,
            "entry_price": current_price,
            "quantity": quantity,
            "trade_type": direction,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "OPEN",
            "platform": platform,
            "mode": platform,
            "timestamp": datetime.utcnow().isoformat(),
            "executed_by": "AI_CHAT"
        }
        
        # Save to database
        await db.trades.insert_one(trade)
        
        logger.info(f"✅ AI executed trade: {direction} {symbol} @{current_price} on {platform}")
        
        return {
            "success": True,
            "trade_id": trade['id'],
            "message": f"✅ Trade ausgeführt: {direction} {symbol} @{current_price:.2f}",
            "details": {
                "symbol": symbol,
                "direction": direction,
                "entry": current_price,
                "quantity": quantity,
                "sl": stop_loss,
                "tp": take_profit,
                "platform": platform
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def close_trade(db, trade_id: str) -> Dict[str, Any]:
    """Close a specific trade"""
    try:
        trade = await db.trades.find_one({"id": trade_id})
        
        if not trade:
            return {
                "success": False,
                "error": f"Trade {trade_id} nicht gefunden"
            }
        
        # Update trade status
        await db.trades.update_one(
            {"id": trade_id},
            {"$set": {"status": "CLOSED", "closed_at": datetime.utcnow().isoformat()}}
        )
        
        logger.info(f"✅ AI closed trade: {trade_id}")
        
        return {
            "success": True,
            "message": f"✅ Trade geschlossen: {trade.get('commodity')} {trade.get('trade_type')}",
            "trade_id": trade_id
        }
        
    except Exception as e:
        logger.error(f"Error closing trade: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def close_all_trades(db) -> Dict[str, Any]:
    """Close all open trades"""
    try:
        open_trades = await db.trades.find({"status": "OPEN"}).to_list(100)
        
        closed_count = 0
        for trade in open_trades:
            await db.trades.update_one(
                {"id": trade['id']},
                {"$set": {"status": "CLOSED", "closed_at": datetime.utcnow().isoformat()}}
            )
            closed_count += 1
        
        logger.info(f"✅ AI closed all trades: {closed_count} trades")
        
        return {
            "success": True,
            "message": f"✅ Alle {closed_count} offenen Trades geschlossen",
            "closed_count": closed_count
        }
        
    except Exception as e:
        logger.error(f"Error closing all trades: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def close_trades_by_symbol(db, symbol: str) -> Dict[str, Any]:
    """Close all trades for a specific symbol"""
    try:
        open_trades = await db.trades.find({
            "status": "OPEN",
            "commodity": symbol
        }).to_list(100)
        
        closed_count = 0
        for trade in open_trades:
            await db.trades.update_one(
                {"id": trade['id']},
                {"$set": {"status": "CLOSED", "closed_at": datetime.utcnow().isoformat()}}
            )
            closed_count += 1
        
        logger.info(f"✅ AI closed {symbol} trades: {closed_count} trades")
        
        return {
            "success": True,
            "message": f"✅ {closed_count} {symbol}-Trades geschlossen",
            "closed_count": closed_count,
            "symbol": symbol
        }
        
    except Exception as e:
        logger.error(f"Error closing trades by symbol: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_open_positions(db) -> Dict[str, Any]:
    """Get all open positions"""
    try:
        open_trades = await db.trades.find({"status": "OPEN"}).to_list(100)
        
        positions_text = []
        for trade in open_trades:
            positions_text.append(
                f"- {trade.get('trade_type')} {trade.get('commodity')} "
                f"@{trade.get('entry_price'):.2f} "
                f"(SL: {trade.get('stop_loss', 'N/A')}, TP: {trade.get('take_profit', 'N/A')})"
            )
        
        return {
            "success": True,
            "positions": open_trades,
            "count": len(open_trades),
            "message": f"📊 {len(open_trades)} offene Positionen:\n" + "\n".join(positions_text) if positions_text else "Keine offenen Positionen"
        }
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def update_stop_loss(db, trade_id: str, new_stop_loss: float) -> Dict[str, Any]:
    """Update stop loss for a trade"""
    try:
        trade = await db.trades.find_one({"id": trade_id})
        
        if not trade:
            return {
                "success": False,
                "error": f"Trade {trade_id} nicht gefunden"
            }
        
        await db.trades.update_one(
            {"id": trade_id},
            {"$set": {"stop_loss": new_stop_loss}}
        )
        
        logger.info(f"✅ AI updated SL for {trade_id}: {new_stop_loss}")
        
        return {
            "success": True,
            "message": f"✅ Stop Loss aktualisiert: {trade.get('commodity')} SL → {new_stop_loss:.2f}",
            "trade_id": trade_id,
            "new_stop_loss": new_stop_loss
        }
        
    except Exception as e:
        logger.error(f"Error updating stop loss: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Function dispatcher
FUNCTION_MAP = {
    "execute_trade": execute_trade,
    "close_trade": close_trade,
    "close_all_trades": close_all_trades,
    "close_trades_by_symbol": close_trades_by_symbol,
    "get_open_positions": get_open_positions,
    "update_stop_loss": update_stop_loss
}

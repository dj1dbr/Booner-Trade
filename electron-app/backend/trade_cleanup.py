"""
Trade Cleanup Service
Bereinigt fehlerhafte Trades und Duplikate aus der Datenbank
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

async def cleanup_error_trades(db):
    """Lösche alle Trades mit MetaAPI Error Codes"""
    try:
        # Finde Trades mit Error Codes im Ticket oder Commodity
        error_conditions = [
            {"mt5_ticket": {"$regex": "TRADE_RETCODE", "$options": "i"}},
            {"ticket": {"$regex": "TRADE_RETCODE", "$options": "i"}},
            {"commodity": {"$regex": "TRADE_RETCODE", "$options": "i"}}
        ]
        
        error_trades = await db.trades.find({"$or": error_conditions}).to_list(1000)
        
        if error_trades:
            error_count = len(error_trades)
            logger.info(f"🗑️ Gefunden: {error_count} fehlerhafte Trades (TRADE_RETCODE_*)")
            
            # Lösche alle fehlerhaften Trades
            result = await db.trades.delete_many({"$or": error_conditions})
            
            logger.info(f"✅ {result.deleted_count} fehlerhafte Trades gelöscht")
            return result.deleted_count
        else:
            logger.info("✅ Keine fehlerhaften Trades gefunden")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Cleanup: {e}")
        return 0


async def cleanup_duplicate_trades(db):
    """Lösche doppelte Trades (gleiche Ticket-Nummer)"""
    try:
        # Alle Trades holen
        all_trades = await db.trades.find({}, {"_id": 1, "mt5_ticket": 1, "ticket": 1, "id": 1, "timestamp": 1, "profit_loss": 1}).to_list(10000)
        
        # Gruppiere nach Ticket
        ticket_groups = {}
        for trade in all_trades:
            ticket = trade.get('mt5_ticket') or trade.get('ticket')
            if ticket:
                if ticket not in ticket_groups:
                    ticket_groups[ticket] = []
                ticket_groups[ticket].append(trade)
        
        # Finde Duplikate
        duplicates_to_delete = []
        for ticket, trades in ticket_groups.items():
            if len(trades) > 1:
                logger.info(f"🔍 Duplikat gefunden: Ticket {ticket} ({len(trades)} Einträge)")
                
                # Sortiere nach: Hat P&L? Dann neuester Timestamp
                trades_sorted = sorted(
                    trades, 
                    key=lambda x: (
                        x.get('profit_loss') is not None and x.get('profit_loss') != 0,  # Hat P&L?
                        x.get('timestamp', '')  # Neuester
                    ),
                    reverse=True
                )
                
                # Behalte den ersten (besten), lösche den Rest
                keep_trade = trades_sorted[0]
                delete_trades = trades_sorted[1:]
                
                for trade in delete_trades:
                    duplicates_to_delete.append(trade['id'])
                    logger.info(f"   🗑️ Lösche Duplikat: ID {trade['id']}")
        
        if duplicates_to_delete:
            result = await db.trades.delete_many({"id": {"$in": duplicates_to_delete}})
            logger.info(f"✅ {result.deleted_count} doppelte Trades gelöscht")
            return result.deleted_count
        else:
            logger.info("✅ Keine Duplikate gefunden")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Duplikat-Cleanup: {e}")
        return 0


async def run_full_cleanup():
    """Führe vollständiges Cleanup durch"""
    try:
        # Verbinde mit MongoDB
        mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
        client = AsyncIOMotorClient(mongo_url)
        db = client['trading_app']
        
        logger.info("🧹 Starte Trade-Cleanup...")
        
        # 1. Lösche fehlerhafte Trades
        error_deleted = await cleanup_error_trades(db)
        
        # 2. Lösche Duplikate
        duplicate_deleted = await cleanup_duplicate_trades(db)
        
        total_deleted = error_deleted + duplicate_deleted
        
        logger.info(f"✅ Cleanup abgeschlossen: {total_deleted} Trades gelöscht")
        
        client.close()
        
        return {
            "success": True,
            "error_trades_deleted": error_deleted,
            "duplicate_trades_deleted": duplicate_deleted,
            "total_deleted": total_deleted
        }
        
    except Exception as e:
        logger.error(f"❌ Cleanup fehlgeschlagen: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Für direkten Aufruf
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_full_cleanup())
    print(f"\n{'='*50}")
    print(f"Cleanup Ergebnis:")
    print(f"  Fehlerhafte Trades gelöscht: {result.get('error_trades_deleted', 0)}")
    print(f"  Duplikate gelöscht: {result.get('duplicate_trades_deleted', 0)}")
    print(f"  Gesamt: {result.get('total_deleted', 0)}")
    print(f"{'='*50}\n")

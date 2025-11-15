"""
MetaAPI SDK Connector - Stabiler als REST API!
Verwendet offizielles MetaAPI Python SDK
"""
import logging
from typing import Dict, List, Optional, Any
from metaapi_cloud_sdk import MetaApi
import asyncio

logger = logging.getLogger(__name__)

class MetaAPISDKConnector:
    """MetaAPI SDK-basierter Connector - viel stabiler!"""
    
    def __init__(self, account_id: str, token: str):
        self.account_id = account_id
        self.token = token
        self.api = MetaApi(token)
        self.account = None
        self.connection = None
        self.connected = False
        
        logger.info(f"MetaAPI SDK Connector initialized: {account_id}")
    
    async def connect(self):
        """Verbinde mit MetaAPI über SDK"""
        try:
            # Account abrufen
            self.account = await self.api.metatrader_account_api.get_account(self.account_id)
            
            # Warte bis deployed
            if self.account.state != 'DEPLOYED':
                logger.info(f"Account {self.account_id} wird deployed...")
                await self.account.deploy()
                await self.account.wait_deployed()
            
            # Verbindung erstellen
            self.connection = self.account.get_streaming_connection()
            await self.connection.connect()
            
            # Warte bis verbunden und synchronisiert
            await self.connection.wait_synchronized()
            
            self.connected = True
            logger.info(f"✅ MetaAPI SDK verbunden: {self.account_id}")
            return True
            
        except Exception as e:
            logger.error(f"MetaAPI SDK Verbindungsfehler: {e}")
            self.connected = False
            return False
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Hole Account-Informationen"""
        try:
            if not self.connection:
                return None
            
            account_info = self.connection.account_information
            terminal_state = self.connection.terminal_state
            
            return {
                'balance': account_info.balance if account_info else 0,
                'equity': account_info.equity if account_info else 0,
                'margin': account_info.margin if account_info else 0,
                'freeMargin': account_info.freeMargin if account_info else 0,
                'leverage': account_info.leverage if account_info else 0,
                'connected': terminal_state.connected if terminal_state else False,
                'connectedToBroker': terminal_state.connectedToBroker if terminal_state else False
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Hole offene Positionen"""
        try:
            if not self.connection:
                return []
            
            positions = self.connection.terminal_state.positions if self.connection.terminal_state else []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.id,
                    'symbol': pos.symbol,
                    'type': pos.type,  # POSITION_TYPE_BUY oder POSITION_TYPE_SELL
                    'volume': pos.volume,
                    'price_open': pos.openPrice,
                    'price_current': pos.currentPrice,
                    'profit': pos.profit,
                    'swap': pos.swap,
                    'time': pos.time,
                    'sl': pos.stopLoss if hasattr(pos, 'stopLoss') else None,
                    'tp': pos.takeProfit if hasattr(pos, 'takeProfit') else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def create_market_order(self, symbol: str, order_type: str, volume: float, 
                                   sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Platziere Market Order"""
        try:
            if not self.connection:
                return {'success': False, 'error': 'Not connected'}
            
            # Order ausführen
            result = await self.connection.create_market_buy_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            ) if order_type == 'BUY' else await self.connection.create_market_sell_order(
                symbol=symbol,
                volume=volume,
                stop_loss=sl,
                take_profit=tp
            )
            
            logger.info(f"✅ Order platziert: {symbol} {order_type} {volume} Lots")
            
            return {
                'success': True,
                'orderId': result.orderId if hasattr(result, 'orderId') else result['orderId'],
                'positionId': result.positionId if hasattr(result, 'positionId') else result.get('positionId')
            }
            
        except Exception as e:
            logger.error(f"Order execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close_position(self, position_id: str) -> bool:
        """Schließe Position"""
        try:
            if not self.connection:
                return False
            
            await self.connection.close_position(position_id)
            logger.info(f"✅ Position geschlossen: {position_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return False
    
    async def disconnect(self):
        """Verbindung trennen"""
        try:
            if self.connection:
                await self.connection.close()
            self.connected = False
            logger.info(f"MetaAPI SDK disconnected: {self.account_id}")
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    async def is_connected(self) -> bool:
        """Prüfe ob verbunden"""
        try:
            if not self.connection or not self.connection.terminal_state:
                return False
            return self.connection.terminal_state.connected and self.connection.terminal_state.connectedToBroker
        except:
            return False


async def test_sdk_connector():
    """Test-Funktion"""
    import os
    
    token = os.getenv('METAAPI_TOKEN')
    account_id = os.getenv('METAAPI_ACCOUNT_ID')
    
    connector = MetaAPISDKConnector(account_id, token)
    
    # Verbinden
    await connector.connect()
    
    # Account Info
    info = await connector.get_account_info()
    print(f"Balance: {info['balance']}, Equity: {info['equity']}")
    
    # Positionen
    positions = await connector.get_positions()
    print(f"Offene Positionen: {len(positions)}")
    
    # Disconnect
    await connector.disconnect()


if __name__ == "__main__":
    asyncio.run(test_sdk_connector())

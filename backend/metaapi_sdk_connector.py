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
            
            # Get terminal state which contains account information
            terminal_state = self.connection.terminal_state
            if not terminal_state:
                logger.warning("Terminal state not available yet")
                return None
            
            # Access account information from terminal state
            account_info = terminal_state.account_information
            
            return {
                'balance': account_info.get('balance', 0) if account_info else 0,
                'equity': account_info.get('equity', 0) if account_info else 0,
                'margin': account_info.get('margin', 0) if account_info else 0,
                'freeMargin': account_info.get('freeMargin', 0) if account_info else 0,
                'leverage': account_info.get('leverage', 0) if account_info else 0,
                'connected': terminal_state.connected if hasattr(terminal_state, 'connected') else False,
                'connectedToBroker': terminal_state.connected_to_broker if hasattr(terminal_state, 'connected_to_broker') else False
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}", exc_info=True)
            return None
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Hole offene Positionen"""
        try:
            if not self.connection:
                return []
            
            terminal_state = self.connection.terminal_state
            if not terminal_state:
                return []
            
            positions = terminal_state.positions if hasattr(terminal_state, 'positions') else []
            
            result = []
            for pos in positions:
                # Handle both dict and object types
                if isinstance(pos, dict):
                    result.append({
                        'ticket': pos.get('id'),
                        'id': pos.get('id'),
                        'positionId': pos.get('id'),
                        'symbol': pos.get('symbol'),
                        'type': pos.get('type'),
                        'volume': pos.get('volume'),
                        'price_open': pos.get('openPrice'),
                        'openPrice': pos.get('openPrice'),
                        'price_current': pos.get('currentPrice'),
                        'currentPrice': pos.get('currentPrice'),
                        'profit': pos.get('profit'),
                        'unrealizedProfit': pos.get('profit'),
                        'swap': pos.get('swap'),
                        'time': pos.get('time'),
                        'openTime': pos.get('time'),
                        'updateTime': pos.get('updateTime'),
                        'sl': pos.get('stopLoss'),
                        'stopLoss': pos.get('stopLoss'),
                        'tp': pos.get('takeProfit'),
                        'takeProfit': pos.get('takeProfit')
                    })
                else:
                    result.append({
                        'ticket': pos.id if hasattr(pos, 'id') else None,
                        'id': pos.id if hasattr(pos, 'id') else None,
                        'positionId': pos.id if hasattr(pos, 'id') else None,
                        'symbol': pos.symbol if hasattr(pos, 'symbol') else None,
                        'type': pos.type if hasattr(pos, 'type') else None,
                        'volume': pos.volume if hasattr(pos, 'volume') else None,
                        'price_open': pos.openPrice if hasattr(pos, 'openPrice') else None,
                        'openPrice': pos.openPrice if hasattr(pos, 'openPrice') else None,
                        'price_current': pos.currentPrice if hasattr(pos, 'currentPrice') else None,
                        'currentPrice': pos.currentPrice if hasattr(pos, 'currentPrice') else None,
                        'profit': pos.profit if hasattr(pos, 'profit') else None,
                        'unrealizedProfit': pos.profit if hasattr(pos, 'profit') else None,
                        'swap': pos.swap if hasattr(pos, 'swap') else None,
                        'time': pos.time if hasattr(pos, 'time') else None,
                        'openTime': pos.time if hasattr(pos, 'time') else None,
                        'updateTime': pos.updateTime if hasattr(pos, 'updateTime') else None,
                        'sl': pos.stopLoss if hasattr(pos, 'stopLoss') else None,
                        'stopLoss': pos.stopLoss if hasattr(pos, 'stopLoss') else None,
                        'tp': pos.takeProfit if hasattr(pos, 'takeProfit') else None,
                        'takeProfit': pos.takeProfit if hasattr(pos, 'takeProfit') else None
                    })
            
            return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}", exc_info=True)
            return []
    
    async def create_market_order(self, symbol: str, order_type: str, volume: float, 
                                   sl: float = None, tp: float = None) -> Dict[str, Any]:
        """Platziere Market Order mit Timeout-Handling"""
        try:
            if not self.connection:
                logger.error("SDK not connected!")
                return {'success': False, 'error': 'Not connected to trading platform'}
            
            logger.info(f"🔄 Placing order: {symbol} {order_type} {volume} lots (SL: {sl}, TP: {tp})")
            
            # Order ausführen mit asyncio.wait_for für Timeout
            import asyncio
            
            try:
                if order_type.upper() == 'BUY':
                    order_coro = self.connection.create_market_buy_order(
                        symbol=symbol,
                        volume=volume,
                        stop_loss=sl,
                        take_profit=tp
                    )
                else:
                    order_coro = self.connection.create_market_sell_order(
                        symbol=symbol,
                        volume=volume,
                        stop_loss=sl,
                        take_profit=tp
                    )
                
                # Warte max 30 Sekunden auf Antwort
                result = await asyncio.wait_for(order_coro, timeout=30.0)
                
            except asyncio.TimeoutError:
                logger.error(f"❌ Order timeout after 30 seconds")
                return {'success': False, 'error': 'Order timeout - Platform nicht erreichbar (30s)'}
            
            logger.info(f"✅ Order platziert: {symbol} {order_type} {volume} Lots")
            
            return {
                'success': True,
                'orderId': result.orderId if hasattr(result, 'orderId') else result.get('orderId'),
                'positionId': result.positionId if hasattr(result, 'positionId') else result.get('positionId'),
                'message': f'Order executed: {symbol} {order_type} {volume} lots'
            }
            
        except Exception as e:
            logger.error(f"❌ Order execution error: {e}", exc_info=True)
            return {'success': False, 'error': f'Trade execution failed: {str(e)}'}
    
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
    
    async def get_symbol_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current symbol price"""
        try:
            if not self.connection:
                return None
            
            # Get symbol price from terminal state
            terminal_state = self.connection.terminal_state
            if not terminal_state:
                return None
            
            # Access price data - terminal_state.price is a dict
            if hasattr(terminal_state, 'price'):
                prices = terminal_state.price
                # price is actually a method, we need to call it
                if callable(prices):
                    try:
                        # Try to get the price by calling the method
                        price_data = await prices(symbol)
                        if price_data:
                            return {
                                'symbol': symbol,
                                'bid': price_data.get('bid') if isinstance(price_data, dict) else getattr(price_data, 'bid', None),
                                'ask': price_data.get('ask') if isinstance(price_data, dict) else getattr(price_data, 'ask', None),
                                'time': price_data.get('time') if isinstance(price_data, dict) else getattr(price_data, 'time', None)
                            }
                    except:
                        pass
                elif isinstance(prices, dict) and symbol in prices:
                    price_data = prices[symbol]
                    return {
                        'symbol': symbol,
                        'bid': price_data.get('bid') if isinstance(price_data, dict) else getattr(price_data, 'bid', None),
                        'ask': price_data.get('ask') if isinstance(price_data, dict) else getattr(price_data, 'ask', None),
                        'time': price_data.get('time') if isinstance(price_data, dict) else getattr(price_data, 'time', None)
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error getting symbol price for {symbol}: {e}", exc_info=True)
            return None
    
    async def get_symbols(self) -> List[str]:
        """Get all available symbols"""
        try:
            if not self.connection:
                return []
            
            terminal_state = self.connection.terminal_state
            if not terminal_state:
                return []
            
            # Get specifications
            if hasattr(terminal_state, 'specifications'):
                specs = terminal_state.specifications
                if isinstance(specs, dict):
                    return list(specs.keys())
                elif isinstance(specs, list):
                    return [s.get('symbol') if isinstance(s, dict) else s.symbol for s in specs]
            
            return []
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []


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

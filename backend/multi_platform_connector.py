"""
Multi-Platform Connector - SDK VERSION (Viel stabiler!)
Migrated from REST API to official metaapi-python-sdk
Supports: MT5 Libertex Demo, MT5 ICMarkets Demo, MT5 Libertex REAL
Removed: Bitpanda (as requested)
"""

import logging
import os
from typing import Optional, Dict, List, Any
from metaapi_sdk_connector import MetaAPISDKConnector

logger = logging.getLogger(__name__)

class MultiPlatformConnector:
    """Manages connections to multiple MT5 platforms using stable SDK"""
    
    def __init__(self):
        self.platforms = {}
        self.metaapi_token = os.environ.get('METAAPI_TOKEN', '')
        
        # MT5 Libertex Demo
        libertex_demo_id = os.environ.get('METAAPI_ACCOUNT_ID', '5cc9abd1-671a-447e-ab93-5abbfe0ed941')
        self.platforms['MT5_LIBERTEX_DEMO'] = {
            'type': 'MT5',
            'name': 'MT5 Libertex Demo',
            'account_id': libertex_demo_id,
            'region': 'london',
            'connector': None,
            'active': False,
            'balance': 0.0,
            'is_real': False
        }
        
        # MT5 ICMarkets Demo
        icmarkets_demo_id = os.environ.get('METAAPI_ICMARKETS_ACCOUNT_ID', 'd2605e89-7bc2-4144-9f7c-951edd596c39')
        self.platforms['MT5_ICMARKETS_DEMO'] = {
            'type': 'MT5',
            'name': 'MT5 ICMarkets Demo',
            'account_id': icmarkets_demo_id,
            'region': 'london',
            'connector': None,
            'active': False,
            'balance': 0.0,
            'is_real': False
        }
        
        # MT5 Libertex REAL (wenn in .env konfiguriert)
        libertex_real_id = os.environ.get('METAAPI_LIBERTEX_REAL_ACCOUNT_ID', '')
        if libertex_real_id and libertex_real_id != 'PLACEHOLDER_REAL_ACCOUNT_ID':
            self.platforms['MT5_LIBERTEX_REAL'] = {
                'type': 'MT5',
                'name': '💰 MT5 Libertex REAL 💰',
                'account_id': libertex_real_id,
                'region': 'london',
                'connector': None,
                'active': False,
                'balance': 0.0,
                'is_real': True  # ECHTES GELD!
            }
            logger.warning("⚠️  REAL MONEY ACCOUNT available: MT5_LIBERTEX_REAL")
        else:
            logger.info("ℹ️  Real Account not configured (only Demo available)")
        
        # Legacy compatibility mappings
        if 'MT5_LIBERTEX_DEMO' in self.platforms:
            self.platforms['MT5_LIBERTEX'] = self.platforms['MT5_LIBERTEX_DEMO']
        if 'MT5_ICMARKETS_DEMO' in self.platforms:
            self.platforms['MT5_ICMARKETS'] = self.platforms['MT5_ICMARKETS_DEMO']
        
        logger.info(f"MultiPlatformConnector (SDK) initialized with {len(self.platforms)} platform(s)")
    
    async def connect_platform(self, platform_name: str) -> bool:
        """Connect to platform using stable SDK"""
        try:
            # Handle legacy names
            if platform_name == 'MT5_LIBERTEX':
                platform_name = 'MT5_LIBERTEX_DEMO'
            elif platform_name == 'MT5_ICMARKETS':
                platform_name = 'MT5_ICMARKETS_DEMO'
            
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return False
            
            platform = self.platforms[platform_name]
            
            # Already connected?
            if platform.get('active') and platform.get('connector'):
                connector = platform['connector']
                if await connector.is_connected():
                    logger.debug(f"ℹ️  {platform_name} already connected")
                    return True
                else:
                    logger.warning(f"⚠️  {platform_name} connection lost, reconnecting...")
            
            # Create SDK connector
            logger.info(f"🔄 Connecting to {platform_name} via SDK...")
            connector = MetaAPISDKConnector(
                account_id=platform['account_id'],
                token=self.metaapi_token
            )
            
            # Connect
            success = await connector.connect()
            if success:
                account_info = await connector.get_account_info()
                
                platform['connector'] = connector
                platform['active'] = True
                platform['balance'] = account_info.get('balance', 0.0) if account_info else 0.0
                
                logger.info(f"✅ SDK Connected: {platform_name} | Balance: €{platform['balance']:.2f}")
                return True
            else:
                logger.error(f"❌ Failed to connect {platform_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error connecting to {platform_name}: {e}", exc_info=True)
            return False
    
    async def disconnect_platform(self, platform_name: str) -> bool:
        """Disconnect from platform"""
        try:
            if platform_name in self.platforms:
                platform = self.platforms[platform_name]
                if platform.get('connector'):
                    await platform['connector'].disconnect()
                platform['active'] = False
                platform['connector'] = None
                logger.info(f"Disconnected from {platform_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error disconnecting from {platform_name}: {e}")
            return False
    
    async def get_account_info(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get account information"""
        try:
            # Handle legacy names
            if platform_name == 'MT5_LIBERTEX':
                platform_name = 'MT5_LIBERTEX_DEMO'
            elif platform_name == 'MT5_ICMARKETS':
                platform_name = 'MT5_ICMARKETS_DEMO'
            
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return None
            
            platform = self.platforms[platform_name]
            
            # Connect if needed
            if not platform['active'] or not platform['connector']:
                await self.connect_platform(platform_name)
            
            if platform['connector']:
                account_info = await platform['connector'].get_account_info()
                if account_info:
                    platform['balance'] = account_info.get('balance', 0.0)
                return account_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info for {platform_name}: {e}")
            return None
    
    async def execute_trade(self, platform_name: str, symbol: str, action: str, 
                           volume: float, stop_loss: float = None, 
                           take_profit: float = None) -> Optional[Dict[str, Any]]:
        """Execute trade via SDK"""
        try:
            # Handle legacy names
            if platform_name == 'MT5_LIBERTEX':
                platform_name = 'MT5_LIBERTEX_DEMO'
            elif platform_name == 'MT5_ICMARKETS':
                platform_name = 'MT5_ICMARKETS_DEMO'
            
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return None
            
            platform = self.platforms[platform_name]
            
            # SAFETY: Warnung bei Real Account
            if platform.get('is_real', False):
                logger.warning(f"⚠️⚠️⚠️  EXECUTING REAL MONEY TRADE on {platform_name}! ⚠️⚠️⚠️")
            
            # Connect if needed
            if not platform['active'] or not platform['connector']:
                await self.connect_platform(platform_name)
            
            if not platform['connector']:
                logger.error(f"Platform {platform_name} not connected")
                return None
            
            # Execute via SDK
            result = await platform['connector'].create_market_order(
                symbol=symbol,
                order_type=action.upper(),
                volume=volume,
                sl=stop_loss,
                tp=take_profit
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade on {platform_name}: {e}")
            return None
    
    async def get_open_positions(self, platform_name: str) -> List[Dict[str, Any]]:
        """Get open positions - DIREKT von MT5, keine Deduplizierung"""
        try:
            # Handle legacy names
            if platform_name == 'MT5_LIBERTEX':
                platform_name = 'MT5_LIBERTEX_DEMO'
            elif platform_name == 'MT5_ICMARKETS':
                platform_name = 'MT5_ICMARKETS_DEMO'
            
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return []
            
            platform = self.platforms[platform_name]
            
            if not platform['active'] or not platform['connector']:
                return []
            
            # Hole Positionen DIREKT vom SDK (MT5-Sync)
            positions = await platform['connector'].get_positions()
            
            # Filter nur offensichtliche Fehler (TRADE_RETCODE)
            clean_positions = []
            for pos in positions:
                ticket = pos.get('ticket') or pos.get('id') or pos.get('positionId')
                symbol = pos.get('symbol', '')
                
                # Skip nur error positions
                if ticket and 'TRADE_RETCODE' in str(ticket):
                    continue
                if 'TRADE_RETCODE' in symbol:
                    continue
                
                clean_positions.append(pos)
            
            logger.info(f"{platform_name}: {len(clean_positions)} open positions from MT5")
            return clean_positions
            
        except Exception as e:
            logger.error(f"Error getting positions for {platform_name}: {e}")
            return []
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Alias for compatibility"""
        # Return positions from all active platforms
        all_positions = []
        for platform_name in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO', 'MT5_LIBERTEX_REAL']:
            if platform_name in self.platforms:
                positions = await self.get_open_positions(platform_name)
                for pos in positions:
                    pos['platform'] = platform_name
                all_positions.extend(positions)
        return all_positions
    
    def get_active_platforms(self) -> List[str]:
        """Get list of active platforms"""
        return [name for name, platform in self.platforms.items() 
                if platform['active'] and name in ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO', 'MT5_LIBERTEX_REAL']]
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms"""
        # Only return actual platforms, not legacy aliases
        actual_platforms = ['MT5_LIBERTEX_DEMO', 'MT5_ICMARKETS_DEMO', 'MT5_LIBERTEX_REAL']
        return {
            name: {
                'active': platform['active'],
                'balance': platform['balance'],
                'name': platform['name'],
                'is_real': platform.get('is_real', False)
            }
            for name, platform in self.platforms.items()
            if name in actual_platforms
        }
    
    async def close_position(self, platform_name: str, position_id: str) -> bool:
        """Schließe Position auf Platform"""
        try:
            # Handle legacy names
            if platform_name == 'MT5_LIBERTEX':
                platform_name = 'MT5_LIBERTEX_DEMO'
            elif platform_name == 'MT5_ICMARKETS':
                platform_name = 'MT5_ICMARKETS_DEMO'
            
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return False
            
            platform = self.platforms[platform_name]
            
            # Connect if needed
            if not platform['active'] or not platform['connector']:
                await self.connect_platform(platform_name)
            
            if not platform['connector']:
                logger.error(f"Platform {platform_name} not connected")
                return False
            
            # Close via SDK
            success = await platform['connector'].close_position(position_id)
            
            if success:
                logger.info(f"✅ Position {position_id} geschlossen auf {platform_name}")
            else:
                logger.error(f"❌ Position {position_id} konnte nicht geschlossen werden")
            
            return success
            
        except Exception as e:
            logger.error(f"Error closing position on {platform_name}: {e}")
            return False

# Global instance
multi_platform = MultiPlatformConnector()

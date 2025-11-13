"""
Multi-Platform Connector - Manages multiple MT5 accounts and platforms
Supports: MT5 Libertex, MT5 ICMarkets, and Bitpanda
"""

import logging
import os
from typing import Optional, Dict, List, Any
from metaapi_connector import MetaAPIConnector
from bitpanda_connector import BitpandaConnector

logger = logging.getLogger(__name__)

class MultiPlatformConnector:
    """Manages connections to multiple trading platforms"""
    
    def __init__(self):
        self.platforms = {}
        self.metaapi_token = os.environ.get('METAAPI_TOKEN', '')
        
        # Initialize MT5 Libertex (Default/Primary)
        self.platforms['MT5_LIBERTEX'] = {
            'type': 'MT5',
            'name': 'MT5 Libertex',
            'account_id': os.environ.get('METAAPI_ACCOUNT_ID', '142e1085-f20b-437e-93c7-b87a0e639a30'),
            'region': 'london',
            'connector': None,
            'active': False,
            'balance': 0.0
        }
        
        # Initialize MT5 ICMarkets (Secondary)
        self.platforms['MT5_ICMARKETS'] = {
            'type': 'MT5',
            'name': 'MT5 ICMarkets',
            'account_id': os.environ.get('METAAPI_ICMARKETS_ACCOUNT_ID', 'd2605e89-7bc2-4144-9f7c-951edd596c39'),
            'region': 'london',
            'connector': None,
            'active': False,
            'balance': 0.0
        }
        
        # Initialize Bitpanda
        self.platforms['BITPANDA'] = {
            'type': 'BITPANDA',
            'name': 'Bitpanda',
            'api_key': os.environ.get('BITPANDA_API_KEY', ''),
            'connector': None,
            'active': False,
            'balance': 0.0
        }
        
        logger.info("MultiPlatformConnector initialized with 3 platforms")
    
    async def connect_platform(self, platform_name: str) -> bool:
        """Connect to a specific platform (with connection reuse)"""
        try:
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return False
            
            platform = self.platforms[platform_name]
            
            # CHECK: Already connected and active?
            if platform.get('active') and platform.get('connector'):
                logger.debug(f"ℹ️ {platform_name} already connected, reusing connection")
                return True
            
            if platform['type'] == 'MT5':
                # Create MetaAPI connector
                connector = MetaAPIConnector(
                    account_id=platform['account_id'],
                    token=self.metaapi_token
                )
                
                # Set region-specific base URL
                if platform['region'] == 'london':
                    connector.base_url = "https://mt-client-api-v1.london.agiliumtrade.ai"
                elif platform['region'] == 'new-york':
                    connector.base_url = "https://mt-client-api-v1.new-york.agiliumtrade.ai"
                elif platform['region'] == 'singapore':
                    connector.base_url = "https://mt-client-api-v1.singapore.agiliumtrade.ai"
                
                # Connect
                success = await connector.connect()
                if success:
                    platform['connector'] = connector
                    platform['active'] = True
                    platform['balance'] = connector.balance
                    logger.info(f"✅ Connected to {platform_name}: Balance={connector.balance}")
                    return True
                else:
                    logger.error(f"Failed to connect to {platform_name}")
                    return False
                    
            elif platform['type'] == 'BITPANDA':
                # Create Bitpanda connector
                connector = BitpandaConnector(api_key=platform['api_key'])
                success = await connector.connect()
                if success:
                    platform['connector'] = connector
                    platform['active'] = True
                    platform['balance'] = connector.balance
                    logger.info(f"✅ Connected to {platform_name}: Balance={connector.balance}")
                    return True
                else:
                    logger.error(f"Failed to connect to {platform_name}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to {platform_name}: {e}")
            return False
    
    async def disconnect_platform(self, platform_name: str) -> bool:
        """Disconnect from a specific platform"""
        try:
            if platform_name in self.platforms:
                platform = self.platforms[platform_name]
                platform['active'] = False
                platform['connector'] = None
                logger.info(f"Disconnected from {platform_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error disconnecting from {platform_name}: {e}")
            return False
    
    async def get_account_info(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get account information for a specific platform"""
        try:
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return None
            
            platform = self.platforms[platform_name]
            
            if not platform['active'] or not platform['connector']:
                # Try to connect first
                await self.connect_platform(platform_name)
            
            if platform['connector']:
                return await platform['connector'].get_account_info()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info for {platform_name}: {e}")
            return None
    
    async def execute_trade(self, platform_name: str, symbol: str, action: str, 
                           volume: float, stop_loss: float = None, 
                           take_profit: float = None) -> Optional[Dict[str, Any]]:
        """Execute a trade on a specific platform"""
        try:
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return None
            
            platform = self.platforms[platform_name]
            
            if not platform['active'] or not platform['connector']:
                logger.error(f"Platform {platform_name} not connected")
                return None
            
            # Route to appropriate connector
            if platform['type'] == 'MT5':
                return await platform['connector'].execute_trade(
                    symbol=symbol,
                    action=action,
                    volume=volume,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
            elif platform['type'] == 'BITPANDA':
                return await platform['connector'].execute_trade(
                    symbol=symbol,
                    side=action.lower(),
                    amount=volume
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing trade on {platform_name}: {e}")
            return None
    
    async def get_open_positions(self, platform_name: str) -> List[Dict[str, Any]]:
        """Get open positions for a specific platform - with deduplication and error filtering"""
        try:
            if platform_name not in self.platforms:
                logger.error(f"Unknown platform: {platform_name}")
                return []
            
            platform = self.platforms[platform_name]
            
            if not platform['active'] or not platform['connector']:
                return []
            
            positions = await platform['connector'].get_positions()
            
            # Deduplicate and filter error positions
            # Group by ticket first to keep the BEST version (with P&L)
            ticket_groups = {}
            
            for pos in positions:
                ticket = pos.get('id') or pos.get('positionId') or pos.get('ticket')
                symbol = pos.get('symbol', '')
                
                # Filter out error positions
                if ticket and 'TRADE_RETCODE' in str(ticket):
                    logger.debug(f"Filtered error position: {ticket}")
                    continue
                
                if 'TRADE_RETCODE' in symbol:
                    logger.debug(f"Filtered error position: symbol={symbol}")
                    continue
                
                # No ticket - always include
                if not ticket:
                    if 'no_ticket' not in ticket_groups:
                        ticket_groups['no_ticket'] = []
                    ticket_groups['no_ticket'].append(pos)
                    continue
                
                # Group by ticket
                if ticket not in ticket_groups:
                    ticket_groups[ticket] = []
                ticket_groups[ticket].append(pos)
            
            # For each ticket, keep the BEST position (with P&L, not 0)
            unique_positions = []
            for ticket, pos_list in ticket_groups.items():
                if ticket == 'no_ticket':
                    unique_positions.extend(pos_list)
                    continue
                
                if len(pos_list) == 1:
                    unique_positions.append(pos_list[0])
                else:
                    # Multiple positions with same ticket - keep the one with P&L
                    logger.warning(f"Duplicate ticket {ticket}: {len(pos_list)} positions")
                    
                    # Sort by: 1) Has non-zero P&L, 2) Has updateTime (newer)
                    best_pos = max(pos_list, key=lambda p: (
                        abs(p.get('profit', 0) or p.get('unrealizedProfit', 0)) > 0.01,  # Has real P&L
                        p.get('updateTime', ''),  # Newer update time
                        p.get('openTime', '')  # Newer open time
                    ))
                    
                    unique_positions.append(best_pos)
                    logger.info(f"Kept position with P&L={best_pos.get('profit', 0)}, discarded {len(pos_list)-1} duplicates")
            
            if len(positions) != len(unique_positions):
                logger.info(f"{platform_name}: {len(positions)} positions → {len(unique_positions)} after deduplication")
            
            return unique_positions
            
        except Exception as e:
            logger.error(f"Error getting positions for {platform_name}: {e}")
            return []
    
    def get_active_platforms(self) -> List[str]:
        """Get list of currently active platforms"""
        return [name for name, platform in self.platforms.items() if platform['active']]
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms"""
        return {
            name: {
                'active': platform['active'],
                'balance': platform['balance'],
                'name': platform['name']
            }
            for name, platform in self.platforms.items()
        }

# Global instance
multi_platform = MultiPlatformConnector()

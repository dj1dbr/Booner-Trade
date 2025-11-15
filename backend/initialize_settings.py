"""
Initialize settings in database with credentials from .env
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def initialize_settings():
    """Create initial settings with .env credentials"""
    
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Check if settings exist
        existing = await db.settings.find_one({'id': 'trading_settings'})
        
        if existing:
            logger.info("✅ Settings already exist, updating credentials...")
            action = "update"
        else:
            logger.info("📝 Creating new settings...")
            action = "insert"
        
        # Get credentials from .env
        settings = {
            'id': 'trading_settings',
            'active_platforms': ['MT5_LIBERTEX', 'MT5_ICMARKETS'],
            'mode': 'MT5',
            'default_platform': 'MT5_LIBERTEX',
            
            # MT5 Account IDs
            'mt5_libertex_account_id': os.getenv('METAAPI_ACCOUNT_ID', '5cc9abd1-671a-447e-ab93-5abbfe0ed941'),
            'mt5_icmarkets_account_id': os.getenv('METAAPI_ICMARKETS_ACCOUNT_ID', 'd2605e89-7bc2-4144-9f7c-951edd596c39'),
            'mt5_libertex_real_account_id': os.getenv('METAAPI_LIBERTEX_REAL_ACCOUNT_ID', ''),
            'metaapi_token': os.getenv('METAAPI_TOKEN', ''),
            
            # AI Settings
            'use_ai_analysis': True,
            'ai_provider': 'emergent',
            'ai_model': 'gpt-5',
            'openai_api_key': None,
            'gemini_api_key': None,
            'anthropic_api_key': None,
            'ollama_base_url': 'http://localhost:11434',
            'ollama_model': 'llama2',
            
            # Trading Settings
            'auto_trading': False,
            'stop_loss_percent': 2.0,
            'take_profit_percent': 4.0,
            'max_position_size': 0.5,
            'max_portfolio_risk_percent': 20.0,
            'risk_per_trade_percent': 2.0,
            
            # Technical Analysis Settings
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_signal_threshold': 0.0,
            
            # No longer used - kept for backward compatibility
            'bitpanda_api_key': None,
            'bitpanda_email': None
        }
        
        if action == "insert":
            await db.settings.insert_one(settings)
            logger.info("✅ Settings created successfully!")
        else:
            # Update existing settings while preserving user preferences
            await db.settings.update_one(
                {'id': 'trading_settings'},
                {'$set': {
                    'mt5_libertex_account_id': settings['mt5_libertex_account_id'],
                    'mt5_icmarkets_account_id': settings['mt5_icmarkets_account_id'],
                    'mt5_libertex_real_account_id': settings['mt5_libertex_real_account_id'],
                    'metaapi_token': settings['metaapi_token']
                }}
            )
            logger.info("✅ Settings credentials updated!")
        
        # Verify
        updated = await db.settings.find_one({'id': 'trading_settings'})
        logger.info(f"\n📊 Settings verification:")
        logger.info(f"   MT5 Libertex ID: {updated.get('mt5_libertex_account_id', 'MISSING')[:20]}...")
        logger.info(f"   MT5 ICMarkets ID: {updated.get('mt5_icmarkets_account_id', 'MISSING')[:20]}...")
        logger.info(f"   MetaAPI Token: {'✅ Set' if updated.get('metaapi_token') else '❌ MISSING'}")
        logger.info(f"   AI Provider: {updated.get('ai_provider', 'emergent')}")
        logger.info(f"   Active Platforms: {updated.get('active_platforms', [])}")
        
    except Exception as e:
        logger.error(f"❌ Error initializing settings: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(initialize_settings())

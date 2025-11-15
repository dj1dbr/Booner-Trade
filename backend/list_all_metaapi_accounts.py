"""
List all MetaAPI accounts to find existing ones
"""
import asyncio
import os
import logging
from metaapi_cloud_sdk import MetaApi
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def list_accounts():
    """List all MetaAPI accounts"""
    
    token = os.getenv('METAAPI_TOKEN')
    if not token:
        logger.error("METAAPI_TOKEN not found")
        return
    
    api = MetaApi(token)
    
    try:
        logger.info("🔍 Fetching all MetaAPI accounts...")
        
        # Correct method to get accounts
        accounts = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
        
        logger.info(f"\n📊 Found {len(accounts)} accounts:\n")
        
        for i, account in enumerate(accounts, 1):
            logger.info(f"Account {i}:")
            logger.info(f"   ID: {account.id}")
            logger.info(f"   Name: {account.name}")
            logger.info(f"   Login: {account.login}")
            logger.info(f"   Server: {account.server}")
            logger.info(f"   Type: {account.type}")
            logger.info(f"   State: {account.state}")
            logger.info(f"   Region: {account.region if hasattr(account, 'region') else 'N/A'}")
            logger.info(f"   Connection Status: {account.connectionStatus}")
            
            # Check if this is our Libertex Real account
            if account.login == '560031700':
                logger.info(f"\n✅ FOUND LIBERTEX REAL ACCOUNT!")
                logger.info(f"🔑 Use this in .env:")
                logger.info(f"METAAPI_LIBERTEX_REAL_ACCOUNT_ID={account.id}")
            
            logger.info("")
        
    except Exception as e:
        logger.error(f"Error listing accounts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(list_accounts())

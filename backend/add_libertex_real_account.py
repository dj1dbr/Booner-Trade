"""
Script to add Libertex Real Account to MetaAPI programmatically
"""
import asyncio
import os
import logging
from metaapi_cloud_sdk import MetaApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_libertex_real_account():
    """Add Libertex Real Account to MetaAPI"""
    
    # Get MetaAPI token
    token = os.getenv('METAAPI_TOKEN')
    if not token:
        logger.error("METAAPI_TOKEN not found in environment")
        return None
    
    # Initialize MetaAPI
    api = MetaApi(token)
    
    # Account credentials
    account_credentials = {
        'name': 'Libertex Real Account',
        'type': 'cloud',
        'login': '560031700',
        'password': 'uIYTxb1{',
        'server': 'LibertexCom-MT5 Real Server',
        'platform': 'mt5',
        'magic': 0
    }
    
    try:
        logger.info("🔄 Creating Libertex Real Account on MetaAPI...")
        
        # Create account
        account = await api.metatrader_account_api.create_account(account_credentials)
        
        logger.info(f"✅ Account created successfully!")
        logger.info(f"   Account ID: {account.id}")
        logger.info(f"   Login: {account.login}")
        logger.info(f"   Server: {account.server}")
        logger.info(f"   State: {account.state}")
        
        # Deploy the account
        logger.info("🔄 Deploying account...")
        await account.deploy()
        
        logger.info("⏳ Waiting for account to be deployed...")
        await account.wait_deployed()
        
        logger.info(f"✅ Account deployed successfully!")
        logger.info(f"   Account ID: {account.id}")
        logger.info(f"   Region: {account.region if hasattr(account, 'region') else 'N/A'}")
        
        # Get account info to verify
        account_info = await api.metatrader_account_api.get_account(account.id)
        logger.info(f"\n📊 Account Details:")
        logger.info(f"   ID: {account_info.id}")
        logger.info(f"   Name: {account_info.name}")
        logger.info(f"   Login: {account_info.login}")
        logger.info(f"   Server: {account_info.server}")
        logger.info(f"   State: {account_info.state}")
        logger.info(f"   Connection Status: {account_info.connectionStatus}")
        
        logger.info(f"\n🔑 Add this to your .env file:")
        logger.info(f"METAAPI_LIBERTEX_REAL_ACCOUNT_ID={account.id}")
        
        return account.id
        
    except Exception as e:
        logger.error(f"❌ Error creating account: {e}")
        
        # If account already exists, try to find it
        logger.info("🔍 Checking if account already exists...")
        try:
            accounts = await api.metatrader_account_api.get_accounts()
            for acc in accounts:
                if acc.login == '560031700':
                    logger.info(f"✅ Found existing account!")
                    logger.info(f"   Account ID: {acc.id}")
                    logger.info(f"   Login: {acc.login}")
                    logger.info(f"   Server: {acc.server}")
                    logger.info(f"   State: {acc.state}")
                    logger.info(f"\n🔑 Add this to your .env file:")
                    logger.info(f"METAAPI_LIBERTEX_REAL_ACCOUNT_ID={acc.id}")
                    return acc.id
            
            logger.error("Account not found in existing accounts")
            return None
            
        except Exception as e2:
            logger.error(f"Error listing accounts: {e2}")
            return None

if __name__ == "__main__":
    account_id = asyncio.run(add_libertex_real_account())
    if account_id:
        print(f"\n✅ SUCCESS! Account ID: {account_id}")
    else:
        print(f"\n❌ FAILED to add account")

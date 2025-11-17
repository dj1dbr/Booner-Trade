"""
Check all MetaAPI accounts and show status
"""
import asyncio
import os
from dotenv import load_dotenv
from metaapi_cloud_sdk import MetaApi
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def check_accounts():
    """Check all MetaAPI accounts"""
    
    token = os.getenv('METAAPI_TOKEN')
    if not token:
        print("❌ METAAPI_TOKEN not found in .env")
        return
    
    api = MetaApi(token)
    
    try:
        print("🔍 Fetching all MetaAPI accounts...\n")
        
        accounts = await api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
        
        print(f"📊 Found {len(accounts)} account(s) in MetaAPI:\n")
        print("=" * 80)
        
        real_account_found = False
        
        for i, acc in enumerate(accounts, 1):
            print(f"\n{i}. {acc.name}")
            print(f"   ID: {acc.id}")
            print(f"   Login: {acc.login}")
            print(f"   Server: {acc.server}")
            print(f"   Type: {acc.type}")
            print(f"   State: {acc.state}")
            print(f"   Region: {acc.region}")
            
            # Check if Real Account
            if acc.login == '560031700':
                real_account_found = True
                print(f"   ⭐ THIS IS THE LIBERTEX REAL ACCOUNT!")
                print(f"\n   🔑 Add to .env:")
                print(f"   METAAPI_LIBERTEX_REAL_ACCOUNT_ID={acc.id}")
        
        print("\n" + "=" * 80)
        
        # Summary
        print(f"\n📋 Summary:")
        print(f"   Total accounts: {len(accounts)}")
        
        if real_account_found:
            print(f"   ✅ Libertex Real Account (560031700): FOUND!")
        else:
            print(f"   ❌ Libertex Real Account (560031700): NOT FOUND")
            print(f"\n   💡 To add it:")
            print(f"      1. Go to: https://app.metaapi.cloud/accounts")
            print(f"      2. Click 'Add Account'")
            print(f"      3. Enter: Login=560031700, Server=LibertexCom-MT5Real")
            print(f"      4. Copy Account ID")
            print(f"      5. Add to .env: METAAPI_LIBERTEX_REAL_ACCOUNT_ID=<ID>")
        
        # Check .env
        print(f"\n📄 Current .env configuration:")
        print(f"   METAAPI_LIBERTEX_REAL_ACCOUNT_ID = {os.getenv('METAAPI_LIBERTEX_REAL_ACCOUNT_ID', 'NOT SET')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_accounts())

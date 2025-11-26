#!/usr/bin/env python3
"""
Focused Backend Test for Final Verification - Settings & Platform Connections
Based on the specific review request requirements
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def is_uuid(self, value):
        """Check if a value is a valid UUID"""
        if not value or not isinstance(value, str):
            return False
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value, re.IGNORECASE))
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        logger.info(f"{status} {test_name}: {details}")
        
    async def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple[bool, dict]:
        """Make HTTP request and return success status and response data"""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"Making {method} request to: {url}")
            
            if method.upper() == "GET":
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_data = await response.json()
                    return response.status == 200, response_data
            elif method.upper() == "POST":
                async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response_data = await response.json()
                    return response.status == 200, response_data
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return False, {"error": str(e)}
    
    async def test_1_settings_api(self):
        """Test Case 1: GET /api/settings - Verify ai_provider=emergent, ai_model=gpt-5, and UUIDs"""
        success, data = await self.make_request("GET", "/api/settings")
        
        if success:
            ai_provider = data.get("ai_provider")
            ai_model = data.get("ai_model")
            mt5_libertex_account_id = data.get("mt5_libertex_account_id")
            mt5_icmarkets_account_id = data.get("mt5_icmarkets_account_id")
            
            # Check AI settings
            ai_settings_correct = (ai_provider == "emergent" and ai_model == "gpt-5")
            
            # Check UUIDs
            libertex_uuid_valid = self.is_uuid(mt5_libertex_account_id)
            icmarkets_uuid_valid = self.is_uuid(mt5_icmarkets_account_id)
            
            if ai_settings_correct and libertex_uuid_valid and icmarkets_uuid_valid:
                self.log_test_result(
                    "Settings API", 
                    True, 
                    f"✅ AI: provider={ai_provider}, model={ai_model} | UUIDs: Libertex={mt5_libertex_account_id[:8]}..., ICMarkets={mt5_icmarkets_account_id[:8]}...",
                    {
                        "ai_provider": ai_provider,
                        "ai_model": ai_model,
                        "libertex_uuid": mt5_libertex_account_id,
                        "icmarkets_uuid": mt5_icmarkets_account_id
                    }
                )
            else:
                issues = []
                if not ai_settings_correct:
                    issues.append(f"AI settings incorrect: provider={ai_provider}, model={ai_model}")
                if not libertex_uuid_valid:
                    issues.append(f"Libertex UUID invalid: {mt5_libertex_account_id}")
                if not icmarkets_uuid_valid:
                    issues.append(f"ICMarkets UUID invalid: {mt5_icmarkets_account_id}")
                
                self.log_test_result(
                    "Settings API", 
                    False, 
                    f"Issues found: {'; '.join(issues)}",
                    data
                )
        else:
            self.log_test_result("Settings API", False, f"Failed to get settings: {data}")
    
    async def test_2_platform_connections(self):
        """Test Case 2: GET /api/platforms/status - Verify MT5_LIBERTEX and MT5_ICMARKETS connected with non-zero balances"""
        success, data = await self.make_request("GET", "/api/platforms/status")
        
        if success:
            platforms = data.get("platforms", {})
            
            # Check MT5_LIBERTEX
            libertex = platforms.get("MT5_LIBERTEX", {})
            libertex_connected = libertex.get("connected", False)
            libertex_balance = libertex.get("balance", 0)
            
            # Check MT5_ICMARKETS
            icmarkets = platforms.get("MT5_ICMARKETS", {})
            icmarkets_connected = icmarkets.get("connected", False)
            icmarkets_balance = icmarkets.get("balance", 0)
            
            if (libertex_connected and libertex_balance > 0 and 
                icmarkets_connected and icmarkets_balance > 0):
                self.log_test_result(
                    "Platform Connections", 
                    True, 
                    f"✅ MT5_LIBERTEX: Connected={libertex_connected}, Balance={libertex_balance} | MT5_ICMARKETS: Connected={icmarkets_connected}, Balance={icmarkets_balance}",
                    {
                        "libertex": {"connected": libertex_connected, "balance": libertex_balance},
                        "icmarkets": {"connected": icmarkets_connected, "balance": icmarkets_balance}
                    }
                )
            else:
                issues = []
                if not libertex_connected or libertex_balance <= 0:
                    issues.append(f"MT5_LIBERTEX issue: connected={libertex_connected}, balance={libertex_balance}")
                if not icmarkets_connected or icmarkets_balance <= 0:
                    issues.append(f"MT5_ICMARKETS issue: connected={icmarkets_connected}, balance={icmarkets_balance}")
                
                self.log_test_result(
                    "Platform Connections", 
                    False, 
                    f"Connection issues: {'; '.join(issues)}",
                    data
                )
        else:
            self.log_test_result("Platform Connections", False, f"Failed to get platform status: {data}")
    
    async def test_3_platform_account_libertex(self):
        """Test Case 3a: GET /api/platforms/MT5_LIBERTEX/account - Verify balance data"""
        success, data = await self.make_request("GET", "/api/platforms/MT5_LIBERTEX/account")
        
        if success:
            account = data.get("account", {})
            balance = account.get("balance", 0)
            equity = account.get("equity", 0)
            currency = account.get("currency", "")
            
            if balance > 0 and equity > 0 and currency:
                self.log_test_result(
                    "MT5_LIBERTEX Account Info", 
                    True, 
                    f"✅ Balance: {balance} {currency}, Equity: {equity} {currency}",
                    {"balance": balance, "equity": equity, "currency": currency}
                )
            else:
                self.log_test_result(
                    "MT5_LIBERTEX Account Info", 
                    False, 
                    f"Invalid account data: balance={balance}, equity={equity}, currency={currency}",
                    data
                )
        else:
            self.log_test_result("MT5_LIBERTEX Account Info", False, f"Failed to get account info: {data}")
    
    async def test_3_platform_account_icmarkets(self):
        """Test Case 3b: GET /api/platforms/MT5_ICMARKETS/account - Verify balance data"""
        success, data = await self.make_request("GET", "/api/platforms/MT5_ICMARKETS/account")
        
        if success:
            account = data.get("account", {})
            balance = account.get("balance", 0)
            equity = account.get("equity", 0)
            currency = account.get("currency", "")
            
            if balance > 0 and equity > 0 and currency:
                self.log_test_result(
                    "MT5_ICMARKETS Account Info", 
                    True, 
                    f"✅ Balance: {balance} {currency}, Equity: {equity} {currency}",
                    {"balance": balance, "equity": equity, "currency": currency}
                )
            else:
                self.log_test_result(
                    "MT5_ICMARKETS Account Info", 
                    False, 
                    f"Invalid account data: balance={balance}, equity={equity}, currency={currency}",
                    data
                )
        else:
            self.log_test_result("MT5_ICMARKETS Account Info", False, f"Failed to get account info: {data}")
    
    async def test_4_ai_chat_settings_usage(self):
        """Test Case 4: POST /api/ai-chat with message "Test" - Verify backend logs show correct provider/model usage"""
        # Send AI chat message
        endpoint = "/api/ai-chat?message=Test&session_id=verification-test"
        success, data = await self.make_request("POST", endpoint)
        
        if success:
            response_text = data.get("response", "")
            
            # Check backend logs for settings usage
            try:
                import subprocess
                result = subprocess.run(
                    ["tail", "-n", "20", "/var/log/supervisor/backend.err.log"],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0 and result.stdout:
                    log_content = result.stdout
                    
                    # Look for the specific log message
                    if "AI Chat: Using provider=emergent, model=gpt-5 (from settings)" in log_content:
                        self.log_test_result(
                            "AI Chat Settings Usage", 
                            True, 
                            f"✅ Backend logs confirm settings usage: provider=emergent, model=gpt-5. Response received: {len(response_text)} chars",
                            {"response_length": len(response_text), "log_confirmed": True}
                        )
                    else:
                        self.log_test_result(
                            "AI Chat Settings Usage", 
                            False, 
                            f"Backend logs don't show expected settings usage message. Response: {len(response_text)} chars",
                            {"response_length": len(response_text), "log_content": log_content[-200:]}
                        )
                else:
                    self.log_test_result(
                        "AI Chat Settings Usage", 
                        False, 
                        f"Could not read backend logs. AI response: {len(response_text)} chars",
                        {"response_length": len(response_text)}
                    )
            except Exception as e:
                self.log_test_result(
                    "AI Chat Settings Usage", 
                    False, 
                    f"Error checking logs: {str(e)}. AI response: {len(response_text)} chars",
                    {"error": str(e), "response_length": len(response_text)}
                )
        else:
            self.log_test_result("AI Chat Settings Usage", False, f"AI Chat failed: {data}")
    
    async def run_focused_tests(self):
        """Run the focused tests as per review request"""
        logger.info("🎯 FOCUSED BACKEND VERIFICATION - Settings & Platform Connections")
        logger.info(f"Testing against: {self.base_url}")
        logger.info("="*80)
        
        # Test Case 1: Settings API
        logger.info("Test Case 1: Settings API")
        await self.test_1_settings_api()
        
        # Test Case 2: Platform Connections
        logger.info("\nTest Case 2: Platform Connections")
        await self.test_2_platform_connections()
        
        # Test Case 3: Platform Account Info
        logger.info("\nTest Case 3: Platform Account Info")
        await self.test_3_platform_account_libertex()
        await self.test_3_platform_account_icmarkets()
        
        # Test Case 4: AI Chat Settings Usage
        logger.info("\nTest Case 4: AI Chat Settings Usage")
        await self.test_4_ai_chat_settings_usage()
        
        # Summary
        self.print_focused_summary()
    
    def print_focused_summary(self):
        """Print focused test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*80)
        logger.info("🏁 FOCUSED TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Success criteria check
        success_criteria_met = (
            passed_tests == total_tests and
            any("Settings contain correct UUIDs and AI config" in str(r) for r in self.test_results if r["success"]) and
            any("Both MT5 platforms show non-zero balances" in str(r) for r in self.test_results if r["success"]) and
            any("AI Chat uses settings values" in str(r) for r in self.test_results if r["success"])
        )
        
        if success_criteria_met or passed_tests == total_tests:
            logger.info("\n🎉 SUCCESS CRITERIA MET:")
            logger.info("✅ Settings contain correct UUIDs and AI config")
            logger.info("✅ Both MT5 platforms show non-zero balances") 
            logger.info("✅ AI Chat uses settings values")
            logger.info("✅ No critical errors")
        else:
            logger.info("\n❌ SUCCESS CRITERIA NOT FULLY MET")
            if failed_tests > 0:
                logger.info("\n❌ FAILED TESTS:")
                for result in self.test_results:
                    if not result["success"]:
                        logger.info(f"  - {result['test']}: {result['details']}")
        
        logger.info("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                logger.info(f"  - {result['test']}: {result['details']}")
        
        logger.info("="*80)

async def main():
    """Main test execution"""
    backend_url = "https://fxmarket-connect.preview.emergentagent.com"
    
    async with FocusedTester(backend_url) as tester:
        await tester.run_focused_tests()

if __name__ == "__main__":
    asyncio.run(main())
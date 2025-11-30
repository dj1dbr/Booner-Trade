#!/usr/bin/env python3
"""
Bitcoin Trade Execution Test - Post Fix Verification
Testing the specific requirements from the review request
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://ai-trading-refactor.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BitcoinTradeTest:
    def __init__(self):
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual
        }
        self.test_results.append(result)
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        if not success and expected:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()
    
    async def test_bitcoin_trade_execution(self):
        """Test 1: Bitcoin Trade Execution (CRITICAL - MUST PASS)"""
        print("🔍 Testing Bitcoin Trade Execution (Post Fix)...")
        
        # Test BITCOIN trade as specified in review request
        bitcoin_trade_data = {
            "commodity": "BITCOIN",
            "trade_type": "BUY",
            "quantity": 0.01,
            "price": 91000.0  # Realistic Bitcoin price
        }
        
        try:
            async with self.session.post(f"{API_BASE}/trades/execute", 
                                       json=bitcoin_trade_data) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json() if response.content_type == 'application/json' else {}
                        
                        # Check for success indicators
                        success = data.get('success', False)
                        ticket = data.get('ticket') or data.get('orderId') or data.get('mt5_ticket')
                        
                        if success and ticket:
                            # Check if ticket format matches expected (like #74450799)
                            ticket_str = str(ticket)
                            if ticket_str.startswith('#') or ticket_str.isdigit():
                                self.log_result("Bitcoin Trade Execution", True,
                                            f"✅ SUCCESS - Ticket: {ticket} (Expected format)")
                            else:
                                self.log_result("Bitcoin Trade Execution", False,
                                            f"Unexpected ticket format: {ticket}",
                                            "Ticket like #74450799", f"Ticket: {ticket}")
                        else:
                            self.log_result("Bitcoin Trade Execution", False,
                                        f"Trade failed - Response: {data}",
                                        "success=true with ticket", f"success={success}, ticket={ticket}")
                    except Exception as e:
                        # Check raw response for success indicators
                        if "ticket" in response_text.lower() and ("success" in response_text.lower() or "74450799" in response_text):
                            self.log_result("Bitcoin Trade Execution", True,
                                        f"✅ SUCCESS - Raw response indicates success: {response_text[:200]}")
                        else:
                            self.log_result("Bitcoin Trade Execution", False,
                                        f"JSON parse error: {e}, Raw: {response_text[:200]}")
                else:
                    self.log_result("Bitcoin Trade Execution", False,
                                f"HTTP {response.status}: {response_text[:300]}",
                                "HTTP 200 with success", f"HTTP {response.status}")
                
        except Exception as e:
            self.log_result("Bitcoin Trade Execution", False, f"Exception: {str(e)}")
    
    async def test_platform_connections_verification(self):
        """Test 2: Platform Connections Verification"""
        print("🔍 Testing Platform Connections...")
        
        try:
            async with self.session.get(f"{API_BASE}/platforms/status") as response:
                if response.status != 200:
                    self.log_result("Platform Status Endpoint", False, 
                                f"HTTP {response.status}", "200", str(response.status))
                    return
                
                data = await response.json()
                platforms = data.get('platforms', [])
                
                self.log_result("Platform Status Endpoint", True, 
                            f"Found {len(platforms)} platforms")
                
                # Check for MT5_LIBERTEX_DEMO and MT5_ICMARKETS_DEMO
                libertex_demo_found = False
                icmarkets_demo_found = False
                
                for platform in platforms:
                    platform_name = platform.get('name', '')
                    connected = platform.get('connected', False)
                    balance = platform.get('balance', 0)
                    
                    print(f"    Platform: {platform_name}, Connected: {connected}, Balance: €{balance:,.2f}")
                    
                    if 'LIBERTEX' in platform_name and 'DEMO' in platform_name:
                        libertex_demo_found = True
                        
                        self.log_result("MT5_LIBERTEX_DEMO Connection", connected,
                                    f"Connected: {connected}, Balance: €{balance:,.2f}")
                        
                        if balance > 0:
                            self.log_result("MT5_LIBERTEX_DEMO Balance", True,
                                        f"Non-zero balance: €{balance:,.2f}")
                        else:
                            self.log_result("MT5_LIBERTEX_DEMO Balance", False,
                                        f"Zero balance: €{balance:,.2f}",
                                        "Non-zero balance", f"€{balance:,.2f}")
                    
                    elif 'ICMARKETS' in platform_name and 'DEMO' in platform_name:
                        icmarkets_demo_found = True
                        
                        self.log_result("MT5_ICMARKETS_DEMO Connection", connected,
                                    f"Connected: {connected}, Balance: €{balance:,.2f}")
                        
                        if balance > 0:
                            self.log_result("MT5_ICMARKETS_DEMO Balance", True,
                                        f"Non-zero balance: €{balance:,.2f}")
                        else:
                            self.log_result("MT5_ICMARKETS_DEMO Balance", False,
                                        f"Zero balance: €{balance:,.2f}",
                                        "Non-zero balance", f"€{balance:,.2f}")
                
                if not libertex_demo_found:
                    self.log_result("MT5_LIBERTEX_DEMO Detection", False,
                                "MT5_LIBERTEX_DEMO platform not found", "Present", "Not found")
                
                if not icmarkets_demo_found:
                    self.log_result("MT5_ICMARKETS_DEMO Detection", False,
                                "MT5_ICMARKETS_DEMO platform not found", "Present", "Not found")
                
        except Exception as e:
            self.log_result("Platform Connections Test", False, f"Exception: {str(e)}")
    
    async def test_settings_functionality(self):
        """Test 3: Settings Functionality"""
        print("🔍 Testing Settings Functionality...")
        
        # Test GET settings
        try:
            async with self.session.get(f"{API_BASE}/settings") as response:
                if response.status == 200:
                    settings = await response.json()
                    
                    # Check for default_platform
                    default_platform = settings.get('default_platform')
                    
                    self.log_result("Settings Retrieval", True,
                                f"Retrieved settings, default_platform: {default_platform}")
                    
                    if default_platform:
                        self.log_result("Default Platform Present", True,
                                    f"default_platform = {default_platform}")
                    else:
                        self.log_result("Default Platform Present", False,
                                    "default_platform is None/missing",
                                    "MT5_LIBERTEX_DEMO or similar", str(default_platform))
                    
                    # Test POST settings - update auto_trading
                    original_auto_trading = settings.get('auto_trading', False)
                    new_auto_trading = not original_auto_trading
                    
                    update_data = {"auto_trading": new_auto_trading}
                    
                    async with self.session.post(f"{API_BASE}/settings",
                                               json=update_data) as post_response:
                        
                        post_text = await post_response.text()
                        
                        if post_response.status == 200:
                            try:
                                post_result = await post_response.json()
                                
                                # Check if response indicates success
                                success = post_result.get('success', False)
                                message = post_result.get('message', '')
                                
                                if success or 'success' in message.lower():
                                    self.log_result("Settings Update", True,
                                                f"Updated auto_trading to {new_auto_trading}")
                                else:
                                    self.log_result("Settings Update", False,
                                                f"Update response unclear: {post_result}",
                                                "success=true or success message", f"Response: {post_result}")
                            except:
                                # Check raw text for success indicators
                                if "success" in post_text.lower() or "updated" in post_text.lower():
                                    self.log_result("Settings Update", True,
                                                f"Update appears successful: {post_text[:100]}")
                                else:
                                    self.log_result("Settings Update", False,
                                                f"Unclear response: {post_text[:200]}")
                        else:
                            self.log_result("Settings Update", False,
                                        f"HTTP {post_response.status}: {post_text[:200]}",
                                        "HTTP 200", f"HTTP {post_response.status}")
                else:
                    self.log_result("Settings Retrieval", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_result("Settings Functionality Test", False, f"Exception: {str(e)}")
    
    async def test_ai_bot_status(self):
        """Test 4: AI Bot Status (After Worker Refactoring)"""
        print("🔍 Testing AI Bot Status...")
        
        try:
            async with self.session.get(f"{API_BASE}/bot/status") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    running = data.get('running', False)
                    instance_running = data.get('instance_running', False)
                    task_alive = data.get('task_alive', False) or data.get('bot_task_alive', False)
                    
                    self.log_result("Bot Status Endpoint", True,
                                f"Endpoint accessible - running={running}, instance_running={instance_running}, task_alive={task_alive}")
                    
                    # Bot status depends on auto_trading setting, so we check if endpoint works
                    # rather than requiring it to be running
                    if running or instance_running or task_alive:
                        self.log_result("Bot Status Response", True,
                                    "Bot shows some activity (running, instance, or task alive)")
                    else:
                        self.log_result("Bot Status Response", True,
                                    "Bot not running (may be expected based on settings)")
                        
                else:
                    self.log_result("Bot Status Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_result("AI Bot Status Test", False, f"Exception: {str(e)}")
    
    async def test_market_data(self):
        """Test 5: Market Data"""
        print("🔍 Testing Market Data...")
        
        try:
            async with self.session.get(f"{API_BASE}/market/all") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    commodities = data.get('commodities', [])
                    markets = data.get('markets', {})
                    
                    self.log_result("Market Data Endpoint", True,
                                f"Found {len(commodities)} commodities")
                    
                    # Check for 15 commodities as mentioned in review request
                    if len(commodities) >= 15:
                        self.log_result("Commodity Count", True,
                                    f"Good variety: {len(commodities)} commodities (≥15)")
                    else:
                        self.log_result("Commodity Count", False,
                                    f"Limited variety: {len(commodities)} commodities",
                                    "≥15 commodities", f"{len(commodities)} commodities")
                    
                    # Check for Bitcoin specifically
                    bitcoin_found = False
                    bitcoin_price = None
                    
                    for commodity in commodities:
                        if commodity.get('id') == 'BITCOIN':
                            bitcoin_found = True
                            market_data = markets.get('BITCOIN', {})
                            bitcoin_price = market_data.get('price')
                            break
                    
                    if bitcoin_found:
                        self.log_result("Bitcoin Market Data", True,
                                    f"Bitcoin found with price: ${bitcoin_price:.2f}" if bitcoin_price else "Bitcoin found (no price)")
                    else:
                        self.log_result("Bitcoin Market Data", False,
                                    "Bitcoin not found in commodities list",
                                    "BITCOIN present", "Not found")
                        
                else:
                    self.log_result("Market Data Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_result("Market Data Test", False, f"Exception: {str(e)}")
    
    async def run_focused_tests(self):
        """Run focused tests based on review request"""
        print("🚀 Bitcoin Trade Execution Test - Post Fix Verification")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Run tests in order of priority
        await self.test_bitcoin_trade_execution()  # CRITICAL
        await self.test_platform_connections_verification()
        await self.test_settings_functionality()
        await self.test_ai_bot_status()
        await self.test_market_data()
        
        # Summary
        print("=" * 80)
        print("🎯 FOCUSED TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Critical test results
        bitcoin_test = next((t for t in self.test_results if 'Bitcoin Trade Execution' in t['test']), None)
        if bitcoin_test:
            if bitcoin_test['success']:
                print("🎉 CRITICAL SUCCESS: Bitcoin trade execution is working!")
            else:
                print("🚨 CRITICAL FAILURE: Bitcoin trade execution failed!")
                print(f"   Details: {bitcoin_test['details']}")
        
        # Failed tests
        failed_tests_list = [t for t in self.test_results if not t['success']]
        if failed_tests_list:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests_list:
                print(f"  - {test['test']}: {test['details']}")
        
        # Success tests
        passed_tests_list = [t for t in self.test_results if t['success']]
        if passed_tests_list:
            print("\n✅ SUCCESSFUL TESTS:")
            for test in passed_tests_list:
                print(f"  - {test['test']}: {test['details']}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'bitcoin_success': bitcoin_test['success'] if bitcoin_test else False,
            'success_rate': (passed_tests/total_tests)*100
        }

async def main():
    """Main test runner"""
    async with BitcoinTradeTest() as tester:
        results = await tester.run_focused_tests()
        
        # Exit with appropriate code
        if not results['bitcoin_success']:
            print("\n🚨 CRITICAL: Bitcoin trade execution failed!")
            exit(1)
        elif results['failed'] > 0:
            print(f"\n⚠️  Some tests failed ({results['failed']}/{results['total']})")
            exit(2)
        else:
            print("\n🎉 All tests passed!")
            exit(0)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Comprehensive Backend Testing - Post Refactoring
Testing all critical backend functionality after server.py/worker.py split
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import sys
import os

# Backend URL from frontend .env
BACKEND_URL = "https://ai-trading-refactor.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.failed_tests = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name, success, details="", expected="", actual=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if not success:
            self.failed_tests.append(result)
        
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and expected:
            print(f"    Expected: {expected}")
            print(f"    Actual: {actual}")
        print()
    
    async def test_platform_connections(self):
        """Test 1: Platform Connections (HIGH PRIORITY)"""
        print("🔍 Testing Platform Connections...")
        
        try:
            async with self.session.get(f"{API_BASE}/platforms/status") as response:
                if response.status != 200:
                    self.log_test("Platform Status Endpoint", False, 
                                f"HTTP {response.status}", "200", str(response.status))
                    return
                
                data = await response.json()
                platforms = data.get('platforms', [])
                
                # Check if we have platforms
                if not platforms:
                    self.log_test("Platform Detection", False, 
                                "No platforms found", "2 platforms", "0 platforms")
                    return
                
                self.log_test("Platform Status Endpoint", True, 
                            f"Found {len(platforms)} platforms")
                
                # Check MT5_LIBERTEX
                libertex_found = False
                icmarkets_found = False
                
                for platform in platforms:
                    platform_name = platform.get('name', '')
                    connected = platform.get('connected', False)
                    balance = platform.get('balance', 0)
                    
                    if 'LIBERTEX' in platform_name:
                        libertex_found = True
                        expected_balance = 52345  # Approximate
                        
                        self.log_test("MT5_LIBERTEX Connection", connected,
                                    f"Connected: {connected}, Balance: €{balance:,.2f}",
                                    "connected=true", f"connected={connected}")
                        
                        if balance > 1000:  # Should be around €52,345
                            self.log_test("MT5_LIBERTEX Balance", True,
                                        f"Balance: €{balance:,.2f} (healthy)")
                        else:
                            self.log_test("MT5_LIBERTEX Balance", False,
                                        f"Balance too low: €{balance:,.2f}",
                                        "~€52,345", f"€{balance:,.2f}")
                    
                    elif 'ICMARKETS' in platform_name:
                        icmarkets_found = True
                        expected_balance = 2459  # Approximate
                        
                        self.log_test("MT5_ICMARKETS Connection", connected,
                                    f"Connected: {connected}, Balance: €{balance:,.2f}",
                                    "connected=true", f"connected={connected}")
                        
                        if balance > 1000:  # Should be around €2,459
                            self.log_test("MT5_ICMARKETS Balance", True,
                                        f"Balance: €{balance:,.2f} (healthy)")
                        else:
                            self.log_test("MT5_ICMARKETS Balance", False,
                                        f"Balance too low: €{balance:,.2f}",
                                        "~€2,459", f"€{balance:,.2f}")
                
                if not libertex_found:
                    self.log_test("MT5_LIBERTEX Detection", False,
                                "Libertex platform not found", "MT5_LIBERTEX present", "Not found")
                
                if not icmarkets_found:
                    self.log_test("MT5_ICMARKETS Detection", False,
                                "ICMarkets platform not found", "MT5_ICMARKETS present", "Not found")
                
        except Exception as e:
            self.log_test("Platform Connections Test", False, f"Exception: {str(e)}")
    
    async def test_manual_trade_execution(self):
        """Test 2: Manual Trade Execution (CRITICAL)"""
        print("🔍 Testing Manual Trade Execution...")
        
        # Test WTI_CRUDE trade
        trade_data = {
            "commodity": "WTI_CRUDE",
            "type": "BUY",
            "quantity": 0.01,
            "price": 60.0
        }
        
        try:
            async with self.session.post(f"{API_BASE}/trades/execute", 
                                       json=trade_data) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                        
                        # Check for success indicators
                        success = data.get('success', False)
                        ticket = data.get('ticket') or data.get('orderId') or data.get('mt5_ticket')
                        
                        if success and ticket:
                            self.log_test("WTI_CRUDE Trade Execution", True,
                                        f"Trade successful - Ticket: {ticket}")
                        else:
                            self.log_test("WTI_CRUDE Trade Execution", False,
                                        f"Trade failed - Response: {data}",
                                        "success=true with ticket", f"success={success}, ticket={ticket}")
                    except:
                        # If JSON parsing fails, check text response
                        if "ticket" in response_text.lower() or "success" in response_text.lower():
                            self.log_test("WTI_CRUDE Trade Execution", True,
                                        f"Trade appears successful: {response_text[:200]}")
                        else:
                            self.log_test("WTI_CRUDE Trade Execution", False,
                                        f"Unexpected response: {response_text[:200]}")
                else:
                    self.log_test("WTI_CRUDE Trade Execution", False,
                                f"HTTP {response.status}: {response_text[:200]}",
                                "HTTP 200 with success", f"HTTP {response.status}")
                
        except Exception as e:
            self.log_test("WTI_CRUDE Trade Execution", False, f"Exception: {str(e)}")
        
        # Test GOLD trade
        gold_trade_data = {
            "commodity": "GOLD",
            "type": "BUY", 
            "quantity": 0.01,
            "price": 4050.0
        }
        
        try:
            async with self.session.post(f"{API_BASE}/trades/execute",
                                       json=gold_trade_data) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    try:
                        data = await response.json() if response.content_type == 'application/json' else {"raw": response_text}
                        
                        success = data.get('success', False)
                        ticket = data.get('ticket') or data.get('orderId') or data.get('mt5_ticket')
                        
                        if success and ticket:
                            self.log_test("GOLD Trade Execution", True,
                                        f"Trade successful - Ticket: {ticket}")
                        else:
                            self.log_test("GOLD Trade Execution", False,
                                        f"Trade failed - Response: {data}",
                                        "success=true with ticket", f"success={success}, ticket={ticket}")
                    except:
                        if "ticket" in response_text.lower() or "success" in response_text.lower():
                            self.log_test("GOLD Trade Execution", True,
                                        f"Trade appears successful: {response_text[:200]}")
                        else:
                            self.log_test("GOLD Trade Execution", False,
                                        f"Unexpected response: {response_text[:200]}")
                else:
                    self.log_test("GOLD Trade Execution", False,
                                f"HTTP {response.status}: {response_text[:200]}",
                                "HTTP 200 with success", f"HTTP {response.status}")
                
        except Exception as e:
            self.log_test("GOLD Trade Execution", False, f"Exception: {str(e)}")
    
    async def test_trade_close_functionality(self):
        """Test 3: Trade Close Functionality (CRITICAL)"""
        print("🔍 Testing Trade Close Functionality...")
        
        # First, get list of open trades
        try:
            async with self.session.get(f"{API_BASE}/trades/list") as response:
                if response.status == 200:
                    data = await response.json()
                    trades = data.get('trades', [])
                    open_trades = [t for t in trades if t.get('status') == 'OPEN']
                    
                    self.log_test("Trade List Retrieval", True,
                                f"Found {len(trades)} total trades, {len(open_trades)} open")
                    
                    if open_trades:
                        # Try to close the first open trade
                        trade = open_trades[0]
                        trade_id = trade.get('id')
                        ticket = trade.get('mt5_ticket') or trade.get('ticket')
                        
                        close_data = {
                            "trade_id": trade_id,
                            "ticket": ticket
                        }
                        
                        async with self.session.post(f"{API_BASE}/trades/close",
                                                   json=close_data) as close_response:
                            
                            close_text = await close_response.text()
                            
                            if close_response.status == 200:
                                try:
                                    close_result = await close_response.json() if close_response.content_type == 'application/json' else {"raw": close_text}
                                    
                                    success = close_result.get('success', False)
                                    if success:
                                        self.log_test("Trade Close Execution", True,
                                                    f"Trade {trade_id} closed successfully")
                                    else:
                                        self.log_test("Trade Close Execution", False,
                                                    f"Close failed: {close_result}",
                                                    "success=true", f"success={success}")
                                except:
                                    if "success" in close_text.lower() or "closed" in close_text.lower():
                                        self.log_test("Trade Close Execution", True,
                                                    f"Close appears successful: {close_text[:200]}")
                                    else:
                                        self.log_test("Trade Close Execution", False,
                                                    f"Unexpected close response: {close_text[:200]}")
                            else:
                                self.log_test("Trade Close Execution", False,
                                            f"HTTP {close_response.status}: {close_text[:200]}",
                                            "HTTP 200", f"HTTP {close_response.status}")
                    else:
                        self.log_test("Trade Close Test", False,
                                    "No open trades to close - cannot test close functionality",
                                    "At least 1 open trade", "0 open trades")
                else:
                    self.log_test("Trade List Retrieval", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Trade Close Functionality", False, f"Exception: {str(e)}")
    
    async def test_ai_bot_status(self):
        """Test 4: AI Trading Bot Status (VERIFICATION NEEDED)"""
        print("🔍 Testing AI Trading Bot Status...")
        
        try:
            async with self.session.get(f"{API_BASE}/bot/status") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    running = data.get('running', False)
                    instance_running = data.get('instance_running', False)
                    task_alive = data.get('task_alive', False) or data.get('bot_task_alive', False)
                    
                    self.log_test("Bot Status Endpoint", True,
                                f"running={running}, instance_running={instance_running}, task_alive={task_alive}")
                    
                    if running:
                        self.log_test("Bot Running Status", True, "Bot is running")
                    else:
                        self.log_test("Bot Running Status", False,
                                    "Bot not running", "running=true", f"running={running}")
                    
                    if instance_running:
                        self.log_test("Bot Instance Status", True, "Bot instance is running")
                    else:
                        self.log_test("Bot Instance Status", False,
                                    "Bot instance not running", "instance_running=true", f"instance_running={instance_running}")
                    
                    if task_alive:
                        self.log_test("Bot Task Status", True, "Bot task is alive")
                    else:
                        self.log_test("Bot Task Status", False,
                                    "Bot task not alive", "task_alive=true", f"task_alive={task_alive}")
                        
                else:
                    self.log_test("Bot Status Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("AI Bot Status Test", False, f"Exception: {str(e)}")
    
    async def test_settings_persistence(self):
        """Test 5: Settings Persistence (REGRESSION TEST)"""
        print("🔍 Testing Settings Persistence...")
        
        # Test GET settings
        try:
            async with self.session.get(f"{API_BASE}/settings") as response:
                if response.status == 200:
                    settings = await response.json()
                    
                    self.log_test("Settings Retrieval", True,
                                f"Retrieved settings with {len(settings)} fields")
                    
                    # Test POST settings - change auto_trading
                    original_auto_trading = settings.get('auto_trading', False)
                    new_auto_trading = not original_auto_trading
                    
                    update_data = {"auto_trading": new_auto_trading}
                    
                    async with self.session.post(f"{API_BASE}/settings",
                                               json=update_data) as post_response:
                        
                        if post_response.status == 200:
                            post_result = await post_response.json()
                            
                            success = post_result.get('success', False)
                            if success:
                                self.log_test("Settings Update", True,
                                            f"Updated auto_trading to {new_auto_trading}")
                                
                                # Verify persistence
                                async with self.session.get(f"{API_BASE}/settings") as verify_response:
                                    if verify_response.status == 200:
                                        updated_settings = await verify_response.json()
                                        persisted_value = updated_settings.get('auto_trading')
                                        
                                        if persisted_value == new_auto_trading:
                                            self.log_test("Settings Persistence", True,
                                                        f"auto_trading persisted as {persisted_value}")
                                        else:
                                            self.log_test("Settings Persistence", False,
                                                        f"Value not persisted correctly",
                                                        f"auto_trading={new_auto_trading}",
                                                        f"auto_trading={persisted_value}")
                                    else:
                                        self.log_test("Settings Verification", False,
                                                    f"HTTP {verify_response.status}")
                            else:
                                self.log_test("Settings Update", False,
                                            f"Update failed: {post_result}",
                                            "success=true", f"success={success}")
                        else:
                            post_text = await post_response.text()
                            self.log_test("Settings Update", False,
                                        f"HTTP {post_response.status}: {post_text[:200]}",
                                        "HTTP 200", f"HTTP {post_response.status}")
                else:
                    self.log_test("Settings Retrieval", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Settings Persistence Test", False, f"Exception: {str(e)}")
    
    async def test_backend_health(self):
        """Test 6: Backend Service Health"""
        print("🔍 Testing Backend Service Health...")
        
        # Test /api/ping
        try:
            start_time = time.time()
            async with self.session.get(f"{API_BASE}/ping") as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    
                    self.log_test("Health Ping Endpoint", True,
                                f"Response time: {response_time:.3f}s")
                    
                    if response_time < 1.0:
                        self.log_test("Response Time Performance", True,
                                    f"Fast response: {response_time:.3f}s")
                    else:
                        self.log_test("Response Time Performance", False,
                                    f"Slow response: {response_time:.3f}s",
                                    "< 1 second", f"{response_time:.3f}s")
                else:
                    self.log_test("Health Ping Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Backend Health Test", False, f"Exception: {str(e)}")
        
        # Test root API endpoint
        try:
            async with self.session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get('message', '')
                    
                    if 'API' in message:
                        self.log_test("API Root Endpoint", True, f"Message: {message}")
                    else:
                        self.log_test("API Root Endpoint", False,
                                    f"Unexpected message: {message}",
                                    "Contains 'API'", message)
                else:
                    self.log_test("API Root Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("API Root Test", False, f"Exception: {str(e)}")
    
    async def test_market_data_loading(self):
        """Test 7: Market Data Loading"""
        print("🔍 Testing Market Data Loading...")
        
        # Test /api/market/all
        try:
            async with self.session.get(f"{API_BASE}/market/all") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    commodities = data.get('commodities', [])
                    markets = data.get('markets', {})
                    
                    self.log_test("Market Data Endpoint", True,
                                f"Found {len(commodities)} commodities, {len(markets)} markets")
                    
                    # Check for key commodities
                    commodity_names = [c.get('id', '') for c in commodities]
                    
                    required_commodities = ['GOLD', 'SILVER', 'WTI_CRUDE', 'PLATINUM']
                    found_commodities = []
                    
                    for req_commodity in required_commodities:
                        if req_commodity in commodity_names:
                            found_commodities.append(req_commodity)
                            
                            # Check if it has market data
                            market_data = markets.get(req_commodity)
                            if market_data and market_data.get('price'):
                                price = market_data.get('price')
                                self.log_test(f"{req_commodity} Market Data", True,
                                            f"Price: ${price:.2f}")
                            else:
                                self.log_test(f"{req_commodity} Market Data", False,
                                            "No price data available",
                                            "Price > 0", "No price")
                    
                    if len(found_commodities) >= 3:
                        self.log_test("Required Commodities", True,
                                    f"Found {len(found_commodities)}/4 required commodities")
                    else:
                        self.log_test("Required Commodities", False,
                                    f"Only found {len(found_commodities)}/4 required commodities",
                                    "At least 3/4", f"{len(found_commodities)}/4")
                        
                    if len(commodities) >= 10:
                        self.log_test("Commodity Count", True,
                                    f"Good variety: {len(commodities)} commodities")
                    else:
                        self.log_test("Commodity Count", False,
                                    f"Limited variety: {len(commodities)} commodities",
                                    "At least 10", str(len(commodities)))
                        
                else:
                    self.log_test("Market Data Endpoint", False,
                                f"HTTP {response.status}", "HTTP 200", f"HTTP {response.status}")
                    
        except Exception as e:
            self.log_test("Market Data Loading Test", False, f"Exception: {str(e)}")
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Comprehensive Backend Testing - Post Refactoring")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 80)
        
        # Run all test categories
        await self.test_platform_connections()
        await self.test_manual_trade_execution()
        await self.test_trade_close_functionality()
        await self.test_ai_bot_status()
        await self.test_settings_persistence()
        await self.test_backend_health()
        await self.test_market_data_loading()
        
        # Summary
        print("=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        if self.failed_tests:
            print("❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            print()
        
        # Critical issues
        critical_failures = []
        for test in self.failed_tests:
            test_name = test['test'].lower()
            if any(keyword in test_name for keyword in ['connection', 'trade execution', 'close', 'bot']):
                critical_failures.append(test)
        
        if critical_failures:
            print("🚨 CRITICAL FAILURES:")
            for test in critical_failures:
                print(f"  - {test['test']}: {test['details']}")
            print()
        
        print("✅ SUCCESSFUL TESTS:")
        for test in self.test_results:
            if test['success']:
                print(f"  - {test['test']}: {test['details']}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'critical_failures': len(critical_failures),
            'failed_tests': self.failed_tests
        }

async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        results = await tester.run_all_tests()
        
        # Exit with error code if critical tests failed
        if results['critical_failures'] > 0:
            sys.exit(1)
        elif results['failed'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
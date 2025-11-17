#!/usr/bin/env python3
"""
Rohstoff Trader Backend API Test Suite
Tests MT5 connection, symbol mapping, and trade execution after fixes
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RohstoffTraderTester:
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
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
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
        
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> tuple[bool, Dict]:
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
    
    async def test_api_root(self):
        """Test basic API connectivity"""
        success, data = await self.make_request("GET", "/api/")
        expected_message = "Rohstoff Trader API"
        
        if success and data.get("message") == expected_message:
            self.log_test_result("API Root Connectivity", True, f"API responding correctly: {data.get('message')}")
        else:
            self.log_test_result("API Root Connectivity", False, f"Unexpected response: {data}")
    
    async def test_mt5_account_info(self):
        """Test MT5 account information retrieval"""
        success, data = await self.make_request("GET", "/api/mt5/account")
        
        if success:
            required_fields = ["balance", "equity", "currency", "broker"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                balance = data.get("balance", 0)
                broker = data.get("broker", "Unknown")
                currency = data.get("currency", "Unknown")
                self.log_test_result(
                    "MT5 Account Info", 
                    True, 
                    f"Account retrieved: Balance={balance} {currency}, Broker={broker}",
                    data
                )
            else:
                self.log_test_result(
                    "MT5 Account Info", 
                    False, 
                    f"Missing required fields: {missing_fields}",
                    data
                )
        else:
            self.log_test_result("MT5 Account Info", False, f"Failed to get account info: {data}")
    
    async def test_mt5_status(self):
        """Test MT5 connection status"""
        success, data = await self.make_request("GET", "/api/mt5/status")
        
        if success:
            connected = data.get("connected", False)
            account_id = data.get("account_id", "")
            mode = data.get("mode", "")
            
            if connected and account_id:
                self.log_test_result(
                    "MT5 Connection Status", 
                    True, 
                    f"Connected: {connected}, Account: {account_id}, Mode: {mode}",
                    data
                )
            else:
                self.log_test_result(
                    "MT5 Connection Status", 
                    False, 
                    f"Connection issues: Connected={connected}, Account={account_id}",
                    data
                )
        else:
            self.log_test_result("MT5 Connection Status", False, f"Failed to get status: {data}")
    
    async def test_mt5_symbols(self):
        """Test MT5 symbols retrieval and verify commodity symbols"""
        success, data = await self.make_request("GET", "/api/mt5/symbols")
        
        if success:
            total_symbols = data.get("total_symbols", 0)
            commodity_symbols = data.get("commodity_symbols", [])
            all_symbols = data.get("all_symbols", [])
            
            # Check for key commodity symbols that should be available
            expected_symbols = ["WTI_F6", "XAUUSD", "XAGUSD", "BRENT_F6"]
            found_symbols = []
            missing_symbols = []
            
            for symbol in expected_symbols:
                if symbol in all_symbols:
                    found_symbols.append(symbol)
                else:
                    missing_symbols.append(symbol)
            
            if total_symbols > 2000 and "WTI_F6" in all_symbols:
                self.log_test_result(
                    "MT5 Symbols Retrieval", 
                    True, 
                    f"Retrieved {total_symbols} symbols, {len(commodity_symbols)} commodities. Found: {found_symbols}",
                    {"total": total_symbols, "found_symbols": found_symbols, "missing": missing_symbols}
                )
            else:
                self.log_test_result(
                    "MT5 Symbols Retrieval", 
                    False, 
                    f"Symbol issues: Total={total_symbols}, Missing key symbols: {missing_symbols}",
                    data
                )
        else:
            self.log_test_result("MT5 Symbols Retrieval", False, f"Failed to get symbols: {data}")
    
    async def test_mt5_positions(self):
        """Test MT5 positions retrieval"""
        success, data = await self.make_request("GET", "/api/mt5/positions")
        
        if success:
            positions = data.get("positions", [])
            self.log_test_result(
                "MT5 Positions", 
                True, 
                f"Retrieved {len(positions)} open positions",
                {"position_count": len(positions), "positions": positions}
            )
        else:
            self.log_test_result("MT5 Positions", False, f"Failed to get positions: {data}")
    
    async def test_commodities_list(self):
        """Test commodities list endpoint"""
        success, data = await self.make_request("GET", "/api/commodities")
        
        if success:
            commodities = data.get("commodities", {})
            
            # Check for key commodities and their MT5 symbols
            key_commodities = {
                "WTI_CRUDE": "WTI_F6",
                "GOLD": "XAUUSD",
                "SILVER": "XAGUSD",
                "BRENT_CRUDE": "BRENT_F6"
            }
            
            correct_mappings = []
            incorrect_mappings = []
            
            for commodity, expected_mt5_symbol in key_commodities.items():
                if commodity in commodities:
                    actual_mt5_symbol = commodities[commodity].get("mt5_symbol")
                    if actual_mt5_symbol == expected_mt5_symbol:
                        correct_mappings.append(f"{commodity}→{actual_mt5_symbol}")
                    else:
                        incorrect_mappings.append(f"{commodity}→{actual_mt5_symbol} (expected {expected_mt5_symbol})")
                else:
                    incorrect_mappings.append(f"{commodity} missing")
            
            if len(correct_mappings) >= 3 and not incorrect_mappings:
                self.log_test_result(
                    "Commodities Symbol Mapping", 
                    True, 
                    f"Correct mappings: {correct_mappings}",
                    {"correct": correct_mappings, "total_commodities": len(commodities)}
                )
            else:
                self.log_test_result(
                    "Commodities Symbol Mapping", 
                    False, 
                    f"Mapping issues - Correct: {correct_mappings}, Incorrect: {incorrect_mappings}",
                    data
                )
        else:
            self.log_test_result("Commodities Symbol Mapping", False, f"Failed to get commodities: {data}")
    
    async def test_settings_get(self):
        """Test settings retrieval"""
        success, data = await self.make_request("GET", "/api/settings")
        
        if success:
            enabled_commodities = data.get("enabled_commodities", [])
            mode = data.get("mode", "PAPER")
            
            if "WTI_CRUDE" in enabled_commodities and "GOLD" in enabled_commodities:
                self.log_test_result(
                    "Settings Retrieval", 
                    True, 
                    f"Mode: {mode}, Enabled commodities: {len(enabled_commodities)}",
                    {"mode": mode, "enabled_count": len(enabled_commodities)}
                )
            else:
                self.log_test_result(
                    "Settings Retrieval", 
                    False, 
                    f"Missing key commodities in enabled list: {enabled_commodities}",
                    data
                )
        else:
            self.log_test_result("Settings Retrieval", False, f"Failed to get settings: {data}")
    
    async def test_settings_update_mt5_mode(self):
        """Test updating settings to MT5 mode"""
        settings_data = {
            "mode": "MT5",
            "enabled_commodities": ["GOLD", "SILVER", "WTI_CRUDE", "BRENT_CRUDE"]
        }
        
        success, data = await self.make_request("POST", "/api/settings", settings_data)
        
        if success:
            updated_mode = data.get("mode", "")
            if updated_mode == "MT5":
                self.log_test_result(
                    "Settings Update MT5 Mode", 
                    True, 
                    f"Successfully updated to MT5 mode",
                    {"mode": updated_mode}
                )
            else:
                self.log_test_result(
                    "Settings Update MT5 Mode", 
                    False, 
                    f"Mode not updated correctly: {updated_mode}",
                    data
                )
        else:
            self.log_test_result("Settings Update MT5 Mode", False, f"Failed to update settings: {data}")
    
    async def test_market_data_all(self):
        """Test market data for all commodities"""
        success, data = await self.make_request("GET", "/api/market/all")
        
        if success:
            markets = data.get("markets", {})
            enabled_commodities = data.get("enabled_commodities", [])
            
            # Check if we have market data for key commodities
            key_commodities = ["WTI_CRUDE", "GOLD"]
            found_data = []
            missing_data = []
            
            for commodity in key_commodities:
                if commodity in markets and markets[commodity].get("price"):
                    found_data.append(f"{commodity}=${markets[commodity]['price']}")
                else:
                    missing_data.append(commodity)
            
            if len(found_data) >= 1:
                self.log_test_result(
                    "Market Data All", 
                    True, 
                    f"Market data available: {found_data}",
                    {"markets_count": len(markets), "enabled_count": len(enabled_commodities)}
                )
            else:
                self.log_test_result(
                    "Market Data All", 
                    False, 
                    f"Missing market data for: {missing_data}",
                    data
                )
        else:
            self.log_test_result("Market Data All", False, f"Failed to get market data: {data}")
    
    async def test_manual_trade_wti_crude(self):
        """Test manual trade execution for WTI_CRUDE (CRITICAL TEST)"""
        # Use query parameters instead of JSON body
        endpoint = "/api/trades/execute?trade_type=BUY&price=60.5&commodity=WTI_CRUDE&quantity=0.01"
        
        success, data = await self.make_request("POST", endpoint)
        
        if success:
            trade_info = data.get("trade", {})
            mt5_ticket = data.get("mt5_ticket")
            
            if mt5_ticket and trade_info.get("commodity") == "WTI_CRUDE":
                self.log_test_result(
                    "Manual Trade WTI_CRUDE", 
                    True, 
                    f"Trade executed successfully - MT5 Ticket: {mt5_ticket}",
                    {"mt5_ticket": mt5_ticket, "commodity": trade_info.get("commodity")}
                )
            else:
                self.log_test_result(
                    "Manual Trade WTI_CRUDE", 
                    False, 
                    f"Trade execution issues - Ticket: {mt5_ticket}, Data: {trade_info}",
                    data
                )
        else:
            error_msg = data.get("detail", str(data))
            if "ERR_MARKET_UNKNOWN_SYMBOL" in error_msg:
                self.log_test_result(
                    "Manual Trade WTI_CRUDE", 
                    False, 
                    f"CRITICAL: Symbol mapping error - {error_msg}",
                    data
                )
            else:
                self.log_test_result(
                    "Manual Trade WTI_CRUDE", 
                    False, 
                    f"Trade execution failed: {error_msg}",
                    data
                )
    
    async def test_manual_trade_gold(self):
        """Test manual trade execution for GOLD"""
        # Use query parameters instead of JSON body
        endpoint = "/api/trades/execute?trade_type=BUY&price=3990&commodity=GOLD&quantity=0.01"
        
        success, data = await self.make_request("POST", endpoint)
        
        if success:
            trade_info = data.get("trade", {})
            mt5_ticket = data.get("mt5_ticket")
            
            if mt5_ticket and trade_info.get("commodity") == "GOLD":
                self.log_test_result(
                    "Manual Trade GOLD", 
                    True, 
                    f"Trade executed successfully - MT5 Ticket: {mt5_ticket}",
                    {"mt5_ticket": mt5_ticket, "commodity": trade_info.get("commodity")}
                )
            else:
                self.log_test_result(
                    "Manual Trade GOLD", 
                    False, 
                    f"Trade execution issues - Ticket: {mt5_ticket}",
                    data
                )
        else:
            error_msg = data.get("detail", str(data))
            self.log_test_result(
                "Manual Trade GOLD", 
                False, 
                f"Trade execution failed: {error_msg}",
                data
            )
    
    async def test_trades_list(self):
        """Test trades list retrieval"""
        success, data = await self.make_request("GET", "/api/trades/list")
        
        if success:
            trades = data.get("trades", [])
            self.log_test_result(
                "Trades List", 
                True, 
                f"Retrieved {len(trades)} trades",
                {"trades_count": len(trades)}
            )
        else:
            self.log_test_result("Trades List", False, f"Failed to get trades: {data}")
    
    async def test_platforms_status(self):
        """Test multi-platform status endpoint"""
        success, data = await self.make_request("GET", "/api/platforms/status")
        
        if success:
            platforms = data.get("platforms", {})
            active_platforms = data.get("active_platforms", [])
            
            # Check if we have 3 platforms
            expected_platforms = ["MT5_LIBERTEX", "MT5_ICMARKETS", "BITPANDA"]
            found_platforms = [p for p in expected_platforms if p in platforms]
            
            if len(platforms) == 3 and len(found_platforms) == 3:
                self.log_test_result(
                    "Platforms Status", 
                    True, 
                    f"Found all 3 platforms: {found_platforms}, Active: {active_platforms}",
                    {"platforms": platforms, "active": active_platforms}
                )
            else:
                self.log_test_result(
                    "Platforms Status", 
                    False, 
                    f"Expected 3 platforms, found {len(platforms)}: {list(platforms.keys())}",
                    data
                )
        else:
            self.log_test_result("Platforms Status", False, f"Failed to get platforms status: {data}")
    
    async def test_mt5_libertex_account(self):
        """Test MT5 Libertex account endpoint"""
        success, data = await self.make_request("GET", "/api/platforms/MT5_LIBERTEX/account")
        
        if success:
            account = data.get("account", {})
            balance = account.get("balance", 0)
            leverage = account.get("leverage", 0)
            currency = account.get("currency", "")
            
            # Expected: Balance 50000 EUR, Leverage 1000
            if balance > 0 and leverage > 0 and currency == "EUR":
                self.log_test_result(
                    "MT5 Libertex Account", 
                    True, 
                    f"Balance: {balance} {currency}, Leverage: {leverage}",
                    {"balance": balance, "leverage": leverage, "currency": currency}
                )
            else:
                self.log_test_result(
                    "MT5 Libertex Account", 
                    False, 
                    f"Unexpected values - Balance: {balance}, Leverage: {leverage}, Currency: {currency}",
                    data
                )
        else:
            error_msg = data.get("detail", str(data))
            self.log_test_result("MT5 Libertex Account", False, f"Failed to get account: {error_msg}", data)
    
    async def test_mt5_icmarkets_account(self):
        """Test MT5 ICMarkets account endpoint"""
        success, data = await self.make_request("GET", "/api/platforms/MT5_ICMARKETS/account")
        
        if success:
            account = data.get("account", {})
            balance = account.get("balance", 0)
            leverage = account.get("leverage", 0)
            currency = account.get("currency", "")
            
            # Expected: Balance ~2204 EUR, Leverage 30
            if balance > 0 and leverage > 0 and currency == "EUR":
                self.log_test_result(
                    "MT5 ICMarkets Account", 
                    True, 
                    f"Balance: {balance} {currency}, Leverage: {leverage}",
                    {"balance": balance, "leverage": leverage, "currency": currency}
                )
            else:
                self.log_test_result(
                    "MT5 ICMarkets Account", 
                    False, 
                    f"Unexpected values - Balance: {balance}, Leverage: {leverage}, Currency: {currency}",
                    data
                )
        else:
            error_msg = data.get("detail", str(data))
            self.log_test_result("MT5 ICMarkets Account", False, f"Failed to get account: {error_msg}", data)
    
    async def test_settings_platforms(self):
        """Test settings endpoint for platform configuration"""
        success, data = await self.make_request("GET", "/api/settings")
        
        if success:
            active_platforms = data.get("active_platforms", None)
            default_platform = data.get("default_platform", None)
            
            # Check if active_platforms is an array and default_platform is defined
            if active_platforms is not None and default_platform is not None:
                self.log_test_result(
                    "Settings Platform Config", 
                    True, 
                    f"Active platforms: {active_platforms}, Default: {default_platform}",
                    {"active_platforms": active_platforms, "default_platform": default_platform}
                )
            else:
                self.log_test_result(
                    "Settings Platform Config", 
                    False, 
                    f"Missing platform config - Active: {active_platforms}, Default: {default_platform}",
                    data
                )
        else:
            self.log_test_result("Settings Platform Config", False, f"Failed to get settings: {data}")
    
    async def test_commodities_multi_platform_symbols(self):
        """Test commodities endpoint for multi-platform symbol mappings"""
        success, data = await self.make_request("GET", "/api/commodities")
        
        if success:
            commodities = data.get("commodities", {})
            
            # Check WTI_CRUDE specifically
            wti = commodities.get("WTI_CRUDE", {})
            libertex_symbol = wti.get("mt5_libertex_symbol")
            icmarkets_symbol = wti.get("mt5_icmarkets_symbol")
            
            # Expected: USOILCash (Libertex), WTI_F6 (ICMarkets)
            if libertex_symbol == "USOILCash" and icmarkets_symbol == "WTI_F6":
                self.log_test_result(
                    "Commodities Multi-Platform Symbols", 
                    True, 
                    f"WTI_CRUDE: Libertex={libertex_symbol}, ICMarkets={icmarkets_symbol}",
                    {"wti_libertex": libertex_symbol, "wti_icmarkets": icmarkets_symbol}
                )
            else:
                self.log_test_result(
                    "Commodities Multi-Platform Symbols", 
                    False, 
                    f"Incorrect symbols - Libertex: {libertex_symbol} (expected USOILCash), ICMarkets: {icmarkets_symbol} (expected WTI_F6)",
                    {"wti": wti}
                )
        else:
            self.log_test_result("Commodities Multi-Platform Symbols", False, f"Failed to get commodities: {data}")
    
    async def test_ai_settings_retrieval(self):
        """Test AI Settings Retrieval - GET /api/settings for ai_provider and ai_model"""
        success, data = await self.make_request("GET", "/api/settings")
        
        if success:
            ai_provider = data.get("ai_provider")
            ai_model = data.get("ai_model")
            
            # Check if AI settings fields are present
            if ai_provider is not None and ai_model is not None:
                self.log_test_result(
                    "AI Settings Retrieval", 
                    True, 
                    f"AI Provider: {ai_provider}, AI Model: {ai_model}",
                    {"ai_provider": ai_provider, "ai_model": ai_model}
                )
            else:
                self.log_test_result(
                    "AI Settings Retrieval", 
                    False, 
                    f"Missing AI settings - Provider: {ai_provider}, Model: {ai_model}",
                    data
                )
        else:
            self.log_test_result("AI Settings Retrieval", False, f"Failed to get settings: {data}")
    
    async def test_ai_chat_with_settings(self):
        """Test AI Chat with Settings - POST /api/ai-chat using settings values"""
        # First get current settings to see what provider/model is configured
        settings_success, settings_data = await self.make_request("GET", "/api/settings")
        
        if not settings_success:
            self.log_test_result("AI Chat with Settings", False, "Could not retrieve settings for AI chat test")
            return
        
        ai_provider = settings_data.get("ai_provider", "emergent")
        ai_model = settings_data.get("ai_model", "gpt-5")
        
        # Test AI chat endpoint with German message using query parameters
        endpoint = "/api/ai-chat?message=Hallo, was ist der aktuelle Gold-Preis?&session_id=test-session"
        
        success, data = await self.make_request("POST", endpoint)
        
        if success:
            response_text = data.get("response", "")
            provider_used = data.get("provider", "")
            model_used = data.get("model", "")
            
            # Check if response is meaningful and uses settings
            if response_text and len(response_text) > 10:
                self.log_test_result(
                    "AI Chat with Settings", 
                    True, 
                    f"AI responded using Provider: {provider_used}, Model: {model_used}. Response length: {len(response_text)} chars",
                    {"provider": provider_used, "model": model_used, "response_preview": response_text[:100]}
                )
            else:
                self.log_test_result(
                    "AI Chat with Settings", 
                    False, 
                    f"AI response too short or empty: {response_text}",
                    data
                )
        else:
            error_msg = data.get("detail", str(data))
            self.log_test_result("AI Chat with Settings", False, f"AI Chat failed: {error_msg}", data)
    
    async def test_market_data_endpoint(self):
        """Test Market Data - GET /api/market/all (main market data endpoint)"""
        success, data = await self.make_request("GET", "/api/market/all")
        
        if success:
            markets = data.get("markets", {})
            commodities = data.get("commodities", [])
            
            # Check if we have market data for key commodities
            key_commodities = ["GOLD", "WTI_CRUDE", "SILVER"]
            found_data = []
            
            for commodity in key_commodities:
                if commodity in markets and markets[commodity].get("price"):
                    price = markets[commodity]["price"]
                    signal = markets[commodity].get("signal", "UNKNOWN")
                    found_data.append(f"{commodity}=${price:.2f}({signal})")
            
            if len(found_data) >= 2:
                self.log_test_result(
                    "Market Data Endpoint", 
                    True, 
                    f"Live data available: {', '.join(found_data)}",
                    {"markets_count": len(markets), "commodities_count": len(commodities)}
                )
            else:
                self.log_test_result(
                    "Market Data Endpoint", 
                    False, 
                    f"Insufficient market data. Found: {found_data}",
                    data
                )
        else:
            self.log_test_result("Market Data Endpoint", False, f"Failed to get market data: {data}")
    
    async def test_backend_logs_ai_settings(self):
        """Test Backend Logs for AI Settings Usage - Verify logs show settings being used"""
        # Check backend logs for the specific AI Chat settings usage message
        # Expected log: "AI Chat: Using provider=emergent, model=gpt-5 (from settings)"
        
        try:
            # Check if the log file contains the expected message
            import subprocess
            result = subprocess.run(
                ["grep", "-i", "AI Chat: Using provider", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                log_lines = result.stdout.strip().split('\n')
                latest_log = log_lines[-1] if log_lines else ""
                
                if "emergent" in latest_log and "gpt-5" in latest_log and "from settings" in latest_log:
                    self.log_test_result(
                        "Backend Logs AI Settings", 
                        True, 
                        f"✅ Backend logs confirm settings usage: {latest_log.split(' - ')[-1]}",
                        {"log_message": latest_log}
                    )
                else:
                    self.log_test_result(
                        "Backend Logs AI Settings", 
                        False, 
                        f"Log found but doesn't match expected format: {latest_log}",
                        {"log_message": latest_log}
                    )
            else:
                self.log_test_result(
                    "Backend Logs AI Settings", 
                    False, 
                    "No AI Chat settings logs found in backend.err.log",
                    {"grep_result": result.stdout}
                )
        except Exception as e:
            self.log_test_result(
                "Backend Logs AI Settings", 
                False, 
                f"Error checking logs: {str(e)}",
                {"error": str(e)}
            )
    
    async def test_comprehensive_trade_execution(self):
        """KRITISCHER TEST: Trade Execution mit Duplikat-Prüfung"""
        logger.info("🔥 KRITISCHER TEST: Trade Execution mit Duplikat-Prüfung")
        
        # Test data
        trade_data = {
            "trade_type": "BUY",
            "price": 4200.0,
            "commodity": "GOLD",
            "quantity": 0.01
        }
        
        executed_tickets = []
        
        # Execute 3 trades and check for duplicates
        for i in range(3):
            success, data = await self.make_request("POST", "/api/trades/execute", trade_data)
            
            if success:
                success_status = data.get("success", False)
                ticket = data.get("ticket")
                mt5_ticket = data.get("mt5_ticket")
                
                if success_status and ticket and mt5_ticket:
                    executed_tickets.append({
                        "ticket": ticket,
                        "mt5_ticket": mt5_ticket,
                        "execution": i + 1
                    })
                    logger.info(f"Trade {i+1}: SUCCESS - Ticket: {ticket}, MT5: {mt5_ticket}")
                else:
                    logger.error(f"Trade {i+1}: FAILED - Response: {data}")
            else:
                logger.error(f"Trade {i+1}: HTTP ERROR - {data}")
        
        # Check for duplicates
        unique_tickets = set(t["ticket"] for t in executed_tickets)
        unique_mt5_tickets = set(t["mt5_ticket"] for t in executed_tickets)
        
        if len(executed_tickets) == 3 and len(unique_tickets) == 3 and len(unique_mt5_tickets) == 3:
            self.log_test_result(
                "Trade Execution - No Duplicates", 
                True, 
                f"3 trades executed successfully, all unique tickets: {[t['ticket'] for t in executed_tickets]}",
                {"executed_tickets": executed_tickets}
            )
        else:
            self.log_test_result(
                "Trade Execution - No Duplicates", 
                False, 
                f"Duplicate detection failed - Executed: {len(executed_tickets)}, Unique tickets: {len(unique_tickets)}, Unique MT5: {len(unique_mt5_tickets)}",
                {"executed_tickets": executed_tickets}
            )
    
    async def test_trades_list_duplicates(self):
        """KRITISCH: Prüfe Trades List auf Duplikate und Fake-Trades"""
        success, data = await self.make_request("GET", "/api/trades/list")
        
        if success:
            trades = data.get("trades", [])
            
            # Check for duplicates (same ticket number)
            tickets = [t.get("ticket") for t in trades if t.get("ticket")]
            unique_tickets = set(tickets)
            duplicates = len(tickets) - len(unique_tickets)
            
            # Check for fake trades (mt5_ticket=null, P&L=0)
            fake_trades = []
            for trade in trades:
                if trade.get("mt5_ticket") is None and trade.get("profit_loss", 0) == 0:
                    fake_trades.append(trade.get("ticket", "unknown"))
            
            if duplicates == 0 and len(fake_trades) == 0:
                self.log_test_result(
                    "Trades List - No Duplicates/Fakes", 
                    True, 
                    f"✅ {len(trades)} trades, no duplicates, no fake trades",
                    {"total_trades": len(trades), "unique_tickets": len(unique_tickets)}
                )
            else:
                self.log_test_result(
                    "Trades List - No Duplicates/Fakes", 
                    False, 
                    f"❌ Found {duplicates} duplicates, {len(fake_trades)} fake trades",
                    {"duplicates": duplicates, "fake_trades": fake_trades, "total_trades": len(trades)}
                )
        else:
            self.log_test_result("Trades List - No Duplicates/Fakes", False, f"Failed to get trades: {data}")
    
    async def test_live_mt5_positions_comparison(self):
        """KRITISCH: Vergleiche Live MT5 Positions mit App Trades"""
        # Get MT5 Libertex positions
        libertex_success, libertex_data = await self.make_request("GET", "/api/platforms/MT5_LIBERTEX/positions")
        
        # Get MT5 ICMarkets positions  
        icmarkets_success, icmarkets_data = await self.make_request("GET", "/api/platforms/MT5_ICMARKETS/positions")
        
        # Get app trades
        trades_success, trades_data = await self.make_request("GET", "/api/trades/list")
        
        if libertex_success and icmarkets_success and trades_success:
            libertex_positions = libertex_data.get("positions", [])
            icmarkets_positions = icmarkets_data.get("positions", [])
            app_trades = trades_data.get("trades", [])
            
            # Count open positions
            total_mt5_positions = len(libertex_positions) + len(icmarkets_positions)
            open_app_trades = [t for t in app_trades if t.get("status") == "OPEN"]
            
            # Check if they match
            if total_mt5_positions == len(open_app_trades):
                self.log_test_result(
                    "MT5 Positions vs App Trades", 
                    True, 
                    f"✅ IDENTICAL: {total_mt5_positions} MT5 positions = {len(open_app_trades)} app trades",
                    {
                        "libertex_positions": len(libertex_positions),
                        "icmarkets_positions": len(icmarkets_positions),
                        "app_open_trades": len(open_app_trades)
                    }
                )
            else:
                self.log_test_result(
                    "MT5 Positions vs App Trades", 
                    False, 
                    f"❌ MISMATCH: {total_mt5_positions} MT5 positions ≠ {len(open_app_trades)} app trades",
                    {
                        "libertex_positions": len(libertex_positions),
                        "icmarkets_positions": len(icmarkets_positions),
                        "app_open_trades": len(open_app_trades)
                    }
                )
        else:
            self.log_test_result(
                "MT5 Positions vs App Trades", 
                False, 
                f"Failed to get data - Libertex: {libertex_success}, ICMarkets: {icmarkets_success}, Trades: {trades_success}"
            )
    
    async def test_settings_update_all_platform(self):
        """Test Settings Update mit ALL Platform"""
        settings_data = {"default_platform": "ALL"}
        
        success, data = await self.make_request("POST", "/api/settings", settings_data)
        
        if success:
            updated_platform = data.get("default_platform")
            if updated_platform == "ALL":
                self.log_test_result(
                    "Settings Update ALL Platform", 
                    True, 
                    f"Successfully updated to ALL platform: {updated_platform}",
                    {"default_platform": updated_platform}
                )
            else:
                self.log_test_result(
                    "Settings Update ALL Platform", 
                    False, 
                    f"Platform not updated correctly: {updated_platform}",
                    data
                )
        else:
            self.log_test_result("Settings Update ALL Platform", False, f"Failed to update settings: {data}")
    
    async def test_stability_connections(self):
        """Stability Test: 5x GET /api/platforms/status (alle 2 Sekunden)"""
        logger.info("🔄 Stability Test: 5x Platform Status Checks")
        
        stable_connections = True
        connection_results = []
        
        for i in range(5):
            if i > 0:
                await asyncio.sleep(2)  # Wait 2 seconds between requests
            
            success, data = await self.make_request("GET", "/api/platforms/status")
            
            if success:
                platforms = data.get("platforms", {})
                mt5_libertex_active = platforms.get("MT5_LIBERTEX", {}).get("active", False)
                mt5_icmarkets_active = platforms.get("MT5_ICMARKETS", {}).get("active", False)
                
                connection_results.append({
                    "check": i + 1,
                    "libertex_active": mt5_libertex_active,
                    "icmarkets_active": mt5_icmarkets_active,
                    "both_connected": mt5_libertex_active and mt5_icmarkets_active
                })
                
                if not (mt5_libertex_active and mt5_icmarkets_active):
                    stable_connections = False
                    
                logger.info(f"Check {i+1}: Libertex={mt5_libertex_active}, ICMarkets={mt5_icmarkets_active}")
            else:
                stable_connections = False
                connection_results.append({
                    "check": i + 1,
                    "error": data
                })
                logger.error(f"Check {i+1}: FAILED - {data}")
        
        if stable_connections and len(connection_results) == 5:
            self.log_test_result(
                "Stability Test - Connections", 
                True, 
                f"✅ All 5 checks passed, connections remain stable",
                {"connection_results": connection_results}
            )
        else:
            self.log_test_result(
                "Stability Test - Connections", 
                False, 
                f"❌ Stability issues detected in {5 - sum(1 for r in connection_results if r.get('both_connected', False))} checks",
                {"connection_results": connection_results}
            )
    
    async def test_platform_connections_balances(self):
        """Test Platform Connections mit Balance-Prüfung"""
        success, data = await self.make_request("GET", "/api/platforms/status")
        
        if success:
            platforms = data.get("platforms", {})
            
            # Check MT5_LIBERTEX
            libertex = platforms.get("MT5_LIBERTEX", {})
            libertex_connected = libertex.get("active", False)
            libertex_balance = libertex.get("balance", 0)
            
            # Check MT5_ICMARKETS  
            icmarkets = platforms.get("MT5_ICMARKETS", {})
            icmarkets_connected = icmarkets.get("active", False)
            icmarkets_balance = icmarkets.get("balance", 0)
            
            # Success criteria: Both connected AND both have non-zero balance
            if (libertex_connected and libertex_balance > 0 and 
                icmarkets_connected and icmarkets_balance > 0):
                self.log_test_result(
                    "Platform Connections with Balances", 
                    True, 
                    f"✅ MT5_LIBERTEX: connected={libertex_connected}, balance={libertex_balance} | MT5_ICMARKETS: connected={icmarkets_connected}, balance={icmarkets_balance}",
                    {
                        "libertex": {"connected": libertex_connected, "balance": libertex_balance},
                        "icmarkets": {"connected": icmarkets_connected, "balance": icmarkets_balance}
                    }
                )
            else:
                self.log_test_result(
                    "Platform Connections with Balances", 
                    False, 
                    f"❌ Connection/Balance issues - Libertex: connected={libertex_connected}, balance={libertex_balance} | ICMarkets: connected={icmarkets_connected}, balance={icmarkets_balance}",
                    data
                )
        else:
            self.log_test_result("Platform Connections with Balances", False, f"Failed to get platform status: {data}")

    # ========================================
    # AI TRADING BOT TESTS - CRITICAL SECTION
    # ========================================
    
    async def test_bot_status(self):
        """Test AI Trading Bot Status - GET /api/bot/status"""
        success, data = await self.make_request("GET", "/api/bot/status")
        
        if success:
            running = data.get("running", False)
            instance_running = data.get("instance_running", False)
            task_alive = data.get("task_alive", False)
            trade_count = data.get("trade_count", 0)
            last_trades = data.get("last_trades", [])
            
            # Bot should be running if auto_trading is enabled
            if running is not None and instance_running is not None:
                self.log_test_result(
                    "AI Bot Status", 
                    True, 
                    f"Bot status: running={running}, instance_running={instance_running}, task_alive={task_alive}, trade_count={trade_count}",
                    {
                        "running": running,
                        "instance_running": instance_running, 
                        "task_alive": task_alive,
                        "trade_count": trade_count,
                        "last_trades_count": len(last_trades)
                    }
                )
            else:
                self.log_test_result(
                    "AI Bot Status", 
                    False, 
                    f"Invalid bot status response: {data}",
                    data
                )
        else:
            self.log_test_result("AI Bot Status", False, f"Failed to get bot status: {data}")
    
    async def test_bot_stop(self):
        """Test AI Trading Bot Stop - POST /api/bot/stop"""
        success, data = await self.make_request("POST", "/api/bot/stop")
        
        if success:
            success_flag = data.get("success", False)
            message = data.get("message", "")
            
            if success_flag and "gestoppt" in message:
                self.log_test_result(
                    "AI Bot Stop", 
                    True, 
                    f"Bot stopped successfully: {message}",
                    {"success": success_flag, "message": message}
                )
            else:
                self.log_test_result(
                    "AI Bot Stop", 
                    False, 
                    f"Bot stop failed: success={success_flag}, message={message}",
                    data
                )
        else:
            self.log_test_result("AI Bot Stop", False, f"Failed to stop bot: {data}")
    
    async def test_bot_start(self):
        """Test AI Trading Bot Start - POST /api/bot/start"""
        success, data = await self.make_request("POST", "/api/bot/start")
        
        if success:
            success_flag = data.get("success", False)
            message = data.get("message", "")
            
            if success_flag and "gestartet" in message:
                self.log_test_result(
                    "AI Bot Start", 
                    True, 
                    f"Bot started successfully: {message}",
                    {"success": success_flag, "message": message}
                )
            else:
                self.log_test_result(
                    "AI Bot Start", 
                    False, 
                    f"Bot start failed: success={success_flag}, message={message}",
                    data
                )
        else:
            self.log_test_result("AI Bot Start", False, f"Failed to start bot: {data}")
    
    async def test_bot_lifecycle(self):
        """Test Complete AI Bot Lifecycle: Status -> Stop -> Start"""
        logger.info("🤖 Testing AI Bot Lifecycle: Status -> Stop -> Start")
        
        # 1. Check initial status
        await self.test_bot_status()
        
        # 2. Stop bot
        await self.test_bot_stop()
        
        # Wait a moment for bot to stop
        await asyncio.sleep(2)
        
        # 3. Verify bot is stopped
        success, data = await self.make_request("GET", "/api/bot/status")
        if success:
            running = data.get("running", True)  # Default True to catch failures
            if not running:
                self.log_test_result(
                    "AI Bot Lifecycle - Stop Verification", 
                    True, 
                    f"Bot confirmed stopped: running={running}",
                    {"running": running}
                )
            else:
                self.log_test_result(
                    "AI Bot Lifecycle - Stop Verification", 
                    False, 
                    f"Bot still running after stop command: running={running}",
                    data
                )
        
        # 4. Start bot again
        await self.test_bot_start()
        
        # Wait a moment for bot to start
        await asyncio.sleep(2)
        
        # 5. Verify bot is running
        success, data = await self.make_request("GET", "/api/bot/status")
        if success:
            running = data.get("running", False)
            if running:
                self.log_test_result(
                    "AI Bot Lifecycle - Start Verification", 
                    True, 
                    f"Bot confirmed running: running={running}",
                    {"running": running}
                )
            else:
                self.log_test_result(
                    "AI Bot Lifecycle - Start Verification", 
                    False, 
                    f"Bot not running after start command: running={running}",
                    data
                )
    
    async def test_settings_auto_trading_toggle(self):
        """Test Settings Auto-Trading Toggle Integration"""
        logger.info("⚙️ Testing Auto-Trading Toggle Integration")
        
        # 1. Set auto_trading=false
        settings_data = {"auto_trading": False}
        success, data = await self.make_request("POST", "/api/settings", settings_data)
        
        if success:
            auto_trading = data.get("auto_trading", True)  # Default True to catch failures
            if not auto_trading:
                self.log_test_result(
                    "Settings Auto-Trading Disable", 
                    True, 
                    f"Auto-trading disabled: auto_trading={auto_trading}",
                    {"auto_trading": auto_trading}
                )
                
                # Wait for bot to stop automatically
                await asyncio.sleep(3)
                
                # Check if bot stopped
                bot_success, bot_data = await self.make_request("GET", "/api/bot/status")
                if bot_success:
                    bot_running = bot_data.get("running", True)
                    if not bot_running:
                        self.log_test_result(
                            "Auto-Trading Disable - Bot Auto-Stop", 
                            True, 
                            f"Bot automatically stopped when auto_trading=false: running={bot_running}",
                            {"bot_running": bot_running}
                        )
                    else:
                        self.log_test_result(
                            "Auto-Trading Disable - Bot Auto-Stop", 
                            False, 
                            f"Bot did not stop automatically: running={bot_running}",
                            bot_data
                        )
            else:
                self.log_test_result(
                    "Settings Auto-Trading Disable", 
                    False, 
                    f"Failed to disable auto-trading: auto_trading={auto_trading}",
                    data
                )
        
        # 2. Try to start bot when auto_trading=false (should fail)
        start_success, start_data = await self.make_request("POST", "/api/bot/start")
        if not start_success or not start_data.get("success", True):
            self.log_test_result(
                "Bot Start Blocked when Auto-Trading Disabled", 
                True, 
                f"Bot start correctly blocked: {start_data.get('message', 'No message')}",
                start_data
            )
        else:
            self.log_test_result(
                "Bot Start Blocked when Auto-Trading Disabled", 
                False, 
                f"Bot start should have been blocked but succeeded: {start_data}",
                start_data
            )
        
        # 3. Set auto_trading=true
        settings_data = {"auto_trading": True}
        success, data = await self.make_request("POST", "/api/settings", settings_data)
        
        if success:
            auto_trading = data.get("auto_trading", False)
            if auto_trading:
                self.log_test_result(
                    "Settings Auto-Trading Enable", 
                    True, 
                    f"Auto-trading enabled: auto_trading={auto_trading}",
                    {"auto_trading": auto_trading}
                )
                
                # Wait for bot to start automatically
                await asyncio.sleep(3)
                
                # Check if bot started
                bot_success, bot_data = await self.make_request("GET", "/api/bot/status")
                if bot_success:
                    bot_running = bot_data.get("running", False)
                    if bot_running:
                        self.log_test_result(
                            "Auto-Trading Enable - Bot Auto-Start", 
                            True, 
                            f"Bot automatically started when auto_trading=true: running={bot_running}",
                            {"bot_running": bot_running}
                        )
                    else:
                        self.log_test_result(
                            "Auto-Trading Enable - Bot Auto-Start", 
                            False, 
                            f"Bot did not start automatically: running={bot_running}",
                            bot_data
                        )
            else:
                self.log_test_result(
                    "Settings Auto-Trading Enable", 
                    False, 
                    f"Failed to enable auto-trading: auto_trading={auto_trading}",
                    data
                )
    
    async def test_bot_requirements_check(self):
        """Test Bot Requirements: Platform Connections, Market Data, Settings"""
        logger.info("🔍 Testing Bot Requirements")
        
        # 1. Platform Connections
        platform_success, platform_data = await self.make_request("GET", "/api/platforms/status")
        platforms_ok = False
        if platform_success:
            platforms = platform_data.get("platforms", {})
            libertex_active = platforms.get("MT5_LIBERTEX_DEMO", {}).get("active", False) or platforms.get("MT5_LIBERTEX", {}).get("active", False)
            icmarkets_active = platforms.get("MT5_ICMARKETS_DEMO", {}).get("active", False) or platforms.get("MT5_ICMARKETS", {}).get("active", False)
            platforms_ok = libertex_active or icmarkets_active
        
        # 2. Market Data
        market_success, market_data = await self.make_request("GET", "/api/market/all")
        market_data_ok = False
        commodities_count = 0
        if market_success:
            markets = market_data.get("markets", {})
            commodities_count = len(markets)
            market_data_ok = commodities_count >= 10  # At least 10 commodities
        
        # 3. Settings
        settings_success, settings_data = await self.make_request("GET", "/api/settings")
        settings_ok = False
        if settings_success:
            enabled_commodities = settings_data.get("enabled_commodities", [])
            auto_trading = settings_data.get("auto_trading", False)
            settings_ok = len(enabled_commodities) > 0
        
        # Overall assessment
        all_requirements_met = platforms_ok and market_data_ok and settings_ok
        
        self.log_test_result(
            "Bot Requirements Check", 
            all_requirements_met, 
            f"Platform connections: {platforms_ok}, Market data ({commodities_count} commodities): {market_data_ok}, Settings: {settings_ok}",
            {
                "platforms_ok": platforms_ok,
                "market_data_ok": market_data_ok,
                "commodities_count": commodities_count,
                "settings_ok": settings_ok,
                "all_requirements_met": all_requirements_met
            }
        )
    
    async def check_backend_logs_bot_activity(self):
        """Check Backend Logs for Bot Activity"""
        logger.info("📋 Checking Backend Logs for Bot Activity")
        
        try:
            import subprocess
            
            # Check for bot iteration logs
            result = subprocess.run(
                ["grep", "-i", "Bot Iteration", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            bot_iterations_found = result.returncode == 0 and result.stdout
            
            # Check for market data updates
            result2 = subprocess.run(
                ["grep", "-i", "Marktdaten aktualisiert", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            market_updates_found = result2.returncode == 0 and result2.stdout
            
            # Check for position monitoring
            result3 = subprocess.run(
                ["grep", "-i", "Überwache offene Positionen", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            position_monitoring_found = result3.returncode == 0 and result3.stdout
            
            # Check for AI analysis
            result4 = subprocess.run(
                ["grep", "-i", "KI analysiert Markt", "/var/log/supervisor/backend.err.log"],
                capture_output=True, text=True, timeout=5
            )
            
            ai_analysis_found = result4.returncode == 0 and result4.stdout
            
            # Count recent bot activities (last 10 lines)
            recent_activities = 0
            if bot_iterations_found:
                recent_lines = result.stdout.strip().split('\n')[-10:]
                recent_activities = len(recent_lines)
            
            # Success if we find bot iterations and market updates
            logs_healthy = bot_iterations_found and market_updates_found
            
            if logs_healthy:
                self.log_test_result(
                    "Backend Logs - Bot Activity", 
                    True, 
                    f"✅ Bot activity detected: {recent_activities} recent iterations, market updates: {market_updates_found}, position monitoring: {position_monitoring_found}",
                    {
                        "bot_iterations": bot_iterations_found,
                        "market_updates": market_updates_found,
                        "position_monitoring": position_monitoring_found,
                        "ai_analysis": ai_analysis_found,
                        "recent_activities": recent_activities
                    }
                )
            else:
                self.log_test_result(
                    "Backend Logs - Bot Activity", 
                    False, 
                    f"❌ Missing bot activity - Iterations: {bot_iterations_found}, Market updates: {market_updates_found}",
                    {
                        "bot_iterations": bot_iterations_found,
                        "market_updates": market_updates_found,
                        "position_monitoring": position_monitoring_found,
                        "ai_analysis": ai_analysis_found
                    }
                )
                
        except Exception as e:
            self.log_test_result(
                "Backend Logs - Bot Activity", 
                False, 
                f"Error checking logs: {str(e)}",
                {"error": str(e)}
            )
    
    async def test_market_data_for_bot(self):
        """Test Market Data Availability for Bot (specific commodities)"""
        success, data = await self.make_request("GET", "/api/market/all")
        
        if success:
            markets = data.get("markets", {})
            commodities = data.get("commodities", [])
            
            # Check for specific commodities that bot needs
            required_commodities = ["GOLD", "WTI_CRUDE", "SILVER", "PLATINUM"]
            found_commodities = []
            missing_commodities = []
            
            for commodity in required_commodities:
                if commodity in markets and markets[commodity].get("price"):
                    price = markets[commodity]["price"]
                    rsi = markets[commodity].get("rsi", "N/A")
                    signal = markets[commodity].get("signal", "N/A")
                    found_commodities.append(f"{commodity}=${price:.2f}(RSI:{rsi},Signal:{signal})")
                else:
                    missing_commodities.append(commodity)
            
            # Success if we have at least 3 of the required commodities
            if len(found_commodities) >= 3:
                self.log_test_result(
                    "Market Data for Bot", 
                    True, 
                    f"✅ {len(found_commodities)}/4 required commodities available: {', '.join(found_commodities)}",
                    {
                        "total_markets": len(markets),
                        "found_commodities": found_commodities,
                        "missing_commodities": missing_commodities
                    }
                )
            else:
                self.log_test_result(
                    "Market Data for Bot", 
                    False, 
                    f"❌ Insufficient market data - Found: {found_commodities}, Missing: {missing_commodities}",
                    data
                )
        else:
            self.log_test_result("Market Data for Bot", False, f"Failed to get market data: {data}")
    
    async def test_trades_list_for_bot(self):
        """Test Trades List (Bot needs to monitor existing trades)"""
        success, data = await self.make_request("GET", "/api/trades/list")
        
        if success:
            trades = data.get("trades", [])
            open_trades = [t for t in trades if t.get("status") == "OPEN"]
            closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
            
            # Check for AI-generated trades (strategy_signal contains "AI" or "Bot")
            ai_trades = []
            manual_trades = []
            
            for trade in trades:
                strategy = trade.get("strategy_signal", "")
                if "AI" in strategy or "Bot" in strategy or "KI" in strategy:
                    ai_trades.append(trade.get("id", "unknown"))
                else:
                    manual_trades.append(trade.get("id", "unknown"))
            
            self.log_test_result(
                "Trades List for Bot", 
                True, 
                f"✅ Total trades: {len(trades)}, Open: {len(open_trades)}, Closed: {len(closed_trades)}, AI-generated: {len(ai_trades)}, Manual: {len(manual_trades)}",
                {
                    "total_trades": len(trades),
                    "open_trades": len(open_trades),
                    "closed_trades": len(closed_trades),
                    "ai_trades": len(ai_trades),
                    "manual_trades": len(manual_trades)
                }
            )
        else:
            self.log_test_result("Trades List for Bot", False, f"Failed to get trades: {data}")

    async def run_ai_bot_tests(self):
        """Run comprehensive AI Trading Bot tests"""
        logger.info("\n" + "="*80)
        logger.info("🤖 AI TRADING BOT COMPREHENSIVE TESTS")
        logger.info("="*80)
        
        # A. Bot Lifecycle Test
        logger.info("\n=== A. BOT LIFECYCLE TEST ===")
        await self.test_bot_lifecycle()
        
        # B. Auto-Trading Toggle Test
        logger.info("\n=== B. AUTO-TRADING TOGGLE TEST ===")
        await self.test_settings_auto_trading_toggle()
        
        # C. Bot Requirements Check
        logger.info("\n=== C. BOT REQUIREMENTS CHECK ===")
        await self.test_bot_requirements_check()
        await self.test_market_data_for_bot()
        await self.test_trades_list_for_bot()
        
        # D. Backend Logs Check
        logger.info("\n=== D. BACKEND LOGS CHECK ===")
        await self.check_backend_logs_bot_activity()
        
        logger.info("\n🤖 AI Trading Bot Tests Complete")
        logger.info("="*80)

    async def run_all_tests(self):
        """Run all backend tests in sequence - KOMPLETTER APP-TEST"""
        logger.info("🚀 KOMPLETTER APP-TEST - Alle Funktionen systematisch testen")
        logger.info(f"Testing against: {self.base_url}")
        
        # 1. Platform Connections (KRITISCH!)
        logger.info("\n=== 1. PLATFORM CONNECTIONS ===")
        await self.test_platforms_status()
        await self.test_platform_connections_balances()
        
        # 2. Trade-Execution Test (KRITISCH!)
        logger.info("\n=== 2. TRADE-EXECUTION TEST (KRITISCH!) ===")
        await self.test_comprehensive_trade_execution()
        
        # 3. Trades List (KRITISCH!)
        logger.info("\n=== 3. TRADES LIST (KRITISCH!) ===")
        await self.test_trades_list()
        await self.test_trades_list_duplicates()
        
        # 4. Live MT5 Positions
        logger.info("\n=== 4. LIVE MT5 POSITIONS ===")
        await self.test_mt5_libertex_account()
        await self.test_mt5_icmarkets_account()
        await self.test_live_mt5_positions_comparison()
        
        # 5. Settings
        logger.info("\n=== 5. SETTINGS ===")
        await self.test_settings_get()
        await self.test_settings_update_all_platform()
        
        # 6. Stability Test
        logger.info("\n=== 6. STABILITY TEST ===")
        await self.test_stability_connections()
        
        # Additional comprehensive tests
        logger.info("\n=== ADDITIONAL COMPREHENSIVE TESTS ===")
        await self.test_api_root()
        await self.test_market_data_all()
        await self.test_commodities_list()
        
        # Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info("\n" + "="*80)
        logger.info("🏁 TEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
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
    # Backend URL from environment
    backend_url = "https://smart-trader-201.preview.emergentagent.com"
    
    async with RohstoffTraderTester(backend_url) as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
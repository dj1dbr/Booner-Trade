# Fix Plan - Trading Issues

## Problems to Fix:

1. ❌ **Bestätigungsfrage entfernen** beim Schließen von Trades
2. ❌ **Fehler "{Objekt Objekt}"** beim Schließen beheben
3. ❌ **P&L 0,00€** - Trades werden geschlossen aber zeigen kein P&L
4. ❌ **MetaAPI Error Codes** - TRADE_RETCODE_INVALID_STOPS, TRADE_RETCODE_PRICE_OFF
5. ❌ **Trading KI schließt keine echten MT5 Positionen** - nur DB-Trades
6. ✅ **UI Tabs** - Offene/Geschlossene Trades trennen

## Implementation Steps:

### 1. Remove Confirmation Dialog (Dashboard.jsx)
- Line 490: Remove `window.confirm` from `handleCloseTrade`
- Line 1451: Remove `window.confirm` from chart modal close button

### 2. Fix Error Message (Dashboard.jsx)
- Line 515: Improve error serialization
- Add proper error.response.data handling

### 3. Fix AI Trading Functions (ai_trading_functions.py)
- `close_all_trades`: Must close real MT5 positions via MetaAPI
- `close_trades_by_symbol`: Same fix
- `close_trade`: Add MT5 position closing

### 4. Add Trades Tabs UI (Dashboard.jsx)
- Create sub-tabs for "Offene Trades" and "Geschlossene Trades"
- Filter trades by status
- Keep P&L calculations separate

### 5. Fix MetaAPI Close Endpoint (server.py)
- Add better error handling for MetaAPI responses
- Return detailed error messages
- Handle TRADE_RETCODE errors

### 6. Improve P&L Calculation
- Ensure exit_price is captured from MT5
- Calculate P&L correctly for both LONG and SHORT positions
- Handle currency conversions

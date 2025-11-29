#!/bin/bash

# Booner Trade - Check Application Logs
# Hilft beim Debuggen wenn die App abstürzt

echo "======================================"
echo "Booner Trade - Log Viewer"
echo "======================================"
echo ""

APP_NAME="Booner Trade"
LOG_DIR="$HOME/Library/Logs/$APP_NAME"

echo "Checking for logs in: $LOG_DIR"
echo ""

if [ -d "$LOG_DIR" ]; then
    echo "✅ Log directory found"
    echo ""
    
    # Show latest main log
    if [ -f "$LOG_DIR/main.log" ]; then
        echo "📋 MAIN LOG (last 50 lines):"
        echo "================================"
        tail -50 "$LOG_DIR/main.log"
        echo ""
    fi
    
    # Show latest error log
    if [ -f "$LOG_DIR/error.log" ]; then
        echo "❌ ERROR LOG (last 50 lines):"
        echo "================================"
        tail -50 "$LOG_DIR/error.log"
        echo ""
    fi
    
    # List all log files
    echo "📁 All log files:"
    ls -lh "$LOG_DIR"
else
    echo "⚠️  No log directory found. App may not have started at all."
    echo ""
    echo "Try checking macOS Console.app:"
    echo "1. Open Console.app"
    echo "2. Filter for: 'Booner Trade'"
    echo "3. Look for crash logs"
    echo ""
fi

# Check macOS crash logs
CRASH_DIR="$HOME/Library/Logs/DiagnosticReports"
echo "Checking for crash reports..."
CRASHES=$(find "$CRASH_DIR" -name "*Booner*" -mtime -1 2>/dev/null)

if [ -n "$CRASHES" ]; then
    echo "❌ Found crash report(s):"
    echo "$CRASHES"
    echo ""
    echo "Latest crash report:"
    echo "================================"
    ls -t "$CRASH_DIR"/*Booner* 2>/dev/null | head -1 | xargs tail -100
else
    echo "✅ No recent crash reports found"
fi

echo ""
echo "======================================"
echo "Next Steps:"
echo "1. Check the logs above for errors"
echo "2. Open Console.app for real-time logging"
echo "3. Try running: open -a 'Booner Trade' (to see terminal output)"
echo "======================================"

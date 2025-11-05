#!/bin/bash
# ============================================================================
# Discord RAG Bot - Health Check Script
# ============================================================================
# Verifies that the bot is running and healthy
# ============================================================================

set -e

# Check if PID file exists and process is running
if [ -f /tmp/bot.pid ]; then
    PID=$(cat /tmp/bot.pid)

    # Check if process is running
    if kill -0 "$PID" 2>/dev/null; then
        # Process is running

        # Check if log file exists and has recent activity
        if [ -f "${APP_HOME}/logs/bot.log" ]; then
            # Check if file was modified in last 5 minutes
            if [ $(find "${APP_HOME}/logs/bot.log" -mmin -5 | wc -l) -gt 0 ]; then
                # Check for errors in recent logs
                if tail -n 50 "${APP_HOME}/logs/bot.log" | grep -qi "critical\|fatal"; then
                    echo "Health check FAILED: Critical errors in logs"
                    exit 1
                fi

                echo "Health check PASSED: Bot is running and active"
                exit 0
            fi
        fi

        echo "Health check WARNING: Bot running but no recent log activity"
        exit 0
    else
        echo "Health check FAILED: Process not running (PID: $PID)"
        exit 1
    fi
else
    echo "Health check FAILED: PID file not found"
    exit 1
fi

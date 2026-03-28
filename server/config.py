# ==============================
# CONFIGURATION FILE
# ==============================

import os

# Set to True for detailed debug output
DEBUG_MODE = True

# Flask web server port
PORT = int(os.environ.get('PORT', 5000))

# WebSocket server port
WEBSOCKET_PORT = 8765

# Allowed commands (security whitelist)
ALLOWED_COMMANDS = [
    "whoami", 
    "hostname", 
    "ipconfig", 
    "systeminfo", 
    "netstat", 
    "tasklist",
    "echo",
    "ver"
]

# Authentication method: "windows" or "json"
AUTH_METHOD = "windows"

# Connection settings
MAX_CONNECTIONS = 20
TIMEOUT = 60

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
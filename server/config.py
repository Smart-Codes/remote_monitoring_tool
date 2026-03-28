# ==============================
# CONFIGURATION FILE
# ==============================

import os

# Set to True for detailed debug output
DEBUG_MODE = True

# Server settings
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000

# Allowed commands (security whitelist)
ALLOWED_COMMANDS = ["whoami", "hostname", "ipconfig", "systeminfo", "netstat", "tasklist"]

# Authentication method: "windows" or "json"
AUTH_METHOD = "windows"

# Connection settings
MAX_CONNECTIONS = 10
TIMEOUT = 60

# Telegram Bot Configuration (get from environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')
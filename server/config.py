# ==============================
# CONFIGURATION FILE
# ==============================
import os

# Set to True for detailed debug output
DEBUG_MODE = True

# Server settings - Railway will override PORT
HOST = "0.0.0.0"
PORT = 5000  # Default, will be overridden by Railway

# Allowed commands (security whitelist)
ALLOWED_COMMANDS = ["whoami", "hostname", "ipconfig", "systeminfo", "tasklist", "netstat"]

# Authentication method: "windows" or "json"
AUTH_METHOD = "windows"

# Connection settings
MAX_CONNECTIONS = 5
TIMEOUT = 30

# Telegram Bot Configuration
# Get these from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Log file (backup)
LOG_FILE = "logs.txt"
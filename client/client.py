"""
Client Module - Using WebSockets for Render compatibility
"""

import asyncio
import websockets
import json
import platform
import getpass
import subprocess
import sys
import os
import time

SERVER_URL = "wss://remote-monitoring-tool.onrender.com:8765"  # WebSocket URL

def get_exact_username():
    """Get exact Windows username format"""
    try:
        result = subprocess.getoutput('whoami').strip()
        return result
    except:
        return getpass.getuser()

def get_system_info():
    """Gather system information"""
    try:
        hostname = socket.gethostname()
        ip_addresses = []
        try:
            hostname_resolved = socket.gethostbyname_ex(hostname)
            ip_addresses = hostname_resolved[2]
        except:
            ip_addresses = [socket.gethostbyname(hostname)]
        
        exact_user = get_exact_username()
        
        info = f"""
╔══════════════════════════════════════════════════════════╗
║                    SYSTEM INFORMATION                     ║
╠══════════════════════════════════════════════════════════╣
║ IP Addresses:   {', '.join(ip_addresses[:2]):<45} ║
║ Hostname:       {hostname:<45} ║
║ OS:             {platform.system()} {platform.release():<30} ║
║ Architecture:   {platform.machine():<45} ║
║ Windows User:   {exact_user:<45} ║
║ Python Version: {platform.python_version():<45} ║
╚══════════════════════════════════════════════════════════╝
"""
        return info
    except Exception as e:
        return f"Error getting system info: {e}"

async def run_client():
    """Main client function using WebSockets"""
    print("\n" + "="*60)
    print("  REMOTE MONITORING CLIENT (WebSocket)")
    print("="*60)
    
    try:
        print(f"\n[+] Connecting to: {SERVER_URL}")
        
        # Connect to WebSocket server
        async with websockets.connect(SERVER_URL) as websocket:
            # Get credentials
            exact_username = get_exact_username()
            display_username = exact_username.split('\\')[-1] if '\\' in exact_username else exact_username
            
            print(f"\n[+] Windows Username: {exact_username}")
            print(f"[+] Use this username: '{display_username}'")
            print(f"[+] Password: Your Windows login password\n")
            
            # Get credentials
            print("=== LOGIN ===\n")
            username = input(f"Username [{display_username}]: ").strip()
            
            if not username:
                username = display_username
                print(f"[+] Using detected username: '{username}'")
            
            password = getpass.getpass("Password: ")
            
            # Send credentials
            await websocket.send(json.dumps({
                'username': username,
                'password': password
            }))
            
            # Get authentication response
            response = await websocket.recv()
            auth_response = json.loads(response)
            
            if auth_response.get('status') == 'AUTH_SUCCESS':
                print("\n[✓] Login successful! Connected to server.\n")
                
                # Send system info
                system_info = get_system_info()
                await websocket.send(system_info)
                
                print("[+] Connected and waiting for commands...")
                print("[+] Press Ctrl+C to disconnect\n")
                
                # Keep connection alive and listen for commands
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)
                        
                        if data.get('type') == 'ping':
                            await websocket.send(json.dumps({'type': 'pong'}))
                        elif data.get('type') == 'command':
                            command = data.get('command')
                            print(f"\n[+] Executing command: {command}")
                            
                            # Execute command
                            output = subprocess.getoutput(command)
                            
                            # Send output back
                            await websocket.send(json.dumps({
                                'type': 'command_response',
                                'command': command,
                                'output': output
                            }))
                            
                            print("\n" + "="*60)
                            print(f"  COMMAND EXECUTED: {command}")
                            print("="*60)
                            print(output)
                            print("="*60)
                    
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"\n[!] Error: {e}")
                        break
            
            else:
                print("\n[✗] Login failed!")
                print(f"\n[!] Please try with exact username: '{display_username}'")
                print("[!] Make sure you're using your Windows login password")
                input("\nPress Enter to exit...")
                sys.exit(1)
    
    except websockets.exceptions.InvalidURI:
        print(f"\n[✗] Invalid WebSocket URL: {SERVER_URL}")
        print("[!] Make sure the URL is correct")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except ConnectionRefusedError:
        print("\n[✗] Server is not running or unreachable!")
        print("[!] Please check if the server is online")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[+] Disconnecting...")
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    import socket  # Import here to avoid issues
    asyncio.run(run_client())
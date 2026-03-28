import socket
import sys

def connect_to_server():
    # Your Railway app URL (without https)
    # Example: your-app-name.up.railway.app
    host = input("Enter server host (e.g., your-app.up.railway.app): ").strip()
    port = 5000
    
    try:
        # Create socket
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        
        print("\n=== LOGIN ===\n")
        username = input("Username: ")
        password = input("Password: ")
        
        # Send credentials
        client.send(f"{username},{password}".encode())
        
        # Get response
        response = client.recv(1024).decode()
        
        if response == "AUTH_SUCCESS":
            print("\n✅ Login successful!")
            
            # Send system info (simulated)
            system_info = f"Client connected from {host}"
            client.send(system_info.encode())
            
            # Receive command
            command = client.recv(1024).decode()
            print(f"\nCommand received: {command}")
            
            # Execute command and send result
            import subprocess
            result = subprocess.getoutput(command)
            client.send(result.encode())
            
            print("\n=== COMMAND OUTPUT ===")
            print(result)
        
        else:
            print("\n❌ Login failed!")
        
        client.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    connect_to_server()
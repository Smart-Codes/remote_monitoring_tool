import socket
import sys

def test_connection():
    host = input("Enter server host: ").strip()
    port = 5000
    
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        
        username = input("Username: ")
        password = input("Password: ")
        
        client.send(f"{username},{password}".encode())
        
        response = client.recv(1024).decode()
        print(f"Response: {response}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
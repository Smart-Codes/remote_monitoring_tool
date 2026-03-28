"""
Client EXE Launcher - Opens website in background and starts client
"""

import webbrowser
import threading
import time
import sys
import os

def open_website():
    """Open website in background"""
    time.sleep(1)
    try:
        webbrowser.open('https://test.com')
    except:
        pass

def run_client():
    """Run the client"""
    try:
        # Get application path
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        # Change to application directory
        os.chdir(application_path)
        
        # Add to path
        if application_path not in sys.path:
            sys.path.insert(0, application_path)
        
        # Import and run client
        import client
        client.run_client()
        
    except Exception as e:
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

def main():
    """Main function"""
    # Clear console
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*60)
    print("  CYBERSEC REMOTE MONITORING CLIENT")
    print("="*60)
    
    # Start website in background thread
    website_thread = threading.Thread(target=open_website, daemon=True)
    website_thread.start()
    
    print("\n[+] Connecting to server...")
    print("[+] Loading website in background...\n")
    print("="*60)
    
    # Run the client
    run_client()

if __name__ == "__main__":
    main()
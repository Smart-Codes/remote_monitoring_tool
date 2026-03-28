"""
Server EXE Launcher - Opens website in background and starts server
"""

import webbrowser
import threading
import time
import sys
import os
import subprocess
import tempfile

def open_website():
    """Open website in background"""
    time.sleep(1)  # Small delay to ensure smooth execution
    try:
        webbrowser.open('https://test.com')
    except:
        pass  # Silently fail if website can't be opened

def extract_data_files():
    """Extract data files if running as EXE"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = os.path.dirname(sys.executable)
        
        # Data files to extract (included via --add-data)
        data_files = ['auth.py', 'config.py', 'windows_auth.py', 'users.json']
        
        for file in data_files:
            source = os.path.join(application_path, file)
            if not os.path.exists(source):
                # Try to find in _MEIPASS (PyInstaller temp folder)
                if hasattr(sys, '_MEIPASS'):
                    source = os.path.join(sys._MEIPASS, file)
                    if os.path.exists(source):
                        import shutil
                        shutil.copy2(source, os.path.join(application_path, file))
        
        return application_path
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def run_server():
    """Run the server"""
    try:
        # Extract data files
        app_path = extract_data_files()
        os.chdir(app_path)
        
        # Add current directory to path
        if app_path not in sys.path:
            sys.path.insert(0, app_path)
        
        # Import and run server
        import server
        server.start_server()
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

def main():
    """Main function"""
    # Clear console
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("="*60)
    print("  CYBERSEC REMOTE MONITORING SERVER")
    print("="*60)
    
    # Start website in background thread
    website_thread = threading.Thread(target=open_website, daemon=True)
    website_thread.start()
    
    print("\n[+] Starting server...")
    print("[+] Loading website in background...")
    print("[+] Press Ctrl+C to stop the server\n")
    print("="*60)
    
    # Run the server
    run_server()

if __name__ == "__main__":
    main()
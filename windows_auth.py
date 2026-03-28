"""
Windows Authentication Module
Handles authentication using Windows system credentials
"""

import subprocess
import sys
import ctypes
from ctypes import wintypes
import getpass

class WindowsAuthenticator:
    """Handles Windows authentication using multiple methods"""
    
    @staticmethod
    def verify_with_powershell(username, password):
        """Method 1: Using PowerShell (Works on Windows 10/11)"""
        try:
            # PowerShell script to test credentials
            ps_script = f'''
            Add-Type -AssemblyName System.DirectoryServices.AccountManagement
            try {{
                $context = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Machine)
                $result = $context.ValidateCredentials("{username}", "{password}")
                Write-Output $result
            }} catch {{
                Write-Output "False"
            }}
            '''
            
            # Execute PowerShell and capture result
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            
            # Check if output contains "True"
            output = result.stdout.strip()
            return "True" in output
            
        except subprocess.TimeoutExpired:
            print("[!] PowerShell authentication timeout")
            return False
        except Exception as e:
            print(f"[!] PowerShell auth error: {e}")
            return False
    
    @staticmethod
    def verify_with_net_api(username, password):
        """Method 2: Using Windows NetAPI (More reliable)"""
        try:
            # Use net use command to test credentials
            # Create a temporary drive mapping attempt
            import tempfile
            import os
            
            # This is a cleaner method using Windows API
            # For now, fallback to PowerShell
            return WindowsAuthenticator.verify_with_powershell(username, password)
            
        except Exception as e:
            print(f"[!] NetAPI auth error: {e}")
            return False
    
    @staticmethod
    def verify_with_runas(username, password):
        """Method 3: Using runas command (Simple but limited)"""
        try:
            import tempfile
            import os
            
            # Create a test script
            test_script = tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False)
            test_script.write('@echo off\necho SUCCESS > nul')
            test_script.close()
            
            # Try to run with credentials
            cmd = f'runas /user:{username} /savecred "{test_script.name}"'
            
            # Note: This method requires interactive password input
            # Not suitable for programmatic use
            os.unlink(test_script.name)
            return False
            
        except Exception as e:
            print(f"[!] Runas auth error: {e}")
            return False
    
    @staticmethod
    def get_current_user():
        """Get the current Windows username"""
        try:
            return getpass.getuser()
        except:
            try:
                result = subprocess.run(['whoami'], capture_output=True, text=True)
                return result.stdout.strip().split('\\')[-1]
            except:
                return None
    
    @staticmethod
    def authenticate(username, password):
        """Main authentication method - tries all available methods"""
        
        # Check if credentials are for current user (quick check)
        current_user = WindowsAuthenticator.get_current_user()
        if current_user and username.lower() == current_user.lower():
            # For current user, we can do a quick password check
            # This is just a placeholder - actual validation happens below
            pass
        
        # Try PowerShell method first (most reliable)
        if WindowsAuthenticator.verify_with_powershell(username, password):
            return True
        
        # Try NetAPI method as fallback
        if WindowsAuthenticator.verify_with_net_api(username, password):
            return True
        
        return False

# Simple function for easy import
def authenticate_windows(username, password):
    """Simplified authentication function"""
    return WindowsAuthenticator.authenticate(username, password)

# Test function
if __name__ == "__main__":
    print("Windows Authentication Test")
    print("="*40)
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    if authenticate_windows(username, password):
        print("\n✅ Authentication SUCCESSFUL!")
    else:
        print("\n❌ Authentication FAILED!")
"""
Authentication Module - Fixed for usernames with spaces
"""

import json
import hashlib
import subprocess
import os
from config import AUTH_METHOD, DEBUG_MODE

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        # Look for users.json in server directory
        users_path = os.path.join(os.path.dirname(__file__), 'server', 'users.json')
        with open(users_path, "r") as f:
            return json.load(f)
    except:
        return {}

def authenticate_windows(username, password):
    """Windows authentication that works with usernames containing spaces"""
    try:
        # Clean username - preserve spaces
        username = username.strip()
        
        if DEBUG_MODE:
            print(f"\n[Debug] Windows Auth - Testing: '{username}'")
        
        # PowerShell script with proper handling of spaces
        ps_script = f'''
        Add-Type -AssemblyName System.DirectoryServices.AccountManagement
        $context = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Machine)
        $result = $context.ValidateCredentials('{username}', '{password}')
        Write-Output $result
        '''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if DEBUG_MODE:
            print(f"[Debug] PowerShell output: '{result.stdout.strip()}'")
        
        if "True" in result.stdout:
            return True
            
        return False
        
    except Exception as e:
        if DEBUG_MODE:
            print(f"[Debug] Windows auth error: {e}")
        return False

def authenticate_json(username, password):
    """JSON fallback authentication"""
    users = load_users()
    hashed = hash_password(password)
    
    if DEBUG_MODE:
        print(f"[Debug] JSON Auth - Checking '{username}'")
    
    return username in users and users[username] == hashed

def authenticate(username, password):
    """Main authentication function"""
    
    if DEBUG_MODE:
        print("\n" + "="*50)
        print(f"[Debug] Authentication Attempt")
        print(f"[Debug] Username: '{username}'")
        print(f"[Debug] Auth Method: {AUTH_METHOD}")
        print("="*50)
    
    # Try Windows authentication
    if AUTH_METHOD == "windows":
        if authenticate_windows(username, password):
            if DEBUG_MODE:
                print("[Debug] ✅ SUCCESS - Windows authentication")
            return True
        else:
            if DEBUG_MODE:
                print("[Debug] ❌ FAILED - Windows authentication")
    
    # Try JSON authentication as fallback
    if authenticate_json(username, password):
        if DEBUG_MODE:
            print("[Debug] ✅ SUCCESS - JSON authentication")
        return True
    
    if DEBUG_MODE:
        print("[Debug] ❌ FAILED - All authentication methods")
    
    return False
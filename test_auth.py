import subprocess
import getpass

def test_windows_auth():
    print("Testing Windows Authentication")
    print("="*40)
    
    # Get actual Windows username
    try:
        actual_user = subprocess.getoutput('whoami').split('\\')[-1].strip()
        print(f"Your actual Windows username: {actual_user}")
    except:
        actual_user = None
    
    username = input("Enter username to test: ")
    password = getpass.getpass("Enter password: ")
    
    # Test authentication
    ps_script = f'''
    Add-Type -AssemblyName System.DirectoryServices.AccountManagement
    $context = New-Object System.DirectoryServices.AccountManagement.PrincipalContext([System.DirectoryServices.AccountManagement.ContextType]::Machine)
    $context.ValidateCredentials("{username}", "{password}")
    '''
    
    result = subprocess.run(
        ['powershell', '-Command', ps_script],
        capture_output=True,
        text=True
    )
    
    if "True" in result.stdout:
        print("\n✅ Authentication SUCCESSFUL!")
        print(f"You can login with username: {username}")
    else:
        print("\n❌ Authentication FAILED!")
        print("Possible reasons:")
        print("1. Wrong username or password")
        print("2. Using Microsoft account instead of local account")
        print("3. Account type not supported")

if __name__ == "__main__":
    test_windows_auth()
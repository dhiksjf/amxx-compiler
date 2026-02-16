#!/usr/bin/env python3
"""
🚀 ULTIMATE GITHUB AUTO-PUSHER FOR PYDROID3
============================================
Automatically creates GitHub repository and pushes your files
Designed specifically for Pydroid3 on Android

Author: Auto-Deploy System
Version: 3.0.0
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

# ============================================================================
# CONFIGURATION - EDIT THESE VALUES
# ============================================================================

# GitHub Personal Access Token (REQUIRED)
# Get it from: https://github.com/settings/tokens
# Select: repo, workflow, write:packages
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"

# GitHub Username (REQUIRED)
GITHUB_USERNAME = "YOUR_USERNAME_HERE"

# Repository Configuration
REPO_NAME = "amxx-compiler"  # Name of repository to create
REPO_DESCRIPTION = "Professional AMX Mod X Compiler API"
REPO_PRIVATE = False  # True for private, False for public

# Project Directory (where your files are)
# Leave as "." for current directory
PROJECT_DIR = "."

# Files/Folders to exclude from pushing
EXCLUDE = [
    ".git",
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    "venv",
    "env",
    ".env",
    "node_modules"
]

# ============================================================================
# COLORS FOR TERMINAL OUTPUT
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_header(text):
    """Print styled header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")

def run_command(command, description="", check=True):
    """Run shell command and handle output"""
    if description:
        print_info(f"{description}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        
        if result.returncode == 0:
            if description:
                print_success(f"{description} - Done")
            return True, result.stdout
        else:
            if description:
                print_error(f"{description} - Failed")
            print_error(f"Error: {result.stderr}")
            return False, result.stderr
            
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        return False, str(e)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False, str(e)

def check_git_installed():
    """Check if git is installed"""
    success, output = run_command("git --version", "", check=False)
    return success

def install_git_termux():
    """Install git in Termux (Pydroid3)"""
    print_warning("Git not found. Attempting to install via Termux...")
    print_info("This requires Termux to be installed.")
    
    commands = [
        "pkg update -y",
        "pkg install git -y"
    ]
    
    for cmd in commands:
        success, _ = run_command(cmd, f"Running: {cmd}")
        if not success:
            return False
    
    return True

def validate_config():
    """Validate configuration"""
    errors = []
    
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN_HERE" or not GITHUB_TOKEN:
        errors.append("GitHub token is not set")
    
    if GITHUB_USERNAME == "YOUR_USERNAME_HERE" or not GITHUB_USERNAME:
        errors.append("GitHub username is not set")
    
    if not REPO_NAME:
        errors.append("Repository name is not set")
    
    if errors:
        print_error("Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        print()
        print_info("Please edit the script and set:")
        print(f"  {Colors.YELLOW}GITHUB_TOKEN{Colors.END} - Your GitHub personal access token")
        print(f"  {Colors.YELLOW}GITHUB_USERNAME{Colors.END} - Your GitHub username")
        print()
        print_info("Get token from: https://github.com/settings/tokens")
        print_info("Required scopes: repo, workflow, write:packages")
        return False
    
    return True

def create_github_repo():
    """Create GitHub repository using API"""
    print_info(f"Creating repository '{REPO_NAME}'...")
    
    # Prepare API request
    api_url = "https://api.github.com/user/repos"
    
    data = {
        "name": REPO_NAME,
        "description": REPO_DESCRIPTION,
        "private": REPO_PRIVATE,
        "auto_init": False
    }
    
    # Use curl for API request (more reliable on Android)
    curl_command = f"""
    curl -X POST \
      -H "Authorization: token {GITHUB_TOKEN}" \
      -H "Accept: application/vnd.github.v3+json" \
      -d '{json.dumps(data)}' \
      {api_url}
    """
    
    success, output = run_command(curl_command, "", check=False)
    
    if success and "full_name" in output:
        print_success(f"Repository created: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
        return True
    elif "already exists" in output.lower():
        print_warning(f"Repository '{REPO_NAME}' already exists")
        print_info("Will push to existing repository")
        return True
    else:
        print_error("Failed to create repository")
        print_error(f"Response: {output}")
        return False

def init_git_repo():
    """Initialize git repository"""
    os.chdir(PROJECT_DIR)
    
    # Check if already initialized
    if os.path.exists(".git"):
        print_info("Git repository already initialized")
        return True
    
    success, _ = run_command("git init", "Initializing git repository")
    return success

def configure_git():
    """Configure git user"""
    print_info("Configuring git user...")
    
    commands = [
        f'git config user.name "{GITHUB_USERNAME}"',
        f'git config user.email "{GITHUB_USERNAME}@users.noreply.github.com"'
    ]
    
    for cmd in commands:
        success, _ = run_command(cmd, "", check=False)
        if not success:
            print_warning("Could not configure git user (continuing anyway)")
    
    return True

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
*.egg-info/

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Temp
temp_builds/
*.log
*.tmp
.env
"""
    
    try:
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print_success("Created .gitignore")
        return True
    except Exception as e:
        print_warning(f"Could not create .gitignore: {e}")
        return True  # Not critical

def add_files():
    """Add files to git"""
    success, _ = run_command("git add .", "Adding files to git")
    
    if success:
        # Show what was added
        success2, output = run_command("git status --short", "", check=False)
        if success2 and output:
            print_info("Files staged for commit:")
            for line in output.strip().split('\n'):
                if line:
                    print(f"  {line}")
    
    return success

def commit_files():
    """Commit files"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Auto-commit from Pydroid3 - {timestamp}"
    
    success, _ = run_command(
        f'git commit -m "{commit_message}"',
        "Committing files"
    )
    return success

def add_remote():
    """Add GitHub remote"""
    # Remove existing remote if exists
    run_command("git remote remove origin", "", check=False)
    
    # Use HTTPS with token authentication
    remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
    
    success, _ = run_command(
        f'git remote add origin {remote_url}',
        "Adding GitHub remote"
    )
    return success

def push_to_github():
    """Push to GitHub"""
    # Set branch to main
    run_command("git branch -M main", "Setting branch to main")
    
    # Push to GitHub
    success, output = run_command(
        "git push -u origin main --force",
        "Pushing to GitHub"
    )
    
    return success

def display_summary():
    """Display final summary"""
    print_header("🎉 DEPLOYMENT COMPLETE!")
    
    print(f"{Colors.GREEN}✓{Colors.END} Repository: {Colors.BOLD}https://github.com/{GITHUB_USERNAME}/{REPO_NAME}{Colors.END}")
    print(f"{Colors.GREEN}✓{Colors.END} Branch: {Colors.BOLD}main{Colors.END}")
    print(f"{Colors.GREEN}✓{Colors.END} Status: {Colors.BOLD}Successfully pushed{Colors.END}")
    
    print(f"\n{Colors.CYAN}📂 View your repository:{Colors.END}")
    print(f"   https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
    
    print(f"\n{Colors.CYAN}🚀 Next Steps:{Colors.END}")
    print("   1. Go to Koyeb.com")
    print("   2. Create new service")
    print("   3. Connect GitHub")
    print(f"   4. Select: {GITHUB_USERNAME}/{REPO_NAME}")
    print("   5. Deploy with Dockerfile")
    print("   6. Your app will be live in 2-3 minutes!")
    
    print(f"\n{Colors.GREEN}✨ All done! Happy coding!{Colors.END}\n")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main execution function"""
    
    # Print banner
    print_header("🚀 GITHUB AUTO-PUSHER FOR PYDROID3")
    
    print(f"{Colors.BOLD}Configuration:{Colors.END}")
    print(f"  Username: {Colors.CYAN}{GITHUB_USERNAME}{Colors.END}")
    print(f"  Repository: {Colors.CYAN}{REPO_NAME}{Colors.END}")
    print(f"  Private: {Colors.CYAN}{REPO_PRIVATE}{Colors.END}")
    print(f"  Directory: {Colors.CYAN}{os.path.abspath(PROJECT_DIR)}{Colors.END}")
    print()
    
    # Step 1: Validate configuration
    print_header("Step 1: Validating Configuration")
    if not validate_config():
        sys.exit(1)
    print_success("Configuration validated")
    
    # Step 2: Check/Install git
    print_header("Step 2: Checking Git Installation")
    if not check_git_installed():
        print_warning("Git not found")
        if not install_git_termux():
            print_error("Could not install git")
            print_info("Please install git manually:")
            print("  1. Install Termux from Play Store")
            print("  2. Open Termux and run: pkg install git")
            print("  3. Run this script again")
            sys.exit(1)
    print_success("Git is available")
    
    # Step 3: Create GitHub repository
    print_header("Step 3: Creating GitHub Repository")
    if not create_github_repo():
        print_error("Failed to create repository")
        sys.exit(1)
    
    # Step 4: Initialize git
    print_header("Step 4: Initializing Git Repository")
    if not init_git_repo():
        sys.exit(1)
    
    # Step 5: Configure git
    print_header("Step 5: Configuring Git")
    configure_git()
    
    # Step 6: Create .gitignore
    print_header("Step 6: Creating .gitignore")
    create_gitignore()
    
    # Step 7: Add files
    print_header("Step 7: Adding Files")
    if not add_files():
        sys.exit(1)
    
    # Step 8: Commit
    print_header("Step 8: Committing Changes")
    if not commit_files():
        # Check if there are changes to commit
        success, output = run_command("git status --porcelain", "", check=False)
        if not output.strip():
            print_warning("No changes to commit")
        else:
            sys.exit(1)
    
    # Step 9: Add remote
    print_header("Step 9: Adding GitHub Remote")
    if not add_remote():
        sys.exit(1)
    
    # Step 10: Push to GitHub
    print_header("Step 10: Pushing to GitHub")
    if not push_to_github():
        print_error("Failed to push to GitHub")
        print_info("Check your token permissions and try again")
        sys.exit(1)
    
    # Step 11: Display summary
    display_summary()

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠ Operation cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}✗ Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

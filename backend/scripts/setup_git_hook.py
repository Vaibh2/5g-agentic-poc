#!/usr/bin/env python3
"""
Git Hook Setup Script

Run this script in your VSCode project folder where your 5G config files are.
It will create a post-commit hook that triggers deployment when you commit code.

Usage:
    python3 setup_git_hook.py
"""

import os
import sys
import json
import subprocess

BACKEND_URL = "http://localhost:8000"
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__)).replace("/scripts", "")


HOOK_CONTENT = '''#!/bin/bash

# 5G Agentic POC - Post-commit Hook
# Triggers deployment when code is committed

# Get the root of the git repo
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$REPO_ROOT" ]; then
    echo "Not a git repository"
    exit 0
fi

# Find YAML config files that were changed
# Handle first commit case (no HEAD~1) by comparing against empty tree
if git rev-parse HEAD~1 >/dev/null 2>&1; then
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep -E "\\.yaml$|\\.yml$" || echo "")
else
    CHANGED_FILES=$(git diff --name-only 4b825dc745cb65b9cc74247c4e6a2c9665131b60 HEAD 2>/dev/null | grep -E "\\.yaml$|\\.yml$" || echo "")
fi

if [ -z "$CHANGED_FILES" ]; then
    echo "No YAML files changed, skipping deployment trigger"
    exit 0
fi

echo "Detected YAML file changes: $CHANGED_FILES"

# Convert newlines to | separator for safe JSON passing
FILES_ESCAPED=$(echo "$CHANGED_FILES" | tr '\n' '|' | sed 's/|$//')

# Use Python to send webhook - handles JSON properly
python -c "
import json
import urllib.request
import urllib.error
import sys

payload = json.dumps({
    'files': '$FILES_ESCAPED',
    'repo_path': r'$REPO_ROOT'
})

print('Sending payload:', payload)

try:
    req = urllib.request.Request(
        'http://localhost:8000/webhook/git-push',
        data=payload.encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        result = response.read().decode()
        print('Backend response:', result)
except urllib.error.URLError as e:
    print('ERROR: Could not connect to backend:', e.reason)
    sys.exit(1)
except Exception as e:
    print('ERROR:', str(e))
    sys.exit(1)

print('Deployment triggered!')
"
'''


def setup_hook():
    # Check if we're in a git repo
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd="."
        )
        if result.returncode != 0:
            print("❌ Error: Not in a git repository. Please run this in your project folder.")
            print("   Run: git init")
            sys.exit(1)
        
        repo_root = result.stdout.strip()
        print(f"✅ Git repository found: {repo_root}")
        
    except FileNotFoundError:
        print("❌ Error: Git not installed. Please install git first.")
        sys.exit(1)
    
    hook_path = os.path.join(repo_root, ".git", "hooks", "post-commit")
    
    # Check if hook already exists
    if os.path.exists(hook_path):
        response = input("⚠️  post-commit hook already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # Create the hook
    hook_content = HOOK_CONTENT.replace("{BACKEND_URL}", BACKEND_URL)
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make it executable
    os.chmod(hook_path, 0o755)
    
    print(f"✅ Git hook created at: {hook_path}")
    print("")
    print("📝 Next steps:")
    print("   1. Make sure backend is running: cd backend && uvicorn main:app --reload")
    print("   2. Make sure frontend is running: cd frontend && streamlit run app.py")
    print("   3. Add your YAML config files to git and commit")
    print("   4. Watch the Workflows page in the frontend!")


if __name__ == "__main__":
    print("=" * 50)
    print("  5G Agentic POC - Git Hook Setup")
    print("=" * 50)
    print("")
    setup_hook()
#!/usr/bin/env python3
"""
Security Audit Script for Hexagon API
Run this script to check your project's security status
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔍 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print("❌ FAILED")
            if result.stderr.strip():
                print("Error:", result.stderr)
            if result.stdout.strip():
                print("Output:", result.stdout)
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def check_file_security():
    """Check for security issues in files"""
    print(f"\n🔍 Checking File Security")
    print("-" * 50)
    
    # Check .env files are not tracked
    env_files = [".env", ".env.local", ".env.docker", ".env.production"]
    tracked_env = []
    
    try:
        result = subprocess.run("git ls-files", shell=True, capture_output=True, text=True)
        tracked_files = result.stdout.splitlines()
        
        for env_file in env_files:
            if env_file in tracked_files:
                tracked_env.append(env_file)
        
        if tracked_env:
            print(f"❌ SECURITY ISSUE: These .env files are tracked in Git: {tracked_env}")
            print("   Run: git rm --cached " + " ".join(tracked_env))
            return False
        else:
            print("✅ No .env files tracked in Git")
            return True
            
    except Exception as e:
        print(f"❌ ERROR checking Git files: {e}")
        return False

def main():
    print("🛡️  HEXAGON API SECURITY AUDIT")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    results = []
    
    # 1. Check for vulnerable dependencies
    results.append(run_command(
        ".venv/bin/pip-audit --desc",
        "Checking for vulnerable dependencies"
    ))
    
    # 2. Check file security
    results.append(check_file_security())
    
    # 3. Check if old vulnerable packages are gone
    results.append(run_command(
        ".venv/bin/pip show python-jose ecdsa",
        "Checking if vulnerable packages are removed (should fail)"
    ) == False)  # We want this to fail (packages should be gone)
    
    # 4. Test secure imports
    results.append(run_command(
        '.venv/bin/python -c "from app.auth_secure import get_current_user; print(\\"✅ Secure auth import successful\\")"',
        "Testing secure authentication import"
    ))
    
    # 5. Check gitignore
    results.append(run_command(
        'grep -q "^\\.env$" .gitignore && echo "✅ .env files properly ignored"',
        "Checking .gitignore configuration"
    ))
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 SECURITY AUDIT SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("🛡️  Your application is secure!")
    else:
        print(f"❌ SOME CHECKS FAILED ({passed}/{total})")
        print("⚠️  Please address the issues above")
        
    print("\n🔒 Security Best Practices:")
    print("- Keep dependencies updated")
    print("- Never commit .env files")
    print("- Use environment variables for secrets")
    print("- Regularly run security audits")
    print("- Monitor security advisories")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

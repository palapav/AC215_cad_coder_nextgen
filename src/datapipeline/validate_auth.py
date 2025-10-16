#!/usr/bin/env python3
"""
Lightweight authentication validator for Docker containers.
Checks required environment variables and files before pipeline runs.
No external dependencies beyond Python standard library.
"""

import os
import sys
import json

def check_env_vars():
    """Check required environment variables."""
    print("\n" + "="*60)
    print("🔍 VALIDATING AUTHENTICATION")
    print("="*60 + "\n")
    
    required_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": "Google Cloud service account key path",
        "GOOGLE_CLOUD_PROJECT": "Google Cloud project ID",
        "GCS_BUCKET": "GCS bucket name",
        "HF_TOKEN": "HuggingFace authentication token"
    }
    
    missing = []
    invalid = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"  ❌ {var}: Not set ({description})")
        elif var == "HF_TOKEN" and value.startswith("hf_xxx"):
            invalid.append(f"  ❌ {var}: Still has placeholder value")
        elif value.startswith("your-"):
            invalid.append(f"  ❌ {var}: Still has placeholder value")
        else:
            print(f"  ✅ {var}: Set")
    
    if missing or invalid:
        print("\n❌ VALIDATION FAILED\n")
        if missing:
            print("Missing variables:")
            for m in missing:
                print(m)
        if invalid:
            print("\nInvalid values:")
            for i in invalid:
                print(i)
        print("\n💡 Fix .env file and try again")
        return False
    
    print("\n✅ All environment variables are set")
    return True


def check_key_file():
    """Check if Google Cloud key file exists and is valid JSON."""
    key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/key.json")
    
    print(f"\n🔑 Checking key file: {key_path}")
    
    if not os.path.exists(key_path):
        print(f"  ❌ Key file not found: {key_path}")
        print("  💡 Ensure key.json is mounted in docker-compose")
        return False
    
    print(f"  ✅ Key file exists")
    
    # Validate JSON
    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)
        
        required_fields = ["type", "project_id", "private_key", "client_email"]
        for field in required_fields:
            if field not in key_data:
                print(f"  ❌ Invalid key file: missing '{field}'")
                return False
        
        print(f"  ✅ Key file valid")
        print(f"  ℹ️  Service account: {key_data['client_email']}")
        return True
        
    except json.JSONDecodeError:
        print(f"  ❌ Key file is not valid JSON")
        return False
    except Exception as e:
        print(f"  ❌ Error reading key file: {e}")
        return False


def main():
    """Run all validation checks."""
    
    checks = [
        check_env_vars,
        check_key_file,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ VALIDATION PASSED - PROCEEDING WITH PIPELINE")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ VALIDATION FAILED - FIX ERRORS ABOVE")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

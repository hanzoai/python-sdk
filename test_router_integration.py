#!/usr/bin/env python
"""Test hanzo router integration."""

import sys
import os

# Add the site-packages to path if needed
site_packages = "/opt/homebrew/lib/python3.12/site-packages"
if site_packages not in sys.path:
    sys.path.insert(0, site_packages)

print("Testing hanzo router integration...")
print(f"Python path: {sys.path[:3]}...")

try:
    # Try importing hanzo
    import hanzo
    print(f"✓ Imported hanzo version {hanzo.__version__}")
    
    # Check router
    if hasattr(hanzo, 'router'):
        print("✓ hanzo.router is available")
        
        # Test router functions
        if hasattr(hanzo.router, 'completion'):
            print("✓ hanzo.router.completion is available")
        else:
            print("✗ hanzo.router.completion is not available")
            
        if hasattr(hanzo.router, 'Router'):
            print("✓ hanzo.router.Router is available")
        else:
            print("✗ hanzo.router.Router is not available")
    else:
        print("✗ hanzo.router is not available")
        
    # Try direct import
    try:
        from hanzo import router
        print("✓ Direct import 'from hanzo import router' works")
    except ImportError as e:
        print(f"✗ Direct import failed: {e}")
        
except ImportError as e:
    print(f"✗ Failed to import hanzo: {e}")
    
    # Try to debug the issue
    hanzo_path = os.path.join(site_packages, "hanzo")
    if os.path.exists(hanzo_path):
        print(f"Hanzo directory exists at: {hanzo_path}")
        print(f"Contents: {os.listdir(hanzo_path)}")
    else:
        print(f"Hanzo directory does not exist at: {hanzo_path}")
        
print("\nTest complete!")
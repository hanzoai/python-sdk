#!/usr/bin/env python3
"""Setup script for sqlite-vec extension.

Downloads and installs sqlite-vec for vector search capabilities.
"""

import os
import sys
import urllib.request
import platform
import sqlite3
from pathlib import Path


def get_sqlite_vec_url():
    """Get the appropriate sqlite-vec download URL for this platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map platform to sqlite-vec release names
    if system == "darwin":
        if machine in ("x86_64", "amd64"):
            return "https://github.com/asg017/sqlite-vec/releases/latest/download/sqlite-vec-v0.1.0-alpha.7-macos-x86_64.tar.gz"
        elif machine in ("arm64", "aarch64"):
            return "https://github.com/asg017/sqlite-vec/releases/latest/download/sqlite-vec-v0.1.0-alpha.7-macos-aarch64.tar.gz"
    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            return "https://github.com/asg017/sqlite-vec/releases/latest/download/sqlite-vec-v0.1.0-alpha.7-linux-x86_64.tar.gz"
        elif machine in ("arm64", "aarch64"):
            return "https://github.com/asg017/sqlite-vec/releases/latest/download/sqlite-vec-v0.1.0-alpha.7-linux-aarch64.tar.gz"
    elif system == "windows":
        return "https://github.com/asg017/sqlite-vec/releases/latest/download/sqlite-vec-v0.1.0-alpha.7-windows-x86_64.zip"
    
    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def download_sqlite_vec():
    """Download and extract sqlite-vec extension."""
    try:
        url = get_sqlite_vec_url()
        print(f"Downloading sqlite-vec from: {url}")
        
        # Create extension directory
        ext_dir = Path(__file__).parent / "extensions"
        ext_dir.mkdir(exist_ok=True)
        
        # Download
        filename = url.split("/")[-1]
        local_path = ext_dir / filename
        
        urllib.request.urlretrieve(url, local_path)
        print(f"Downloaded: {local_path}")
        
        # Extract
        if filename.endswith(".tar.gz"):
            import tarfile
            with tarfile.open(local_path, 'r:gz') as tar:
                tar.extractall(ext_dir)
        elif filename.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(local_path, 'r') as zip_ref:
                zip_ref.extractall(ext_dir)
        
        # Find the extension file
        for ext_file in ext_dir.rglob("vec0.*"):
            if ext_file.suffix in (".so", ".dll", ".dylib"):
                print(f"Found extension: {ext_file}")
                return ext_file
                
        raise RuntimeError("Could not find vec0 extension after extraction")
        
    except Exception as e:
        print(f"Failed to download sqlite-vec: {e}")
        return None


def test_sqlite_vec(extension_path):
    """Test if sqlite-vec extension works."""
    try:
        conn = sqlite3.connect(":memory:")
        conn.enable_load_extension(True)
        conn.load_extension(str(extension_path))
        
        # Test basic functionality
        conn.execute("CREATE VIRTUAL TABLE test_vec USING vec0(embedding float[3])")
        conn.execute("INSERT INTO test_vec (embedding) VALUES ('[1,2,3]')")
        result = conn.execute("SELECT * FROM test_vec").fetchone()
        
        conn.close()
        
        if result:
            print("✓ sqlite-vec extension is working correctly")
            return True
        else:
            print("✗ sqlite-vec extension test failed")
            return False
            
    except Exception as e:
        print(f"✗ sqlite-vec extension test failed: {e}")
        return False


def install_sqlite_vec():
    """Install sqlite-vec extension."""
    print("Setting up sqlite-vec extension for vector search...")
    
    # Check if already available
    try:
        conn = sqlite3.connect(":memory:")
        conn.enable_load_extension(True)
        conn.load_extension("vec0")
        conn.close()
        print("✓ sqlite-vec extension is already available")
        return True
    except Exception:
        pass  # Extension not available, will download
    
    # Download and install
    extension_path = download_sqlite_vec()
    if extension_path and test_sqlite_vec(extension_path):
        # Create symlink or copy to standard location
        try:
            import shutil
            target_dir = Path.home() / ".hanzo" / "extensions"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / extension_path.name
            
            shutil.copy2(extension_path, target_path)
            print(f"✓ Installed sqlite-vec to: {target_path}")
            
            # Add to environment
            print("\nTo use sqlite-vec, add this to your environment:")
            print(f"export SQLITE_VEC_PATH={target_path}")
            
            return True
        except Exception as e:
            print(f"Warning: Failed to install extension: {e}")
            print(f"You can manually use: {extension_path}")
            return False
    else:
        print("✗ Failed to install sqlite-vec extension")
        print("Vector search will not be available")
        return False


if __name__ == "__main__":
    success = install_sqlite_vec()
    sys.exit(0 if success else 1)
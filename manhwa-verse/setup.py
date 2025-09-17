#!/usr/bin/env python3
"""
ManhwaVerse Setup Script
========================

This script helps set up the ManhwaVerse project by installing dependencies
and providing instructions for running the application.

Author: ManhwaVerse Development Team
Date: 2025
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required Python packages."""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = ['assets/images', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🎌 ManhwaVerse Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\nTo start the application:")
    print("1. Start the Flask API server:")
    print("   python app.py")
    print("\n2. Open your web browser and navigate to:")
    print("   http://127.0.0.1:5000 (API)")
    print("   file:///path/to/manhwa-verse/index.html (Frontend)")
    print("\n3. Or simply open index.html in your browser")
    print("\nThe API will be available at http://127.0.0.1:5000")
    print("The frontend will automatically connect to the API")
    print("=" * 60)

if __name__ == "__main__":
    main()

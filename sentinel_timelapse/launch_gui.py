#!/usr/bin/env python3
"""
Launch GUI for Sentinel-2 Time-Lapse Analysis
Easy-to-use interface with AI-powered change detection
"""

import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        'PyQt5',
        'numpy',
        'rasterio',
        'opencv-python',
        'pillow',
        'scikit-learn',
        'scikit-image',
        'joblib',
        'requests'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"  - {pkg}")
        
        print("\n📦 Installing missing packages...")
        for pkg in missing:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
        print("✅ Dependencies installed!")
    else:
        print("✅ All dependencies available!")

def launch_gui(mode='advanced'):
    """Launch the GUI application"""
    
    try:
        if mode == 'advanced':
            print("🚀 Launching Advanced AI-Powered GUI...")
            from advanced_gui_app import main
        else:
            print("🚀 Launching Standard GUI...")
            from gui_timelapse_app import main
        
        main()
    
    except Exception as e:
        print(f"❌ Error launching GUI: {e}")
        sys.exit(1)

def main():
    """Main launcher"""
    print("\n" + "="*60)
    print("  🛰️  SENTINEL-2 TIME-LAPSE ANALYSIS SYSTEM")
    print("="*60 + "\n")
    
    # Check dependencies
    print("📋 Checking dependencies...")
    try:
        check_dependencies()
    except Exception as e:
        print(f"⚠️  Warning: Could not verify all dependencies: {e}")
    
    print("\n" + "="*60)
    print("  SELECT MODE")
    print("="*60)
    print("1. Advanced (AI-Powered, Recommended)")
    print("2. Standard (Basic Features)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        launch_gui('advanced')
    elif choice == '2':
        launch_gui('standard')
    elif choice == '3':
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice!")
        main()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick Start Script for BCI Music System

This script provides easy startup options for different system configurations.
"""

import sys
import subprocess
from pathlib import Path


def main():
    print("🎵 BCI Music Generator - Quick Start")
    print("=" * 50)
    
    print("\nAvailable startup modes:")
    print("1. Full System (with EEG hardware)")
    print("2. Demo Mode (no hardware required)")
    print("3. Audio Only (test audio engine)")
    print("4. UI Only (frontend development)")
    print("5. Individual Components")
    
    choice = input("\nSelect mode (1-5): ").strip()
    
    if choice == "1":
        # Full system with hardware
        serial_port = input("Enter EEG serial port (e.g., COM3): ").strip()
        model_path = input("Enter model path (.joblib file): ").strip()
        
        if not serial_port or not model_path:
            print("❌ Serial port and model path required")
            sys.exit(1)
            
        cmd = [sys.executable, "main.py", "--mode", "full", 
               "--serial-port", serial_port, "--model-path", model_path]
        
    elif choice == "2":
        # Demo mode - no hardware
        print("🎮 Starting demo mode (no EEG hardware required)")
        print("   Use the UI's 'Dev Bypass' to test the system")
        cmd = [sys.executable, "main.py", "--mode", "full"]
        
    elif choice == "3":
        # Audio only
        print("🔊 Starting audio engine only")
        cmd = [sys.executable, "main.py", "--mode", "audio"]
        
    elif choice == "4":
        # UI only
        print("🖥️  Starting UI only")
        cmd = [sys.executable, "main.py", "--mode", "ui"]
        
    elif choice == "5":
        # Individual components
        print("\nIndividual components:")
        print("a. Real-time Classifier")
        print("b. Music Controller")
        print("c. Audio Bridge")
        print("d. Audio Engine")
        print("e. UI")
        
        component = input("Select component (a-e): ").strip().lower()
        
        if component == "a":
            serial_port = input("Enter EEG serial port: ").strip()
            model_path = input("Enter model path: ").strip()
            if not serial_port or not model_path:
                print("❌ Serial port and model path required")
                sys.exit(1)
            cmd = [sys.executable, "main.py", "--mode", "classifier",
                   "--serial-port", serial_port, "--model-path", model_path]
        elif component == "b":
            cmd = [sys.executable, "main.py", "--mode", "controller"]
        elif component == "c":
            cmd = [sys.executable, "main.py", "--mode", "bridge"]
        elif component == "d":
            cmd = [sys.executable, "main.py", "--mode", "audio"]
        elif component == "e":
            cmd = [sys.executable, "main.py", "--mode", "ui"]
        else:
            print("❌ Invalid selection")
            sys.exit(1)
    else:
        print("❌ Invalid selection")
        sys.exit(1)
    
    print(f"\n🚀 Running: {' '.join(cmd)}")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()


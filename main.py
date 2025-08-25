#!/usr/bin/env python3
"""
BCI Music Generator - Main Entry Point

This is the main entry point for the BCI Music Generator system.
It coordinates the core BCI processing, audio generation, and UI components.
"""

import sys
import os
import argparse
import subprocess
import time
import threading
from pathlib import Path

# Add project directories to path for imports
project_root = Path(__file__).parent
sys.path.extend([
    str(project_root / "core"),
    str(project_root / "audio"), 
    str(project_root / "data"),
    str(project_root / "config")
])


def run_classifier(serial_port, model_path):
    """Run the real-time classifier"""
    from core.real_time_classifier import main as run_rt_classifier
    import sys
    
    # Set up arguments for classifier
    sys.argv = [
        'real_time_classifier.py',
        '--serial-port', serial_port,
        '--model-path', model_path,
        '--enable-osc',
        '--send-prob',
        '--osc-ip', '127.0.0.1',
        '--osc-port', '9000'
    ]
    run_rt_classifier()


def run_music_controller():
    """Run the music controller"""
    from core.music_controller import main as controller_main
    controller_main()


def run_audio_bridge():
    """Run the audio bridge"""
    from core.audio_bridge import main as bridge_main
    bridge_main()


def run_ui():
    """Run the UI"""
    ui_dir = project_root / "ui"
    if not (ui_dir / "node_modules").exists():
        print("Installing UI dependencies...")
        subprocess.run(["npm", "install"], cwd=ui_dir, check=True)
    
    print("Starting UI...")
    subprocess.run(["npm", "start"], cwd=ui_dir)


def run_audio_engine():
    """Run the audio engine"""
    from audio.audio_engine import main as audio_main
    audio_main()


def run_full_system(args):
    """Run the complete integrated system"""
    print("🚀 Starting Complete BCI Music System...")
    
    processes = []
    threads = []
    
    try:
        # Start audio engine first
        print("🔊 Starting audio engine...")
        audio_thread = threading.Thread(target=run_audio_engine, daemon=True)
        audio_thread.start()
        threads.append(audio_thread)
        time.sleep(3)  # Give audio engine time to start
        
        # Start music controller in a thread
        print("🎵 Starting music controller...")
        controller_thread = threading.Thread(target=run_music_controller, daemon=True)
        controller_thread.start()
        threads.append(controller_thread)
        time.sleep(2)  # Give controller time to start
        
        # Start audio bridge in a thread
        print("🔗 Starting audio bridge...")
        bridge_thread = threading.Thread(target=run_audio_bridge, daemon=True)
        bridge_thread.start()
        threads.append(bridge_thread)
        time.sleep(2)  # Give bridge time to start
        
        # Start classifier if model and serial port provided
        if args.model_path and args.serial_port:
            print("🧠 Starting real-time classifier...")
            classifier_thread = threading.Thread(
                target=run_classifier, 
                args=(args.serial_port, args.model_path),
                daemon=True
            )
            classifier_thread.start()
            threads.append(classifier_thread)
            time.sleep(2)
        else:
            print("⚠️  No model or serial port specified. Classifier not started.")
            print("   You can test the system using the UI's Dev Bypass mode.")
        
        print("\n✅ All backend components started!")
        print("🖥️  Starting UI...")
        print("\n📋 System Architecture:")
        print("   🧠 Real-time Classifier → 🎵 Music Controller → 🔗 Audio Bridge → 🔊 Audio Engine")
        print("   📡 All components communicate via OSC messages")
        print("   🖥️  UI monitors and controls all components")
        
        # Start UI (this blocks until UI is closed)
        run_ui()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
    finally:
        # Clean shutdown
        for process in processes:
            process.terminate()


def main():
    """Main entry point for the BCI Music Generator"""
    parser = argparse.ArgumentParser(description='BCI Music Generator')
    parser.add_argument('--mode', choices=['full', 'controller', 'classifier', 'bridge', 'audio', 'ui', 'data'], 
                       default='full',
                       help='Run mode: full (default), controller, classifier, bridge, audio, ui, or data processing')
    parser.add_argument('--config', type=str, default='config/presets.py',
                       help='Configuration file path')
    parser.add_argument('--serial-port', type=str, 
                       help='Serial port for EEG device (e.g., COM3)')
    parser.add_argument('--model-path', type=str,
                       help='Path to trained classifier model (.joblib)')
    
    args = parser.parse_args()
    
    print("🎵 BCI Music Generator Starting...")
    print(f"Mode: {args.mode}")
    
    if args.mode == 'full':
        run_full_system(args)
    elif args.mode == 'controller':
        print("Starting music controller...")
        run_music_controller()
    elif args.mode == 'classifier':
        if not args.serial_port or not args.model_path:
            print("❌ Serial port and model path required for classifier mode")
            sys.exit(1)
        print("Starting real-time classifier...")
        run_classifier(args.serial_port, args.model_path)
    elif args.mode == 'bridge':
        print("Starting audio bridge...")
        run_audio_bridge()
    elif args.mode == 'audio':
        print("Starting audio engine...")
        run_audio_engine()
    elif args.mode == 'ui':
        print("Starting UI...")
        run_ui()
    elif args.mode == 'data':
        print("Starting data processing mode...")
        from data.data_acquisition import main as data_main
        data_main()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


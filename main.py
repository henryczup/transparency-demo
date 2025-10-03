"""
Main entry point for synchronized OAK-D camera and FT232H GPIO recording
"""
import yaml
import argparse
from pathlib import Path
from src.synchronized_recorder import SynchronizedRecorder
from src.postprocessor import DataPostProcessor


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Synchronized OAK-D Camera and FT232H GPIO Recording System"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--record-only',
        action='store_true',
        help='Only record, skip post-processing'
    )
    parser.add_argument(
        '--process-only',
        type=str,
        metavar='SESSION_DIR',
        help='Only post-process existing session (provide session directory path)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    if args.process_only:
        # Post-process only mode
        print(f"Post-processing session: {args.process_only}")
        processor = DataPostProcessor(args.process_only, config)
        processor.process_all()
    else:
        # Recording mode (with optional post-processing)
        print("=" * 60)
        print("SYNCHRONIZED RECORDING SYSTEM")
        print("=" * 60)
        print(f"Configuration loaded from: {args.config}")
        print(f"Recording duration: {config['recording']['duration_seconds']} seconds")
        print(f"Camera: {config['camera']['resolution']} @ {config['camera']['fps']} FPS")
        print(f"GPIO: Pin C{config['gpio']['trigger_pin']} ({config['gpio']['signal_mode']} mode)")
        print("=" * 60)
        
        # Record
        recorder = SynchronizedRecorder(config)
        session_dir = recorder.record()
        
        # Post-process if not disabled
        if not args.record_only:
            processor = DataPostProcessor(session_dir, config)
            processor.process_all()
        else:
            print("\nSkipping post-processing (--record-only flag set)")
            print(f"To process later, run: python main.py --process-only {session_dir}")
    
    print("\n✓ All operations complete!")


if __name__ == "__main__":
    main()

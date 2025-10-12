"""
Main entry point for synchronized camera and FT232H GPIO recording
"""
import yaml
import argparse
from pathlib import Path
from src.synchronized_recorder import SynchronizedRecorder
from src.postprocessor import DataPostProcessor
from src.batch_analyzer import BatchAnalyzer


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def main():
    parser = argparse.ArgumentParser(
        description="Synchronized Camera and FT232H GPIO Recording System"
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
        metavar='RECORDING_DIR',
        help='Only post-process existing recording (provide recording directory path)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    if args.process_only:
        # Post-process only mode
        print(f"Post-processing recording: {args.process_only}")
        processor = DataPostProcessor(args.process_only, config)
        processor.process_all()
    else:
        # Recording mode (with optional post-processing)
        print("=" * 60)
        print("SYNCHRONIZED RECORDING SYSTEM")
        print("=" * 60)
        print(f"Configuration loaded from: {args.config}")
        print(f"Recording duration: {config['recording']['duration_seconds']} seconds")
        
        # Display camera info
        camera_type = config['camera'].get('type', 'oakd').upper()
        camera_res = config['camera'].get('resolution', '1080p')
        camera_fps = config['camera'].get('fps', 30)
        print(f"Camera: {camera_type} - {camera_res} @ {camera_fps} FPS")
        
        # Determine pin label based on mode
        pin_label = "D" if config['gpio'].get('use_adbus', False) else "C"
        print(f"GPIO: Pin {pin_label}{config['gpio']['trigger_pin']} ({config['gpio']['signal_mode']} mode)")
        print("=" * 60)
        
        # Record
        recorder = SynchronizedRecorder(config)
        recording_dirs = recorder.record()
        
        # Post-process if not disabled
        if not args.record_only:
            print("\n" + "=" * 60)
            print("STARTING POST-PROCESSING")
            print("=" * 60)
            
            # Handle both single recording (string) and multiple recordings (list)
            if isinstance(recording_dirs, str):
                recording_dirs = [recording_dirs]
            
            for i, recording_dir in enumerate(recording_dirs, 1):
                print(f"\nPost-processing recording {i} of {len(recording_dirs)}...")
                processor = DataPostProcessor(recording_dir, config)
                processor.process_all()
            
            # Batch-level analysis if multiple recordings
            if len(recording_dirs) > 1:
                # Get batch directory from first recording
                batch_dir = Path(recording_dirs[0]).parent
                
                print("\n" + "=" * 60)
                print("STARTING BATCH-LEVEL ANALYSIS")
                print("=" * 60)
                
                batch_analyzer = BatchAnalyzer(batch_dir, config)
                batch_analyzer.run_full_analysis()
        else:
            print("\nSkipping post-processing (--record-only flag set)")
            if isinstance(recording_dirs, list):
                print("To process later, run:")
                for recording_dir in recording_dirs:
                    print(f"  python main.py --process-only {recording_dir}")
            else:
                print(f"To process later, run: python main.py --process-only {recording_dirs}")
    
    print("\n✓ All operations complete!")


if __name__ == "__main__":
    main()

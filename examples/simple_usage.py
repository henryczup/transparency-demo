"""
Simple usage example for the synchronized recording system
"""
import yaml
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.synchronized_recorder import SynchronizedRecorder
from src.postprocessor import DataPostProcessor


def example_basic_recording():
    """Example: Basic recording with default config"""
    print("Example 1: Basic Recording")
    print("-" * 40)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create recorder and record
    recorder = SynchronizedRecorder(config)
    session_dir = recorder.record()
    
    print(f"\nRecording saved to: {session_dir}")
    return session_dir


def example_custom_config():
    """Example: Recording with custom configuration"""
    print("\nExample 2: Custom Configuration")
    print("-" * 40)
    
    # Create custom config
    config = {
        'recording': {
            'duration_seconds': 5,
            'output_directory': './recordings'
        },
        'camera': {
            'resolution': '720p',
            'fps': 60,
            'enable_depth': False,
            'color_order': 'BGR'
        },
        'gpio': {
            'ft232h_url': 'ftdi://ftdi:232h/1',
            'trigger_pin': 2,
            'signal_high_duration': 0.05,
            'signal_mode': 'pulse'
        },
        'postprocessing': {
            'extract_frames': True,
            'frame_format': 'jpg',
            'generate_metadata': True,
            'frame_extraction_step': 2
        }
    }
    
    # Record
    recorder = SynchronizedRecorder(config)
    session_dir = recorder.record()
    
    print(f"\nRecording saved to: {session_dir}")
    return session_dir


def example_postprocessing(session_dir):
    """Example: Post-processing existing recording"""
    print("\nExample 3: Post-Processing")
    print("-" * 40)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Process
    processor = DataPostProcessor(session_dir, config)
    processor.process_all()


def example_custom_postprocessing(session_dir):
    """Example: Custom post-processing steps"""
    print("\nExample 4: Custom Post-Processing")
    print("-" * 40)
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    processor = DataPostProcessor(session_dir, config)
    
    # Run individual steps
    processor.extract_frames()
    processor.analyze_synchronization()
    processor.create_summary_report()


if __name__ == "__main__":
    # Run basic example
    session = example_basic_recording()
    
    # Run post-processing
    example_postprocessing(session)
    
    print("\n" + "=" * 40)
    print("All examples complete!")
    print("=" * 40)

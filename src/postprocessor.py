"""
Post-processing module for recorded data
"""
import cv2
import json
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from .transparency_analyzer import TransparencyAnalyzer


class DataPostProcessor:
    """Post-processes recorded video and metadata"""
    
    def __init__(self, session_dir, config):
        self.session_dir = Path(session_dir)
        self.config = config
        self.metadata = None
        
        # Load metadata
        metadata_path = self.session_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            print(f"Warning: No metadata found at {metadata_path}")
    
    def extract_frames(self):
        """Extract individual frames from video"""
        if not self.config['postprocessing']['extract_frames']:
            print("Frame extraction disabled in config")
            return
        
        video_path = self.session_dir / "recording.mp4"
        if not video_path.exists():
            print(f"Video file not found: {video_path}")
            return
        
        # Create frames directory
        frames_dir = self.session_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        print(f"\nExtracting frames from video...")
        cap = cv2.VideoCapture(str(video_path))
        
        frame_idx = 0
        extracted_count = 0
        step = self.config['postprocessing']['frame_extraction_step']
        frame_format = self.config['postprocessing']['frame_format']
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Extract every Nth frame
            if frame_idx % step == 0:
                frame_path = frames_dir / f"frame_{frame_idx:06d}.{frame_format}"
                cv2.imwrite(str(frame_path), frame)
                extracted_count += 1
            
            frame_idx += 1
        
        cap.release()
        print(f"Extracted {extracted_count} frames to {frames_dir}")
    
    def generate_frame_metadata(self):
        """Generate CSV with detailed frame information"""
        if not self.config['postprocessing']['generate_metadata']:
            print("Metadata generation disabled in config")
            return
        
        if not self.metadata:
            print("No metadata available")
            return
        
        print("\nGenerating frame metadata CSV...")
        
        # Extract frame data
        timestamps = self.metadata.get('frame_timestamps', [])
        frame_count = self.metadata['session_info']['frame_count']
        
        # Create DataFrame
        data = {
            'frame_number': list(range(frame_count)),
            'timestamp_relative_sec': timestamps,
            'timestamp_relative_ms': [ts * 1000 for ts in timestamps],
        }
        
        # Add GPIO sync information
        sync_info = self.metadata.get('synchronization', {})
        if sync_info.get('gpio_trigger_time'):
            gpio_trigger_relative = sync_info['gpio_trigger_time'] - sync_info['camera_start_time']
            data['time_from_gpio_trigger_ms'] = [(ts - gpio_trigger_relative) * 1000 for ts in timestamps]
        
        df = pd.DataFrame(data)
        
        # Save CSV
        csv_path = self.session_dir / "frame_metadata.csv"
        df.to_csv(csv_path, index=False)
        print(f"Frame metadata saved: {csv_path}")
        
        # Print summary statistics
        print("\n=== Frame Metadata Summary ===")
        print(f"Total frames: {len(df)}")
        if len(df) > 1:
            fps_actual = 1.0 / df['timestamp_relative_sec'].diff().mean()
            print(f"Actual average FPS: {fps_actual:.2f}")
            print(f"Frame time std dev: {df['timestamp_relative_sec'].diff().std() * 1000:.3f} ms")
    
    def analyze_synchronization(self):
        """Analyze and report on synchronization quality"""
        if not self.metadata:
            print("No metadata available for sync analysis")
            return
        
        print("\n=== Synchronization Analysis ===")
        
        sync_info = self.metadata.get('synchronization', {})
        
        if sync_info.get('sync_offset_ms') is not None:
            offset = sync_info['sync_offset_ms']
            print(f"Camera-GPIO sync offset: {offset:.3f} ms")
            
            if abs(offset) < 1.0:
                print("✓ Excellent synchronization (< 1ms)")
            elif abs(offset) < 5.0:
                print("✓ Good synchronization (< 5ms)")
            elif abs(offset) < 10.0:
                print("⚠ Acceptable synchronization (< 10ms)")
            else:
                print("⚠ Poor synchronization (> 10ms) - consider optimization")
        else:
            print("GPIO timing not available")
        
        # Frame timing consistency
        timestamps = self.metadata.get('frame_timestamps', [])
        if len(timestamps) > 1:
            diffs = np.diff(timestamps)
            print(f"\nFrame timing consistency:")
            print(f"  Mean interval: {np.mean(diffs) * 1000:.3f} ms")
            print(f"  Std deviation: {np.std(diffs) * 1000:.3f} ms")
            print(f"  Min interval: {np.min(diffs) * 1000:.3f} ms")
            print(f"  Max interval: {np.max(diffs) * 1000:.3f} ms")
    
    def create_summary_report(self):
        """Create a comprehensive summary report"""
        if not self.metadata:
            print("No metadata available for summary")
            return
        
        report_path = self.session_dir / "summary_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("RECORDING SESSION SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            # Session info
            session = self.metadata['session_info']
            f.write("SESSION INFORMATION:\n")
            f.write(f"  Start Time: {session['start_time']}\n")
            f.write(f"  End Time: {session['end_time']}\n")
            f.write(f"  Duration: {session['duration_seconds']:.3f} seconds\n")
            f.write(f"  Total Frames: {session['frame_count']}\n")
            f.write(f"  Average FPS: {session['frame_count'] / session['duration_seconds']:.2f}\n\n")
            
            # Camera config
            cam = self.metadata['camera_config']
            f.write("CAMERA CONFIGURATION:\n")
            f.write(f"  Resolution: {cam['resolution']}\n")
            f.write(f"  Target FPS: {cam['fps']}\n")
            f.write(f"  Color Order: {cam['color_order']}\n")
            f.write(f"  Depth Enabled: {cam.get('enable_depth', False)}\n\n")
            
            # GPIO config
            gpio = self.metadata['gpio_config']
            f.write("GPIO CONFIGURATION:\n")
            f.write(f"  Trigger Pin: C{gpio['trigger_pin']}\n")
            f.write(f"  Signal Mode: {gpio['signal_mode']}\n")
            f.write(f"  Signal Duration: {gpio['signal_high_duration']}s\n\n")
            
            # Synchronization
            sync = self.metadata.get('synchronization', {})
            f.write("SYNCHRONIZATION:\n")
            if sync.get('sync_offset_ms') is not None:
                f.write(f"  Sync Offset: {sync['sync_offset_ms']:.3f} ms\n")
            else:
                f.write("  GPIO timing not available\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        print(f"Summary report saved: {report_path}")
    
    def run_transparency_analysis(self):
        """Run transparency analysis if enabled"""
        if not self.config.get('transparency_analysis', {}).get('enabled', False):
            print("\nTransparency analysis disabled in config")
            return
        
        # Determine run directory (parent of session directory)
        run_dir = self.session_dir.parent if self.session_dir.parent.name.startswith('run_') else None
        
        # Create analyzer with run_dir for shared ROI
        analyzer = TransparencyAnalyzer(self.session_dir, self.config, self.metadata, run_dir)
        
        # Run full analysis
        analyzer.run_full_analysis()
    
    def process_all(self):
        """Run all post-processing steps"""
        print("\n" + "=" * 60)
        print("STARTING POST-PROCESSING")
        print("=" * 60)
        
        self.extract_frames()
        self.generate_frame_metadata()
        self.analyze_synchronization()
        self.create_summary_report()
        self.run_transparency_analysis()
        
        print("\n" + "=" * 60)
        print("POST-PROCESSING COMPLETE")
        print("=" * 60)

"""
Synchronized Camera and FT232H GPIO Recording System
Supports multiple camera types via Strategy pattern
"""
import cv2
import numpy as np
from pyftdi.gpio import GpioAsyncController
import threading
import time
from pathlib import Path
from datetime import datetime
import json
from .camera_factory import CameraFactory


class SynchronizedRecorder:
    """Handles synchronized recording from camera and FT232H GPIO trigger"""
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.frames = []
        self.timestamps = []
        self.gpio_trigger_time = None
        self.camera_start_time = None
        
        # Setup output directory
        self.output_dir = Path(config['recording']['output_directory'])
        self.recording_dir = None
        
        # Initialize components
        self.camera = None  # Camera strategy instance
        self.gpio = None
        self.gpio_mode = None
        
    def setup_camera(self):
        """Initialize camera using strategy pattern"""
        camera_config = self.config.get('camera', {})
        
        # Create camera strategy based on configuration
        self.camera = CameraFactory.create_camera(camera_config)
        
        # Setup the camera
        self.camera.setup(camera_config)
        
        print("Camera setup complete!")
        
    def setup_gpio(self):
        """Initialize FT232H GPIO controller"""
        print("Setting up FT232H GPIO...")
        
        try:
            # Configure USB backend for Windows
            try:
                import usb.backend.libusb1
                import libusb_package
                # Set backend to use libusb-package
                backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
                import os
                os.environ['PYUSB_BACKEND'] = str(backend)
            except ImportError:
                pass  # Backend will use default
            
            # Check if we should use ADBUS (D pins, 3.3V) or ACBUS (C pins, 2.4V)
            use_adbus = self.config['gpio'].get('use_adbus', False)
            
            if use_adbus:
                # Use ADBUS (D pins) for proper 3.3V output
                from pyftdi.ftdi import Ftdi
                self.gpio = Ftdi()
                self.gpio.open_from_url(self.config['gpio']['ft232h_url'])
                self.gpio.set_bitmode(0xFF, Ftdi.BitMode.BITBANG)
                self.gpio.write_data(bytes([0x00]))
                self.gpio_mode = 'adbus'
                print("FT232H GPIO setup complete (ADBUS/D-pins, 3.3V)!")
            else:
                # Use ACBUS (C pins) - may output lower voltage
                self.gpio = GpioAsyncController()
                self.gpio.configure(
                    self.config['gpio']['ft232h_url'],
                    direction=0xFF  # All pins as output
                )
                self.gpio.write(0x00)
                self.gpio_mode = 'acbus'
                print("FT232H GPIO setup complete (ACBUS/C-pins)!")
            
        except Exception as e:
            print(f"Warning: Could not initialize FT232H: {e}")
            print("Continuing without GPIO control...")
            self.gpio = None
            self.gpio_mode = None
    
    def trigger_gpio(self):
        """Send trigger signal via GPIO"""
        if self.gpio is None:
            print("GPIO not available, skipping trigger")
            return
        
        pin = self.config['gpio']['trigger_pin']
        signal_mode = self.config['gpio']['signal_mode']
        
        # Record exact trigger time
        self.gpio_trigger_time = time.time()
        
        # Set pin HIGH (different methods for ADBUS vs ACBUS)
        pin_label = "D" if self.gpio_mode == 'adbus' else "C"
        
        if self.gpio_mode == 'adbus':
            # ADBUS mode: use write_data with byte array
            self.gpio.write_data(bytes([1 << pin]))
        else:
            # ACBUS mode: use write with integer
            self.gpio.write(1 << pin)
        
        print(f"GPIO trigger sent on pin {pin_label}{pin} at t={self.gpio_trigger_time:.6f}")
        
        if signal_mode == "pulse":
            # Short pulse mode
            duration = self.config['gpio']['signal_high_duration']
            time.sleep(duration)
            
            if self.gpio_mode == 'adbus':
                self.gpio.write_data(bytes([0x00]))
            else:
                self.gpio.write(0x00)
            
            print(f"GPIO pulse completed ({duration}s)")
        # If continuous, leave HIGH until recording stops
    
    def record(self):
        """Main recording function with synchronized start - supports multiple recordings"""
        # Create parent batch directory with timestamp
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.batch_dir = self.output_dir / f"batch_{batch_timestamp}"
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Batch directory: {self.batch_dir}")
        
        # Setup hardware once for all recordings
        self.setup_camera()
        self.setup_gpio()
        
        # Start the camera
        print("\nStarting camera...")
        self.camera.start()
        
        # Startup wait period (camera warmup, GPIO off)
        startup_wait = self.config['recording'].get('startup_wait_seconds', 0)
        if startup_wait > 0:
            print(f"\n⏱  Startup wait period: {startup_wait} seconds")
            print("   Camera warming up, GPIO pins OFF...")
            for remaining in range(startup_wait, 0, -1):
                print(f"   {remaining} seconds remaining...", end='\r')
                time.sleep(1)
            print("\n✓ Startup wait complete")
        
        # Get recording configuration
        num_recordings = self.config['recording'].get('num_recordings', 1)
        interval_seconds = self.config['recording'].get('interval_seconds', 20)
        
        print(f"\n📹 Recording plan: {num_recordings} recording(s)")
        if num_recordings > 1:
            print(f"   Recording duration: {self.config['recording']['duration_seconds']}s")
            print(f"   Interval between recordings: {interval_seconds}s (GPIO OFF)")
        
        all_recording_dirs = []
        
        # Perform multiple recordings
        for recording_num in range(1, num_recordings + 1):
            print("\n" + "=" * 60)
            print(f"RECORDING {recording_num} of {num_recordings}")
            print("=" * 60)
            
            recording_dir = self._record_single(recording_num)
            all_recording_dirs.append(recording_dir)
            
            # Wait between recordings (except after last one)
            if recording_num < num_recordings:
                print(f"\n⏸  Interval period: {interval_seconds} seconds (GPIO OFF)")
                for remaining in range(interval_seconds, 0, -1):
                    print(f"   Next recording in {remaining} seconds...", end='\r')
                    time.sleep(1)
                print("\n")
        
        # Cleanup after all recordings
        self._cleanup()
        
        print("\n" + "=" * 60)
        print("ALL RECORDINGS COMPLETE")
        print("=" * 60)
        print(f"📁 Batch directory: {self.batch_dir}")
        print(f"Total recordings: {len(all_recording_dirs)}")
        for i, dir in enumerate(all_recording_dirs, 1):
            # Show relative path from batch directory
            rel_path = Path(dir).relative_to(self.batch_dir)
            print(f"  Recording {i}: {rel_path}")
        
        return all_recording_dirs
    
    def _record_single(self, recording_num):
        """Record a single recording"""
        # Create recording directory inside batch directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_dir = self.batch_dir / f"recording_{recording_num:02d}_{timestamp}"
        recording_dir.mkdir(parents=True, exist_ok=True)
        
        # Show relative path
        rel_path = recording_dir.relative_to(self.batch_dir)
        print(f"Recording directory: {rel_path}")
        
        # Reset frame storage for this recording
        self.frames = []
        self.timestamps = []
        
        duration = self.config['recording']['duration_seconds']
        print(f"\nStarting synchronized recording for {duration} seconds...")
        print("Synchronizing in 3...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        
        # SYNCHRONIZED START
        print("\n=== RECORDING STARTED ===")
        start_time = time.time()
        self.camera_start_time = start_time
        
        # Trigger GPIO in parallel thread for maximum synchronization
        gpio_thread = threading.Thread(target=self.trigger_gpio)
        gpio_thread.start()
        
        # Recording loop
        frame_count = 0
        while self.camera.is_running():
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                break
            
            # Get frame from camera
            frame = self.camera.get_frame()
            
            if frame is not None:
                timestamp = time.time()
                
                self.frames.append(frame)
                self.timestamps.append(timestamp)
                frame_count += 1
                
        
        # Stop recording
        print("\n=== RECORDING STOPPED ===")
        end_time = time.time()
        
        # Turn off GPIO if in continuous mode
        if self.gpio and self.config['gpio']['signal_mode'] == "continuous":
            if self.gpio_mode == 'adbus':
                self.gpio.write_data(bytes([0x00]))
            else:
                self.gpio.write(0x00)
            print("GPIO signal turned OFF")
        
        gpio_thread.join()
        
        # Save video
        print(f"\nRecorded {frame_count} frames")
        self._save_video(recording_dir)
        self._save_metadata(recording_dir, start_time, end_time)
        
        print(f"Recording saved to: {recording_dir}")
        return str(recording_dir)
    
    def _cleanup(self):
        """Cleanup hardware after all recordings complete"""
        
        cv2.destroyAllWindows()
        
        # Cleanup camera
        if self.camera:
            self.camera.cleanup()
        
        # Ensure GPIO is OFF before closing
        if self.gpio:
            print("Turning off GPIO...")
            if self.gpio_mode == 'adbus':
                self.gpio.write_data(bytes([0x00]))  # Ensure D pins are LOW
            else:
                self.gpio.write(0x00)  # Ensure C pins are LOW
            print("✓ GPIO pins set to LOW")
            print("⚠ Note: Pin may go HIGH after program exits (hardware pull-up)")
            self.gpio.close()
        
        print("✓ Cleanup complete")
    
    def _save_video(self, recording_dir):
        """Save recorded frames as video file"""
        if not self.frames:
            print("No frames to save")
            return
        
        video_path = Path(recording_dir) / "recording.mp4"
        
        height, width = self.frames[0].shape[:2]
        fps = self.config['camera'].get('fps', 30)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        
        for frame in self.frames:
            out.write(frame)
        
        out.release()
        print(f"Video saved: {video_path}")
    
    def _save_metadata(self, recording_dir, start_time, end_time):
        """Save recording metadata including synchronization info"""
        metadata = {
            "recording_info": {
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "duration_seconds": end_time - start_time,
                "frame_count": len(self.frames)
            },
            "synchronization": {
                "camera_start_time": self.camera_start_time,
                "gpio_trigger_time": self.gpio_trigger_time,
                "sync_offset_ms": (self.gpio_trigger_time - self.camera_start_time) * 1000 if self.gpio_trigger_time else None
            },
            "camera_config": self.config['camera'],
            "gpio_config": self.config['gpio'],
            "frame_timestamps": [ts - start_time for ts in self.timestamps]  # Relative timestamps
        }
        
        metadata_path = Path(recording_dir) / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved: {metadata_path}")

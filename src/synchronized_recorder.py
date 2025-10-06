"""
Synchronized OAK-D Camera and FT232H GPIO Recording System
"""
import depthai as dai
import cv2
import numpy as np
from pyftdi.gpio import GpioAsyncController
import threading
import time
from pathlib import Path
from datetime import datetime
import json


class SynchronizedRecorder:
    """Handles synchronized recording from OAK-D camera and FT232H GPIO trigger"""
    
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.frames = []
        self.timestamps = []
        self.gpio_trigger_time = None
        self.camera_start_time = None
        
        # Setup output directory
        self.output_dir = Path(config['recording']['output_directory'])
        self.session_dir = None
        
        # Initialize components
        self.pipeline = None
        self.device = None
        self.gpio = None
        
    def setup_camera(self):
        """Initialize OAK-D camera pipeline"""
        print("Setting up OAK-D camera...")
        
        # Connect to device first
        try:
            self.device = dai.Device()
            print(f"✓ Connected to device: {self.device.getDeviceName()}")
        except RuntimeError as e:
            if "ALREADY_IN_USE" in str(e):
                print("\n✗ Device is locked by another process.")
                print("Run: python reset_camera.py")
                raise
            elif "No device found" in str(e) or "Cannot find device" in str(e):
                print("\n✗ No OAK-D camera detected.")
                print("Please check:")
                print("  1. Camera is connected via USB")
                print("  2. USB cable is working (try USB 3.0 port)")
                print("  3. Camera LED is on")
                raise
            else:
                raise
        
        # Create pipeline with device
        self.pipeline = dai.Pipeline(self.device)
        
        # Use modern Camera node API
        cam = self.pipeline.create(dai.node.Camera)
        
        # Build the camera with socket configuration
        self.cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
        
        # Configure output capability
        cap = dai.ImgFrameCapability()
        
        # Set resolution
        resolution_map = {
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
            "720p": (1280, 720),
        }
        width, height = resolution_map.get(
            self.config['camera']['resolution'], 
            (1920, 1080)
        )
        cap.size.fixed((width, height))
        
        # Set FPS
        cap.fps.fixed(float(self.config['camera']['fps']))
        
        # Request output with capability and create queue
        # Second parameter is onHost (True = process on host, False = on device)
        self.video_queue = self.cam_node.requestOutput(cap, True).createOutputQueue()
        
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
        """Main recording function with synchronized start"""
        # Create session directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{timestamp}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nSession directory: {self.session_dir}")
        
        # Setup hardware (this now connects to device and creates pipeline)
        self.setup_camera()
        self.setup_gpio()
        
        # Start the pipeline
        print("\nStarting camera pipeline...")
        self.pipeline.start()
        
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
        while self.pipeline.isRunning():
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                break
            
            # Get frame from camera
            video_frame = self.video_queue.tryGet()
            
            if video_frame is not None:
                frame = video_frame.getCvFrame()
                timestamp = time.time()
                
                self.frames.append(frame)
                self.timestamps.append(timestamp)
                frame_count += 1
                
                # Optional: Display frame
                cv2.imshow("Recording", frame)
                if cv2.waitKey(1) == ord('q'):
                    print("\nRecording interrupted by user")
                    break
        
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
        cv2.destroyAllWindows()
        
        # Save video
        print(f"\nRecorded {frame_count} frames")
        self._save_video()
        self._save_metadata(start_time, end_time)
        
        # Cleanup
        if self.gpio:
            self.gpio.close()
        
        print(f"\nRecording saved to: {self.session_dir}")
        return str(self.session_dir)
    
    def _save_video(self):
        """Save recorded frames as video file"""
        if not self.frames:
            print("No frames to save")
            return
        
        video_path = self.session_dir / "recording.mp4"
        
        height, width = self.frames[0].shape[:2]
        fps = self.config['camera']['fps']
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        
        for frame in self.frames:
            out.write(frame)
        
        out.release()
        print(f"Video saved: {video_path}")
    
    def _save_metadata(self, start_time, end_time):
        """Save session metadata including synchronization info"""
        metadata = {
            "session_info": {
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
        
        metadata_path = self.session_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved: {metadata_path}")

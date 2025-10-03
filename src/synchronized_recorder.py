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
        
        # Create pipeline
        self.pipeline = dai.Pipeline()
        
        # Define source - color camera
        cam_rgb = self.pipeline.create(dai.node.ColorCamera)
        
        # Set camera properties
        resolution_map = {
            "1080p": dai.ColorCameraProperties.SensorResolution.THE_1080_P,
            "4k": dai.ColorCameraProperties.SensorResolution.THE_4_K,
            "720p": dai.ColorCameraProperties.SensorResolution.THE_720_P,
        }
        
        cam_rgb.setResolution(resolution_map.get(
            self.config['camera']['resolution'], 
            dai.ColorCameraProperties.SensorResolution.THE_1080_P
        ))
        cam_rgb.setFps(self.config['camera']['fps'])
        
        if self.config['camera']['color_order'] == 'RGB':
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
        else:
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        
        # Create output
        xout_video = self.pipeline.create(dai.node.XLinkOut)
        xout_video.setStreamName("video")
        cam_rgb.video.link(xout_video.input)
        
        # Optional: Add depth camera
        if self.config['camera'].get('enable_depth', False):
            mono_left = self.pipeline.create(dai.node.MonoCamera)
            mono_right = self.pipeline.create(dai.node.MonoCamera)
            stereo = self.pipeline.create(dai.node.StereoDepth)
            
            mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
            mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
            mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
            mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
            
            stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
            mono_left.out.link(stereo.left)
            mono_right.out.link(stereo.right)
            
            xout_depth = self.pipeline.create(dai.node.XLinkOut)
            xout_depth.setStreamName("depth")
            stereo.depth.link(xout_depth.input)
        
        print("Camera setup complete!")
        
    def setup_gpio(self):
        """Initialize FT232H GPIO controller"""
        print("Setting up FT232H GPIO...")
        
        try:
            self.gpio = GpioAsyncController()
            self.gpio.configure(
                self.config['gpio']['ft232h_url'],
                direction=0xFF  # All pins as output
            )
            
            # Set all pins low initially
            self.gpio.write(0x00)
            print("FT232H GPIO setup complete!")
            
        except Exception as e:
            print(f"Warning: Could not initialize FT232H: {e}")
            print("Continuing without GPIO control...")
            self.gpio = None
    
    def trigger_gpio(self):
        """Send trigger signal via GPIO"""
        if self.gpio is None:
            print("GPIO not available, skipping trigger")
            return
        
        pin = self.config['gpio']['trigger_pin']
        signal_mode = self.config['gpio']['signal_mode']
        
        # Record exact trigger time
        self.gpio_trigger_time = time.time()
        
        # Set pin HIGH
        self.gpio.write(1 << pin)
        print(f"GPIO trigger sent on pin C{pin} at t={self.gpio_trigger_time:.6f}")
        
        if signal_mode == "pulse":
            # Short pulse mode
            duration = self.config['gpio']['signal_high_duration']
            time.sleep(duration)
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
        
        # Setup hardware
        self.setup_camera()
        self.setup_gpio()
        
        # Connect to device
        print("\nConnecting to OAK-D device...")
        self.device = dai.Device(self.pipeline)
        
        # Get video output queue
        video_queue = self.device.getOutputQueue(name="video", maxSize=30, blocking=False)
        
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
        while True:
            elapsed = time.time() - start_time
            
            if elapsed >= duration:
                break
            
            # Get frame from camera
            video_frame = video_queue.tryGet()
            
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
        
        video_path = self.session_dir / "recording.avi"
        
        height, width = self.frames[0].shape[:2]
        fps = self.config['camera']['fps']
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
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

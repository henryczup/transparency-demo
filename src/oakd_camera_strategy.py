"""
OAK-D Camera Strategy Implementation
Wraps the existing OAK-D camera functionality
"""
import depthai as dai
import numpy as np
from typing import Optional, Tuple
from .camera_strategy import CameraStrategy


class OAKDCameraStrategy(CameraStrategy):
    """Strategy implementation for OAK-D camera"""
    
    def __init__(self):
        self.pipeline = None
        self.device = None
        self.cam_node = None
        self.video_queue = None
        self.config = None
        self._running = False
        self._width = 1920
        self._height = 1080
    
    def setup(self, config: dict) -> None:
        """Initialize OAK-D camera pipeline"""
        self.config = config
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
        self._width, self._height = resolution_map.get(
            config.get('resolution', '1080p'), 
            (1920, 1080)
        )
        cap.size.fixed((self._width, self._height))
        
        # Set FPS
        cap.fps.fixed(float(config.get('fps', 30)))
        
        # Configure camera control settings
        if config.get('manual_exposure', False):
            # Manual exposure settings
            exposure_time = config.get('exposure_time_us', 10000)  # microseconds
            iso_value = config.get('iso', 400)
            
            self.cam_node.initialControl.setManualExposure(exposure_time, iso_value)
            print(f"  Manual exposure: {exposure_time}us, ISO: {iso_value}")
        else:
            # Auto exposure is enabled by default
            print("  Auto exposure: ENABLED (brightness may vary)")
        
        if config.get('manual_white_balance', False):
            # Manual white balance (color temperature in Kelvin)
            wb_temp = config.get('white_balance_temp', 5000)
            self.cam_node.initialControl.setManualWhiteBalance(wb_temp)
            print(f"  Manual white balance: {wb_temp}K")
        else:
            print("  Auto white balance: ENABLED")
        
        # Request output with capability and create queue
        self.video_queue = self.cam_node.requestFullResolutionOutput(
            useHighestResolution=True
        ).createOutputQueue()
        
        print("OAK-D camera setup complete!")
    
    def start(self) -> None:
        """Start the camera pipeline"""
        if self.pipeline is None:
            raise RuntimeError("Camera not setup. Call setup() first.")
        
        print("Starting OAK-D camera pipeline...")
        self.pipeline.start()
        self._running = True
    
    def stop(self) -> None:
        """Stop the camera pipeline"""
        # Pipeline cleanup is handled in cleanup()
        self._running = False
        print("OAK-D camera stopped.")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame from the camera"""
        if not self._running or self.video_queue is None:
            return None
        
        video_frame = self.video_queue.tryGet()
        
        if video_frame is not None:
            frame = video_frame.getCvFrame()
            return frame
        
        return None
    
    def is_running(self) -> bool:
        """Check if camera is currently running"""
        return self._running and self.pipeline is not None and self.pipeline.isRunning()
    
    def get_frame_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of frames from this camera"""
        return (self._width, self._height)
    
    def cleanup(self) -> None:
        """Cleanup camera resources"""
        self._running = False
        # Device cleanup is automatic when object is destroyed
        print("✓ OAK-D camera cleanup complete")

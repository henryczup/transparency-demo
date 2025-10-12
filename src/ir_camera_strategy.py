"""
IR Camera Strategy Implementation
Uses OpenCV VideoCapture for IR camera access
"""
import cv2
import numpy as np
from typing import Optional, Tuple
from .camera_strategy import CameraStrategy


class IRCameraStrategy(CameraStrategy):
    """Strategy implementation for IR camera using OpenCV"""
    
    def __init__(self):
        self.camera_index = None
        self.probe_indices = None
        self.backend = None
        self.cap = None
        self._is_recording = False
        self.config = None
        self._width = 640
        self._height = 480
    
    def setup(self, config: dict) -> None:
        """Initialize IR camera"""
        self.config = config
        print("Setting up IR camera...")
        
        # Get camera configuration
        self.camera_index = config.get('camera_index', None)
        self.probe_indices = config.get('probe_indices', None)
        self.backend = config.get('backend', None)
        
        # Store desired resolution
        resolution_map = {
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
            "720p": (1280, 720),
            "480p": (640, 480),
        }
        self._width, self._height = resolution_map.get(
            config.get('resolution', '480p'),
            (640, 480)
        )
        
        print(f"  Target resolution: {self._width}x{self._height}")
        print(f"  Camera index: {self.camera_index}")
        if self.probe_indices:
            print(f"  Probe indices: {self.probe_indices}")
        
        print("IR camera setup complete!")
    
    def _build_candidate_indices(self):
        """Build list of camera indices to try"""
        indices = []
        if self.camera_index is not None:
            indices.append(self.camera_index)
        if self.probe_indices:
            for idx in self.probe_indices:
                if idx not in indices:
                    indices.append(idx)
        if not indices:
            indices = list(range(5))
        return indices
    
    @staticmethod
    def discover_cameras(max_index=10, backend=None):
        """Discover available camera indices"""
        available_indices = []
        for index in range(max_index):
            cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
            if cap is None:
                continue
            if cap.isOpened():
                available_indices.append(index)
            cap.release()
        return available_indices
    
    def _attempt_open(self, index):
        """Attempt to open camera at given index"""
        cap = cv2.VideoCapture(index) if self.backend is None else cv2.VideoCapture(index, self.backend)
        if cap.isOpened():
            # Try to set resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            
            # Try to set FPS if specified
            if self.config and 'fps' in self.config:
                cap.set(cv2.CAP_PROP_FPS, self.config['fps'])
            
            # Get actual resolution (may differ from requested)
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width > 0 and actual_height > 0:
                self._width = actual_width
                self._height = actual_height
            
            return cap
        cap.release()
        return None
    
    def start(self) -> None:
        """Start the camera capture"""
        if self.cap is None:
            candidate_indices = self._build_candidate_indices()
            attempted_indices = []
            for idx in candidate_indices:
                cap = self._attempt_open(idx)
                attempted_indices.append(idx)
                if cap:
                    self.cap = cap
                    self.camera_index = idx
                    break
            if self.cap is None:
                attempted_str = ", ".join(str(i) for i in attempted_indices)
                raise IOError(f"Cannot open IR camera. Tried indices: {attempted_str}")
        
        self._is_recording = True
        print(f"IR camera started on index {self.camera_index}.")
        print(f"  Actual resolution: {self._width}x{self._height}")
        
        # Get actual FPS
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if actual_fps > 0:
            print(f"  Actual FPS: {actual_fps}")
    
    def stop(self) -> None:
        """Stop the camera capture"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self._is_recording = False
        print("IR camera stopped.")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get a single frame from the camera"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def is_running(self) -> bool:
        """Check if camera is currently running"""
        return self._is_recording and self.cap is not None and self.cap.isOpened()
    
    def get_frame_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of frames from this camera"""
        return (self._width, self._height)
    
    def get_ir_data(self) -> Optional[Tuple[float, float, float]]:
        """
        Get IR data from the frame.
        Returns temperature statistics based on grayscale values.
        """
        frame = self.get_frame()
        if frame is not None:
            # If the frame is color, convert it to grayscale for analysis
            if len(frame.shape) == 3:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray_frame = frame
            
            min_temp = float(np.min(gray_frame))
            max_temp = float(np.max(gray_frame))
            avg_temp = float(np.mean(gray_frame))
            return min_temp, max_temp, avg_temp
        return None, None, None
    
    def cleanup(self) -> None:
        """Cleanup camera resources"""
        self.stop()
        print("✓ IR camera cleanup complete")

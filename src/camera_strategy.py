"""
Abstract Camera Strategy Interface
Defines the interface for different camera implementations
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np


class CameraStrategy(ABC):
    """Abstract base class for camera strategies"""
    
    @abstractmethod
    def setup(self, config: dict) -> None:
        """
        Initialize the camera with the given configuration
        
        Args:
            config: Camera configuration dictionary
        """
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the camera capture"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the camera capture"""
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get a single frame from the camera
        
        Returns:
            Frame as numpy array (BGR format) or None if no frame available
        """
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        """
        Check if camera is currently running
        
        Returns:
            True if camera is running, False otherwise
        """
        pass
    
    @abstractmethod
    def get_frame_dimensions(self) -> Tuple[int, int]:
        """
        Get the dimensions of frames from this camera
        
        Returns:
            Tuple of (width, height)
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup camera resources"""
        pass
    
    def get_ir_data(self) -> Optional[Tuple[float, float, float]]:
        """
        Get IR data from the frame (optional method for IR cameras)
        
        Returns:
            Tuple of (min_temp, max_temp, avg_temp) or None if not supported
        """
        return None

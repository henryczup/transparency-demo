"""
Camera Factory
Creates the appropriate camera strategy based on configuration
"""
from .camera_strategy import CameraStrategy
from .oakd_camera_strategy import OAKDCameraStrategy
from .ir_camera_strategy import IRCameraStrategy


class CameraFactory:
    """Factory for creating camera strategy instances"""
    
    @staticmethod
    def create_camera(config: dict) -> CameraStrategy:
        """
        Create a camera strategy based on configuration
        
        Args:
            config: Camera configuration dictionary with 'type' key
            
        Returns:
            CameraStrategy instance
            
        Raises:
            ValueError: If camera type is not supported
        """
        camera_type = config.get('type', 'oakd').lower()
        
        if camera_type == 'oakd':
            return OAKDCameraStrategy()
        elif camera_type == 'ir':
            return IRCameraStrategy()
        else:
            raise ValueError(
                f"Unsupported camera type: {camera_type}. "
                f"Supported types: 'oakd', 'ir'"
            )
    
    @staticmethod
    def get_supported_types():
        """Get list of supported camera types"""
        return ['oakd', 'ir']

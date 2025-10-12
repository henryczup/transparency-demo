"""
Test script for camera strategy pattern
Demonstrates how to use different camera strategies
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.camera_factory import CameraFactory
from src.ir_camera_strategy import IRCameraStrategy
import cv2
import time


def test_ir_camera_discovery():
    """Test IR camera discovery"""
    print("=" * 60)
    print("IR CAMERA DISCOVERY TEST")
    print("=" * 60)
    
    available = IRCameraStrategy.discover_cameras(max_index=5)
    print(f"\nAvailable camera indices: {available}")
    
    if not available:
        print("⚠ No cameras found!")
    else:
        print(f"✓ Found {len(available)} camera(s)")
    
    return available


def test_ir_camera_capture(camera_index=0):
    """Test IR camera capture"""
    print("\n" + "=" * 60)
    print("IR CAMERA CAPTURE TEST")
    print("=" * 60)
    
    config = {
        'type': 'ir',
        'camera_index': camera_index,
        'resolution': '480p',
        'fps': 30
    }
    
    try:
        # Create camera using factory
        camera = CameraFactory.create_camera(config)
        print("\n✓ Camera strategy created")
        
        # Setup camera
        camera.setup(config)
        print("✓ Camera setup complete")
        
        # Start camera
        camera.start()
        print("✓ Camera started")
        
        # Get frame dimensions
        width, height = camera.get_frame_dimensions()
        print(f"✓ Frame dimensions: {width}x{height}")
        
        # Capture a few frames
        print("\nCapturing frames...")
        frame_count = 0
        start_time = time.time()
        
        while frame_count < 30:  # Capture 30 frames
            frame = camera.get_frame()
            
            if frame is not None:
                frame_count += 1
                
                # Display frame
                cv2.imshow('IR Camera Test', frame)
                
                # Get IR data
                if hasattr(camera, 'get_ir_data'):
                    min_temp, max_temp, avg_temp = camera.get_ir_data()
                    if min_temp is not None:
                        print(f"Frame {frame_count}: Min={min_temp:.1f}, Max={max_temp:.1f}, Avg={avg_temp:.1f}")
                
                # Break on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        
        print(f"\n✓ Captured {frame_count} frames in {elapsed:.2f}s ({fps:.1f} FPS)")
        
        # Cleanup
        camera.stop()
        camera.cleanup()
        cv2.destroyAllWindows()
        
        print("✓ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_camera_factory():
    """Test camera factory"""
    print("\n" + "=" * 60)
    print("CAMERA FACTORY TEST")
    print("=" * 60)
    
    # Test supported types
    supported = CameraFactory.get_supported_types()
    print(f"\nSupported camera types: {supported}")
    
    # Test creating different camera types
    for camera_type in supported:
        try:
            config = {'type': camera_type}
            camera = CameraFactory.create_camera(config)
            print(f"✓ Successfully created {camera_type} camera strategy")
        except Exception as e:
            print(f"✗ Failed to create {camera_type} camera: {e}")
    
    # Test invalid type
    try:
        config = {'type': 'invalid_camera'}
        camera = CameraFactory.create_camera(config)
        print("✗ Should have raised ValueError for invalid type")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CAMERA STRATEGY PATTERN TESTS")
    print("=" * 60)
    
    # Test 1: Factory
    test_camera_factory()
    
    # Test 2: Discovery
    available = test_ir_camera_discovery()
    
    # Test 3: Capture (if cameras available)
    if available:
        print(f"\nAttempting to use camera index {available[0]}...")
        test_ir_camera_capture(available[0])
    else:
        print("\n⚠ Skipping capture test (no cameras found)")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
Simple test script for OAK-D color camera only
Tests the modern Camera API with minimal configuration
"""
import depthai as dai
import cv2

def test_color_camera():
    """Test color camera with modern API"""
    print("Testing OAK-D color camera...")
    
    # Connect to device
    try:
        device = dai.Device()
        print(f"✓ Connected to device: {device.getDeviceName()}")
    except RuntimeError as e:
        print(f"✗ Failed to connect: {e}")
        return
    
    # Create pipeline
    pipeline = dai.Pipeline(device)
    
    # Create Camera node
    cam = pipeline.create(dai.node.Camera)
    
    # Build camera for CAM_A (color camera)
    cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
    
    # Configure output capability
    cap = dai.ImgFrameCapability()
    cap.size.fixed((1920, 1080))  # 1080p
    cap.fps.fixed(30.0)  # 30 FPS
    
    # Request output and create queue
    video_queue = cam_node.requestOutput(cap, True).createOutputQueue()
    
    # Start pipeline
    print("Starting pipeline...")
    pipeline.start()
    
    print("✓ Pipeline started successfully!")
    print("Press 'q' to quit")
    
    frame_count = 0
    try:
        while pipeline.isRunning():
            # Get frame
            video_frame = video_queue.tryGet()
            
            if video_frame is not None:
                frame = video_frame.getCvFrame()
                frame_count += 1
                
                # Add frame counter to display
                cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Display
                cv2.imshow("Color Camera Test", frame)
                
                if cv2.waitKey(1) == ord('q'):
                    print(f"\n✓ Test complete! Captured {frame_count} frames")
                    break
    
    except KeyboardInterrupt:
        print(f"\n✓ Test interrupted. Captured {frame_count} frames")
    
    finally:
        cv2.destroyAllWindows()
        print("✓ Cleanup complete")

if __name__ == "__main__":
    test_color_camera()

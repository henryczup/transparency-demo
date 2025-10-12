"""
Auto-calibration script for camera exposure settings.
This script will:
1. Test different exposure combinations automatically
2. Show you the results with brightness metrics
3. Let you pick the best one or fine-tune manually
4. Update your config.yaml with the chosen settings

Usage: python scripts/calibrate_exposure.py
"""

import cv2
import numpy as np
import depthai as dai
import yaml
from pathlib import Path
import time


def load_config():
    """Load the current config.yaml"""
    config_path = Path("config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def save_config(config):
    """Save updated config.yaml"""
    config_path = Path("config.yaml")
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def capture_test_frame(exposure_us, iso, config):
    """Capture a test frame with given settings"""
    with dai.Pipeline() as pipeline:
        # Create camera node
        cam = pipeline.create(dai.node.Camera)
        cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
        
        # Set manual exposure and white balance
        cam_node.initialControl.setManualExposure(exposure_us, iso)
        cam_node.initialControl.setManualWhiteBalance(5000)
        
        # Configure output capability
        cap = dai.ImgFrameCapability()
        
        # Set resolution
        resolution_map = {
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
            "720p": (1280, 720),
        }
        width, height = resolution_map.get(config['camera']['resolution'], (1920, 1080))
        cap.size.fixed((width, height))
        
        # Set FPS
        cap.fps.fixed(float(config['camera']['fps']))
        
        # Request output and create queue
        video_queue = cam_node.requestOutput(cap, True).createOutputQueue()
        
        # Start pipeline
        pipeline.start()
        
        # Wait for camera to stabilize
        time.sleep(1.5)
        
        # Get frame
        video_in = video_queue.get()
        frame = video_in.getCvFrame()
        
        return frame


def analyze_frame(frame):
    """Analyze frame brightness and quality"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)
    underexposed = np.sum(gray < 10) / gray.size * 100
    overexposed = np.sum(gray > 245) / gray.size * 100
    
    # Calculate quality score (prefer mean around 100-140, low clipping)
    brightness_score = 100 - abs(120 - mean_brightness)
    clipping_penalty = (underexposed + overexposed) * 5
    quality_score = max(0, brightness_score - clipping_penalty)
    
    return {
        'mean': mean_brightness,
        'std': std_brightness,
        'underexposed': underexposed,
        'overexposed': overexposed,
        'quality_score': quality_score
    }


def auto_detect_from_camera(config):
    """Let camera auto-expose, then capture and display the settings it chose"""
    print("\n" + "="*60)
    print("AUTO-DETECT MODE")
    print("="*60)
    print("Camera will use auto-exposure to find optimal settings...")
    print("This will take about 5-10 seconds.\n")
    
    with dai.Pipeline() as pipeline:
        # Create camera node
        cam = pipeline.create(dai.node.Camera)
        cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
        
        # Enable auto-exposure (default behavior - don't set manual exposure)
        # Auto white balance is also enabled by default
        
        # Configure output
        cap = dai.ImgFrameCapability()
        resolution_map = {
            "1080p": (1920, 1080),
            "4k": (3840, 2160),
            "720p": (1280, 720),
        }
        width, height = resolution_map.get(config['camera']['resolution'], (1920, 1080))
        cap.size.fixed((width, height))
        cap.fps.fixed(float(config['camera']['fps']))
        
        video_queue = cam_node.requestOutput(cap, True).createOutputQueue()
        
        # Start pipeline
        pipeline.start()
        
        print("Waiting for camera to stabilize and auto-adjust...")
        time.sleep(3)  # Let auto-exposure settle
        
        # Collect multiple frames to see the exposure settings
        detected_settings = []
        print("Sampling frames to detect exposure settings...")
        
        for i in range(10):
            video_in = video_queue.get()
            frame = video_in.getCvFrame()
            
            # Get exposure metadata from the frame
            exposure_time = video_in.getExposureTime().total_seconds() * 1_000_000  # Convert to microseconds
            iso_value = video_in.getSensitivity()
            
            detected_settings.append({
                'exposure': int(exposure_time),
                'iso': iso_value,
                'frame': frame
            })
            
            time.sleep(0.1)
        
        # Calculate average settings
        avg_exposure = int(np.mean([s['exposure'] for s in detected_settings]))
        avg_iso = int(np.mean([s['iso'] for s in detected_settings]))
        
        # Use the last frame for analysis
        last_frame = detected_settings[-1]['frame']
        metrics = analyze_frame(last_frame)
        
        print("\n" + "="*60)
        print("AUTO-DETECTED SETTINGS")
        print("="*60)
        print(f"Average Exposure: {avg_exposure}µs")
        print(f"Average ISO: {avg_iso}")
        print(f"\nFrame Analysis:")
        print(f"  Mean brightness: {metrics['mean']:.1f} / 255")
        print(f"  Underexposed pixels: {metrics['underexposed']:.1f}%")
        print(f"  Overexposed pixels: {metrics['overexposed']:.1f}%")
        print(f"  Quality score: {metrics['quality_score']:.1f}")
        
        # Show the frame
        display_frame = last_frame.copy()
        cv2.putText(display_frame, f"Auto-detected: {avg_exposure}us, ISO {avg_iso}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(display_frame, f"Brightness: {metrics['mean']:.1f}", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Auto-detected Settings (Press any key to continue)", display_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        print("="*60 + "\n")
        
        return avg_exposure, avg_iso


def auto_calibrate(config):
    """Automatically test different exposure settings"""
    print("\n" + "="*60)
    print("AUTO-CALIBRATION MODE")
    print("="*60)
    print("Testing different exposure combinations...")
    print("This will take about 30-60 seconds.\n")
    
    # Define test combinations (exposure_us, iso)
    test_settings = [
        (5000, 100),    # Very fast, low ISO
        (10000, 100),   # Fast, low ISO
        (15000, 200),   # Medium-fast, low-medium ISO
        (20000, 400),   # Medium, medium ISO
        (25000, 400),   # Medium-slow, medium ISO
        (30000, 800),   # Slow, high ISO
        (33000, 800),   # Very slow, high ISO
        (20000, 1600),  # Medium, very high ISO (noisy but bright)
    ]
    
    results = []
    
    for i, (exposure, iso) in enumerate(test_settings, 1):
        print(f"[{i}/{len(test_settings)}] Testing: exposure={exposure}µs, iso={iso}...", end=" ")
        
        try:
            frame = capture_test_frame(exposure, iso, config)
            metrics = analyze_frame(frame)
            
            results.append({
                'exposure': exposure,
                'iso': iso,
                'frame': frame,
                'metrics': metrics
            })
            
            print(f"✓ Mean brightness: {metrics['mean']:.1f}, Quality: {metrics['quality_score']:.1f}")
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    return results


def display_results(results):
    """Display results in a grid and let user choose"""
    print("\n" + "="*60)
    print("CALIBRATION RESULTS")
    print("="*60)
    
    # Sort by quality score
    results_sorted = sorted(results, key=lambda x: x['metrics']['quality_score'], reverse=True)
    
    print("\nTop 5 settings (by quality score):\n")
    for i, result in enumerate(results_sorted[:5], 1):
        m = result['metrics']
        print(f"{i}. Exposure: {result['exposure']:5d}µs, ISO: {result['iso']:4d}")
        print(f"   Mean brightness: {m['mean']:6.1f} | Quality score: {m['quality_score']:5.1f}")
        print(f"   Underexposed: {m['underexposed']:4.1f}% | Overexposed: {m['overexposed']:4.1f}%")
        print()
    
    # Create visual comparison
    print("Creating visual comparison window...")
    
    # Create grid of top 4 results
    grid_results = results_sorted[:4]
    
    # Resize frames for display
    display_frames = []
    for result in grid_results:
        frame = result['frame'].copy()
        # Resize to smaller size for grid
        frame = cv2.resize(frame, (640, 360))
        
        # Add text overlay
        m = result['metrics']
        text = f"Exp:{result['exposure']}us ISO:{result['iso']} | Bright:{m['mean']:.0f}"
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 255, 0), 2)
        
        display_frames.append(frame)
    
    # Create 2x2 grid
    if len(display_frames) >= 4:
        top_row = np.hstack([display_frames[0], display_frames[1]])
        bottom_row = np.hstack([display_frames[2], display_frames[3]])
        grid = np.vstack([top_row, bottom_row])
    elif len(display_frames) == 2:
        grid = np.hstack(display_frames)
    else:
        grid = display_frames[0]
    
    cv2.imshow("Calibration Results (Press any key to continue)", grid)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return results_sorted


def manual_tune(initial_exposure, initial_iso, config):
    """Interactive manual tuning mode"""
    print("\n" + "="*60)
    print("MANUAL TUNING MODE")
    print("="*60)
    print("Controls:")
    print("  W/S: Increase/Decrease exposure by 2000µs")
    print("  A/D: Decrease/Increase ISO (100, 200, 400, 800, 1600)")
    print("  Q/E: Fine adjust exposure by 500µs")
    print("  SPACE: Capture and analyze current frame")
    print("  ENTER: Accept current settings")
    print("  ESC: Cancel")
    print("="*60 + "\n")
    
    exposure = initial_exposure
    iso = initial_iso
    iso_values = [100, 200, 400, 800, 1600]
    
    # Create initial pipeline
    pipeline = dai.Pipeline()
    cam = pipeline.create(dai.node.Camera)
    cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
    
    # Set initial exposure
    cam_node.initialControl.setManualExposure(exposure, iso)
    cam_node.initialControl.setManualWhiteBalance(5000)
    
    # Configure output
    cap = dai.ImgFrameCapability()
    resolution_map = {
        "1080p": (1920, 1080),
        "4k": (3840, 2160),
        "720p": (1280, 720),
    }
    width, height = resolution_map.get(config['camera']['resolution'], (1920, 1080))
    cap.size.fixed((width, height))
    cap.fps.fixed(float(config['camera']['fps']))
    
    video_queue = cam_node.requestOutput(cap, True).createOutputQueue()
    
    # Start pipeline
    pipeline.start()
    
    # Wait for initial stabilization
    time.sleep(1.5)
    
    try:
        while True:
            # Get latest frame
            video_in = video_queue.get()
            frame = video_in.getCvFrame()
            
            # Display frame with settings
            display_frame = frame.copy()
            cv2.putText(display_frame, f"Exposure: {exposure}us | ISO: {iso}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, "Press SPACE to analyze | ENTER to accept", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Manual Tuning", display_frame)
            key = cv2.waitKey(30) & 0xFF
            
            changed = False
            
            if key == ord('w'):  # Increase exposure
                exposure = min(33000, exposure + 2000)
                changed = True
            elif key == ord('s'):  # Decrease exposure
                exposure = max(1000, exposure - 2000)
                changed = True
            elif key == ord('q'):  # Fine increase
                exposure = min(33000, exposure + 500)
                changed = True
            elif key == ord('e'):  # Fine decrease
                exposure = max(1000, exposure - 500)
                changed = True
            elif key == ord('a'):  # Decrease ISO
                current_idx = iso_values.index(iso) if iso in iso_values else 2
                if current_idx > 0:
                    iso = iso_values[current_idx - 1]
                    changed = True
            elif key == ord('d'):  # Increase ISO
                current_idx = iso_values.index(iso) if iso in iso_values else 2
                if current_idx < len(iso_values) - 1:
                    iso = iso_values[current_idx + 1]
                    changed = True
            elif key == ord(' '):  # Analyze
                metrics = analyze_frame(frame)
                print(f"\nCurrent settings: exposure={exposure}µs, iso={iso}")
                print(f"  Mean brightness: {metrics['mean']:.1f}")
                print(f"  Underexposed: {metrics['underexposed']:.1f}%")
                print(f"  Overexposed: {metrics['overexposed']:.1f}%")
                print(f"  Quality score: {metrics['quality_score']:.1f}")
            elif key == 13:  # ENTER
                cv2.destroyAllWindows()
                return exposure, iso
            elif key == 27:  # ESC
                cv2.destroyAllWindows()
                return None, None
            
            # Restart pipeline if settings changed
            if changed:
                # Close current pipeline
                cv2.destroyAllWindows()
                
                # Create new pipeline with updated settings
                pipeline = dai.Pipeline()
                cam = pipeline.create(dai.node.Camera)
                cam_node = cam.build(dai.CameraBoardSocket.CAM_A)
                
                cam_node.initialControl.setManualExposure(exposure, iso)
                cam_node.initialControl.setManualWhiteBalance(5000)
                
                cap = dai.ImgFrameCapability()
                cap.size.fixed((width, height))
                cap.fps.fixed(float(config['camera']['fps']))
                
                video_queue = cam_node.requestOutput(cap, True).createOutputQueue()
                pipeline.start()
                
                time.sleep(1.0)  # Wait for stabilization
                print(f"Updated: exposure={exposure}µs, iso={iso}")
    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        return None, None


def main():
    print("\n" + "="*60)
    print("CAMERA EXPOSURE CALIBRATION TOOL")
    print("="*60)
    
    # Load config
    config = load_config()
    
    print("\nOptions:")
    print("1. Auto-detect from camera (let camera auto-expose, then lock settings)")
    print("2. Auto-calibrate (test multiple settings automatically)")
    print("3. Manual tune (interactive adjustment)")
    print("4. Auto-detect then manual tune (recommended)")
    
    choice = input("\nSelect option (1/2/3/4): ").strip()
    
    final_exposure = None
    final_iso = None
    
    if choice == '1':
        # Auto-detect from camera's auto-exposure
        final_exposure, final_iso = auto_detect_from_camera(config)
        
        print(f"\n✓ Camera auto-detected settings:")
        print(f"  Exposure: {final_exposure}µs")
        print(f"  ISO: {final_iso}")
    
    elif choice == '2':
        # Run auto-calibration (test multiple combinations)
        results = auto_calibrate(config)
        
        if not results:
            print("❌ Auto-calibration failed. No valid results.")
            return
        
        # Display results
        sorted_results = display_results(results)
        
        # Get best result
        best = sorted_results[0]
        final_exposure = best['exposure']
        final_iso = best['iso']
        
        print(f"\n✓ Best auto-calibrated settings:")
        print(f"  Exposure: {final_exposure}µs")
        print(f"  ISO: {final_iso}")
    
    elif choice == '3':
        # Start with current config settings
        initial_exposure = config['camera'].get('exposure_time_us', 20000)
        initial_iso = config['camera'].get('iso', 800)
        
        result = manual_tune(initial_exposure, initial_iso, config)
        if result[0] is not None:
            final_exposure, final_iso = result
    
    elif choice == '4':
        # Auto-detect then manual tune
        initial_exposure, initial_iso = auto_detect_from_camera(config)
        
        print(f"\n✓ Starting manual tuning with auto-detected settings:")
        print(f"  Exposure: {initial_exposure}µs")
        print(f"  ISO: {initial_iso}")
        
        proceed = input("\nProceed to manual tuning? (y/n): ").strip().lower()
        if proceed == 'y':
            result = manual_tune(initial_exposure, initial_iso, config)
            if result[0] is not None:
                final_exposure, final_iso = result
        else:
            final_exposure, final_iso = initial_exposure, initial_iso
    
    else:
        print("Invalid choice.")
        return
    
    # Save to config
    if final_exposure is not None and final_iso is not None:
        save = input(f"\nSave settings to config.yaml? (y/n): ").strip().lower()
        if save == 'y':
            config['camera']['manual_exposure'] = True
            config['camera']['exposure_time_us'] = final_exposure
            config['camera']['iso'] = final_iso
            save_config(config)
            print(f"\n✓ Settings saved to config.yaml!")
            print(f"  exposure_time_us: {final_exposure}")
            print(f"  iso: {final_iso}")
        else:
            print("\nSettings not saved.")
    else:
        print("\nCalibration cancelled.")


if __name__ == "__main__":
    main()

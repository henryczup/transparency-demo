# Quick Start: Using IR Camera

## Step 1: Update Configuration

Edit your `config.yaml` or use the provided `config_ir_camera.yaml`:

```yaml
camera:
  type: "ir"  # Change from "oakd" to "ir"
  camera_index: 0  # Your IR camera index
  probe_indices: [0, 1, 2]  # Fallback indices to try
  resolution: "480p"
  fps: 30
```

## Step 2: Find Your Camera Index

Run the test script to discover available cameras:

```bash
python tests/test_camera_strategy.py
```

This will show you available camera indices, for example:
```
Available camera indices: [0, 1, 2]
```

## Step 3: Run Recording

### Option A: Use the IR camera config file

```bash
python main.py --config config_ir_camera.yaml
```

### Option B: Modify your existing config

1. Open `config.yaml`
2. Change `camera.type` from `"oakd"` to `"ir"`
3. Add IR camera settings:
   ```yaml
   camera:
     type: "ir"
     camera_index: 0  # Use the index from Step 2
     probe_indices: [0, 1, 2, 3]
     resolution: "480p"
     fps: 30
   ```
4. Run:
   ```bash
   python main.py
   ```

## Step 4: Verify Output

You should see:
```
============================================================
SYNCHRONIZED RECORDING SYSTEM
============================================================
Configuration loaded from: config_ir_camera.yaml
Recording duration: 60 seconds
Camera: IR - 480p @ 30 FPS
GPIO: Pin D0 (continuous mode)
============================================================

Setting up IR camera...
  Target resolution: 640x480
  Camera index: 0
  Probe indices: [0, 1, 2, 3, 4]
IR camera setup complete!
Camera setup complete!

Starting camera...
IR camera started on index 0.
  Actual resolution: 640x480
  Actual FPS: 30.0
```

## Troubleshooting

### Camera Not Found

If you see: `Cannot open IR camera. Tried indices: 0, 1, 2`

**Solutions:**
1. Check camera is connected
2. Try different indices in `probe_indices`
3. Run discovery script to find available cameras
4. On Windows, try adding backend:
   ```yaml
   camera:
     backend: 700  # cv2.CAP_DSHOW
   ```

### Wrong Camera Selected

If the wrong camera opens:

1. Find the correct index using the test script
2. Set `camera_index` to the correct value
3. Remove other indices from `probe_indices`

### Low Frame Rate

If FPS is lower than expected:

1. Reduce resolution (try "480p")
2. Check camera capabilities
3. Close other applications using the camera

## IR Data Access

The IR camera provides temperature statistics. To access them programmatically:

```python
from src.camera_factory import CameraFactory

config = {
    'type': 'ir',
    'camera_index': 0,
    'resolution': '480p',
    'fps': 30
}

camera = CameraFactory.create_camera(config)
camera.setup(config)
camera.start()

# Get IR data
min_temp, max_temp, avg_temp = camera.get_ir_data()
print(f"Temperature: {min_temp:.1f} - {max_temp:.1f} (avg: {avg_temp:.1f})")

camera.stop()
camera.cleanup()
```

## Switching Back to OAK-D

To switch back to OAK-D camera:

```yaml
camera:
  type: "oakd"  # Change back to "oakd"
  resolution: "1080p"
  fps: 30
```

## Complete Example Config

```yaml
recording:
  duration_seconds: 60
  output_directory: "./recordings"
  interval_seconds: 180
  startup_wait_seconds: 60

camera:
  type: "ir"
  camera_index: 0
  probe_indices: [0, 1, 2, 3, 4]
  resolution: "480p"
  fps: 30

gpio:
  ft232h_url: "ftdi://ftdi:232h/1"
  trigger_pin: 0
  signal_high_duration: 0.1
  signal_mode: "continuous"
  use_adbus: true

postprocessing:
  extract_frames: true
  frame_format: "jpg"
  generate_metadata: true
  frame_extraction_step: 1

transparency_analysis:
  enabled: true
  roi_selection_mode: "interactive"
  baseline_frames: 0
  visualization:
    create_plots: true
    annotate_frames: true
    plot_gpio_trigger_line: true
```

## That's It!

Your IR camera is now integrated into the workflow. All existing features (GPIO synchronization, post-processing, transparency analysis) work the same way.

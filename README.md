# Transparency Demo - Synchronized Recording System

Synchronized camera recording with GPIO triggering and difference frame analysis.

## Features

- **Multi-Camera Support**: OAK-D or IR cameras (switch via config)
- **Synchronized Recording**: Camera + GPIO trigger start simultaneously
- **Batch Recording**: Record multiple videos with intervals
- **Difference Frame Analysis**: Calculate end - start for each recording
- **Batch Averaging**: Average difference frames across batch (noise reduction)
- **Single Config File**: One unified configuration for all camera types

## Quick Start

### 1. Install

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml`:

```yaml
camera:
  type: "ir"  # Switch to "oakd" for OAK-D camera
  camera_index: 0
  
recording:
  duration_seconds: 60
  num_recordings: 3  # Batch of 3 recordings
```

### 3. Run

```bash
python main.py
```

## Configuration

The unified `config.yaml` supports both camera types. Simply change `camera.type`:

### Use IR Camera

```yaml
camera:
  type: "ir"
  camera_index: 0
  resolution: "480p"
  fps: 30
```

### Use OAK-D Camera

```yaml
camera:
  type: "oakd"
  resolution: "1080p"
  fps: 30
  manual_exposure: true
  exposure_time_us: 40000
```

### Recording Options

```yaml
recording:
  duration_seconds: 60        # Length of each recording
  num_recordings: 3           # Number of recordings in batch
  interval_seconds: 180       # Time between recordings
  startup_wait_seconds: 60    # Camera warmup time
```

## Output Structure

```
recordings/
└── batch_20251012_123000/
    ├── recording_01_*/
    │   ├── recording.mp4
    │   ├── frames/
    │   │   ├── start_frame.png
    │   │   ├── end_frame.png
    │   │   └── difference_frame_*.png
    │   └── difference_frame_raw.npy
    ├── recording_02_*/
    ├── recording_03_*/
    ├── averaged_difference_visualized.png
    ├── averaged_difference_heatmap.png
    ├── batch_analysis.json
    └── batch_report.txt
```

## Post-Processing

### Per-Recording

For each recording, calculates:
- **Difference Frame**: `end_frame - start_frame` (with configurable offsets)
- **Artifact Removal**: Skips startup/cooldown frames for clean data
- Shows what changed during the recording

**Frame Offsets:**
```yaml
postprocessing:
  start_frame_offset: 30  # Skip first 30 frames (1 sec @ 30fps)
  end_frame_offset: 30    # Skip last 30 frames (1 sec @ 30fps)
```

This ensures you're comparing stable frames without camera initialization artifacts.

### Batch-Level

Averages all difference frames:
- **Noise Reduction**: ~√N improvement (e.g., 3 recordings = 1.73x better)
- **Visualizations**: Heatmaps, channel analysis, statistics

## Usage Examples

### Single Recording

```bash
# Quick test with IR camera
python main.py
```

With config:
```yaml
recording:
  num_recordings: 1
  duration_seconds: 30
```

### Batch Recording

```bash
# 5 recordings with 2-minute intervals
python main.py
```

With config:
```yaml
recording:
  num_recordings: 5
  interval_seconds: 120
```

### Record Only (Skip Post-Processing)

```bash
python main.py --record-only
```

### Post-Process Existing Recording

```bash
python main.py --process-only ./recordings/batch_*/recording_01_*
```

## Camera Discovery

To find available IR cameras:

```python
from src.ir_camera_strategy import IRCameraStrategy

cameras = IRCameraStrategy.discover_cameras(max_index=10)
print(f"Available cameras: {cameras}")
```

Then update config:
```yaml
camera:
  camera_index: 0  # Use the index you found
```

## Hardware

- **OAK-D Camera** (optional): High-quality depth camera
- **IR Camera** (optional): Any USB camera
- **FT232H Board** (optional): For GPIO triggering
- USB connections

## Troubleshooting

### IR Camera Not Found

```yaml
camera:
  camera_index: 0
  probe_indices: [0, 1, 2, 3, 4]  # Try multiple indices
```

### OAK-D Camera Issues

```bash
python tests/reset_camera.py  # Reset if locked
```

### GPIO Not Working

- Check FT232H connection
- Windows: Use Zadig to set driver to libusbK
- System continues without GPIO if not available

## Documentation

- **`docs/CAMERA_STRATEGY_README.md`** - Camera strategy pattern details
- **`docs/POST_PROCESSING_REDESIGN.md`** - Post-processing explanation
- **`docs/QUICK_START_IR_CAMERA.md`** - IR camera quick start

## Architecture

### Strategy Pattern

The system uses the Strategy pattern for camera abstraction:

```
SynchronizedRecorder
    ↓
CameraStrategy (interface)
    ↓
├── OAKDCameraStrategy
└── IRCameraStrategy
```

Switch cameras by changing one config parameter.

### Terminology

- **Batch**: Collection of multiple recordings
- **Recording**: Single video capture
- **Difference Frame**: End frame - start frame
- **Averaged Difference**: Mean of all difference frames in batch

## License

MIT License

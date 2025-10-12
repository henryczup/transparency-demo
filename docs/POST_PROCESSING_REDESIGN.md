# Post-Processing Redesign

## Overview

The post-processing system has been completely redesigned with a simpler, more focused approach:

1. **New Terminology**: Renamed `run/session` → `batch/recording` for clarity
2. **Simplified Analysis**: Calculate difference frames (end - start) for each recording
3. **Batch Averaging**: Average all difference frames across recordings in a batch

## New Terminology

| Old Term | New Term | Description |
|----------|----------|-------------|
| Run | **Batch** | A collection of multiple recordings |
| Session | **Recording** | A single video capture |
| Run directory | **Batch directory** | e.g., `batch_20251012_121500/` |
| Session directory | **Recording directory** | e.g., `recording_01_20251012_121530/` |

## Directory Structure

```
recordings/
└── batch_20251012_121500/              # Batch directory
    ├── recording_01_20251012_121530/   # Recording 1
    │   ├── recording.mp4
    │   ├── metadata.json
    │   ├── frames/
    │   │   ├── start_frame.png
    │   │   ├── end_frame.png
    │   │   ├── difference_frame_visualized.png
    │   │   └── difference_frame_absolute.png
    │   ├── difference_frame_raw.npy
    │   └── difference_metadata.json
    ├── recording_02_20251012_121830/   # Recording 2
    │   └── ...
    ├── recording_03_20251012_122130/   # Recording 3
    │   └── ...
    ├── averaged_difference_raw.npy      # Batch-level outputs
    ├── averaged_difference_visualized.png
    ├── averaged_difference_absolute.png
    ├── averaged_difference_heatmap.png
    ├── channel_analysis/
    │   ├── blue_channel_difference.png
    │   ├── green_channel_difference.png
    │   └── red_channel_difference.png
    ├── batch_analysis.json
    └── batch_report.txt
```

## Post-Processing Workflow

### Per-Recording Processing

For each recording, the `DataPostProcessor` calculates:

1. **Difference Frame**: `end_frame - start_frame` (with configurable offsets)
   - Skips startup frames (camera initialization artifacts)
   - Skips cooldown frames (camera shutdown artifacts)
   - Uses clean, stable frames for comparison
   - Raw difference saved as `.npy` file (float32, can have negative values)
   - Visualized difference (shifted to center at gray, 0-255)
   - Absolute difference (for easier viewing)

2. **Frame Offsets** (configurable):
   - `start_frame_offset`: Skip first N frames (default: 30)
   - `end_frame_offset`: Skip last N frames (default: 30)
   - Example: 300 total frames, offsets of 30 each → uses frames 30-269 (240 clean frames)

3. **Outputs**:
   - `frames/start_frame.png` - Start frame (after offset)
   - `frames/end_frame.png` - End frame (before offset)
   - `frames/difference_frame_visualized.png` - Difference centered at gray
   - `frames/difference_frame_absolute.png` - Absolute difference
   - `difference_frame_raw.npy` - Raw float32 difference data
   - `difference_metadata.json` - Statistics including frame indices and offsets

### Batch-Level Analysis

The `BatchAnalyzer` averages all difference frames:

1. **Load** all `difference_frame_raw.npy` files from recordings
2. **Average** them together (reduces noise by ~√N)
3. **Generate visualizations**:
   - Visualized average (centered at gray)
   - Absolute average
   - Heatmap (colorized)
   - Per-channel analysis (B, G, R)

4. **Outputs**:
   - `averaged_difference_raw.npy` - Averaged difference (float32)
   - `averaged_difference_visualized.png` - Visual representation
   - `averaged_difference_absolute.png` - Absolute values
   - `averaged_difference_heatmap.png` - Jet colormap heatmap
   - `channel_analysis/` - Per-channel breakdowns
   - `batch_analysis.json` - Detailed statistics
   - `batch_report.txt` - Human-readable report

## Configuration

### Basic Configuration

```yaml
recording:
  duration_seconds: 60
  output_directory: "./recordings"
  num_recordings: 3  # Number of recordings in batch
  interval_seconds: 180  # Time between recordings
  startup_wait_seconds: 60

postprocessing:
  enabled: true
  start_frame_offset: 30  # Skip first 30 frames (startup artifacts)
  end_frame_offset: 30    # Skip last 30 frames (cooldown artifacts)
```

### Frame Offset Configuration

Control which frames are used for difference calculation:

```yaml
postprocessing:
  start_frame_offset: 30  # Skip first N frames
  end_frame_offset: 30    # Skip last N frames
```

**Why use offsets?**
- **Camera startup artifacts**: First few frames may have auto-exposure/white balance adjusting
- **Camera cooldown artifacts**: Last few frames may have shutdown effects
- **Clean data**: Use only stable, artifact-free frames for analysis

**Choosing offset values:**
- **30 FPS camera**: 30 frames = 1 second of startup/cooldown
- **60 FPS camera**: 60 frames = 1 second of startup/cooldown
- **Rule of thumb**: Skip 1-2 seconds worth of frames on each end
- **Set to 0**: Use first and last frames directly (no offset)

### Single Recording

```yaml
recording:
  duration_seconds: 60
  num_recordings: 1  # Single recording (no batch analysis)
```

## Usage

### Run Complete Workflow

```bash
python main.py --config config.yaml
```

This will:
1. Record multiple videos (batch)
2. Post-process each recording (calculate difference frames)
3. Perform batch-level analysis (average differences)

### Record Only (Skip Post-Processing)

```bash
python main.py --config config.yaml --record-only
```

### Post-Process Existing Recording

```bash
python main.py --process-only ./recordings/batch_20251012_121500/recording_01_20251012_121530
```

## Understanding the Outputs

### Difference Frame Visualization

The difference frame shows changes between start and end:

- **Gray (127)**: No change
- **Brighter than gray**: Pixel value increased
- **Darker than gray**: Pixel value decreased

### Absolute Difference

Shows magnitude of change regardless of direction:

- **Black (0)**: No change
- **White (255)**: Maximum change

### Heatmap

Color-coded visualization of change magnitude:

- **Blue**: Minimal change
- **Green/Yellow**: Moderate change
- **Red**: Maximum change

### Statistics

The `batch_analysis.json` contains:

```json
{
  "num_recordings": 3,
  "noise_reduction_factor": 1.73,
  "overall_stats": {
    "min": -45.2,
    "max": 78.9,
    "mean": 2.3,
    "std": 12.4
  },
  "channel_stats": {
    "blue": {...},
    "green": {...},
    "red": {...}
  }
}
```

## Benefits of New Approach

1. **Simplicity**: Clear, focused analysis (difference frames)
2. **Noise Reduction**: Averaging multiple recordings reduces noise
3. **Better Naming**: "Batch/Recording" is more intuitive than "Run/Session"
4. **Flexible**: Works with single recording or multiple recordings
5. **Visual**: Multiple visualization options for different insights

## Migration from Old System

### Deleted Files

- `src/transparency_analyzer.py` - Removed
- Old `src/run_analyzer.py` - Replaced with `src/batch_analyzer.py`
- Old `src/postprocessor.py` - Completely rewritten

### New Files

- `src/postprocessor.py` - New difference frame calculator
- `src/batch_analyzer.py` - New batch-level analyzer

### Breaking Changes

- Directory names changed: `run_*` → `batch_*`, `session_*` → `recording_*`
- Config parameter: `num_sessions` → `num_recordings`
- Removed transparency analysis features
- Simplified to difference frame analysis only

## Example Workflow

### 1. Configure

Edit `config.yaml`:

```yaml
recording:
  duration_seconds: 60
  num_recordings: 5  # 5 recordings in this batch
  interval_seconds: 120
```

### 2. Run

```bash
python main.py
```

### 3. Results

```
recordings/batch_20251012_143000/
├── recording_01_*/  # Difference: end - start
├── recording_02_*/  # Difference: end - start
├── recording_03_*/  # Difference: end - start
├── recording_04_*/  # Difference: end - start
├── recording_05_*/  # Difference: end - start
└── averaged_difference_*.png  # Average of all 5 differences
```

The averaged difference has ~2.24x better signal-to-noise ratio (√5) compared to a single recording.

## Technical Details

### Difference Calculation

```python
# Convert to float for proper subtraction
start_float = start_frame.astype(np.float32)
end_float = end_frame.astype(np.float32)

# Calculate difference
difference = end_float - start_float  # Can be negative

# Save raw (float32)
np.save('difference_frame_raw.npy', difference)

# Visualize (shift to center at gray)
difference_vis = np.clip(difference + 127, 0, 255).astype(np.uint8)
```

### Batch Averaging

```python
# Load all difference frames
differences = [np.load(f) for f in difference_files]

# Stack and average
stacked = np.stack(differences, axis=0)
averaged = np.mean(stacked, axis=0)

# Noise reduction factor
noise_reduction = np.sqrt(len(differences))
```

## Future Enhancements

Potential additions:

1. **Temporal analysis**: Track changes frame-by-frame
2. **ROI selection**: Focus on specific regions
3. **Statistical tests**: Significance testing across batch
4. **Comparison tools**: Compare multiple batches
5. **Export formats**: Additional output formats (CSV, HDF5, etc.)

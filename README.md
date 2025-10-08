# Transparency Demo - Synchronized OAK-D & FT232H Recording

Python project for synchronized recording from OAK-D camera with FT232H GPIO triggering and post-processing capabilities. Includes advanced transparency analysis for polymer film color change detection.

## Features

- **Synchronized Start**: Camera recording and GPIO trigger start at the exact same time
- **OAK-D Camera Support**: High-quality video recording with configurable resolution and FPS
- **FT232H GPIO Control**: Precise GPIO triggering with pulse or continuous modes
- **Timestamp Precision**: Microsecond-level timestamp tracking for all frames
- **Post-Processing Suite**: Frame extraction, metadata generation, and synchronization analysis
- **Transparency Analysis**: Measure color/transparency changes in polymer films (purple → transparent)
- **Configurable**: YAML-based configuration for easy parameter adjustment

## Hardware Requirements

- **OAK-D Camera** (any variant: OAK-D, OAK-D Lite, OAK-D Pro, etc.)
- **Adafruit FT232H Breakout Board** or compatible FTDI FT232H device
- USB connections for both devices

## Installation

### 1. Clone or navigate to project directory

```bash
cd c:\Users\henry\dev\transparency-demo
```

### 2. Create virtual environment (recommended)

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. FT232H Driver Setup (Windows)

The FT232H requires special driver setup on Windows:

1. Download and install [Zadig](https://zadig.akeo.ie/)
2. Connect your FT232H board
3. Run Zadig and select your FT232H device
4. Replace the driver with **libusbK** or **WinUSB**

## Configuration

Edit `config.yaml` to customize your recording:

```yaml
recording:
  duration_seconds: 10  # How long to record

camera:
  resolution: "1080p"   # 1080p, 4k, or 720p
  fps: 30               # Frames per second

gpio:
  trigger_pin: 0        # GPIO pin C0-C7
  signal_mode: "pulse"  # "pulse" or "continuous"
```

## Usage

### Basic Recording with Post-Processing

```bash
python main.py
```

This will:
1. Start synchronized recording from camera and GPIO
2. Save video and metadata
3. Extract frames and analyze synchronization

### Record Only (Skip Post-Processing)

```bash
python main.py --record-only
```

### Post-Process Existing Session

```bash
python main.py --process-only ./recordings/session_20251003_105720
```

### Custom Configuration File

## Output Structure

Each recording run creates a timestamped directory with multiple sessions:

```
recordings/
└── run_20251007_152200/
    ├── shared_roi.json                    # ROI shared across all sessions
    ├── run_summary.json                   # Aggregated run-level metrics
    ├── run_analysis.csv                   # Per-session comparison table
    ├── session_comparison.png             # Bar charts comparing sessions
    ├── run_timeline.png                   # Multi-session timeline plot
    ├── run_statistics.png                 # Statistical distributions
    ├── run_report.txt                     # Human-readable run summary
    ├── averaged_final_frame.png           # Noise-reduced averaged image
    ├── averaged_final_frame_annotated.png # Averaged image with annotations
    ├── averaged_image_analysis.json       # Frame info + color metrics
    ├── session_01_20251007_152205/
    │   ├── recording.mp4                  # Raw video file
    │   ├── metadata.json                  # Complete session metadata
    │   ├── frame_metadata.csv             # Per-frame timing data
    │   ├── summary_report.txt             # Human-readable summary
    │   ├── transparency_analysis.csv      # Color/transparency metrics per frame
    │   ├── transparency_summary.json      # Analysis statistics and ROI info
    │   ├── transparency_plot.png          # Visualization graphs
    │   ├── roi_visualization.png          # Before/after comparison
    │   └── frames/                        # Individual extracted frames
    │       ├── frame_000000.jpg
    │       └── ...
    ├── session_02_20251007_152235/
    │   ├── recording.mp4
    │   ├── transparency_analysis.csv      # Uses same ROI as session 01
    │   └── ...
    └── session_03_20251007_152305/
        └── ...
Columns:
- `frame_number`: Sequential frame index
- `timestamp_relative_sec`: Time from recording start
- `timestamp_relative_ms`: Same in milliseconds
- `time_from_gpio_trigger_ms`: Time offset from GPIO trigger

## GPIO Pin Modes

### Pulse Mode (Default)

Sends a brief HIGH pulse at recording start:
- Duration controlled by `signal_high_duration`
- Good for triggering external equipment
- Minimal power consumption

### Continuous Mode

Keeps GPIO HIGH for entire recording:
- Useful for gating or enabling external circuits
- Automatically turns LOW when recording stops

## Synchronization Analysis

The post-processor analyzes synchronization quality:

- **< 1ms offset**: Excellent synchronization ✓
- **< 5ms offset**: Good synchronization ✓
- **< 10ms offset**: Acceptable ⚠
- **> 10ms offset**: Poor, consider optimization ⚠

## Troubleshooting

### OAK-D Camera Not Found

```
Error: Device not found
```

**Solution**: Ensure OAK-D is connected via USB3 and drivers are installed.

### FT232H Not Detected

```
Warning: Could not initialize FT232H
```

**Solutions**:
- Check USB connection
- Verify driver is set to libusbK/WinUSB (use Zadig)
- Try different USB port
- Check `ft232h_url` in config.yaml

### Low Frame Rate

**Solutions**:
- Reduce resolution in config
- Close other applications using camera
- Check USB bandwidth (use USB3 port)

### Sync Offset Too Large

**Solutions**:
- Close background applications
- Use higher priority for Python process
- Consider using threading optimization
- Reduce recording resolution/FPS

## Transparency Analysis

### Overview

The transparency analyzer measures color/transparency changes in polymer films that transition from purple to transparent when exposed to E-field (e.g., from an antenna).

### Metrics Tracked

- **Transparency Score** (0-1): Combined metric where 0 = opaque purple, 1 = fully transparent
- **Saturation**: HSV saturation (decreases as color fades)
- **Brightness**: HSV value (increases as film becomes transparent)
- **Purple Index**: Custom metric measuring purple color intensity
- **RGB Channels**: Individual red, green, blue values
- **Luminance**: Perceived brightness

### ROI Selection Modes

**Interactive Mode** (default):
- Run analysis and click/drag to select measurement region on first session
- Visual feedback with rectangle overlay
- Press ENTER to confirm, 'r' to reset, ESC to cancel
- **ROI is automatically saved and reused for all sessions in the same run**

**Config Mode**:
```yaml
transparency_analysis:
  roi_selection_mode: "config"
  roi_coordinates:
    x: 500      # X position of top-left corner
    y: 400      # Y position of top-left corner
    width: 200  # Width of ROI
    height: 200 # Height of ROI
```

### Running Analysis

**Automatic** (during post-processing):
```bash
python main.py
```

**Standalone** (on existing session):
```bash
python analyze_transparency.py ./recordings/run_20251007_152200/session_01_20251007_152205
```

**With custom ROI**:
```bash
python analyze_transparency.py ./recordings/run_20251007_152200/session_01_20251007_152205 --roi 500,400,200,200
```

### Output Files

- **transparency_analysis.csv**: Time-series data for all metrics
- **transparency_summary.json**: Statistics including:
  - Max/min/mean transparency scores
  - Time to 50% and 90% transparency
  - Saturation and brightness change percentages
- **transparency_plot.png**: Multi-panel graph showing:
  - Transparency score over time
  - Saturation and brightness trends
  - Purple color intensity
  - GPIO trigger timing (red line)
- **roi_visualization.png**: Side-by-side before/after comparison with ROI overlay

### Configuration Options

```yaml
transparency_analysis:
  enabled: true
  roi_selection_mode: "interactive"  # or "config"
  baseline_frames: 10  # Number of initial frames for baseline
  visualization:
    create_plots: true
    annotate_frames: true
    plot_gpio_trigger_line: true
```

## Advanced Usage

### Extract Every Nth Frame

```yaml
postprocessing:
  frame_extraction_step: 5  # Extract every 5th frame
```

### Disable Transparency Analysis

```yaml
transparency_analysis:
  enabled: false
```

### Change GPIO Pin

```yaml
gpio:
  trigger_pin: 3  # Use pin D3 instead of D0
```

## Run-Level Analysis

When recording multiple sessions (e.g., 5 sessions with intervals), the system automatically performs run-level analysis to compare and aggregate results across all sessions.

### Features

- **Session Comparison**: Bar charts comparing max transparency, saturation change, etc.
- **Timeline Visualization**: All sessions plotted together on one timeline
- **Statistical Analysis**: Box plots showing distributions across sessions
- **Trend Detection**: Identifies degradation, improvement, or stability
- **Consistency Metrics**: Measures how similar sessions are to each other

### Running Run Analysis

**Automatic** (after multi-session recording):
```bash
python main.py  # Runs automatically if num_sessions > 1
```

**Standalone** (on existing run):
```bash
python scripts/analyze_run.py ./recordings/run_20251007_154637
```

### Output Files

- **run_summary.json**: Aggregated metrics and statistics
- **run_analysis.csv**: Per-session comparison table
- **session_comparison.png**: Bar charts (max transparency, saturation, brightness)
- **run_timeline.png**: Multi-session timeline showing all sessions together
- **run_statistics.png**: Box plots showing statistical distributions
- **run_report.txt**: Human-readable summary with trends and recommendations
- **averaged_final_frame.png**: Noise-reduced image averaged from all sessions
- **averaged_final_frame_annotated.png**: Averaged image with ROI overlay
- **averaged_image_analysis.json**: Combined frame info and color metrics

### Key Metrics

- **Aggregated Statistics**: Mean, std dev, min, max across all sessions
- **Consistency Score**: 0-1 score indicating session-to-session variability
- **Trend Analysis**: Linear trend detection (increasing/decreasing/stable)
- **Degradation Detection**: Flags if film response is declining over sessions

### Image Averaging (Noise Reduction)

The run analyzer automatically creates an averaged image from selected frames of each session:

**Benefits:**
- **Noise Reduction**: Averaging N images reduces random noise by ~√N
- **Cleaner Measurements**: More accurate color/transparency metrics
- **Better Visualization**: Smoother, clearer final result

**How it works:**
1. Extracts a specific frame from each session (configurable offset from end)
2. Averages all frames pixel-by-pixel
3. Analyzes the averaged image for color metrics
4. Saves both raw and annotated versions

**Configuration:**
```yaml
run_analysis:
  averaged_image:
    frame_offset_from_end: 0  # Which frame to use
    # 0 = last frame (default)
    # 5 = 5 frames before the end
    # 10 = 10 frames before the end
```

**Use cases:**
- `frame_offset_from_end: 0` - Use final frame (maximum E-field exposure)
- `frame_offset_from_end: 5` - Skip last few frames if they have artifacts
- `frame_offset_from_end: 10` - Use earlier frame for different analysis point

**Example:** With 5 sessions, noise is reduced by ~2.2x, giving you much cleaner measurements

## API Reference

### SynchronizedRecorder

```python
from src.synchronized_recorder import SynchronizedRecorder

recorder = SynchronizedRecorder(config)
session_dir = recorder.record()
```

### DataPostProcessor

```python
from src.postprocessor import DataPostProcessor

processor = DataPostProcessor(session_dir, config)
processor.extract_frames()
processor.generate_frame_metadata()
processor.analyze_synchronization()
processor.run_transparency_analysis()
```
### TransparencyAnalyzer

```python
from src.transparency_analyzer import TransparencyAnalyzer

analyzer = TransparencyAnalyzer(session_dir, config, metadata, run_dir)
analyzer.analyze_frames()
analyzer.save_results()
analyzer.create_visualizations()
```

### RunAnalyzer

```python
from src.run_analyzer import RunAnalyzer

run_analyzer = RunAnalyzer(run_dir, config)
run_analyzer.discover_sessions()
run_analyzer.load_session_summaries()
run_analyzer.calculate_run_metrics()
run_analyzer.create_comparison_plots()
run_analyzer.create_timeline_plot()
```

## License

MIT License

## Support
For issues or questions, please check:
- OAK-D Documentation: https://docs.luxonis.com/
- PyFTDI Documentation: https://eblot.github.io/pyftdi/

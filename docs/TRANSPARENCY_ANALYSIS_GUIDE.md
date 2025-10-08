# Transparency Analysis Guide

## Overview

This guide explains how to use the transparency analysis feature to measure color and transparency changes in polymer films that transition from purple to transparent when exposed to electromagnetic fields.

## Quick Start

### 1. Record a Session

```bash
python main.py
```

This will:
- Record video with synchronized GPIO triggering
- Extract frames automatically
- Run transparency analysis with interactive ROI selection
- Generate plots and statistics

### 2. Select Your Measurement Region (Once Per Run)

**Important:** When recording multiple sessions in a run, you only need to select the ROI once!

When prompted on the **first session**, the first frame will appear:
1. **Click and drag** to draw a rectangle around the area you want to measure
2. **Press ENTER** to confirm your selection
3. **Press 'r'** to reset and redraw if needed
4. **Press ESC** to cancel

The ROI will be automatically saved to the run directory and **reused for all subsequent sessions** in the same run.

**Tips for ROI Selection:**
- Choose a region with uniform purple color in the baseline
- Avoid edges or areas with shadows
- A 200x200 pixel square is usually sufficient
- Place it where you expect maximum E-field exposure
- Make sure it's in a location that's consistent across all sessions

### 3. Review Results

After analysis completes, check your session directory for:

```
session_01_20251007_152205/
├── transparency_plot.png          # Main visualization
├── roi_visualization.png          # Before/after comparison
├── transparency_analysis.csv      # Detailed metrics
└── transparency_summary.json      # Statistics
```

## Output Structure

Each recording run creates a timestamped directory with multiple sessions:

```
recordings/
└── run_20251007_152200/
    ├── shared_roi.json                    # ROI shared across all sessions
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
```

**Note:** The `shared_roi.json` file is created after the first session's ROI selection and is automatically used by all subsequent sessions in the same run.

## Understanding the Metrics

### Transparency Score (0-1)

The primary metric combining saturation and brightness changes:
- **0.0** = Fully opaque purple (baseline)
- **0.5** = Half transparent
- **1.0** = Fully transparent

**Formula:**
```
transparency_score = 0.6 × saturation_change + 0.4 × brightness_change
```

### Saturation

HSV saturation value (0-255):
- **High saturation** = Vivid purple color
- **Low saturation** = Faded/gray appearance
- **Decreases** as film becomes transparent

### Brightness (Value)

HSV value/brightness (0-255):
- **Low brightness** = Dark appearance
- **High brightness** = Light appearance
- **Increases** as more light passes through

### Purple Index

Custom metric measuring purple color intensity:
- Combines hue deviation from purple (140° in OpenCV HSV) with saturation
- **High value** = Strong purple color
- **Low value** = Color has faded

### Key Statistics

From `transparency_summary.json`:

- **max_transparency_score**: Peak transparency reached
- **final_transparency_score**: Transparency at end of recording
- **time_to_50_percent_transparency_sec**: Response time to half-transparent
- **time_to_90_percent_transparency_sec**: Response time to mostly transparent
- **saturation_change_percent**: How much color faded (%)
- **brightness_change_percent**: How much brightness increased (%)

## Visualization Guide

### transparency_plot.png

Three-panel graph showing:

**Panel 1: Transparency Score**
- Blue line: Transparency score over time
- Red dashed line: 50% threshold
- Orange dashed line: 90% threshold
- Vertical red line: GPIO trigger moment

**Panel 2: Saturation and Brightness**
- Purple line: Saturation (left axis)
- Gold line: Brightness (right axis)
- Shows inverse relationship as film changes

**Panel 3: Purple Index**
- Magenta line: Purple color intensity
- Tracks overall color strength

### roi_visualization.png

Side-by-side comparison:
- **Left**: First frame (baseline, opaque purple)
- **Right**: Last frame (after E-field exposure)
- Green rectangle shows measurement region
- Transparency scores displayed on each frame

## Advanced Usage

### Using Config-Based ROI

If you know the exact coordinates you want to measure:

1. Edit `config.yaml`:
```yaml
transparency_analysis:
  roi_selection_mode: "config"
  roi_coordinates:
    x: 640      # Center of 1920x1080 frame
    y: 440
    width: 200
    height: 200
```

2. Run analysis:
```bash
python main.py
```

No interactive selection needed!

### Analyzing Existing Sessions

Already have recorded sessions? Run analysis separately:

```bash
# Interactive ROI selection
python analyze_transparency.py ./recordings/run_20251007_152200/session_01_20251007_152205

# Specify ROI via command line
python analyze_transparency.py ./recordings/run_20251007_152200/session_01_20251007_152205 --roi 640,440,200,200

# Use config mode
python analyze_transparency.py ./recordings/run_20251007_152200/session_01_20251007_152205 --roi-mode config
```

### Batch Processing Multiple Sessions

Process all sessions in a run:

```bash
# Windows PowerShell
Get-ChildItem ./recordings/run_20251007_152200/session_* | ForEach-Object {
    python analyze_transparency.py $_.FullName --roi 640,440,200,200
}
```

### Adjusting Baseline Calculation

The baseline (reference for "fully opaque") is calculated from initial frames:

```yaml
transparency_analysis:
  baseline_frames: 10  # Average first 10 frames
```

**Recommendations:**
- **10 frames** (default): Good for most cases
- **20-30 frames**: If initial frames are noisy
- **5 frames**: If E-field activates very quickly

### Customizing Visualizations

```yaml
transparency_analysis:
  visualization:
    create_plots: true              # Generate graphs
    annotate_frames: true           # Create before/after images
    plot_gpio_trigger_line: true   # Show trigger timing
```

## Interpreting Results

### Good Response Pattern

Characteristics of a successful measurement:
- ✓ Transparency score increases smoothly
- ✓ Saturation decreases steadily
- ✓ Brightness increases steadily
- ✓ Clear correlation with GPIO trigger timing
- ✓ Final transparency score > 0.7

### Troubleshooting Poor Results

**Problem: Transparency score stays near 0**
- Film may not be responding to E-field
- Check antenna power and positioning
- Verify GPIO trigger is activating correctly

**Problem: Noisy/erratic measurements**
- ROI may include shadows or edges
- Try selecting a more uniform region
- Increase baseline_frames for better reference

**Problem: Transparency decreases over time**
- ROI may be affected by lighting changes
- Check for camera auto-exposure issues
- Ensure consistent lighting conditions

**Problem: Very fast saturation (< 1 second)**
- May be too fast to measure accurately
- Increase camera FPS in config
- Consider shorter recording duration with higher frame rate

## Data Export and Analysis

### CSV Format

`transparency_analysis.csv` contains per-frame data:

| Column | Description |
|--------|-------------|
| frame_number | Sequential frame index |
| timestamp | Time from recording start (seconds) |
| transparency_score | Main metric (0-1) |
| mean_saturation | Average HSV saturation in ROI |
| mean_value | Average HSV brightness in ROI |
| mean_hue | Average HSV hue in ROI |
| purple_index | Purple color intensity |
| mean_r, mean_g, mean_b | RGB channel averages |
| luminance | Perceived brightness |
| std_saturation, std_value, std_hue | Uniformity metrics |

### Importing to Excel/Python

**Excel:**
1. Open Excel
2. Data → From Text/CSV
3. Select `transparency_analysis.csv`
4. Create charts from columns

**Python/Pandas:**
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('transparency_analysis.csv')

# Plot custom metrics
plt.figure(figsize=(10, 6))
plt.plot(df['timestamp'], df['transparency_score'])
plt.xlabel('Time (s)')
plt.ylabel('Transparency Score')
plt.title('Custom Analysis')
plt.show()

# Calculate custom statistics
response_time = df[df['transparency_score'] >= 0.5].iloc[0]['timestamp']
print(f"50% transparency reached at {response_time:.3f} seconds")
```

## Best Practices

### Experimental Setup

1. **Consistent lighting**: Use controlled lighting to avoid shadows
2. **Stable camera**: Mount camera securely to prevent movement
3. **Baseline period**: Allow 1-2 seconds before GPIO trigger
4. **Multiple trials**: Record multiple sessions for statistical analysis
5. **ROI consistency**: Use config mode for same ROI across trials

### Data Quality

1. **Frame rate**: 30 FPS is usually sufficient; use 60 FPS for fast changes
2. **Resolution**: 1080p provides good detail without excessive file size
3. **ROI size**: 200x200 pixels balances detail and noise reduction
4. **Recording duration**: Capture full transition plus 2-3 seconds after

### Analysis Workflow

1. **Initial test**: Run one session with interactive ROI to find optimal region
2. **Note coordinates**: Record ROI coordinates from `transparency_summary.json`
3. **Production runs**: Use config mode with fixed ROI for consistency
4. **Batch analysis**: Process multiple sessions with same ROI
5. **Compare results**: Use CSV data to analyze trends across sessions

## Example Use Cases

### Measuring E-Field Response Time

Goal: Determine how quickly film responds to antenna activation

1. Record with GPIO trigger synchronized to antenna
2. Analyze transparency score vs. time
3. Extract `time_to_50_percent_transparency_sec` from summary
4. Compare across different antenna powers or frequencies

### Comparing Film Samples

Goal: Test different polymer formulations

1. Use identical ROI coordinates for all samples
2. Record under same conditions (power, distance, duration)
3. Compare final transparency scores
4. Analyze saturation change percentages

### Spatial Uniformity Analysis

Goal: Measure if film changes uniformly

1. Define multiple ROIs in config (center, edges, corners)
2. Run analysis on each ROI
3. Compare transparency scores across regions
4. Identify areas of maximum/minimum response

### Reversibility Testing

Goal: Check if film returns to purple after E-field removal

1. Record longer session with GPIO pulse mode
2. Analyze transparency during and after pulse
3. Look for transparency score decrease after trigger ends
4. Calculate recovery time and final state

## Troubleshooting

### "No frames found in directory"

**Solution:** Run frame extraction first:
```bash
python main.py --record-only  # Record without processing
python main.py --process-only ./recordings/run_XXX/session_XX  # Process later
```

### "ROI selection cancelled"

**Solution:** 
- Make sure you press ENTER after drawing rectangle
- Try using config mode instead
- Check that frames directory contains valid images

### "Analysis results empty"

**Solution:**
- Verify frames were extracted successfully
- Check that ROI coordinates are within frame bounds
- Ensure frame files are readable (not corrupted)

### Matplotlib display issues

**Solution:**
```bash
# Install matplotlib backend
pip install matplotlib pillow

# Or disable visualization
# In config.yaml:
transparency_analysis:
  visualization:
    create_plots: false
```

## FAQ

**Q: What purple hue should my film be?**  
A: The analyzer is tuned for purple around 270-290° (standard hue), which is 135-145° in OpenCV's HSV space. Most purple polymer films fall in this range.

**Q: Can I analyze other color transitions?**  
A: Yes! Modify the `purple_hue_center` variable in `transparency_analyzer.py` line 170 to match your target color.

**Q: How accurate is the transparency score?**  
A: It's a relative metric (0-1) based on your baseline. Absolute accuracy depends on lighting consistency and ROI selection.

**Q: Can I analyze multiple ROIs simultaneously?**  
A: Currently, you need to run analysis multiple times with different ROI coordinates. Batch processing support is planned.

**Q: What if my film doesn't return to purple?**  
A: The analysis measures the transition during recording. For reversibility, record a longer session and analyze the full time series.

**Q: How do I export data for publication?**  
A: Use the CSV file for raw data and the PNG plots for figures. All metrics are documented for methods sections.

## Support

For issues or questions:
- Check the main README.md
- Review example output in recordings directory
- Examine the transparency_summary.json for diagnostic info

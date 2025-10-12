# Frame Offset Guide

## Overview

Frame offsets allow you to exclude camera startup and cooldown artifacts from your difference frame analysis, ensuring you're comparing clean, stable frames.

## Problem: Camera Artifacts

### Startup Artifacts (First Few Frames)
- **Auto-exposure adjusting**: Brightness changes as camera finds optimal exposure
- **Auto-white balance adjusting**: Color shifts as camera calibrates
- **Sensor initialization**: Electronic noise or instability
- **Focus settling**: Slight blur or sharpness changes

### Cooldown Artifacts (Last Few Frames)
- **Shutdown effects**: Camera may change settings before stopping
- **Buffer flushing**: Last frames may be incomplete or corrupted
- **Timing issues**: Final frames may have irregular timestamps

## Solution: Frame Offsets

Skip problematic frames at the beginning and end of your recording:

```yaml
postprocessing:
  start_frame_offset: 30  # Skip first 30 frames
  end_frame_offset: 30    # Skip last 30 frames
```

## Visual Example

### Without Offsets (Default: 0, 0)

```
Recording: 300 frames total (10 seconds @ 30 fps)

Frame:  0   1   2  ...  297  298  299
        ↑                          ↑
     START                       END
     (may have artifacts)    (may have artifacts)

Difference = Frame 299 - Frame 0
```

### With Offsets (30, 30)

```
Recording: 300 frames total (10 seconds @ 30 fps)

Frame:  0 ... 29  30  31 ... 268  269  270 ... 299
        [SKIP]    ↑              ↑      [SKIP]
                START           END
             (stable)        (stable)

Difference = Frame 269 - Frame 30
Frames analyzed: 240 clean frames
```

## Configuration Examples

### Conservative (1 second buffer)

For 30 FPS camera:
```yaml
postprocessing:
  start_frame_offset: 30  # 1 second
  end_frame_offset: 30    # 1 second
```

For 60 FPS camera:
```yaml
postprocessing:
  start_frame_offset: 60  # 1 second
  end_frame_offset: 60    # 1 second
```

### Aggressive (2 second buffer)

For 30 FPS camera:
```yaml
postprocessing:
  start_frame_offset: 60  # 2 seconds
  end_frame_offset: 60    # 2 seconds
```

### Minimal (0.5 second buffer)

For 30 FPS camera:
```yaml
postprocessing:
  start_frame_offset: 15  # 0.5 seconds
  end_frame_offset: 15    # 0.5 seconds
```

### No Offsets (Use all frames)

```yaml
postprocessing:
  start_frame_offset: 0
  end_frame_offset: 0
```

## Choosing Offset Values

### Step 1: Calculate Frame Rate

```
Frames per second (FPS) = 30  # From your config
```

### Step 2: Decide Buffer Time

How many seconds of startup/cooldown to skip?
- **0.5 seconds**: Minimal, for very stable cameras
- **1 second**: Recommended for most cases
- **2 seconds**: Conservative, for cameras with slow auto-adjustments

### Step 3: Calculate Offset

```
offset = FPS × buffer_time_seconds

Examples:
- 30 FPS × 1 sec = 30 frames
- 30 FPS × 2 sec = 60 frames
- 60 FPS × 1 sec = 60 frames
```

### Step 4: Verify Sufficient Frames Remain

```
frames_analyzed = total_frames - start_offset - end_offset

Example:
- Total frames: 300
- Start offset: 30
- End offset: 30
- Frames analyzed: 300 - 30 - 30 = 240 ✓ (plenty remaining)
```

**Warning**: If offsets are too large, you'll get an error:
```
Error: Invalid frame offsets. Start offset (150) + end offset (150) exceed total frames (300)
```

## Real-World Example

### Scenario
- Recording duration: 10 seconds
- Camera FPS: 30
- Total frames: 300
- Camera has noticeable auto-exposure in first second

### Configuration
```yaml
recording:
  duration_seconds: 10

camera:
  fps: 30

postprocessing:
  start_frame_offset: 30  # Skip first 1 second
  end_frame_offset: 30    # Skip last 1 second (for symmetry)
```

### Result
```
Total frames: 300
Start frame: 30 (at 1.0 seconds)
End frame: 269 (at 8.97 seconds)
Frames analyzed: 240 (8 seconds of clean data)
```

## Output Metadata

The `difference_metadata.json` file shows which frames were used:

```json
{
  "start_frame_index": 30,
  "end_frame_index": 269,
  "start_frame_offset": 30,
  "end_frame_offset": 30,
  "total_frames": 300,
  "frames_analyzed": 240,
  "difference_stats": {
    "min": -45.2,
    "max": 78.9,
    "mean": 2.3,
    "std": 12.4
  }
}
```

## Best Practices

### 1. Start Conservative
Begin with 1-2 seconds of offset, then reduce if needed:
```yaml
start_frame_offset: 60  # 2 seconds @ 30fps
end_frame_offset: 60
```

### 2. Check Your Camera
Record a test video and inspect the first/last frames:
- Do colors shift in the first second?
- Does brightness change?
- Are there any visible artifacts?

### 3. Match Your Use Case
- **High precision needed**: Use larger offsets (2 seconds)
- **Long recordings**: Smaller offsets are fine (0.5 seconds)
- **Short recordings**: Be careful not to offset too much

### 4. Symmetric Offsets
Use the same value for start and end for consistency:
```yaml
start_frame_offset: 30
end_frame_offset: 30  # Same as start
```

### 5. Document Your Choice
Add a comment explaining your offset choice:
```yaml
postprocessing:
  # Using 1 second offset to avoid auto-exposure adjustment
  # observed in first 30 frames during testing
  start_frame_offset: 30
  end_frame_offset: 30
```

## Troubleshooting

### Error: "Invalid frame offsets exceed total frames"

**Problem**: Your offsets are too large for the recording duration.

**Solution**: Reduce offsets or increase recording duration:
```yaml
# Option 1: Reduce offsets
postprocessing:
  start_frame_offset: 15  # Reduced from 30
  end_frame_offset: 15

# Option 2: Increase recording duration
recording:
  duration_seconds: 20  # Increased from 10
```

### Warning: Very few frames analyzed

If you see:
```
Frames analyzed: 50
```

This might be too few for good analysis. Increase recording duration or reduce offsets.

### Difference looks wrong

If the difference frame shows unexpected results:
1. Check the saved `start_frame.png` and `end_frame.png`
2. Verify they're the frames you expect
3. Adjust offsets if needed

## Summary

Frame offsets are a simple but powerful tool to ensure clean, artifact-free difference frame analysis:

- **Skip startup artifacts**: First N frames
- **Skip cooldown artifacts**: Last N frames
- **Get clean data**: Only stable frames used
- **Easy to configure**: Just two numbers in config
- **Automatic validation**: System checks for valid offsets

**Recommended starting point:**
```yaml
postprocessing:
  start_frame_offset: 30  # 1 second @ 30fps
  end_frame_offset: 30    # 1 second @ 30fps
```

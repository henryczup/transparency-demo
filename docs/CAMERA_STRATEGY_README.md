# Camera Strategy Pattern Implementation

## Overview

This project now supports multiple camera types through the **Strategy Pattern**. You can easily switch between different camera implementations (OAK-D, IR camera, etc.) by simply changing the configuration file.

## Architecture

### Strategy Pattern Components

1. **`CameraStrategy` (Abstract Base Class)** - `src/camera_strategy.py`
   - Defines the interface that all camera implementations must follow
   - Methods: `setup()`, `start()`, `stop()`, `get_frame()`, `is_running()`, `get_frame_dimensions()`, `cleanup()`
   - Optional method: `get_ir_data()` for IR-specific functionality

2. **`OAKDCameraStrategy`** - `src/oakd_camera_strategy.py`
   - Concrete implementation for OAK-D cameras
   - Wraps the existing DepthAI functionality
   - Supports manual exposure, white balance, and high-resolution capture

3. **`IRCameraStrategy`** - `src/ir_camera_strategy.py`
   - Concrete implementation for IR cameras
   - Uses OpenCV's VideoCapture for camera access
   - Supports camera index probing and IR data extraction
   - Provides `get_ir_data()` method for temperature statistics

4. **`CameraFactory`** - `src/camera_factory.py`
   - Factory class that creates the appropriate camera strategy
   - Selects implementation based on `camera.type` in config

5. **`SynchronizedRecorder`** - `src/synchronized_recorder.py`
   - Updated to use camera strategies instead of direct OAK-D implementation
   - Camera-agnostic recording logic

## Supported Camera Types

### 1. OAK-D Camera (`type: "oakd"`)

High-quality depth camera with advanced features.

**Configuration Example:**
```yaml
camera:
  type: "oakd"
  resolution: "1080p"  # Options: "1080p", "4k", "720p"
  fps: 30
  manual_exposure: true
  exposure_time_us: 40000
  iso: 100
  manual_white_balance: false
  white_balance_temp: 5000
```

**Features:**
- High resolution (up to 4K)
- Manual exposure control
- Manual white balance
- Hardware-accelerated processing

### 2. IR Camera (`type: "ir"`)

Generic IR camera support via OpenCV.

**Configuration Example:**
```yaml
camera:
  type: "ir"
  resolution: "480p"  # Options: "1080p", "4k", "720p", "480p"
  fps: 30
  camera_index: 0  # Specific camera to use
  probe_indices: [0, 1, 2, 3, 4]  # Fallback indices to try
  # backend: null  # Optional OpenCV backend
```

**Features:**
- Automatic camera discovery
- Camera index probing
- IR data extraction (min/max/avg temperature)
- Cross-platform support

## Usage

### Using OAK-D Camera

```bash
python main.py --config config.yaml
```

The default `config.yaml` is configured for OAK-D.

### Using IR Camera

```bash
python main.py --config config_ir_camera.yaml
```

Or modify your config file:
```yaml
camera:
  type: "ir"
  camera_index: 0
  probe_indices: [0, 1, 2]
  resolution: "480p"
  fps: 30
```

### Discovering Available Cameras

To find available IR camera indices:

```python
from src.ir_camera_strategy import IRCameraStrategy

# Discover cameras
available = IRCameraStrategy.discover_cameras(max_index=10)
print(f"Available camera indices: {available}")
```

## IR Camera Features

### Temperature Data Extraction

The IR camera strategy provides a `get_ir_data()` method that returns temperature statistics:

```python
camera = IRCameraStrategy()
camera.setup(config)
camera.start()

# Get IR data
min_temp, max_temp, avg_temp = camera.get_ir_data()
print(f"Temperature range: {min_temp} - {max_temp}, Average: {avg_temp}")
```

**Note:** The current implementation uses grayscale pixel values as a proxy for temperature. For actual temperature readings, you would need to integrate with your IR camera's SDK.

## Adding New Camera Types

To add support for a new camera type:

1. **Create a new strategy class** that inherits from `CameraStrategy`:

```python
from src.camera_strategy import CameraStrategy

class MyNewCameraStrategy(CameraStrategy):
    def setup(self, config: dict) -> None:
        # Initialize your camera
        pass
    
    def start(self) -> None:
        # Start capture
        pass
    
    def stop(self) -> None:
        # Stop capture
        pass
    
    def get_frame(self) -> Optional[np.ndarray]:
        # Return frame as BGR numpy array
        pass
    
    def is_running(self) -> bool:
        # Return running status
        pass
    
    def get_frame_dimensions(self) -> Tuple[int, int]:
        # Return (width, height)
        pass
    
    def cleanup(self) -> None:
        # Cleanup resources
        pass
```

2. **Register in the factory** (`src/camera_factory.py`):

```python
def create_camera(config: dict) -> CameraStrategy:
    camera_type = config.get('type', 'oakd').lower()
    
    if camera_type == 'oakd':
        return OAKDCameraStrategy()
    elif camera_type == 'ir':
        return IRCameraStrategy()
    elif camera_type == 'mynewcamera':
        return MyNewCameraStrategy()
    else:
        raise ValueError(f"Unsupported camera type: {camera_type}")
```

3. **Update configuration** to use the new type:

```yaml
camera:
  type: "mynewcamera"
  # Your camera-specific settings
```

## Benefits of Strategy Pattern

1. **Flexibility**: Easy to switch between camera types
2. **Extensibility**: Add new camera types without modifying existing code
3. **Maintainability**: Each camera implementation is isolated
4. **Testability**: Mock camera strategies for testing
5. **Separation of Concerns**: Recording logic is independent of camera implementation

## Configuration Files

- `config.yaml` - Default configuration (OAK-D camera)
- `config_ir_camera.yaml` - Example configuration for IR camera

## Troubleshooting

### IR Camera Not Found

If the IR camera is not detected:

1. Check camera connection
2. Try different camera indices (0, 1, 2, etc.)
3. Use the discovery function to find available cameras
4. On Windows, try setting the backend:
   ```yaml
   camera:
     backend: 700  # cv2.CAP_DSHOW
   ```

### OAK-D Camera Issues

If OAK-D camera fails:

1. Ensure camera is connected via USB 3.0
2. Run `python tests/reset_camera.py` if device is locked
3. Check that DepthAI drivers are installed

## Example: IR Camera Code

The IR camera implementation provided in your request has been integrated as `IRCameraStrategy`. Here's how it maps:

| Original Code | Strategy Implementation |
|--------------|------------------------|
| `Camera.__init__()` | `IRCameraStrategy.__init__()` |
| `Camera.start()` | `IRCameraStrategy.start()` |
| `Camera.stop()` | `IRCameraStrategy.stop()` |
| `Camera.get_frame()` | `IRCameraStrategy.get_frame()` |
| `Camera.get_ir_data()` | `IRCameraStrategy.get_ir_data()` |
| `Camera.discover_cameras()` | `IRCameraStrategy.discover_cameras()` |

All functionality from your original IR camera code has been preserved and integrated into the strategy pattern.

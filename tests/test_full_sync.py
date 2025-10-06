"""
Full Synchronization Test - Simulates main.py recording with oscilloscope capture
"""
import time
from pyftdi.gpio import GpioAsyncController
import threading

print("Full Synchronization Test")
print("=" * 60)
print("This simulates the synchronized recording start.")
print("Oscilloscope will capture the exact trigger timing.")
print("=" * 60)

def trigger_gpio(gpio, config):
    """Trigger function matching synchronized_recorder.py"""
    # Record exact trigger time
    trigger_time = time.time()
    
    # Set pin HIGH
    pin = config['trigger_pin']
    gpio.write(1 << pin)
    print(f"  GPIO trigger sent on pin C{pin} at t={trigger_time:.6f}")
    
    # Hold for duration if pulse mode
    if config['signal_mode'] == "pulse":
        time.sleep(config['signal_high_duration'])
        gpio.write(0x00)
        print(f"  GPIO pulse completed")
    
    return trigger_time

try:
    # Configure USB backend for Windows
    try:
        import usb.backend.libusb1
        import libusb_package
        backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        import os
        os.environ['PYUSB_BACKEND'] = str(backend)
    except ImportError:
        pass
    
    # Setup GPIO
    gpio = GpioAsyncController()
    gpio.configure("ftdi://ftdi:232h/1", direction=0xFF)
    gpio.write(0x00)  # Start LOW
    
    print("\n✓ Connected to FT232H")
    print("\nOscilloscope Setup:")
    print("  - CH1: FT232H pin C0 + GND")
    print("  - Trigger: Rising edge, 1.5V, Single mode")
    print("  - Time scale: 100μs/div (to see rise time)")
    print("  - Voltage scale: 1V/div")
    
    # Configuration (matching config.yaml)
    config = {
        'trigger_pin': 0,
        'signal_mode': 'continuous',  # or 'pulse'
        'signal_high_duration': 0.1
    }
    
    duration = 5  # 5 second recording
    
    print(f"\nTest parameters:")
    print(f"  - Signal mode: {config['signal_mode']}")
    print(f"  - Duration: {duration} seconds")
    
    input("\nArm oscilloscope trigger, then press ENTER...")
    
    print("\nSynchronizing in 3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    
    # SYNCHRONIZED START (matches synchronized_recorder.py lines 172-179)
    print("\n=== RECORDING STARTED ===")
    start_time = time.time()
    camera_start_time = start_time
    print(f"Camera start time: {camera_start_time:.6f}")
    
    # Trigger GPIO in parallel thread (for maximum synchronization)
    gpio_thread = threading.Thread(target=trigger_gpio, args=(gpio, config))
    gpio_thread.start()
    
    # Simulate recording loop
    print(f"\nRecording for {duration} seconds...")
    time.sleep(duration)
    
    # Stop recording
    print("\n=== RECORDING STOPPED ===")
    end_time = time.time()
    
    # Turn off GPIO if continuous mode
    if config['signal_mode'] == 'continuous':
        gpio.write(0x00)
        print("GPIO signal turned OFF")
    
    gpio_thread.join()
    
    # Calculate sync offset (would normally come from metadata.json)
    print(f"\nTiming Analysis:")
    print(f"  Total duration: {end_time - start_time:.3f} seconds")
    print(f"  Expected sync offset: < 1ms (check oscilloscope)")
    
    gpio.close()
    print("\n✓ Test complete")
    print("\nOn oscilloscope, measure:")
    print("  1. Rise time (10% to 90%)")
    print("  2. Time from trigger to stable HIGH")
    print("  3. Any overshoot or ringing")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\nTest cancelled")
    gpio.write(0x00)
    gpio.close()
    
except Exception as e:
    print(f"\n✗ Error: {e}")

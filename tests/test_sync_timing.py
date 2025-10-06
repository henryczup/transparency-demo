"""
Synchronization Timing Test - Single trigger for oscilloscope capture
"""
import time
from pyftdi.gpio import GpioAsyncController

print("Synchronization Timing Test")
print("=" * 60)
print("This will send a SINGLE trigger pulse after countdown.")
print("Use oscilloscope in SINGLE trigger mode to capture.")
print("=" * 60)

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
    
    print("\n✓ Connected to FT232H")
    print("\nOscilloscope Setup:")
    print("  - CH1: Connect to FT232H pin C0 and GND")
    print("  - Trigger: Rising edge, 1.5V, Single mode")
    print("  - Time scale: 1ms/div")
    print("  - Voltage scale: 1V/div")
    print("\nArm your oscilloscope trigger (press SINGLE button)")
    input("\nPress ENTER when oscilloscope is ready...")
    
    # Set pin LOW initially
    gpio.write(0x00)
    
    print("\nCountdown to trigger:")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    
    # TRIGGER EVENT - Record exact time
    print("\n=== TRIGGER SENT ===")
    trigger_time = time.time()
    gpio.write(0x01)  # Set C0 HIGH
    
    print(f"Trigger timestamp: {trigger_time:.6f}")
    
    # Keep HIGH for 5 seconds (continuous mode simulation)
    print("\nHolding HIGH for 5 seconds...")
    time.sleep(5)
    
    # Turn OFF
    gpio.write(0x00)
    print("Trigger turned OFF")
    
    gpio.close()
    print("\n✓ Test complete - check oscilloscope capture")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\nTest cancelled")
    gpio.write(0x00)
    gpio.close()
    
except Exception as e:
    print(f"\n✗ Error: {e}")

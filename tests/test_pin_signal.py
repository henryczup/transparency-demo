"""
Manual GPIO Pin Test - Toggle pin HIGH/LOW to verify signal
"""
import time
from pyftdi.gpio import GpioAsyncController

print("FT232H Pin Signal Test")
print("=" * 60)
print("This will toggle pin C0 HIGH and LOW repeatedly.")
print("Use a multimeter or LED to verify the signal.")
print("Press Ctrl+C to stop.")
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
        pass  # Backend will use default
    
    # Setup GPIO
    gpio = GpioAsyncController()
    gpio.configure("ftdi://ftdi:232h/1", direction=0xFF)
    
    print("\n✓ Connected to FT232H")
    print("\nStarting pin toggle test on C0...")
    print("Expected: ~3.3V when HIGH, ~0V when LOW\n")
    
    # Set all pins LOW initially
    gpio.write(0x00)
    time.sleep(1)
    
    cycle = 1
    while True:
        # Set pin C0 HIGH
        print(f"Cycle {cycle}: Pin C0 → HIGH (should see ~3.3V)")
        gpio.write(0x01)  # Binary: 00000001 (C0 HIGH)
        time.sleep(2)
        
        # Set pin C0 LOW
        print(f"Cycle {cycle}: Pin C0 → LOW (should see ~0V)")
        gpio.write(0x00)  # Binary: 00000000 (all LOW)
        time.sleep(2)
        
        cycle += 1

except KeyboardInterrupt:
    print("\n\nTest stopped by user")
    gpio.write(0x00)  # Ensure pin is LOW
    gpio.close()
    print("✓ Pin set to LOW and connection closed")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Run: python test_gpio.py")
    print("2. Check FT232H connection")
    print("3. Verify driver setup (Zadig on Windows)")

"""
FT232H Voltage Level Diagnostic
"""
import time
from pyftdi.gpio import GpioAsyncController

print("FT232H Voltage Level Diagnostic")
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
    print("\nDiagnostic Information:")
    print("  - FT232H should output 3.3V logic levels")
    print("  - Current measurement: 2.4V (LOW)")
    print("\nPossible issues:")
    print("  1. Insufficient USB power")
    print("  2. Load connected to pin (resistor/LED)")
    print("  3. Weak pull-down on pin")
    
    print("\n" + "=" * 60)
    print("Setting all pins HIGH...")
    print("Measure voltage on pin C0 with multimeter")
    print("=" * 60)
    
    # Set all pins HIGH
    gpio.write(0xFF)  # All pins HIGH
    
    print("\n✓ All pins set to HIGH (0xFF)")
    print("\nWith multimeter, measure voltage on pin C0:")
    print("  Expected: 3.3V")
    print("  Your reading: 2.4V")
    
    print("\nChecklist:")
    print("  [ ] Is anything connected to pin C0? (disconnect it)")
    print("  [ ] Is USB cable good quality? (try different cable)")
    print("  [ ] Is USB port providing enough power? (try different port)")
    print("  [ ] Are you measuring between C0 and GND? (not C0 and VCC)")
    
    input("\nPress ENTER to set pins LOW and exit...")
    
    # Set all pins LOW
    gpio.write(0x00)
    gpio.close()
    
    print("\n✓ Pins set to LOW and connection closed")
    
except Exception as e:
    print(f"\n✗ Error: {e}")

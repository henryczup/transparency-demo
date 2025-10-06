"""
Test if RESET mode keeps pins LOW after closing
"""
from pyftdi.ftdi import Ftdi
import time

print("Testing RESET mode to keep pins OFF")
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
    
    print("\nStep 1: Opening device and setting bitbang mode...")
    ftdi = Ftdi()
    ftdi.open_from_url("ftdi://ftdi:232h/1")
    ftdi.set_bitmode(0xFF, Ftdi.BitMode.BITBANG)
    ftdi.write_data(bytes([0x00]))  # All pins LOW
    print("  Pins set to LOW in bitbang mode")
    input("  → Measure D0 (should be 0V), press ENTER...")
    
    print("\nStep 2: Resetting to UART mode (tri-state)...")
    ftdi.set_bitmode(0x00, Ftdi.BitMode.RESET)
    time.sleep(0.1)
    print("  Reset to UART mode")
    input("  → Measure D0 now, press ENTER...")
    
    print("\nStep 3: Closing device...")
    ftdi.close()
    print("  Device closed")
    input("  → Measure D0 now (should still be 0V or floating), press ENTER...")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("\nWhat voltage did you measure at Step 3?")
    print("  - If 0V or floating: RESET mode works! ✓")
    print("  - If 3.3V: Pin still goes HIGH (hardware pull-up)")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

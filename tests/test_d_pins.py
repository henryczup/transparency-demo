"""
Test D pins (ADBUS) - Should output 3.3V
"""
import time
from pyftdi.ftdi import Ftdi

print("FT232H D-Pin (ADBUS) Test")
print("=" * 60)
print("Testing D pins which output proper 3.3V logic levels")
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
    
    # Use FTDI interface for ADBUS (D pins) control
    ftdi = Ftdi()
    ftdi.open_from_url("ftdi://ftdi:232h/1")
    
    # Configure ADBUS pins as outputs (all 8 pins)
    # Direction: 1=output, 0=input
    # 0xFF = all outputs
    direction = 0xFF
    ftdi.set_bitmode(direction, Ftdi.BitMode.BITBANG)
    
    print("\n✓ Connected to FT232H (ADBUS mode)")
    print("\nPin mapping:")
    print("  D0 (ADBUS0) = Pin 0")
    print("  D1 (ADBUS1) = Pin 1")
    print("  D2 (ADBUS2) = Pin 2")
    print("  ... etc")
    
    print("\nSetting D0 HIGH...")
    ftdi.write_data(bytes([0x01]))  # D0 HIGH, all others LOW
    
    print("\n✓ D0 set to HIGH")
    print("\nMeasure voltage on D0 pin:")
    print("  Expected: 3.3V")
    print("  Should be correct now!")
    
    input("\nPress ENTER to toggle D0 on/off...")
    
    print("\nToggling D0 for 10 seconds...")
    for i in range(5):
        print(f"Cycle {i+1}: D0 HIGH")
        ftdi.write_data(bytes([0x01]))
        time.sleep(1)
        print(f"Cycle {i+1}: D0 LOW")
        ftdi.write_data(bytes([0x00]))
        time.sleep(1)
    
    # Clean up
    ftdi.write_data(bytes([0x00]))
    ftdi.close()
    
    print("\n✓ Test complete")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

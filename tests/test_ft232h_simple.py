"""
Simple FT232H connection test
"""
import sys

print("FT232H Quick Test")
print("=" * 50)

# Test connection
try:
    from pyftdi.gpio import GpioAsyncController
    import usb.backend.libusb1
    import libusb_package
    
    # Setup backend
    backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    
    print("\nAttempting connection to FT232H...")
    gpio = GpioAsyncController()
    gpio.configure("ftdi://ftdi:232h/1", direction=0xFF)
    
    print("✓ SUCCESS: Connected to FT232H!")
    print("✓ GPIO controller initialized")
    
    # Test write
    gpio.write(0x00)
    print("✓ Test write successful")
    
    gpio.close()
    print("✓ Connection closed")
    print("\n" + "=" * 50)
    print("FT232H is working correctly!")
    
except Exception as e:
    print(f"\n✗ FAILED: {e}")
    print("\nPossible issues:")
    print("1. WinUSB driver not installed (use Zadig)")
    print("2. Device not connected")
    print("3. Device in use by another program")
    print("\n" + "=" * 50)
    sys.exit(1)

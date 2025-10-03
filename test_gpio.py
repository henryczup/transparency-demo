"""
Test script for FT232H GPIO connection
"""
import sys

print("Testing FT232H GPIO Setup...")
print("=" * 60)

# Test 1: Check pyftdi installation
print("\n1. Checking pyftdi installation...")
try:
    import pyftdi
    print(f"   ✓ pyftdi version: {pyftdi.__version__}")
except ImportError as e:
    print(f"   ✗ pyftdi not installed: {e}")
    sys.exit(1)

# Test 2: Check USB backend
print("\n2. Checking USB backend...")
try:
    import usb.core
    import usb.backend.libusb1
    
    # Try to find libusb DLL from libusb-package
    backend = None
    try:
        import libusb_package
        backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        print(f"   ✓ libusb backend loaded from libusb-package: {backend}")
    except:
        backend = usb.backend.libusb1.get_backend()
        if backend:
            print(f"   ✓ libusb backend available: {backend}")
    
    if backend is None:
        print("   ✗ libusb backend not available")
        print("   → Trying alternative method...")
except ImportError as e:
    print(f"   ✗ pyusb not installed: {e}")
    print("   → Install with: pip install pyusb libusb-package")

# Test 3: List USB devices
print("\n3. Scanning for USB devices...")
try:
    import usb.core
    import libusb_package
    
    # Use libusb-package backend explicitly
    backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
    devices = list(usb.core.find(find_all=True, backend=backend))
    print(f"   Found {len(devices)} USB devices")
    
    # Look for FTDI devices
    ftdi_devices = [d for d in devices if d.idVendor == 0x0403]
    if ftdi_devices:
        print(f"   ✓ Found {len(ftdi_devices)} FTDI device(s):")
        for dev in ftdi_devices:
            print(f"     - Vendor: 0x{dev.idVendor:04x}, Product: 0x{dev.idProduct:04x}")
    else:
        print("   ✗ No FTDI devices found")
        print("   → Check if FT232H is connected")
except Exception as e:
    print(f"   ✗ Error scanning devices: {e}")

# Test 4: Try to connect to FT232H
print("\n4. Attempting FT232H connection...")
try:
    from pyftdi.gpio import GpioAsyncController
    
    gpio = GpioAsyncController()
    gpio.configure("ftdi://ftdi:232h/1", direction=0xFF)
    
    print("   ✓ Successfully connected to FT232H!")
    print("   ✓ GPIO controller initialized")
    
    # Test write
    gpio.write(0x00)
    print("   ✓ Test write successful")
    
    gpio.close()
    print("   ✓ Connection closed cleanly")
    
except Exception as e:
    print(f"   ✗ Connection failed: {e}")
    print("\n   Troubleshooting steps:")
    print("   1. Install USB backend: pip install pyusb libusb-package")
    print("   2. Check FT232H is connected via USB")
    print("   3. On Windows, you may need Zadig to install WinUSB driver")
    print("   4. Try different USB ports (prefer USB 2.0)")

print("\n" + "=" * 60)
print("Test complete!")

"""
Utility script to reset OAK-D camera connection
Run this if you get "device already in use" errors
"""
import depthai as dai
import time

print("OAK-D Camera Reset Utility")
print("=" * 50)

# List all devices
devices = dai.Device.getAllAvailableDevices()
print(f"\nFound {len(devices)} device(s):")
for i, dev_info in enumerate(devices):
    print(f"  Device {i}: {dev_info.name}")
    print(f"    State: {dev_info.state}")

if not devices:
    print("\nNo devices found. Please check:")
    print("  1. Camera is connected via USB")
    print("  2. USB cable is working (try USB 3.0 port)")
    print("  3. Camera has power (LED should be on)")
    exit(1)

print("\nAttempting to reset connection...")

# Try to connect and immediately close
try:
    device = dai.Device()
    print("✓ Connected successfully")
    device.close()
    print("✓ Device closed")
    
    # Wait for device to fully release
    print("\nWaiting for device to fully release...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    print("\n✓ Camera reset complete! You can now run main.py")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nManual reset steps:")
    print("  1. Unplug the OAK-D camera")
    print("  2. Wait 5 seconds")
    print("  3. Plug it back in")
    print("  4. Wait for Windows to recognize it")
    print("  5. Run this script again")

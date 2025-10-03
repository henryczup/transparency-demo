# Installing WinUSB Driver for FT232H

Your FT232H is detected but needs the WinUSB driver to work with pyftdi.

## Steps to Install WinUSB Driver

### 1. Download Zadig
- Go to: https://zadig.akeo.ie/
- Download the latest version (zadig-2.8.exe or newer)
- **No installation needed** - it's a portable executable

### 2. Run Zadig as Administrator
- Right-click `zadig.exe`
- Select "Run as administrator"

### 3. Configure Zadig
1. In Zadig menu: **Options** → **List All Devices** ✓
2. From the dropdown, select your FTDI device:
   - Look for: **"FT232H"** or **"USB Serial Converter"**
   - Should show: `USB ID 0403:6014`

### 4. Install WinUSB Driver
1. In the driver selection box (middle), choose: **WinUSB**
2. Click the **"Replace Driver"** or **"Install Driver"** button
3. Wait for installation to complete (may take 1-2 minutes)
4. You should see "Driver installed successfully"

### 5. Verify Installation
After installing the driver:

```powershell
python test_gpio.py
```

You should now see:
```
4. Attempting FT232H connection...
   ✓ Successfully connected to FT232H!
   ✓ GPIO controller initialized
```

## Troubleshooting

### Device not showing in Zadig
- Unplug and replug the FT232H
- Try a different USB port
- Make sure "List All Devices" is checked

### Driver installation fails
- Make sure Zadig is running as Administrator
- Close any programs that might be using the device
- Restart your computer and try again

### Still getting errors after driver install
- Unplug the FT232H and plug it back in
- Restart your computer
- Try a USB 2.0 port instead of USB 3.0

## Reverting to Original Driver (if needed)

If you need to revert to the original FTDI driver:
1. Open Device Manager
2. Find the device under "Universal Serial Bus devices"
3. Right-click → Uninstall device
4. Check "Delete the driver software"
5. Unplug and replug the device
6. Windows will reinstall the original driver

## Current Status

✓ pyftdi installed (v0.57.1)
✓ libusb backend working
✓ FT232H detected (0403:6014)
⚠ WinUSB driver needed ← **YOU ARE HERE**

Once you complete the Zadig installation, your GPIO interface will be fully functional!

"""
GPIO Timing Mode - Run GPIO trigger cycles without camera
Useful for testing external device timing and synchronization
"""

import yaml
import time
from pathlib import Path
from datetime import datetime
from pyftdi.gpio import GpioAsyncController
from pyftdi.ftdi import Ftdi


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path("config.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_gpio(config):
    """Initialize FT232H GPIO controller"""
    print("Setting up FT232H GPIO...")
    
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
        
        # Check if we should use ADBUS (D pins, 3.3V) or ACBUS (C pins, 2.4V)
        use_adbus = config['gpio'].get('use_adbus', False)
        
        if use_adbus:
            # Use ADBUS (D pins) for proper 3.3V output
            gpio = Ftdi()
            gpio.open_from_url(config['gpio']['ft232h_url'])
            gpio.set_bitmode(0xFF, Ftdi.BitMode.BITBANG)
            gpio.write_data(bytes([0x00]))
            gpio_mode = 'adbus'
            print("✓ FT232H GPIO setup complete (ADBUS/D-pins, 3.3V)!")
        else:
            # Use ACBUS (C pins) - may output lower voltage
            gpio = GpioAsyncController()
            gpio.configure(
                config['gpio']['ft232h_url'],
                direction=0xFF  # All pins as output
            )
            gpio.write(0x00)
            gpio_mode = 'acbus'
            print("✓ FT232H GPIO setup complete (ACBUS/C-pins)!")
        
        return gpio, gpio_mode
    
    except Exception as e:
        print(f"Warning: Could not initialize FT232H: {e}")
        print("Continuing in simulation mode (no actual GPIO output)...")
        return None, None


def set_gpio_high(gpio, gpio_mode, pin):
    """Set GPIO pin HIGH"""
    if gpio is None:
        return
    
    pin_mask = 1 << pin
    
    if gpio_mode == 'adbus':
        gpio.write_data(bytes([pin_mask]))
    else:
        gpio.write(pin_mask)


def set_gpio_low(gpio, gpio_mode):
    """Set all GPIO pins LOW"""
    if gpio is None:
        return
    
    if gpio_mode == 'adbus':
        gpio.write_data(bytes([0x00]))
    else:
        gpio.write(0x00)


def run_gpio_timing(config, num_cycles=None):
    """Run GPIO timing cycles"""
    
    # Get timing parameters
    duration_seconds = config['recording']['duration_seconds']
    interval_seconds = config['recording']['interval_seconds']
    startup_wait = config['recording'].get('startup_wait_seconds', 0)
    trigger_pin = config['gpio']['trigger_pin']
    signal_mode = config['gpio'].get('signal_mode', 'continuous')
    
    # Setup GPIO
    gpio, gpio_mode = setup_gpio(config)
    
    print("\n" + "="*60)
    print("GPIO TIMING MODE")
    print("="*60)
    print(f"GPIO Pin: D{trigger_pin}")
    print(f"Signal Mode: {signal_mode}")
    print(f"ON Duration: {duration_seconds} seconds")
    print(f"OFF Interval: {interval_seconds} seconds")
    if num_cycles:
        print(f"Number of Cycles: {num_cycles}")
    else:
        print("Number of Cycles: Infinite (press Ctrl+C to stop)")
    print("="*60 + "\n")
    
    # Startup wait
    if startup_wait > 0:
        print(f"⏳ Startup wait: {startup_wait} seconds...")
        time.sleep(startup_wait)
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            
            if num_cycles and cycle > num_cycles:
                break
            
            # GPIO ON phase
            print(f"\n{'='*60}")
            print(f"CYCLE {cycle}")
            print(f"{'='*60}")
            print(f"🟢 GPIO HIGH - {datetime.now().strftime('%H:%M:%S')}")
            
            set_gpio_high(gpio, gpio_mode, trigger_pin)
            
            # Count down during ON phase
            for remaining in range(duration_seconds, 0, -1):
                print(f"  ON: {remaining}s remaining...", end='\r')
                time.sleep(1)
            
            print(f"  ON: Complete!     ")
            
            # Check if this is the last cycle
            if num_cycles and cycle >= num_cycles:
                print(f"🔴 GPIO LOW - {datetime.now().strftime('%H:%M:%S')}")
                set_gpio_low(gpio, gpio_mode)
                break
            
            # GPIO OFF phase
            print(f"🔴 GPIO LOW - {datetime.now().strftime('%H:%M:%S')}")
            set_gpio_low(gpio, gpio_mode)
            
            # Count down during OFF phase
            for remaining in range(interval_seconds, 0, -1):
                print(f"  OFF: {remaining}s until next cycle...", end='\r')
                time.sleep(1)
            
            print(f"  OFF: Complete!     ")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    finally:
        # Ensure GPIO is LOW when exiting
        print(f"\n🔴 Setting GPIO LOW...")
        set_gpio_low(gpio, gpio_mode)
        
        if gpio:
            if gpio_mode == 'adbus':
                gpio.close()
        
        print("\n" + "="*60)
        print(f"GPIO TIMING COMPLETE")
        print(f"Total cycles completed: {cycle}")
        print("="*60)


def main():
    print("\n" + "="*60)
    print("GPIO TIMING MODE")
    print("="*60)
    print("This mode runs GPIO trigger cycles without the camera.")
    print("Useful for testing external device timing.\n")
    
    # Load config
    config = load_config()
    
    # Ask for number of cycles
    print("How many cycles do you want to run?")
    print("  Enter a number (e.g., 5)")
    print("  Or press ENTER for infinite cycles (stop with Ctrl+C)")
    
    user_input = input("\nNumber of cycles: ").strip()
    
    if user_input == "":
        num_cycles = None
    else:
        try:
            num_cycles = int(user_input)
            if num_cycles <= 0:
                print("Invalid number. Must be positive.")
                return
        except ValueError:
            print("Invalid input. Must be a number or empty.")
            return
    
    # Run timing cycles
    run_gpio_timing(config, num_cycles)


if __name__ == "__main__":
    main()

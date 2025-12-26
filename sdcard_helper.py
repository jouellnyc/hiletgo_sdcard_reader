#For testing / etc
#sdcard_helper

import busio			
import sdcardio
import storage
import os
import time

import sd_config

_spi = None
_sd = None
_vfs = None
_mounted = False
_last_print_time = 0  # Add this at module level with other globals


def mount():
    """Initialize SPI and mount the SD card."""
    global _spi, _sd, _vfs, _mounted
    
    if _mounted:
        print("✓ SD card already mounted")
        return True
    
    print("Initializing SD card...")
    
    try:
        # Initialize SPI
        _spi = busio.SPI(
            clock=sd_config.SD_SCK,
            MOSI=sd_config.SD_MOSI,
            MISO=sd_config.SD_MISO,
        )
        
        # Create SD card + filesystem
        _sd = sdcardio.SDCard(
            _spi,
            sd_config.SD_CS,
            baudrate=sd_config.SD_BAUDRATE,
        )
        _vfs = storage.VfsFat(_sd)
        storage.mount(_vfs, sd_config.SD_MOUNT)
        
        # CRITICAL: Let SD card settle after mount
        import time
        print("Waiting for SD card to stabilize...")
        time.sleep(1.0)
        
        # Prime the directory cache with a dummy read
        print("Initializing directory cache...")
        try:
            _ = os.listdir(sd_config.SD_MOUNT)
        except:
            pass  # Ignore errors on first read
        
        os.sync()
        time.sleep(0.5)
        
    except OSError as e:
        print(f"✗ Mount failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check SD card is inserted properly")
        print("2. Ensure SD card is FAT32 formatted")
        print("3. Try different CS pin")
        print("4. Check wiring connections")
        print("5. Verify VCC is 3.3V (NOT 5V)")
        print("6. Try slower baudrate (100000)")
        return False
    else:
        _mounted = True
        print("✓ SD card mounted successfully!")
        return True

def print_info():
    """Print SD card size and file list."""
    global _last_print_time
    
    if not _mounted:
        print("✗ SD card not mounted")
        return False
    
    # Rate limiting: enforce 250ms minimum between calls
    current_time = time.monotonic()
    time_since_last = current_time - _last_print_time
    
    if _last_print_time > 0 and time_since_last < 0.25:
        wait_time = 0.25 - time_since_last
        print(f"[Rate limit: waiting {wait_time:.2f}s...]")
        time.sleep(wait_time)
    
    _last_print_time = time.monotonic()
    
    # Read operations
    stats = os.statvfs(sd_config.SD_MOUNT)
    total_mb = (stats[0] * stats[2]) / (1024 * 1024)
    free_mb = (stats[0] * stats[3]) / (1024 * 1024)
    used_mb = total_mb - free_mb
    
    print("\nSD Card:")
    print(f"  Total: {total_mb:.2f} MB")
    print(f"  Used:  {used_mb:.2f} MB")
    print(f"  Free:  {free_mb:.2f} MB")
    
    print("\nFiles:")
    files = os.listdir(sd_config.SD_MOUNT)
    if files:
        for f in files:
            print(f"  - {f}")
    else:
        print("  (empty)")
    
    return True



def test_sd(slow=False, count=60, interval=1):
    """
    Test SD card read/write.

    slow=False  → single quick write/read (default)
    slow=True   → repeated writes (default: 60 times, 1s interval)
    """

    if not _mounted:
        print("✗ SD card not mounted")
        return False

    path = sd_config.SD_MOUNT + "/test.txt"

    try:
        if not slow:
            print("\nTesting write...")
            with open(path, "w") as f:
                f.write("Hello from ESP32-S3!\n")
            print("✓ Write successful")

            print("Testing read...")
            with open(path, "r") as f:
                content = f.read()
                print(f"✓ Read successful: {content.strip()}")

            return True

        # -------------------------------
        # Slow test
        # -------------------------------
        print(f"\nStarting slow SD test ({count} writes, {interval}s interval)")

        for i in range(count):
            with open(path, "a") as f:
                f.write(f"Slow test {i+1}/{count}\n")

            print(f"  ✓ Write {i+1}/{count}")
            time.sleep(interval)

        print("✓ Slow SD test completed successfully")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


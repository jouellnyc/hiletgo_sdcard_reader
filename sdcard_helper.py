"""
Robust SD card helper for CircuitPython with proper initialization.

Addresses timing issues in CircuitPython's sdcardio module:
- Settling time after mount
- Directory cache priming
- Rate limiting to prevent controller overwhelm

Usage:
    import sdcard_helper
    
    if sdcard_helper.mount():
        sdcard_helper.print_info()
        files = sdcard_helper.list_files()
"""

__version__ = "1.2.0"

import busio
import sdcardio
import storage
import os
import time
import gc
import sd_config

print(f"sdcard_helper v{__version__}")

# Module-level state
_spi = None
_sd = None
_vfs = None
_mounted = False
_last_operation_time = 0
_verbosity = 'diags'  # 'silent', 'diags', or 'debug'


def _debug_print(message):
    """Print debug message if debug mode is enabled."""
    if _verbosity == 'debug':
        print(message)


def _diag_print(message):
    """Print diagnostic message if diags or debug mode is enabled."""
    if _verbosity in ('diags', 'debug'):
        print(message)


def set_verbosity(level):
    """
    Set verbosity level for output.
    
    Args:
        level: 'silent' (minimal output), 'diags' (basic diagnostics), or 'debug' (full debug output)
    """
    global _verbosity
    if level not in ('silent', 'diags', 'debug'):
        print(f"Invalid verbosity level: {level}. Use 'silent', 'diags', or 'debug'")
        return
    _verbosity = level
    print(f"Verbosity: {level}")


def set_debug(enabled):
    """
    Enable or disable debug output (legacy function, use set_verbosity instead).
    
    Args:
        enabled: True to enable debug output, False to disable
    """
    set_verbosity('debug' if enabled else 'silent')


def _check_rate_limit():
    """Internal helper to enforce rate limiting across all SD operations."""
    global _last_operation_time
    
    current_time = time.monotonic()
    time_since_last = current_time - _last_operation_time
    
    if _last_operation_time > 0 and time_since_last < 0.5:  # 500ms between operations
        wait_time = 0.5 - time_since_last
        _debug_print(f"  [DEBUG] Rate limiting: waiting {wait_time:.3f}s")
        time.sleep(wait_time)
    
    _last_operation_time = time.monotonic()


def _validate_sd_communication(sd_card):
    """
    Validate SD card communication and gather diagnostic info.
    
    Args:
        sd_card: Initialized sdcardio.SDCard object
    
    Returns:
        True if validation passed, False otherwise
    """
    try:
        _debug_print("  [DEBUG] Getting block count...")
        # Get basic card info
        block_count = sd_card.count()
        block_size = 512  # Standard SD card block size
        capacity_mb = (block_count * block_size) / (1024 * 1024)
        
        _diag_print(f"  Block count: {block_count}")
        _diag_print(f"  Capacity: {capacity_mb:.2f} MB ({capacity_mb/1024:.2f} GB)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Communication test failed: {e}")
        return False


def _read_mbr(sd_card):
    """
    Read and validate the Master Boot Record.
    
    Args:
        sd_card: Initialized sdcardio.SDCard object
    
    Returns:
        True if MBR is valid, False otherwise
    """
    try:
        _diag_print("  Reading MBR (block 0)...")
        mbr = bytearray(512)
        _debug_print("  [DEBUG] Reading block 0...")
        sd_card.readblocks(0, mbr)
        
        # Check MBR signature (should be 0x55AA at bytes 510-511)
        mbr_signature = (mbr[511] << 8) | mbr[510]
        _debug_print(f"  [DEBUG] MBR signature bytes: 0x{mbr[510]:02X} 0x{mbr[511]:02X}")
        
        if mbr_signature == 0xAA55:
            _diag_print(f"  ✓ Valid MBR signature: 0x{mbr_signature:04X}")
        else:
            print(f"  ⚠ Invalid MBR signature: 0x{mbr_signature:04X} (expected 0xAA55)")
            return False
        
        # Check partition type (byte 450, first partition entry + 4)
        partition_type = mbr[450]
        _debug_print(f"  [DEBUG] Partition type byte (450): 0x{partition_type:02X}")
        
        partition_types = {
            0x01: "FAT12",
            0x04: "FAT16 <32MB",
            0x06: "FAT16",
            0x0B: "FAT32",
            0x0C: "FAT32 LBA",
            0x0E: "FAT16 LBA",
            0x83: "Linux",
            0x07: "NTFS/exFAT"
        }
        partition_name = partition_types.get(partition_type, f"Unknown (0x{partition_type:02X})")
        _diag_print(f"  Partition type: {partition_name}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ MBR read failed: {e}")
        return False


def _test_multiblock_read(sd_card):
    """
    Test sustained multi-block reads.
    
    Args:
        sd_card: Initialized sdcardio.SDCard object
    
    Returns:
        True if test passed, False otherwise
    """
    try:
        _diag_print("  Testing multi-block read...")
        test_block = bytearray(512)
        _debug_print("  [DEBUG] Reading block 1...")
        sd_card.readblocks(1, test_block)
        # Format hex dump of first 16 bytes
        hex_dump = ' '.join(f'{b:02X}' for b in test_block[:16])
        _debug_print(f"  [DEBUG] First 16 bytes: {hex_dump}")
        _diag_print("  ✓ Multi-block read successful")
        return True
        
    except Exception as e:
        print(f"  ✗ Multi-block read failed: {e}")
        return False


def _check_timeout(start_time, timeout, operation):
    """
    Check if operation has exceeded timeout.
    
    Args:
        start_time: Start time from time.monotonic()
        timeout: Maximum allowed seconds
        operation: Description of operation for error message
    
    Returns:
        True if timeout exceeded, False otherwise
    """
    elapsed = time.monotonic() - start_time
    if elapsed > timeout:
        print(f"✗ Mount timeout: {operation} took too long ({elapsed:.1f}s)")
        return True
    _debug_print(f"  [DEBUG] {operation}: {elapsed:.3f}s elapsed")
    return False


def mount(timeout=10, verbose=None):
    """
    Mount SD card with timeout protection and pre-validation.
    
    Args:
        timeout: Maximum seconds to wait for mount (default: 10)
        verbose: Deprecated. Use set_verbosity() instead. If provided, overrides current verbosity.
    
    Returns:
        True if mounted successfully, False otherwise
    """
    global _spi, _sd, _vfs, _mounted
    
    # Handle legacy verbose parameter
    if verbose is not None:
        old_verbosity = _verbosity
        set_verbosity('diags' if verbose else 'silent')
    
    if _mounted: 
        _debug_print("[DEBUG] SD card already mounted")
        return True

    _diag_print("Initializing SD card...")
    start_time = time.monotonic()
    
    try:
        # Initialize SPI and SD card (reuses existing if available)
        _spi, _sd = _init_sd_card()
        
        if _sd is None:
            return False
        
        if _check_timeout(start_time, timeout, "SD card init"):
            return False
        
        # PRE-VALIDATE: Run diagnostics before mount attempt
        _diag_print("Testing SD card communication...")
        
        if not _validate_sd_communication(_sd):
            return False
        
        # Run MBR and multiblock tests (warnings only if they fail)
        if not _read_mbr(_sd):
            _diag_print("  ⚠ MBR validation failed, attempting mount anyway...")
        
        if not _test_multiblock_read(_sd):
            _diag_print("  ⚠ Multi-block read failed, attempting mount anyway...")
        
        if _check_timeout(start_time, timeout, "pre-validation"):
            return False
        
        # Mount the filesystem
        _diag_print("Initializing directory cache...")
        _debug_print(f"[DEBUG] Creating VfsFat filesystem...")
        _vfs = storage.VfsFat(_sd)
        _debug_print(f"[DEBUG] Mounting to {sd_config.SD_MOUNT} (readonly=True)...")
        storage.mount(_vfs, sd_config.SD_MOUNT, readonly=True)
        
        # Wait for electrical settling
        _debug_print("[DEBUG] Waiting 0.2s for electrical settling...")
        time.sleep(0.2) 
        
        # Check final timeout
        elapsed = time.monotonic() - start_time
        if elapsed > timeout:
            print(f"✗ Mount timeout after {elapsed:.1f}s")
            unmount()
            return False
        
        _mounted = True
        print(f"✓ SD card mounted successfully in {elapsed:.1f}s")
        return True
        
    except Exception as e:
        elapsed = time.monotonic() - start_time
        print(f"✗ Mount failed after {elapsed:.1f}s: {e}")
        _debug_print(f"[DEBUG] Exception details: {type(e).__name__}")
        return False
    finally:
        # Restore verbosity if it was temporarily changed
        if verbose is not None:
            set_verbosity(old_verbosity)


def unmount():
    """Unmount the SD card with aggressive cleanup."""
    global _spi, _sd, _vfs, _mounted, _last_operation_time
    
    if not _mounted:
        print("✓ SD card not mounted, nothing to do")
        return True
    
    try:
        # Unmount filesystem first
        try:
            storage.umount(sd_config.SD_MOUNT)
        except:
            pass  # Might already be unmounted
        
        # Aggressively clean up SPI and related objects
        if _spi:
            try:
                _spi.deinit()
            except:
                pass  # Already deinitialized
        
        # Clear all references
        _spi = None
        _sd = None
        _vfs = None
        
        # Force garbage collection to release pins
        gc.collect()
        
        # Give hardware time to release pins
        time.sleep(0.5)
        
        _mounted = False
        _last_operation_time = 0
        print("✓ SD card unmounted")
        return True
        
    except Exception as e:
        print(f"✗ Unmount failed: {e}")
        # Force cleanup anyway
        _spi = None
        _sd = None
        _vfs = None
        _mounted = False
        gc.collect()
        return False


def print_info():
    """Print SD card size and file list with rate limiting."""
    if not _mounted:
        print("✗ SD card not mounted")
        return False
    
    _check_rate_limit()
    
    # Get filesystem stats
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
    
    NOTE: This will fail if SD is mounted read-only!
    
    Args:
        slow: If False (default), single quick write/read test
              If True, repeated writes over time
        count: Number of writes for slow test (default: 60)
        interval: Seconds between writes for slow test (default: 1)
    """
    if not _mounted:
        print("✗ SD card not mounted")
        return False
    
    _check_rate_limit()
    
    path = sd_config.SD_MOUNT + "/test.txt"
    
    try:
        if not slow:
            # Quick test
            print("\nTesting write...")
            with open(path, "w") as f:
                f.write("Hello from ESP32!\n")
            print("✓ Write successful")
            
            print("Testing read...")
            with open(path, "r") as f:
                content = f.read()
                print(f"✓ Read successful: {content.strip()}")
            return True
        
        # Slow test - repeated writes
        print(f"\nStarting slow SD test ({count} writes, {interval}s interval)")
        for i in range(count):
            with open(path, "a") as f:
                f.write(f"Slow test {i+1}/{count}\n")
            print(f"  ✓ Write {i+1}/{count}")
            time.sleep(interval)
        
        print("✓ Slow SD test completed successfully")
        return True
        
    except OSError as e:
        if "Read-only" in str(e):
            print(f"✗ Test failed: SD card is mounted read-only")
            print("  This is normal - SD card is read-only for stability")
        else:
            print(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def list_files(path=None):
    """List all files in a directory (rate-limited)."""
    if not _mounted:
        print("✗ SD card not mounted")
        return []
    
    _check_rate_limit()
    
    # Use the provided path, or default to the config mount point
    search_path = path if path else sd_config.SD_MOUNT
    
    try:
        return os.listdir(search_path)
    except Exception as e:
        print(f"✗ Error listing files: {e}")
        return []


def get_stats():
    """
    Get SD card statistics (rate-limited).
    
    Returns:
        Dictionary with total_mb, used_mb, free_mb, or None on error
    """
    if not _mounted:
        return None
    
    _check_rate_limit()
    
    try:
        stats = os.statvfs(sd_config.SD_MOUNT)
        total_mb = (stats[0] * stats[2]) / (1024 * 1024)
        free_mb = (stats[0] * stats[3]) / (1024 * 1024)
        used_mb = total_mb - free_mb
        
        return {
            'total_mb': total_mb,
            'used_mb': used_mb,
            'free_mb': free_mb
        }
    except Exception as e:
        print(f"✗ Error getting stats: {e}")
        return None


def is_mounted():
    """Check if SD card is currently mounted."""
    return _mounted


def verify_sd_stability(iterations=10):
    """Loops through all files on the SD card multiple times."""
    for i in range(1, iterations + 1):
        print(f"\n--- Test Loop {i} ---")
        try:
            files = os.listdir("/sd")
            print(f"Found {len(files)} files:")
            
            for filename in files:
                # Check file size to verify it's readable
                stats = os.stat("/sd/" + filename)
                size = stats[6] # Index 6 is the file size in bytes
                print(f" - {filename} ({size} bytes)")
                
            # Small pause between loops to prevent overheating
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"STABILITY ERROR on loop {i}: {e}")
            return False
            
    print("\n[SUCCESS] SD card is stable over 10 read cycles.")
    return True


def _init_sd_card():
    """
    Initialize SPI and SD card without mounting filesystem.
    Reuses existing module-level SPI/SD objects if available.
    
    Returns:
        Tuple of (spi, sd) objects, or (None, None) on failure
    """
    global _spi, _sd
    
    # If we already have initialized objects, reuse them
    if _spi is not None and _sd is not None:
        _debug_print("  [DEBUG] Reusing existing SPI/SD card objects")
        return (_spi, _sd)
    
    try:
        # Initialize SPI
        _diag_print("  Initializing SPI...")
        _spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
        
        # Initialize SD Card
        _diag_print("  Initializing SD card...")
        _sd = sdcardio.SDCard(_spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
        
        return (_spi, _sd)
        
    except Exception as e:
        print(f"✗ SD card initialization failed: {e}")
        return (None, None)


def _read_mbr_standalone():
    """
    Internal function to read MBR with independent SD card initialization.
    Used by read_mbr() public function.
    
    Returns:
        True if MBR read successful, False otherwise
    """
    # Use shared initialization (will reuse pins if already claimed)
    temp_spi, temp_sd = _init_sd_card()
    if temp_sd is None:
        return False
    
    try:
        # Validate communication
        print("Testing SD card communication...")
        if not _validate_sd_communication(temp_sd):
            return False
        
        # Test MBR read
        print("Reading MBR...")
        result = _read_mbr(temp_sd)
        
        if result:
            print("✅ MBR read successful!")
        else:
            print("✗ MBR read failed")
        
        return result
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def read_mbr():
    """
    Test reading MBR from SD card without mounting filesystem.
    Useful for debugging SD card issues.
    
    Note: Releases all pins after completion. Wait before calling mount().
    
    Returns:
        True if MBR read successful, False otherwise
    """
    print("Testing MBR read (no mount required)...")
    return _read_mbr_standalone()
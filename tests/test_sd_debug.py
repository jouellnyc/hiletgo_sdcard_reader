"""
test_sd_debug.py - Complete SD card diagnostic test

Tests for known bugs across different ESP32 boards.
Uses sdcard_helper's shared SPI/SD objects to avoid pin conflicts.
"""

import time
import os
import sd_config
import sdcard_helper

def run_test():
    """Run complete SD card diagnostic test."""
    
    print("=" * 60)
    print("SD Card Bug Test - Complete Diagnostic")
    print("=" * 60)
    
    print(f"⚠️  IMPORTANT: If you just pressed Ctrl+D, this will hang!")
    print(f"    Use RESET button instead")
    
    print(f"Board: {sd_config.board_type}")
    print(f"Baudrate: {sd_config.SD_BAUDRATE:,} Hz")
    
    print("=" * 60)
    print("MOUNTING SD CARD")
    print("=" * 60)
    
    # Use sdcard_helper's mount function (uses shared objects)
    if not sdcard_helper.mount():
        print("✗ Mount failed!")
        print("\nPossible causes:")
        print("  1. SD card not inserted")
        print("  2. Wiring issue")
        print("  3. Wrong baudrate")
        print("  4. Incompatible card (try 16GB card)")
        return False
    
    print("=" * 60)
    print("DISK USAGE")
    print("=" * 60)
    
    stats = sdcard_helper.get_stats()
    if stats:
        print(f"  Total: {stats['total_mb']:.2f} MB")
        print(f"  Used:  {stats['used_mb']:.2f} MB")
        print(f"  Free:  {stats['free_mb']:.2f} MB")
    
    print("=" * 60)
    print("TESTING FOR BUGS")
    print("=" * 60)
    
    # Test 1: Immediate listdir
    print("[Test 1] First listdir (immediate after mount):")
    t1 = time.monotonic()
    files1 = os.listdir("/sd")
    elapsed1 = time.monotonic() - t1
    print(f"  Completed in {elapsed1:.3f}s")
    print(f"  Result: {len(files1)} files")
    
    # Test 2: After 3 second delay
    print("[Test 2] Waiting 3 seconds...")
    for i in range(3):
        print(f"  {i+1}...")
        time.sleep(1.0)
    
    print("[Test 2] Second listdir (after 3s):")
    t2 = time.monotonic()
    files2 = os.listdir("/sd")
    elapsed2 = time.monotonic() - t2
    print(f"  Completed in {elapsed2:.3f}s")
    print(f"  Result: {len(files2)} files")
    
    # Test 3: Write test
    print("[Test 3] WRITE TEST - Creating 10 test files...")
    try:
        for i in range(10):
            with open(f"/sd/test_{i}.txt", "w") as f:
                f.write(f"Test file {i}\n")
        print(f"  ✓ Created 10 files")
        test3_success = True
    except OSError as e:
        if "Read-only" in str(e):
            print(f"  ⚠ Skipped (SD mounted read-only)")
            test3_success = False
        else:
            print(f"  ✗ Write failed: {e}")
            test3_success = False
    
    # Test 4: After 1 second delay with new files
    if test3_success:
        print("[Test 4] Waiting 1 second...")
        time.sleep(1.0)
        print("[Test 4] Checking if new files visible (after 1s):")
        t4 = time.monotonic()
        files4 = os.listdir("/sd")
        elapsed4 = time.monotonic() - t4
        print(f"  Completed in {elapsed4:.3f}s")
        print(f"  Result: {len(files4)} files")
    else:
        files4 = files2
        elapsed4 = 0
    
    # Test 5: Delete test files
    if test3_success:
        print("[Test 5] DELETE TEST - Removing test files...")
        try:
            for i in range(10):
                os.remove(f"/sd/test_{i}.txt")
            print(f"  ✓ Deleted 10 files")
            test5_success = True
        except Exception as e:
            print(f"  ✗ Delete failed: {e}")
            test5_success = False
    else:
        test5_success = False
    
    # Test 6: Verify deletion
    if test5_success:
        print("[Test 6] Verifying deletion (immediate):")
        t6 = time.monotonic()
        files6 = os.listdir("/sd")
        elapsed6 = time.monotonic() - t6
        print(f"  Completed in {elapsed6:.3f}s")
        print(f"  Result: {len(files6)} files")
    else:
        files6 = files4
        elapsed6 = 0
    
    # Test 7: Final check
    print("[Test 7] Final listdir (immediate):")
    t7 = time.monotonic()
    files7 = os.listdir("/sd")
    elapsed7 = time.monotonic() - t7
    print(f"  Completed in {elapsed7:.3f}s")
    print(f"  Result: {len(files7)} files")
    
    # Results summary
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Board:       {sd_config.board_type}")
    print(f"Baudrate:    {sd_config.SD_BAUDRATE:,} Hz")
    if stats:
        print(f"Disk usage:  {stats['used_mb']:.2f} MB")
    print(f"File counts:")
    print(f"  Test 1 (immediate):  {len(files1)}")
    print(f"  Test 2 (after 3s):   {len(files2)}")
    if test3_success:
        print(f"  Test 3 (immediate):  10 files created")
        print(f"  Test 4 (after 1s):   {len(files4)}")
        print(f"  Test 5 (immediate):  10 files deleted")
        print(f"  Test 6 (immediate):  {len(files6)}")
    print(f"  Test 7 (immediate):  {len(files7)}")
    
    # Analysis
    print("=" * 60)
    print("WHAT HAPPENED (Simple English)")
    print("=" * 60)
    
    print("📋 Step by step:")
    print(f"   1. Started with {len(files1)} files")
    print(f"   2. Waited 3 seconds → saw {len(files2)} files")
    
    if test3_success:
        print(f"   3. Tried to write 10 files → wrote 10 files")
        print(f"   4. Waited 1 second → saw {len(files4)} files")
        print(f"   5. Tried to delete test files → deleted 10 files")
        print(f"   6. Checked immediately → saw {len(files6)} files")
        print(f"   7. Checked again → saw {len(files7)} files")
    else:
        print(f"   3. Write test skipped (read-only mount)")
        print(f"   7. Checked again → saw {len(files7)} files")
    
    # Diagnosis
    print("=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    # Check for bugs
    has_timeout_bug = (len(files1) > 0 and len(files2) == 0)
    has_cache_bug = (len(files1) == 0 and len(files2) > 0)
    
    if test3_success:
        has_write_issue = (len(files4) != len(files1) + 10)
        has_delete_issue = (len(files6) != len(files1))
    else:
        has_write_issue = False
        has_delete_issue = False
    
    if has_timeout_bug:
        print("🐛 TIMEOUT BUG DETECTED!")
        print(f"   • Files appeared immediately: {len(files1)}")
        print(f"   • After 3s wait: {len(files2)}")
        print(f"   • This is the 1-second timeout bug")
        print(f"\n💡 SOLUTION:")
        print(f"   • Use keepalive pattern (call os.listdir every 0.8s)")
        print(f"   • Or switch to different board (Huzzah, RP2350, S2)")
    
    elif has_cache_bug:
        print("🐛 CACHE BUG DETECTED!")
        print(f"   • Files missing immediately: 0")
        print(f"   • Files appeared after wait: {len(files2)}")
        print(f"   • Directory cache needs priming")
        print(f"\n💡 SOLUTION:")
        print(f"   • Add time.sleep(1.0) after mount")
        print(f"   • Call os.listdir() once to prime cache")
    
    elif has_write_issue:
        print("🐛 WRITE ISSUE DETECTED!")
        print(f"   • Expected {len(files1) + 10} files after write")
        print(f"   • Actually saw {len(files4)} files")
    
    elif has_delete_issue:
        print("🐛 DELETE ISSUE DETECTED!")
        print(f"   • Expected {len(files1)} files after delete")
        print(f"   • Actually saw {len(files6)} files")
    
    else:
        print("✅ NO BUGS!")
        print(f"   • Started with {len(files1)} files ✓")
        if test3_success:
            print(f"   • Wrote 10 files ✓")
            print(f"   • Saw {len(files4)} files (10 + 10) ✓")
            print(f"   • Deleted 10 files ✓")
            print(f"   • Back to {len(files7)} files ✓")
        else:
            print(f"   • Consistent file count ✓")
        print(f"   • Everything works!")
    
    # Important notes
    print("=" * 60)
    print("IMPORTANT")
    print("=" * 60)
    print("🔴 NEVER use Ctrl+D with SD cards on ESP32!")
    print("   Always use RESET button")
    print("✅ To test again: Press RESET, then import test_sd_debug")
    
    # Note about shared objects
    print("\n💡 This test uses sdcard_helper's shared SPI/SD objects")
    print("   You can now run sdcard_helper commands without conflicts")
    
    print("=" * 60)
    print("CLEANUP")
    print("=" * 60)
    print("✓ Done")
    print("✓ TEST COMPLETE")
    
    return True


def stress_test_listdir(iterations=100):
    """
    Stress test: Repeatedly call os.listdir() to verify stability.
    
    This test verifies that repeated directory listings work reliably
    without errors, hangs, or inconsistent results.
    
    Args:
        iterations: Number of times to call os.listdir() (default: 100)
    
    Usage:
        import test_sd_debug
        test_sd_debug.stress_test_listdir()
        
        # Or with custom iteration count:
        test_sd_debug.stress_test_listdir(500)
    """
    print("=" * 60)
    print(f"STRESS TEST: {iterations} consecutive os.listdir() calls")
    print("=" * 60)
    
    # Ensure SD is mounted
    if not sdcard_helper.is_mounted():
        print("Mounting SD card...")
        if not sdcard_helper.mount():
            print("✗ Mount failed - cannot run stress test")
            return False
    
    print(f"\nRunning {iterations} listdir operations...")
    print("(Showing file list on first attempt only)\n")
    
    count = 0
    first_result = None
    
    for x in range(iterations):
        try:
            result = os.listdir('/sd/')
            
            # Show files on first iteration
            if x == 0:
                print(f"Files found: {result}")
                print()
                first_result = result
            
            # This only runs if there WAS NO error
            count += 1
            
        except Exception as e:
            # This only runs if there WAS an error
            print(f"\n✗ Error on attempt {x}: {e}")
            print(f"   Cumulative successes before failure: {count}")
            return False
        
        finally:
            # Show progress every 10 iterations
            if (x + 1) % 10 == 0:
                print(f"Attempt {x} | Cumulative Successes: {count}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("STRESS TEST RESULTS")
    print("=" * 60)
    print(f"Total attempts:  {iterations}")
    print(f"Successful:      {count}")
    print(f"Failed:          {iterations - count}")
    print(f"Success rate:    {(count/iterations)*100:.1f}%")
    
    if count == iterations:
        print("\n✅ PERFECT! All operations succeeded!")
        print(f"   SD card is stable and reliable")
    else:
        print(f"\n⚠️  {iterations - count} failures detected")
        print(f"   SD card may have stability issues")
    
    print("=" * 60)
    
    return count == iterations


# Auto-run main test when imported
print("\n💡 Running automatic diagnostic test...")
print("   To skip auto-run in future, comment out the line at bottom of this file\n")
run_test()

print("\n" + "=" * 60)
print("ADDITIONAL TESTS AVAILABLE")
print("=" * 60)
print("To run stress test (100 consecutive listdir calls):")
print("  >>> import test_sd_debug")
print("  >>> test_sd_debug.stress_test_listdir()")
print()
print("To run with more iterations:")
print("  >>> test_sd_debug.stress_test_listdir(500)")
print("=" * 60 + "\n")
"""
CircuitPython SD Card Bug Test - Compatible with CP 10.0.3

WHAT THIS TEST DOES:
====================
This script tests for SD card bugs in CircuitPython:

1. WRITE INVISIBLE BUG (Most severe):
   - Files are written successfully
   - After 1 second, files become INVISIBLE
   - Pattern: 10 files → create 10 → wait 1s → 0 files visible

2. CACHE BUG ("Schrödinger's Files"):
   - Files appear empty first, then visible after delay
   - Pattern: 0 files → (wait) → 10 files

3. TIMEOUT BUG (DevKitC specific):
   - Files appear, then DISAPPEAR after idle time
   - Pattern: 10 files → (wait) → 0 files

4. INCONSISTENT READ BUG (Signal quality issue):
   - File count changes on every read
   - Pattern: 10 files → 7 files → 10 files
   - Indicates signal corruption or hardware incompatibility

HOW IT WORKS:
=============
1. Mounts SD card (hangs if you used Ctrl+D soft reboot)
2. Checks disk usage
3. Calls os.listdir() with delays
4. WRITES 10 test files
5. Checks if written files are visible after 1s delay
6. DELETES test files
7. Analyzes pattern to identify specific bug
8. Provides workarounds for detected issue

TESTED BOARDS:
==============
- Waveshare RP2350-Plus: ✅ Perfect at 12 MHz
- ESP32 Feather Huzzah: ✅ Perfect at 4 MHz
- ESP32-S3 DevKitC: ❌ Multiple issues at all speeds tested

IMPORTANT:
==========
- NEVER use Ctrl+D (soft reboot) with SD cards on ESP32
- Always use RESET button
- Requires sd_config.py

USAGE:
======
1. Hard reset (press RESET button)
2. Run: import test_sd_debug
3. Review diagnosis
4. Follow recommendations

Related: https://github.com/adafruit/circuitpython/issues/10741
"""

import board
import busio
import sdcardio
import storage
import os
import time

print("=" * 60)
print("SD Card Bug Test - Complete Diagnostic")
print("=" * 60)

# Import config
try:
    import sd_config
except ImportError:
    print("\n✗ ERROR: sd_config.py not found!")
    raise SystemExit

# Warn about soft reboot
print("\n⚠️  IMPORTANT: If you just pressed Ctrl+D, this will hang!")
print("    Use RESET button instead")
print("")

print(f"Board: {board.board_id}")
print(f"Baudrate: {sd_config.SD_BAUDRATE:,} Hz")

def safe_listdir(path):
    """List directory with timing info"""
    start = time.monotonic()
    try:
        files = os.listdir(path)
        elapsed = time.monotonic() - start
        print(f"  Completed in {elapsed:.3f}s")
        return files
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"  FAILED after {elapsed:.3f}s: {e}")
        return None

# Mount
print("\n" + "=" * 60)
print("MOUNTING SD CARD")
print("=" * 60)

try:
    print("\n[1/4] Creating SPI...")
    spi = busio.SPI(sd_config.SD_SCK, MOSI=sd_config.SD_MOSI, MISO=sd_config.SD_MISO)
    print("      ✓ Done")
    
    print(f"\n[2/4] Creating SDCard ({sd_config.SD_BAUDRATE:,} Hz)...")
    sd = sdcardio.SDCard(spi, sd_config.SD_CS, baudrate=sd_config.SD_BAUDRATE)
    print("      ✓ Done")
    
    print("\n[3/4] Creating VfsFat...")
    print("      (Soft reboot hangs here - press RESET if stuck)")
    vfs = storage.VfsFat(sd)
    print("      ✓ Done")
    
    print(f"\n[4/4] Mounting to {sd_config.SD_MOUNT}...")
    storage.mount(vfs, sd_config.SD_MOUNT)
    print("      ✓ Mounted!")
    
except Exception as e:
    print(f"\n      ✗ Failed: {e}")
    print("\nIf 'IO pin in use', press RESET and try again")
    raise SystemExit

# Check disk usage
print("\n" + "=" * 60)
print("DISK USAGE")
print("=" * 60)

used_mb = 0
try:
    stats = os.statvfs(sd_config.SD_MOUNT)
    total_mb = (stats[0] * stats[2]) / (1024 * 1024)
    used_mb = ((stats[0] * stats[2]) - (stats[0] * stats[3])) / (1024 * 1024)
    free_mb = (stats[0] * stats[3]) / (1024 * 1024)
    print(f"\n  Total: {total_mb:.2f} MB")
    print(f"  Used:  {used_mb:.2f} MB")
    print(f"  Free:  {free_mb:.2f} MB")
except Exception as e:
    print(f"\n  ✗ Failed: {e}")

# Test for bugs
print("\n" + "=" * 60)
print("TESTING FOR BUGS")
print("=" * 60)

# Test 1: Immediate
print("\n[Test 1] First listdir (immediate after mount):")
files1 = safe_listdir(sd_config.SD_MOUNT)
len1 = len(files1) if files1 else 0
print(f"  Result: {len1} files")

# Test 2: After 3 seconds
print("\n[Test 2] Waiting 3 seconds...")
time.sleep(1)
print("  1...")
time.sleep(1)
print("  2...")
time.sleep(1)
print("  3...")

print("\n[Test 2] Second listdir (after 3s):")
files2 = safe_listdir(sd_config.SD_MOUNT)
len2 = len(files2) if files2 else 0
print(f"  Result: {len2} files")

# Test 3: Write test - create 10 files
print("\n[Test 3] WRITE TEST - Creating 10 test files...")
test_files_created = 0
try:
    for i in range(10):
        with open(f"{sd_config.SD_MOUNT}/test_{i}.txt", "w") as f:
            f.write(f"Test file {i}\n")
        test_files_created += 1
    print(f"  ✓ Created {test_files_created} files")
except Exception as e:
    print(f"  ✗ Failed after {test_files_created} files: {e}")

# Test 4: Check if files appear after 1 second
print("\n[Test 4] Waiting 1 second...")
time.sleep(1)
print("\n[Test 4] Checking if new files visible (after 1s):")
files4 = safe_listdir(sd_config.SD_MOUNT)
len4 = len(files4) if files4 else 0
print(f"  Result: {len4} files")

# Test 5: Delete test files
print("\n[Test 5] DELETE TEST - Removing test files...")
deleted = 0
try:
    for i in range(10):
        try:
            os.remove(f"{sd_config.SD_MOUNT}/test_{i}.txt")
            deleted += 1
        except:
            pass
    print(f"  ✓ Deleted {deleted} files")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 6: Verify deletion
print("\n[Test 6] Verifying deletion (immediate):")
files6 = safe_listdir(sd_config.SD_MOUNT)
len6 = len(files6) if files6 else 0
print(f"  Result: {len6} files")

# Test 7: Final consistency check
print("\n[Test 7] Final listdir (immediate):")
files7 = safe_listdir(sd_config.SD_MOUNT)
len7 = len(files7) if files7 else 0
print(f"  Result: {len7} files")

# Analysis
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

print(f"\nBoard:       {board.board_id}")
print(f"Baudrate:    {sd_config.SD_BAUDRATE:,} Hz")
print(f"Disk usage:  {used_mb:.2f} MB")
print(f"\nFile counts:")
print(f"  Test 1 (immediate):  {len1}")
print(f"  Test 2 (after 3s):   {len2}")
print(f"  Test 3 (immediate):  {test_files_created} files created")
print(f"  Test 4 (after 1s):   {len4}")
print(f"  Test 5 (immediate):  {deleted} files deleted")
print(f"  Test 6 (immediate):  {len6}")
print(f"  Test 7 (immediate):  {len7}")

# Diagnosis
print("\n" + "=" * 60)
print("WHAT HAPPENED (Simple English)")
print("=" * 60)

print("\n📋 Step by step:")
print(f"   1. Started with {len1} files")
print(f"   2. Waited 3 seconds → saw {len2} files")
print(f"   3. Tried to write 10 files → wrote {test_files_created} files")
print(f"   4. Waited 1 second → saw {len4} files")
print(f"   5. Tried to delete test files → deleted {deleted} files")
print(f"   6. Checked immediately → saw {len6} files")
print(f"   7. Checked again → saw {len7} files")

# Simple diagnosis
print("\n" + "=" * 60)
print("DIAGNOSIS")
print("=" * 60)

bug_type = None
baseline = len1

# Write failed completely
if test_files_created == 0:
    bug_type = "WRITE_FAILED"
    print("\n❌ BUG: CANNOT WRITE FILES!")
    print(f"   • Tried to write 10 files")
    print(f"   • Actually wrote: {test_files_created} files")
    print(f"   • SD card rejected the write!")

# Wrote files but they disappeared
elif test_files_created == 10 and len4 == 0:
    bug_type = "WRITE_INVISIBLE"
    print("\n❌ BUG: FILES DISAPPEARED!")
    print(f"   • Wrote 10 files successfully")
    print(f"   • Waited 1 second")
    print(f"   • Files vanished! Saw {len4} files")

# Wrote files but wrong count visible
elif test_files_created == 10 and len4 != (baseline + 10):
    bug_type = "WRONG_COUNT"
    print("\n❌ BUG: WRONG FILE COUNT!")
    print(f"   • Started with {baseline} files")
    print(f"   • Wrote 10 more files")
    print(f"   • Should see {baseline + 10} files")
    print(f"   • Actually saw {len4} files")

# Numbers keep changing
elif len(set([len1, len2, len4, len6, len7])) > 3:
    bug_type = "INCONSISTENT"
    print("\n❌ BUG: NUMBERS KEEP CHANGING!")
    print(f"   • File count changes every time:")
    print(f"   • {len1} → {len2} → {len4} → {len6} → {len7}")
    print(f"   • SD card is confused!")

# Files disappeared after waiting
elif len1 > 0 and len2 == 0:
    bug_type = "TIMEOUT"
    print("\n❌ BUG: FILES DISAPPEARED AFTER WAITING!")
    print(f"   • Started with {len1} files")
    print(f"   • Waited 3 seconds")
    print(f"   • Files vanished! Saw {len2} files")

# Everything worked
elif test_files_created == 10 and len4 == (baseline + 10) and len6 == baseline:
    print("\n✅ NO BUGS!")
    print(f"   • Started with {baseline} files ✓")
    print(f"   • Wrote 10 files ✓")
    print(f"   • Saw {len4} files ({baseline} + 10) ✓")
    print(f"   • Deleted 10 files ✓")
    print(f"   • Back to {len6} files ✓")
    print(f"   • Everything works!")

# Something weird
else:
    print("\n⚠️  SOMETHING WEIRD HAPPENED")
    print(f"   The numbers don't make sense.")

# Details for each bug type
if bug_type == "WRITE_FAILED":
    print("\n" + "=" * 60)
    print("WHY THIS IS BAD")
    print("=" * 60)
    print("\nThe SD card won't let you save files!")
    print(f"At {sd_config.SD_BAUDRATE:,} Hz, the SD card says NO.")
    print("\nWhat to do:")
    print("  • Try slower speed (like 250,000)")
    print("  • Check if wires are loose")
    print("  • Try different SD card")

elif bug_type == "WRITE_INVISIBLE":
    print("\n" + "=" * 60)
    print("WHY THIS IS BAD")
    print("=" * 60)
    print("\nYou saved files but they became invisible!")
    print("Like magic... but bad magic.")
    print(f"At {sd_config.SD_BAUDRATE:,} Hz, the SD card forgets what you saved.")
    print("\nWhat to do:")
    print("  • Use MUCH slower speed")
    print("  • This board might not work with SD cards")

elif bug_type == "WRONG_COUNT":
    print("\n" + "=" * 60)
    print("WHY THIS IS BAD")
    print("=" * 60)
    print("\nThe SD card lost track of your files!")
    print("You saved files but it doesn't remember them all.")
    print("\nWhat to do:")
    print("  • Use slower speed")
    print("  • Check wires")

elif bug_type == "INCONSISTENT":
    print("\n" + "=" * 60)
    print("WHY THIS IS BAD")
    print("=" * 60)
    print("\nThe SD card can't count!")
    print("Every time you ask 'how many files?', it gives a different answer.")
    print(f"At {sd_config.SD_BAUDRATE:,} Hz, this board is talking TOO FAST.")
    print("\nWhat to do:")
    print("  • Use MUCH MUCH slower speed (like 100,000)")
    print("  • Or use different board")

elif bug_type == "TIMEOUT":
    print("\n" + "=" * 60)
    print("WHY THIS IS BAD")
    print("=" * 60)
    print("\nIf you wait too long, files disappear!")
    print("The SD card forgets after being quiet.")
    print("\nWhat to do:")
    print("  • Keep asking about files every second")
    print("  • Or use slower speed")



# Important notes
print("\n" + "=" * 60)
print("IMPORTANT")
print("=" * 60)
print("\n🔴 NEVER use Ctrl+D with SD cards on ESP32!")
print("   Always use RESET button")
print("\n✅ To test again: Press RESET, then import test_sd_debug")

# Cleanup
print("\n" + "=" * 60)
print("CLEANUP")
print("=" * 60)

try:
    storage.umount(sd_config.SD_MOUNT)
    spi.deinit()
    print("\n✓ Done")
except Exception as e:
    print(f"\n⚠️  Failed: {e}")
    print("Press RESET before next test")

print("\n✓ TEST COMPLETE\n")

# CircuitPython SD Card Reader Guide

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## Board Compatibility

| Board | Status | Max Speed | Key Issue |
|-------|--------|-----------|-----------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅ Perfect | 12 MHz | None |
| **ESP32 Feather Huzzah** | ✅✅✅ Excellent | 8 MHz | ~~Soft reboot hangs mount~~ **FIXED in v1.2.0!** ✅ |
| **ESP32-S3 DevKitC** | ⚠ Poor | 250 kHz | 1-second timeout bug |

---

## Detailed Comparisons

### 🏆 Waveshare RP2350-Plus (RECOMMENDED)

**Perfect reliability, no workarounds needed.**

- Baudrate: 12 MHz
- Soft reboot (Ctrl+D): Works fine
- Cache bug: No
- Timeout issue: No
- Audio quality: Best

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Use for all projects

---

### ESP32 Feather Huzzah

**Excellent performance with sdcard_helper v1.2.0+**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): ✅ **Works with v1.2.0+**
- Cache bug: No
- Timeout issue: No
- Audio quality: Excellent

**Previous Issue (RESOLVED):** Earlier versions hung after Ctrl+D soft reboot. Version 1.2.0 introduced pre-validation steps that act as an SD card "warm-up sequence," ensuring the card controller is fully initialized before mounting. This completely resolved the soft reboot issue.

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # Up to 8 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Excellent choice, now fully reliable with sdcard_helper v1.2.0+

---

### ESP32-S3 DevKitC

**Not recommended - multiple severe issues.**

- Baudrate: 250 kHz only 
- Soft reboot (Ctrl+D): Stable 
- Cache bug: Yes
- Timeout issue: **YES - 1 second** ❌
- Audio quality: Works but slow / inconsistent

**Critical Issue:** Directory cache dumps after 1 second of SPI idle:
```python
files = os.listdir("/sd")  # 10 files
time.sleep(1.0)            # Wait 1 second
files = os.listdir("/sd")  # 0 files ❌
```

**Why:** Poor signal quality from weak GPIO + level shifter causes SD card to aggressively power-save.

**Workaround:** Keepalive every 0.8 seconds
```python
import sdcard_helper
import time

while True:
    # Your code here
    time.sleep(0.8)
    sdcard_helper.keepalive()  # Prevent timeout
```

**Configuration:**
```python
SD_BAUDRATE = 250_000  # 250 kHz only
```

**Recommendation:** ⭐ Avoid for SD card projects

---

## Quick Start

### 1. Choose Board

- **New projects:** Waveshare RP2350-Plus or ESP32 Feather Huzzah
- **ESP32 projects:** Huzzah (excellent with v1.2.0+) - avoid DevKitC

### 2. Hardware Setup

- Add 100µF capacitor to SD card VCC
- Use short wires (<6 inches)
- Power via USB or external supply

### 3. Pin Configuration

Create `sd_config.py`:
```python
import board

board_type = board.board_id

# Waveshare RP2350-Plus
if "rp2350" in board_type:
    SD_SCK  = board.GP18
    SD_MOSI = board.GP19
    SD_MISO = board.GP16
    SD_CS   = board.GP17
    SD_BAUDRATE = 12_000_000

# ESP32 Feather Huzzah
elif "huzzah32" in board_type and "s3" not in board_type:
    SD_SCK  = board.SCK   # GPIO 5
    SD_MOSI = board.MOSI  # GPIO 18
    SD_MISO = board.MISO  # GPIO 19
    SD_CS   = board.A5    # GPIO 4
    SD_BAUDRATE = 8_000_000  # Up to 8 MHz

# ESP32-S3 DevKitC
elif "s3" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    SD_BAUDRATE = 250_000

SD_MOUNT = "/sd"
```

### 4. Basic Usage
```python
import sdcard_helper

if sdcard_helper.mount():
    files = sdcard_helper.list_files()
    print(f"Found {len(files)} files")
```

---

## What's New in v1.2.0

### 🎉 Soft Reboot Issue RESOLVED (Huzzah)

**The Problem:** After soft reboot (Ctrl+D), `storage.mount()` would hang on the Huzzah. The SD card stayed powered but the data channel broke during reinitialization.

**The Solution:** Version 1.2.0 introduces a pre-validation sequence that acts as an SD card "warm-up":

1. **`_validate_sd_communication()`** - Reads block count, wakes up controller
2. **`_read_mbr()`** - First data read, exercises the data path
3. **`_test_multiblock_read()`** - Sequential read, verifies sustained communication
4. **Then** `storage.mount()` - Card is now fully ready

This sequence gives the SD card controller time to stabilize and clear any stale state from the previous session.

**Result:** ✅ Soft reboot now works 100% reliably on Huzzah!

### Other Improvements in v1.2.0

- **Shared SPI/SD objects:** `read_mbr()` and `mount()` now reuse the same hardware initialization, preventing "pin in use" errors
- **Modular architecture:** Clean separation of initialization, validation, and mounting
- **Better error handling:** Clear diagnostics at each step
- **Version tracking:** Know exactly which version you're running

---

## Testing

Run diagnostic test:
```python
import test_sd_debug
```

Detects board, checks for bugs, provides specific recommendations.

Check your sdcard_helper version:
```python
import sdcard_helper
# Prints: sdcard_helper v1.2.0
print(sdcard_helper.__version__)
```

---

## Known Issues

### Issue 1: Soft Reboot Hang (RESOLVED ✅)

**Status:** ✅ **FIXED in v1.2.0**

**Previous symptom:** Mount hung after Ctrl+D on Huzzah

**Solution:** Update to sdcard_helper v1.2.0 or later. The pre-validation warm-up sequence completely resolves this issue.

**Affected:** Huzzah (now fixed), DevKitC (minimal impact)  
**Not affected:** Waveshare

### Issue 2: 1-Second Timeout (DevKitC)

**Symptom:** Files disappear after 1 second idle

**Solution:** Keepalive pattern or use different board

**Affected:** DevKitC only  

### Issue 3: Cache Bug (DevKitC)

**Symptom:** First `listdir()` returns empty

**Solution:** Add settling time after mount
```python
storage.mount(vfs, "/sd")
time.sleep(1.0)
_ = os.listdir("/sd")  # Prime cache
os.sync()
```

Issues 2 and 3 overlap but are not fully 'work aroundable'...Really the DEV KIT C was so difficult to use, it's not worth it.

---

## Performance

| Operation | Waveshare | Huzzah | DevKitC |
|-----------|-----------|--------|---------|
| Mount time | ~0.5s | ~0.5s | ~0.5s |
| listdir() | <1ms | ~2ms | ~8ms |
| Read 5MB MP3 | ~1s | ~2.5s | ~10s |
| Soft reboot reliability | ✅ 100% | ✅ 100% (v1.2.0+) | ⚠️ Varies |

---

## Rules

### ✅ DO:
- Use sdcard_helper v1.2.0 or later
- Use RESET button OR Ctrl+D (both work with v1.2.0+)
- Add 100µF capacitor on SD VCC
- Use short wires

### ❌ DON'T:
- Use DevKitC for SD projects
- Use wires >6 inches
- ~~Use Ctrl+D with Huzzah~~ (This is now fine with v1.2.0!)

---

## Troubleshooting

**Mount fails:**
1. Verify sdcard_helper version (should be 1.2.0+)
2. Check wiring
3. Verify FAT32 format
4. Try different SD card (see SD Card Compatibility section)
5. Lower baudrate

**Files not appearing:**
- Waveshare: Check SD format
- Huzzah: Update to v1.2.0+ (resolves soft reboot issues)
- DevKitC: Implement keepalive or switch boards

**Hangs on mount:**
- Solution: Update to sdcard_helper v1.2.0 or later
- If still hanging: Try different SD card (see compatibility section)

---

## ⚠️ SD Card Compatibility: Our Observations

### What We Observed

During testing, we encountered an unexpected SD card compatibility issue:

**A Samsung SD card (EVO Select 64 GB) that worked perfectly on PC failed to mount on three different microcontroller boards:**

- ❌ ESP32-S3 DevKitC - Hangs reading MBR
- ❌ Adafruit Huzzah32 - Hangs reading MBR
- ❌ WaveShare RP2350 Plus - Hangs during MBR read
- ✅ PC/Mac/Linux - Reads and writes perfectly

**A generic no-name SD card worked flawlessly on all three boards.**

### Our Theory (Unverified)

We suspect this happens because:

**PCs handle SD cards more robustly than microcontrollers:**

| PC/Computer | Microcontroller |
|-------------|-----------------|
| Sophisticated error correction | Minimal error handling |
| Retries failed operations | Quick timeouts |
| Aggressive caching | Little to no caching |
| Works around bad sectors | Fails on first error |
| Complex drivers | Simple SPI implementation |

The Samsung card may have timing or communication characteristics that work fine with robust PC drivers but cause issues with CircuitPython's simpler SPI implementation.

### Symptoms We Encountered

With the problematic Samsung card:
- `sdcardio.SDCard()` initialized successfully
- `_sd.count()` returned block count correctly (58,064,896 blocks = ~28GB, suggesting it's actually a 32GB card, not 64GB)
- **`readblocks()` hung indefinitely when trying to read MBR**
- Same behavior across all three different microcontroller boards
- Likely a counterfeit card with buggy controller firmware

With the working generic card:
- All operations completed successfully
- Reliable mounting and file operations at 12MHz
- No issues across any tested board

### What To Try If You Have SD Card Issues

**If your SD card works on your computer but fails on your microcontroller:**

1. **Try a different SD card** - Even if your current card appears healthy on PC
2. **Test with a basic/generic card** - In our case, the cheaper card worked better
3. **Format as FAT32** - Not exFAT
4. **Try different baudrates** - Lower speeds (1-4MHz) may help marginal cards
5. **Check your wiring and power** - Rule out hardware issues first
6. **Test for counterfeits** - Use h2testw (Windows) or F3 (Mac/Linux) to verify real capacity

### Testing Your SD Card without mounting it!
```python
# This may work even if you can't mount

import sdcard_helper
Output: sdcard_helper v1.2.0
Output: --- SD Config: Detected adafruit_feather_huzzah32 ---
Output: --- SD Config: using 4000000 SD_BAUDRATE ---

sdcard_helper.read_mbr()
Testing MBR read (no mount required)...
  Initializing SPI...
  Initializing SD card...
Testing SD card communication...
  Block count: 30535680
  Capacity: 14910.00 MB (14.56 GB)
Reading MBR...
  Reading MBR (block 0)...
  ✓ Valid MBR signature: 0xAA55
  Partition type: FAT32
✅ MBR read successful!
True
```

If `read_mbr()` hangs, the SD card has fundamental SPI communication issues and won't work with CircuitPython regardless of the board or settings.

---

**Bottom Line:** Any given microcontroller, with any given external component could work or not work based on some internal variance. The best teacher is empirical evidence, testing, and keeping good notes. 

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741)
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)

---

## License

MIT License

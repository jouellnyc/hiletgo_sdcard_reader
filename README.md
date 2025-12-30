# CircuitPython SD Card Reader Guide

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## Board Compatibility

| Board | Status | Max Speed | Key Issue |
|-------|--------|-----------|-----------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅ Perfect | 12 MHz | None |
| **ESP32 Feather Huzzah** | ✅✅✅ Excellent | 8 MHz | None (with compatible SD cards) |
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
- SD card compatibility: Excellent

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Use for all projects

---

### ESP32 Feather Huzzah

**Excellent performance with compatible SD cards.**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): ✅ Works perfectly
- Cache bug: No
- Timeout issue: No
- Audio quality: Excellent
- SD card compatibility: Good (avoid problematic cards - see SD Card Compatibility section)

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # Up to 8 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Excellent choice with compatible SD cards

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
- **ESP32 projects:** Huzzah (excellent performance) - avoid DevKitC

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

### 🎉 Improved SD Card Compatibility

**The Enhancement:** Version 1.2.0 introduces a pre-validation sequence that improves SD card compatibility:

1. **`_validate_sd_communication()`** - Reads block count, wakes up controller
2. **`_read_mbr()`** - First data read, exercises the data path
3. **`_test_multiblock_read()`** - Sequential read, verifies sustained communication
4. **Then** `storage.mount()` - Card is now fully ready

This sequence gives SD card controllers time to stabilize and clear any stale state, which helps with:
- Marginal/slower SD cards
- Cards with complex controllers
- Soft reboot scenarios on some boards

**Note:** This does NOT fix fundamentally incompatible SD cards (like the Samsung card documented below). Those cards will fail regardless of warm-up sequence because their SPI implementation is broken.

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

### Issue 1: 1-Second Timeout (DevKitC)

**Symptom:** Files disappear after 1 second idle

**Solution:** Keepalive pattern or use different board

**Affected:** DevKitC only  

### Issue 2: Cache Bug (DevKitC)

**Symptom:** First `listdir()` returns empty

**Solution:** Add settling time after mount
```python
storage.mount(vfs, "/sd")
time.sleep(1.0)
_ = os.listdir("/sd")  # Prime cache
os.sync()
```

Issues 1 and 2 overlap but are not fully 'work aroundable'...Really the DEV KIT C was so difficult to use, it's not worth it.

---

## Performance

| Operation | Waveshare | Huzzah | DevKitC |
|-----------|-----------|--------|---------|
| Mount time | ~0.5s | ~0.5s | ~0.5s |
| listdir() | <1ms | ~2ms | ~8ms |
| Read 5MB MP3 | ~1s | ~2.5s | ~10s |
| SD card compatibility | Excellent | Excellent | Poor |

---

## Rules

### ✅ DO:
- Use sdcard_helper v1.2.0 or later
- Test your SD card with `sdcard_helper.read_mbr()` before using
- Add 100µF capacitor on SD VCC
- Use short wires
- Use compatible SD cards (avoid Samsung EVO - see compatibility section)

### ❌ DON'T:
- Use DevKitC for SD projects
- Use wires >6 inches
- Assume expensive SD cards work better (often the opposite!)

---

## Troubleshooting

**Mount fails:**
1. Test SD card with `sdcard_helper.read_mbr()` to verify basic compatibility
2. Try a different SD card (generic/no-name cards often work better)
3. Check wiring
4. Verify FAT32 format
5. Lower baudrate

**Hangs during mount:**
- Most likely: Incompatible SD card (try a different card)
- Test with `sdcard_helper.read_mbr()` - if this hangs, card is incompatible
- See SD Card Compatibility section below

**Files not appearing:**
- Waveshare/Huzzah: Check SD format, try different card
- DevKitC: Implement keepalive or switch boards

---

## ⚠️ SD Card Compatibility: Critical Information

### **The Most Important Lesson: Expensive ≠ Better**

**During extensive testing, we discovered that "premium" SD cards can be WORSE for microcontrollers than cheap generic cards.**

---

### What We Observed

**A Samsung EVO Select 64GB card that worked perfectly on PC failed on ALL THREE tested microcontroller boards:**

| Board | Samsung EVO Select Result | Generic No-Name Card Result |
|-------|---------------------------|----------------------------|
| ESP32-S3 DevKitC | ❌ Hangs reading MBR | ✅ Works perfectly |
| Adafruit Huzzah32 | ❌ Hangs reading MBR | ✅ Works perfectly |
| WaveShare RP2350 Plus | ❌ Hangs reading MBR | ✅ Works perfectly |
| PC/Mac/Linux | ✅ Works perfectly | ✅ Works perfectly |

---

### The Samsung Card's Behavior

**Successful operations:**
- ✅ `sdcardio.SDCard()` initialization
- ✅ `_sd.count()` returns block count (58,064,896 blocks)
- ✅ Capacity calculation (28352 MB / 27.69 GB)

**Where it fails:**
- ❌ **`readblocks(0, mbr)` hangs indefinitely**
- ❌ Cannot read ANY data blocks via SPI
- ❌ `storage.mount()` never completes

**Interesting finding:** Card reports ~28GB capacity but is sold as 64GB, strongly suggesting it's a **counterfeit card with hacked firmware**. This buggy firmware likely explains why SPI block reads fail.

---

### Why This Happens

**PCs vs. Microcontrollers handle SD cards differently:**

| PC/Computer | Microcontroller |
|-------------|-----------------|
| Sophisticated error correction | Minimal error handling |
| Retries failed operations dozens of times | Times out quickly |
| Aggressive caching and buffering | Little to no caching |
| Works around bad sectors automatically | Fails on first error |
| Complex drivers with fallback modes | Simple SPI implementation |
| Can use different communication modes | SPI mode only |

**Premium SD cards often have:**
- Complex controllers with advanced features
- Aggressive wear-leveling that confuses simple SPI
- Timing characteristics optimized for UHS speeds, not basic SPI
- Manufacturing variations that robust PC drivers tolerate but simple implementations don't

**Cheap/generic SD cards often have:**
- Simpler, more predictable controllers
- Basic SPI implementation that follows spec closely
- Fewer "optimization" features that cause compatibility issues
- Better compatibility with embedded systems

---

### How to Test Your SD Card

**Before using an SD card in your project, test it:**
```python
import sdcard_helper

# Test basic communication without mounting
result = sdcard_helper.read_mbr()

# If this hangs or fails, the SD card is incompatible
# Try a different card before wasting time debugging
```

**What `read_mbr()` shows:**
```
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
```

**If it hangs at "Reading MBR (block 0)..." → Card is incompatible, try a different one**

---

### Recommended SD Cards

**Cards confirmed to work well:**
- Generic/no-name microSD cards from various manufacturers
- SanDisk Ultra (basic models, not Extreme/Pro)
- Basic Kingston cards
- **Rule of thumb: Cheaper and simpler is often better**

**Cards with known issues:**
- Samsung EVO Select (tested multiple, all failed)
- Samsung EVO Plus (likely similar issues)
- High-performance cards marketed for cameras/video (UHS-II, V90, etc.)

**Note:** Even within the same model, manufacturing variations exist. Always test your specific card!

---

### Verifying Card Authenticity

Many "branded" SD cards sold online are counterfeits with:
- Hacked firmware reporting fake capacity
- Poor quality flash chips
- Buggy controllers

**Test for counterfeits:**
- **Windows:** Use [h2testw](https://www.heise.de/download/product/h2testw-50539)
- **Mac/Linux:** Use [F3](https://github.com/AltraMayor/f3)

These tools verify actual capacity by writing and reading test data. The Samsung card in our testing reported 28GB actual capacity when sold as 64GB - a clear sign of counterfeiting.

---

### What To Try If You Have SD Card Issues

**If your SD card works on your computer but fails on your microcontroller:**

1. **Run `sdcard_helper.read_mbr()` first** - Tests basic SPI block reads
2. **Try a different SD card** - Preferably a cheap generic one
3. **Test for counterfeits** - Use h2testw or F3 to verify
4. **Format as FAT32** - Not exFAT (some controllers don't support it)
5. **Try lower baudrates** - Some cards work at 1-4MHz but not higher
6. **Check wiring and power** - Eliminate hardware issues first

**If `read_mbr()` hangs, stop - the card is incompatible. No amount of debugging will fix a broken SD card controller.**

---

### The Bottom Line

**SD card compatibility with microcontrollers is unpredictable and counterintuitive:**

- ❌ Expensive doesn't mean better
- ❌ Name brand doesn't guarantee compatibility  
- ❌ Working on PC doesn't mean it works on microcontrollers
- ✅ Cheap generic cards often work best
- ✅ Simpler is better for embedded systems
- ✅ Always test before committing to a card

**When in doubt, buy a cheap generic microSD card. It will probably work better than the expensive one.**

---

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741)
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)
- [h2testw - SD Card Verification Tool](https://www.heise.de/download/product/h2testw-50539)
- [F3 - Fight Flash Fraud](https://github.com/AltraMayor/f3)

---

## License

MIT License

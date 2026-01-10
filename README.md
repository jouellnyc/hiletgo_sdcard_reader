# CircuitPython SD Card Reader Guide for HiLetgo SD card reader

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## ⚠ CRITICAL: Use SD Cards 32 GB or less

**The most important factor for reliability is SD card size, not the board or reader.**

### Quick Reference

| Card Size | Works? | Tested |
|-----------|--------|--------|
| 16 GB | ✅ Yes | Extensively - works on all boards |
| ≤ 32 GB | ✅ Likely | Per Adafruit documentation |
| ≥ 64 GB | ❌ No | Tested - fails on all boards |

**Key Finding:** All tested boards work perfectly with 16GB cards and all fail with 64GB cards. Card size matters far more than board model.

Adafruit states: "CircuitPython has trouble recognizing cards bigger than 32GB" ([source](https://learn.adafruit.com/adafruit-microsd-spi-sdio/circuitpython)).

### Our Test Results

| Card | PC Capacity | Microcontroller Reports | Result |
|------|-------------|------------------------|--------|
| Generic 16GB | ~15 GB | ~15 GB | ✅ Works perfectly on all boards |
| Samsung 64GB | 59.69 GB | 28.35 GB | ❌ Hangs on MBR read |
| Microcenter 64GB | 58.24 GB | 26.87 GB | ❌ I/O Errors on reads |

**Observations:**
- 16GB card: Worked reliably on all tested boards at all speeds
- 64GB cards: Both reported approximately half their actual capacity (~26-28GB) to microcontrollers
- 64GB cards: Both failed when attempting to read data blocks
- Different 64GB cards failed in different ways (hangs vs I/O errors)

**PC capacity measurements:**
```bash
# Samsung 64GB on PC
Disk /dev/sda: 59.69 GiB, 64088965120 bytes, 125173760 sectors

# Microcenter 64GB on PC  
Disk /dev/sda: 58.24 GiB, 62534975488 bytes, 122138624 sectors

# Both cards show full capacity on PC but reduced capacity on microcontrollers
```

### Recommendation

**✅ Use 16GB cards** - Proven to work reliably across all tested boards  
**❌ Avoid 64GB+ cards** - CircuitPython limitation, will not work

---

## Board Compatibility

**Board reliability varies significantly with 16GB cards.**

| Board | Status | Max Speed | Notes |
|-------|--------|-----------|-------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅✅ Perfect | 12 MHz | Fastest, most consistent, amazing value|
| **ESP32 Feather Huzzah** | ✅✅ Very Good | 4-8 MHz | Generally reliable, pricey at the time of this post|
| **ESP32-S3 DevKitC** | ⚠️ Inconsistent | 12 MHz | Directory operations reliable, file reads inconsistent |
| **ESP32-S2 DevKitC** | ⚠️ Inconsistent | 4-8 MHz | Variable results across testing sessions |

**Important:** With 16GB cards, RP2350 and Huzzah boards perform consistently well. ESP32-S3 and S2 DevKits show varying behavior that can differ between testing sessions and individual boards.

---

## What We Learned Through Extensive Testing

### The Journey

Initial testing suggested some boards (particularly ESP32-S3) had reliability issues with SD cards. After weeks of systematic debugging and testing multiple variables:

**Variables tested:**
- 4 different boards (RP2350, S3, S2, Huzzah)
- Multiple SD cards (Samsung 64GB, Microcenter 64GB, two different 16GB generics)
- Different baudrates (250kHz to 12MHz)
- With/without 100µF capacitor
- Different software versions
- Different initialization sequences

### The Discovery

**Card size is critical:** ALL boards work better with 16GB cards. ALL boards fail with 64GB cards.

**Board consistency varies:** The RP2350 and Huzzah boards showed predictable, repeatable behavior across testing sessions. The ESP32-S3 and S2 DevKits showed variable results that could differ significantly between sessions, including scenarios where directory operations (listdir) would succeed reliably while file content reads would fail after the first attempt.

### Key Observations

**ESP32-S3 and S2 Behavior Patterns:**
- Directory operations (os.listdir) can work flawlessly for hundreds of consecutive operations
- File content reads may succeed once then fail on all subsequent attempts
- The same board and card combination may behave differently across power cycles
- Environmental factors (breadboard quality, wire length, power stability) appear to have greater impact on these boards

**RP2350 and Huzzah Behavior:**
- Consistent performance across multiple testing sessions
- Predictable behavior that matches expectations
- More forgiving of varying environmental conditions

### Key Takeaway

**When troubleshooting SD card issues with CircuitPython:**
1. ✅ **First, try a different SD card** (use 16GB)
2. Consider board choice - RP2350 offers most consistent results
3. Then check wiring, power, code
4. Don't assume it's the SD card reader!

---

## Detailed Comparisons

### 🏆 Waveshare RP2350-Plus (RECOMMENDED)

**Fastest performance, most consistent reliability.**

- Baudrate: 12 MHz
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card
- Result: Consistently reliable across all testing sessions

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Best choice for new projects requiring SD card reliability

---

### ESP32 Feather Huzzah

**Popular board with generally good SD card performance.**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): Works perfectly
- Tested with: 16GB generic card
- Result: Generally reliable, though lost SD card connection during extended continuous audio playback testing

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # Up to 8 MHz
```

**Recommendation:** ⭐⭐⭐⭐ Good choice for most projects

---

### ESP32-S3 DevKitC

**Fast but inconsistent SD card behavior.**

- Baudrate: 12 MHz (capable of high speeds)
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card (two different cards)
- Result: **Directory operations highly reliable (555/555 stress test), but file content reads show inconsistent behavior**

**Observed patterns:**
- os.listdir() operations: 100% success rate across hundreds of consecutive calls
- File content reads: First read may succeed, subsequent reads often fail with I/O errors
- Behavior varies between power cycles and testing sessions
- Same code that fails on S3 works reliably on RP2350

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐ Consider alternative boards if SD card file access reliability is critical

---

### ESP32-S2 DevKitC

**Variable SD card performance across testing.**

- Baudrate: 4 MHz
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card
- Result: Inconsistent results across different testing sessions

**Configuration:**
```python
SD_BAUDRATE = 4_000_000  # 4 MHz
```

**Recommendation:** ⭐⭐ Consider S3 or other boards if SD card access is important

---

## Quick Start

### 1. Choose Board & SD Card

**Boards:**
- **Most reliable:** RP2350 (12 MHz, consistent behavior)
- **Generally reliable:** Huzzah (8 MHz, popular choice)
- **Variable results:** S3 and S2 DevKits (may require troubleshooting)

**SD Cards:**
- **✅ Use:** 16GB cards (proven to work best on all boards)
- **❌ Avoid:** 64GB+ cards (CircuitPython limitation)

### 2. Hardware Setup

- Optional: Add 100µF capacitor to SD card VCC (works with or without)
- Use short wires (<6 inches)
- Power via USB or external supply
- Consider using soldered connections instead of breadboards for ESP32 DevKits

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

# ESP32-S3 DevKitC
elif "s3" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    SD_BAUDRATE = 12_000_000

# ESP32 Feather Huzzah
elif "huzzah32" in board_type and "s3" not in board_type:
    SD_SCK  = board.SCK   # GPIO 5
    SD_MOSI = board.MOSI  # GPIO 18
    SD_MISO = board.MISO  # GPIO 19
    SD_CS   = board.A5    # GPIO 4
    SD_BAUDRATE = 8_000_000

# ESP32-S2 DevKitC
elif "s2" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    SD_BAUDRATE = 4_000_000

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

## What's New in sdcard_helper v1.2.1

### Improved Reliability

**Pre-validation sequence:**
- Validates SD card communication before mounting
- Reads MBR to verify filesystem
- Tests multi-block reads
- Provides better diagnostics

**Better resource management:**
- Shared SPI/SD objects prevent "pin in use" errors
- `unmount()` keeps hardware initialized for reuse
- Multiple mount/unmount cycles work reliably

**Version tracking:**
- `sdcard_helper.__version__` shows current version

**Standalone testing:**
- `read_mbr()` tests card without mounting
- Quickly verify card compatibility

---

## Testing

Check your sdcard_helper version:
```python
import sdcard_helper
# Prints: sdcard_helper v1.2.1
print(sdcard_helper.__version__)
```

Test SD card compatibility (before mounting):
```python
import sdcard_helper
result = sdcard_helper.read_mbr()
# If this hangs, the SD card is incompatible (likely >32GB)
```

Run comprehensive diagnostics:
```python
import test_sd_debug
# Runs automatic diagnostic test

# Optional: Run stress test
test_sd_debug.stress_test_listdir(100)
```

---

## Performance

| Operation | RP2350 | S3 | Huzzah | S2 |
|-----------|--------|-------|--------|-------|
| Baudrate | 12 MHz | 12 MHz | 8 MHz | 4 MHz |
| Mount time | ~0.5s | ~0.5s | ~0.5s | ~0.5s |
| listdir() | <1ms | <1ms | ~2ms | ~2ms |
| Directory reliability | 100% | 100% | ~100% | Variable |
| File read reliability | 100% | Inconsistent | ~95% | Variable |

*All tests with 16GB generic cards*

---

## Troubleshooting

**Mount fails or hangs:**
1. **Check card size first!** Is it >32GB? Use a 16GB card instead
2. Test with `sdcard_helper.read_mbr()` 
3. Try a different SD card (seriously, this is often the issue!)
4. Check wiring
5. Verify FAT32 format (not exFAT)

**Card reports unexpected capacity:**
- If a 64GB card reports ~26-30GB to microcontroller, it's incompatible
- This is a CircuitPython limitation, not a hardware problem
- Switch to 16GB card

**Directory operations work but file reads fail:**
- This pattern has been observed on ESP32-S3 DevKits
- Try power cycling the board
- Consider switching to RP2350 for more consistent results
- Check wiring and power supply quality
- Try soldered connections instead of breadboards

**Inconsistent behavior across power cycles:**
- Observed on ESP32-S2 and S3 DevKits
- May indicate environmental sensitivity
- Improve power supply stability
- Reduce wire lengths
- Consider alternative board (RP2350)

**Slow performance:**
- Check your baudrate setting in `sd_config.py`
- RP2350 and S3 can handle 12MHz
- Huzzah works well at 8MHz
- S2 may need 4MHz

---

## Detailed Test Results: Why 64GB Cards Fail

### Samsung EVO Select 64GB

**PC fdisk output:**
```
Disk /dev/sda: 59.69 GiB, 64088965120 bytes, 125173760 sectors
Device     Boot Start       End   Sectors  Size Id Type
/dev/sda1        2048 125173759 125171712 59.7G  b W95 FAT32
```

**Microcontroller (all boards) output:**
```
Testing SD card communication...
  Block count: 58064896
  Capacity: 28352.00 MB (27.69 GB)
Reading MBR (block 0)...
  ← HANGS HERE (indefinitely)
```

**Result:** Card initializes, reports half capacity, then hangs when attempting to read MBR block. Same behavior on RP2350, S3, Huzzah, and S2.

---

### Microcenter Generic 64GB

**PC fdisk output:**
```
Disk /dev/sda: 58.24 GiB, 62534975488 bytes, 122138624 sectors
```

**Microcontroller (all boards) first attempt:**
```
Testing SD card communication...
  Block count: 55029760
  Capacity: 26870.00 MB (26.24 GB)
Reading MBR...
  ✓ Valid MBR signature: 0xAA55
  Partition type: FAT32 LBA
✅ MBR read successful!
```

**Microcontroller (all boards) second attempt:**
```
  ✗ MBR read failed: [Errno 5] Input/output error
```

**Result:** Card initializes, reports half capacity, first MBR read succeeds, subsequent reads fail with I/O error. Same behavior on all tested boards.

---

### Generic 16GB Cards (Two Different Cards Tested)

**Microcontroller (all boards):**
```
Testing SD card communication...
  Block count: 30535680
  Capacity: 14910.00 MB (14.56 GB)
Reading MBR...
  Reading MBR (block 0)...
  ✓ Valid MBR signature: 0xAA55
  Partition type: FAT32
✅ MBR read successful!
```

**RP2350 stress test:** Consistent 100% success across all operations
**ESP32-S3 directory stress test:** 555/555 consecutive listdir operations (100%)
**ESP32-S3 file access:** Variable results, first read may succeed then subsequent reads fail

---

## Summary: What Really Matters

After extensive testing with multiple boards, cards, and configurations:

### ✅ What Works Consistently
- **16GB SD cards** on RP2350
- **16GB SD cards** on Huzzah (generally)
- Directory operations on most boards
- Baudrates from 4MHz to 12MHz

### ⚠️ What Shows Variable Results
- **File content reads on ESP32-S3 and S2 DevKits**
- Extended continuous playback on some boards
- Performance consistency across power cycles (S2, S3)

### ❌ What Doesn't Work
- **64GB+ SD cards** on any board
- Cards >32GB (CircuitPython limitation)

### 💡 Key Insights
**Card size is critical:** Use 16GB cards for best compatibility.
**Board choice matters:** RP2350 provides most consistent SD card behavior across all operations. ESP32 DevKits (S2, S3) may require additional troubleshooting and show less predictable behavior with file access operations.

---

## SD Card Module Addendum: Testing Results with 5V

### HiLetgo SD Card Module (5V with Level Shifter)

**Tested configuration:**
- Module: [HiLetgo SD Card Reader](https://www.amazon.com/dp/B07BJ2P6X6)
- Power: 5V (required by level shifter)
- SD Card: 16GB generic
- Capacitor: Tested with and without 100µF

**Results:**
- ✅ Works when powered at 5V
- ❌ Does not work at 3.3V (level shifter requires 5V)
- Various reliability experiences across different setups

**Note:** This repository documents our testing with the HiLetgo module. 

For simpler setup and consistent results across all boards, the WaveShare native 3.3V module worked well in our testing and is highly recommended.

### WaveShare Micro SD Storage Board (Native 3.3V)

**Tested configuration:**
- Module: [WaveShare Micro SD Storage Board](https://www.waveshare.com/wiki/Micro_SD_Storage_Board)
- Power: 3.3V (native, no level shifter)
- SD Card: 16GB generic
- Capacitor: Not used

**Results:**
- ✅ ESP32-S3 DevKitC: Directory operations work well, file reads show variable results
- ✅ Waveshare RP2350-Plus: Works consistently across all operations
- ✅ ESP32 Feather Huzzah: Generally reliable performance

---

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [Adafruit SD Card Guide - CircuitPython](https://learn.adafruit.com/adafruit-microsd-spi-sdio/circuitpython)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741) - S3 behavior reports
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)

---

## License

MIT License


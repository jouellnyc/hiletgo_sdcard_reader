# CircuitPython SD Card Reader Guide for HiLetgo SD card reader

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## ⚠️ CRITICAL: Use SD Cards 32 GB or less

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

**All tested boards work reliably with 16GB cards.**

| Board | Status | Max Speed | Notes |
|-------|--------|-----------|-------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅✅ Perfect | 12 MHz | Fastest, best overall, amazing value|
| **ESP32-S3 DevKitC** | ✅✅✅ Excellent | 12 MHz | Works great with 16GB cards |
| **ESP32-S2 DevKitC** | ✅✅✅ Excellent | 4-8 MHz | Reliable, but YMMV |
| **ESP32 Feather Huzzah** | ✅✅ Very Good | 4-8 MHz | Reliable, but YMMV, pricey at the time of this post|

**Important:** With 16GB cards, all boards perform well. Previous reports of board-specific issues were related to incompatible SD cards, not the boards themselves.

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

**ALL boards work perfectly with 16GB cards. ALL boards fail with 64GB cards.**

What appeared to be board-specific problems were like SD card compatibility issues or environmentally issues - I am simply not sure. The ESP32-S3, which initially seemed problematic, runs at 12MHz with 100% reliability when using a 16GB card.

**Stress test results (16GB cards):**
- ESP32-S3: 555/555 consecutive operations (100% success)
- All other boards: 100% reliability

### Key Takeaway

**When troubleshooting SD card issues with CircuitPython:**
1. ✅ **First, try a different SD card** (use 16GB)
2. Then check wiring, power, code
3. Don't assume it's the board!

---

## Detailed Comparisons

### 🏆 Waveshare RP2350-Plus (RECOMMENDED)

**Fastest performance, excellent reliability.**

- Baudrate: 12 MHz
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card
- Result: Just a Beast: Perfect reliability, depite only 512k ram

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Best choice for new projects

---

### ESP32-S3 DevKitC

**Excellent performance with correct SD card.**

- Baudrate: 12 MHz (same as RP2350!)
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card (two different cards)
- Result: **555/555 stress test = 100% reliability**

**Previous misconception:** Early testing suggested this board had timeout issues. Extensive recent testing proves it works perfectly with 16GB cards at full speed.

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Excellent choice, works as well as RP2350

---

### ESP32 Feather Huzzah

**Very popular board, excellent performance.**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): Works perfectly
- Tested with: 16GB generic card
- Result: 100% reliability on fast reads but over the course of a few minutes it failed to continuously play even low quality files well and lost connection to the sd card.

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # Up to 8 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Good  choice, but no reason not to get the 2 MB psram version instead.

---

### ESP32-S2 DevKitC

**Solid performance, good availability.**

- Baudrate: 4 MHz
- Soft reboot (Ctrl+D): Works fine
- Tested with: 16GB generic card
- Result: 100% reliability

**Configuration:**
```python
SD_BAUDRATE = 4_000_000  # 4 MHz
```

**Recommendation:** ⭐⭐⭐⭐ Good choice, but no reason not to get an S3 instead.

---

## Quick Start

### 1. Choose Board & SD Card

**Boards:**
- **All tested boards work great!** Choose based on availability and other project needs
- Fastest: RP2350 or S3 (12 MHz)
- Most popular: Huzzah (8 MHz)
- Budget: S2 (4 MHz)

**SD Cards:**
- **✅ Use:** 16GB cards (proven to work on all boards at all speeds)
- **❌ Avoid:** 64GB+ cards (CircuitPython limitation)

### 2. Hardware Setup

- Optional: Add 100µF capacitor to SD card VCC (works with or without)
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

# ESP32-S3 DevKitC
elif "s3" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    SD_BAUDRATE = 12_000_000  # Works great at full speed!

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
| Read 5MB file | ~1s | ~1s | ~2.5s | ~3s |
| Reliability | 100% | 100% | 100% | 100% |

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

**Slow performance:**
- Check your baudrate setting in `sd_config.py`
- Most boards can handle 4-12MHz with 16GB cards

**"It worked before but doesn't now":**
- Did you change SD cards? Try going back to your original card
- Card compatibility matters more than you think!

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

**Stress test:** 555/555 consecutive operations on ESP32-S3 (100%)

**Result:** Cards initialize correctly, report correct capacity, all operations succeed reliably on all boards at all speeds.

---

## Summary: What Really Matters

After extensive testing with multiple boards, cards, and configurations:

### ✅ What Works
- **16GB SD cards** on any tested board
- All boards (RP2350, S3, S2, Huzzah) at their rated speeds
- With or without 100µF capacitor
- Baudrates from 4MHz to 12MHz

### ❌ What Doesn't Work
- **64GB+ SD cards** on any board
- Cards >32GB (CircuitPython limitation)

### 💡 Key Insight
**Card size is everything.** Board choice matters for speed, but any of the tested boards will work perfectly with a 16GB card.

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

For simpler setup and consistent results across all boards, the WaveShare native 3.3V module worked well in our testing and is highly reccommended.


### WaveShare Micro SD Storage Board (Native 3.3V)

**Tested configuration:**
- Module: [WaveShare Micro SD Storage Board](https://www.waveshare.com/wiki/Micro_SD_Storage_Board)
- Power: 3.3V (native, no level shifter)
- SD Card: 16GB generic
- Capacitor: Not used

**Results:**
- ✅ ESP32-S3 DevKitC: Works perfectly
- ✅ Waveshare RP2350-Plus: Works perfectly
- ✅ ESP32 Feather Huzzah: Works perfectly
---

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [Adafruit SD Card Guide - CircuitPython](https://learn.adafruit.com/adafruit-microsd-spi-sdio/circuitpython)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741) - Original S3 issue report
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)

---

## License

MIT License


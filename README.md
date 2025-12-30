# CircuitPython SD Card Reader Guide

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## ⚠️ CRITICAL: SD Card Size Limitation Observed

**Based on our testing and Adafruit documentation, 64GB cards do not work reliably with CircuitPython.**

Adafruit states: "CircuitPython has trouble recognizing cards bigger than 32GB" ([source](https://learn.adafruit.com/adafruit-microsd-spi-sdio/circuitpython)).

### Our Test Results

| Card | PC Capacity | Microcontroller Reports | Result |
|------|-------------|------------------------|--------|
| Generic 16GB | ~15 GB | ~15 GB | ✅ Works perfectly |
| Samsung 64GB | 59.69 GB | 28.35 GB | ❌ Hangs on MBR read |
| Microcenter 64GB | 58.24 GB | 26.87 GB | ❌ I/O Errors on reads |

**Observations:**
- 16GB card: Worked reliably on all tested boards
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

### What We Did Not Test

- 32GB cards
- 8GB cards
- 4GB cards
- Other capacity sizes between 16GB and 64GB

### Recommendation Based on Our Testing

**✅ What worked:** 16GB generic card  
**❌ What didn't work:** Both 64GB cards tested (Samsung and Microcenter)

Based on Adafruit's documentation and our test results, we recommend using cards 32GB or smaller. However, we only directly verified that 16GB works and 64GB does not.

---

## Board Compatibility

| Board | Status | Max Speed | Key Issue |
|-------|--------|-----------|-----------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅ Perfect | 12 MHz | None |
| **ESP32 Feather Huzzah** | ✅✅✅ Excellent | 8 MHz (4 MHx most reliable)| None (with tested 16GB card) |
| **ESP32-S3 DevKitC** | ⚠ Poor | 250 kHz | 1-second timeout bug |

---

## Detailed Comparisons

### 🏆 Waveshare RP2350-Plus (RECOMMENDED)

**Perfect reliability with tested hardware.**

- Baudrate: 12 MHz
- Soft reboot (Ctrl+D): Works fine
- Cache bug: No
- Timeout issue: No
- Audio quality: Best
- Tested with: 16GB generic card (worked perfectly)

**Configuration:**
```python
SD_BAUDRATE = 12_000_000  # 12 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Use for all projects

---

### ESP32 Feather Huzzah

**Excellent performance with tested hardware.**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): ✅ Works perfectly
- Cache bug: No
- Timeout issue: No
- Audio quality: Excellent
- Tested with: 16GB generic card (worked perfectly)

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # Up to 8 MHz
```

**Recommendation:** ⭐⭐⭐⭐⭐ Excellent choice

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

### 1. Choose Board & SD Card

**Boards:**
- **New projects:** Waveshare RP2350-Plus or ESP32 Feather Huzzah
- **ESP32 projects:** Huzzah - avoid DevKitC

**SD Cards:**
- **✅ Tested working:** 16GB generic card
- **❌ Tested NOT working:** 64GB cards (Samsung and Microcenter brands both failed)
- **Recommendation:** Use 16GB cards or refer to Adafruit's guidance about 32GB limit

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

### Improved Reliability

Version 1.2.0 introduces a pre-validation sequence before mounting:

1. **`_validate_sd_communication()`** - Reads block count
2. **`_read_mbr()`** - Reads Master Boot Record
3. **`_test_multiblock_read()`** - Tests sequential reads
4. **Then** `storage.mount()` - Mounts filesystem

This sequence improved reliability in our testing with the 16GB card across soft reboots and multiple mount/unmount cycles.

### Other Improvements in v1.2.0

- **Shared SPI/SD objects:** `read_mbr()` and `mount()` reuse hardware initialization
- **Modular architecture:** Clean separation of initialization, validation, and mounting
- **Better error handling:** Clear diagnostics at each step
- **Version tracking:** `sdcard_helper.__version__`
- **Standalone MBR testing:** Test card compatibility without mounting

---

## Testing

Check your sdcard_helper version:
```python
import sdcard_helper
# Prints: sdcard_helper v1.2.0
print(sdcard_helper.__version__)
```

Test SD card compatibility:
```python
import sdcard_helper
result = sdcard_helper.read_mbr()
# Shows card capacity and attempts to read MBR
```

---

## Known Issues

### Issue 1: 1-Second Timeout (DevKitC)

**Symptom:** Files disappear after 1 second idle

**Affected:** DevKitC only  

**Solution:** Keepalive pattern or use different board

### Issue 2: Cache Bug (DevKitC)

**Symptom:** First `listdir()` returns empty

**Solution:** Add settling time after mount
```python
storage.mount(vfs, "/sd")
time.sleep(1.0)
_ = os.listdir("/sd")  # Prime cache
os.sync()
```

---

## Performance

| Operation | Waveshare | Huzzah | DevKitC |
|-----------|-----------|--------|---------|
| Mount time | ~0.5s | ~0.5s | ~0.5s |
| listdir() | <1ms | ~2ms | ~8ms |
| Read 5MB file | ~1s | ~2.5s | ~10s |

*Tests performed with 16GB generic card*

---

## Troubleshooting

**Mount fails or hangs:**
1. Check card size - our 64GB cards failed, 16GB worked
2. Test with `sdcard_helper.read_mbr()` 
3. Check wiring
4. Verify FAT32 format
5. Try lowering baudrate

**Card reports unexpected capacity:**
- Both our 64GB cards reported ~26-28GB to microcontroller
- Same cards showed correct ~58-60GB capacity on PC
- This was one symptom before they failed to read data

**Files not appearing:**
- Waveshare/Huzzah: Check SD format
- DevKitC: Implement keepalive or switch boards

---

## Detailed Test Results: 64GB Card Failures

### Samsung EVO Select 64GB

**PC fdisk output:**
```
Disk /dev/sda: 59.69 GiB, 64088965120 bytes, 125173760 sectors
Device     Boot Start       End   Sectors  Size Id Type
/dev/sda1        2048 125173759 125171712 59.7G  b W95 FAT32
```

**Microcontroller (Huzzah32) output:**
```
Testing SD card communication...
  Block count: 58064896
  Capacity: 28352.00 MB (27.69 GB)
Reading MBR (block 0)...
  ← HANGS HERE (indefinitely)
```

**Result:** Card initializes, reports half capacity, then hangs when attempting to read MBR block.

---

### Microcenter Generic 64GB

**PC fdisk output:**
```
Disk /dev/sda: 58.24 GiB, 62534975488 bytes, 122138624 sectors
Device     Boot  Start       End   Sectors  Size Id Type
/dev/sda1         8192    532479    524288  256M  c W95 FAT32 (LBA)
/dev/sda2       532480 122138623 121606144   58G 83 Linux
```

**Microcontroller (Huzzah32) first attempt:**
```
Testing SD card communication...
  Block count: 55029760
  Capacity: 26870.00 MB (26.24 GB)
Reading MBR...
  Reading MBR (block 0)...
  ✓ Valid MBR signature: 0xAA55
  Partition type: FAT32 LBA
✅ MBR read successful!
```

**Microcontroller (Huzzah32) second attempt:**
```
Testing SD card communication...
  Block count: 55029760
  Capacity: 26870.00 MB (26.24 GB)
Reading MBR...
  Reading MBR (block 0)...
  ✗ MBR read failed: [Errno 5] Input/output error
```

**Result:** Card initializes, reports half capacity, first MBR read succeeds, subsequent reads fail with I/O error.

---

### Generic 16GB Card

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

**Result:** Card initializes correctly, reports correct capacity, all operations succeed reliably.

---

## What We Learned

**Facts from our testing:**

1. A 16GB generic card worked perfectly on all three boards
2. Two different 64GB cards both failed (in different ways)
3. Both 64GB cards reported approximately half their actual capacity to microcontrollers
4. Both 64GB cards showed correct capacity when connected to PC
5. Failure modes varied between cards:
   - Samsung: Hung on first MBR read
   - Microcenter: First read succeeded, subsequent reads failed
6. The pre-validation sequence in sdcard_helper v1.2.0 improved reliability with the working 16GB card

**What this suggests (but we cannot definitively prove):**

- There appears to be a capacity-related incompatibility with cards larger than some threshold
- This aligns with Adafruit's documented 32GB limit
- Different large cards fail in different ways

**What we recommend:**

- Use 16GB cards (proven to work in our testing)
- Avoid 64GB cards (proven NOT to work in our testing)
- For other sizes, refer to Adafruit's guidance or test before committing to a project

---

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [Adafruit SD Card Guide - CircuitPython](https://learn.adafruit.com/adafruit-microsd-spi-sdio/circuitpython)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741)
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)

---

## License

MIT License


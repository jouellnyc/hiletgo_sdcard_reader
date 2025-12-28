# CircuitPython SD Card Reader Guide

Quick reference for SD card compatibility across microcontroller boards with CircuitPython.

**Hardware tested:** [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6) with level shifter  
**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## Board Compatibility

| Board | Status | Max Speed | Key Issue |
|-------|--------|-----------|-----------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅ Perfect | 12 MHz | None |
| **ESP32 Feather Huzzah** | ✅✅ Very Good | 8 MHz | Soft reboot hangs mount |
| **ESP32-S3 DevKitC** | ⚠️ Poor | 250 kHz | 1-second timeout bug |

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

**Good performance but requires hard reset.**

- Baudrate: Up to 8 MHz
- Soft reboot (Ctrl+D): **HANGS on mount** ❌
- Cache bug: No
- Timeout issue: No
- Audio quality: Good

**Critical Issue:** After Ctrl+D, `storage.mount()` hangs at VfsFat creation. SD card stays powered but data channel breaks.

**Configuration:**
```python
SD_BAUDRATE = 8_000_000  # 4 up toHz
```

**Recommendation:** ⭐⭐⭐⭐ Good choice, just avoid soft reboot

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

- **New projects:** Waveshare RP2350-Plus
- **ESP32 projects:** Huzzah (avoid DevKitC)

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
    SD_BAUDRATE = 4_000_000

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

## Testing

Run diagnostic test:
```python
import test_sd_debug
```

Detects board, checks for bugs, provides specific recommendations.

---

## Known Issues

### Issue 1: Soft Reboot Hang (Huzzah & DevKitC)

**Symptom:** Mount hangs after Ctrl+D

**Solution:** Always use RESET button, add soft reboot detection

**Affected:** Huzzah
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

---

## Rules

### ✅ DO:
- Use RESET button (ESP32 boards)
- Add 100µF capacitor on SD VCC
- Use short wires

### ❌ DON'T:
- Use Ctrl+D with Huzzah/DevKitC
- Use DevKitC for SD projects
- Use wires >6 inches

---

## Troubleshooting

**Mount fails:**
1. Check wiring
2. Verify FAT32 format
3. Press RESET (not Ctrl+D)
4. Lower baudrate

**Files not appearing:**
- Waveshare: Check SD format
- Huzzah: Use RESET not Ctrl+D
- DevKitC: Implement keepalive or switch boards

**Hangs on mount:**
- Cause: Soft reboot (Ctrl+D)
- Solution: Press RESET, add soft reboot detection

---

## Related Links

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)
- [CircuitPython Issue #10741](https://github.com/adafruit/circuitpython/issues/10741)
- [CircuitPython Issue #10758](https://github.com/adafruit/circuitpython/issues/10758)

---

## License

MIT License

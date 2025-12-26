# ESP32 SD Card Reader Guide: Board Compatibility

Quick reference for using HiLetgo SD card readers with ESP32 boards and CircuitPython.

## Hardware Compatibility

| Board | Status | Baudrate | Notes |
|-------|--------|----------|-------|
| **ESP32 Feather Huzzah** | ✅ Excellent | Up to 4MHz | Recommended for production |
| **ESP32-S3 DevKitC** | ⚠️ Functional | 250kHz max | Requires workarounds |

## Quick Setup

### Pin Configuration (sd_config.py)
```python
import board

SD_SCK = board.IO36    # Clock
SD_MOSI = board.IO35   # Data out
SD_MISO = board.IO37   # Data in
SD_CS = board.IO34     # Chip select
SD_BAUDRATE = 250000   # 250kHz for S3, up to 4MHz for Huzzah
SD_MOUNT = "/sd"
```

### Basic Usage
```python
import sdcard_helper

if sdcard_helper.mount():
    files = sdcard_helper.list_files()
    print(f"Found {len(files)} files")
```

## ESP32-S3 DevKitC: Required Configuration

**sdcard_helper.py settings:**
```python
SD_BAUDRATE = 250000      # Critical - higher speeds fail
time.sleep(2.0)           # Settling time (in mount())
time.sleep(1.0)           # Cache priming delay
readonly=True             # Stability (no writes needed)
```

**Common issues:**
- Files invisible after mount → Call `list_tracks()` twice
- `refresh_sd()` fails with "IO pin in use" → Use Ctrl+D instead
- Device crashes → Powered USB hub required + 100µF capacitor

## ESP32 Feather Huzzah: Works Out of Box

**sdcard_helper.py settings:**
```python
SD_BAUDRATE = 1000000     # Can go up to 4MHz
time.sleep(1.0)           # Settling time
time.sleep(0.5)           # Cache priming delay
```

**No workarounds needed** - stable and reliable.

## Hardware Requirements

### Both Boards
- **100µF capacitor** on SD VCC (mandatory)
- HiLetgo SD reader with level shifter (5V powered)
- Short wires (<6 inches)

### ESP32-S3 Specific
- Powered USB hub (not just computer USB port)
- External 3.3V regulator recommended for SD card
- Lower baudrate (250kHz) required

## Known Issues & Solutions

| Issue | Board | Solution |
|-------|-------|----------|
| Files not visible after mount | S3 | Call listing function twice |
| "IO pin in use" on refresh | S3 | Use Ctrl+D soft reboot |
| Device crashes during SD ops | S3 | Lower baudrate to 250kHz |
| Rapid calls cause files to disappear | Both | Built-in rate limiting (500ms) |

## CircuitPython SD Card Bug

**Symptom:** Empty `listdir()` after soft reboot  
**Root cause:** SD card directory cache not initialized  
**Solution:** Use `sdcard_helper.py` (handles settling + cache priming)

Related issues: [#10741](https://github.com/adafruit/circuitpython/issues/10741), [#10758](https://github.com/adafruit/circuitpython/issues/10758)

## Recommendation

**Production projects:** Use ESP32 Feather Huzzah  
**Development/prototyping:** Either board works (S3 requires care)

## Files
- `sdcard_helper.py` - Robust SD mounting with timing fixes
- `sd_config.py` - Pin configuration
- `play.py` - Example music player

## Technical Notes

**Why S3 is problematic:**
- Weaker 3.3V regulator (marginal under SD + audio load)
- Level shifter expects 5V signals, ESP32 outputs 3.3V
- Less mature CircuitPython support
- Pin conflicts prevent clean remounting

**Why Huzzah works better:**
- Stronger GPIO drivers
- Better power regulation (Adafruit board design)
- More mature CircuitPython support
- Stable across all operations

---

**Questions?** See full README or open an issue with board model + SD module details.

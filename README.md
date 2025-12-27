# CircuitPython SD Card Reader Guide: Board Compatibility

Quick reference for using SD card readers (tested with [HiLetgo SD card reader](https://www.amazon.com/dp/B07BJ2P6X6)) with various microcontroller boards and CircuitPython.

**Related project:** [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A)

---

## Board Compatibility Summary

| Board | SD Card Status | Speed | Notes |
|-------|----------------|-------|-------|
| **🏆 Waveshare RP2350-Plus** | ✅✅✅ Flawless | Up to 12 MHz | **RECOMMENDED** - Perfect for production |
| **ESP32 Feather Huzzah** | ✅ Very Good | Up to 4 MHz | Requires soft reboot workaround |
| **ESP32-S3 DevKitC** | ⚠️ Problematic | 250 kHz max | Has 1-second timeout issue |

---

## Detailed Board Comparisons

### 🏆 Waveshare RP2350-Plus (RECOMMENDED)

**Status:** Perfect, no issues

| Feature | Status | Details |
|---------|--------|---------|
| **SD card mount** | ✅ Perfect | Fast and reliable |
| **Directory listing** | ✅ Perfect | No cache bug |
| **File operations** | ✅ Perfect | No timeout issues |
| **Soft reboot (Ctrl+D)** | ✅ Works | No issues |
| **Audio playback** | ✅ Excellent | Best sound quality |

**Configuration:**
- Baudrate: **12 MHz** (fastest of all boards tested)
- Settling time: None needed
- Special handling: None required

**Hardware tested:**
- SD card reader: HiLetgo with level shifter
- Power: USB or external (both work)
- No capacitor required (but 100µF recommended for best practice)

**Recommendation:** ⭐⭐⭐⭐⭐ **Use this for all projects**  
Perfect reliability, fastest speed, best audio quality. No workarounds needed.

---

### ESP32 Feather Huzzah

**Status:** Very good with one caveat

| Feature | Status | Details |
|---------|--------|---------|
| **SD card mount** | ✅ Good | Reliable at 4 MHz |
| **Directory listing** | ✅ Good | No cache bug |
| **File operations** | ✅ Good | No timeout issues |
| **Soft reboot (Ctrl+D)** | ❌ **HANGS** | Must use hard reset |
| **Audio playback** | ✅ Good | Stable playback |

**Configuration:**
- Baudrate: **4 MHz**
- Settling time: Minimal (0.1s just to be safe)
- Special handling: Soft reboot protection required

**Critical Issue: Soft Reboot Hang**

After Ctrl+D soft reboot, mounting the SD card will **hang at VfsFat creation**.
```python
# Works after hard reset:
storage.mount(vfs, "/sd")  # ✅ Success

# After Ctrl+D:
storage.mount(vfs, "/sd")  # ❌ HANGS (never returns)
```

**Why this happens:**
- After soft reboot, SD card stays powered but in confused state
- Command interface works (SDCard init succeeds)
- Data read channel broken (VfsFat creation hangs trying to read filesystem)
- Only hard reset recovers the SD card

**Workaround:** Detect and prevent soft reboot mounting
```python
import supervisor

if supervisor.runtime.run_reason == supervisor.RunReason.SOFT_REBOOT:
    print("⚠️  Soft reboot detected - SD mount will hang")
    print("Press RESET button instead")
    raise SystemExit

# Safe to mount after hard reset
```

**Hardware tested:**
- SD card reader: HiLetgo with level shifter (5V power)
- 100µF capacitor on SD VCC recommended
- Powered USB hub not required

**Recommendation:** ⭐⭐⭐⭐ Good for projects, but **always use hard reset (RESET button), never Ctrl+D**

---

### ESP32-S3 DevKitC

**Status:** Problematic - not recommended for SD cards

| Feature | Status | Details |
|---------|--------|---------|
| **SD card mount** | ⚠️ Slow | Works at 250 kHz only |
| **Directory listing** | ❌ **1s timeout** | Cache invalidates after 1s idle |
| **File operations** | ⚠️ Unreliable | Timeout causes failures |
| **Soft reboot (Ctrl+D)** | ❌ **HANGS** | Same as Huzzah |
| **Audio playback** | ⚠️ Works | Slower, requires keepalive |

**Configuration:**
- Baudrate: **250 kHz** (4x slower than Huzzah)
- Settling time: 0.5s
- Special handling: Keepalive required + soft reboot protection

**Critical Issue: 1-Second Timeout**

The SD card **dumps its directory cache after exactly 1 second of SPI inactivity**.
```python
files = os.listdir("/sd")  # ✅ 10 files
time.sleep(1.0)            # Wait 1 second
files = os.listdir("/sd")  # ❌ 0 files (cache dumped!)
```

**Why this happens:**
- DevKitC's weaker GPIO + HiLetgo level shifter = poor signal quality
- SD card interprets gaps as "end of session"
- Enters power-saving mode after 1 second
- Cache invalidated, returns empty directory

**This affects ALL speeds:**
- 250 kHz: 1 second timeout
- 1 MHz: 1 second timeout
- Higher speeds: Unstable/crash

**Workaround: Keepalive Pattern**

Must prevent >1 second idle periods:
```python
import sdcard_helper
import time

if sdcard_helper.mount():
    while True:
        # Your code here
        
        # Keep SD awake every 0.9 seconds
        time.sleep(0.8)
        sdcard_helper.keepalive()  # Dummy operation to reset timeout
```

**Hardware tested:**
- SD card reader: HiLetgo with level shifter (5V power)
- 100µF capacitor on SD VCC required
- Powered USB hub required
- Various SD card brands all show same behavior

**Recommendation:** ⭐ **Not recommended for SD card projects**  
Use Waveshare or Huzzah instead. If you must use DevKitC, implement keepalive pattern or wait for 3.3V native SD module (no level shifter).

---

## Hardware Requirements

### Power Supply

**All boards:**
- 100µF capacitor on SD card VCC line (recommended, sometimes required)
- Stable power source (USB or external)

**DevKitC specifically:**
- Powered USB hub recommended
- 100µF capacitor required (not optional)

### SD Card Modules

**Tested and working:**
- HiLetgo SD card reader with level shifter (5V powered)
  - Works best with Waveshare and Huzzah
  - Problematic with DevKitC due to signal quality

**Recommended for DevKitC (not yet tested in this guide):**
- 3.3V native SD card modules (no level shifter)
  - Adafruit MicroSD Breakout
  - SparkFun MicroSD Breakout
  - Generic "SPI SD Module" without level shifter

---

## CircuitPython SD Card Issues

### Issue 1: Schrödinger's Files (Cache Bug)

**Symptom:**
```python
storage.mount(vfs, "/sd")
files = os.listdir("/sd")  # Returns [] (empty)
time.sleep(2)
files = os.listdir("/sd")  # Returns ['file1.mp3', 'file2.wav']
```

Files exist (disk shows usage) but first `listdir()` sees nothing.

**Root cause:** SD card directory cache not initialized after mount

**Affected boards:**
- ✅ Waveshare: No issue
- ✅ Huzzah: No issue  
- ⚠️ DevKitC: Can occur, but overshadowed by timeout issue

**Solution:** Add settling time after mount
```python
storage.mount(vfs, "/sd")
time.sleep(1.0)              # Let hardware settle
_ = os.listdir("/sd")        # Prime directory cache
os.sync()
time.sleep(0.5)
# Now listdir() works reliably
```

**Related CircuitPython issues:**
- [#10741](https://github.com/adafruit/circuitpython/issues/10741) - Initial report
- [#10758](https://github.com/adafruit/circuitpython/issues/10758) - Soft reboot variant

### Issue 2: Soft Reboot Hang

**Symptom:**
After Ctrl+D soft reboot, `storage.mount()` hangs forever at VfsFat creation.

**Root cause:** 
After soft reboot, SD card stays powered but in corrupted state:
- Command interface: Works
- Data read channel: Broken
- VfsFat tries to read filesystem → hangs

**Affected boards:**
- ✅ Waveshare: No issue
- ❌ Huzzah: **ALWAYS hangs**
- ❌ DevKitC: **ALWAYS hangs** (assumed, not extensively tested)

**Solution:** Always use hard reset, never Ctrl+D
```python
import supervisor

# Detect and abort on soft reboot
if supervisor.runtime.run_reason == supervisor.RunReason.SOFT_REBOOT:
    print("⚠️  Soft reboot detected - use RESET button")
    raise SystemExit
```

### Issue 3: 1-Second Timeout (DevKitC Only)

**Symptom:**
```python
files = os.listdir("/sd")  # 10 files
time.sleep(1.0)
files = os.listdir("/sd")  # 0 files
```

**Root cause:** Signal quality issues cause SD card to aggressively power-save

**Affected boards:**
- ✅ Waveshare: No issue
- ✅ Huzzah: No issue
- ❌ DevKitC: **Always present**

**Solution:** Keepalive pattern (see DevKitC section above)

---

## Quick Start Guide

### Step 1: Choose Your Board

**For new projects:** Waveshare RP2350-Plus  
**If using ESP32:** Huzzah (avoid DevKitC for SD cards)

### Step 2: Hardware Setup

1. Connect SD card reader to board (see pin configs below)
2. Add 100µF capacitor to SD card VCC
3. Use short wires (<6 inches)
4. Power board via USB or external supply

### Step 3: Software Setup

Copy these files to your CIRCUITPY drive:
- `sd_config.py` - Pin configuration
- `sdcard_helper.py` - Mounting helper with workarounds
- Your main code (e.g., `play.py`, `test_sd_bug.py`)

### Step 4: Pin Configuration

Create `sd_config.py`:
```python
"""
sd_config.py
Universal configuration for RP2350, ESP32, and ESP32-S3
"""
import board

board_type = board.board_id
print(f"--- SD Config: Detected {board_type} ---")

# ============================================
# Waveshare RP2350-Plus
# ============================================
if "rp2350" in board_type:
    SD_SCK  = board.GP18
    SD_MOSI = board.GP19
    SD_MISO = board.GP16
    SD_CS   = board.GP17
    SD_BAUDRATE = 12_000_000  # 12 MHz - perfect!

# ============================================
# ESP32 Feather Huzzah
# ============================================
elif "huzzah32" in board_type and "s3" not in board_type:
    SD_SCK  = board.SCK   # GPIO 5
    SD_MOSI = board.MOSI  # GPIO 18
    SD_MISO = board.MISO  # GPIO 19
    SD_CS   = board.A5    # GPIO 4
    SD_BAUDRATE = 4_000_000  # 4 MHz

# ============================================
# ESP32-S3 DevKitC
# ============================================
elif "s3" in board_type:
    SD_SCK  = board.IO12
    SD_MOSI = board.IO11
    SD_MISO = board.IO13
    SD_CS   = board.IO16
    SD_BAUDRATE = 250_000  # 250 kHz only (slow but stable)

# ============================================
# Fallback
# ============================================
else:
    print("⚠️ Unknown board - using defaults")
    SD_SCK  = board.SCK
    SD_MOSI = board.MOSI
    SD_MISO = board.MISO
    SD_CS   = board.D5
    SD_BAUDRATE = 1_000_000

# Shared settings
SD_MOUNT = "/sd"
SD_TEST_FILE = SD_MOUNT + "/test.txt"

print(f"    Baudrate: {SD_BAUDRATE:,} Hz")
```

### Step 5: Basic Usage
```python
import sdcard_helper

# Mount SD card (includes all workarounds)
if sdcard_helper.mount():
    print("✓ SD card ready!")
    
    # List files
    files = sdcard_helper.list_files()
    print(f"Found {len(files)} files")
    
    # Use files...
    for file in files:
        print(f"  - {file}")
```

---

## Testing Your Setup

Run the included test to verify your board:
```python
# Copy test_sd_bug.py to your board, then:
import test_sd_bug
```

This will:
- Detect your board automatically
- Check for soft reboot issues
- Test for cache bugs
- Measure timeout behavior
- Provide specific recommendations

---

## Important Rules

### ✅ DO:
- Use hard reset (RESET button) when developing with SD cards
- Add 100µF capacitor on SD card VCC
- Use short wires
- Keep wires away from high-speed signals

### ❌ DON'T:
- **Never use Ctrl+D (soft reboot) with SD cards on ESP32 boards**
- Don't use long wires (>6 inches)
- Don't expect DevKitC to work well with SD cards
- Don't mix 5V and 3.3V power without level shifters

---

## Troubleshooting

### "Mount failed" Error

1. Check wiring (verify against `sd_config.py`)
2. Verify SD card is FAT32 formatted
3. Add/check 100µF capacitor on SD VCC
4. Try lower baudrate in `sd_config.py`
5. Press RESET button (not Ctrl+D)

### Files Not Appearing

**Waveshare:** Should work immediately - check SD card is formatted correctly

**Huzzah:** 
- Ensure you used hard reset (not Ctrl+D)
- Files should appear immediately at 4 MHz

**DevKitC:**
- Files may disappear after 1 second
- Implement keepalive pattern or use different board

### Board Hangs on Mount

**Symptom:** Code stops at `storage.mount()` or `storage.VfsFat()`

**Cause:** Soft reboot (Ctrl+D) was used

**Solution:** 
1. Press RESET button
2. Run code immediately
3. Add soft reboot detection to your code

### Random Crashes

- Check power supply (brownouts)
- Add bigger capacitor (220µF)
- Lower baudrate
- Use powered USB hub (DevKitC)

---

## Performance Comparison

| Operation | Waveshare | Huzzah | DevKitC |
|-----------|-----------|--------|---------|
| **Mount time** | ~0.5s | ~0.5s | ~0.5s |
| **listdir() speed** | <1ms | ~2ms | ~8ms |
| **Read 5MB MP3** | ~1s | ~2.5s | ~10s |
| **Reliability** | Perfect | Excellent | Poor |

---

## Recommendations

### For Audio Projects
**Winner:** Waveshare RP2350-Plus
- Best audio quality
- Fastest SD card access
- No workarounds needed
- Most reliable

### For ESP32 Projects
**Winner:** ESP32 Feather Huzzah
- Good performance
- Reliable (with hard reset)
- Widely available
- Well documented

### To Avoid
**Avoid:** ESP32-S3 DevKitC for SD card projects
- 1-second timeout issue unfixable
- 4x slower than Huzzah
- Requires complex workarounds
- Use it for non-SD projects instead

---

## Files in This Repository

- **`sd_config.py`** - Universal pin configuration
- **`sdcard_helper.py`** - Mount helper with all workarounds
- **`test_sd_bug.py`** - Comprehensive SD card test
- **`README.md`** - This file
- **`examples/`** - Usage examples

---

## Contributing

Found an issue or tested a new board? Pull requests welcome!

Please include:
- Board model and CircuitPython version
- SD card reader model
- Test results from `test_sd_bug.py`
- Any workarounds you discovered

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- Adafruit for CircuitPython and helpful community
- Claude.ai for extensive debugging assistance
- All contributors who tested various hardware combinations

---

## See Also

- [ESP32 MAX98357A Audio Player](https://github.com/jouellnyc/esp32_MAX98357A) - Music player using these SD card helpers
- [CircuitPython Documentation](https://docs.circuitpython.org/)
- [SD Card Issues #10741](https://github.com/adafruit/circuitpython/issues/10741)
- [SD Card Issues #10758](https://github.com/adafruit/circuitpython/issues/10758)


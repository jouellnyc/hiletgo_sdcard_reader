# ESP32 SD Card Reader Guide: Board Compatibility

Quick reference for using HiLetgo SD card readers with ESP32 boards and CircuitPython.

## Hardware Compatibility

| Board | Status | Baudrate | Notes |
|-------|--------|----------|-------|
| **Waveshare RP2350-Plus** |✅✅✅FFlawless | up to 12MHZ | Recommended for production|
| **ESP32 Feather Huzzah** | ✅Very Good | Up to 4MHz | Required Workarounds |
| **ESP32-S3 DevKitC** | ⚠️ Barely Functional | 250kHz max | Unstable - sometimes worked |

Also See: https://github.com/jouellnyc/esp32_MAX98357A

## Hardware Requirements

### Both Boards
- **100µF capacitor** on SD VCC (mandatory)
- HiLetgo SD reader with level shifter (5V powered)
- Short wires (<6 inches)

## CircuitPython SD Card Bug

**Symptom:** Empty `listdir()` after soft reboot  
**Root cause:** SD card directory cache not initialized  
**Solution:** Use `sdcard_helper.py` (handles settling + cache priming)

Related issues: [#10741](https://github.com/adafruit/circuitpython/issues/10741), [#10758](https://github.com/adafruit/circuitpython/issues/10758)

## Recommendation
**Development/prototyping:** Either Huzzah or WaveShare board works 
**Production projects:** WaveShare Board 

"""
sd_config.py
Single source of truth for SD card configuration
"""

#ESP32 HUZZAH
#https://www.adafruit.com/product/3591
#NOT https://www.adafruit.com/product/5900 !

import board

# ============================================
# SD Card Configuration
# ============================================
SD_SCK  = board.SCK    # GPIO5
SD_MOSI = board.MOSI   # GPIO18
SD_MISO = board.MISO   # GPIO19
SD_CS   = board.A5     # GPIO4


# ============================================
# SD Settings
# ============================================

#SD_BAUDRATE = 1_000_000 Jack Hammer?
SD_BAUDRATE = 4_000_000
SD_MOUNT    = "/sd"

SD_TEST_FILE = SD_MOUNT + "/test.txt"

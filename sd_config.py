"""
sd_config.py
Single source of truth for SD card configuration
"""

import board

# ============================================
# Wiring
# ============================================
#   CS   → GPIO 16
#   MOSI → GPIO 11
#   MISO → GPIO 13
#   SCK  → GPIO 12

SD_SCK  = board.IO12
SD_MOSI = board.IO11
SD_MISO = board.IO13
SD_CS   = board.IO16

# ============================================
# SD Settings
# ============================================

#SD_BAUDRATE = 1_000_000
SD_BAUDRATE = 4_000_000
SD_MOUNT    = "/sd"

SD_TEST_FILE = SD_MOUNT + "/test.txt"
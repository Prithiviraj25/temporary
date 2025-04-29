import os
from pathlib import Path

# Base directories
BASE_DIR = Path("/data/students/Automation")
TEMP_DIR = BASE_DIR / "temp"
PATCHES_DIR = BASE_DIR / "patches"
STABLE_PATCHES_DIR = TEMP_DIR / "stable-patches"
DATA_DIR = Path("/data/students/data")

# File patterns
BUILD_LOG_PATTERN = "*_build.log"
CHECK_LOG_PATTERN = "*_check.log"
PATCH_PATTERNS = ["*.patch", "*.diff"]

# Other constants
BUILDENV_FILENAME = "buildenv"
LOG_STABLE_DIR = "log.STABLE"
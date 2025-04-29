import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from error_handling import BuildError
from config import TEMP_DIR, BUILD_LOG_PATTERN, CHECK_LOG_PATTERN, LOG_STABLE_DIR

logger = logging.getLogger(__name__)

def run_zopen_build(build_dir: Path) -> Tuple[bool, Optional[Path]]:
    """Run zopen build and capture logs"""
    logger.info(f"🚀 Running 'zopen build -vv' in: {build_dir}")
    
    try:
        result = subprocess.run(
            ["zopen", "build", "-vv"],
            cwd=str(build_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='ignore'
        )
    except Exception as e:
        error_msg = f"Failed to run zopen build: {e}"
        logger.error(error_msg)
        raise BuildError(error_msg)

    logger.info("⏳ Waiting for log file to be written...")
    time.sleep(2)

    build_log = find_latest_build_log(build_dir)
    if not build_log:
        error_msg = "No build log files found"
        logger.error(error_msg)
        raise BuildError(error_msg)

    logger.info(f"📄 Found latest log file: {build_log}")
    
    if check_for_successful_build(build_dir):
        logger.info("✅ The tool is built without any errors")
        return True, None
    
    return False, build_log

def find_latest_build_log(build_dir: Path) -> Optional[Path]:
    """Find the latest build log file"""
    log_dir = build_dir / LOG_STABLE_DIR
    log_files = list(log_dir.glob(BUILD_LOG_PATTERN))
    
    if not log_files:
        return None
        
    return max(log_files, key=lambda f: f.stat().st_mtime)

def check_for_successful_build(build_dir: Path) -> bool:
    """Check if build was successful by looking for check logs"""
    log_dir = build_dir / LOG_STABLE_DIR
    check_logs = list(log_dir.glob(CHECK_LOG_PATTERN))
    return len(check_logs) > 0

def check_build_errors(log_file: Path) -> str:
    """Check build log for errors"""
    try:
        logger.info(f"Checking build log for errors: {log_file}")
        
        if not log_file.exists():
            error_msg = f"Log file does not exist: {log_file}"
            logger.error(error_msg)
            raise BuildError(error_msg)

        result = subprocess.run(
            ['grep', '-i', '-A', '3', 'error:', str(log_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            logger.error("❌ Build failed with errors")
            return result.stdout
        elif result.returncode == 1:
            logger.info("✅ Build successful. No errors found.")
            return ""
        else:
            error_msg = f"Grep encountered an issue: {result.stderr}"
            logger.error(error_msg)
            raise BuildError(error_msg)

    except Exception as e:
        error_msg = f"Error checking build log: {e}"
        logger.error(error_msg)
        raise BuildError(error_msg)
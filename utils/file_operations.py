import re
import logging
from pathlib import Path
from typing import Optional, Tuple
from error_handling import FileOperationError
from config import BUILDENV_FILENAME

logger = logging.getLogger(__name__)

def check_build_type(buildenv_path: Path) -> str:
    """Check if build is stable"""
    try:
        content = buildenv_path.read_text(encoding='utf-8', errors='ignore')
        return 'stable' if 'STABLE' in content else 'unknown'
    except Exception as e:
        logger.warning(f"⚠️ Could not read buildenv: {e}")
        return 'unknown'

def extract_source_folder_name(buildenv_path: Path) -> Optional[str]:
    """Extract tool-version folder name from buildenv"""
    try:
        content = buildenv_path.read_text()
        for line in content.splitlines():
            match = re.match(r'([A-Z0-9_]+)_VERSION\s*=\s*[\'"](.+?)[\'"]', line)
            if match:
                tool_name = match.group(1).lower()
                version = match.group(2)
                return f"{tool_name}-{version}"
        logger.warning("No *_VERSION assignment found in buildenv")
        return None
    except FileNotFoundError:
        logger.error(f"File not found: {buildenv_path}")
        return None
    except Exception as e:
        logger.error(f"Error parsing buildenv: {e}")
        return None

def create_jsonl_file(source_folder_name: str) -> Path:
    """Create empty JSONL file for data collection"""
    data_file = Path(f"/data/students/data/{source_folder_name}.jsonl")
    try:
        data_file.touch()
        logger.info(f"✅ Created empty .jsonl file at: {data_file}")
        return data_file
    except Exception as e:
        error_msg = f"Failed to create JSONL file: {e}"
        logger.error(error_msg)
        raise FileOperationError(error_msg)
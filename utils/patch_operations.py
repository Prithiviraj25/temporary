import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict
from error_handling import PatchError
from config import PATCHES_DIR, STABLE_PATCHES_DIR, PATCH_PATTERNS
import re,subprocess,json

logger = logging.getLogger(__name__)

def move_stable_patches(source_dir: Path, destination_dir: Path) -> list[str]:
    """Move stable patches to destination directory"""
    moved_files = []
    try:
        for pattern in ['*.c.patch', '*.h.patch']:
            for patch_file in source_dir.glob(pattern):
                dest_path = destination_dir / patch_file.name
                if patch_file != dest_path:
                    shutil.move(str(patch_file), str(dest_path))
                    moved_files.append(patch_file.name)
        
        if moved_files:
            logger.info("✅ Moved stable patch files:")
            for f in moved_files:
                logger.info(f" - {f}")
        else:
            logger.info(f"ℹ️ No .c.patch or .h.patch files found in: {source_dir}")
            
        return moved_files
    except Exception as e:
        error_msg = f"Error moving stable patches: {e}"
        logger.error(error_msg)
        raise PatchError(error_msg)

def check_for_patches(directory: Path) -> bool:
    """Check if directory contains any patch files"""
    try:
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            return False

        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory}")
            return False

        has_patches = any(
            any(directory.glob(pattern)) 
            for pattern in PATCH_PATTERNS
        )
        
        if has_patches:
            logger.info(f"📁 Found patches in: {directory}")
        else:
            logger.info(f"✅ No patches found in: {directory}")
            
        return has_patches
    except Exception as e:
        error_msg = f"Error checking for patches: {e}"
        logger.error(error_msg)
        raise PatchError(error_msg)

def extract_patch_target(patch_path: Path) -> Optional[str]:
    """Extract relative file path from patch file"""
    try:
        content = patch_path.read_text()
        match = re.search(r'^diff --git a/(.*?) b/', content, re.MULTILINE)
        return match.group(1) if match else None
    except Exception as e:
        logger.error(f"Error reading patch file {patch_path}: {e}")
        return None

def apply_patch(patch_file: Path, source_dir: Path, jsonl_file: Path) -> bool:
    """Apply patch and record changes in JSONL file"""
    relative_path = extract_patch_target(patch_file)
    if not relative_path:
        logger.error(f"Skipping {patch_file}: could not extract file path.")
        return False

    full_path = source_dir / relative_path
    if not full_path.exists():
        logger.info(f"File {relative_path} not found in source dir. Skipping.")
        return False

    data: Dict = {"error": "Functionality Error"}
    
    try:
        # Read original content
        data["wrong_code"] = full_path.read_text(encoding='utf-8', errors='ignore')
        
        # Read patch content
        data["patch_code"] = patch_file.read_text(encoding='utf-8', errors='ignore')

        # Apply patch
        result = subprocess.run(
            ["patch", str(full_path), "-i", str(patch_file)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0:
            # Read patched content
            data["correct_code"] = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Append to JSONL
            with jsonl_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(data) + '\n')
            
            logger.info(f"✅ Applied patch: {patch_file}")
            return True
        else:
            logger.error(f"Failed to apply {patch_file}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error applying patch {patch_file}: {e}")
        return False

def process_functionality_patches(patch_dir: Path, source_dir: Path, jsonl_file: Path):
    """Process all functionality patches"""
    try:
        logger.info("Processing functionality patches...")
        for pattern in PATCH_PATTERNS:
            for patch_file in patch_dir.glob(pattern):
                if apply_patch(patch_file, source_dir, jsonl_file):
                    patch_file.unlink()
                    logger.info(f"🧹 Deleted patch: {patch_file}")
                    
        logger.info("✅ Processed all functionality patches")
    except Exception as e:
        error_msg = f"Error processing functionality patches: {e}"
        logger.error(error_msg)
        raise PatchError(error_msg)
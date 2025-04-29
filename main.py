import argparse
import json
from pathlib import Path
from typing import Optional
import shutil,subprocess,re
from utils.logging_utils import setup_logging
from utils.git_operations import clone_repository
from utils.build_operations import run_zopen_build, check_build_errors
from utils.file_operations import (
    check_build_type,
    extract_source_folder_name,
    create_jsonl_file
)
from utils.patch_operations import (
    move_stable_patches,
    check_for_patches,
    process_functionality_patches
)
from utils.error_handling import (
    AutomationError,
    BuildError,
    PatchError,
    FileOperationError,
    GitOperationError
)
from config import TEMP_DIR, PATCHES_DIR, STABLE_PATCHES_DIR, BUILDENV_FILENAME

logger = setup_logging()

def main():
    parser = argparse.ArgumentParser(description="Automation tool for building and patching")
    parser.add_argument("clone_link", help="GitHub repository clone link")
    args = parser.parse_args()

    try:
        # Setup directories
        temp_dir = TEMP_DIR
        patches_dir = PATCHES_DIR
        stable_patches_dir = STABLE_PATCHES_DIR

        # Clone repository
        clone_repository(args.clone_link, temp_dir)

        # Check build type and move patches
        buildenv_path = temp_dir / BUILDENV_FILENAME
        build_type = check_build_type(buildenv_path)
        
        if build_type == "stable":
            move_stable_patches(patches_dir, stable_patches_dir)

        # Get source folder name
        source_folder_name = extract_source_folder_name(buildenv_path)
        if not source_folder_name:
            raise AutomationError("Could not determine source folder name")

        # Create data file
        jsonl_file = create_jsonl_file(source_folder_name)

        # Main build loop
        while True:
            try:
                build_success, build_log = run_zopen_build(temp_dir)
                
                if build_success:
                    if check_for_patches(patches_dir):
                        logger.info("Processing remaining functionality patches...")
                        process_functionality_patches(
                            patches_dir,
                            temp_dir / source_folder_name,
                            jsonl_file
                        )
                    break
                
                if build_log:
                    error_message = check_build_errors(build_log)
                    if error_message:
                        process_build_error(
                            error_message,
                            source_folder_name,
                            patches_dir,
                            stable_patches_dir,
                            jsonl_file
                        )

            except BuildError as e:
                logger.error(f"Build failed: {e}")
                raise
            except PatchError as e:
                logger.error(f"Patch operation failed: {e}")
                raise

    except AutomationError as e:
        logger.error(f"Automation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

    logger.info("✅ Automation completed successfully")
    return 0

def process_build_error(
    error_message: str,
    source_folder_name: str,
    patches_dir: Path,
    stable_patches_dir: Path,
    jsonl_file: Path
):
    """Process a build error by extracting code and applying patches"""
    logger.info("Processing build error...")
    
    # Extract file path from error
    file_match = re.search(r'(src|lib)/[a-zA-Z0-9_\-]+\.([ch])', error_message)
    if not file_match:
        raise AutomationError("Could not extract filename from error message")

    file_path = file_match.group(0)
    full_file_path = TEMP_DIR / source_folder_name / file_path

    # Prepare data dictionary
    data = {"error": error_message}

    try:
        # Read original (wrong) code
        data["wrong_code"] = full_file_path.read_text(encoding='utf-8', errors='ignore')

        # Find and apply patch
        base_name = Path(file_path).name
        patch_name = f"{base_name}.patch"
        patch_path = patches_dir / patch_name

        if not patch_path.exists():
            raise FileOperationError(f"Patch file not found: {patch_path}")

        # Apply patch
        result = subprocess.run(
            ["patch", str(full_file_path), "-i", str(patch_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise PatchError(f"Patch failed: {result.stderr}")

        # Read corrected code
        data["correct_code"] = full_file_path.read_text(encoding='utf-8', errors='ignore')

        # Move and read patch file
        stable_patch_path = stable_patches_dir / patch_name
        stable_patches_dir.mkdir(exist_ok=True)
        shutil.move(str(patch_path), str(stable_patch_path))
        data["patch_code"] = stable_patch_path.read_text(encoding='utf-8', errors='ignore')

        # Write to JSONL
        with jsonl_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')

        logger.info(f"✅ Processed error for file: {file_path}")

    except Exception as e:
        logger.error(f"Error processing build error: {e}")
        raise

if __name__ == "__main__":
    exit(main())
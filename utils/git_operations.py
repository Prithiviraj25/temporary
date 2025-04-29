import subprocess
import logging
from pathlib import Path
from error_handling import GitOperationError

logger = logging.getLogger(__name__)

def clone_repository(clone_link: str, destination: Path) -> None:
    """Clone a git repository with error handling"""
    try:
        logger.info(f"Cloning repository from {clone_link} to {destination}")
        result = subprocess.run(
            ['git', 'clone', clone_link, str(destination)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Repository cloned successfully")
    except subprocess.CalledProcessError as e:
        error_msg = f"Git clone failed: {e.stderr}"
        logger.error(error_msg)
        raise GitOperationError(error_msg)
    except FileNotFoundError:
        error_msg = "Git command not found. Is git installed?"
        logger.error(error_msg)
        raise GitOperationError(error_msg)
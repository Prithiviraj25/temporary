class AutomationError(Exception):
    """Base exception for automation tool"""
    pass

class BuildError(AutomationError):
    """Exception raised for build failures"""
    pass

class PatchError(AutomationError):
    """Exception raised for patch-related failures"""
    pass

class FileOperationError(AutomationError):
    """Exception raised for file operations"""
    pass

class GitOperationError(AutomationError):
    """Exception raised for git operations"""
    pass
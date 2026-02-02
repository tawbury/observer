"""
DEPRECATED: This module has been consolidated into src/backup/.

Please update your imports:
    from maintenance.backup import create_backup
    -> from backup import BackupManager
"""
import warnings
from backup import BackupManager

warnings.warn(
    "maintenance.backup is deprecated. Use 'from backup import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["BackupManager"]

"""
DEPRECATED: This module has been consolidated into src/retention/.

Please update your imports:
    from maintenance.retention import RetentionPolicy
    -> from retention import RetentionPolicy
"""
import warnings
from retention import RetentionPolicy, RetentionScanner

warnings.warn(
    "maintenance.retention is deprecated. Use 'from retention import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["RetentionPolicy", "RetentionScanner"]

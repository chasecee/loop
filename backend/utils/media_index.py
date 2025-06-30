"""
Media index utilities - SQLite migration completed.

LEGACY JSON system has been replaced with efficient SQLite backend.
This module now provides backward compatibility only.
"""
from __future__ import annotations

from contextlib import contextmanager

# Legacy imports for backward compatibility
from utils.sqlite_media_index import MediaMetadata, ProcessingJob

# Global instance - using SQLite implementation
from utils.sqlite_media_index import SQLiteMediaIndexManager
media_index = SQLiteMediaIndexManager()

@contextmanager
def batch_operations(media_index_manager):
    """Context manager for batching operations (no-op in SQLite version)."""
    yield  # SQLite handles atomicity natively 
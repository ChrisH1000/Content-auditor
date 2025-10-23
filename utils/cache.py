"""Disk-based caching for page analysis results."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Cache:
    """Simple disk-based cache using JSON files."""

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initialize cache.

        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache initialized at {self.cache_dir}")

    def _get_hash(self, key: str) -> str:
        """
        Generate SHA256 hash of key.

        Args:
            key: String to hash (typically URL)

        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """
        Get cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        key_hash = self._get_hash(key)
        return self.cache_dir / f"{key_hash}.json"

    def get(self, key: str) -> Optional[dict]:
        """
        Retrieve cached data.

        Args:
            key: Cache key (typically URL)

        Returns:
            Cached data dictionary or None if not found
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, "r") as f:
                    data = json.load(f)
                logger.debug(f"Cache hit for key: {key[:50]}...")
                return data
            except Exception as e:
                logger.error(f"Error reading cache for {key}: {e}")
                return None
        logger.debug(f"Cache miss for key: {key[:50]}...")
        return None

    def set(self, key: str, data: dict):
        """
        Store data in cache.

        Args:
            key: Cache key (typically URL)
            data: Data dictionary to cache
        """
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached data for key: {key[:50]}...")
        except Exception as e:
            logger.error(f"Error writing cache for {key}: {e}")

    def clear(self):
        """Clear all cached data."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        logger.info(f"Cleared {count} cached files")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        return {
            "total_entries": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

"""Simple caching system for metric results."""

import json
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import logging
from backend.config import CACHE_DIR, ENABLE_CACHE, CACHE_TTL

logger = logging.getLogger(__name__)


class MetricCache:
    """Simple file-based cache for metric results."""

    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.enabled = ENABLE_CACHE
        self.ttl = CACHE_TTL

    def _generate_key(self, metric_name: str, **kwargs) -> str:
        """Generate a unique cache key from metric name and parameters."""
        # Create a stable string from parameters
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        combined = f"{metric_name}:{params_str}"

        # Generate hash
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _get_cache_path(self, key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{key}.json"

    def get(self, metric_name: str, **kwargs) -> Optional[Any]:
        """Retrieve cached result if available and not expired."""
        if not self.enabled:
            return None

        try:
            key = self._generate_key(metric_name, **kwargs)
            cache_path = self._get_cache_path(key)

            if not cache_path.exists():
                return None

            # Check if cache is expired
            cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - cache_time > timedelta(seconds=self.ttl):
                cache_path.unlink()  # Remove expired cache
                return None

            # Load and return cached data
            with open(cache_path, 'r') as f:
                data = json.load(f)

            logger.debug(f"Cache hit for {metric_name}")

            # Reconstruct MetricResult if needed
            result_data = data['result']
            if data.get('result_type') == 'MetricResult':
                from backend.metrics.base import MetricResult
                return MetricResult(**result_data)

            return result_data

        except Exception as e:
            logger.warning(f"Cache retrieval failed for {metric_name}: {e}")
            return None

    def set(self, metric_name: str, result: Any, **kwargs) -> None:
        """Store result in cache."""
        if not self.enabled:
            return

        try:
            key = self._generate_key(metric_name, **kwargs)
            cache_path = self._get_cache_path(key)

            # Convert MetricResult to dict for JSON serialization
            if hasattr(result, '__dict__'):
                result_dict = result.__dict__
            else:
                result_dict = result

            cache_data = {
                'metric_name': metric_name,
                'result': result_dict,
                'result_type': type(result).__name__,
                'cached_at': datetime.now().isoformat(),
                'parameters': kwargs
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, default=str, indent=2)

            logger.debug(f"Cached result for {metric_name}")

        except Exception as e:
            logger.warning(f"Cache storage failed for {metric_name}: {e}")

    def clear(self, metric_name: Optional[str] = None) -> None:
        """Clear cache files. If metric_name provided, clear only that metric."""
        try:
            if metric_name:
                # Clear specific metric (would need to track by prefix)
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                        if data.get('metric_name') == metric_name:
                            cache_file.unlink()
                    except:
                        continue
            else:
                # Clear all cache files
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()

            logger.info(f"Cache cleared for {metric_name or 'all metrics'}")

        except Exception as e:
            logger.warning(f"Cache clearing failed: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_files = len(cache_files)
            total_size = sum(f.stat().st_size for f in cache_files)

            # Count expired files
            expired_count = 0
            for cache_file in cache_files:
                cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - cache_time > timedelta(seconds=self.ttl):
                    expired_count += 1

            return {
                'enabled': self.enabled,
                'ttl_seconds': self.ttl,
                'total_files': total_files,
                'total_size_bytes': total_size,
                'expired_files': expired_count
            }

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {'enabled': self.enabled, 'error': str(e)}


# Global instance
metric_cache = MetricCache()
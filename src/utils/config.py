"""
Configuration Management.

Loads configuration from environment variables, files, or defaults.
Provides a centralized config object accessible throughout the application.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from src.monitoring.logger import get_logger

logger = get_logger(__name__)


class Config:
    """Configuration manager with nested dict support and type coercion."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize config with optional dict.
        
        Args:
            config_dict: Dictionary of configuration values
        """
        self._config = config_dict or {}
        self._load_env_overrides()
    
    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        for key, value in os.environ.items():
            if key.startswith("APP_"):
                config_key = key[4:].lower()
                self._config[config_key] = value
    
    @staticmethod
    def from_file(file_path: str) -> "Config":
        """
        Load configuration from JSON or environment file.
        
        Args:
            file_path: Path to config file
        
        Returns:
            Config instance
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Config file not found: {file_path}. Using defaults.")
            return Config()
        
        try:
            with open(path, 'r') as f:
                if path.suffix == '.json':
                    config_dict = json.load(f)
                elif path.suffix in ['.env', '.txt']:
                    config_dict = {}
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            config_dict[key.strip()] = value.strip()
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            
            logger.info(f"Loaded config from {file_path}")
            return Config(config_dict)
        
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            return Config()
    
    def get(self, key: str, default: Any = None, coerce: type = str) -> Any:
        """
        Get config value with dot notation and type coercion.
        
        Args:
            key: Config key with optional dot notation (e.g., "rag.static.index_path")
            default: Default value if key not found
            coerce: Type to coerce value to (str, int, float, bool)
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
            
            if value is None:
                return default
        
        if value is not None and coerce:
            if coerce == bool:
                value = str(value).lower() in ('true', '1', 'yes', 'on')
            elif coerce in (int, float):
                value = coerce(value)
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Get entire config as dictionary."""
        return self._config.copy()


# Global config instance
_global_config: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get or initialize global config instance.
    
    Args:
        config_file: Optional path to config file to load
    
    Returns:
        Global Config instance
    """
    global _global_config
    
    if _global_config is None:
        if config_file:
            _global_config = Config.from_file(config_file)
        else:
            # Try to load from default locations
            default_paths = [
                Path("config.json"),
                Path(".env"),
                Path("config/.env"),
            ]
            
            for path in default_paths:
                if path.exists():
                    logger.info(f"Loading config from {path}")
                    _global_config = Config.from_file(str(path))
                    break
            
            if _global_config is None:
                logger.info("No config file found. Using environment variables and defaults.")
                _global_config = Config()
    
    return _global_config


def reset_config() -> None:
    """Reset global config (useful for testing)."""
    global _global_config
    _global_config = None

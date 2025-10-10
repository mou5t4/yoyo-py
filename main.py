"""
YoyoPod Connect - Main entry point

A screen-minimal streaming device for kids aged 6-12 based on Raspberry Pi Zero 2 W.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from yoyopy.utils.logger import init_logger


__version__ = "0.1.0"


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing configuration settings

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Creating default config from config.example.json...")

        example_config = config_path.parent / "config.example.json"
        if example_config.exists():
            with open(example_config, "r") as f:
                config = json.load(f)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.success(f"Created {config_path}")
        else:
            raise FileNotFoundError(f"Neither {config_path} nor {example_config} found")

    with open(config_path, "r") as f:
        config = json.load(f)

    logger.debug(f"Loaded configuration from {config_path}")
    return config


def main() -> int:
    """
    Main entry point for YoyoPod Connect.

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Print startup banner
    print("=" * 60)
    print(f"YoyoPod Connect v{__version__}")
    print("Screen-minimal streaming device for kids")
    print("=" * 60)
    print()

    # Initialize logger with default settings
    init_logger(level="INFO")

    logger.info(f"yoyopy v{__version__} starting...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")

    try:
        # Load configuration
        config_path = Path("config") / "config.json"
        config = load_config(config_path)

        # Re-initialize logger with config settings
        if "logging" in config:
            log_config = config["logging"]
            init_logger(
                level=log_config.get("level", "INFO"),
                log_dir=Path(log_config.get("log_dir", "./logs")) if log_config.get("log_dir") else None,
                console=log_config.get("console", True),
                file_logging=log_config.get("file", True),
            )

        logger.info("Configuration loaded successfully")
        logger.debug(f"Device: {config.get('device', {}).get('name', 'Unknown')}")
        logger.debug(f"Connectivity mode: {config.get('connectivity', {}).get('mode', 'Unknown')}")

        # TODO: Initialize hardware modules
        # - Display (Pimoroni Display HAT Mini)
        # - Audio system
        # - 4G/WiFi connectivity
        # - GPS module
        # - Button inputs

        # TODO: Initialize software modules
        # - MQTT client for real-time sync
        # - Content manager
        # - Parental controls
        # - VoIP handler

        logger.success("YoyoPod Connect initialized successfully!")
        logger.info("Ready!")

        # TODO: Start main event loop
        # For now, just exit gracefully

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

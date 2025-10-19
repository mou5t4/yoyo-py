#!/usr/bin/env python3
"""
YoyoPod Phase 1 Demo - Core Integration Framework

Tests the integrated YoyoPod application with:
- Enhanced state machine with VoIP + music states
- YoyoPodApp coordinator
- Callback coordination between VoIP and music
- Automatic music pause on incoming call
- Automatic music resume after call ends

Phase 1 Focus:
- State machine and callback coordination ONLY
- No UI/screen integration (Phase 2)
- Verify state transitions and music pause/resume logic

Requirements:
- linphonec installed and VoIP account configured
- Mopidy server running on localhost:6680
- config/yoyopod_config.yaml (auto-created if missing)

Usage:
    # Simulation mode (no hardware required)
    python demo_yoyopod_phase1.py --simulate

    # Hardware mode
    python demo_yoyopod_phase1.py
"""

import sys
import time
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

from yoyopy.app import YoyoPodApp


def main():
    """Run YoyoPod Phase 1 demo."""
    # Check for simulation mode
    simulate = "--simulate" in sys.argv

    # Create app
    app = YoyoPodApp(config_dir="config", simulate=simulate)

    # Setup
    if not app.setup():
        logger.error("Failed to setup application!")
        return 1

    # Run main loop
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())

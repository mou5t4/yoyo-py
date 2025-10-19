#!/usr/bin/env python3
"""
YoyoPod - Full Integrated VoIP + Music Application

This is the production YoyoPod application with full integration:
- VoIP calling with linphonec
- Music streaming via Mopidy/Spotify
- Seamless call interruption (auto-pause/resume music)
- Full UI with all screens
- Context-sensitive button controls

Requirements:
- Raspberry Pi Zero 2W (or simulation mode)
- DisplayHATMini 320x240 display
- linphonec installed and VoIP account configured
- Mopidy server running on localhost:6680
- config/yoyopod_config.yaml
- config/voip_config.yaml
- config/contacts.yaml

Usage:
    # Hardware mode (on Raspberry Pi)
    ./yoyopod.py

    # Simulation mode (no hardware required)
    ./yoyopod.py --simulate

Features:
    - Browse and play Spotify playlists
    - Make and receive VoIP calls
    - Auto-pause music on incoming calls
    - Auto-resume music after call ends (configurable)
    - Contact list with favorites
    - Live call duration display
    - Caller name resolution

Button Controls:
    Menu Screen:
        A - Select item
        B - Back
        X/Y - Navigate

    Now Playing:
        A - Play/Pause
        B - Back to menu
        X - Previous track
        Y - Next track

    Incoming Call:
        A - Answer
        B - Reject

    In Call:
        B - Hang up
        X - Toggle mute
"""

import sys
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
    """Run YoyoPod full integrated application."""
    # Check for simulation mode
    simulate = "--simulate" in sys.argv

    if simulate:
        logger.warning("=" * 60)
        logger.warning("SIMULATION MODE")
        logger.warning("Running without hardware (display will not work)")
        logger.warning("Use this mode for testing on development machine")
        logger.warning("=" * 60)

    # Create app
    logger.info("Initializing YoyoPod...")
    app = YoyoPodApp(config_dir="config", simulate=simulate)

    # Setup
    if not app.setup():
        logger.error("Failed to setup application!")
        logger.error("Check that:")
        logger.error("  - config/voip_config.yaml exists")
        logger.error("  - config/contacts.yaml exists")
        logger.error("  - linphonec is installed")
        logger.error("  - Mopidy is running on localhost:6680")
        return 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("YoyoPod Ready!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Available Features:")
    logger.info("  ✓ Music streaming (Mopidy/Spotify)")
    logger.info("  ✓ VoIP calling (linphonec)")
    logger.info("  ✓ Auto-pause music on calls")
    logger.info("  ✓ Auto-resume after calls")
    logger.info("  ✓ Full UI navigation")
    logger.info("")
    logger.info("Current Configuration:")
    status = app.get_status()
    logger.info(f"  Auto-resume: {status['auto_resume']}")
    logger.info(f"  VoIP available: {status['voip_available']}")
    logger.info(f"  Music available: {status['music_available']}")
    logger.info("")
    logger.info("Press Ctrl+C to exit")
    logger.info("=" * 60)
    logger.info("")

    # Run main loop
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Shutting down...")
    finally:
        app.stop()

    logger.info("")
    logger.info("Goodbye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

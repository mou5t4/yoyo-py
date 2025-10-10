#!/usr/bin/env python3
"""
Test script for YoyoPod display and screens.

Cycles through all screen types every 3 seconds to demonstrate
the display functionality.
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from yoyopy.ui.display import Display
from yoyopy.ui.screens import HomeScreen, MenuScreen, NowPlayingScreen
from yoyopy.utils.logger import init_logger


def main() -> int:
    """Main test function."""
    # Initialize logger
    init_logger(level="INFO")

    logger.info("=" * 60)
    logger.info("YoyoPod Display Test")
    logger.info("=" * 60)

    try:
        # Initialize display (will auto-detect if hardware is available)
        display = Display(simulate=False)

        # Create screens
        home_screen = HomeScreen(display)
        menu_screen = MenuScreen(display, items=["Music", "Podcasts", "Stories", "Settings"])
        now_playing_screen = NowPlayingScreen(
            display,
            track_title="Adventure Time",
            artist="Kids Podcast Network"
        )

        screens = [
            ("Home", home_screen),
            ("Menu", menu_screen),
            ("Now Playing", now_playing_screen)
        ]

        logger.info(f"Created {len(screens)} test screens")
        logger.info("Cycling through screens every 3 seconds...")
        logger.info("Press Ctrl+C to stop")

        # Cycle through screens
        cycle_count = 0
        while True:
            for screen_name, screen in screens:
                logger.info(f"Displaying: {screen_name}")
                screen.enter()
                screen.render()

                # For menu, show cycling through items
                if isinstance(screen, MenuScreen):
                    for _ in range(3):
                        time.sleep(1)
                        screen.select_next()
                        screen.render()
                # For now playing, animate progress
                elif isinstance(screen, NowPlayingScreen):
                    for i in range(10):
                        time.sleep(0.3)
                        screen.set_progress(i / 10.0)
                        screen.render()
                else:
                    time.sleep(3)

                screen.exit()

            cycle_count += 1
            logger.info(f"Completed cycle {cycle_count}")

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        return 0
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

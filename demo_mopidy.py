#!/usr/bin/env python3
"""
Demo application for Mopidy integration with YoyoPod.

This demo connects to a Mopidy server and allows control of
Spotify streaming through the NowPlayingScreen interface.

Requirements:
- Mopidy server running on localhost:6680
- Mopidy-Spotify extension configured
- DisplayHATMini hardware (or simulation mode)

Button controls:
- Button A: Play/Pause
- Button B: Back to menu
- Button X: Previous track
- Button Y: Next track
"""

import sys
import time
from pathlib import Path
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

from yoyopy.ui.display import Display
from yoyopy.ui.screens import NowPlayingScreen, MenuScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler
from yoyopy.app_context import AppContext
from yoyopy.audio.mopidy_client import MopidyClient


def main():
    """Run Mopidy streaming demo."""
    logger.info("=" * 60)
    logger.info("YoyoPod Mopidy Streaming Demo")
    logger.info("=" * 60)

    # Check for simulation mode
    simulate = "--simulate" in sys.argv
    if simulate:
        logger.warning("Running in SIMULATION mode (no hardware required)")

    # Initialize display
    logger.info("Initializing display...")
    display = Display(simulate=simulate)
    display.clear(display.COLOR_BLACK)
    display.text(
        "Connecting to Mopidy...",
        10, 100,
        color=display.COLOR_WHITE,
        font_size=16
    )
    display.update()

    # Initialize Mopidy client
    logger.info("Connecting to Mopidy server...")
    mopidy = MopidyClient(host="localhost", port=6680)

    try:
        if not mopidy.connect():
            logger.error("Failed to connect to Mopidy server!")
            logger.error("Make sure Mopidy is running on localhost:6680")
            display.clear(display.COLOR_BLACK)
            display.text(
                "Mopidy Connection",
                10, 60,
                color=display.COLOR_RED,
                font_size=18
            )
            display.text(
                "Failed!",
                10, 85,
                color=display.COLOR_RED,
                font_size=18
            )
            display.text(
                "Check Mopidy server",
                10, 120,
                color=display.COLOR_WHITE,
                font_size=14
            )
            display.update()
            time.sleep(3)
            return
    except Exception as e:
        logger.error(f"Error connecting to Mopidy: {e}")
        display.clear(display.COLOR_BLACK)
        display.text(
            "Connection Error",
            10, 80,
            color=display.COLOR_RED,
            font_size=16
        )
        display.text(
            str(e)[:30],
            10, 110,
            color=display.COLOR_WHITE,
            font_size=12
        )
        display.update()
        time.sleep(3)
        return

    logger.info("Connected to Mopidy successfully!")

    # Initialize app context
    context = AppContext()

    # Initialize input handler (if not simulating)
    input_handler = None
    if not simulate:
        logger.info("Initializing input handler...")
        input_handler = InputHandler(simulate=False)
        input_handler.start()  # Start polling for button presses
        logger.info("Input handler started")

    # Initialize screen manager
    logger.info("Setting up screens...")
    screen_manager = ScreenManager(display, input_handler)

    # Create menu screen
    menu_items = ["Load Playlist", "Now Playing", "Playlists", "Back"]
    menu_screen = MenuScreen(display, context, items=menu_items)

    # Create now playing screen with Mopidy client
    now_playing_screen = NowPlayingScreen(
        display,
        context,
        mopidy_client=mopidy
    )

    # Register screens
    screen_manager.register_screen("menu", menu_screen)
    screen_manager.register_screen("now_playing", now_playing_screen)

    # Set initial screen (use push_screen for first screen)
    screen_manager.push_screen("now_playing")

    # Start polling for track changes
    logger.info("Starting track change polling...")
    mopidy.start_polling()

    # Register track change callback to update display
    def on_track_change(track):
        logger.info(f"Track changed: {track.name if track else 'None'}")
        if screen_manager.current_screen == now_playing_screen:
            now_playing_screen.render()

    mopidy.on_track_change(on_track_change)

    # Show instructions
    logger.info("")
    logger.info("Mopidy Demo Running!")
    logger.info("-" * 60)
    logger.info("Button Controls:")
    logger.info("  A - Play/Pause")
    logger.info("  B - Back to menu")
    logger.info("  X - Previous track")
    logger.info("  Y - Next track")
    logger.info("")

    if simulate:
        logger.info("Simulation mode - no buttons available")
        logger.info("Display will auto-refresh every 2 seconds")

    logger.info("")
    logger.info("Press Ctrl+C to exit")
    logger.info("-" * 60)

    try:
        # Main loop
        if simulate:
            # Simulation: auto-refresh display
            while True:
                now_playing_screen.render()
                time.sleep(2)
        else:
            # Hardware: input handler handles updates
            while True:
                time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("\nShutting down...")

    finally:
        # Cleanup
        logger.info("Stopping Mopidy polling...")
        mopidy.stop_polling()

        logger.info("Cleaning up Mopidy client...")
        mopidy.cleanup()

        if input_handler:
            logger.info("Stopping input handler...")
            input_handler.stop()
            logger.info("Cleaning up input handler...")
            input_handler.cleanup()

        logger.info("Clearing display...")
        display.clear(display.COLOR_BLACK)
        display.text(
            "Goodbye!",
            70, 120,
            color=display.COLOR_CYAN,
            font_size=20
        )
        display.update()
        time.sleep(1)
        display.cleanup()

        logger.info("Demo ended.")


if __name__ == "__main__":
    main()

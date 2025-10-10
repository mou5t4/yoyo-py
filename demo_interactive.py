#!/usr/bin/env python3
"""
Interactive YoyoPod UI Demo with Button Input

This demo shows the full navigation flow with button controls:
- Button A: Select/OK
- Button B: Back
- Button X: Up/Previous
- Button Y: Down/Next

Press Ctrl+C to exit.
"""

import time
import sys
from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.screens import HomeScreen, MenuScreen, NowPlayingScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler, Button, ButtonEvent

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def main():
    """Run the interactive demo."""
    logger.info("Starting YoyoPod Interactive Demo")
    logger.info("=" * 50)
    logger.info("Button Controls:")
    logger.info("  A = Select/OK")
    logger.info("  B = Back")
    logger.info("  X = Up/Previous")
    logger.info("  Y = Down/Next")
    logger.info("=" * 50)

    # Check if hardware is available
    try:
        from displayhatmini import DisplayHATMini
        has_hardware = True
        logger.info("DisplayHATMini detected - using hardware")
    except ImportError:
        has_hardware = False
        logger.warning("DisplayHATMini not available - simulation mode")
        logger.info("Use keyboard for testing:")
        logger.info("  Press 'a', 'b', 'x', 'y' + Enter to simulate buttons")

    # Initialize display
    display = Display(simulate=not has_hardware)

    # Initialize input handler
    if has_hardware:
        # Get the device reference from the display
        device = display.device if hasattr(display, 'device') else None
        input_handler = InputHandler(display_device=device, simulate=False)
    else:
        input_handler = InputHandler(simulate=True)

    # Create screen manager
    screen_manager = ScreenManager(display, input_handler)

    # Create and register screens
    home_screen = HomeScreen(display)
    menu_screen = MenuScreen(display)
    now_playing_screen = NowPlayingScreen(
        display,
        track_title="The Adventure Begins",
        artist="Story Time Stories",
        progress=0.3
    )

    screen_manager.register_screen("home", home_screen)
    screen_manager.register_screen("menu", menu_screen)
    screen_manager.register_screen("now_playing", now_playing_screen)

    # Start with home screen
    screen_manager.replace_screen("home")

    # Start input handler
    input_handler.start()

    try:
        if has_hardware:
            # Hardware mode - just wait for button presses
            logger.info("Demo running - press buttons to navigate")
            logger.info("Press Ctrl+C to exit")

            while True:
                time.sleep(0.1)

        else:
            # Simulation mode - keyboard input
            logger.info("Simulation mode - type button commands")
            logger.info("Commands: a, b, x, y (+ Enter)")
            logger.info("Type 'quit' to exit")

            while True:
                try:
                    cmd = input("> ").strip().lower()

                    if cmd == 'quit':
                        break
                    elif cmd == 'a':
                        input_handler.simulate_button_press(Button.A, ButtonEvent.PRESS)
                    elif cmd == 'b':
                        input_handler.simulate_button_press(Button.B, ButtonEvent.PRESS)
                    elif cmd == 'x':
                        input_handler.simulate_button_press(Button.X, ButtonEvent.PRESS)
                    elif cmd == 'y':
                        input_handler.simulate_button_press(Button.Y, ButtonEvent.PRESS)
                    elif cmd == 'al':  # Long press A
                        input_handler.simulate_button_press(Button.A, ButtonEvent.LONG_PRESS)
                    elif cmd == 'ad':  # Double press A
                        input_handler.simulate_button_press(Button.A, ButtonEvent.DOUBLE_PRESS)
                    elif cmd == 'help':
                        logger.info("Commands: a, b, x, y, al (long A), ad (double A), quit")
                    else:
                        logger.warning(f"Unknown command: {cmd}")

                except EOFError:
                    break

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")

    finally:
        # Cleanup
        input_handler.stop()
        logger.info("Demo stopped")


if __name__ == "__main__":
    main()

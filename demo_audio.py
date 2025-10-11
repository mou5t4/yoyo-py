#!/usr/bin/env python3
"""
Audio System Demo for YoyoPod

Demonstrates audio playback and volume control with the AudioManager
and AudioScreen.

Press Ctrl+C to exit.
"""

import time
import sys
from pathlib import Path
from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.audio_screen import AudioScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler, Button, ButtonEvent
from yoyopy.app_context import AppContext
from yoyopy.audio.audio_manager import AudioManager

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def main():
    """Run the audio demo."""
    logger.info("Starting YoyoPod Audio Demo")
    logger.info("=" * 50)

    # Check if hardware is available
    try:
        from displayhatmini import DisplayHATMini
        has_hardware = True
        logger.info("DisplayHATMini detected - using hardware")
    except ImportError:
        has_hardware = False
        logger.warning("DisplayHATMini not available - simulation mode")

    # Initialize application context
    context = AppContext()
    context.update_system_status(battery=85, signal=3, connected=True)

    # Initialize audio manager with parental volume limit (80%)
    audio_manager = AudioManager(max_volume=80, simulate=not has_hardware)

    # Set initial volume
    audio_manager.volume = 50

    # Initialize display
    display = Display(simulate=not has_hardware)

    # Initialize input handler
    if has_hardware:
        device = display.device if hasattr(display, 'device') else None
        input_handler = InputHandler(display_device=device, simulate=False)
    else:
        input_handler = InputHandler(simulate=True)

    # Create screen manager
    screen_manager = ScreenManager(display, input_handler)

    # Create audio screen
    audio_screen = AudioScreen(display, audio_manager, context)

    # Register screen
    screen_manager.register_screen("audio", audio_screen)

    # Show audio screen
    screen_manager.replace_screen("audio")

    # Start input handler
    input_handler.start()

    # Log available test sounds
    sounds_dir = Path("assets/sounds")
    if sounds_dir.exists():
        sound_files = list(sounds_dir.glob("*.wav"))
        logger.info(f"Found {len(sound_files)} test sounds:")
        for sound in sound_files:
            logger.info(f"  - {sound.name}")
    else:
        logger.warning("No test sounds found. Run scripts/generate_test_sounds.py first")

    try:
        if has_hardware:
            # Hardware mode - just wait for button presses
            logger.info("Audio demo running - press buttons to test")
            logger.info("  A: Play test sound")
            logger.info("  X: Volume up")
            logger.info("  Y: Volume down")
            logger.info("  B: Exit")
            logger.info("Press Ctrl+C to exit")

            # Register back button to exit
            def exit_demo():
                raise KeyboardInterrupt

            input_handler.on_button(Button.B, ButtonEvent.PRESS, exit_demo)

            while True:
                time.sleep(0.1)

        else:
            # Simulation mode - keyboard input
            logger.info("Simulation mode - type button commands")
            logger.info("Commands: a (play), x (vol up), y (vol down), quit")

            while True:
                try:
                    logger.info(f"Current volume: {audio_manager.volume}%")
                    cmd = input("> ").strip().lower()

                    if cmd == 'quit' or cmd == 'b':
                        break
                    elif cmd == 'a':
                        input_handler.simulate_button_press(Button.A, ButtonEvent.PRESS)
                    elif cmd == 'x':
                        input_handler.simulate_button_press(Button.X, ButtonEvent.PRESS)
                    elif cmd == 'y':
                        input_handler.simulate_button_press(Button.Y, ButtonEvent.PRESS)
                    elif cmd == 'vol':
                        logger.info(f"Volume: {audio_manager.volume}% (max: {audio_manager.max_volume}%)")
                    elif cmd == 'device':
                        device_info = audio_manager.get_device_info()
                        if device_info:
                            logger.info(f"Device: {device_info.name} ({device_info.device_type.value})")
                        else:
                            logger.info("No audio device detected")
                    elif cmd == 'help':
                        logger.info("Commands: a, x, y, vol, device, quit")
                    else:
                        logger.warning(f"Unknown command: {cmd}")

                except EOFError:
                    break

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")

    finally:
        # Cleanup
        input_handler.stop()
        audio_manager.cleanup()
        logger.info(f"Final volume: {audio_manager.volume}%")
        logger.info("Demo stopped")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
State Machine Demo for YoyoPod

Demonstrates the full state machine integration with screens and app context.
Button presses trigger state transitions which manage screen changes.

Press Ctrl+C to exit.
"""

import time
import sys
from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.screens import HomeScreen, MenuScreen, NowPlayingScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler, Button, ButtonEvent
from yoyopy.app_context import AppContext
from yoyopy.state_machine import StateMachine, AppState

# Configure logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def main():
    """Run the state machine demo."""
    logger.info("Starting YoyoPod State Machine Demo")
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

    # Create demo playlist and set it as current
    demo_playlist = context.create_demo_playlist()
    context.set_playlist(demo_playlist)
    context.update_system_status(battery=85, signal=3, connected=True)

    logger.info(f"Demo playlist loaded: {len(demo_playlist.tracks)} tracks")

    # Initialize display
    display = Display(simulate=not has_hardware)

    # Initialize input handler
    if has_hardware:
        device = display.device if hasattr(display, 'device') else None
        input_handler = InputHandler(display_device=device, simulate=False)
    else:
        input_handler = InputHandler(simulate=True)

    # Initialize state machine
    state_machine = StateMachine(context)

    # Create screen manager
    screen_manager = ScreenManager(display, input_handler)

    # Create screens with context
    home_screen = HomeScreen(display, context)
    menu_screen = MenuScreen(display, context)
    now_playing_screen = NowPlayingScreen(display, context)

    # Register screens
    screen_manager.register_screen("home", home_screen)
    screen_manager.register_screen("menu", menu_screen)
    screen_manager.register_screen("now_playing", now_playing_screen)

    # Wire up state machine to screen manager
    def on_enter_idle():
        """When entering IDLE state, show home screen."""
        screen_manager.replace_screen("home")

    def on_enter_menu():
        """When entering MENU state, show menu screen."""
        screen_manager.replace_screen("menu")

    def on_enter_playing():
        """When entering PLAYING state, show now playing screen."""
        screen_manager.replace_screen("now_playing")

    def on_enter_paused():
        """When entering PAUSED state, update now playing screen."""
        screen_manager.refresh_current_screen()

    # Register state callbacks
    state_machine.on_enter(AppState.IDLE, on_enter_idle)
    state_machine.on_enter(AppState.MENU, on_enter_menu)
    state_machine.on_enter(AppState.PLAYING, on_enter_playing)
    state_machine.on_enter(AppState.PAUSED, on_enter_paused)

    # Custom button handlers that use state machine
    def handle_button_a():
        """Handle Button A based on current state."""
        current_state = state_machine.current_state

        if current_state == AppState.IDLE:
            state_machine.open_menu()
        elif current_state == AppState.MENU:
            # Let menu screen handler deal with selection
            screen_manager.current_screen.on_button_a()
            # If music/podcast selected, transition to PLAYING
            selected = menu_screen.get_selected()
            if selected in ["Music", "Podcasts", "Audiobooks"]:
                state_machine.start_playback()
        elif current_state in [AppState.PLAYING, AppState.PAUSED]:
            # Toggle playback
            state_machine.toggle_playback()
            screen_manager.refresh_current_screen()

    def handle_button_b():
        """Handle Button B (back) based on current state."""
        current_state = state_machine.current_state

        if current_state == AppState.MENU:
            state_machine.transition_to(AppState.IDLE, "back")
        elif current_state in [AppState.PLAYING, AppState.PAUSED]:
            state_machine.transition_to(AppState.MENU, "back")

    def handle_button_x():
        """Handle Button X based on current state."""
        current_state = state_machine.current_state

        if current_state == AppState.MENU:
            menu_screen.select_previous()
            screen_manager.refresh_current_screen()
        elif current_state in [AppState.PLAYING, AppState.PAUSED]:
            context.volume_up()
            logger.info(f"Volume: {context.playback.volume}")

    def handle_button_y():
        """Handle Button Y based on current state."""
        current_state = state_machine.current_state

        if current_state == AppState.MENU:
            menu_screen.select_next()
            screen_manager.refresh_current_screen()
        elif current_state in [AppState.PLAYING, AppState.PAUSED]:
            context.volume_down()
            logger.info(f"Volume: {context.playback.volume}")

    # Register button handlers with input handler
    input_handler.on_button(Button.A, ButtonEvent.PRESS, handle_button_a)
    input_handler.on_button(Button.B, ButtonEvent.PRESS, handle_button_b)
    input_handler.on_button(Button.X, ButtonEvent.PRESS, handle_button_x)
    input_handler.on_button(Button.Y, ButtonEvent.PRESS, handle_button_y)

    # Start with IDLE state
    state_machine.transition_to(AppState.IDLE, "init")

    # Start input handler
    input_handler.start()

    try:
        if has_hardware:
            # Hardware mode - just wait for button presses
            logger.info("Demo running - press buttons to navigate")
            logger.info("State: " + state_machine.get_state_name())
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
                    logger.info(f"Current state: {state_machine.get_state_name()}")
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
                    elif cmd == 'state':
                        logger.info(f"State: {state_machine.get_state_name()}")
                        logger.info(f"Track: {context.get_current_track().title if context.get_current_track() else 'None'}")
                        logger.info(f"Playing: {context.playback.is_playing}")
                        logger.info(f"Volume: {context.playback.volume}")
                    elif cmd == 'help':
                        logger.info("Commands: a, b, x, y, state, quit")
                    else:
                        logger.warning(f"Unknown command: {cmd}")

                except EOFError:
                    break

    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")

    finally:
        # Cleanup
        input_handler.stop()
        logger.info(f"Final state: {state_machine.get_state_name()}")
        logger.info("Demo stopped")


if __name__ == "__main__":
    main()

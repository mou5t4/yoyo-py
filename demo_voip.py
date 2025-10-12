#!/usr/bin/env python3
"""
Demo application for VoIP calling with YoyoPod.

This demo initializes VoIPManager and displays the CallScreen
showing registration status and VoIP readiness.

Requirements:
- linphonec installed at /usr/bin/linphonec
- SIP account configured (sip.linphone.org or other provider)
- DisplayHATMini hardware (or simulation mode)

Button controls:
- Button A: Answer/Hangup call (future)
- Button B: Back to menu
- Button X/Y: Reserved for dial pad (future)
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
from yoyopy.ui.screens import CallScreen, MenuScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler
from yoyopy.app_context import AppContext
from yoyopy.connectivity import VoIPManager, VoIPConfig, RegistrationState


def main():
    """Run VoIP demo."""
    logger.info("=" * 60)
    logger.info("YoyoPod VoIP Demo")
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
        "Initializing VoIP...",
        10, 100,
        color=display.COLOR_WHITE,
        font_size=16
    )
    display.update()

    # Initialize app context
    context = AppContext()

    # Configure VoIP (using linphone.org test account)
    logger.info("Configuring VoIP...")
    voip_config = VoIPConfig(
        sip_server="sip.linphone.org",
        sip_username="tifo",
        sip_password="",  # Will use saved credentials from .linphonerc
        sip_identity="sip:tifo@sip.linphone.org",
        transport="tcp",
        linphonec_path="/usr/bin/linphonec"
    )

    # Initialize VoIP manager
    logger.info("Starting VoIP manager...")
    voip_manager = VoIPManager(voip_config)

    # Register callback for registration state changes
    def on_registration_change(state: RegistrationState):
        logger.info(f"Registration state changed: {state.value}")
        # Re-render call screen when registration state changes
        if screen_manager.current_screen == call_screen:
            call_screen.render()

    voip_manager.on_registration_change(on_registration_change)

    try:
        if not voip_manager.start():
            logger.error("Failed to start VoIP manager!")
            display.clear(display.COLOR_BLACK)
            display.text(
                "VoIP Start Failed",
                10, 60,
                color=display.COLOR_RED,
                font_size=18
            )
            display.text(
                "Check linphonec",
                10, 85,
                color=display.COLOR_RED,
                font_size=18
            )
            display.text(
                "installation",
                10, 110,
                color=display.COLOR_WHITE,
                font_size=14
            )
            display.update()
            time.sleep(3)
            return
    except Exception as e:
        logger.error(f"Error starting VoIP: {e}")
        display.clear(display.COLOR_BLACK)
        display.text(
            "VoIP Error",
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

    logger.info("VoIP manager started successfully!")

    # Initialize input handler (if not simulating)
    input_handler = None
    if not simulate:
        logger.info("Initializing input handler...")
        input_handler = InputHandler(display_device=display.device, simulate=False)
        input_handler.start()  # Start polling for button presses
        logger.info("Input handler started")

    # Initialize screen manager
    logger.info("Setting up screens...")
    screen_manager = ScreenManager(display, input_handler)

    # Create menu screen
    menu_items = ["VoIP Status", "Back"]
    menu_screen = MenuScreen(display, context, items=menu_items)

    # Create call screen with VoIP manager
    call_screen = CallScreen(
        display,
        context,
        voip_manager=voip_manager
    )

    # Register screens
    screen_manager.register_screen("menu", menu_screen)
    screen_manager.register_screen("call", call_screen)

    # Set initial screen (start with call screen to show VoIP status)
    screen_manager.push_screen("call")

    # Show instructions
    logger.info("")
    logger.info("VoIP Demo Running!")
    logger.info("-" * 60)
    logger.info("Navigation:")
    logger.info("  Call Screen:")
    logger.info("    B - Back to menu")
    logger.info("")
    logger.info("VoIP Status:")
    status = voip_manager.get_status()
    logger.info(f"  Running: {status['running']}")
    logger.info(f"  Registered: {status['registered']}")
    logger.info(f"  Registration State: {status['registration_state']}")
    logger.info(f"  SIP Identity: {status['sip_identity']}")
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
                if screen_manager.current_screen:
                    screen_manager.current_screen.render()
                time.sleep(2)
        else:
            # Hardware: input handler handles updates
            while True:
                time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("\nShutting down...")

    finally:
        # Cleanup
        logger.info("Stopping VoIP manager...")
        voip_manager.stop()

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

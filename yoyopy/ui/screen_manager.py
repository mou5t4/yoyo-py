"""
Screen management and navigation for YoyoPod.

Handles screen transitions and the navigation stack.
"""

from typing import Optional, Dict, Type
from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.screens import Screen
from yoyopy.ui.input_handler import InputHandler, Button, ButtonEvent


class ScreenManager:
    """
    Manages screen navigation and transitions.

    Maintains a stack of screens for back navigation and
    handles screen lifecycle (enter/exit).
    """

    def __init__(self, display: Display, input_handler: InputHandler) -> None:
        """
        Initialize the screen manager.

        Args:
            display: Display controller instance
            input_handler: Input handler for button events
        """
        self.display = display
        self.input_handler = input_handler
        self.current_screen: Optional[Screen] = None
        self.screen_stack: list[Screen] = []
        self.screens: Dict[str, Screen] = {}

        logger.info("ScreenManager initialized")

    def register_screen(self, name: str, screen: Screen) -> None:
        """
        Register a screen with the manager.

        Args:
            name: Unique name for the screen
            screen: Screen instance
        """
        self.screens[name] = screen
        screen.set_screen_manager(self)
        logger.debug(f"Registered screen: {name}")

    def push_screen(self, screen_name: str) -> None:
        """
        Push a new screen onto the stack and display it.

        Args:
            screen_name: Name of the registered screen to display
        """
        if screen_name not in self.screens:
            logger.error(f"Screen not found: {screen_name}")
            return

        # Exit current screen and remove button handlers
        if self.current_screen:
            self._disconnect_buttons()
            self.current_screen.exit()
            self.screen_stack.append(self.current_screen)

        # Enter new screen and set up button handlers
        self.current_screen = self.screens[screen_name]
        self.current_screen.enter()
        self._connect_buttons()
        self.current_screen.render()

        logger.info(f"Pushed screen: {screen_name} (stack depth: {len(self.screen_stack)})")

    def pop_screen(self) -> bool:
        """
        Pop the current screen and return to the previous one.

        Returns:
            True if successful, False if stack is empty
        """
        if not self.screen_stack:
            logger.warning("Cannot pop: screen stack is empty")
            return False

        # Exit current screen and remove button handlers
        if self.current_screen:
            self._disconnect_buttons()
            self.current_screen.exit()

        # Return to previous screen and reconnect button handlers
        self.current_screen = self.screen_stack.pop()
        self.current_screen.enter()
        self._connect_buttons()
        self.current_screen.render()

        logger.info(f"Popped screen (stack depth: {len(self.screen_stack)})")
        return True

    def replace_screen(self, screen_name: str) -> None:
        """
        Replace the current screen without adding to stack.

        Args:
            screen_name: Name of the registered screen to display
        """
        if screen_name not in self.screens:
            logger.error(f"Screen not found: {screen_name}")
            return

        # Exit current screen and remove button handlers
        if self.current_screen:
            self._disconnect_buttons()
            self.current_screen.exit()

        # Enter new screen and connect button handlers (don't push old one to stack)
        self.current_screen = self.screens[screen_name]
        self.current_screen.enter()
        self._connect_buttons()
        self.current_screen.render()

        logger.info(f"Replaced screen with: {screen_name}")

    def clear_stack(self) -> None:
        """Clear the screen stack."""
        self.screen_stack.clear()
        logger.debug("Screen stack cleared")

    def get_current_screen(self) -> Optional[Screen]:
        """Get the currently displayed screen."""
        return self.current_screen

    def refresh_current_screen(self) -> None:
        """Re-render the current screen."""
        if self.current_screen:
            self.current_screen.render()

    def _connect_buttons(self) -> None:
        """Connect button handlers for the current screen."""
        if not self.current_screen:
            return

        # Register button callbacks with input handler
        self.input_handler.on_button(Button.A, ButtonEvent.PRESS, self.current_screen.on_button_a)
        self.input_handler.on_button(Button.B, ButtonEvent.PRESS, self.current_screen.on_button_b)
        self.input_handler.on_button(Button.X, ButtonEvent.PRESS, self.current_screen.on_button_x)
        self.input_handler.on_button(Button.Y, ButtonEvent.PRESS, self.current_screen.on_button_y)

        logger.debug(f"Connected button handlers for {self.current_screen.name}")

    def _disconnect_buttons(self) -> None:
        """Disconnect button handlers for the current screen."""
        if not self.current_screen:
            return

        # Clear all button callbacks by removing the current screen's handlers
        # Since we're switching screens, we'll just clear all callbacks
        for button in Button:
            for event_type in ButtonEvent:
                self.input_handler.callbacks[button][event_type].clear()

        logger.debug(f"Disconnected button handlers for {self.current_screen.name}")

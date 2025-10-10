"""
Input handling for YoyoPod button controls.

Manages button presses from the Pimoroni Display HAT Mini with
support for different event types and debouncing.
"""

import time
from enum import Enum
from typing import Callable, Dict, Optional
from threading import Thread, Event
from loguru import logger

try:
    from displayhatmini import DisplayHATMini
    HAS_BUTTONS = True
except ImportError:
    HAS_BUTTONS = False
    logger.warning("DisplayHATMini not available - button input will be simulated")


class ButtonEvent(Enum):
    """Button event types."""
    PRESS = "press"           # Single button press
    LONG_PRESS = "long_press" # Hold > 1 second
    DOUBLE_PRESS = "double_press"  # Two quick presses


class Button(Enum):
    """Button identifiers."""
    A = "A"
    B = "B"
    X = "X"
    Y = "Y"


class InputHandler:
    """
    Handles button input from Display HAT Mini.

    Supports single press, long press, and double press detection
    with debouncing to prevent false triggers.
    """

    # Timing constants (in seconds)
    DEBOUNCE_TIME = 0.05      # 50ms debounce
    LONG_PRESS_TIME = 1.0     # 1 second for long press
    DOUBLE_PRESS_TIME = 0.3   # 300ms window for double press

    def __init__(self, display_device: Optional[object] = None, simulate: bool = False) -> None:
        """
        Initialize the input handler.

        Args:
            display_device: DisplayHATMini instance (optional)
            simulate: If True, run in simulation mode
        """
        self.simulate = simulate or not HAS_BUTTONS
        self.device = display_device
        self.running = False
        self.poll_thread: Optional[Thread] = None
        self.stop_event = Event()

        # Button state tracking
        self.button_states: Dict[Button, bool] = {
            Button.A: False,
            Button.B: False,
            Button.X: False,
            Button.Y: False,
        }

        # Press time tracking for long press detection
        self.button_press_times: Dict[Button, Optional[float]] = {
            Button.A: None,
            Button.B: None,
            Button.X: None,
            Button.Y: None,
        }

        # Last press time for double press detection
        self.button_last_press: Dict[Button, Optional[float]] = {
            Button.A: None,
            Button.B: None,
            Button.X: None,
            Button.Y: None,
        }

        # Callbacks for button events
        self.callbacks: Dict[Button, Dict[ButtonEvent, list]] = {
            button: {
                ButtonEvent.PRESS: [],
                ButtonEvent.LONG_PRESS: [],
                ButtonEvent.DOUBLE_PRESS: [],
            }
            for button in Button
        }

        # Long press fired flags (to avoid firing both PRESS and LONG_PRESS)
        self.long_press_fired: Dict[Button, bool] = {
            Button.A: False,
            Button.B: False,
            Button.X: False,
            Button.Y: False,
        }

        if not self.simulate:
            logger.info("InputHandler initialized with hardware buttons")
        else:
            logger.info("InputHandler running in simulation mode")

    def on_button(
        self,
        button: Button,
        event_type: ButtonEvent,
        callback: Callable[[], None]
    ) -> None:
        """
        Register a callback for a button event.

        Args:
            button: Which button to listen for
            event_type: Type of event (PRESS, LONG_PRESS, DOUBLE_PRESS)
            callback: Function to call when event occurs
        """
        self.callbacks[button][event_type].append(callback)
        logger.debug(f"Registered callback for {button.value} {event_type.value}")

    def _get_button_state(self, button: Button) -> bool:
        """
        Get the current state of a button.

        Args:
            button: Button to check

        Returns:
            True if button is pressed, False otherwise
        """
        if self.simulate or not self.device:
            return False

        # Map button enum to displayhatmini button attributes
        button_map = {
            Button.A: self.device.read_button(self.device.BUTTON_A),
            Button.B: self.device.read_button(self.device.BUTTON_B),
            Button.X: self.device.read_button(self.device.BUTTON_X),
            Button.Y: self.device.read_button(self.device.BUTTON_Y),
        }

        return button_map.get(button, False)

    def _fire_callbacks(self, button: Button, event_type: ButtonEvent) -> None:
        """
        Fire all registered callbacks for a button event.

        Args:
            button: Button that triggered the event
            event_type: Type of event that occurred
        """
        callbacks = self.callbacks[button][event_type]
        if callbacks:
            logger.info(f"Button {button.value} {event_type.value}")
            for callback in callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in button callback: {e}")

    def _poll_buttons(self) -> None:
        """
        Poll button states in a loop.

        This runs in a separate thread and checks button states,
        detecting press types and firing appropriate callbacks.
        """
        logger.debug("Button polling started")

        while not self.stop_event.is_set():
            current_time = time.time()

            for button in Button:
                current_state = self._get_button_state(button)
                previous_state = self.button_states[button]

                # Button just pressed (transition from False to True)
                if current_state and not previous_state:
                    # Debounce
                    time.sleep(self.DEBOUNCE_TIME)
                    current_state = self._get_button_state(button)

                    if current_state:  # Still pressed after debounce
                        self.button_press_times[button] = current_time
                        self.button_states[button] = True
                        self.long_press_fired[button] = False
                        logger.debug(f"Button {button.value} pressed")

                # Button released (transition from True to False)
                elif not current_state and previous_state:
                    press_time = self.button_press_times[button]
                    self.button_states[button] = False

                    if press_time:
                        press_duration = current_time - press_time

                        # Don't fire PRESS if LONG_PRESS already fired
                        if not self.long_press_fired[button]:
                            # Check for double press
                            last_press = self.button_last_press[button]
                            if last_press and (current_time - last_press) < self.DOUBLE_PRESS_TIME:
                                self._fire_callbacks(button, ButtonEvent.DOUBLE_PRESS)
                                self.button_last_press[button] = None  # Reset to avoid triple press
                            else:
                                # Single press
                                self._fire_callbacks(button, ButtonEvent.PRESS)
                                self.button_last_press[button] = current_time

                        self.button_press_times[button] = None
                        logger.debug(f"Button {button.value} released after {press_duration:.2f}s")

                # Button held down - check for long press
                elif current_state and previous_state:
                    press_time = self.button_press_times[button]
                    if press_time and not self.long_press_fired[button]:
                        hold_duration = current_time - press_time
                        if hold_duration >= self.LONG_PRESS_TIME:
                            self._fire_callbacks(button, ButtonEvent.LONG_PRESS)
                            self.long_press_fired[button] = True

            time.sleep(0.01)  # 10ms polling rate

        logger.debug("Button polling stopped")

    def start(self) -> None:
        """Start the button input handler."""
        if self.running:
            logger.warning("InputHandler already running")
            return

        self.running = True
        self.stop_event.clear()
        self.poll_thread = Thread(target=self._poll_buttons, daemon=True)
        self.poll_thread.start()
        logger.info("InputHandler started")

    def stop(self) -> None:
        """Stop the button input handler."""
        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        if self.poll_thread:
            self.poll_thread.join(timeout=1.0)

        logger.info("InputHandler stopped")

    def simulate_button_press(self, button: Button, event_type: ButtonEvent = ButtonEvent.PRESS) -> None:
        """
        Simulate a button press (for testing without hardware).

        Args:
            button: Button to simulate
            event_type: Type of event to simulate
        """
        logger.info(f"Simulating {button.value} {event_type.value}")
        self._fire_callbacks(button, event_type)

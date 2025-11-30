"""
Input HAL for YoyoPod.

Provides hardware abstraction for various input methods:
- 4-button interface (Pimoroni Display HAT Mini)
- PTT button (Whisplay HAT)
- Voice commands (future)
- Touch screen (future)
"""

from yoyopy.ui.input.input_hal import InputHAL, InputAction
from yoyopy.ui.input.input_manager import InputManager
from yoyopy.ui.input.input_factory import get_input_manager

__all__ = [
    'InputHAL',
    'InputAction',
    'InputManager',
    'get_input_manager',
]

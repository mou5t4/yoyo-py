"""
Input adapter implementations.

Each adapter translates hardware-specific input (buttons, voice, touch)
into semantic InputActions.
"""

from yoyopy.ui.input.adapters.four_button import FourButtonInputAdapter
from yoyopy.ui.input.adapters.ptt_button import PTTInputAdapter
from yoyopy.ui.input.adapters.keyboard import KeyboardInputAdapter, get_keyboard_adapter

__all__ = [
    'FourButtonInputAdapter',
    'PTTInputAdapter',
    'KeyboardInputAdapter',
    'get_keyboard_adapter',
]

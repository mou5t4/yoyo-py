"""
Display hardware adapters for YoyoPod.

This package contains hardware-specific implementations of the DisplayHAL interface.

Available adapters:
- PimoroniDisplayAdapter: Pimoroni Display HAT Mini (320×240 landscape)
- WhisplayDisplayAdapter: PiSugar Whisplay HAT (240×280 portrait)
"""

from yoyopy.ui.adapters.display_pimoroni import PimoroniDisplayAdapter
from yoyopy.ui.adapters.display_whisplay import WhisplayDisplayAdapter

__all__ = [
    'PimoroniDisplayAdapter',
    'WhisplayDisplayAdapter',
]

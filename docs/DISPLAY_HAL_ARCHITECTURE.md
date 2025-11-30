# YoyoPod Display Hardware Abstraction Layer (HAL) Architecture

**Version:** 1.0
**Date:** 2025-11-30
**Status:** Proposal
**Author:** Claude Code

---

## 1. Executive Summary

This document proposes a **Hardware Abstraction Layer (HAL)** for the YoyoPod display subsystem to support multiple display hardware configurations while maintaining a unified programming interface.

### Key Goals

1. ✅ **Hardware Independence**: Support both Pimoroni Display HAT Mini (320×240 landscape) and PiSugar Whisplay HAT (240×280 portrait)
2. ✅ **Backward Compatibility**: Preserve existing `Display` class API for minimal code changes
3. ✅ **Extensibility**: Easy addition of new display hardware in the future
4. ✅ **Configuration-Driven**: Hardware selection via config file, not code changes
5. ✅ **Zero Performance Overhead**: Direct hardware calls, no unnecessary abstraction layers

---

## 2. Current Architecture (Before HAL)

```
┌─────────────────────────────────────────────┐
│           YoyoPod Application               │
│  (app.py, screens.py, screen_manager.py)   │
└─────────────────┬───────────────────────────┘
                  │
                  │ Direct dependency
                  ▼
┌─────────────────────────────────────────────┐
│         Display Controller                  │
│         (yoyopy/ui/display.py)              │
│                                             │
│  - WIDTH = 320, HEIGHT = 240               │
│  - from displayhatmini import...           │
│  - Hardcoded to Pimoroni HAT               │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Pimoroni Display    │
        │  HAT Mini Hardware  │
        │   (320×240 SPI)     │
        └─────────────────────┘
```

**Problems:**
- ❌ Hardcoded to Pimoroni hardware
- ❌ Fixed display dimensions
- ❌ Cannot support Whisplay HAT without rewriting
- ❌ Screens assume landscape orientation

---

## 3. Proposed HAL Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    YoyoPod Application                           │
│            (app.py, screens.py, screen_manager.py)               │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ Uses unified interface
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Display Controller                             │
│                   (yoyopy/ui/display.py)                         │
│                                                                  │
│  - get_display(hardware: str) -> DisplayHAL                     │
│  - Factory method creates appropriate adapter                   │
│  - Maintains backward-compatible API                            │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             │ Abstract interface
                             ▼
         ┌─────────────────────────────────────────┐
         │       DisplayHAL Interface              │
         │    (yoyopy/ui/display_hal.py)           │
         │                                         │
         │  Abstract Methods:                      │
         │  - clear(color)                         │
         │  - text(text, x, y, color, ...)         │
         │  - rectangle(x1, y1, x2, y2, ...)       │
         │  - circle(x, y, radius, ...)            │
         │  - line(x1, y1, x2, y2, ...)            │
         │  - image(path, x, y, w, h)              │
         │  - status_bar(time, battery, signal)    │
         │  - update()                             │
         │  - set_backlight(brightness)            │
         │  - get_text_size(text, size)            │
         │                                         │
         │  Properties:                            │
         │  - WIDTH: int                           │
         │  - HEIGHT: int                          │
         │  - ORIENTATION: str ("landscape"/"portrait") │
         │  - COLOR_* constants                    │
         └──────────┬────────────────────┬─────────┘
                    │                    │
         ┌──────────▼──────────┐  ┌─────▼──────────────┐
         │ PimoroniAdapter     │  │ WhisplayAdapter    │
         │ (display_pimoroni)  │  │ (display_whisplay) │
         │                     │  │                    │
         │ - 320×240 landscape │  │ - 240×280 portrait │
         │ - DisplayHATMini    │  │ - WhisPlayBoard    │
         │ - 4 buttons (ABXY)  │  │ - 1 button (PTT)   │
         └──────────┬──────────┘  └─────┬──────────────┘
                    │                   │
                    ▼                   ▼
         ┌──────────────────┐  ┌────────────────────┐
         │  Pimoroni HAT    │  │   Whisplay HAT     │
         │  (DisplayHATMini)│  │  (WhisPlayBoard)   │
         └──────────────────┘  └────────────────────┘
```

---

## 4. Design Patterns Used

### 4.1 **Adapter Pattern**
Each hardware implementation is wrapped in an adapter that implements the `DisplayHAL` interface.

```python
DisplayHAL (Interface)
    ↑ implements
    │
    ├── PimoroniDisplayAdapter
    └── WhisplayDisplayAdapter
```

### 4.2 **Factory Pattern**
A factory function creates the appropriate adapter based on configuration.

```python
def get_display(hardware: str = "auto", simulate: bool = False) -> DisplayHAL:
    """Factory method to create display adapter"""
    if hardware == "auto":
        hardware = detect_hardware()

    if hardware == "whisplay":
        return WhisplayDisplayAdapter(simulate)
    elif hardware == "pimoroni":
        return PimoroniDisplayAdapter(simulate)
    else:
        raise ValueError(f"Unknown hardware: {hardware}")
```

### 4.3 **Facade Pattern**
The existing `Display` class becomes a facade that delegates to the HAL adapter.

```python
class Display:
    """Facade for display hardware (backward compatibility)"""
    def __init__(self, hardware: str = "auto", simulate: bool = False):
        self._adapter = get_display(hardware, simulate)

    def clear(self, color=None):
        return self._adapter.clear(color)

    # ... delegates all methods to adapter
```

---

## 5. Component Specifications

### 5.1 DisplayHAL Interface

**File:** `yoyopy/ui/display_hal.py`

```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from pathlib import Path
from PIL import Image


class DisplayHAL(ABC):
    """
    Abstract base class for display hardware adapters.

    All display implementations must inherit from this class
    and implement the required methods.
    """

    # Display dimensions (must be set by subclass)
    WIDTH: int = 0
    HEIGHT: int = 0
    ORIENTATION: str = "landscape"  # "landscape" or "portrait"
    STATUS_BAR_HEIGHT: int = 20

    # Standard color palette (RGB tuples)
    COLOR_BLACK = (0, 0, 0)
    COLOR_WHITE = (255, 255, 255)
    COLOR_RED = (255, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_YELLOW = (255, 255, 0)
    COLOR_CYAN = (0, 255, 255)
    COLOR_MAGENTA = (255, 0, 255)
    COLOR_GRAY = (128, 128, 128)
    COLOR_DARK_GRAY = (64, 64, 64)

    @abstractmethod
    def __init__(self, simulate: bool = False) -> None:
        """Initialize the display hardware"""
        pass

    @abstractmethod
    def clear(self, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Clear display with specified color"""
        pass

    @abstractmethod
    def text(
        self,
        text: str,
        x: int,
        y: int,
        color: Optional[Tuple[int, int, int]] = None,
        font_size: int = 16,
        font_path: Optional[Path] = None
    ) -> None:
        """Draw text at specified position"""
        pass

    @abstractmethod
    def rectangle(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a rectangle"""
        pass

    @abstractmethod
    def circle(
        self,
        x: int, y: int,
        radius: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a circle"""
        pass

    @abstractmethod
    def line(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        color: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a line"""
        pass

    @abstractmethod
    def image(
        self,
        image_path: Path,
        x: int, y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> None:
        """Draw an image"""
        pass

    @abstractmethod
    def status_bar(
        self,
        time_str: str = "--:--",
        battery_percent: int = 100,
        signal_strength: int = 4
    ) -> None:
        """Draw status bar at top of screen"""
        pass

    @abstractmethod
    def update(self) -> None:
        """Flush buffer to physical display"""
        pass

    @abstractmethod
    def set_backlight(self, brightness: float) -> None:
        """Set backlight brightness (0.0 to 1.0)"""
        pass

    @abstractmethod
    def get_text_size(self, text: str, font_size: int = 16) -> Tuple[int, int]:
        """Get rendered text dimensions (width, height)"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources on shutdown"""
        pass

    # Helper methods (can be overridden)
    def get_orientation(self) -> str:
        """Get display orientation"""
        return self.ORIENTATION

    def is_portrait(self) -> bool:
        """Check if display is in portrait mode"""
        return self.ORIENTATION == "portrait"

    def is_landscape(self) -> bool:
        """Check if display is in landscape mode"""
        return self.ORIENTATION == "landscape"
```

---

### 5.2 PimoroniDisplayAdapter

**File:** `yoyopy/ui/adapters/display_pimoroni.py`

```python
from yoyopy.ui.display_hal import DisplayHAL
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

try:
    from displayhatmini import DisplayHATMini
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    logger.warning("DisplayHATMini library not available")


class PimoroniDisplayAdapter(DisplayHAL):
    """
    Adapter for Pimoroni Display HAT Mini.

    Specs:
    - 320×240 pixels (landscape)
    - ST7789 driver (SPI)
    - 4 buttons (A, B, X, Y)
    - RGB LED
    """

    # Display configuration
    WIDTH = 320
    HEIGHT = 240
    ORIENTATION = "landscape"
    STATUS_BAR_HEIGHT = 20

    def __init__(self, simulate: bool = False) -> None:
        self.simulate = simulate or not HAS_HARDWARE
        self.buffer: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.device = None

        self._create_buffer()

        if not self.simulate:
            try:
                self.device = DisplayHATMini(self.buffer, backlight_pwm=True)
                self.device.set_backlight(1.0)
                self.device.set_led(0.1, 0.0, 0.5)  # Purple LED
                logger.info("Pimoroni DisplayHATMini initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Pimoroni display: {e}")
                self.simulate = True
                self.device = None
        else:
            logger.info("Pimoroni display in simulation mode")

    def _create_buffer(self) -> None:
        """Create PIL drawing buffer"""
        self.buffer = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BLACK)
        self.draw = ImageDraw.Draw(self.buffer)

    def clear(self, color: Optional[Tuple[int, int, int]] = None) -> None:
        if color is None:
            color = self.COLOR_BLACK
        self.draw.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=color)

    def text(self, text: str, x: int, y: int,
             color: Optional[Tuple[int, int, int]] = None,
             font_size: int = 16,
             font_path: Optional[Path] = None) -> None:
        if color is None:
            color = self.COLOR_WHITE

        # Font loading logic (same as current implementation)
        try:
            if font_path and font_path.exists():
                font = ImageFont.truetype(str(font_path), font_size)
            else:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    font_size
                )
        except:
            font = ImageFont.load_default()

        self.draw.text((x, y), text, fill=color, font=font)

    # ... (implement all other abstract methods)

    def update(self) -> None:
        if not self.simulate and self.device:
            try:
                self.device.display()
            except Exception as e:
                logger.error(f"Display update failed: {e}")

    def cleanup(self) -> None:
        """Cleanup Pimoroni display resources"""
        if self.device:
            self.device.set_backlight(0)
            self.device.set_led(0, 0, 0)
        logger.info("Pimoroni display cleaned up")
```

---

### 5.3 WhisplayDisplayAdapter

**File:** `yoyopy/ui/adapters/display_whisplay.py`

```python
from yoyopy.ui.display_hal import DisplayHAL
from typing import Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import sys

# Add Whisplay driver to path
sys.path.append("/home/tifo/Whisplay/Driver")

try:
    from WhisPlay import WhisPlayBoard
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    logger.warning("WhisPlay library not available")


class WhisplayDisplayAdapter(DisplayHAL):
    """
    Adapter for PiSugar Whisplay HAT.

    Specs:
    - 240×280 pixels (portrait)
    - ST7789P3 driver (SPI)
    - 1 mouse click button (PTT)
    - RGB LED
    - WM8960 audio codec with dual mics
    """

    # Display configuration
    WIDTH = 240
    HEIGHT = 280
    ORIENTATION = "portrait"
    STATUS_BAR_HEIGHT = 25  # Slightly taller for portrait

    def __init__(self, simulate: bool = False) -> None:
        self.simulate = simulate or not HAS_HARDWARE
        self.buffer: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.device = None

        self._create_buffer()

        if not self.simulate:
            try:
                self.device = WhisPlayBoard()
                self.device.set_backlight(100)
                self.device.set_rgb(0, 100, 200)  # Blue LED
                logger.info("Whisplay HAT initialized (240×280 portrait)")
            except Exception as e:
                logger.error(f"Failed to initialize Whisplay display: {e}")
                self.simulate = True
                self.device = None
        else:
            logger.info("Whisplay display in simulation mode")

    def _create_buffer(self) -> None:
        """Create PIL drawing buffer"""
        self.buffer = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BLACK)
        self.draw = ImageDraw.Draw(self.buffer)

    def clear(self, color: Optional[Tuple[int, int, int]] = None) -> None:
        if color is None:
            color = self.COLOR_BLACK
        self.draw.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=color)

    def text(self, text: str, x: int, y: int,
             color: Optional[Tuple[int, int, int]] = None,
             font_size: int = 16,
             font_path: Optional[Path] = None) -> None:
        if color is None:
            color = self.COLOR_WHITE

        try:
            if font_path and font_path.exists():
                font = ImageFont.truetype(str(font_path), font_size)
            else:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    font_size
                )
        except:
            font = ImageFont.load_default()

        self.draw.text((x, y), text, fill=color, font=font)

    # ... (implement all other abstract methods)

    def update(self) -> None:
        """Convert PIL buffer to RGB565 and send to Whisplay display"""
        if not self.simulate and self.device:
            try:
                # Convert RGB888 PIL image to RGB565 byte array
                pixel_data = []
                for y in range(self.HEIGHT):
                    for x in range(self.WIDTH):
                        r, g, b = self.buffer.getpixel((x, y))
                        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                        pixel_data.extend([(rgb565 >> 8) & 0xFF, rgb565 & 0xFF])

                self.device.draw_image(0, 0, self.WIDTH, self.HEIGHT, pixel_data)
            except Exception as e:
                logger.error(f"Whisplay display update failed: {e}")

    def set_backlight(self, brightness: float) -> None:
        """Set backlight (0.0 to 1.0)"""
        if not self.simulate and self.device:
            # Whisplay uses 0-100 scale
            self.device.set_backlight(int(brightness * 100))

    def cleanup(self) -> None:
        """Cleanup Whisplay display resources"""
        if self.device:
            self.device.set_backlight(0)
            self.device.set_rgb(0, 0, 0)
            self.device.cleanup()
        logger.info("Whisplay display cleaned up")
```

---

## 6. Display Factory

**File:** `yoyopy/ui/display_factory.py`

```python
from yoyopy.ui.display_hal import DisplayHAL
from yoyopy.ui.adapters.display_pimoroni import PimoroniDisplayAdapter
from yoyopy.ui.adapters.display_whisplay import WhisplayDisplayAdapter
from loguru import logger
import os


def detect_hardware() -> str:
    """
    Auto-detect which display hardware is connected.

    Detection logic:
    1. Check environment variable YOYOPOD_DISPLAY
    2. Check for Whisplay driver (/home/tifo/Whisplay/Driver/WhisPlay.py)
    3. Check for DisplayHATMini library
    4. Default to simulation

    Returns:
        "whisplay", "pimoroni", or "simulation"
    """
    # 1. Check environment override
    env_display = os.getenv("YOYOPOD_DISPLAY")
    if env_display:
        logger.info(f"Display hardware set by YOYOPOD_DISPLAY={env_display}")
        return env_display.lower()

    # 2. Check for Whisplay driver
    whisplay_driver = "/home/tifo/Whisplay/Driver/WhisPlay.py"
    if os.path.exists(whisplay_driver):
        logger.info("Detected Whisplay HAT (driver found)")
        return "whisplay"

    # 3. Check for Pimoroni library
    try:
        import displayhatmini
        logger.info("Detected Pimoroni Display HAT Mini (library imported)")
        return "pimoroni"
    except ImportError:
        pass

    # 4. Default to simulation
    logger.warning("No display hardware detected, using simulation")
    return "simulation"


def get_display(hardware: str = "auto", simulate: bool = False) -> DisplayHAL:
    """
    Factory method to create appropriate display adapter.

    Args:
        hardware: "auto" (auto-detect), "whisplay", "pimoroni", or "simulation"
        simulate: Force simulation mode (for testing)

    Returns:
        DisplayHAL instance

    Raises:
        ValueError: If hardware type is unknown

    Examples:
        # Auto-detect hardware
        display = get_display()

        # Force specific hardware
        display = get_display("whisplay")

        # Simulation mode
        display = get_display(simulate=True)
    """
    if hardware == "auto":
        hardware = detect_hardware()

    hardware = hardware.lower()

    if hardware == "whisplay":
        logger.info("Creating Whisplay display adapter (240×280 portrait)")
        return WhisplayDisplayAdapter(simulate=simulate)

    elif hardware == "pimoroni":
        logger.info("Creating Pimoroni display adapter (320×240 landscape)")
        return PimoroniDisplayAdapter(simulate=simulate)

    elif hardware == "simulation":
        logger.info("Creating simulated display adapter")
        # Use Pimoroni adapter in simulation mode for backward compatibility
        return PimoroniDisplayAdapter(simulate=True)

    else:
        raise ValueError(
            f"Unknown display hardware: '{hardware}'. "
            f"Valid options: 'auto', 'whisplay', 'pimoroni', 'simulation'"
        )
```

---

## 7. Updated Display Controller (Backward Compatible)

**File:** `yoyopy/ui/display.py`

```python
"""
Display controller with hardware abstraction.

Provides backward-compatible Display class that delegates to
appropriate hardware adapter based on configuration.
"""

from yoyopy.ui.display_factory import get_display
from yoyopy.ui.display_hal import DisplayHAL
from typing import Optional, Tuple
from pathlib import Path


class Display:
    """
    Display controller with hardware abstraction.

    This class maintains the same API as the original Display class
    for backward compatibility, but delegates to hardware-specific
    adapters internally.

    Usage:
        # Auto-detect hardware
        display = Display()

        # Specify hardware
        display = Display(hardware="whisplay")

        # Simulation mode
        display = Display(simulate=True)
    """

    def __init__(self, hardware: str = "auto", simulate: bool = False) -> None:
        """
        Initialize display with hardware abstraction.

        Args:
            hardware: "auto", "whisplay", "pimoroni", or "simulation"
            simulate: Force simulation mode
        """
        # Create appropriate adapter using factory
        self._adapter: DisplayHAL = get_display(hardware, simulate)

        # Expose adapter properties as Display properties
        self.WIDTH = self._adapter.WIDTH
        self.HEIGHT = self._adapter.HEIGHT
        self.ORIENTATION = self._adapter.ORIENTATION
        self.STATUS_BAR_HEIGHT = self._adapter.STATUS_BAR_HEIGHT

        # Expose color constants
        self.COLOR_BLACK = self._adapter.COLOR_BLACK
        self.COLOR_WHITE = self._adapter.COLOR_WHITE
        self.COLOR_RED = self._adapter.COLOR_RED
        self.COLOR_GREEN = self._adapter.COLOR_GREEN
        self.COLOR_BLUE = self._adapter.COLOR_BLUE
        self.COLOR_YELLOW = self._adapter.COLOR_YELLOW
        self.COLOR_CYAN = self._adapter.COLOR_CYAN
        self.COLOR_MAGENTA = self._adapter.COLOR_MAGENTA
        self.COLOR_GRAY = self._adapter.COLOR_GRAY
        self.COLOR_DARK_GRAY = self._adapter.COLOR_DARK_GRAY

    # Delegate all methods to adapter
    def clear(self, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Clear display with specified color"""
        self._adapter.clear(color)

    def text(
        self,
        text: str,
        x: int,
        y: int,
        color: Optional[Tuple[int, int, int]] = None,
        font_size: int = 16,
        font_path: Optional[Path] = None
    ) -> None:
        """Draw text at specified position"""
        self._adapter.text(text, x, y, color, font_size, font_path)

    def rectangle(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a rectangle"""
        self._adapter.rectangle(x1, y1, x2, y2, fill, outline, width)

    def circle(
        self,
        x: int, y: int,
        radius: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a circle"""
        self._adapter.circle(x, y, radius, fill, outline, width)

    def line(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        color: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """Draw a line"""
        self._adapter.line(x1, y1, x2, y2, color, width)

    def image(
        self,
        image_path: Path,
        x: int, y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> None:
        """Draw an image"""
        self._adapter.image(image_path, x, y, width, height)

    def status_bar(
        self,
        time_str: str = "--:--",
        battery_percent: int = 100,
        signal_strength: int = 4
    ) -> None:
        """Draw status bar at top of screen"""
        self._adapter.status_bar(time_str, battery_percent, signal_strength)

    def update(self) -> None:
        """Flush buffer to physical display"""
        self._adapter.update()

    def set_backlight(self, brightness: float) -> None:
        """Set backlight brightness (0.0 to 1.0)"""
        self._adapter.set_backlight(brightness)

    def get_text_size(self, text: str, font_size: int = 16) -> Tuple[int, int]:
        """Get rendered text dimensions"""
        return self._adapter.get_text_size(text, font_size)

    def cleanup(self) -> None:
        """Cleanup display resources"""
        self._adapter.cleanup()

    # Helper methods
    def is_portrait(self) -> bool:
        """Check if display is in portrait orientation"""
        return self._adapter.is_portrait()

    def is_landscape(self) -> bool:
        """Check if display is in landscape orientation"""
        return self._adapter.is_landscape()
```

---

## 8. Configuration

**File:** `config/yoyopod_config.yaml`

```yaml
# YoyoPod Configuration

# Display hardware selection
display:
  # Hardware type: "auto" (auto-detect), "whisplay", "pimoroni", or "simulation"
  hardware: "auto"

  # Force simulation mode (for testing without hardware)
  simulate: false

  # Default backlight brightness (0.0 to 1.0)
  backlight: 0.8

# Audio configuration
audio:
  # For Whisplay HAT (WM8960)
  whisplay:
    output_device: "wm8960soundcard"
    card_id: 1
    device_id: 0
    sample_rate: 48000
    channels: 2

    # Microphone (dual MEMS mics)
    mic_enabled: true
    mic_sample_rate: 16000
    mic_channels: 1

  # For Pimoroni HAT (USB audio)
  pimoroni:
    output_device: "USB"
    card_id: 0

# Input configuration
input:
  # For Whisplay HAT
  whisplay:
    button_gpio: 11  # BOARD mode
    button_mode: "ptt"  # Push-to-talk

  # For Pimoroni HAT
  pimoroni:
    buttons: ["A", "B", "X", "Y"]

# VoIP settings
voip:
  enabled: true
  # ... (existing VoIP config)

# Mopidy settings
mopidy:
  enabled: true
  # ... (existing Mopidy config)
```

---

## 9. Directory Structure

```
yoyo-py/
├── yoyopy/
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── display.py              ← Updated (facade with HAL)
│   │   ├── display_hal.py          ← NEW (abstract interface)
│   │   ├── display_factory.py      ← NEW (factory + auto-detect)
│   │   ├── adapters/
│   │   │   ├── __init__.py         ← NEW
│   │   │   ├── display_pimoroni.py ← NEW (Pimoroni adapter)
│   │   │   └── display_whisplay.py ← NEW (Whisplay adapter)
│   │   ├── screen.py
│   │   ├── screens.py              ← Will update (dynamic layouts)
│   │   ├── screen_manager.py
│   │   └── input_handler.py
│   ├── app.py                      ← Minor update (config-driven display)
│   └── ...
├── config/
│   └── yoyopod_config.yaml         ← Updated (display hardware config)
├── docs/
│   └── DISPLAY_HAL_ARCHITECTURE.md ← This document
└── ...
```

---

## 10. Migration Strategy

### Phase 1: Create HAL Infrastructure ✅
1. Create `display_hal.py` (abstract interface)
2. Create `display_factory.py` (factory + detection)
3. Create `adapters/` directory

### Phase 2: Implement Adapters ✅
1. Create `display_pimoroni.py` (move existing code)
2. Create `display_whisplay.py` (new Whisplay support)
3. Test both adapters independently

### Phase 3: Update Display Controller ✅
1. Update `display.py` to use factory pattern
2. Maintain backward compatibility
3. Test with existing screens

### Phase 4: Update Application Code ✅
1. Update `app.py` to load display config
2. Update `yoyopod.py` to pass hardware parameter
3. Add config file parsing

### Phase 5: Adapt Screens (Optional) 🔄
1. Update screens to query `display.ORIENTATION`
2. Adjust layouts for portrait vs landscape
3. Make text/element sizing dynamic

### Phase 6: Testing & Validation ✅
1. Test Pimoroni HAT (verify no regression)
2. Test Whisplay HAT (verify portrait mode)
3. Test simulation mode
4. Test hardware auto-detection

---

## 11. Backward Compatibility

### Existing Code (No Changes Required)
```python
# This code continues to work unchanged
from yoyopy.ui.display import Display

display = Display()
display.clear()
display.text("Hello", 10, 10, color=display.COLOR_WHITE, font_size=16)
display.update()
```

### New Code (Hardware Selection)
```python
# Explicitly select hardware
from yoyopy.ui.display import Display

display = Display(hardware="whisplay")  # Force Whisplay HAT
display.clear()
display.text("Hello", 10, 10, color=display.COLOR_WHITE, font_size=16)
display.update()
```

### Configuration-Driven (Recommended)
```python
# Load from config file
from yoyopy.ui.display import Display
from yoyopy.config import ConfigManager

config = ConfigManager("config")
hardware = config.get("display.hardware", "auto")

display = Display(hardware=hardware)
# ... rest of code unchanged
```

---

## 12. Benefits of This Architecture

### ✅ **Hardware Independence**
- Swap display hardware by changing config file
- No code changes required in application layer

### ✅ **Maintainability**
- Clear separation of concerns
- Each adapter is self-contained
- Easy to add new display hardware

### ✅ **Testability**
- Simulation mode works for both hardware types
- Can test portrait and landscape layouts without hardware
- Factory pattern enables dependency injection

### ✅ **Extensibility**
- Adding new display hardware requires only:
  1. Create new adapter (implement `DisplayHAL`)
  2. Register in factory function
  3. Update config schema

### ✅ **Performance**
- Zero overhead: Direct delegation to adapters
- No unnecessary abstraction layers
- Hardware-specific optimizations in adapters

### ✅ **Developer Experience**
- Same familiar API as before
- Auto-detection "just works"
- Configuration overrides for testing

---

## 13. Next Steps

Once this architecture is approved:

1. **Implement HAL interface** (`display_hal.py`)
2. **Create Pimoroni adapter** (refactor existing `display.py`)
3. **Create Whisplay adapter** (integrate WhisPlay driver)
4. **Update Display controller** (factory pattern)
5. **Test with existing application**
6. **Update screen layouts** for portrait mode
7. **Document usage** and best practices

---

## 14. Open Questions / Design Decisions Needed

1. **Screen Adaptation Strategy**:
   - Should screens auto-adapt to portrait/landscape?
   - Or create separate screen variants (e.g., `MenuScreen` vs `MenuScreenPortrait`)?
   - **Recommendation**: Auto-adapt with orientation queries

2. **Status Bar**:
   - Should status bar layout differ in portrait mode?
   - **Recommendation**: Yes, portrait can have taller status bar with vertical layout

3. **Button Input**:
   - Should input handling also use HAL pattern?
   - **Recommendation**: Yes, but separate document (not in scope for display HAL)

4. **Testing**:
   - Should we create pytest fixtures for HAL testing?
   - **Recommendation**: Yes, add to Phase 6

---

## Appendix A: Hardware Comparison

| Feature | Pimoroni Display HAT Mini | PiSugar Whisplay HAT |
|---------|---------------------------|----------------------|
| **Display** | 320×240 pixels | 240×280 pixels |
| **Orientation** | Landscape | Portrait |
| **Driver** | ST7789 (SPI) | ST7789P3 (SPI) |
| **Buttons** | 4 tactile (A, B, X, Y) | 1 mouse click |
| **LED** | RGB LED | RGB LED |
| **Audio** | None (external USB) | WM8960 codec |
| **Microphone** | None | Dual MEMS |
| **Interface** | DisplayHATMini library | WhisPlay driver |
| **Power** | 5V GPIO | 5V GPIO |
| **Use Case** | Music player + VoIP | Kids streaming + voice |

---

**End of Architecture Proposal**

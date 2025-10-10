"""
Display controller for Pimoroni Display HAT Mini.

Provides hardware abstraction for the Display HAT Mini 320x240 display
with drawing primitives and status bar functionality.
"""

from typing import Optional, Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

try:
    from displayhatmini import DisplayHATMini
    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False
    logger.warning("DisplayHATMini library not available - display will be simulated")


class Display:
    """
    Display controller for Pimoroni Display HAT Mini.

    Manages the ST7789 240x320 pixel display with hardware acceleration
    and provides high-level drawing primitives.
    """

    # Display dimensions for Pimoroni Display HAT Mini
    WIDTH = 320
    HEIGHT = 240

    # Status bar height
    STATUS_BAR_HEIGHT = 20

    # Colors (RGB tuples)
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

    def __init__(self, simulate: bool = False) -> None:
        """
        Initialize the display controller.

        Args:
            simulate: If True, simulate display without hardware (for testing)
        """
        self.simulate = simulate or not HAS_DISPLAY
        self.buffer: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.device = None

        # Create drawing buffer first
        self._create_buffer()

        if not self.simulate:
            try:
                # Initialize DisplayHATMini with buffer and backlight PWM
                self.device = DisplayHATMini(self.buffer, backlight_pwm=True)
                self.device.set_backlight(1.0)  # Full brightness
                # Optional: Set LED to a subtle color
                self.device.set_led(0.1, 0.0, 0.5)  # Purple LED
                logger.info("DisplayHATMini initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize display hardware: {e}")
                logger.info("Falling back to simulation mode")
                self.simulate = True
                self.device = None
        else:
            logger.info("Display running in simulation mode")

    def _create_buffer(self) -> None:
        """Create a new drawing buffer."""
        self.buffer = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COLOR_BLACK)
        self.draw = ImageDraw.Draw(self.buffer)

    def clear(self, color: Tuple[int, int, int] = None) -> None:
        """
        Clear the display with specified color.

        Args:
            color: RGB tuple (default: black)
        """
        if color is None:
            color = self.COLOR_BLACK

        self._create_buffer()
        self.draw.rectangle([(0, 0), (self.WIDTH, self.HEIGHT)], fill=color)
        logger.debug(f"Display cleared with color {color}")

    def text(
        self,
        text: str,
        x: int,
        y: int,
        color: Tuple[int, int, int] = None,
        font_size: int = 16,
        font_path: Optional[Path] = None
    ) -> None:
        """
        Draw text on the display.

        Args:
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            color: Text color (default: white)
            font_size: Font size in pixels
            font_path: Path to TTF font file (optional)
        """
        if color is None:
            color = self.COLOR_WHITE

        try:
            if font_path and font_path.exists():
                font = ImageFont.truetype(str(font_path), font_size)
            else:
                # Try to use a default system font
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    font = ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Failed to load font: {e}, using default")
            font = ImageFont.load_default()

        self.draw.text((x, y), text, fill=color, font=font)

    def rectangle(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """
        Draw a rectangle.

        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
            fill: Fill color (optional)
            outline: Outline color (optional)
            width: Outline width
        """
        self.draw.rectangle([(x1, y1), (x2, y2)], fill=fill, outline=outline, width=width)

    def circle(
        self,
        x: int,
        y: int,
        radius: int,
        fill: Optional[Tuple[int, int, int]] = None,
        outline: Optional[Tuple[int, int, int]] = None,
        width: int = 1
    ) -> None:
        """
        Draw a circle.

        Args:
            x, y: Center coordinates
            radius: Circle radius
            fill: Fill color (optional)
            outline: Outline color (optional)
            width: Outline width
        """
        bbox = [x - radius, y - radius, x + radius, y + radius]
        self.draw.ellipse(bbox, fill=fill, outline=outline, width=width)

    def line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: Tuple[int, int, int] = None,
        width: int = 1
    ) -> None:
        """
        Draw a line.

        Args:
            x1, y1: Start point
            x2, y2: End point
            color: Line color (default: white)
            width: Line width
        """
        if color is None:
            color = self.COLOR_WHITE

        self.draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    def image(
        self,
        image_path: Path,
        x: int,
        y: int,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> None:
        """
        Draw an image.

        Args:
            image_path: Path to image file
            x, y: Position to draw image
            width, height: Optional resize dimensions
        """
        try:
            img = Image.open(image_path)

            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            self.buffer.paste(img, (x, y))
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")

    def status_bar(
        self,
        time_str: str = "--:--",
        battery_percent: int = 100,
        signal_strength: int = 4
    ) -> None:
        """
        Draw a status bar at the top of the screen.

        Args:
            time_str: Time string to display
            battery_percent: Battery percentage (0-100)
            signal_strength: Signal strength (0-4 bars)
        """
        # Draw background
        self.rectangle(
            0, 0,
            self.WIDTH, self.STATUS_BAR_HEIGHT,
            fill=self.COLOR_DARK_GRAY
        )

        # Draw time (centered)
        time_x = (self.WIDTH - len(time_str) * 8) // 2
        self.text(time_str, time_x, 2, color=self.COLOR_WHITE, font_size=14)

        # Draw battery indicator (right side)
        battery_x = self.WIDTH - 50
        battery_y = 4
        battery_width = 40
        battery_height = 12

        # Battery outline
        self.rectangle(
            battery_x, battery_y,
            battery_x + battery_width, battery_y + battery_height,
            outline=self.COLOR_WHITE,
            width=1
        )

        # Battery tip
        self.rectangle(
            battery_x + battery_width, battery_y + 3,
            battery_x + battery_width + 3, battery_y + battery_height - 3,
            fill=self.COLOR_WHITE
        )

        # Battery fill
        fill_width = int((battery_width - 4) * (battery_percent / 100))
        if fill_width > 0:
            battery_color = self.COLOR_GREEN if battery_percent > 20 else self.COLOR_RED
            self.rectangle(
                battery_x + 2, battery_y + 2,
                battery_x + 2 + fill_width, battery_y + battery_height - 2,
                fill=battery_color
            )

        # Draw signal strength (left side)
        signal_x = 5
        signal_y = 8
        bar_width = 3
        bar_spacing = 2

        for i in range(4):
            bar_height = 4 + (i * 2)
            bar_color = self.COLOR_WHITE if i < signal_strength else self.COLOR_DARK_GRAY

            self.rectangle(
                signal_x + (i * (bar_width + bar_spacing)),
                signal_y + (12 - bar_height),
                signal_x + (i * (bar_width + bar_spacing)) + bar_width,
                signal_y + 12,
                fill=bar_color
            )

    def update(self) -> None:
        """
        Update the physical display with the current buffer.
        """
        if self.buffer is None:
            logger.warning("No buffer to display")
            return

        if not self.simulate and self.device:
            try:
                self.device.display()
                logger.debug("Display updated")
            except Exception as e:
                logger.error(f"Failed to update display: {e}")
        else:
            # In simulation mode, optionally save to file for debugging
            logger.debug("Display update (simulated)")

    def set_backlight(self, brightness: float) -> None:
        """
        Set display backlight brightness.

        Args:
            brightness: Brightness level (0.0 to 1.0)
        """
        if not self.simulate and self.device:
            try:
                self.device.set_backlight(brightness)
                logger.debug(f"Backlight set to {brightness}")
            except Exception as e:
                logger.error(f"Failed to set backlight: {e}")

    def get_text_size(self, text: str, font_size: int = 16) -> Tuple[int, int]:
        """
        Get the size of text that would be rendered.

        Args:
            text: Text to measure
            font_size: Font size

        Returns:
            (width, height) tuple
        """
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = self.draw.textbbox((0, 0), text, font=font)
        return (bbox[2] - bbox[0], bbox[3] - bbox[1])

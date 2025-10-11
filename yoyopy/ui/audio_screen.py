"""
Audio test screen for YoyoPod.

Displays current volume and allows audio testing.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pathlib import Path
from loguru import logger

from yoyopy.ui.display import Display
from yoyopy.ui.screens import Screen

if TYPE_CHECKING:
    from yoyopy.app_context import AppContext
    from yoyopy.audio.audio_manager import AudioManager


class AudioScreen(Screen):
    """
    Audio test screen.

    Displays current volume level, audio device, and allows testing
    audio playback with test sounds.

    Button mapping:
    - Button A: Play test sound
    - Button B: Go back
    - Button X: Volume up
    - Button Y: Volume down
    """

    def __init__(
        self,
        display: Display,
        audio_manager: 'AudioManager',
        context: Optional['AppContext'] = None
    ) -> None:
        """
        Initialize audio screen.

        Args:
            display: Display controller
            audio_manager: Audio manager instance
            context: Application context
        """
        super().__init__(display, context, "Audio")
        self.audio_manager = audio_manager
        self.test_sound_path: Optional[Path] = None

        # Try to find test sound
        test_sounds = Path("assets/sounds")
        if test_sounds.exists():
            for sound_file in test_sounds.glob("*.wav"):
                self.test_sound_path = sound_file
                break
            if not self.test_sound_path:
                for sound_file in test_sounds.glob("*.mp3"):
                    self.test_sound_path = sound_file
                    break

    def render(self) -> None:
        """Render the audio test screen."""
        # Get volume from audio manager
        current_volume = self.audio_manager.volume
        max_volume = self.audio_manager.max_volume
        device_info = self.audio_manager.get_device_info()

        # Clear display
        self.display.clear(self.display.COLOR_BLACK)

        # Draw status bar
        current_time = datetime.now().strftime("%H:%M")
        battery = self.context.battery_percent if self.context else 100
        signal = self.context.signal_strength if self.context else 4

        self.display.status_bar(
            time_str=current_time,
            battery_percent=battery,
            signal_strength=signal
        )

        # Draw title
        title = "Audio Test"
        title_size = 20
        title_width, title_height = self.display.get_text_size(title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2
        title_y = self.display.STATUS_BAR_HEIGHT + 15

        self.display.text(
            title,
            title_x,
            title_y,
            color=self.display.COLOR_CYAN,
            font_size=title_size
        )

        # Draw volume label
        vol_label_y = title_y + title_height + 30
        self.display.text(
            "VOLUME",
            20,
            vol_label_y,
            color=self.display.COLOR_GRAY,
            font_size=14
        )

        # Draw large volume number
        volume_text = f"{current_volume}%"
        volume_size = 48
        vol_width, vol_height = self.display.get_text_size(volume_text, volume_size)
        vol_x = (self.display.WIDTH - vol_width) // 2
        vol_y = vol_label_y + 30

        self.display.text(
            volume_text,
            vol_x,
            vol_y,
            color=self.display.COLOR_WHITE,
            font_size=volume_size
        )

        # Draw volume bar
        bar_y = vol_y + vol_height + 20
        bar_width = self.display.WIDTH - 40
        bar_height = 20
        bar_x = 20

        # Background
        self.display.rectangle(
            bar_x, bar_y,
            bar_x + bar_width, bar_y + bar_height,
            fill=self.display.COLOR_DARK_GRAY,
            outline=self.display.COLOR_GRAY,
            width=2
        )

        # Volume fill
        fill_width = int(bar_width * (current_volume / 100.0))
        if fill_width > 0:
            # Color based on volume level
            if current_volume > 70:
                bar_color = self.display.COLOR_RED
            elif current_volume > 40:
                bar_color = self.display.COLOR_YELLOW
            else:
                bar_color = self.display.COLOR_GREEN

            self.display.rectangle(
                bar_x, bar_y,
                bar_x + fill_width, bar_y + bar_height,
                fill=bar_color
            )

        # Draw max volume indicator if limited
        if max_volume < 100:
            max_x = bar_x + int(bar_width * (max_volume / 100.0))
            self.display.line(
                max_x, bar_y - 5,
                max_x, bar_y + bar_height + 5,
                color=self.display.COLOR_CYAN,
                width=3
            )

            limit_text = f"Limit: {max_volume}%"
            self.display.text(
                limit_text,
                bar_x,
                bar_y + bar_height + 10,
                color=self.display.COLOR_CYAN,
                font_size=12
            )

        # Draw device info
        device_y = self.display.HEIGHT - 60
        if device_info:
            device_text = f"Device: {device_info.name}"
            self.display.text(
                device_text,
                20,
                device_y,
                color=self.display.COLOR_GRAY,
                font_size=12
            )

        # Draw button hints
        hints_y = self.display.HEIGHT - 40
        self.display.text(
            "A: Test Sound  X/Y: Volume  B: Back",
            20,
            hints_y,
            color=self.display.COLOR_GRAY,
            font_size=12
        )

        # Update display
        self.display.update()

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Play test sound."""
        if self.test_sound_path and self.test_sound_path.exists():
            logger.info(f"Playing test sound: {self.test_sound_path.name}")
            if self.audio_manager.load(self.test_sound_path):
                self.audio_manager.play()
        else:
            logger.warning("No test sound available")

    def on_button_b(self) -> None:
        """Button B: Go back."""
        if self.screen_manager:
            self.screen_manager.pop_screen()

    def on_button_x(self) -> None:
        """Button X: Volume up."""
        new_volume = self.audio_manager.volume_up()
        logger.info(f"Volume: {new_volume}%")
        self.render()

    def on_button_y(self) -> None:
        """Button Y: Volume down."""
        new_volume = self.audio_manager.volume_down()
        logger.info(f"Volume: {new_volume}%")
        self.render()

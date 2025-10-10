"""
Screen management for YoyoPod UI.

Provides base Screen class and concrete screen implementations
for different application states.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from loguru import logger

from yoyopy.ui.display import Display


class Screen(ABC):
    """
    Base class for all UI screens.

    Screens are responsible for rendering their content to the display
    and handling any screen-specific logic.
    """

    def __init__(self, display: Display, name: str = "Screen") -> None:
        """
        Initialize the screen.

        Args:
            display: Display controller instance
            name: Screen name for logging
        """
        self.display = display
        self.name = name
        logger.debug(f"Screen '{name}' initialized")

    @abstractmethod
    def render(self) -> None:
        """
        Render the screen content.

        This method should draw all screen elements to the display buffer.
        Call display.update() to show the rendered content.
        """
        pass

    def enter(self) -> None:
        """
        Called when screen becomes active.

        Override to perform screen initialization.
        """
        logger.info(f"Entering screen: {self.name}")

    def exit(self) -> None:
        """
        Called when screen becomes inactive.

        Override to perform cleanup.
        """
        logger.info(f"Exiting screen: {self.name}")


class HomeScreen(Screen):
    """
    Home screen displaying YoyoPod logo and status.

    Shows the main branding and current device status including
    battery, time, and signal strength.
    """

    def __init__(self, display: Display) -> None:
        super().__init__(display, "Home")

    def render(self) -> None:
        """Render the home screen."""
        # Clear display
        self.display.clear(self.display.COLOR_BLACK)

        # Draw status bar
        current_time = datetime.now().strftime("%H:%M")
        self.display.status_bar(
            time_str=current_time,
            battery_percent=85,
            signal_strength=3
        )

        # Draw YoyoPod logo text
        logo_text = "YoyoPod"
        logo_size = 32
        text_width, text_height = self.display.get_text_size(logo_text, logo_size)
        logo_x = (self.display.WIDTH - text_width) // 2
        logo_y = 60

        self.display.text(
            logo_text,
            logo_x,
            logo_y,
            color=self.display.COLOR_CYAN,
            font_size=logo_size
        )

        # Draw subtitle
        subtitle = "Connect"
        subtitle_size = 16
        sub_width, sub_height = self.display.get_text_size(subtitle, subtitle_size)
        sub_x = (self.display.WIDTH - sub_width) // 2
        sub_y = logo_y + text_height + 10

        self.display.text(
            subtitle,
            sub_x,
            sub_y,
            color=self.display.COLOR_WHITE,
            font_size=subtitle_size
        )

        # Draw decorative circle
        circle_y = logo_y + text_height + sub_height + 40
        self.display.circle(
            self.display.WIDTH // 2,
            circle_y,
            30,
            outline=self.display.COLOR_CYAN,
            width=3
        )

        # Draw status text
        status_text = "Ready to Play"
        status_size = 14
        status_width, _ = self.display.get_text_size(status_text, status_size)
        status_x = (self.display.WIDTH - status_width) // 2
        status_y = self.display.HEIGHT - 40

        self.display.text(
            status_text,
            status_x,
            status_y,
            color=self.display.COLOR_GREEN,
            font_size=status_size
        )

        # Update display
        self.display.update()


class MenuScreen(Screen):
    """
    Menu screen for navigation.

    Displays a list of menu options with selection indicator.
    """

    def __init__(
        self,
        display: Display,
        items: Optional[List[str]] = None,
        selected_index: int = 0
    ) -> None:
        """
        Initialize menu screen.

        Args:
            display: Display controller
            items: List of menu items
            selected_index: Currently selected item index
        """
        super().__init__(display, "Menu")

        if items is None:
            items = ["Music", "Podcasts", "Audiobooks", "Settings"]

        self.items = items
        self.selected_index = selected_index

    def render(self) -> None:
        """Render the menu screen."""
        # Clear display
        self.display.clear(self.display.COLOR_BLACK)

        # Draw status bar
        current_time = datetime.now().strftime("%H:%M")
        self.display.status_bar(
            time_str=current_time,
            battery_percent=85,
            signal_strength=3
        )

        # Draw menu title
        title = "Main Menu"
        title_size = 20
        title_width, title_height = self.display.get_text_size(title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2
        title_y = self.display.STATUS_BAR_HEIGHT + 15

        self.display.text(
            title,
            title_x,
            title_y,
            color=self.display.COLOR_WHITE,
            font_size=title_size
        )

        # Draw separator line
        separator_y = title_y + title_height + 10
        self.display.line(
            20, separator_y,
            self.display.WIDTH - 20, separator_y,
            color=self.display.COLOR_GRAY,
            width=2
        )

        # Draw menu items
        item_y_start = separator_y + 20
        item_height = 35
        item_font_size = 16

        for i, item in enumerate(self.items):
            y_pos = item_y_start + (i * item_height)

            # Draw selection indicator
            if i == self.selected_index:
                # Highlight selected item
                self.display.rectangle(
                    10, y_pos - 5,
                    self.display.WIDTH - 10, y_pos + item_height - 10,
                    fill=self.display.COLOR_DARK_GRAY,
                    outline=self.display.COLOR_CYAN,
                    width=2
                )

                # Draw arrow
                self.display.text(
                    ">",
                    20,
                    y_pos,
                    color=self.display.COLOR_CYAN,
                    font_size=item_font_size
                )

            # Draw item text
            text_x = 45 if i == self.selected_index else 30
            text_color = self.display.COLOR_WHITE if i == self.selected_index else self.display.COLOR_GRAY

            self.display.text(
                item,
                text_x,
                y_pos,
                color=text_color,
                font_size=item_font_size
            )

        # Update display
        self.display.update()

    def select_next(self) -> None:
        """Move selection to next item."""
        self.selected_index = (self.selected_index + 1) % len(self.items)
        logger.debug(f"Selected: {self.items[self.selected_index]}")

    def select_previous(self) -> None:
        """Move selection to previous item."""
        self.selected_index = (self.selected_index - 1) % len(self.items)
        logger.debug(f"Selected: {self.items[self.selected_index]}")

    def get_selected(self) -> str:
        """Get currently selected item."""
        return self.items[self.selected_index]


class NowPlayingScreen(Screen):
    """
    Now Playing screen for audio playback.

    Displays current track information, playback controls,
    and progress indicator.
    """

    def __init__(
        self,
        display: Display,
        track_title: str = "Track Title",
        artist: str = "Artist Name",
        progress: float = 0.5
    ) -> None:
        """
        Initialize now playing screen.

        Args:
            display: Display controller
            track_title: Current track title
            artist: Artist name
            progress: Playback progress (0.0 to 1.0)
        """
        super().__init__(display, "NowPlaying")
        self.track_title = track_title
        self.artist = artist
        self.progress = progress
        self.is_playing = True

    def render(self) -> None:
        """Render the now playing screen."""
        # Clear display
        self.display.clear(self.display.COLOR_BLACK)

        # Draw status bar
        current_time = datetime.now().strftime("%H:%M")
        self.display.status_bar(
            time_str=current_time,
            battery_percent=85,
            signal_strength=3
        )

        # Draw "Now Playing" label
        label_y = self.display.STATUS_BAR_HEIGHT + 15
        self.display.text(
            "NOW PLAYING",
            20,
            label_y,
            color=self.display.COLOR_GRAY,
            font_size=12
        )

        # Draw album art placeholder (square)
        art_size = 100
        art_x = (self.display.WIDTH - art_size) // 2
        art_y = label_y + 30

        # Gradient-like effect with multiple rectangles
        for i in range(0, art_size // 2, 20):
            gray_value = 40 + i
            color = (gray_value, gray_value, gray_value)
            self.display.rectangle(
                art_x + i, art_y + i,
                art_x + art_size - i, art_y + art_size - i,
                fill=color
            )

        # Draw music note icon (simple representation)
        note_x = art_x + art_size // 2 - 10
        note_y = art_y + art_size // 2 - 15
        self.display.circle(
            note_x, note_y + 20,
            8,
            fill=self.display.COLOR_CYAN
        )
        self.display.rectangle(
            note_x + 7, note_y,
            note_x + 10, note_y + 20,
            fill=self.display.COLOR_CYAN
        )

        # Draw track title
        title_y = art_y + art_size + 20
        title_size = 18

        # Truncate if too long
        max_title_length = 20
        display_title = self.track_title[:max_title_length]
        if len(self.track_title) > max_title_length:
            display_title += "..."

        title_width, _ = self.display.get_text_size(display_title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2

        self.display.text(
            display_title,
            title_x,
            title_y,
            color=self.display.COLOR_WHITE,
            font_size=title_size
        )

        # Draw artist name
        artist_y = title_y + 25
        artist_size = 14

        max_artist_length = 25
        display_artist = self.artist[:max_artist_length]
        if len(self.artist) > max_artist_length:
            display_artist += "..."

        artist_width, _ = self.display.get_text_size(display_artist, artist_size)
        artist_x = (self.display.WIDTH - artist_width) // 2

        self.display.text(
            display_artist,
            artist_x,
            artist_y,
            color=self.display.COLOR_GRAY,
            font_size=artist_size
        )

        # Draw progress bar
        progress_y = self.display.HEIGHT - 35
        progress_width = self.display.WIDTH - 40
        progress_height = 6
        progress_x = 20

        # Background
        self.display.rectangle(
            progress_x, progress_y,
            progress_x + progress_width, progress_y + progress_height,
            fill=self.display.COLOR_DARK_GRAY
        )

        # Progress
        filled_width = int(progress_width * self.progress)
        if filled_width > 0:
            self.display.rectangle(
                progress_x, progress_y,
                progress_x + filled_width, progress_y + progress_height,
                fill=self.display.COLOR_CYAN
            )

        # Draw play/pause indicator
        control_y = self.display.HEIGHT - 20
        if self.is_playing:
            # Play symbol (simple triangle)
            play_x = self.display.WIDTH // 2 - 5
            self.display.text(
                "▶",
                play_x,
                control_y,
                color=self.display.COLOR_GREEN,
                font_size=12
            )
        else:
            # Pause symbol
            pause_x = self.display.WIDTH // 2 - 5
            self.display.rectangle(
                pause_x, control_y,
                pause_x + 3, control_y + 10,
                fill=self.display.COLOR_YELLOW
            )
            self.display.rectangle(
                pause_x + 7, control_y,
                pause_x + 10, control_y + 10,
                fill=self.display.COLOR_YELLOW
            )

        # Update display
        self.display.update()

    def set_track(self, title: str, artist: str) -> None:
        """Update track information."""
        self.track_title = title
        self.artist = artist
        logger.debug(f"Track updated: {title} - {artist}")

    def set_progress(self, progress: float) -> None:
        """Update playback progress."""
        self.progress = max(0.0, min(1.0, progress))

    def toggle_playback(self) -> None:
        """Toggle play/pause state."""
        self.is_playing = not self.is_playing
        logger.debug(f"Playback: {'playing' if self.is_playing else 'paused'}")

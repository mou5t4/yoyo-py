"""
Screen management for YoyoPod UI.

Provides base Screen class and concrete screen implementations
for different application states.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from loguru import logger

from yoyopy.ui.display import Display

if TYPE_CHECKING:
    from yoyopy.ui.screen_manager import ScreenManager
    from yoyopy.app_context import AppContext


class Screen(ABC):
    """
    Base class for all UI screens.

    Screens are responsible for rendering their content to the display
    and handling any screen-specific logic.
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        name: str = "Screen"
    ) -> None:
        """
        Initialize the screen.

        Args:
            display: Display controller instance
            context: Application context (optional)
            name: Screen name for logging
        """
        self.display = display
        self.context = context
        self.name = name
        self.screen_manager: Optional['ScreenManager'] = None
        logger.debug(f"Screen '{name}' initialized")

    def set_screen_manager(self, manager: 'ScreenManager') -> None:
        """Set the screen manager for navigation."""
        self.screen_manager = manager

    def set_context(self, context: 'AppContext') -> None:
        """Set the application context."""
        self.context = context

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

        Override to perform screen initialization and set up button handlers.
        """
        logger.info(f"Entering screen: {self.name}")

    def exit(self) -> None:
        """
        Called when screen becomes inactive.

        Override to perform cleanup and remove button handlers.
        """
        logger.info(f"Exiting screen: {self.name}")

    def on_button_a(self) -> None:
        """Handle Button A press. Override in subclasses."""
        pass

    def on_button_b(self) -> None:
        """Handle Button B press. Override in subclasses."""
        pass

    def on_button_x(self) -> None:
        """Handle Button X press. Override in subclasses."""
        pass

    def on_button_y(self) -> None:
        """Handle Button Y press. Override in subclasses."""
        pass


class HomeScreen(Screen):
    """
    Home screen displaying YoyoPod logo and status.

    Shows the main branding and current device status including
    battery, time, and signal strength.

    Button mapping:
    - Button A: Open main menu
    """

    def __init__(self, display: Display, context: Optional['AppContext'] = None) -> None:
        super().__init__(display, context, "Home")

    def render(self) -> None:
        """Render the home screen."""
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

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Open main menu."""
        if self.screen_manager:
            self.screen_manager.push_screen("menu")


class MenuScreen(Screen):
    """
    Menu screen for navigation.

    Displays a list of menu options with selection indicator.

    Button mapping:
    - Button A: Select current item
    - Button B: Go back to home screen
    - Button X: Move selection up
    - Button Y: Move selection down
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        items: Optional[List[str]] = None,
        selected_index: int = 0
    ) -> None:
        """
        Initialize menu screen.

        Args:
            display: Display controller
            context: Application context
            items: List of menu items
            selected_index: Currently selected item index
        """
        super().__init__(display, context, "Menu")

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

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Select current item."""
        selected_item = self.get_selected()
        logger.info(f"Menu item selected: {selected_item}")

        # Navigate to appropriate screen based on selection
        if self.screen_manager:
            if selected_item == "Music" or selected_item == "Podcasts" or selected_item == "Audiobooks":
                self.screen_manager.push_screen("now_playing")
            elif selected_item == "Settings":
                logger.info("Settings not implemented yet")

    def on_button_b(self) -> None:
        """Button B: Go back to home screen."""
        if self.screen_manager:
            self.screen_manager.pop_screen()

    def on_button_x(self) -> None:
        """Button X: Move selection up."""
        self.select_previous()
        self.render()

    def on_button_y(self) -> None:
        """Button Y: Move selection down."""
        self.select_next()
        self.render()


class NowPlayingScreen(Screen):
    """
    Now Playing screen for audio playback.

    Displays current track information, playback controls,
    and progress indicator.

    Button mapping:
    - Button A: Toggle play/pause
    - Button B: Go back to menu
    - Button X: Volume up (placeholder)
    - Button Y: Volume down (placeholder)
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None
    ) -> None:
        """
        Initialize now playing screen.

        Args:
            display: Display controller
            context: Application context
        """
        super().__init__(display, context, "NowPlaying")

    def render(self) -> None:
        """Render the now playing screen."""
        # Get track info from context
        track = self.context.get_current_track() if self.context else None
        track_title = track.title if track else "No Track"
        artist = track.artist if track else "Unknown Artist"
        progress = self.context.get_playback_progress() if self.context else 0.0
        is_playing = self.context.playback.is_playing if self.context else False

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
        display_title = track_title[:max_title_length]
        if len(track_title) > max_title_length:
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
        display_artist = artist[:max_artist_length]
        if len(artist) > max_artist_length:
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
        filled_width = int(progress_width * progress)
        if filled_width > 0:
            self.display.rectangle(
                progress_x, progress_y,
                progress_x + filled_width, progress_y + progress_height,
                fill=self.display.COLOR_CYAN
            )

        # Draw play/pause indicator
        control_y = self.display.HEIGHT - 20
        if is_playing:
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

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Toggle play/pause."""
        if self.context:
            self.context.toggle_playback()
        self.render()

    def on_button_b(self) -> None:
        """Button B: Go back to menu."""
        if self.screen_manager:
            self.screen_manager.pop_screen()

    def on_button_x(self) -> None:
        """Button X: Volume up."""
        if self.context:
            new_volume = self.context.volume_up()
            logger.info(f"Volume up: {new_volume}")

    def on_button_y(self) -> None:
        """Button Y: Volume down."""
        if self.context:
            new_volume = self.context.volume_down()
            logger.info(f"Volume down: {new_volume}")

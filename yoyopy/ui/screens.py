"""
Screen management for YoyoPod UI.

Provides base Screen class and concrete screen implementations
for different application states.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import threading
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
            elif selected_item == "Browse Playlists" or selected_item == "Playlists":
                self.screen_manager.push_screen("playlists")
            elif selected_item == "Call Parent" or selected_item == "Call" or selected_item == "Call Contact":
                self.screen_manager.push_screen("contacts")
            elif selected_item == "VoIP Status":
                self.screen_manager.push_screen("call")
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
    - Button X: Previous track
    - Button Y: Next track
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        mopidy_client=None  # Optional MopidyClient for Spotify streaming
    ) -> None:
        """
        Initialize now playing screen.

        Args:
            display: Display controller
            context: Application context
            mopidy_client: Optional MopidyClient for streaming
        """
        super().__init__(display, context, "NowPlaying")
        self.mopidy_client = mopidy_client

    def render(self) -> None:
        """Render the now playing screen."""
        # Get track info from Mopidy or context
        if self.mopidy_client:
            # Get track from Mopidy
            mopidy_track = self.mopidy_client.get_current_track()
            if mopidy_track:
                track_title = mopidy_track.name
                artist = mopidy_track.get_artist_string()
                # Calculate progress from position and track length
                if mopidy_track.length > 0:
                    position_ms = self.mopidy_client.get_time_position()
                    progress = position_ms / mopidy_track.length
                else:
                    progress = 0.0
                is_playing = self.mopidy_client.get_playback_state() == "playing"
            else:
                track_title = "No Track"
                artist = "Unknown Artist"
                progress = 0.0
                is_playing = False
        else:
            # Fallback to context for local tracks
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
        if self.mopidy_client:
            # Use Mopidy for playback control
            state = self.mopidy_client.get_playback_state()
            if state == "playing":
                self.mopidy_client.pause()
            else:
                self.mopidy_client.play()
        elif self.context:
            # Fallback to context for local playback
            self.context.toggle_playback()
        self.render()

    def on_button_b(self) -> None:
        """Button B: Go back to menu."""
        if self.screen_manager:
            self.screen_manager.pop_screen()

    def on_button_x(self) -> None:
        """Button X: Previous track."""
        if self.mopidy_client:
            # Use Mopidy for track navigation
            self.mopidy_client.previous_track()
            self.render()
        elif self.context:
            # Fallback to context for local tracks
            self.context.previous_track()
            self.render()

    def on_button_y(self) -> None:
        """Button Y: Next track."""
        if self.mopidy_client:
            # Use Mopidy for track navigation
            self.mopidy_client.next_track()
            self.render()
        elif self.context:
            # Fallback to context for local tracks
            self.context.next_track()
            self.render()


class PlaylistScreen(Screen):
    """
    Playlist browser screen for Mopidy playlists.

    Displays a scrollable list of playlists with track counts.
    Allows loading and playing selected playlist.

    Button mapping:
    - Button A: Load and play selected playlist
    - Button B: Go back to menu
    - Button X: Move selection up
    - Button Y: Move selection down
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        mopidy_client=None
    ) -> None:
        """
        Initialize playlist browser screen.

        Args:
            display: Display controller
            context: Application context
            mopidy_client: MopidyClient for fetching playlists
        """
        super().__init__(display, context, "PlaylistBrowser")
        self.mopidy_client = mopidy_client
        self.playlists = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 5  # Number of playlists visible at once
        self.loading = False
        self.error_message = None

    def enter(self) -> None:
        """Called when screen becomes active - fetch playlists."""
        super().enter()
        self.fetch_playlists()

    def fetch_playlists(self) -> None:
        """Fetch playlists from Mopidy."""
        if not self.mopidy_client:
            self.error_message = "No Mopidy client"
            logger.error("Cannot fetch playlists: No Mopidy client")
            return

        self.loading = True
        self.render()  # Show loading indicator

        try:
            logger.info("Fetching playlists from Mopidy...")
            self.playlists = self.mopidy_client.get_playlists(fetch_track_counts=True)
            self.error_message = None
            logger.info(f"Fetched {len(self.playlists)} playlists")
        except Exception as e:
            self.error_message = f"Error: {str(e)[:30]}"
            logger.error(f"Failed to fetch playlists: {e}")
        finally:
            self.loading = False
            self.render()

    def render(self) -> None:
        """Render the playlist browser screen."""
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
        title = "Playlists"
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

        content_y = separator_y + 15

        # Show loading indicator
        if self.loading:
            loading_text = "Loading playlists..."
            loading_size = 14
            loading_width, _ = self.display.get_text_size(loading_text, loading_size)
            loading_x = (self.display.WIDTH - loading_width) // 2
            loading_y = self.display.HEIGHT // 2

            self.display.text(
                loading_text,
                loading_x,
                loading_y,
                color=self.display.COLOR_CYAN,
                font_size=loading_size
            )

            # Update display and return
            self.display.update()
            return

        # Show error message
        if self.error_message:
            error_size = 14
            error_width, _ = self.display.get_text_size(self.error_message, error_size)
            error_x = (self.display.WIDTH - error_width) // 2
            error_y = self.display.HEIGHT // 2

            self.display.text(
                self.error_message,
                error_x,
                error_y,
                color=self.display.COLOR_RED,
                font_size=error_size
            )

            # Update display and return
            self.display.update()
            return

        # Show empty message
        if not self.playlists:
            empty_text = "No playlists found"
            empty_size = 14
            empty_width, _ = self.display.get_text_size(empty_text, empty_size)
            empty_x = (self.display.WIDTH - empty_width) // 2
            empty_y = self.display.HEIGHT // 2

            self.display.text(
                empty_text,
                empty_x,
                empty_y,
                color=self.display.COLOR_GRAY,
                font_size=empty_size
            )

            # Update display and return
            self.display.update()
            return

        # Calculate scroll offset to keep selected item visible
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1

        # Draw playlist items
        item_height = 30
        item_font_size = 14
        count_font_size = 12

        for i in range(self.max_visible_items):
            playlist_index = self.scroll_offset + i
            if playlist_index >= len(self.playlists):
                break

            playlist = self.playlists[playlist_index]
            y_pos = content_y + (i * item_height)

            # Draw selection indicator
            if playlist_index == self.selected_index:
                # Highlight selected item
                self.display.rectangle(
                    10, y_pos - 3,
                    self.display.WIDTH - 10, y_pos + item_height - 8,
                    fill=self.display.COLOR_DARK_GRAY,
                    outline=self.display.COLOR_CYAN,
                    width=2
                )

                # Draw arrow
                self.display.text(
                    ">",
                    15,
                    y_pos,
                    color=self.display.COLOR_CYAN,
                    font_size=item_font_size
                )

            # Draw playlist name (truncate if too long)
            max_name_length = 22
            display_name = playlist.name[:max_name_length]
            if len(playlist.name) > max_name_length:
                display_name = display_name[:-3] + "..."

            text_x = 35 if playlist_index == self.selected_index else 20
            text_color = self.display.COLOR_WHITE if playlist_index == self.selected_index else self.display.COLOR_GRAY

            self.display.text(
                display_name,
                text_x,
                y_pos,
                color=text_color,
                font_size=item_font_size
            )

            # Draw track count if available
            if playlist.track_count > 0:
                count_text = f"{playlist.track_count} tracks"
                count_width, _ = self.display.get_text_size(count_text, count_font_size)
                count_x = self.display.WIDTH - count_width - 15

                self.display.text(
                    count_text,
                    count_x,
                    y_pos + 2,
                    color=self.display.COLOR_GRAY,
                    font_size=count_font_size
                )

        # Draw scroll indicator if needed
        if len(self.playlists) > self.max_visible_items:
            indicator_x = self.display.WIDTH - 8
            indicator_height = self.max_visible_items * item_height
            indicator_y_start = content_y

            # Calculate scrollbar size and position
            scrollbar_height = max(10, int(indicator_height * self.max_visible_items / len(self.playlists)))
            scrollbar_y_offset = int((indicator_height - scrollbar_height) * self.scroll_offset / (len(self.playlists) - self.max_visible_items))

            # Draw scrollbar background
            self.display.rectangle(
                indicator_x, indicator_y_start,
                indicator_x + 3, indicator_y_start + indicator_height,
                fill=self.display.COLOR_DARK_GRAY
            )

            # Draw scrollbar
            self.display.rectangle(
                indicator_x, indicator_y_start + scrollbar_y_offset,
                indicator_x + 3, indicator_y_start + scrollbar_y_offset + scrollbar_height,
                fill=self.display.COLOR_CYAN
            )

        # Draw instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 10
        instructions = "A: Load | B: Back | X/Y: Navigate"
        instr_width, _ = self.display.get_text_size(instructions, instructions_size)
        instr_x = (self.display.WIDTH - instr_width) // 2

        self.display.text(
            instructions,
            instr_x,
            instructions_y,
            color=self.display.COLOR_GRAY,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    def select_next(self) -> None:
        """Move selection to next playlist."""
        if self.playlists and self.selected_index < len(self.playlists) - 1:
            self.selected_index += 1
            logger.debug(f"Selected: {self.playlists[self.selected_index].name}")

    def select_previous(self) -> None:
        """Move selection to previous playlist."""
        if self.playlists and self.selected_index > 0:
            self.selected_index -= 1
            logger.debug(f"Selected: {self.playlists[self.selected_index].name}")

    def load_selected_playlist(self) -> None:
        """Load and play the selected playlist."""
        if not self.playlists or self.selected_index >= len(self.playlists):
            logger.warning("No playlist selected")
            return

        if not self.mopidy_client:
            logger.error("Cannot load playlist: No Mopidy client")
            return

        playlist = self.playlists[self.selected_index]
        logger.info(f"Loading playlist: {playlist.name}")

        # Show loading message
        self.display.clear(self.display.COLOR_BLACK)
        loading_text = f"Loading {playlist.name[:15]}..."
        loading_size = 14
        loading_width, _ = self.display.get_text_size(loading_text, loading_size)
        loading_x = (self.display.WIDTH - loading_width) // 2
        loading_y = self.display.HEIGHT // 2

        self.display.text(
            loading_text,
            loading_x,
            loading_y,
            color=self.display.COLOR_CYAN,
            font_size=loading_size
        )
        self.display.update()

        # Load playlist
        try:
            if self.mopidy_client.load_playlist(playlist.uri):
                logger.info(f"Successfully loaded playlist: {playlist.name}")
                # Navigate to now playing screen
                if self.screen_manager:
                    self.screen_manager.push_screen("now_playing")
            else:
                logger.error(f"Failed to load playlist: {playlist.name}")
                self.error_message = "Failed to load"
                self.render()
        except Exception as e:
            logger.error(f"Error loading playlist: {e}")
            self.error_message = f"Error: {str(e)[:20]}"
            self.render()

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Load and play selected playlist."""
        self.load_selected_playlist()

    def on_button_b(self) -> None:
        """Button B: Go back to menu."""
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


class CallScreen(Screen):
    """
    VoIP call screen showing registration and call status.

    Displays VoIP registration status and allows making/receiving calls.

    Button mapping:
    - Button A: (Reserved for answer/hangup)
    - Button B: Back to menu
    - Button X: (Reserved for dial pad)
    - Button Y: (Reserved for dial pad)
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        voip_manager=None,
        config_manager=None
    ) -> None:
        """
        Initialize call screen.

        Args:
            display: Display controller
            context: Application context
            voip_manager: VoIPManager instance
            config_manager: ConfigManager instance for contacts
        """
        super().__init__(display, context, "Call")
        self.voip_manager = voip_manager
        self.config_manager = config_manager

    def render(self) -> None:
        """Render the call screen."""
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
        title = "VoIP Call"
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

        content_y = separator_y + 20

        # Get VoIP status
        if self.voip_manager:
            status = self.voip_manager.get_status()
            registered = status.get("registered", False)
            reg_state = status.get("registration_state", "none")
            call_state = status.get("call_state", "idle")
            sip_identity = status.get("sip_identity", "")

            # Draw registration status
            if registered:
                status_text = "VoIP Ready"
                status_color = self.display.COLOR_GREEN
            elif reg_state == "progress":
                status_text = "Connecting..."
                status_color = self.display.COLOR_YELLOW
            elif reg_state == "failed":
                status_text = "Registration Failed"
                status_color = self.display.COLOR_RED
            else:
                status_text = "VoIP Disconnected"
                status_color = self.display.COLOR_GRAY

            # Draw status with icon
            status_size = 18
            status_width, _ = self.display.get_text_size(status_text, status_size)
            status_x = (self.display.WIDTH - status_width) // 2
            status_y = content_y + 30

            self.display.text(
                status_text,
                status_x,
                status_y,
                color=status_color,
                font_size=status_size
            )

            # Draw SIP identity
            if sip_identity:
                identity_size = 12
                # Truncate long identity
                max_len = 30
                display_identity = sip_identity[:max_len]
                if len(sip_identity) > max_len:
                    display_identity = display_identity[:-3] + "..."

                identity_width, _ = self.display.get_text_size(display_identity, identity_size)
                identity_x = (self.display.WIDTH - identity_width) // 2
                identity_y = status_y + 30

                self.display.text(
                    display_identity,
                    identity_x,
                    identity_y,
                    color=self.display.COLOR_GRAY,
                    font_size=identity_size
                )

            # Draw call state if not idle
            if call_state != "idle":
                call_text = f"Call: {call_state}"
                call_size = 14
                call_width, _ = self.display.get_text_size(call_text, call_size)
                call_x = (self.display.WIDTH - call_width) // 2
                call_y = self.display.HEIGHT // 2 + 20

                self.display.text(
                    call_text,
                    call_x,
                    call_y,
                    color=self.display.COLOR_CYAN,
                    font_size=call_size
                )

        else:
            # No VoIP manager
            error_text = "VoIP Not Available"
            error_size = 16
            error_width, _ = self.display.get_text_size(error_text, error_size)
            error_x = (self.display.WIDTH - error_width) // 2
            error_y = self.display.HEIGHT // 2

            self.display.text(
                error_text,
                error_x,
                error_y,
                color=self.display.COLOR_RED,
                font_size=error_size
            )

        # Draw instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 10
        instructions = "B: Back"
        instr_width, _ = self.display.get_text_size(instructions, instructions_size)
        instr_x = (self.display.WIDTH - instr_width) // 2

        self.display.text(
            instructions,
            instr_x,
            instructions_y,
            color=self.display.COLOR_GRAY,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Reserved for answer/hangup."""
        # TODO: Implement call answer/hangup
        pass

    def on_button_b(self) -> None:
        """Button B: Go back to menu."""
        if self.screen_manager:
            self.screen_manager.pop_screen()

    def on_button_x(self) -> None:
        """Button X: Reserved for dial pad."""
        # TODO: Implement dial pad
        pass

    def on_button_y(self) -> None:
        """Button Y: Reserved for dial pad."""
        # TODO: Implement dial pad
        pass


class IncomingCallScreen(Screen):
    """
    Incoming call screen showing caller information.

    Displays incoming call with caller name/address and answer/reject options.

    Button mapping:
    - Button A: Answer call
    - Button B: Reject call
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        voip_manager=None,
        caller_address: str = "",
        caller_name: str = "Unknown"
    ) -> None:
        """
        Initialize incoming call screen.

        Args:
            display: Display controller
            context: Application context
            voip_manager: VoIPManager instance
            caller_address: SIP address of caller
            caller_name: Display name of caller
        """
        super().__init__(display, context, "IncomingCall")
        self.voip_manager = voip_manager
        self.caller_address = caller_address
        self.caller_name = caller_name
        self.ring_animation_frame = 0

    def render(self) -> None:
        """Render the incoming call screen."""
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

        # Draw "Incoming Call" title
        title = "Incoming Call"
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

        # Draw separator line
        separator_y = title_y + title_height + 10
        self.display.line(
            20, separator_y,
            self.display.WIDTH - 20, separator_y,
            color=self.display.COLOR_GRAY,
            width=2
        )

        content_y = separator_y + 30

        # Draw caller icon (phone with ringing animation)
        icon_x = self.display.WIDTH // 2
        icon_y = content_y + 20
        icon_radius = 25

        # Animate ring (pulsing circle)
        ring_color = self.display.COLOR_GREEN if self.ring_animation_frame % 2 == 0 else self.display.COLOR_CYAN
        self.display.circle(
            icon_x,
            icon_y,
            icon_radius,
            outline=ring_color,
            width=3
        )

        # Inner phone icon
        self.display.text(
            "☎",
            icon_x - 10,
            icon_y - 10,
            color=self.display.COLOR_WHITE,
            font_size=20
        )

        # Update animation frame for next render
        self.ring_animation_frame += 1

        # Draw caller name
        name_y = icon_y + icon_radius + 30
        name_size = 18

        # Truncate if too long
        max_name_length = 20
        display_name = self.caller_name[:max_name_length]
        if len(self.caller_name) > max_name_length:
            display_name = display_name[:-3] + "..."

        name_width, _ = self.display.get_text_size(display_name, name_size)
        name_x = (self.display.WIDTH - name_width) // 2

        self.display.text(
            display_name,
            name_x,
            name_y,
            color=self.display.COLOR_WHITE,
            font_size=name_size
        )

        # Draw caller address (smaller, below name)
        if self.caller_address:
            address_y = name_y + 25
            address_size = 12

            # Truncate long address
            max_addr_length = 30
            display_addr = self.caller_address[:max_addr_length]
            if len(self.caller_address) > max_addr_length:
                display_addr = display_addr[:-3] + "..."

            addr_width, _ = self.display.get_text_size(display_addr, address_size)
            addr_x = (self.display.WIDTH - addr_width) // 2

            self.display.text(
                display_addr,
                addr_x,
                address_y,
                color=self.display.COLOR_GRAY,
                font_size=address_size
            )

        # Draw button instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 12

        # Answer button (A)
        answer_text = "A: Answer"
        answer_width, _ = self.display.get_text_size(answer_text, instructions_size)
        answer_x = 20

        self.display.text(
            answer_text,
            answer_x,
            instructions_y,
            color=self.display.COLOR_GREEN,
            font_size=instructions_size
        )

        # Reject button (B)
        reject_text = "B: Reject"
        reject_width, _ = self.display.get_text_size(reject_text, instructions_size)
        reject_x = self.display.WIDTH - reject_width - 20

        self.display.text(
            reject_text,
            reject_x,
            instructions_y,
            color=self.display.COLOR_RED,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Answer call."""
        logger.info("Answering incoming call")
        if self.voip_manager:
            if self.voip_manager.answer_call():
                logger.info("Call answered, transitioning to InCall screen")
                # Navigate to in-call screen
                if self.screen_manager:
                    self.screen_manager.push_screen("in_call")
            else:
                logger.error("Failed to answer call")

    def on_button_b(self) -> None:
        """Button B: Reject call."""
        logger.info("Rejecting incoming call")
        if self.voip_manager:
            if self.voip_manager.reject_call():
                logger.info("Call rejected, going back")
                # Go back to previous screen
                if self.screen_manager:
                    self.screen_manager.pop_screen()
            else:
                logger.error("Failed to reject call")


class OutgoingCallScreen(Screen):
    """
    Outgoing call screen showing callee information.

    Displays outgoing call with callee name/address and cancel option.

    Button mapping:
    - Button B: Cancel call
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        voip_manager=None,
        callee_address: str = "",
        callee_name: str = "Unknown"
    ) -> None:
        """
        Initialize outgoing call screen.

        Args:
            display: Display controller
            context: Application context
            voip_manager: VoIPManager instance
            callee_address: SIP address of callee
            callee_name: Display name of callee
        """
        super().__init__(display, context, "OutgoingCall")
        self.voip_manager = voip_manager
        self.callee_address = callee_address
        self.callee_name = callee_name
        self.ring_animation_frame = 0

    def render(self) -> None:
        """Render the outgoing call screen."""
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

        # Draw "Calling..." title
        title = "Calling..."
        title_size = 20
        title_width, title_height = self.display.get_text_size(title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2
        title_y = self.display.STATUS_BAR_HEIGHT + 15

        self.display.text(
            title,
            title_x,
            title_y,
            color=self.display.COLOR_YELLOW,
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

        content_y = separator_y + 30

        # Draw calling icon (phone with outgoing animation)
        icon_x = self.display.WIDTH // 2
        icon_y = content_y + 20
        icon_radius = 25

        # Animate outgoing call (pulsing circle)
        ring_color = self.display.COLOR_YELLOW if self.ring_animation_frame % 2 == 0 else self.display.COLOR_CYAN
        self.display.circle(
            icon_x,
            icon_y,
            icon_radius,
            outline=ring_color,
            width=3
        )

        # Inner phone icon with arrow
        self.display.text(
            "☎",
            icon_x - 10,
            icon_y - 10,
            color=self.display.COLOR_WHITE,
            font_size=20
        )

        # Outgoing arrow
        self.display.text(
            "→",
            icon_x + 15,
            icon_y - 5,
            color=self.display.COLOR_YELLOW,
            font_size=16
        )

        # Update animation frame for next render
        self.ring_animation_frame += 1

        # Get caller info dynamically from VoIPManager
        callee_name = self.callee_name
        callee_address = self.callee_address

        if self.voip_manager:
            caller_info = self.voip_manager.get_caller_info()
            # Use caller info from VoIPManager if available
            if caller_info.get("display_name") != "Unknown":
                callee_name = caller_info.get("display_name", "Unknown")
            if caller_info.get("address"):
                callee_address = caller_info.get("address", "")

        # Draw callee name
        name_y = icon_y + icon_radius + 30
        name_size = 18

        # Truncate if too long
        max_name_length = 20
        display_name = callee_name[:max_name_length]
        if len(callee_name) > max_name_length:
            display_name = display_name[:-3] + "..."

        name_width, _ = self.display.get_text_size(display_name, name_size)
        name_x = (self.display.WIDTH - name_width) // 2

        self.display.text(
            display_name,
            name_x,
            name_y,
            color=self.display.COLOR_WHITE,
            font_size=name_size
        )

        # Draw callee address (smaller, below name)
        if callee_address:
            address_y = name_y + 25
            address_size = 12

            # Truncate long address
            max_addr_length = 30
            display_addr = callee_address[:max_addr_length]
            if len(callee_address) > max_addr_length:
                display_addr = display_addr[:-3] + "..."

            addr_width, _ = self.display.get_text_size(display_addr, address_size)
            addr_x = (self.display.WIDTH - addr_width) // 2

            self.display.text(
                display_addr,
                addr_x,
                address_y,
                color=self.display.COLOR_GRAY,
                font_size=address_size
            )

        # Draw status text
        status_y = self.display.HEIGHT - 40
        status_text = "Connecting..."
        status_size = 14
        status_width, _ = self.display.get_text_size(status_text, status_size)
        status_x = (self.display.WIDTH - status_width) // 2

        self.display.text(
            status_text,
            status_x,
            status_y,
            color=self.display.COLOR_GRAY,
            font_size=status_size
        )

        # Draw button instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 12

        # Cancel button (B)
        cancel_text = "B: Cancel"
        cancel_width, _ = self.display.get_text_size(cancel_text, instructions_size)
        cancel_x = (self.display.WIDTH - cancel_width) // 2

        self.display.text(
            cancel_text,
            cancel_x,
            instructions_y,
            color=self.display.COLOR_RED,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    # Button handlers
    def on_button_b(self) -> None:
        """Button B: Cancel call."""
        logger.info("Canceling outgoing call")
        if self.voip_manager:
            if self.voip_manager.hangup():
                logger.info("Call canceled, going back")
                # Go back to previous screen
                if self.screen_manager:
                    self.screen_manager.pop_screen()
            else:
                logger.error("Failed to cancel call")


class InCallScreen(Screen):
    """
    In-call screen showing active call information.

    Displays call duration, mute status, and call controls.

    Button mapping:
    - Button B: End call
    - Button X: Toggle mute
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        voip_manager=None
    ) -> None:
        """
        Initialize in-call screen.

        Args:
            display: Display controller
            context: Application context
            voip_manager: VoIPManager instance
        """
        super().__init__(display, context, "InCall")
        self.voip_manager = voip_manager
        self.refresh_thread = None
        self.refresh_stop_event = None

    def format_duration(self, seconds: int) -> str:
        """
        Format call duration as MM:SS.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def render(self) -> None:
        """Render the in-call screen."""
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

        # Get call info
        caller_info = {"display_name": "Unknown", "address": ""}
        duration = 0
        is_muted = False

        if self.voip_manager:
            caller_info = self.voip_manager.get_caller_info()
            duration = self.voip_manager.get_call_duration()
            is_muted = self.voip_manager.is_muted

        # Draw "Call Active" title
        title = "Call Active"
        title_size = 20
        title_width, title_height = self.display.get_text_size(title, title_size)
        title_x = (self.display.WIDTH - title_width) // 2
        title_y = self.display.STATUS_BAR_HEIGHT + 15

        self.display.text(
            title,
            title_x,
            title_y,
            color=self.display.COLOR_GREEN,
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

        content_y = separator_y + 20

        # Draw call icon
        icon_x = self.display.WIDTH // 2
        icon_y = content_y + 20
        icon_radius = 25

        # Active call indicator (solid circle)
        self.display.circle(
            icon_x,
            icon_y,
            icon_radius,
            fill=self.display.COLOR_GREEN,
            outline=self.display.COLOR_WHITE,
            width=2
        )

        # Phone icon
        self.display.text(
            "☎",
            icon_x - 10,
            icon_y - 10,
            color=self.display.COLOR_WHITE,
            font_size=20
        )

        # Draw caller/callee name
        name_y = icon_y + icon_radius + 25
        name_size = 18

        caller_name = caller_info.get("display_name", "Unknown")

        # Truncate if too long
        max_name_length = 20
        display_name = caller_name[:max_name_length]
        if len(caller_name) > max_name_length:
            display_name = display_name[:-3] + "..."

        name_width, _ = self.display.get_text_size(display_name, name_size)
        name_x = (self.display.WIDTH - name_width) // 2

        self.display.text(
            display_name,
            name_x,
            name_y,
            color=self.display.COLOR_WHITE,
            font_size=name_size
        )

        # Draw call duration
        duration_y = name_y + 30
        duration_text = self.format_duration(duration)
        duration_size = 24
        duration_width, _ = self.display.get_text_size(duration_text, duration_size)
        duration_x = (self.display.WIDTH - duration_width) // 2

        self.display.text(
            duration_text,
            duration_x,
            duration_y,
            color=self.display.COLOR_CYAN,
            font_size=duration_size
        )

        # Draw mute indicator if muted
        if is_muted:
            mute_y = duration_y + 35
            mute_text = "🔇 MUTED"
            mute_size = 14
            mute_width, _ = self.display.get_text_size(mute_text, mute_size)
            mute_x = (self.display.WIDTH - mute_width) // 2

            self.display.text(
                mute_text,
                mute_x,
                mute_y,
                color=self.display.COLOR_YELLOW,
                font_size=mute_size
            )

        # Draw button instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 12

        # Mute button (X)
        mute_text = f"X: {'Unmute' if is_muted else 'Mute'}"
        mute_width, _ = self.display.get_text_size(mute_text, instructions_size)
        mute_x = 20

        self.display.text(
            mute_text,
            mute_x,
            instructions_y,
            color=self.display.COLOR_YELLOW,
            font_size=instructions_size
        )

        # End call button (B)
        end_text = "B: End Call"
        end_width, _ = self.display.get_text_size(end_text, instructions_size)
        end_x = self.display.WIDTH - end_width - 20

        self.display.text(
            end_text,
            end_x,
            instructions_y,
            color=self.display.COLOR_RED,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    # Button handlers
    def on_button_b(self) -> None:
        """Button B: End call."""
        logger.info("Ending call")
        if self.voip_manager:
            if self.voip_manager.hangup():
                logger.info("Call ended, going back")
                # Go back to previous screen
                if self.screen_manager:
                    self.screen_manager.pop_screen()
            else:
                logger.error("Failed to end call")

    def on_button_x(self) -> None:
        """Button X: Toggle mute."""
        logger.info("Toggling mute")
        if self.voip_manager:
            is_muted = self.voip_manager.toggle_mute()
            logger.info(f"Mute toggled: {'muted' if is_muted else 'unmuted'}")
            # Re-render to show mute status
            self.render()

    def enter(self) -> None:
        """Called when screen becomes active - start auto-refresh thread."""
        super().enter()
        # Start refresh thread for live duration updates
        self.refresh_stop_event = threading.Event()
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop,
            daemon=True
        )
        self.refresh_thread.start()
        logger.debug("InCallScreen auto-refresh thread started")

    def exit(self) -> None:
        """Called when screen becomes inactive - stop auto-refresh thread."""
        super().exit()
        # Stop refresh thread
        if self.refresh_stop_event:
            self.refresh_stop_event.set()
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1)
            self.refresh_thread = None
        self.refresh_stop_event = None
        logger.debug("InCallScreen auto-refresh thread stopped")

    def _refresh_loop(self) -> None:
        """Background thread to refresh display every second."""
        while not self.refresh_stop_event.is_set():
            try:
                self.render()
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
            # Wait 1 second before next refresh
            self.refresh_stop_event.wait(1.0)


class ContactListScreen(Screen):
    """
    Contact list screen for selecting a contact to call.

    Displays a scrollable list of contacts with favorite indicators.

    Button mapping:
    - Button A: Call selected contact
    - Button B: Go back
    - Button X: Move selection up
    - Button Y: Move selection down
    """

    def __init__(
        self,
        display: Display,
        context: Optional['AppContext'] = None,
        voip_manager=None,
        config_manager=None
    ) -> None:
        """
        Initialize contact list screen.

        Args:
            display: Display controller
            context: Application context
            voip_manager: VoIPManager instance
            config_manager: ConfigManager instance for loading contacts
        """
        super().__init__(display, context, "ContactList")
        self.voip_manager = voip_manager
        self.config_manager = config_manager
        self.contacts = []
        self.selected_index = 0
        self.scroll_offset = 0
        self.max_visible_items = 5  # Number of contacts visible at once

    def enter(self) -> None:
        """Called when screen becomes active - load contacts."""
        super().enter()
        self.load_contacts()

    def load_contacts(self) -> None:
        """Load contacts from config manager."""
        if self.config_manager:
            self.contacts = self.config_manager.get_contacts()
            # Sort by favorites first, then by name
            self.contacts.sort(key=lambda c: (not c.favorite, c.name.lower()))
            logger.info(f"Loaded {len(self.contacts)} contacts")
        else:
            logger.warning("No config manager available to load contacts")
            self.contacts = []

    def render(self) -> None:
        """Render the contact list screen."""
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
        title = "Call Contact"
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

        content_y = separator_y + 15

        # Show empty message if no contacts
        if not self.contacts:
            empty_text = "No contacts found"
            empty_size = 14
            empty_width, _ = self.display.get_text_size(empty_text, empty_size)
            empty_x = (self.display.WIDTH - empty_width) // 2
            empty_y = self.display.HEIGHT // 2

            self.display.text(
                empty_text,
                empty_x,
                empty_y,
                color=self.display.COLOR_GRAY,
                font_size=empty_size
            )

            # Update display and return
            self.display.update()
            return

        # Calculate scroll offset to keep selected item visible
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + self.max_visible_items:
            self.scroll_offset = self.selected_index - self.max_visible_items + 1

        # Draw contact items
        item_height = 30
        item_font_size = 14

        for i in range(self.max_visible_items):
            contact_index = self.scroll_offset + i
            if contact_index >= len(self.contacts):
                break

            contact = self.contacts[contact_index]
            y_pos = content_y + (i * item_height)

            # Draw selection indicator
            if contact_index == self.selected_index:
                # Highlight selected item
                self.display.rectangle(
                    10, y_pos - 3,
                    self.display.WIDTH - 10, y_pos + item_height - 8,
                    fill=self.display.COLOR_DARK_GRAY,
                    outline=self.display.COLOR_CYAN,
                    width=2
                )

                # Draw arrow
                self.display.text(
                    ">",
                    15,
                    y_pos,
                    color=self.display.COLOR_CYAN,
                    font_size=item_font_size
                )

            # Draw favorite indicator
            text_x = 35 if contact_index == self.selected_index else 20
            if contact.favorite:
                self.display.text(
                    "★",
                    text_x,
                    y_pos,
                    color=self.display.COLOR_YELLOW,
                    font_size=item_font_size
                )
                text_x += 20

            # Draw contact name (truncate if too long)
            max_name_length = 18
            display_name = contact.name[:max_name_length]
            if len(contact.name) > max_name_length:
                display_name = display_name[:-3] + "..."

            text_color = self.display.COLOR_WHITE if contact_index == self.selected_index else self.display.COLOR_GRAY

            self.display.text(
                display_name,
                text_x,
                y_pos,
                color=text_color,
                font_size=item_font_size
            )

        # Draw scroll indicator if needed
        if len(self.contacts) > self.max_visible_items:
            indicator_x = self.display.WIDTH - 8
            indicator_height = self.max_visible_items * item_height
            indicator_y_start = content_y

            # Calculate scrollbar size and position
            scrollbar_height = max(10, int(indicator_height * self.max_visible_items / len(self.contacts)))
            scrollbar_y_offset = int((indicator_height - scrollbar_height) * self.scroll_offset / (len(self.contacts) - self.max_visible_items))

            # Draw scrollbar background
            self.display.rectangle(
                indicator_x, indicator_y_start,
                indicator_x + 3, indicator_y_start + indicator_height,
                fill=self.display.COLOR_DARK_GRAY
            )

            # Draw scrollbar
            self.display.rectangle(
                indicator_x, indicator_y_start + scrollbar_y_offset,
                indicator_x + 3, indicator_y_start + scrollbar_y_offset + scrollbar_height,
                fill=self.display.COLOR_CYAN
            )

        # Draw instructions at bottom
        instructions_y = self.display.HEIGHT - 15
        instructions_size = 10
        instructions = "A: Call | B: Back | X/Y: Navigate"
        instr_width, _ = self.display.get_text_size(instructions, instructions_size)
        instr_x = (self.display.WIDTH - instr_width) // 2

        self.display.text(
            instructions,
            instr_x,
            instructions_y,
            color=self.display.COLOR_GRAY,
            font_size=instructions_size
        )

        # Update display
        self.display.update()

    def select_next(self) -> None:
        """Move selection to next contact."""
        if self.contacts and self.selected_index < len(self.contacts) - 1:
            self.selected_index += 1
            logger.debug(f"Selected: {self.contacts[self.selected_index].name}")

    def select_previous(self) -> None:
        """Move selection to previous contact."""
        if self.contacts and self.selected_index > 0:
            self.selected_index -= 1
            logger.debug(f"Selected: {self.contacts[self.selected_index].name}")

    def call_selected_contact(self) -> None:
        """Initiate call to selected contact."""
        if not self.contacts or self.selected_index >= len(self.contacts):
            logger.warning("No contact selected")
            return

        if not self.voip_manager:
            logger.error("Cannot make call: No VoIP manager")
            return

        contact = self.contacts[self.selected_index]
        logger.info(f"Calling contact: {contact.name} at {contact.sip_address}")

        # Make the call with contact name
        if self.voip_manager.make_call(contact.sip_address, contact_name=contact.name):
            logger.info(f"Call initiated to {contact.name}")
            # Navigate to outgoing call screen
            if self.screen_manager:
                self.screen_manager.push_screen("outgoing_call")
        else:
            logger.error(f"Failed to initiate call to {contact.name}")

    # Button handlers
    def on_button_a(self) -> None:
        """Button A: Call selected contact."""
        self.call_selected_contact()

    def on_button_b(self) -> None:
        """Button B: Go back."""
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

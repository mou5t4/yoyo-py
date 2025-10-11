"""
Mopidy client for YoyoPod.

Provides interface to Mopidy music server for Spotify streaming
and playlist management via HTTP JSON-RPC API.
"""

import requests
import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from threading import Thread, Event
from loguru import logger


@dataclass
class MopidyTrack:
    """Represents a Mopidy track."""
    uri: str
    name: str
    artists: List[str]
    album: str = ""
    length: int = 0  # Duration in milliseconds
    track_no: Optional[int] = None

    @classmethod
    def from_mopidy(cls, track_data: Dict[str, Any]) -> 'MopidyTrack':
        """
        Create MopidyTrack from Mopidy API response.

        Args:
            track_data: Track data from Mopidy API

        Returns:
            MopidyTrack instance
        """
        artists = [artist.get('name', 'Unknown') for artist in track_data.get('artists', [])]
        album = track_data.get('album', {}).get('name', '')

        return cls(
            uri=track_data.get('uri', ''),
            name=track_data.get('name', 'Unknown Track'),
            artists=artists,
            album=album,
            length=track_data.get('length', 0),
            track_no=track_data.get('track_no')
        )

    def get_artist_string(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(self.artists) if self.artists else "Unknown Artist"


@dataclass
class MopidyPlaylist:
    """Represents a Mopidy playlist."""
    uri: str
    name: str
    track_count: int = 0


class MopidyClient:
    """
    Client for Mopidy HTTP JSON-RPC API.

    Provides playback control, track navigation, and playlist management
    for Mopidy music server.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6680,
        timeout: int = 5
    ) -> None:
        """
        Initialize Mopidy client.

        Args:
            host: Mopidy server host (default: localhost)
            port: Mopidy HTTP port (default: 6680)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}/mopidy/rpc"

        # Track change callbacks
        self.track_change_callbacks: List[Callable[[Optional[MopidyTrack]], None]] = []

        # State tracking
        self.current_track: Optional[MopidyTrack] = None
        self.is_connected = False

        # Polling thread for track changes
        self.poll_thread: Optional[Thread] = None
        self.poll_event = Event()
        self.polling = False

        logger.info(f"MopidyClient initialized ({host}:{port})")

    def _rpc_call(self, method: str, params: Optional[Dict] = None) -> Any:
        """
        Make JSON-RPC call to Mopidy.

        Args:
            method: RPC method name (e.g., "core.playback.play")
            params: Optional parameters dict

        Returns:
            Response data

        Raises:
            requests.RequestException: On connection/request error
        """
        if params is None:
            params = {}

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                error = result["error"]
                logger.error(f"Mopidy RPC error: {error.get('message', 'Unknown error')}")
                return None

            return result.get("result")

        except requests.exceptions.ConnectionError:
            if self.is_connected:
                logger.error("Lost connection to Mopidy")
                self.is_connected = False
            raise
        except requests.exceptions.Timeout:
            logger.warning(f"Mopidy request timeout ({method})")
            raise
        except Exception as e:
            logger.error(f"Mopidy RPC error: {e}")
            raise

    def connect(self) -> bool:
        """
        Test connection to Mopidy.

        Returns:
            True if connected, False otherwise
        """
        try:
            # Test connection with a simple call
            version = self._rpc_call("core.get_version")
            if version:
                self.is_connected = True
                logger.info(f"Connected to Mopidy {version}")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to Mopidy: {e}")
            self.is_connected = False

        return False

    def play(self) -> bool:
        """
        Start playback.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._rpc_call("core.playback.play")
            logger.info("Playback started")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to play: {e}")
            return False

    def pause(self) -> bool:
        """
        Pause playback.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._rpc_call("core.playback.pause")
            logger.info("Playback paused")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to pause: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop playback.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._rpc_call("core.playback.stop")
            logger.info("Playback stopped")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to stop: {e}")
            return False

    def next_track(self) -> bool:
        """
        Skip to next track.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._rpc_call("core.playback.next")
            logger.info("Skipped to next track")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to skip track: {e}")
            return False

    def previous_track(self) -> bool:
        """
        Go to previous track.

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._rpc_call("core.playback.previous")
            logger.info("Went to previous track")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to go to previous track: {e}")
            return False

    def set_volume(self, volume: int) -> bool:
        """
        Set playback volume.

        Args:
            volume: Volume level (0-100)

        Returns:
            True if successful, False otherwise
        """
        volume = max(0, min(100, volume))

        try:
            result = self._rpc_call("core.mixer.set_volume", {"volume": volume})
            logger.debug(f"Volume set to {volume}%")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    def get_volume(self) -> Optional[int]:
        """
        Get current volume.

        Returns:
            Volume level (0-100) or None on error
        """
        try:
            volume = self._rpc_call("core.mixer.get_volume")
            return volume
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return None

    def get_current_track(self) -> Optional[MopidyTrack]:
        """
        Get currently playing track.

        Returns:
            MopidyTrack or None if no track playing
        """
        try:
            tl_track = self._rpc_call("core.playback.get_current_tl_track")

            if tl_track and "track" in tl_track:
                track = MopidyTrack.from_mopidy(tl_track["track"])
                return track

            return None
        except Exception as e:
            logger.error(f"Failed to get current track: {e}")
            return None

    def get_playback_state(self) -> str:
        """
        Get current playback state.

        Returns:
            State string: "playing", "paused", "stopped"
        """
        try:
            state = self._rpc_call("core.playback.get_state")
            return state if state else "stopped"
        except Exception as e:
            logger.error(f"Failed to get playback state: {e}")
            return "stopped"

    def get_time_position(self) -> int:
        """
        Get current playback position in milliseconds.

        Returns:
            Position in milliseconds, 0 on error
        """
        try:
            pos = self._rpc_call("core.playback.get_time_position")
            return pos if pos is not None else 0
        except Exception as e:
            logger.error(f"Failed to get time position: {e}")
            return 0

    def get_playlists(self) -> List[MopidyPlaylist]:
        """
        Get available playlists.

        Returns:
            List of MopidyPlaylist objects
        """
        try:
            playlists_data = self._rpc_call("core.playlists.as_list")

            if not playlists_data:
                return []

            playlists = []
            for pl_data in playlists_data:
                playlist = MopidyPlaylist(
                    uri=pl_data.get("uri", ""),
                    name=pl_data.get("name", "Unknown Playlist")
                )
                playlists.append(playlist)

            logger.debug(f"Found {len(playlists)} playlists")
            return playlists

        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []

    def load_playlist(self, playlist_uri: str) -> bool:
        """
        Load and play a playlist.

        Args:
            playlist_uri: Mopidy playlist URI

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear current tracklist
            self._rpc_call("core.tracklist.clear")

            # Get playlist tracks
            playlist = self._rpc_call("core.playlists.lookup", {"uri": playlist_uri})

            if playlist and "tracks" in playlist:
                track_uris = [track["uri"] for track in playlist["tracks"]]

                # Add tracks to tracklist
                self._rpc_call("core.tracklist.add", {"uris": track_uris})

                # Start playback
                self.play()

                logger.info(f"Loaded playlist: {playlist.get('name', 'Unknown')}")
                return True
            else:
                logger.warning(f"Playlist not found: {playlist_uri}")
                return False

        except Exception as e:
            logger.error(f"Failed to load playlist: {e}")
            return False

    def on_track_change(self, callback: Callable[[Optional[MopidyTrack]], None]) -> None:
        """
        Register callback for track changes.

        Args:
            callback: Function to call when track changes
        """
        self.track_change_callbacks.append(callback)
        logger.debug("Registered track change callback")

    def _poll_track_changes(self) -> None:
        """Poll for track changes (runs in background thread)."""
        logger.debug("Track change polling started")

        while self.polling and not self.poll_event.is_set():
            try:
                track = self.get_current_track()

                # Check if track changed
                if track != self.current_track:
                    old_track = self.current_track
                    self.current_track = track

                    # Fire callbacks
                    for callback in self.track_change_callbacks:
                        try:
                            callback(track)
                        except Exception as e:
                            logger.error(f"Error in track change callback: {e}")

                    if track:
                        logger.info(f"Track changed: {track.name} - {track.get_artist_string()}")

            except Exception as e:
                logger.error(f"Error polling track changes: {e}")

            # Poll every 2 seconds
            self.poll_event.wait(2.0)

        logger.debug("Track change polling stopped")

    def start_polling(self) -> None:
        """Start polling for track changes."""
        if self.polling:
            logger.warning("Polling already started")
            return

        self.polling = True
        self.poll_event.clear()
        self.poll_thread = Thread(target=self._poll_track_changes, daemon=True)
        self.poll_thread.start()
        logger.info("Started track change polling")

    def stop_polling(self) -> None:
        """Stop polling for track changes."""
        if not self.polling:
            return

        self.polling = False
        self.poll_event.set()

        if self.poll_thread:
            self.poll_thread.join(timeout=3.0)

        logger.info("Stopped track change polling")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_polling()
        logger.info("Mopidy client cleaned up")

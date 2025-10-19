"""
State machine for YoyoPod application.

Manages application states and transitions with validation
and context tracking.
"""

from enum import Enum
from typing import Optional, Callable, Dict, List, Set
from dataclasses import dataclass
from loguru import logger

from yoyopy.app_context import AppContext


class AppState(Enum):
    """Application states."""
    IDLE = "idle"                    # Home screen, ready to start
    MENU = "menu"                    # Main menu navigation
    PLAYING = "playing"              # Playing audio content
    PAUSED = "paused"                # Playback paused
    SETTINGS = "settings"            # Settings screen
    PLAYLIST = "playlist"            # Playlist/library view
    PLAYLIST_BROWSER = "playlist_browser"  # Browsing Mopidy playlists
    CALL_IDLE = "call_idle"          # VoIP ready, no active call
    CALL_INCOMING = "call_incoming"  # Incoming call ringing
    CALL_OUTGOING = "call_outgoing"  # Outgoing call dialing
    CALL_ACTIVE = "call_active"      # Call connected and active
    CALLING = "calling"              # Active VoIP call (outgoing/incoming/connected) - legacy
    CONNECTING = "connecting"        # Network connection setup
    ERROR = "error"                  # Error state

    # Phase 5: VoIP + Music Integration States
    PLAYING_WITH_VOIP = "playing_with_voip"  # Music playing, VoIP ready to receive calls
    PAUSED_BY_CALL = "paused_by_call"        # Music auto-paused for incoming/active call
    CALL_ACTIVE_MUSIC_PAUSED = "call_active_music_paused"  # In call, music paused in background


@dataclass
class StateTransition:
    """Represents a state transition."""
    from_state: AppState
    to_state: AppState
    trigger: str
    guard: Optional[Callable[[], bool]] = None  # Optional condition check


class StateMachine:
    """
    Manages application state transitions.

    Provides state management with validation, history tracking,
    and callback hooks for state changes.
    """

    def __init__(self, context: AppContext) -> None:
        """
        Initialize the state machine.

        Args:
            context: Application context instance
        """
        self.context = context
        self.current_state = AppState.IDLE
        self.previous_state: Optional[AppState] = None
        self.state_history: List[AppState] = [AppState.IDLE]

        # Callbacks for state changes
        self.on_enter_callbacks: Dict[AppState, List[Callable]] = {
            state: [] for state in AppState
        }
        self.on_exit_callbacks: Dict[AppState, List[Callable]] = {
            state: [] for state in AppState
        }

        # Define valid transitions
        self.transitions: List[StateTransition] = self._define_transitions()

        logger.info(f"StateMachine initialized in {self.current_state.value} state")

    def _define_transitions(self) -> List[StateTransition]:
        """
        Define valid state transitions.

        Returns:
            List of valid transitions
        """
        return [
            # From IDLE
            StateTransition(AppState.IDLE, AppState.MENU, "open_menu"),
            StateTransition(AppState.IDLE, AppState.SETTINGS, "open_settings"),
            StateTransition(AppState.IDLE, AppState.CONNECTING, "connect"),

            # From MENU
            StateTransition(AppState.MENU, AppState.IDLE, "back"),
            StateTransition(AppState.MENU, AppState.PLAYING, "select_media"),
            StateTransition(AppState.MENU, AppState.PLAYLIST, "select_playlist"),
            StateTransition(AppState.MENU, AppState.PLAYLIST_BROWSER, "browse_playlists"),
            StateTransition(AppState.MENU, AppState.CALL_IDLE, "open_voip"),
            StateTransition(AppState.MENU, AppState.SETTINGS, "select_settings"),

            # From PLAYING
            StateTransition(AppState.PLAYING, AppState.PAUSED, "pause"),
            StateTransition(AppState.PLAYING, AppState.MENU, "back"),
            StateTransition(AppState.PLAYING, AppState.IDLE, "stop"),

            # From PAUSED
            StateTransition(AppState.PAUSED, AppState.PLAYING, "resume"),
            StateTransition(AppState.PAUSED, AppState.PLAYING_WITH_VOIP, "resume"),  # Phase 5: resume with VoIP
            StateTransition(AppState.PAUSED, AppState.MENU, "back"),
            StateTransition(AppState.PAUSED, AppState.IDLE, "stop"),

            # From PLAYLIST
            StateTransition(AppState.PLAYLIST, AppState.MENU, "back"),
            StateTransition(AppState.PLAYLIST, AppState.PLAYING, "select_track"),

            # From PLAYLIST_BROWSER
            StateTransition(AppState.PLAYLIST_BROWSER, AppState.MENU, "back"),
            StateTransition(AppState.PLAYLIST_BROWSER, AppState.PLAYING, "load_playlist"),

            # From CALL_IDLE
            StateTransition(AppState.CALL_IDLE, AppState.MENU, "back"),
            StateTransition(AppState.CALL_IDLE, AppState.CALL_OUTGOING, "make_call"),
            StateTransition(AppState.CALL_IDLE, AppState.CALL_INCOMING, "incoming_call"),
            StateTransition(AppState.CALL_IDLE, AppState.CALLING, "make_call"),  # Legacy
            StateTransition(AppState.CALL_IDLE, AppState.CALLING, "incoming_call"),  # Legacy

            # From CALL_INCOMING
            StateTransition(AppState.CALL_INCOMING, AppState.CALL_ACTIVE, "answer_call"),
            StateTransition(AppState.CALL_INCOMING, AppState.CALL_IDLE, "reject_call"),
            StateTransition(AppState.CALL_INCOMING, AppState.CALL_IDLE, "call_ended"),

            # From CALL_OUTGOING
            StateTransition(AppState.CALL_OUTGOING, AppState.CALL_ACTIVE, "call_connected"),
            StateTransition(AppState.CALL_OUTGOING, AppState.CALL_IDLE, "cancel_call"),
            StateTransition(AppState.CALL_OUTGOING, AppState.CALL_IDLE, "call_failed"),

            # From CALL_ACTIVE
            StateTransition(AppState.CALL_ACTIVE, AppState.CALL_IDLE, "end_call"),
            StateTransition(AppState.CALL_ACTIVE, AppState.CALL_IDLE, "call_ended"),

            # From CALLING (Legacy - keep for backward compatibility)
            StateTransition(AppState.CALLING, AppState.CALL_IDLE, "call_ended"),
            StateTransition(AppState.CALLING, AppState.MENU, "back"),

            # From SETTINGS
            StateTransition(AppState.SETTINGS, AppState.MENU, "back"),
            StateTransition(AppState.SETTINGS, AppState.IDLE, "home"),

            # From CONNECTING
            StateTransition(AppState.CONNECTING, AppState.IDLE, "cancel"),
            StateTransition(AppState.CONNECTING, AppState.MENU, "connected"),

            # From ERROR - can go to idle
            StateTransition(AppState.ERROR, AppState.IDLE, "reset"),

            # Phase 5: VoIP + Music Integration Transitions
            # Music to VoIP-ready music
            StateTransition(AppState.PLAYING, AppState.PLAYING_WITH_VOIP, "voip_ready"),
            StateTransition(AppState.PLAYLIST_BROWSER, AppState.PLAYING_WITH_VOIP, "load_playlist_with_voip"),
            StateTransition(AppState.MENU, AppState.PLAYING_WITH_VOIP, "select_media_with_voip"),

            # From PLAYING_WITH_VOIP (music playing, VoIP ready)
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.PAUSED, "pause"),
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.MENU, "back"),
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.IDLE, "stop"),
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.PAUSED_BY_CALL, "auto_pause_for_call"),
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.CALL_INCOMING, "incoming_call"),

            # From PAUSED_BY_CALL (music paused for call)
            StateTransition(AppState.PAUSED_BY_CALL, AppState.CALL_INCOMING, "incoming_call_ringing"),
            StateTransition(AppState.PAUSED_BY_CALL, AppState.CALL_ACTIVE_MUSIC_PAUSED, "call_answered"),
            StateTransition(AppState.PAUSED_BY_CALL, AppState.PLAYING_WITH_VOIP, "call_rejected_resume"),
            StateTransition(AppState.PAUSED_BY_CALL, AppState.PAUSED, "call_rejected_stay_paused"),

            # From CALL_INCOMING with music in background
            StateTransition(AppState.CALL_INCOMING, AppState.CALL_ACTIVE_MUSIC_PAUSED, "answer_call_resume_after"),
            StateTransition(AppState.CALL_INCOMING, AppState.PAUSED, "reject_call_stay_paused"),
            StateTransition(AppState.CALL_INCOMING, AppState.PLAYING_WITH_VOIP, "reject_call_resume"),

            # From CALL_ACTIVE_MUSIC_PAUSED (in call, music paused)
            StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.PLAYING_WITH_VOIP, "call_ended_auto_resume"),
            StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.PAUSED, "call_ended_stay_paused"),
            StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.MENU, "call_ended_stop_music"),

            # Outgoing call from music screen
            StateTransition(AppState.PLAYING_WITH_VOIP, AppState.CALL_OUTGOING, "make_call_pause_music"),
            StateTransition(AppState.CALL_OUTGOING, AppState.CALL_ACTIVE_MUSIC_PAUSED, "call_connected_music_paused"),
        ]

    def can_transition(self, to_state: AppState, trigger: str = "manual") -> bool:
        """
        Check if transition to new state is valid.

        Args:
            to_state: Target state
            trigger: Trigger name (for logging)

        Returns:
            True if transition is valid, False otherwise
        """
        # Find matching transition
        for transition in self.transitions:
            if (transition.from_state == self.current_state and
                transition.to_state == to_state and
                transition.trigger == trigger):

                # Check guard condition if present
                if transition.guard and not transition.guard():
                    logger.warning(
                        f"Transition {self.current_state.value} -> {to_state.value} "
                        f"blocked by guard"
                    )
                    return False

                return True

        # Check if it's the same state (always allowed)
        if to_state == self.current_state:
            return True

        logger.warning(
            f"Invalid transition: {self.current_state.value} -> {to_state.value} "
            f"(trigger: {trigger})"
        )
        return False

    def transition_to(self, new_state: AppState, trigger: str = "manual") -> bool:
        """
        Transition to a new state.

        Args:
            new_state: Target state
            trigger: Trigger name

        Returns:
            True if transition succeeded, False otherwise
        """
        # Check if transition is valid
        if not self.can_transition(new_state, trigger):
            logger.error(
                f"Cannot transition from {self.current_state.value} "
                f"to {new_state.value}"
            )
            return False

        # Don't do anything if already in target state
        if new_state == self.current_state:
            logger.debug(f"Already in {new_state.value} state")
            return True

        old_state = self.current_state

        # Exit current state
        logger.info(f"Exiting state: {old_state.value}")
        self._fire_callbacks(self.on_exit_callbacks[old_state])

        # Update state
        self.previous_state = old_state
        self.current_state = new_state
        self.state_history.append(new_state)

        # Limit history size
        if len(self.state_history) > 50:
            self.state_history = self.state_history[-50:]

        # Enter new state
        logger.info(f"Entering state: {new_state.value} (trigger: {trigger})")
        self._fire_callbacks(self.on_enter_callbacks[new_state])

        return True

    def go_back(self) -> bool:
        """
        Go back to the previous state.

        Returns:
            True if successful, False otherwise
        """
        if len(self.state_history) < 2:
            logger.warning("Cannot go back: no previous state")
            return False

        # Get the state before current
        # state_history[-1] is current, [-2] is previous
        previous = self.state_history[-2]

        # Determine trigger based on current state
        trigger = "back"

        return self.transition_to(previous, trigger)

    def on_enter(self, state: AppState, callback: Callable) -> None:
        """
        Register callback for entering a state.

        Args:
            state: State to register callback for
            callback: Function to call when entering state
        """
        self.on_enter_callbacks[state].append(callback)
        logger.debug(f"Registered on_enter callback for {state.value}")

    def on_exit(self, state: AppState, callback: Callable) -> None:
        """
        Register callback for exiting a state.

        Args:
            state: State to register callback for
            callback: Function to call when exiting state
        """
        self.on_exit_callbacks[state].append(callback)
        logger.debug(f"Registered on_exit callback for {state.value}")

    def _fire_callbacks(self, callbacks: List[Callable]) -> None:
        """
        Fire all callbacks in a list.

        Args:
            callbacks: List of callbacks to fire
        """
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    def get_valid_transitions(self) -> List[AppState]:
        """
        Get list of valid states that can be transitioned to from current state.

        Returns:
            List of valid target states
        """
        valid_states = []
        for transition in self.transitions:
            if transition.from_state == self.current_state:
                # Check guard if present
                if not transition.guard or transition.guard():
                    if transition.to_state not in valid_states:
                        valid_states.append(transition.to_state)
        return valid_states

    def reset(self) -> None:
        """Reset state machine to initial state."""
        logger.info("Resetting state machine")
        self.transition_to(AppState.IDLE, "reset")
        self.state_history = [AppState.IDLE]
        self.previous_state = None

    # Convenience methods for common transitions

    def open_menu(self) -> bool:
        """Transition to MENU state."""
        return self.transition_to(AppState.MENU, "open_menu")

    def start_playback(self) -> bool:
        """Transition to PLAYING state."""
        if self.transition_to(AppState.PLAYING, "select_media"):
            self.context.play()
            return True
        return False

    def pause_playback(self) -> bool:
        """Transition to PAUSED state."""
        if self.transition_to(AppState.PAUSED, "pause"):
            self.context.pause()
            return True
        return False

    def resume_playback(self) -> bool:
        """Transition to PLAYING state from PAUSED."""
        if self.transition_to(AppState.PLAYING, "resume"):
            self.context.resume()
            return True
        return False

    def stop_playback(self) -> bool:
        """Stop playback and return to IDLE."""
        if self.transition_to(AppState.IDLE, "stop"):
            self.context.stop()
            return True
        return False

    def toggle_playback(self) -> bool:
        """
        Toggle between playing and paused states.

        Returns:
            True if now playing, False if paused
        """
        if self.current_state == AppState.PLAYING:
            self.pause_playback()
            return False
        elif self.current_state == AppState.PAUSED:
            self.resume_playback()
            return True
        else:
            # Start playback from other states
            self.start_playback()
            return True

    def open_settings(self) -> bool:
        """Transition to SETTINGS state."""
        return self.transition_to(AppState.SETTINGS, "select_settings")

    def get_state_name(self) -> str:
        """Get the current state name."""
        return self.current_state.value

    def is_playing(self) -> bool:
        """Check if currently in PLAYING state."""
        return self.current_state == AppState.PLAYING

    def is_idle(self) -> bool:
        """Check if currently in IDLE state."""
        return self.current_state == AppState.IDLE

    # Phase 5: VoIP + Music Integration helper methods

    def is_playing_with_voip(self) -> bool:
        """Check if currently playing music with VoIP ready."""
        return self.current_state == AppState.PLAYING_WITH_VOIP

    def is_music_paused_by_call(self) -> bool:
        """Check if music is paused due to call."""
        return self.current_state in [
            AppState.PAUSED_BY_CALL,
            AppState.CALL_ACTIVE_MUSIC_PAUSED
        ]

    def is_in_call(self) -> bool:
        """Check if currently in any call state."""
        return self.current_state in [
            AppState.CALL_INCOMING,
            AppState.CALL_OUTGOING,
            AppState.CALL_ACTIVE,
            AppState.CALL_ACTIVE_MUSIC_PAUSED,
            AppState.CALLING  # Legacy
        ]

    def is_music_playing(self) -> bool:
        """Check if music is currently playing (any music state)."""
        return self.current_state in [
            AppState.PLAYING,
            AppState.PLAYING_WITH_VOIP
        ]

    def has_paused_music_for_call(self) -> bool:
        """Check if we have music paused that should resume after call."""
        return self.current_state in [
            AppState.PAUSED_BY_CALL,
            AppState.CALL_ACTIVE_MUSIC_PAUSED
        ]

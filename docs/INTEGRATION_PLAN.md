# YoyoPod VoIP + Music Streaming Integration Plan

**Date:** 2025-10-19
**Version:** 1.0
**Status:** Planning Phase

---

## Executive Summary

This document outlines the integration plan for merging YoyoPod's VoIP calling and music streaming capabilities into a unified application. The integration will create a seamless experience where users can:

- Stream music via Mopidy/Spotify
- Make and receive VoIP calls
- Handle call interruptions during music playback
- Switch between music and call modes with unified controls

**Key Requirements:**
- Auto-pause music when incoming call arrives
- Restore music playback after call ends (configurable)
- Unified state machine managing both subsystems
- Context-sensitive button controls
- Proper screen transitions and stack management
- RAM-efficient implementation (151 MB available on Pi Zero 2W)

---

## 1. Current Architecture Analysis

### 1.1 Existing Components

**Working Demos:**
- `demo_voip.py` - VoIP calling with full UI (38 MB RAM)
- `demo_playlists.py` - Playlist browsing (54.5 MB RAM)
- `demo_mopidy.py` - Music streaming with Now Playing UI

**Core Managers:**
- `VoIPManager` - SIP registration, call handling, callbacks
- `MopidyClient` - Music playback, playlist management, track polling
- `StateMachine` - Application state management (already exists!)
- `ScreenManager` - Screen stack navigation
- `InputHandler` - Button event handling

**Screens:**
- Menu, NowPlaying, PlaylistScreen (music side)
- CallScreen, ContactListScreen, IncomingCallScreen, OutgoingCallScreen, InCallScreen (VoIP side)

### 1.2 Integration Patterns Observed

**VoIP Demo Pattern (demo_voip.py):**
```python
# Initialize managers
voip_manager = VoIPManager(voip_config, config_manager)
screen_manager = ScreenManager(display, input_handler)

# Register callbacks
def on_incoming_call(caller_address, caller_name):
    incoming_call_screen.caller_address = caller_address
    incoming_call_screen.caller_name = caller_name
    if screen_manager.current_screen != incoming_call_screen:
        screen_manager.push_screen("incoming_call")

voip_manager.on_incoming_call(on_incoming_call)
```

**Music Demo Pattern (demo_playlists.py):**
```python
# Initialize managers
mopidy = MopidyClient(host="localhost", port=6680)
screen_manager = ScreenManager(display, input_handler)

# Register callbacks
def on_track_change(track):
    if screen_manager.current_screen == now_playing_screen:
        now_playing_screen.render()

mopidy.on_track_change(on_track_change)
```

**Key Observation:**
Both demos use similar patterns - initialize managers, register screens, set up callbacks. Integration will merge these patterns into a single coordinated system.

---

## 2. Enhanced State Machine Design

### 2.1 New Application States

The existing `StateMachine` (yoyopy/state_machine.py) already has basic states. We'll enhance it with combined states for call interruption scenarios:

```python
class AppState(Enum):
    # Existing states (keep these)
    IDLE = "idle"
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"

    # Enhanced VoIP states (already partially exists)
    CALL_IDLE = "call_idle"          # VoIP ready, no call
    CALL_INCOMING = "call_incoming"   # Incoming call ringing
    CALL_OUTGOING = "call_outgoing"   # Dialing out
    CALL_ACTIVE = "call_active"       # In active call

    # NEW: Combined states for music + VoIP coordination
    PLAYING_WITH_VOIP = "playing_with_voip"  # Music playing, VoIP ready to receive
    PAUSED_BY_CALL = "paused_by_call"        # Music auto-paused for call
    CALL_ACTIVE_MUSIC_PAUSED = "call_active_music_paused"  # Alias for clarity

    # Existing navigation states
    PLAYLIST_BROWSER = "playlist_browser"
    SETTINGS = "settings"
    ERROR = "error"
```

### 2.2 State Transition Map

**Critical Transitions for Integration:**

```
┌─────────────────────────────────────────────────────────────────┐
│                     Normal Music Flow                           │
└─────────────────────────────────────────────────────────────────┘

MENU → PLAYLIST_BROWSER → PLAYING_WITH_VOIP ⟷ PAUSED
                              ↓
                            MENU (stop)

┌─────────────────────────────────────────────────────────────────┐
│                  Call Interruption Flow                         │
└─────────────────────────────────────────────────────────────────┘

PLAYING_WITH_VOIP → CALL_INCOMING → CALL_ACTIVE_MUSIC_PAUSED
    (auto-pause)       (answer)
                           ↓
                    PLAYING_WITH_VOIP (call ends, auto-resume)
                           or
                         PAUSED (call ends, don't auto-resume)

┌─────────────────────────────────────────────────────────────────┐
│                    Outgoing Call Flow                           │
└─────────────────────────────────────────────────────────────────┘

MENU → CALL_IDLE → CALL_OUTGOING → CALL_ACTIVE
                        ↓               ↓
                    CALL_IDLE      CALL_IDLE (call ends)
                   (cancel)

OR (from music):

PLAYING_WITH_VOIP → CALL_IDLE → CALL_OUTGOING → CALL_ACTIVE_MUSIC_PAUSED
  (user action)     (manual pause)                    ↓
                                               PLAYING_WITH_VOIP
                                              (call ends, resume)
```

### 2.3 New State Transitions

**Add to StateMachine._define_transitions():**

```python
# Music + VoIP combined states
StateTransition(AppState.PLAYING, AppState.PLAYING_WITH_VOIP, "voip_ready"),
StateTransition(AppState.PLAYING_WITH_VOIP, AppState.CALL_INCOMING, "incoming_call"),
StateTransition(AppState.PLAYING_WITH_VOIP, AppState.PAUSED_BY_CALL, "auto_pause_for_call"),
StateTransition(AppState.PAUSED_BY_CALL, AppState.CALL_INCOMING, "incoming_call"),
StateTransition(AppState.CALL_INCOMING, AppState.CALL_ACTIVE_MUSIC_PAUSED, "answer_call"),
StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.PLAYING_WITH_VOIP, "call_ended_auto_resume"),
StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.PAUSED, "call_ended_stay_paused"),
StateTransition(AppState.CALL_ACTIVE_MUSIC_PAUSED, AppState.MENU, "call_ended_stop_music"),

# Guard conditions example
StateTransition(
    AppState.PLAYING_WITH_VOIP,
    AppState.CALL_INCOMING,
    "incoming_call",
    guard=lambda: voip_manager.is_registered()
)
```

### 2.4 State Transition Triggers

**Trigger Events:**
- `"incoming_call"` - VoIPManager callback fires
- `"auto_pause_for_call"` - Music auto-paused
- `"answer_call"` - User pressed A on incoming call screen
- `"call_ended_auto_resume"` - Call ended, resume music
- `"call_ended_stay_paused"` - Call ended, keep music paused
- `"voip_ready"` - VoIP registered successfully

---

## 3. Unified Application Architecture

### 3.1 YoyoPod Main Application Class

**New file: `yoyopy/yoyopod_app.py`**

```python
class YoyoPodApp:
    """
    Main YoyoPod application coordinator.

    Integrates VoIP, music streaming, state management,
    and UI into a unified application.
    """

    def __init__(self, config_dir: str = "config", simulate: bool = False):
        # Core components
        self.display = Display(simulate=simulate)
        self.context = AppContext()
        self.config_manager = ConfigManager(config_dir)

        # Input handling
        self.input_handler = InputHandler(...) if not simulate else None

        # State machine
        self.state_machine = StateMachine(self.context)

        # Screen manager
        self.screen_manager = ScreenManager(self.display, self.input_handler)

        # VoIP manager
        voip_config = VoIPConfig.from_config_manager(self.config_manager)
        self.voip_manager = VoIPManager(voip_config, self.config_manager)

        # Music manager
        self.mopidy_client = MopidyClient(host="localhost", port=6680)

        # Integration state
        self.music_was_playing_before_call = False
        self.auto_resume_after_call = True  # Configurable

    def setup(self):
        """Initialize all components and register callbacks."""
        self._setup_screens()
        self._setup_voip_callbacks()
        self._setup_music_callbacks()
        self._setup_state_callbacks()

    def _setup_voip_callbacks(self):
        """Register VoIP event callbacks."""
        self.voip_manager.on_incoming_call(self._handle_incoming_call)
        self.voip_manager.on_call_state_change(self._handle_call_state_change)
        self.voip_manager.on_registration_change(self._handle_registration_change)

    def _setup_music_callbacks(self):
        """Register music event callbacks."""
        self.mopidy_client.on_track_change(self._handle_track_change)

    def _handle_incoming_call(self, caller_address: str, caller_name: str):
        """Handle incoming call - coordinate music pause and screen switch."""
        logger.info(f"Incoming call from {caller_name}")

        # Check if music is playing
        if self.state_machine.current_state == AppState.PLAYING_WITH_VOIP:
            self.music_was_playing_before_call = True
            # Auto-pause music
            logger.info("Auto-pausing music for incoming call")
            self.mopidy_client.pause()
            self.state_machine.transition_to(
                AppState.PAUSED_BY_CALL,
                "auto_pause_for_call"
            )

        # Update incoming call screen
        incoming_screen = self.screen_manager.screens["incoming_call"]
        incoming_screen.caller_address = caller_address
        incoming_screen.caller_name = caller_name

        # Push incoming call screen
        if self.screen_manager.current_screen != incoming_screen:
            self.screen_manager.push_screen("incoming_call")

        # Transition state
        self.state_machine.transition_to(
            AppState.CALL_INCOMING,
            "incoming_call"
        )

    def _handle_call_state_change(self, state):
        """Handle call state changes."""
        if state.value == "released":
            # Call ended
            self._handle_call_ended()

    def _handle_call_ended(self):
        """Handle call end - restore music if needed."""
        logger.info("Call ended")

        # Pop all call screens
        while self.screen_manager.current_screen in [
            self.screen_manager.screens["incoming_call"],
            self.screen_manager.screens["outgoing_call"],
            self.screen_manager.screens["in_call"]
        ]:
            self.screen_manager.pop_screen()
            if not self.screen_manager.screen_stack:
                break

        # Resume music if it was playing
        if self.music_was_playing_before_call and self.auto_resume_after_call:
            logger.info("Auto-resuming music after call")
            self.mopidy_client.play()
            self.state_machine.transition_to(
                AppState.PLAYING_WITH_VOIP,
                "call_ended_auto_resume"
            )
            self.music_was_playing_before_call = False
        else:
            # Stay paused
            self.state_machine.transition_to(
                AppState.PAUSED,
                "call_ended_stay_paused"
            )
            self.music_was_playing_before_call = False
```

### 3.2 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        YoyoPodApp                               │
│  (Central coordinator - owns all managers and state)            │
└──────┬────────────┬────────────┬────────────┬───────────────────┘
       │            │            │            │
       ▼            ▼            ▼            ▼
  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │ VoIP    │ │ Mopidy   │ │ State    │ │ Screen       │
  │ Manager │ │ Client   │ │ Machine  │ │ Manager      │
  └─────────┘ └──────────┘ └──────────┘ └──────────────┘
       │            │            │            │
       │ callbacks  │ callbacks  │ callbacks  │ screen
       │            │            │            │ transitions
       └────────────┴────────────┴────────────┘
                     ▲
                     │
           Coordination happens
           in YoyoPodApp callbacks
```

**Key Principle:**
YoyoPodApp owns all managers and coordinates their interactions through callbacks. No direct communication between VoIPManager and MopidyClient.

---

## 4. Screen Flow Integration

### 4.1 Screen-to-State Mapping

| State                        | Primary Screen        | Notes                              |
|------------------------------|-----------------------|------------------------------------|
| IDLE                         | MenuScreen            | Main menu                          |
| MENU                         | MenuScreen            | Same as IDLE                       |
| PLAYING_WITH_VOIP            | NowPlayingScreen      | Shows track info + playback status |
| PAUSED                       | NowPlayingScreen      | Same screen, different state       |
| PAUSED_BY_CALL               | NowPlayingScreen      | (Background - call screen on top)  |
| PLAYLIST_BROWSER             | PlaylistScreen        | Browse Spotify playlists           |
| CALL_IDLE                    | CallScreen            | VoIP status, ready to call         |
| CALL_INCOMING                | IncomingCallScreen    | Ringing, caller name, answer/reject|
| CALL_OUTGOING                | OutgoingCallScreen    | Calling..., contact name           |
| CALL_ACTIVE                  | InCallScreen          | Active call with duration          |
| CALL_ACTIVE_MUSIC_PAUSED     | InCallScreen          | Active call (music paused in bg)   |

### 4.2 Screen Transition Scenarios

#### Scenario 1: Incoming Call During Music Playback

```
┌──────────────────────────────────────────────────────────────────┐
│ User Action: None (incoming call arrives while music playing)    │
└──────────────────────────────────────────────────────────────────┘

Screen Stack Before:  [MenuScreen, NowPlayingScreen]
State:                PLAYING_WITH_VOIP

↓ (Incoming call callback fires)

1. YoyoPodApp._handle_incoming_call() called
2. Mopidy paused: mopidy_client.pause()
3. State → CALL_INCOMING
4. Screen pushed: screen_manager.push_screen("incoming_call")

Screen Stack After:   [MenuScreen, NowPlayingScreen, IncomingCallScreen]
State:                CALL_INCOMING

↓ (User presses A to answer)

5. State → CALL_ACTIVE_MUSIC_PAUSED
6. Screen pushed: screen_manager.push_screen("in_call")

Screen Stack:         [MenuScreen, NowPlayingScreen, IncomingCallScreen, InCallScreen]
State:                CALL_ACTIVE_MUSIC_PAUSED

↓ (Call ends)

7. YoyoPodApp._handle_call_ended() called
8. Pop all call screens (InCallScreen, IncomingCallScreen)
9. Mopidy resumed: mopidy_client.play()
10. State → PLAYING_WITH_VOIP

Screen Stack After:   [MenuScreen, NowPlayingScreen]
State:                PLAYING_WITH_VOIP
```

**Implementation Notes:**
- Guard against screen stack overflow (already fixed in demo_voip.py:216-217)
- Only push IncomingCallScreen if not already showing
- Loop to pop ALL call screens when call ends (already implemented in demo_voip.py:229-235)

#### Scenario 2: User Makes Call While Browsing Playlists

```
┌──────────────────────────────────────────────────────────────────┐
│ User Action: Navigate to Menu → Call Contact                    │
└──────────────────────────────────────────────────────────────────┘

Screen Stack Before:  [MenuScreen]
State:                MENU

↓ (User selects "Call Contact" from menu)

1. Screen pushed: screen_manager.push_screen("contacts")
2. State → CALL_IDLE

Screen Stack:         [MenuScreen, ContactListScreen]
State:                CALL_IDLE

↓ (User selects contact and presses A to call)

3. VoIP call initiated: voip_manager.make_call(sip_address)
4. Screen pushed: screen_manager.push_screen("outgoing_call")
5. State → CALL_OUTGOING

Screen Stack:         [MenuScreen, ContactListScreen, OutgoingCallScreen]
State:                CALL_OUTGOING

↓ (Call connects)

6. Call state change callback fires
7. Screen pushed: screen_manager.push_screen("in_call")
8. State → CALL_ACTIVE

Screen Stack:         [MenuScreen, ContactListScreen, OutgoingCallScreen, InCallScreen]
State:                CALL_ACTIVE

↓ (Call ends)

9. Pop all call screens
10. State → CALL_IDLE (or MENU if user presses back)

Screen Stack After:   [MenuScreen, ContactListScreen] or [MenuScreen]
State:                CALL_IDLE or MENU
```

### 4.3 Screen Stack Management Strategy

**Problem:** Screen stack overflow during repeated incoming calls (fixed in previous session).

**Solution (Already Implemented):**
```python
# In incoming call callback (demo_voip.py:216-217)
if screen_manager.current_screen != incoming_call_screen:
    screen_manager.push_screen("incoming_call")

# In call release handler (demo_voip.py:229-235)
while screen_manager.current_screen in [in_call_screen, incoming_call_screen, outgoing_call_screen]:
    screen_manager.pop_screen()
    if not screen_manager.screen_stack:
        break
```

**Apply same pattern in YoyoPodApp.**

---

## 5. Context-Sensitive Input Mapping

### 5.1 Button Functions by State

**Hardware:** 4 buttons (A, B, X, Y)

| State                    | Button A        | Button B      | Button X         | Button Y        |
|--------------------------|-----------------|---------------|------------------|-----------------|
| **MENU**                 | Select item     | Back          | Move up          | Move down       |
| **PLAYING_WITH_VOIP**    | Play/Pause      | Back to menu  | Previous track   | Next track      |
| **PAUSED**               | Play/Pause      | Back to menu  | Previous track   | Next track      |
| **PLAYLIST_BROWSER**     | Load playlist   | Back to menu  | Move up          | Move down       |
| **CALL_IDLE**            | -               | Back to menu  | -                | -               |
| **CALL_INCOMING**        | Answer call     | Reject call   | -                | -               |
| **CALL_OUTGOING**        | Cancel call     | Cancel call   | -                | -               |
| **CALL_ACTIVE**          | -               | Hang up       | Toggle mute      | -               |
| **CALL_ACTIVE_MUSIC_PAUSED** | -           | Hang up       | Toggle mute      | -               |

### 5.2 Input Handler Pattern

**Current Implementation:**
Each screen implements `on_button_a()`, `on_button_b()`, `on_button_x()`, `on_button_y()` methods.
ScreenManager connects these when screen becomes active.

**No Changes Needed:**
This pattern already supports context-sensitive controls. Each screen defines its own button behavior.

**Example (NowPlayingScreen):**
```python
def on_button_a(self):
    """Play/Pause toggle."""
    if self.mopidy_client.get_playback_state() == "playing":
        self.mopidy_client.pause()
    else:
        self.mopidy_client.play()
    self.render()

def on_button_b(self):
    """Back to menu."""
    self.screen_manager.pop_screen()

def on_button_x(self):
    """Previous track."""
    self.mopidy_client.previous_track()

def on_button_y(self):
    """Next track."""
    self.mopidy_client.next_track()
```

### 5.3 Priority Handling

**Question:** What happens if button pressed during state transition?

**Answer:**
ScreenManager._connect_buttons() and _disconnect_buttons() handle this:
- When pushing new screen, old screen's buttons are disconnected
- New screen's buttons are connected
- No race condition possible (single-threaded button handling)

**Already Working:**
No changes needed.

---

## 6. VoIP-Music Coordination

### 6.1 Music Auto-Pause on Incoming Call

**Implementation:**

```python
def _handle_incoming_call(self, caller_address: str, caller_name: str):
    # Check if music is playing
    playback_state = self.mopidy_client.get_playback_state()

    if playback_state == "playing":
        self.music_was_playing_before_call = True
        logger.info("Auto-pausing music for incoming call")
        self.mopidy_client.pause()

    # ... continue with screen push and state transition
```

**State Transitions:**
- `PLAYING_WITH_VOIP` → `PAUSED_BY_CALL` → `CALL_INCOMING`

**Mopidy API Call:**
- `mopidy_client.pause()` - Immediate pause (no fade-out)

### 6.2 Music Auto-Resume After Call

**Configuration Options:**

```yaml
# config/yoyopod_config.yaml (new file)
audio:
  auto_resume_after_call: true  # Resume music after call ends
  fade_out_duration_ms: 500     # Fade out before call (future)
  fade_in_duration_ms: 1000     # Fade in after call (future)

voip:
  priority_over_music: true     # Always pause music for calls
```

**Implementation:**

```python
def _handle_call_ended(self):
    logger.info("Call ended")

    # Pop call screens
    self._pop_call_screens()

    # Resume music if configured and was playing
    if (self.music_was_playing_before_call and
        self.config.get("audio.auto_resume_after_call", True)):
        logger.info("Auto-resuming music after call")
        self.mopidy_client.play()
        self.state_machine.transition_to(
            AppState.PLAYING_WITH_VOIP,
            "call_ended_auto_resume"
        )
    else:
        # Stay paused
        self.state_machine.transition_to(
            AppState.PAUSED,
            "call_ended_stay_paused"
        )

    # Reset flag
    self.music_was_playing_before_call = False
```

### 6.3 Preventing Simultaneous Playback

**Not a problem:**
VoIP (linphonec) and Mopidy use different audio streams. They can coexist.

**But for UX:**
Always pause music during calls to avoid confusion and audio mixing.

**Guard in State Machine:**

```python
# Don't allow starting music while in active call
StateTransition(
    AppState.CALL_ACTIVE,
    AppState.PLAYING_WITH_VOIP,
    "start_music",
    guard=lambda: not self.voip_manager.has_active_call()  # Will return False
)
```

### 6.4 Error Handling

**Scenario:** Mopidy connection lost during music playback

**Handling:**
```python
def _handle_track_change(self, track: Optional[MopidyTrack]):
    if track is None and self.state_machine.current_state == AppState.PLAYING_WITH_VOIP:
        logger.warning("Track is None - Mopidy may have stopped")
        # Transition to PAUSED instead of PLAYING
        self.state_machine.transition_to(AppState.PAUSED, "playback_stopped")
```

**Scenario:** VoIP disconnects during call

**Handling:**
VoIPManager already handles this with registration_state callbacks. YoyoPodApp should:
```python
def _handle_registration_change(self, state: RegistrationState):
    if state == RegistrationState.FAILED:
        # Show error on call screen if visible
        if isinstance(self.screen_manager.current_screen, CallScreen):
            self.screen_manager.current_screen.render()  # Will show "Failed" status
```

---

## 7. Implementation Phases

### Phase 1: Core Integration Framework (Week 1)

**Goal:** Create YoyoPodApp coordinator and enhance StateMachine

**Tasks:**
1. Create `yoyopy/yoyopod_app.py` with YoyoPodApp class
2. Enhance `yoyopy/state_machine.py` with new states:
   - `PLAYING_WITH_VOIP`
   - `PAUSED_BY_CALL`
   - `CALL_ACTIVE_MUSIC_PAUSED`
3. Add new state transitions for call interruption
4. Implement basic callback coordination in YoyoPodApp:
   - `_handle_incoming_call()`
   - `_handle_call_state_change()`
   - `_handle_call_ended()`
   - `_handle_track_change()`
5. Create configuration file: `config/yoyopod_config.yaml`

**Testing:**
- Run in simulation mode with mock calls and music
- Verify state transitions logged correctly
- Check RAM usage (should be similar to demo_playlists.py ~55 MB)

**Deliverable:**
Working YoyoPodApp skeleton that can coordinate VoIP and music managers without full UI.

---

### Phase 2: Screen Integration (Week 2)

**Goal:** Integrate all screens into YoyoPodApp and test navigation

**Tasks:**
1. Update YoyoPodApp._setup_screens() to register all screens:
   - Music screens: MenuScreen, NowPlayingScreen, PlaylistScreen
   - VoIP screens: CallScreen, ContactListScreen, IncomingCallScreen, OutgoingCallScreen, InCallScreen
2. Wire up state machine to screen manager:
   - State change callbacks trigger screen transitions
   - Screen navigation triggers state transitions
3. Test screen stack management:
   - Incoming call during music playback
   - Multiple call screens pushed/popped correctly
4. Update existing screens to work with YoyoPodApp context:
   - Pass both voip_manager and mopidy_client where needed
   - Ensure screens don't directly call state transitions (use callbacks instead)

**Testing:**
- Test on hardware: full navigation flow
- Simulate incoming call while music playing
- Verify screen stack doesn't overflow
- Check screen transitions are smooth

**Deliverable:**
Fully navigable application with all screens integrated.

---

### Phase 3: Call Interruption Handling (Week 3)

**Goal:** Implement music pause/resume on call events

**Tasks:**
1. Implement music auto-pause in `_handle_incoming_call()`:
   - Check mopidy playback state
   - Pause if playing
   - Set `music_was_playing_before_call` flag
2. Implement music auto-resume in `_handle_call_ended()`:
   - Check flag and config
   - Resume playback if configured
   - Reset flag
3. Add configuration options:
   - `auto_resume_after_call`
   - Load from `config/yoyopod_config.yaml`
4. Test edge cases:
   - Multiple incoming calls in succession
   - User manually pauses during call
   - User changes track during call (shouldn't be possible - call screen active)

**Testing:**
- Real calls on hardware
- Verify music pauses immediately on incoming call
- Verify music resumes after hangup (if configured)
- Test with auto_resume_after_call = false

**Deliverable:**
Seamless call interruption with music pause/resume.

---

### Phase 4: Testing and Refinement (Week 4)

**Goal:** Polish UX, fix bugs, optimize performance

**Tasks:**
1. RAM profiling:
   - Measure YoyoPodApp RAM usage
   - Compare to demo_playlists.py baseline
   - Optimize if needed (target: <120 MB total app RAM)
2. Bug fixing:
   - Test all state transitions
   - Test screen navigation edge cases
   - Handle Mopidy disconnection gracefully
   - Handle VoIP registration failures
3. UX improvements:
   - Add visual feedback during state transitions
   - Smooth screen animations (if performance allows)
   - Add call history tracking (stretch goal)
4. Documentation:
   - Update CLAUDE.md with integration status
   - Add user manual for unified app
   - Document configuration options

**Testing:**
- Extended hardware testing (30+ minutes continuous use)
- Stress test: multiple calls while streaming
- Test with low-quality WiFi (call quality, music buffering)

**Deliverable:**
Production-ready YoyoPod application with VoIP + music streaming.

---

## 8. Code Structure

### 8.1 New Files

```
yoyopy/
├── yoyopod_app.py          # NEW: Main application coordinator
config/
├── yoyopod_config.yaml     # NEW: Unified app configuration
demos/
├── yoyopod_full.py         # NEW: Full integrated demo
docs/
├── INTEGRATION_PLAN.md     # This document
├── USER_MANUAL.md          # NEW: User guide (Phase 4)
```

### 8.2 Modified Files

```
yoyopy/
├── state_machine.py        # Add new states and transitions
├── ui/
│   ├── screens.py          # Update screens to support YoyoPodApp context
```

### 8.3 Main Entry Point

**New file: `yoyopod_full.py`**

```python
#!/usr/bin/env python3
"""
YoyoPod - Unified VoIP + Music Streaming Application

Combines VoIP calling and Spotify music streaming into a seamless
iPod-inspired experience.
"""

import sys
from yoyopy.yoyopod_app import YoyoPodApp

def main():
    simulate = "--simulate" in sys.argv

    app = YoyoPodApp(config_dir="config", simulate=simulate)
    app.setup()
    app.run()

if __name__ == "__main__":
    main()
```

---

## 9. Configuration Schema

### 9.1 Unified Config File

**File: `config/yoyopod_config.yaml`**

```yaml
# YoyoPod Unified Configuration

app:
  name: "YoyoPod"
  version: "1.0.0"
  simulate: false

# Audio / Music Settings
audio:
  mopidy_host: "localhost"
  mopidy_port: 6680
  auto_resume_after_call: true    # Resume music after call ends
  fade_out_duration_ms: 0         # Fade out before call (0 = instant)
  fade_in_duration_ms: 0          # Fade in after call (0 = instant)
  default_volume: 70              # 0-100

# VoIP Settings (reference to voip_config.yaml)
voip:
  config_file: "config/voip_config.yaml"
  priority_over_music: true       # Always pause music for calls
  auto_answer: false              # Auto-answer incoming calls
  ring_duration_seconds: 30       # Max ring time before auto-reject

# UI Settings
ui:
  theme: "dark"                   # dark, light
  show_album_art: true            # Show album art if available
  screen_timeout_seconds: 300     # Dim screen after 5 minutes
  button_debounce_ms: 50          # Button debounce time

# Display Settings
display:
  brightness: 80                  # 0-100
  rotation: 0                     # 0, 90, 180, 270
  backlight_timeout_seconds: 60   # Turn off backlight after 1 min

# Logging
logging:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
  file: "logs/yoyopod.log"
  max_size_mb: 10
  backup_count: 3
```

### 9.2 Backward Compatibility

Existing config files remain unchanged:
- `config/voip_config.yaml` - VoIP settings (already exists)
- `config/contacts.yaml` - Contact list (already exists)

New `config/yoyopod_config.yaml` references these and adds integration settings.

---

## 10. Success Criteria

### 10.1 Functional Requirements

- ✅ Music streaming via Mopidy works independently
- ✅ VoIP calling works independently
- ✅ Incoming call auto-pauses music
- ✅ Call end auto-resumes music (if configured)
- ✅ Screen transitions work correctly during interruptions
- ✅ No screen stack overflow
- ✅ All 4 buttons work in all states
- ✅ Unified menu provides access to both music and calls

### 10.2 Performance Requirements

- ✅ Total RAM usage: <120 MB for YoyoPodApp (excluding mopidy/linphonec)
- ✅ System RAM available: >140 MB (safe margin on 416 MB Pi Zero 2W)
- ✅ Screen transitions: <200ms
- ✅ Button response time: <100ms
- ✅ Music pause on incoming call: <500ms
- ✅ No audio glitches during transitions

### 10.3 UX Requirements

- ✅ Intuitive navigation (no dead ends)
- ✅ Clear visual feedback for state changes
- ✅ Caller name visible during ring (already implemented)
- ✅ Track name/artist visible during playback
- ✅ Call duration updates in real-time
- ✅ Graceful error handling (no crashes on network loss)

---

## 11. Risk Assessment

### 11.1 Technical Risks

**Risk:** RAM exhaustion crashes the application

**Mitigation:**
- Profile RAM usage early (Phase 1)
- Set hard limit: total app RAM <120 MB
- Implement memory monitoring and warnings
- Test with multiple playlists and call scenarios

**Risk:** Screen stack overflow returns

**Mitigation:**
- Use guard conditions in incoming call callback
- Loop to pop ALL call screens on release
- Unit test screen stack management
- Already implemented pattern from demo_voip.py

**Risk:** State machine transitions become complex and buggy

**Mitigation:**
- Define all transitions upfront in planning phase (done above)
- Use state machine validation (can_transition() method)
- Log all state transitions for debugging
- Write unit tests for critical transitions

**Risk:** Mopidy or VoIP disconnection causes crash

**Mitigation:**
- Wrap all RPC calls in try/except
- Implement connection monitoring
- Add ERROR state in state machine
- Show error screen instead of crashing

### 11.2 UX Risks

**Risk:** Music doesn't resume after call (user frustration)

**Mitigation:**
- Make auto-resume configurable (default: true)
- Add visual indicator if music will resume
- Test extensively with real calls

**Risk:** Buttons don't work as expected in some states

**Mitigation:**
- Document button behavior per state (done in Section 5.1)
- Add on-screen button hints (stretch goal)
- User testing on hardware

---

## 12. Testing Strategy

### 12.1 Unit Tests

**Test State Transitions:**
```python
def test_incoming_call_pauses_music():
    app = YoyoPodApp(simulate=True)
    app.state_machine.transition_to(AppState.PLAYING_WITH_VOIP)

    # Simulate incoming call
    app._handle_incoming_call("sip:test@example.com", "Test User")

    assert app.state_machine.current_state == AppState.CALL_INCOMING
    assert app.music_was_playing_before_call == True
```

**Test Screen Stack:**
```python
def test_call_screens_popped_on_hangup():
    app = YoyoPodApp(simulate=True)
    # Push call screens
    app.screen_manager.push_screen("incoming_call")
    app.screen_manager.push_screen("in_call")

    # Simulate call end
    app._handle_call_ended()

    assert "in_call" not in [s.name for s in app.screen_manager.screen_stack]
    assert "incoming_call" not in [s.name for s in app.screen_manager.screen_stack]
```

### 12.2 Integration Tests

**Test Full Flow:**
1. Start app
2. Play music
3. Simulate incoming call (inject callback)
4. Verify music paused
5. Answer call
6. Hang up
7. Verify music resumed

**Test Edge Cases:**
1. Incoming call while browsing playlists (music not playing)
2. User manually pauses during call
3. Multiple incoming calls in rapid succession
4. Call ends before user answers

### 12.3 Hardware Testing

**Test on Pi Zero 2W:**
1. Run for 30+ minutes continuously
2. Make 10+ calls while music streaming
3. Monitor RAM usage throughout
4. Test with weak WiFi (simulate network issues)
5. Test button responsiveness

---

## 13. Future Enhancements

### 13.1 Phase 5+ Ideas

**Music Features:**
- Volume control screen
- Equalizer settings
- Search/filter playlists
- Recently played tracks
- Favorite tracks/playlists

**VoIP Features:**
- Call history (missed, incoming, outgoing)
- Speed dial shortcuts
- Dial pad for manual SIP address entry
- Conference calling (multi-party)
- Voicemail support

**Integration Features:**
- Music playback during call on hold (background music)
- Custom ringtones per contact
- Do Not Disturb mode (reject calls automatically)
- Scheduled auto-resume (don't resume after 10pm)

**System Features:**
- Battery monitoring (if on portable power)
- WiFi signal strength indicator
- Bluetooth audio support
- Web UI for remote control
- OTA updates

### 13.2 Optimization Ideas

**RAM Reduction:**
- Lazy load screens (create on demand, destroy on exit)
- Stream album art instead of caching
- Use lighter VoIP client (PJSIP instead of linphonec)

**Performance:**
- Hardware-accelerated rendering
- Button interrupt instead of polling
- Asynchronous RPC calls with futures

---

## 14. Appendix: API Reference

### 14.1 YoyoPodApp Public Methods

```python
class YoyoPodApp:
    def __init__(config_dir: str, simulate: bool)
    def setup() -> None
    def run() -> None
    def stop() -> None

    # Internal (use via state machine instead)
    def _handle_incoming_call(caller_address: str, caller_name: str) -> None
    def _handle_call_state_change(state: CallState) -> None
    def _handle_call_ended() -> None
    def _handle_track_change(track: Optional[MopidyTrack]) -> None
```

### 14.2 StateMachine New Methods

```python
class StateMachine:
    # Existing methods...

    # New state checks
    def is_playing_with_voip() -> bool
    def is_call_active() -> bool
    def has_paused_music() -> bool
```

### 14.3 Configuration API

```python
from yoyopy.config import ConfigManager

cm = ConfigManager("config")

# Read settings
auto_resume = cm.get("audio.auto_resume_after_call", default=True)
volume = cm.get("audio.default_volume", default=70)

# Update settings
cm.set("audio.default_volume", 80)
cm.save()
```

---

## 15. Revision History

| Version | Date       | Author | Changes                                    |
|---------|------------|--------|--------------------------------------------|
| 1.0     | 2025-10-19 | Claude | Initial integration plan                   |

---

**End of Document**

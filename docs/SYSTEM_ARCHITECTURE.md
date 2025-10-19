# YoyoPod System Architecture

**Date:** 2025-10-19
**Version:** 2.0
**Status:** Production

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Component Diagram](#2-component-diagram)
3. [Process Architecture](#3-process-architecture)
4. [Data Flow Diagrams](#4-data-flow-diagrams)
5. [Network Architecture](#5-network-architecture)
6. [Component Specifications](#6-component-specifications)
7. [Integration Patterns](#7-integration-patterns)
8. [Resource Management](#8-resource-management)

---

## 1. System Overview

YoyoPod is an iPod-inspired VoIP music player running on Raspberry Pi Zero 2W. It integrates:
- **Music Streaming** via Mopidy (Spotify/local files)
- **VoIP Calling** via Linphone SIP client
- **Touch Display UI** via DisplayHATMini (320x240)
- **Hardware Buttons** for navigation and control

### 1.1 Key Features

✅ Stream music from Spotify or local library
✅ Make and receive VoIP calls (SIP)
✅ Auto-pause music on incoming calls
✅ Auto-resume music after call ends
✅ Animated progress bars during playback
✅ Audible ringing for incoming calls
✅ Real-time state synchronization
✅ Context-sensitive button controls

---

## 2. Component Diagram

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Raspberry Pi Zero 2W                        │
│                         (416 MB RAM, ARMv8)                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
┌───────────────▼────────────┐         ┌─────────────▼──────────────┐
│    Hardware Components     │         │   Software Stack           │
│                            │         │                            │
│  • DisplayHATMini          │         │  • Raspberry Pi OS         │
│    (320x240 LCD, I2C)      │         │  • Python 3.x              │
│  • AB13X USB Audio Card    │         │  • Systemd services        │
│  • 4 Tactile Buttons       │         │  • NetworkManager          │
│    (A, B, X, Y)            │         │                            │
└────────────────────────────┘         └────────────────────────────┘
```

### 2.2 Application Layer Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         YoyoPodApp (yoyopod.py)                       │
│                         Main Coordinator Process                      │
│                         PID: varies, ~54 MB RAM                       │
└─────┬─────────────┬─────────────┬─────────────┬─────────────────────┘
      │             │             │             │
      ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐
│  VoIP    │  │  Music   │  │  State   │  │   Screen   │
│ Manager  │  │  Client  │  │  Machine │  │   Manager  │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘
     │             │             │              │
     │ subprocess  │ HTTP API    │ callbacks    │ render
     │             │             │              │
     ▼             ▼             ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐
│linphonec │  │  Mopidy  │  │AppContext│  │  Display   │
│ Process  │  │  Server  │  │          │  │   HAT      │
└──────────┘  └──────────┘  └──────────┘  └────────────┘
```

---

## 3. Process Architecture

### 3.1 System Processes

```
┌────────────────────────────────────────────────────────────────────┐
│                         Process Tree                               │
└────────────────────────────────────────────────────────────────────┘

systemd (PID 1)
├── mopidy.service (user service)
│   └── mopidy (PID ~300)
│       • Music streaming server
│       • HTTP JSON-RPC API (port 6680)
│       • MPD protocol (port 6600)
│       • RAM: ~28.7 MB
│       • Threads: ~15
│
├── yoyopod.py (manual start or systemd)
│   • Main application coordinator
│   • Python process
│   • RAM: ~54.5 MB
│   • Threads: ~5 (main + polling threads)
│   │
│   └── linphonec (subprocess, PID varies)
│       • SIP VoIP client
│       • Spawned by VoIPManager
│       • RAM: ~21.7 MB
│       • Audio: ALSA direct (plughw:1)
│       • Managed via stdin/stdout pipes
│
└── speaker-test (temporary, during ring)
    • Ring tone generator (800Hz sine wave)
    • Spawned during incoming calls
    • Killed when call answered/rejected
    • RAM: ~2 MB
    • Audio: ALSA (plughw:1)
```

### 3.2 Process Communication

```
YoyoPodApp Process
├── Thread: Main Loop
│   • Screen updates (1 Hz when playing)
│   • Button event handling (10 Hz polling)
│   • State machine transitions
│
├── Thread: VoIP Output Monitor
│   • Reads linphonec stdout (blocking)
│   • Parses call state changes
│   • Fires callbacks to main thread
│
├── Thread: Mopidy Track Poller
│   • Polls Mopidy API (every 2 seconds)
│   • Detects track changes
│   • Detects playback state changes
│   • Fires callbacks to main thread
│
└── Subprocess: linphonec
    • stdin: Commands from VoIPManager
    • stdout: Status messages to VoIPManager
    • stderr: Debug logs
```

---

## 4. Data Flow Diagrams

### 4.1 Incoming Call Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  SIP Server (sip.linphone.org)                                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ SIP INVITE
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  linphonec Process                                                   │
│  • Receives SIP INVITE                                               │
│  • Prints: "New incoming call from [sip:user@domain]"               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ stdout
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  VoIPManager (VoIP Output Monitor Thread)                           │
│  1. Parses stdout with regex                                         │
│  2. Extracts caller SIP address                                      │
│  3. Looks up caller name in contacts                                 │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ Callback
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  YoyoPodApp._handle_incoming_call(caller_address, caller_name)      │
│  1. Check if music playing → pause if yes                            │
│  2. Update IncomingCallScreen properties                             │
│  3. Push IncomingCallScreen to stack                                 │
│  4. Start ring tone (speaker-test)                                   │
│  5. Transition state: → CALL_INCOMING                                │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌────────────────────┐              ┌─────────────────────┐
│  Mopidy Server     │              │  DisplayHATMini     │
│  pause() called    │              │  Shows caller name  │
│  Music stops       │              │  "Answer" / "Reject"│
└────────────────────┘              └─────────────────────┘
```

### 4.2 Music Playback Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  User Action: Button A on PlaylistScreen                            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  PlaylistScreen.on_button_a()                                        │
│  1. Get selected playlist URI                                        │
│  2. Call mopidy_client.load_playlist(uri)                            │
│  3. Push NowPlayingScreen                                            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  Mopidy Server (localhost:6680)                                      │
│  1. core.tracklist.clear()                                           │
│  2. core.tracklist.add(uris=[...])                                   │
│  3. core.playback.play()                                             │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ Audio stream (ALSA)
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  USB Audio Card (card 1)                                             │
│  Playback device: plughw:1                                           │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ Analog audio
                             ▼
                        [Speakers/Headphones]


┌──────────────────────────────────────────────────────────────────────┐
│  MopidyClient (Track Poller Thread, every 2 seconds)                │
│  1. GET core.playback.get_current_tl_track()                         │
│  2. GET core.playback.get_state()                                    │
│  3. Detect changes → fire callbacks                                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ Callback
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  YoyoPodApp._handle_track_change(track)                              │
│  • Refresh NowPlayingScreen if visible                               │
│  • Update progress bar (1 Hz)                                        │
│                                                                       │
│  YoyoPodApp._handle_playback_state_change(state)                     │
│  • Sync state machine: IDLE → PLAYING_WITH_VOIP                     │
│  • Refresh screen icons (play/pause)                                 │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.3 State Machine Coordination

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Event Sources                                 │
└──────────────────────────────────────────────────────────────────────┘

VoIPManager                MopidyClient              User Input
    │                          │                          │
    │ incoming_call            │ track_change             │ button_press
    │ call_state_change        │ playback_state_change    │
    │ registration_change      │                          │
    │                          │                          │
    └──────────┬───────────────┴──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  YoyoPodApp Callback Handlers                                        │
│  • _handle_incoming_call()                                           │
│  • _handle_call_state_change()                                       │
│  • _handle_call_ended()                                              │
│  • _handle_track_change()                                            │
│  • _handle_playback_state_change()                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│  StateMachine.transition_to(new_state, trigger)                      │
│  1. Validate transition exists                                       │
│  2. Call on_exit() callback for current state                        │
│  3. Update current_state                                             │
│  4. Call on_enter() callback for new state                           │
│  5. Log transition                                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
┌────────────────────────┐     ┌──────────────────────┐
│  ScreenManager         │     │  Subsystem Actions   │
│  • Push/pop screens    │     │  • Pause music       │
│  • Update display      │     │  • Start ringing     │
│  • Connect buttons     │     │  • Answer call       │
└────────────────────────┘     └──────────────────────┘
```

---

## 5. Network Architecture

### 5.1 Network Connectivity

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Internet                                   │
└─────────────────┬────────────────────────────────┬───────────────────┘
                  │                                │
                  │                                │
      ┌───────────▼──────────┐        ┌───────────▼──────────┐
      │  SIP Server          │        │  Spotify API         │
      │  sip.linphone.org    │        │  (via Mopidy)        │
      │  Port: 5060 (TCP)    │        │  HTTPS               │
      │  STUN: 3478 (UDP)    │        │                      │
      └───────────┬──────────┘        └───────────┬──────────┘
                  │                                │
                  │                                │
┌─────────────────▼────────────────────────────────▼───────────────────┐
│                        Home Router / WiFi                            │
│                        NAT, DHCP, DNS                                │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │ WiFi (2.4 GHz)
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│                    Raspberry Pi Zero 2W                              │
│                    IP: 192.168.x.x (DHCP)                            │
│                    Hostname: rpi-zero.local (mDNS)                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Local Network Services

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi Zero 2W (localhost)                  │
└──────────────────────────────────────────────────────────────────────┘

Port 6680 (HTTP)
├── Mopidy JSON-RPC API
│   • Core API: playback, tracklist, playlists
│   • Spotify extension
│   • Local files extension
│   └── Client: MopidyClient in YoyoPodApp
│
Port 6600 (TCP)
├── Mopidy MPD Protocol
│   • Music Player Daemon compatibility
│   └── Not used by YoyoPod (reserved)
│
Port 22 (SSH)
├── Remote development access
│   • git pull, deployment, debugging
│   └── User: tifo@rpi-zero
│
No External Ports Exposed
• YoyoPod is client-only (no incoming connections)
• SIP uses NAT traversal via STUN
```

---

## 6. Component Specifications

### 6.1 YoyoPodApp (Main Coordinator)

**File:** `yoyopy/yoyopod_app.py`

**Responsibilities:**
- Initialize and coordinate all subsystems
- Manage application lifecycle
- Route events between components
- Maintain integration state

**Key Methods:**
```python
class YoyoPodApp:
    def __init__(config_dir, simulate)
    def setup() -> bool           # Initialize all components
    def run() -> None              # Main event loop
    def stop() -> None             # Cleanup and shutdown

    # VoIP callbacks
    def _handle_incoming_call(caller_address, caller_name)
    def _handle_call_state_change(state)
    def _handle_call_ended()
    def _handle_registration_change(state)

    # Music callbacks
    def _handle_track_change(track)
    def _handle_playback_state_change(state)

    # Helper methods
    def _setup_screens()
    def _pop_call_screens()
    def _update_now_playing_if_needed()
    def _start_ringing()
    def _stop_ringing()
```

**Dependencies:**
- VoIPManager
- MopidyClient
- StateMachine
- ScreenManager
- ConfigManager

**RAM Usage:** ~54.5 MB

---

### 6.2 VoIPManager

**File:** `yoyopy/connectivity/voip_manager.py`

**Responsibilities:**
- Manage linphonec subprocess
- Parse SIP events from stdout
- Send commands via stdin
- Lookup caller names from contacts
- Fire callbacks for call events

**Key Methods:**
```python
class VoIPManager:
    def __init__(config, config_manager)
    def start() -> bool
    def stop()
    def make_call(sip_address) -> bool
    def answer_call() -> bool
    def hangup() -> bool
    def get_status() -> Dict

    # Callbacks
    def on_incoming_call(callback)
    def on_call_state_change(callback)
    def on_registration_change(callback)
```

**Communication:**
- Spawns: `linphonec -c /home/tifo/.linphonerc`
- stdin: Commands (e.g., "answer", "terminate")
- stdout: Events (parsed with regex)
- Audio: Direct ALSA (plughw:1)

**RAM Usage:** ~21.7 MB (linphonec subprocess)

---

### 6.3 MopidyClient

**File:** `yoyopy/audio/mopidy_client.py`

**Responsibilities:**
- Communicate with Mopidy HTTP API
- Poll for track and state changes
- Control playback (play, pause, next, prev)
- Load playlists

**Key Methods:**
```python
class MopidyClient:
    def __init__(host, port, timeout)
    def connect() -> bool
    def play()
    def pause()
    def next_track()
    def previous_track()
    def get_playback_state() -> str
    def get_current_track() -> MopidyTrack
    def get_time_position() -> int
    def load_playlist(uri) -> bool

    # Polling
    def start_polling()
    def stop_polling()

    # Callbacks
    def on_track_change(callback)
    def on_playback_state_change(callback)
```

**Communication:**
- Protocol: HTTP JSON-RPC
- Endpoint: http://localhost:6680/mopidy/rpc
- Polling: Every 2 seconds (background thread)

**Mopidy Server RAM:** ~28.7 MB (separate process)

---

### 6.4 StateMachine

**File:** `yoyopy/state_machine.py`

**Responsibilities:**
- Track current application state
- Validate state transitions
- Fire state enter/exit callbacks
- Provide state query methods

**States:**
```python
class AppState(Enum):
    IDLE = "idle"
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    PLAYING_WITH_VOIP = "playing_with_voip"
    PAUSED_BY_CALL = "paused_by_call"
    CALL_IDLE = "call_idle"
    CALL_INCOMING = "call_incoming"
    CALL_OUTGOING = "call_outgoing"
    CALL_ACTIVE = "call_active"
    CALL_ACTIVE_MUSIC_PAUSED = "call_active_music_paused"
    PLAYLIST_BROWSER = "playlist_browser"
    SETTINGS = "settings"
    ERROR = "error"
```

**Key Methods:**
```python
class StateMachine:
    def transition_to(new_state, trigger) -> bool
    def get_state_name() -> str
    def is_music_playing() -> bool
    def is_call_active() -> bool
    def has_paused_music_for_call() -> bool
    def on_enter(state, callback)
    def on_exit(state, callback)
```

**Transitions:** 24+ defined transitions

---

### 6.5 ScreenManager

**File:** `yoyopy/ui/screen_manager.py`

**Responsibilities:**
- Manage screen stack navigation
- Connect/disconnect button handlers
- Render active screen
- Track navigation history

**Key Methods:**
```python
class ScreenManager:
    def register_screen(name, screen)
    def push_screen(name)
    def pop_screen()
    def get_current_screen() -> Screen
```

**Screens:**
- MenuScreen
- NowPlayingScreen
- PlaylistScreen
- CallScreen
- ContactListScreen
- IncomingCallScreen
- OutgoingCallScreen
- InCallScreen
- HomeScreen

---

### 6.6 DisplayHATMini Driver

**File:** `yoyopy/ui/display.py`

**Responsibilities:**
- Initialize ST7789 LCD (320x240)
- Provide drawing primitives
- Render to framebuffer
- Update display

**Key Methods:**
```python
class Display:
    def clear(color)
    def text(text, x, y, color, font_size)
    def rectangle(x1, y1, x2, y2, fill, outline)
    def circle(x, y, radius, fill)
    def status_bar(time_str, battery_percent, signal_strength)
    def update()
```

**Hardware:**
- Interface: I2C (GPIO pins)
- Resolution: 320x240
- Colors: RGB565 (16-bit)
- Refresh: ~15 FPS

---

## 7. Integration Patterns

### 7.1 Callback Pattern

All subsystems communicate via callbacks registered with YoyoPodApp:

```python
# VoIP callbacks
voip_manager.on_incoming_call(self._handle_incoming_call)
voip_manager.on_call_state_change(self._handle_call_state_change)

# Music callbacks
mopidy_client.on_track_change(self._handle_track_change)
mopidy_client.on_playback_state_change(self._handle_playback_state_change)

# State callbacks
state_machine.on_enter(AppState.PLAYING_WITH_VOIP, self._on_enter_playing_with_voip)
```

**Benefits:**
- Loose coupling between components
- Easy to test with mock callbacks
- Clear event flow

### 7.2 State Synchronization

**Problem:** State machine can get out of sync with actual subsystem states

**Solution:** Periodic polling + event-driven updates

```python
# Mopidy poller thread (every 2 seconds)
current_state = get_playback_state()
if current_state != last_state:
    fire_callback(current_state)

# YoyoPodApp handler
def _handle_playback_state_change(state):
    if state == "playing":
        state_machine.transition_to(PLAYING_WITH_VOIP, "music_started")
```

### 7.3 Screen Stack Management

**Problem:** Call screens can overflow stack during repeated calls

**Solution:** Guard conditions + loop to pop all call screens

```python
# Guard: Only push if not already showing
if screen_manager.current_screen != incoming_call_screen:
    screen_manager.push_screen("incoming_call")

# Pop all call screens when call ends
def _pop_call_screens():
    call_screens = [in_call_screen, incoming_call_screen, outgoing_call_screen]
    while screen_manager.current_screen in call_screens:
        screen_manager.pop_screen()
```

---

## 8. Resource Management

### 8.1 RAM Profile

**Total System RAM:** 416 MB

```
System Breakdown:
├── Kernel + System:     160 MB
├── YoyoPod App:          54.5 MB (13%)
├── Mopidy Server:        28.7 MB (7%)
├── linphonec:            21.7 MB (5%)
├── Other Services:       60 MB
└── Available:           ~150 MB (36%)
```

**RAM Optimization Strategies:**
- Use lazy loading for playlists
- Limit screen stack depth
- Poll instead of websockets (lower overhead)
- Direct ALSA instead of PulseAudio

### 8.2 CPU Profile

**Raspberry Pi Zero 2W:** 4x ARM Cortex-A53 @ 1 GHz

```
CPU Usage (typical):
├── YoyoPod App:         5-10% (idle) / 15-20% (active)
├── Mopidy Server:       10-15% (streaming)
├── linphonec:           8-12% (in call)
├── speaker-test:        2-3% (ringing)
└── System:              10-15%
```

**CPU Optimization:**
- Screen updates: 1 Hz (not 60 Hz)
- Button polling: 10 Hz (not 100 Hz)
- Mopidy polling: 0.5 Hz (every 2 seconds)

### 8.3 Storage

```
/home/tifo/yoyo-py/:
├── Python code:         ~2 MB
├── Configuration:       ~10 KB
├── Logs:                ~5 MB (rotating)
└── Virtual env:         ~100 MB
```

### 8.4 Network Bandwidth

**Music Streaming (Spotify):**
- Bitrate: ~320 kbps (high quality)
- Data: ~2.4 MB per minute
- Buffering: Minimal (Mopidy handles)

**VoIP Calling (SIP):**
- Codec: Opus (typical)
- Bitrate: ~20-40 kbps
- Data: ~150-300 KB per minute
- Latency: <100ms (local network)

---

## 9. Configuration Files

### 9.1 Configuration Hierarchy

```
config/
├── yoyopod_config.yaml        # Main app configuration
├── voip_config.yaml           # VoIP/SIP settings
└── contacts.yaml              # Contact list

~/.linphonerc                  # Generated by VoIPManager
~/.config/mopidy/mopidy.conf   # Mopidy server config
```

### 9.2 Key Configuration Parameters

**yoyopod_config.yaml:**
```yaml
audio:
  auto_resume_after_call: true

voip:
  config_file: "config/voip_config.yaml"
```

**voip_config.yaml:**
```yaml
account:
  sip_server: "sip.linphone.org"
  sip_username: "username"
  sip_password_ha1: "hash"
  transport: "tcp"

network:
  stun_server: "stun.linphone.org"
  enable_ice: true

linphonec_path: "/usr/bin/linphonec"
```

**~/.linphonerc (generated):**
```ini
[sound]
playback_dev_id=ALSA: plughw:1
capture_dev_id=ALSA: plughw:1
mic_gain_db=10.0
echocancellation=1
```

---

## 10. Error Handling

### 10.1 Failure Modes

**Mopidy Connection Lost:**
- Detection: HTTP timeout on API calls
- Recovery: Show error on screen, retry connection
- Fallback: VoIP still works

**VoIP Registration Failed:**
- Detection: RegistrationState.FAILED callback
- Recovery: Display error on CallScreen
- Fallback: Music still works

**Display Crash:**
- Detection: Exception in render()
- Recovery: Log error, continue without display
- Fallback: App keeps running (audio still works)

**Network Loss:**
- Detection: Both Mopidy and VoIP fail
- Recovery: Periodic retry
- Fallback: Show network error screen

### 10.2 Graceful Degradation

Priority order:
1. VoIP calls (highest priority)
2. Music playback
3. UI updates
4. Status displays

If RAM critical:
- Skip non-essential screen updates
- Reduce polling frequency
- Show simplified UI

---

## 11. Deployment

### 11.1 Installation

```bash
# On Raspberry Pi
cd /home/tifo
git clone https://github.com/mou5t4/yoyo-py.git
cd yoyo-py

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/voip_config.yaml.example config/voip_config.yaml
# Edit config files...

# Run
python yoyopod.py
```

### 11.2 Systemd Service (Optional)

```ini
[Unit]
Description=YoyoPod VoIP Music Player
After=network.target mopidy.service

[Service]
Type=simple
User=tifo
WorkingDirectory=/home/tifo/yoyo-py
ExecStart=/home/tifo/yoyo-py/.venv/bin/python yoyopod.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 12. Monitoring & Debugging

### 12.1 Logging

**Log Levels:**
- DEBUG: All events, state transitions
- INFO: User actions, callbacks, important events (default)
- WARNING: Recoverable errors
- ERROR: Failures requiring attention

**Log Output:**
- stderr (default)
- File: logs/yoyopod.log (optional)

### 12.2 Debug Commands

```bash
# Check running processes
ps aux | grep -E '(python|linphonec|mopidy)'

# Monitor RAM
free -h
ps aux --sort=-%mem | head -20

# Check Mopidy
systemctl --user status mopidy
curl http://localhost:6680/mopidy/rpc

# Check audio devices
arecord -l
aplay -l
pactl list sources short
```

---

## 13. Future Enhancements

### 13.1 Planned Features

**Phase 5+ (Post-Integration):**
- Call history tracking
- Speed dial
- Custom ringtones per contact
- Volume control UI
- Bluetooth audio support
- Web remote control interface

### 13.2 Performance Improvements

- Hardware-accelerated display rendering
- Asynchronous HTTP calls
- Lighter VoIP client (PJSIP)
- Lazy screen loading

---

## Appendix A: Glossary

**ALSA:** Advanced Linux Sound Architecture - low-level audio API
**HA1 Hash:** MD5 hash used for SIP digest authentication
**I2C:** Inter-Integrated Circuit - serial communication protocol
**JSON-RPC:** Remote procedure call protocol using JSON
**mDNS:** Multicast DNS - allows .local hostname resolution
**MPD:** Music Player Daemon - music player protocol
**NAT:** Network Address Translation
**SIP:** Session Initiation Protocol - VoIP signaling
**STUN:** Session Traversal Utilities for NAT - NAT traversal protocol
**URI:** Uniform Resource Identifier - Mopidy uses for tracks/playlists

---

## Appendix B: Version History

| Version | Date       | Changes                                     |
|---------|------------|---------------------------------------------|
| 1.0     | 2025-10-13 | Initial architecture for VoIP-only system   |
| 2.0     | 2025-10-19 | Full integration with music streaming       |
|         |            | Added state synchronization                 |
|         |            | Added progress animation                    |
|         |            | Added ringing sound                         |

---

**End of System Architecture Document**

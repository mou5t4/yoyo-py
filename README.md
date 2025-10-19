# YoyoPod 🎵📞

**An iPod-inspired VoIP music player with seamless call interruption**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Hardware](https://img.shields.io/badge/hardware-Raspberry%20Pi%20Zero%202W-red)]()
[![Python](https://img.shields.io/badge/python-3.x-blue)]()

---

## Overview

YoyoPod is a fully integrated music streaming and VoIP calling device built on Raspberry Pi Zero 2W. Inspired by the classic iPod interface, it combines Spotify music playback with SIP-based voice calling in a compact, button-controlled experience.

### Key Features

✅ **Music Streaming** - Stream from Spotify or local library via Mopidy
✅ **VoIP Calling** - Make and receive SIP calls via Linphone
✅ **Seamless Integration** - Auto-pause music on incoming calls
✅ **Smart Resume** - Auto-resume music after call ends
✅ **Animated UI** - Live progress bars and state indicators
✅ **Audible Ringing** - Incoming call ring tone
✅ **Touch Display** - 320x240 color LCD with status bar
✅ **Button Controls** - 4-button navigation (A, B, X, Y)
✅ **RAM Efficient** - Runs smoothly on 416 MB RAM

---

## Hardware Requirements

### Required Components

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **Raspberry Pi Zero 2W** | 1 GHz quad-core, 512 MB RAM | Main computing platform |
| **DisplayHATMini** | Pimoroni 320x240 LCD | Touch display and buttons |
| **USB Audio Card** | AB13X or compatible | Microphone and speaker audio |
| **WiFi Network** | 2.4 GHz | Internet connectivity |
| **Power Supply** | 5V 2.5A micro USB | Device power |

### Pin Connections

- **Display**: I2C (GPIO 2/3)
- **Buttons**: GPIO pins (A, B, X, Y)
- **Audio**: USB port (card 1)

---

## Software Stack

```
┌────────────────────────────────────────┐
│          YoyoPod Application           │
│         (yoyopod_full.py)              │
│                                        │
│  ┌──────────────┐  ┌────────────────┐ │
│  │ VoIPManager  │  │ MopidyClient   │ │
│  │ (Linphone)   │  │ (Music)        │ │
│  └──────────────┘  └────────────────┘ │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │      State Machine               │ │
│  │      Screen Manager              │ │
│  │      Display Driver              │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────┐
│  linphonec      │  │  mopidy         │
│  (VoIP client)  │  │  (Music server) │
└─────────────────┘  └─────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────────────────────────┐
│         USB Audio Card              │
│         (ALSA: plughw:1)            │
└─────────────────────────────────────┘
```

---

## Installation

### Prerequisites

1. **Operating System**: Raspberry Pi OS (Bookworm or later)
2. **Python**: 3.x with pip
3. **Mopidy**: Music server (`sudo apt install mopidy`)
4. **Linphone**: VoIP client (`sudo apt install linphone-cli`)

### Quick Start

```bash
# Clone repository
git clone https://github.com/mou5t4/yoyo-py.git
cd yoyo-py

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure VoIP and music
cp config/voip_config.yaml.example config/voip_config.yaml
cp config/contacts.yaml.example config/contacts.yaml
# Edit config files with your SIP credentials and contacts

# Configure Mopidy
sudo systemctl --user enable mopidy
sudo systemctl --user start mopidy

# Run YoyoPod
python yoyopod_full.py
```

---

## Configuration

### VoIP Configuration

**File**: `config/voip_config.yaml`

```yaml
account:
  sip_server: "sip.linphone.org"
  sip_username: "your_username"
  sip_password_ha1: "your_ha1_hash"
  sip_identity: "sip:you@sip.linphone.org"
  transport: "tcp"

network:
  stun_server: "stun.linphone.org"
  enable_ice: true
```

### Contact List

**File**: `config/contacts.yaml`

```yaml
contacts:
  - name: "Mom"
    sip_address: "sip:mom@example.com"
    favorite: true

  - name: "Dad"
    sip_address: "sip:dad@example.com"
    favorite: true
```

### App Configuration

**File**: `config/yoyopod_config.yaml`

```yaml
audio:
  auto_resume_after_call: true  # Resume music after call

voip:
  config_file: "config/voip_config.yaml"
```

---

## Project Structure

```
yoyo-py/
├── yoyopod_full.py           # Main application entry point
├── main.py                   # Legacy entry point
├── README.md                 # This file
│
├── yoyopy/                   # Core package
│   ├── ui/                   # Display and screen management
│   │   ├── display.py        # DisplayHATMini driver
│   │   ├── screens.py        # All UI screens
│   │   ├── screen_manager.py # Screen stack navigation
│   │   └── input_handler.py  # Button event handling
│   │
│   ├── audio/                # Music playback
│   │   └── mopidy_client.py  # Mopidy HTTP API client
│   │
│   ├── connectivity/         # VoIP and network
│   │   ├── voip_manager.py   # Linphone VoIP interface
│   │   └── voip_config.py    # VoIP configuration
│   │
│   ├── config/               # Configuration management
│   │   └── config_manager.py # Config and contacts
│   │
│   ├── state_machine.py      # Application state management
│   ├── yoyopod_app.py        # Main coordinator class
│   └── app_context.py        # Shared application context
│
├── config/                   # Configuration files
│   ├── voip_config.yaml      # VoIP settings
│   ├── contacts.yaml         # Contact list
│   └── yoyopod_config.yaml   # App settings
│
├── demos/                    # Demo applications
│   ├── demo_voip.py          # VoIP-only demo
│   ├── demo_playlists.py     # Music-only demo
│   └── demo_yoyopod_phase1.py # Phase 1 framework demo
│
├── tests/                    # Test suite
│   ├── test_phase1_state_machine.py
│   ├── test_voip_registration.py
│   └── test_incoming_call_debug.py
│
└── docs/                     # Documentation
    ├── SYSTEM_ARCHITECTURE.md  # Complete system diagrams
    ├── INTEGRATION_PLAN.md     # Implementation phases
    ├── PHASE1_SUMMARY.md       # Phase 1 details
    └── PHASE2_SUMMARY.md       # Phase 2 details
```

---

## Usage

### Starting the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Start YoyoPod
python yoyopod_full.py

# Or in simulation mode (no hardware required)
python yoyopod_full.py --simulate
```

### Button Controls

| Screen | Button A | Button B | Button X | Button Y |
|--------|----------|----------|----------|----------|
| **Menu** | Select | Back | Up | Down |
| **Now Playing** | Play/Pause | Back | Previous | Next |
| **Playlists** | Load | Back | Up | Down |
| **Incoming Call** | Answer | Reject | - | - |
| **In Call** | - | Hang Up | Mute | - |

### Navigation Flow

```
Menu Screen
├── Browse Playlists → Playlist List → Now Playing Screen
├── VoIP Status → Call Screen (shows registration)
└── Call Contact → Contact List → Outgoing Call → In Call Screen
```

### Call Interruption

When an incoming call arrives while music is playing:

1. 🎵 Music auto-pauses
2. 📞 Incoming call screen appears
3. 🔔 Ring tone plays (800 Hz)
4. Press **A** to answer or **B** to reject
5. During call: Press **B** to hang up
6. 🎵 Music auto-resumes after call ends

---

## Development

### Running Demos

```bash
# VoIP calling demo (contacts, incoming/outgoing calls)
python demos/demo_voip.py

# Music streaming demo (playlists, now playing)
python demos/demo_playlists.py

# State machine framework demo
python demos/demo_yoyopod_phase1.py
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_phase1_state_machine.py
```

### SSH Deployment to Pi

```bash
# From development machine
git push origin main

# On Raspberry Pi
ssh rpi-zero
cd yoyo-py
git pull origin main
source .venv/bin/activate
python yoyopod_full.py
```

---

## System Architecture

For detailed system architecture including component diagrams, data flow, and process architecture, see:

📄 **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)**

Key diagrams include:
- Component interaction diagram
- Process architecture
- Incoming call data flow
- Music playback data flow
- State machine coordination
- Network architecture

---

## Implementation Phases

YoyoPod was built in 4 phases:

### ✅ Phase 1: Core Integration Framework
- Enhanced state machine with combined VoIP+music states
- YoyoPodApp coordinator class
- Callback coordination infrastructure
- Configuration system

### ✅ Phase 2: Screen Integration
- All 9 screens integrated
- Full navigation flow
- Screen stack management
- Production app created

### ✅ Phase 3: Call Interruption Handling
- Music auto-pause on incoming calls
- Music auto-resume after call ends
- Microphone configuration
- Hardware testing

### ✅ Phase 4: Testing & Refinement
- Progress bar animation
- Pause icon synchronization
- State machine sync
- Audible ringing
- Bug fixes and documentation

📄 **See [docs/INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md) for complete details**

---

## Performance

**RAM Usage** (on Raspberry Pi Zero 2W, 416 MB total):
- YoyoPod app: ~54.5 MB (13%)
- Mopidy server: ~28.7 MB (7%)
- linphonec: ~21.7 MB (5%)
- System: ~160 MB
- **Available: ~150 MB** ✅

**CPU Usage** (quad-core 1 GHz):
- Idle: 5-10%
- Music playing: 10-15%
- During call: 15-20%

---

## Troubleshooting

### Common Issues

**VoIP won't register:**
```bash
# Check network
ping sip.linphone.org

# Check config
cat config/voip_config.yaml

# View logs (set to DEBUG level in code)
```

**No audio output:**
```bash
# List audio devices
aplay -l
arecord -l

# Test speaker
speaker-test -t wav -c 2

# Check volume
amixer -c 1
```

**Mopidy not connecting:**
```bash
# Check service status
systemctl --user status mopidy

# Restart service
systemctl --user restart mopidy

# Test API
curl http://localhost:6680/mopidy/rpc
```

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Credits

**Built with:**
- [Mopidy](https://mopidy.com/) - Music server
- [Linphone](https://www.linphone.org/) - VoIP client
- [Pimoroni DisplayHATMini](https://shop.pimoroni.com/products/display-hat-mini) - Display and buttons
- [Raspberry Pi](https://www.raspberrypi.com/) - Computing platform

**Development:**
- Integration architecture and implementation
- State machine design
- VoIP + Music coordination

---

## Status

**Current Version**: 2.0
**Status**: ✅ Production Ready
**Tested On**: Raspberry Pi Zero 2W
**Last Updated**: 2025-10-19

---

**Built with ❤️ for music lovers and conversationalists**

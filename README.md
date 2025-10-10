# yoyopy

**YoyoPod Connect** - A screen-minimal streaming device for kids aged 6-12, built on Raspberry Pi Zero 2 W.

## Overview

yoyopy is the Python application that powers the YoyoPod Connect variant, featuring audio streaming, VoIP calling, and GPS tracking capabilities. Designed to provide a safe, parent-controlled entertainment experience for children.

## Hardware Requirements

### Core Components
- **Raspberry Pi Zero 2 W** - Main computing platform
- **Pimoroni Display HAT Mini** - 320x240 color LCD with buttons
- **Cat.1 4G Module** - Primary connectivity (with WiFi fallback)
- **GPS Module** - Location tracking for safety
- **Battery & Power Management** - Portable operation

### Optional Components
- NFC reader for content tokens
- Emergency button for quick parent contact

## Features

- Audio streaming playback
- VoIP calling capabilities
- GPS location tracking
- Parental controls and content filtering
- Offline content caching
- MQTT-based real-time synchronization
- Battery-optimized operation
- Kid-friendly UI with minimal screen interaction

## Project Structure

```
yoyopy/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
├── main.py                 # Application entry point
├── yoyopy/                 # Main package
│   ├── __init__.py
│   ├── ui/                # Display and button handling
│   ├── audio/             # Audio playback and VoIP
│   ├── connectivity/      # 4G/WiFi/network management
│   ├── power/             # Battery monitoring
│   ├── security/          # Parental controls
│   ├── sync/              # Cloud synchronization
│   └── utils/             # Logger and helpers
├── tests/                 # Test suite
├── assets/                # Fonts, icons, sounds
│   ├── fonts/
│   ├── icons/
│   └── sounds/
└── config/                # Configuration files
    └── config.example.json
```

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd yoyopy
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Create configuration file:**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config/config.json with your settings
   ```

4. **Run the application:**
   ```bash
   uv run main.py
   ```

### Development Setup

Install development dependencies:
```bash
uv sync --extra dev
```

Run tests:
```bash
uv run pytest
```

Format code:
```bash
uv run black .
uv run ruff check .
```

Type checking:
```bash
uv run mypy .
```

## Configuration

Edit `config/config.json` to customize:

- **Device settings** - Name, ID, model
- **Display** - Resolution, rotation, backlight
- **Audio** - Volume, sample rate, buffer size
- **Connectivity** - 4G/WiFi, APN settings
- **Server** - API URL, MQTT broker
- **Parental controls** - Time limits, content ratings
- **Features** - Enable/disable VoIP, GPS, NFC

See `config/config.example.json` for all available options.

## Development Phases

### Phase 0: Project Setup (Current)
- ✅ Initialize uv-based Python project
- ✅ Set up directory structure
- ✅ Configure dependencies
- ✅ Create logging utility with Loguru
- ✅ Basic configuration management

### Phase 1: Hardware Abstraction
- Display driver for Pimoroni HAT Mini
- Button input handling
- Audio output configuration
- 4G/WiFi connectivity manager
- GPS module integration

### Phase 2: Core Functionality
- Audio streaming playback
- Content caching and management
- MQTT client for real-time sync
- Basic UI navigation

### Phase 3: Advanced Features
- VoIP calling implementation
- Parental control enforcement
- Battery optimization
- Offline mode handling

### Phase 4: Production Ready
- Security hardening
- Performance optimization
- Field testing
- Documentation completion

## Dependencies

### Core
- **Pillow** - Image processing for UI
- **pygame-ce** - Display rendering and audio
- **evdev** - Button input handling
- **requests** - HTTP API communication
- **paho-mqtt** - Real-time messaging
- **loguru** - Structured logging

### Development
- **pytest** - Testing framework
- **black** - Code formatting
- **ruff** - Fast Python linter
- **mypy** - Static type checking

## License

MIT License - See LICENSE file for details

## Contributing

This is a prototype project for YoyoPod Connect. Contributions welcome!

## Support

For issues and questions, please open a GitHub issue or contact the YoyoPod team.

---

**Built with ❤️ for kids and parents**

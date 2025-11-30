# UI Module Restructuring Proposal

**Date:** 2025-11-30
**Status:** PROPOSAL
**Goal:** Organize UI module for clarity, consistency, and maintainability

---

## Current Problems

### 1. **Scattered Display Files**
```
yoyopy/ui/
├── display.py              # Main Display class (facade)
├── display_hal.py          # Abstract base class
├── display_factory.py      # Factory function
└── adapters/               # Display adapters (confusing name)
    ├── display_pimoroni.py
    └── display_whisplay.py
```
**Issues:**
- Display components at root level (not organized)
- `adapters/` folder name is ambiguous (display or input?)
- Inconsistent with `input/` module structure

### 2. **Monolithic screens.py (72K file!)**
```
yoyopy/ui/screens.py  (2,200 lines)
├── Screen (base class)
├── HomeScreen
├── MenuScreen
├── NowPlayingScreen
├── PlaylistScreen
├── CallScreen
├── IncomingCallScreen
├── OutgoingCallScreen
├── InCallScreen
└── ContactListScreen
```
**Issues:**
- Single file with 10 classes (hard to navigate)
- No logical grouping (music, voip, navigation)
- Difficult to maintain and test

### 3. **screen_manager.py at Root**
- Should be with screens module
- Not clear it manages screen navigation

### 4. **Deprecated Files**
- `input_handler.py` (replaced by Input HAL)
- `display.py.bak` (backup file)
- `audio_screen.py` (unused?)

---

## Proposed Structure

### **New Organization (Clean & Consistent)**

```
yoyopy/ui/
│
├── display/                    # Display HAL module (mirrors input/)
│   ├── __init__.py             # Exports: Display, DisplayHAL, get_display
│   ├── display_hal.py          # Abstract base class
│   ├── display_manager.py      # Main Display class (facade) [was display.py]
│   ├── display_factory.py      # Auto-detection factory
│   └── adapters/
│       ├── __init__.py         # Exports: PimoroniDisplayAdapter, WhisplayDisplayAdapter
│       ├── pimoroni.py         # Pimoroni adapter [was display_pimoroni.py]
│       └── whisplay.py         # Whisplay adapter [was display_whisplay.py]
│
├── input/                      # Input HAL module (already clean!)
│   ├── __init__.py
│   ├── input_hal.py
│   ├── input_manager.py
│   ├── input_factory.py
│   └── adapters/
│       ├── __init__.py
│       ├── four_button.py
│       └── ptt_button.py
│
├── screens/                    # Screens module (split by feature)
│   ├── __init__.py             # Exports all screens + Screen base class
│   ├── base.py                 # Screen base class [extracted from screens.py]
│   ├── manager.py              # ScreenManager [was screen_manager.py]
│   │
│   ├── navigation/             # Navigation screens
│   │   ├── __init__.py
│   │   ├── home.py             # HomeScreen
│   │   └── menu.py             # MenuScreen
│   │
│   ├── music/                  # Music screens
│   │   ├── __init__.py
│   │   ├── now_playing.py      # NowPlayingScreen
│   │   └── playlist.py         # PlaylistScreen
│   │
│   └── voip/                   # VoIP screens
│       ├── __init__.py
│       ├── call.py             # CallScreen
│       ├── incoming_call.py    # IncomingCallScreen
│       ├── outgoing_call.py    # OutgoingCallScreen
│       ├── in_call.py          # InCallScreen
│       └── contact_list.py     # ContactListScreen
│
└── __init__.py                 # Main UI exports
```

---

## Benefits

### 1. **Consistency**
- Display module mirrors Input module structure
- Both use `adapters/` subfolder
- Both have HAL, Manager, Factory pattern

### 2. **Clarity**
- Clear separation: `display/`, `input/`, `screens/`
- No ambiguity about what's in each folder
- Easier for new developers to understand

### 3. **Maintainability**
- Small, focused files (200-400 lines each)
- Logical grouping by feature (music, voip, navigation)
- Easy to find and modify specific screens

### 4. **Scalability**
- Easy to add new screens (just create new file)
- Can add new display/input adapters without clutter
- Can add new screen categories (e.g., `settings/`)

### 5. **Testing**
- Can test each screen in isolation
- Can import specific screens without loading all
- Easier to mock dependencies

---

## Migration Strategy

### Phase 1: Restructure Display Module ✅
**Goal:** Move display files into `display/` module

1. Create `yoyopy/ui/display/` module structure
2. Move files:
   - `display_hal.py` → `display/display_hal.py`
   - `display.py` → `display/display_manager.py`
   - `display_factory.py` → `display/display_factory.py`
   - `adapters/display_pimoroni.py` → `display/adapters/pimoroni.py`
   - `adapters/display_whisplay.py` → `display/adapters/whisplay.py`
3. Update imports in:
   - `yoyopy/ui/display/__init__.py` (exports)
   - `yoyopy/ui/__init__.py`
   - `yoyopy/app.py`
   - All screen files
4. Test on hardware
5. Delete old `adapters/` folder

### Phase 2: Split screens.py into Modules ✅
**Goal:** Create organized `screens/` module

1. Create `yoyopy/ui/screens/` module structure
2. Extract and move classes:
   - `Screen` base class → `screens/base.py`
   - `HomeScreen` → `screens/navigation/home.py`
   - `MenuScreen` → `screens/navigation/menu.py`
   - `NowPlayingScreen` → `screens/music/now_playing.py`
   - `PlaylistScreen` → `screens/music/playlist.py`
   - `CallScreen` → `screens/voip/call.py`
   - `IncomingCallScreen` → `screens/voip/incoming_call.py`
   - `OutgoingCallScreen` → `screens/voip/outgoing_call.py`
   - `InCallScreen` → `screens/voip/in_call.py`
   - `ContactListScreen` → `screens/voip/contact_list.py`
3. Move `screen_manager.py` → `screens/manager.py`
4. Update imports in `yoyopy/ui/screens/__init__.py`
5. Update imports in `yoyopy/app.py`
6. Test on hardware
7. Delete old `screens.py` and `screen_manager.py`

### Phase 3: Migrate Screens to Semantic Actions ✅
**Goal:** Replace physical button handlers with semantic actions

For each screen, replace:
```python
# OLD (hardware-specific)
def on_button_a(self):
    self.select_item()

def on_button_b(self):
    self.screen_manager.pop_screen()

# NEW (hardware-agnostic)
def on_select(self, data=None):
    self.select_item()

def on_back(self, data=None):
    self.screen_manager.pop_screen()
```

**Migration order:**
1. Navigation screens (home, menu)
2. Music screens (now_playing, playlist)
3. VoIP screens (call, incoming_call, outgoing_call, in_call, contact_list)

### Phase 4: Cleanup ✅
**Goal:** Remove deprecated files and update documentation

1. Delete deprecated files:
   - `yoyopy/ui/input_handler.py` (replaced by Input HAL)
   - `yoyopy/ui/display.py.bak` (backup)
   - `yoyopy/ui/audio_screen.py` (if unused)
2. Update documentation:
   - `.claude/CLAUDE.md` (update architecture section)
   - `docs/SYSTEM_ARCHITECTURE.md` (if exists)
   - Add migration guide for developers

---

## Import Examples

### After Restructuring

```python
# Display
from yoyopy.ui.display import Display, DisplayHAL
from yoyopy.ui.display import get_display  # Factory
from yoyopy.ui.display.adapters import PimoroniDisplayAdapter, WhisplayDisplayAdapter

# Input
from yoyopy.ui.input import InputManager, InputAction
from yoyopy.ui.input import get_input_manager  # Factory
from yoyopy.ui.input.adapters import FourButtonInputAdapter, PTTInputAdapter

# Screens
from yoyopy.ui.screens import (
    Screen,                  # Base class
    ScreenManager,           # Manager
    HomeScreen,              # Navigation
    MenuScreen,
    NowPlayingScreen,        # Music
    PlaylistScreen,
    CallScreen,              # VoIP
    IncomingCallScreen,
    OutgoingCallScreen,
    InCallScreen,
    ContactListScreen,
)

# Or import by category
from yoyopy.ui.screens.navigation import HomeScreen, MenuScreen
from yoyopy.ui.screens.music import NowPlayingScreen, PlaylistScreen
from yoyopy.ui.screens.voip import CallScreen, IncomingCallScreen
```

---

## File Size Comparison

### Before
```
yoyopy/ui/screens.py           72K (2,200 lines) ❌ TOO BIG
```

### After
```
yoyopy/ui/screens/
├── base.py                     ~6K  (200 lines)
├── manager.py                  ~8K  (220 lines)
├── navigation/
│   ├── home.py                 ~3K  (95 lines)
│   └── menu.py                 ~5K  (166 lines)
├── music/
│   ├── now_playing.py          ~8K  (248 lines)
│   └── playlist.py             ~12K (358 lines)
└── voip/
    ├── call.py                 ~7K  (204 lines)
    ├── incoming_call.py        ~7K  (206 lines)
    ├── outgoing_call.py        ~7K  (216 lines)
    ├── in_call.py              ~9K  (264 lines)
    └── contact_list.py         ~13K (290 lines)

Total: ~85K (split into 12 focused files) ✅ MAINTAINABLE
```

---

## Backward Compatibility

All imports remain backward compatible via `__init__.py` exports:

```python
# yoyopy/ui/__init__.py
from yoyopy.ui.display import Display
from yoyopy.ui.input import InputManager
from yoyopy.ui.screens import (
    Screen, ScreenManager,
    HomeScreen, MenuScreen,
    NowPlayingScreen, PlaylistScreen,
    CallScreen, IncomingCallScreen, OutgoingCallScreen, InCallScreen,
    ContactListScreen,
)

__all__ = [
    'Display',
    'InputManager',
    'Screen',
    'ScreenManager',
    # ... all screens
]
```

Existing code like this **still works**:
```python
from yoyopy.ui import Display, ScreenManager, MenuScreen
```

---

## Estimated Effort

- **Phase 1** (Display restructure): 1-2 hours
- **Phase 2** (Screens split): 2-3 hours
- **Phase 3** (Semantic actions migration): 2-3 hours
- **Phase 4** (Cleanup): 30 minutes

**Total:** 6-9 hours

---

## Recommendation

✅ **Proceed with restructuring** - The benefits far outweigh the effort:
1. Cleaner, more professional codebase
2. Easier to maintain and extend
3. Consistent with Input HAL architecture
4. Better developer experience
5. Improved testability

**Order of execution:**
1. Phase 1 (Display) - Non-breaking, can test immediately
2. Phase 2 (Screens) - Non-breaking via exports
3. Phase 3 (Semantic actions) - Incremental migration
4. Phase 4 (Cleanup) - Final polish

---

**END OF PROPOSAL**

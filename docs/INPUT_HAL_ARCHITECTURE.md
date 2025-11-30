# Input HAL Architecture Proposal

**Date:** 2025-11-30
**Status:** PROPOSAL
**Author:** Claude Code

## Executive Summary

This document proposes a **Hardware Abstraction Layer (HAL)** for input handling in YoyoPod, decoupling the ScreenManager from specific input hardware (4-button interface, PTT button, voice commands, etc.).

### Current Problems

1. **ScreenManager tightly coupled to InputHandler** - Directly calls `input_handler.on_button()` and accesses `callbacks`
2. **InputHandler is Pimoroni-specific** - Hardcoded for 4 buttons (A, B, X, Y)
3. **Screens have hardcoded button methods** - `on_button_a/b/x/y()` assume 4 physical buttons
4. **No abstraction for input types** - Can't easily support PTT, voice, touch, gamepad, etc.
5. **Action semantics tied to hardware** - "Button A" means nothing on voice input

### Proposed Solution

Create an **Input HAL** similar to the Display HAL, with:

- **Abstract input actions** (SELECT, BACK, UP, DOWN, etc.) instead of physical buttons
- **Input adapters** for different hardware (4-button, PTT, voice)
- **Unified input manager** to coordinate input sources
- **Decoupled ScreenManager** that receives semantic actions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         YoyoPod App                             │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │ ScreenManager│◄────────┤ InputManager │                    │
│  └──────────────┘         └──────┬───────┘                    │
│         │                         │                             │
│         │                         │                             │
│    ┌────▼─────┐            ┌──────▼─────────────┐             │
│    │ Screens  │            │   InputHAL (ABC)   │             │
│    └──────────┘            └──────┬─────────────┘             │
│         │                         │                             │
│         │              ┌──────────┼──────────┐                 │
│         │              │          │          │                 │
│    ┌────▼────────┐  ┌─▼────┐  ┌─▼────┐  ┌─▼──────┐          │
│    │   Actions:  │  │ 4-Btn│  │ PTT  │  │ Voice  │          │
│    │  - SELECT   │  │Adapter│  │Adapter│  │Adapter │          │
│    │  - BACK     │  └──────┘  └──────┘  └────────┘          │
│    │  - UP/DOWN  │      │         │          │                │
│    │  - CONFIRM  │  ┌───▼─────┐ ┌▼────┐  ┌─▼──────┐         │
│    └─────────────┘  │Pimoroni │ │Whis │  │Speech  │         │
│                     │HAT Mini │ │play │  │Recog.  │         │
│                     └─────────┘ └─────┘  └────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Input Actions (Semantic Events)

Instead of physical button names, use **semantic actions**:

```python
class InputAction(Enum):
    """Semantic input actions independent of hardware."""
    SELECT = "select"       # Select/Confirm current item
    BACK = "back"           # Go back/Cancel
    UP = "up"               # Navigate up in lists
    DOWN = "down"           # Navigate down in lists
    LEFT = "left"           # Navigate left / Previous
    RIGHT = "right"         # Navigate right / Next
    MENU = "menu"           # Open menu
    PLAY_PAUSE = "play_pause"  # Toggle playback
    PTT_PRESS = "ptt_press"    # Push-to-talk pressed
    PTT_RELEASE = "ptt_release"  # Push-to-talk released
    VOICE_COMMAND = "voice_command"  # Voice command received (with data)
```

### 2. Input HAL (Abstract Interface)

```python
class InputHAL(ABC):
    """Abstract base class for all input adapters."""

    @abstractmethod
    def start(self) -> None:
        """Start input processing."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop input processing."""
        pass

    @abstractmethod
    def on_action(self, action: InputAction, callback: Callable[[Optional[Any]], None]) -> None:
        """
        Register callback for an input action.

        Args:
            action: Semantic action to listen for
            callback: Function to call when action occurs (receives optional data)
        """
        pass

    @abstractmethod
    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        pass

    def get_capabilities(self) -> List[InputAction]:
        """Return list of supported actions."""
        return []
```

### 3. Input Adapters

#### A. Four-Button Adapter (Pimoroni Display HAT Mini)

Maps physical buttons to semantic actions:

```python
class FourButtonInputAdapter(InputHAL):
    """Input adapter for 4-button interface (Pimoroni Display HAT Mini)."""

    DEFAULT_MAPPING = {
        Button.A: InputAction.SELECT,
        Button.B: InputAction.BACK,
        Button.X: InputAction.UP,
        Button.Y: InputAction.DOWN,
    }

    def __init__(self, display_device, button_mapping: Optional[Dict] = None):
        self.device = display_device
        self.mapping = button_mapping or self.DEFAULT_MAPPING
        self.callbacks: Dict[InputAction, List[Callable]] = defaultdict(list)
        self.button_handler = None  # Internal button polling

    def start(self):
        # Start button polling thread
        self.button_handler.start()

    def on_action(self, action: InputAction, callback: Callable):
        self.callbacks[action].append(callback)

    def _on_physical_button(self, button: Button):
        """Internal: Map physical button to semantic action."""
        action = self.mapping.get(button)
        if action:
            self._fire_action(action, None)
```

#### B. PTT Button Adapter (Whisplay HAT)

Single button for push-to-talk:

```python
class PTTInputAdapter(InputHAL):
    """Input adapter for single PTT button (Whisplay HAT)."""

    def __init__(self, whisplay_device):
        self.device = whisplay_device
        self.callbacks: Dict[InputAction, List[Callable]] = defaultdict(list)

    def start(self):
        # Register Whisplay button callback
        self.device.on_button_press(self._on_button_press)
        self.device.on_button_release(self._on_button_release)

    def _on_button_press(self):
        self._fire_action(InputAction.PTT_PRESS, None)

    def _on_button_release(self):
        self._fire_action(InputAction.PTT_RELEASE, None)

    def get_capabilities(self):
        return [InputAction.PTT_PRESS, InputAction.PTT_RELEASE]
```

#### C. Voice Input Adapter (Future)

Voice commands mapped to actions:

```python
class VoiceInputAdapter(InputHAL):
    """Input adapter for voice commands."""

    COMMAND_MAPPING = {
        "select": InputAction.SELECT,
        "back": InputAction.BACK,
        "up": InputAction.UP,
        "down": InputAction.DOWN,
        "play": InputAction.PLAY_PAUSE,
        "menu": InputAction.MENU,
    }

    def __init__(self, speech_recognizer):
        self.recognizer = speech_recognizer
        self.callbacks: Dict[InputAction, List[Callable]] = defaultdict(list)

    def start(self):
        self.recognizer.on_command(self._on_voice_command)

    def _on_voice_command(self, command: str):
        action = self.COMMAND_MAPPING.get(command.lower())
        if action:
            self._fire_action(action, {"command": command})
        else:
            # Generic voice command with data
            self._fire_action(InputAction.VOICE_COMMAND, {"command": command})
```

### 4. Input Manager (Coordinator)

Replaces the current `InputHandler`, coordinates multiple input sources:

```python
class InputManager:
    """
    Manages multiple input sources and dispatches actions.

    Can combine multiple input adapters (e.g., buttons + voice).
    """

    def __init__(self):
        self.adapters: List[InputHAL] = []
        self.callbacks: Dict[InputAction, List[Callable]] = defaultdict(list)

    def add_adapter(self, adapter: InputHAL):
        """Add an input adapter (buttons, voice, etc.)."""
        self.adapters.append(adapter)
        # Forward adapter callbacks to manager callbacks
        for action in InputAction:
            adapter.on_action(action, lambda data, a=action: self._fire_action(a, data))

    def on_action(self, action: InputAction, callback: Callable):
        """Register callback for an action."""
        self.callbacks[action].append(callback)

    def clear_callbacks(self):
        """Clear all callbacks and notify adapters."""
        self.callbacks.clear()
        for adapter in self.adapters:
            adapter.clear_callbacks()

    def start(self):
        """Start all adapters."""
        for adapter in self.adapters:
            adapter.start()

    def stop(self):
        """Stop all adapters."""
        for adapter in self.adapters:
            adapter.stop()

    def _fire_action(self, action: InputAction, data: Optional[Any]):
        """Fire all callbacks for an action."""
        for callback in self.callbacks.get(action, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in action callback: {e}")
```

### 5. Input Factory

Auto-detect and create appropriate input adapter:

```python
def get_input_manager(display_adapter, config: Dict) -> InputManager:
    """
    Create input manager with appropriate adapters based on hardware.

    Args:
        display_adapter: Display adapter to determine hardware
        config: Configuration dict

    Returns:
        Configured InputManager instance
    """
    manager = InputManager()

    # Determine hardware type
    adapter_name = display_adapter.__class__.__name__

    if adapter_name == "PimoroniDisplayAdapter":
        # 4-button interface
        display_device = getattr(display_adapter, 'device', None)
        button_adapter = FourButtonInputAdapter(display_device)
        manager.add_adapter(button_adapter)
        logger.info("Added 4-button input adapter (Pimoroni)")

    elif adapter_name == "WhisplayDisplayAdapter":
        # PTT button
        whisplay_device = getattr(display_adapter, 'device', None)
        ptt_adapter = PTTInputAdapter(whisplay_device)
        manager.add_adapter(ptt_adapter)
        logger.info("Added PTT input adapter (Whisplay)")

        # Optional: Add voice input for Whisplay
        if config.get('input', {}).get('enable_voice', False):
            voice_adapter = VoiceInputAdapter()
            manager.add_adapter(voice_adapter)
            logger.info("Added voice input adapter")

    return manager
```

---

## Updated ScreenManager

Decoupled from specific input hardware:

```python
class ScreenManager:
    """Manages screen navigation and transitions."""

    def __init__(self, display: Display, input_manager: Optional[InputManager] = None):
        self.display = display
        self.input_manager = input_manager
        self.current_screen: Optional[Screen] = None
        self.screen_stack: List[Screen] = []
        self.screens: Dict[str, Screen] = {}

    def push_screen(self, screen_name: str):
        if self.current_screen:
            self._disconnect_inputs()
            self.current_screen.exit()
            self.screen_stack.append(self.current_screen)

        self.current_screen = self.screens[screen_name]
        self.current_screen.enter()
        self._connect_inputs()
        self.current_screen.render()

    def _connect_inputs(self):
        """Connect input actions to current screen."""
        if not self.current_screen or not self.input_manager:
            return

        # Register semantic actions instead of physical buttons
        self.input_manager.on_action(InputAction.SELECT, self.current_screen.on_select)
        self.input_manager.on_action(InputAction.BACK, self.current_screen.on_back)
        self.input_manager.on_action(InputAction.UP, self.current_screen.on_up)
        self.input_manager.on_action(InputAction.DOWN, self.current_screen.on_down)
        self.input_manager.on_action(InputAction.LEFT, self.current_screen.on_left)
        self.input_manager.on_action(InputAction.RIGHT, self.current_screen.on_right)
        self.input_manager.on_action(InputAction.PTT_PRESS, self.current_screen.on_ptt_press)
        self.input_manager.on_action(InputAction.PTT_RELEASE, self.current_screen.on_ptt_release)
        self.input_manager.on_action(InputAction.VOICE_COMMAND, self.current_screen.on_voice_command)

        logger.debug(f"Connected input actions for {self.current_screen.name}")

    def _disconnect_inputs(self):
        """Disconnect input actions."""
        if not self.input_manager:
            return

        self.input_manager.clear_callbacks()
        logger.debug(f"Disconnected input actions")
```

---

## Updated Screen Base Class

Semantic action handlers instead of physical buttons:

```python
class Screen(ABC):
    """Base class for all UI screens."""

    def __init__(self, display: Display, context: Optional['AppContext'] = None, name: str = "Screen"):
        self.display = display
        self.context = context
        self.name = name
        self.screen_manager: Optional['ScreenManager'] = None

    @abstractmethod
    def render(self) -> None:
        """Render the screen content."""
        pass

    def enter(self) -> None:
        """Called when screen becomes active."""
        logger.info(f"Entering screen: {self.name}")

    def exit(self) -> None:
        """Called when screen becomes inactive."""
        logger.info(f"Exiting screen: {self.name}")

    # ===== SEMANTIC ACTION HANDLERS =====
    # Screens override these based on their functionality

    def on_select(self, data: Optional[Any] = None) -> None:
        """Handle SELECT action (confirm/accept)."""
        pass

    def on_back(self, data: Optional[Any] = None) -> None:
        """Handle BACK action (cancel/return)."""
        pass

    def on_up(self, data: Optional[Any] = None) -> None:
        """Handle UP action (navigate up)."""
        pass

    def on_down(self, data: Optional[Any] = None) -> None:
        """Handle DOWN action (navigate down)."""
        pass

    def on_left(self, data: Optional[Any] = None) -> None:
        """Handle LEFT action (navigate left/previous)."""
        pass

    def on_right(self, data: Optional[Any] = None) -> None:
        """Handle RIGHT action (navigate right/next)."""
        pass

    def on_ptt_press(self, data: Optional[Any] = None) -> None:
        """Handle PTT button press."""
        pass

    def on_ptt_release(self, data: Optional[Any] = None) -> None:
        """Handle PTT button release."""
        pass

    def on_voice_command(self, data: Optional[Any] = None) -> None:
        """Handle voice command with data dict."""
        pass
```

---

## File Structure

```
yoyopy/ui/
├── adapters/
│   ├── display_pimoroni.py      # Existing
│   ├── display_whisplay.py      # Existing
│   └── __init__.py
│
├── input/                        # NEW: Input HAL module
│   ├── __init__.py
│   ├── input_hal.py              # Abstract InputHAL base class + InputAction enum
│   ├── input_manager.py          # InputManager coordinator
│   ├── input_factory.py          # Factory function + auto-detection
│   │
│   └── adapters/                 # Input adapter implementations
│       ├── __init__.py
│       ├── four_button.py        # FourButtonInputAdapter (Pimoroni)
│       ├── ptt_button.py         # PTTInputAdapter (Whisplay)
│       └── voice.py              # VoiceInputAdapter (future)
│
├── display_hal.py                # Existing
├── display_factory.py            # Existing
├── display.py                    # Existing
├── screen_manager.py             # UPDATED: Use InputManager
├── screens.py                    # UPDATED: Semantic action handlers
└── input_handler.py              # DEPRECATED: To be removed
```

---

## Migration Strategy

### Phase 1: Create Input HAL Infrastructure ✅

**Goal:** Implement core input abstraction without breaking existing code

**Tasks:**
1. Create `yoyopy/ui/input/` module structure
2. Implement `InputHAL` abstract base class
3. Implement `InputAction` enum with all semantic actions
4. Implement `InputManager` coordinator
5. Implement `InputFactory` with auto-detection
6. Create adapter implementations:
   - `FourButtonInputAdapter` (wraps existing button logic)
   - `PTTInputAdapter` (for Whisplay button)
7. Add unit tests for input adapters

**Files to create:**
- `yoyopy/ui/input/__init__.py`
- `yoyopy/ui/input/input_hal.py`
- `yoyopy/ui/input/input_manager.py`
- `yoyopy/ui/input/input_factory.py`
- `yoyopy/ui/input/adapters/__init__.py`
- `yoyopy/ui/input/adapters/four_button.py`
- `yoyopy/ui/input/adapters/ptt_button.py`

**Validation:**
- Input adapters can be created independently
- `InputManager` can coordinate multiple adapters
- Factory correctly detects and creates adapters

---

### Phase 2: Update ScreenManager ✅

**Goal:** Decouple ScreenManager from InputHandler

**Tasks:**
1. Update `ScreenManager.__init__()` to accept `InputManager` instead of `InputHandler`
2. Update `_connect_inputs()` to register semantic actions
3. Update `_disconnect_inputs()` to clear via InputManager
4. Add backward compatibility check (allow None input_manager)
5. Update app.py to create InputManager via factory

**Files to modify:**
- `yoyopy/ui/screen_manager.py`
- `yoyopy/app.py`

**Validation:**
- ScreenManager works with InputManager
- No references to physical buttons in ScreenManager
- App initializes correctly with new InputManager

---

### Phase 3: Update Screen Classes ✅

**Goal:** Replace physical button handlers with semantic actions

**Tasks:**
1. Update `Screen` base class:
   - Add semantic action handlers (`on_select`, `on_back`, `on_up`, etc.)
   - Mark old button handlers as deprecated
2. Update all screen implementations:
   - **MenuScreen**: Map `on_button_a` → `on_select`, `on_button_b` → `on_back`, etc.
   - **NowPlayingScreen**: Map actions
   - **PlaylistScreen**: Map actions
   - **ContactListScreen**: Map actions
   - **CallScreen**: Map actions
   - **IncomingCallScreen**: Map actions
   - **OutgoingCallScreen**: Map actions
   - **InCallScreen**: Map actions
3. Add PTT/voice handlers where appropriate (e.g., CallScreen)

**Files to modify:**
- `yoyopy/ui/screens.py` (all screen classes)

**Example migration:**
```python
# OLD (Pimoroni-specific)
class MenuScreen(Screen):
    def on_button_a(self):  # "A" button = Select
        self.select_item()

    def on_button_b(self):  # "B" button = Back
        self.screen_manager.pop_screen()

    def on_button_x(self):  # "X" button = Up
        self.move_cursor(-1)

    def on_button_y(self):  # "Y" button = Down
        self.move_cursor(1)

# NEW (Hardware-agnostic)
class MenuScreen(Screen):
    def on_select(self, data=None):  # Works with button, voice, etc.
        self.select_item()

    def on_back(self, data=None):
        self.screen_manager.pop_screen()

    def on_up(self, data=None):
        self.move_cursor(-1)

    def on_down(self, data=None):
        self.move_cursor(1)

    def on_voice_command(self, data=None):
        # Future: "Select playlists" -> navigate to playlists
        command = data.get('command', '')
        if 'playlist' in command.lower():
            self.screen_manager.push_screen('playlists')
```

**Validation:**
- All screens work with 4-button input (Pimoroni)
- All screens work with PTT input (Whisplay) where applicable
- No references to `on_button_a/b/x/y` in active code

---

### Phase 4: Testing & Validation ✅

**Goal:** Ensure all input methods work correctly

**Tasks:**
1. Test on Pimoroni Display HAT Mini (4 buttons)
2. Test on Whisplay HAT (PTT button)
3. Test input manager with multiple adapters
4. Test voice input (if implemented)
5. Integration testing with full YoyoPod app

**Test scenarios:**
- Menu navigation with buttons
- List scrolling with up/down
- PTT for voice recording (future)
- Voice commands for navigation (future)
- Mixed input (buttons + voice)

---

### Phase 5: Cleanup ✅

**Goal:** Remove deprecated code

**Tasks:**
1. Remove old `InputHandler` class (`yoyopy/ui/input_handler.py`)
2. Remove deprecated button handler methods from screens
3. Update documentation
4. Update `.claude/CLAUDE.md` with new architecture

**Files to remove:**
- `yoyopy/ui/input_handler.py`

**Files to update:**
- `.claude/CLAUDE.md`
- `docs/SYSTEM_ARCHITECTURE.md` (if exists)
- README.md (update architecture diagrams)

---

## Configuration

Add input configuration to `yoyopod_config.yaml`:

```yaml
# Input Settings
input:
  # Primary input method (auto-detect by default)
  primary: "auto"  # auto, four_button, ptt, voice

  # Enable voice input (requires microphone)
  enable_voice: false

  # Voice command settings
  voice:
    language: "en-US"
    sensitivity: "medium"  # low, medium, high
    wake_word: "yoyo"      # Optional wake word

  # Button mapping (for 4-button interfaces)
  button_mapping:
    A: "select"
    B: "back"
    X: "up"
    Y: "down"

  # PTT settings
  ptt:
    long_press_threshold: 0.5  # seconds
    enable_voice_on_press: true
```

---

## Benefits of This Architecture

### 1. Hardware Independence
- Screens don't care about physical buttons
- Easy to swap input methods (buttons → voice → gamepad)
- Same screen code works on different hardware

### 2. Semantic Clarity
- `on_select()` is clearer than `on_button_a()`
- Actions have meaning (SELECT, BACK) not labels (A, B)
- Easier for developers to understand intent

### 3. Extensibility
- Add new input methods without changing screens
- Support multiple simultaneous inputs (buttons + voice)
- Easy to add touch, gamepad, remote control, etc.

### 4. Flexibility
- Customize button mappings per device
- Different screen contexts can handle same action differently
- Voice commands can trigger any action

### 5. Testability
- Mock input actions easily in tests
- No dependency on physical hardware
- Simulate complex input scenarios

### 6. Consistency with Display HAL
- Same architectural pattern as Display HAL
- Unified approach to hardware abstraction
- Easy to understand for developers familiar with Display HAL

---

## Example: PTT + Voice Integration

With this architecture, Whisplay HAT can use PTT + voice naturally:

```python
class MenuScreen(Screen):
    """Menu screen with PTT voice navigation."""

    def on_ptt_press(self, data=None):
        """Start voice recording when PTT pressed."""
        self.display.text("Listening...", 10, 260, color=self.display.COLOR_GREEN)
        self.display.update()
        # Start voice recognition

    def on_ptt_release(self, data=None):
        """Process voice command when PTT released."""
        self.display.text("Processing...", 10, 260, color=self.display.COLOR_YELLOW)
        self.display.update()
        # Stop recording, process command

    def on_voice_command(self, data=None):
        """Handle recognized voice command."""
        command = data.get('command', '').lower()

        if 'music' in command or 'playlist' in command:
            self.screen_manager.push_screen('playlists')
        elif 'call' in command or 'contact' in command:
            self.screen_manager.push_screen('contacts')
        elif 'back' in command or 'return' in command:
            self.screen_manager.pop_screen()
        else:
            self.display.text(f"Unknown: {command}", 10, 260, color=self.display.COLOR_RED)
            self.display.update()
```

---

## Recommended Implementation Order

1. **Phase 1** - Create Input HAL infrastructure (non-breaking)
2. **Phase 2** - Update ScreenManager to use InputManager
3. **Phase 3** - Migrate screens to semantic actions
4. **Test on hardware** - Validate both Pimoroni and Whisplay
5. **Phase 4** - Testing & validation
6. **Phase 5** - Cleanup deprecated code

**Estimated effort:** 4-6 hours for Phases 1-3, 2-3 hours for testing/cleanup

---

## Open Questions

1. **Voice activation:** Use PTT only, or add wake word detection?
2. **Multi-touch:** Add touch screen support for future displays?
3. **Gesture input:** Support accelerometer gestures (shake, tilt)?
4. **Haptic feedback:** Add vibration/LED feedback for input actions?
5. **Input history:** Track input sequence for shortcuts (e.g., double-back = exit app)?

---

## Conclusion

This Input HAL architecture provides a **clean, extensible, and hardware-agnostic** way to handle user input in YoyoPod. It follows the same successful pattern as the Display HAL and positions the codebase for future enhancements (voice, touch, gamepad, etc.) without major refactoring.

**Next Step:** Review this proposal and approve for implementation.

---

**END OF PROPOSAL**

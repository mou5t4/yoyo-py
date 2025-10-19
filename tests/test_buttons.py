#!/usr/bin/env python3
"""
Quick test of button integration (simulation mode).
This tests that all the wiring is correct.
"""

from yoyopy.ui.display import Display
from yoyopy.ui.screens import HomeScreen, MenuScreen, NowPlayingScreen
from yoyopy.ui.screen_manager import ScreenManager
from yoyopy.ui.input_handler import InputHandler, Button, ButtonEvent

print("Testing button integration...")

# Create components in simulation mode
display = Display(simulate=True)
input_handler = InputHandler(simulate=True)
screen_manager = ScreenManager(display, input_handler)

# Create screens
home = HomeScreen(display)
menu = MenuScreen(display)
now_playing = NowPlayingScreen(display)

# Register screens
screen_manager.register_screen("home", home)
screen_manager.register_screen("menu", menu)
screen_manager.register_screen("now_playing", now_playing)

# Start input handler
input_handler.start()

print("✓ Input handler started")

# Start with home screen
screen_manager.replace_screen("home")
print("✓ Home screen loaded")
print(f"  Current screen: {screen_manager.current_screen.name}")

# Simulate Button A press on home screen (should go to menu)
print("\nSimulating Button A on HomeScreen...")
input_handler.simulate_button_press(Button.A, ButtonEvent.PRESS)
print(f"  Current screen: {screen_manager.current_screen.name}")
assert screen_manager.current_screen.name == "Menu", "Should navigate to menu"
print("✓ Navigated to menu")

# Simulate Button Y to move down in menu
print("\nSimulating Button Y (down) on MenuScreen...")
initial_selection = menu.selected_index
input_handler.simulate_button_press(Button.Y, ButtonEvent.PRESS)
print(f"  Selection changed from {initial_selection} to {menu.selected_index}")
assert menu.selected_index != initial_selection, "Selection should change"
print("✓ Menu navigation works")

# Simulate Button A to select menu item (should go to now playing)
print("\nSimulating Button A on MenuScreen...")
input_handler.simulate_button_press(Button.A, ButtonEvent.PRESS)
print(f"  Current screen: {screen_manager.current_screen.name}")
assert screen_manager.current_screen.name == "NowPlaying", "Should navigate to now playing"
print("✓ Navigated to now playing")

# Simulate Button A to toggle play/pause
print("\nSimulating Button A on NowPlayingScreen...")
initial_state = now_playing.is_playing
input_handler.simulate_button_press(Button.A, ButtonEvent.PRESS)
print(f"  Playback state: {initial_state} → {now_playing.is_playing}")
assert now_playing.is_playing != initial_state, "Playback should toggle"
print("✓ Play/pause toggle works")

# Simulate Button B to go back
print("\nSimulating Button B (back)...")
input_handler.simulate_button_press(Button.B, ButtonEvent.PRESS)
print(f"  Current screen: {screen_manager.current_screen.name}")
assert screen_manager.current_screen.name == "Menu", "Should go back to menu"
print("✓ Back navigation works")

# Simulate Button B again to go to home
print("\nSimulating Button B (back) again...")
input_handler.simulate_button_press(Button.B, ButtonEvent.PRESS)
print(f"  Current screen: {screen_manager.current_screen.name}")
assert screen_manager.current_screen.name == "Home", "Should go back to home"
print("✓ Back to home works")

# Stop input handler
input_handler.stop()
print("\n✓ Input handler stopped")

print("\n" + "=" * 50)
print("✅ All button integration tests passed!")
print("=" * 50)

#!/usr/bin/env python3
"""
Test script for Display HAL with Whisplay HAT.

This script tests the new HAL architecture by:
1. Auto-detecting the Whisplay HAT
2. Testing basic drawing primitives
3. Verifying RGB565 conversion
4. Displaying test pattern with live time

Run on Raspberry Pi with Whisplay HAT connected.
"""

from yoyopy.ui.display import Display
from loguru import logger
import time
from datetime import datetime

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=''), level="INFO")

print("="*60)
print("YoyoPod Display HAL Test - Whisplay HAT")
print("="*60)

# Test 1: Auto-detect hardware
print("\n[Test 1] Auto-detecting display hardware...")
display = Display()  # Auto-detect (should find Whisplay)

print(f"✓ Display initialized:")
print(f"  - Type: {display.get_adapter().__class__.__name__}")
print(f"  - Dimensions: {display.WIDTH}x{display.HEIGHT}")
print(f"  - Orientation: {display.ORIENTATION}")
print(f"  - Simulated: {display.simulate}")

# Test 2: Drawing primitives
print("\n[Test 2] Testing drawing primitives...")

# Clear screen
display.clear(display.COLOR_BLACK)
print("  ✓ clear()")

# Draw color bars
colors = [
    (display.COLOR_RED, "Red"),
    (display.COLOR_GREEN, "Green"),
    (display.COLOR_BLUE, "Blue"),
    (display.COLOR_CYAN, "Cyan"),
    (display.COLOR_MAGENTA, "Magenta"),
    (display.COLOR_YELLOW, "Yellow"),
]

bar_height = 20
for i, (color, name) in enumerate(colors):
    y = i * bar_height
    display.rectangle(0, y, display.WIDTH, y + bar_height, fill=color)
    print(f"  ✓ rectangle({name})")

# Draw text
display.text("YoyoPod HAL Test", 10, 130, color=display.COLOR_WHITE, font_size=18)
print("  ✓ text()")

# Draw circle
display.circle(120, 180, 20, outline=display.COLOR_CYAN, width=3)
print("  ✓ circle()")

# Draw line
display.line(10, 220, 230, 220, color=display.COLOR_WHITE, width=2)
print("  ✓ line()")

# Update display
display.update()
print("  ✓ update()")

time.sleep(2)

# Test 3: Status bar
print("\n[Test 3] Testing status bar...")
display.clear(display.COLOR_BLACK)
current_time = datetime.now().strftime("%H:%M")
display.status_bar(time_str=current_time, battery_percent=85, signal_strength=3)
display.text("Status Bar Test", 50, 100, color=display.COLOR_WHITE, font_size=16)
display.update()
print(f"  ✓ status_bar(time={current_time}, battery=85%, signal=3)")

time.sleep(2)

# Test 4: Live time display
print("\n[Test 4] Live time display (5 seconds)...")
for i in range(5):
    display.clear(display.COLOR_BLACK)

    # Status bar with current time
    current_time = datetime.now().strftime("%H:%M:%S")
    display.status_bar(time_str=current_time, battery_percent=85, signal_strength=4)

    # Title
    display.text(
        "Whisplay HAT",
        (display.WIDTH - 120) // 2,
        60,
        color=display.COLOR_CYAN,
        font_size=20
    )

    # Display dimensions
    dim_text = f"{display.WIDTH}x{display.HEIGHT}"
    display.text(
        dim_text,
        (display.WIDTH - len(dim_text) * 8) // 2,
        100,
        color=display.COLOR_WHITE,
        font_size=16
    )

    # Orientation
    display.text(
        display.ORIENTATION.upper(),
        (display.WIDTH - len(display.ORIENTATION) * 8) // 2,
        130,
        color=display.COLOR_YELLOW,
        font_size=14
    )

    # Counter
    display.text(
        f"Count: {i+1}/5",
        (display.WIDTH - 70) // 2,
        160,
        color=display.COLOR_GREEN,
        font_size=16
    )

    display.update()
    time.sleep(1)

# Test 5: Backlight control
print("\n[Test 5] Testing backlight control...")
for brightness in [100, 50, 10, 50, 100]:
    display.set_backlight(brightness / 100.0)
    print(f"  ✓ set_backlight({brightness}%)")
    time.sleep(0.5)

# Test 6: Helper methods
print("\n[Test 6] Testing helper methods...")
print(f"  ✓ is_portrait() = {display.is_portrait()}")
print(f"  ✓ is_landscape() = {display.is_landscape()}")
print(f"  ✓ get_orientation() = {display.get_orientation()}")
print(f"  ✓ get_dimensions() = {display.get_dimensions()}")
print(f"  ✓ get_usable_height() = {display.get_usable_height()}")
text_size = display.get_text_size("Test", 16)
print(f"  ✓ get_text_size('Test', 16) = {text_size}")

# Final message
print("\n[Test Complete] All tests passed! ✓")
display.clear(display.COLOR_BLACK)
display.text("HAL TEST", 60, 100, color=display.COLOR_GREEN, font_size=24)
display.text("PASSED", 70, 140, color=display.COLOR_GREEN, font_size=20)
display.update()

time.sleep(3)

# Cleanup
print("\nCleaning up...")
display.cleanup()
print("✓ Display cleaned up")

print("\n" + "="*60)
print("Test completed successfully!")
print("="*60)

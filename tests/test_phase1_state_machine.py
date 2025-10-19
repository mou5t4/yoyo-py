#!/usr/bin/env python3
"""
Test Phase 1 State Machine Enhancements

Validates that the new VoIP + music integration states and transitions
work correctly without requiring hardware.
"""

import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

from yoyopy.app_context import AppContext
from yoyopy.state_machine import StateMachine, AppState


def test_state_machine():
    """Test state machine with new Phase 5 states."""
    logger.info("=" * 60)
    logger.info("Testing Phase 5 State Machine Enhancements")
    logger.info("=" * 60)

    # Initialize
    context = AppContext()
    sm = StateMachine(context)

    logger.info(f"\n✓ Initial state: {sm.get_state_name()}")

    # Test 1: Music playback with VoIP ready
    logger.info("\n--- Test 1: Music Playback with VoIP Ready ---")
    assert sm.transition_to(AppState.MENU, "open_menu"), "Failed to go to MENU"
    logger.info(f"  State: {sm.get_state_name()}")

    assert sm.transition_to(AppState.PLAYING_WITH_VOIP, "select_media_with_voip"), \
        "Failed to start music with VoIP"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_playing_with_voip(), "Should be in PLAYING_WITH_VOIP"
    assert sm.is_music_playing(), "Should report music playing"
    logger.info("  ✓ Music playing with VoIP ready")

    # Test 2: Incoming call pauses music
    logger.info("\n--- Test 2: Incoming Call Pauses Music ---")
    assert sm.transition_to(AppState.PAUSED_BY_CALL, "auto_pause_for_call"), \
        "Failed to auto-pause for call"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_music_paused_by_call(), "Should be paused by call"
    logger.info("  ✓ Music auto-paused for call")

    assert sm.transition_to(AppState.CALL_INCOMING, "incoming_call_ringing"), \
        "Failed to transition to CALL_INCOMING"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_in_call(), "Should be in call state"
    logger.info("  ✓ Incoming call ringing")

    # Test 3: Answer call with music paused
    logger.info("\n--- Test 3: Answer Call (Music Paused in Background) ---")
    assert sm.transition_to(AppState.CALL_ACTIVE_MUSIC_PAUSED, "answer_call_resume_after"), \
        "Failed to answer call"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_in_call(), "Should still be in call"
    assert sm.has_paused_music_for_call(), "Should have paused music"
    logger.info("  ✓ In active call with music paused")

    # Test 4: Call ends, music auto-resumes
    logger.info("\n--- Test 4: Call Ends, Music Auto-Resumes ---")
    assert sm.transition_to(AppState.PLAYING_WITH_VOIP, "call_ended_auto_resume"), \
        "Failed to auto-resume music"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_playing_with_voip(), "Should be back to playing with VoIP"
    assert sm.is_music_playing(), "Music should be playing"
    logger.info("  ✓ Music auto-resumed after call")

    # Test 5: Call ends, music stays paused
    logger.info("\n--- Test 5: Alternative Flow - Call Ends, Music Stays Paused ---")
    # Start from music playing again
    assert sm.transition_to(AppState.PAUSED_BY_CALL, "auto_pause_for_call"), \
        "Failed to pause for call"
    assert sm.transition_to(AppState.CALL_INCOMING, "incoming_call_ringing"), \
        "Failed to ring"
    assert sm.transition_to(AppState.CALL_ACTIVE_MUSIC_PAUSED, "answer_call_resume_after"), \
        "Failed to answer"
    logger.info(f"  State: {sm.get_state_name()}")

    # End call but stay paused
    assert sm.transition_to(AppState.PAUSED, "call_ended_stay_paused"), \
        "Failed to stay paused"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.current_state == AppState.PAUSED, "Should be in PAUSED state"
    logger.info("  ✓ Music stayed paused after call (user preference)")

    # Test 6: Outgoing call from music screen
    logger.info("\n--- Test 6: Outgoing Call from Music Screen ---")
    assert sm.transition_to(AppState.PLAYING_WITH_VOIP, "resume"), \
        "Failed to resume music"
    assert sm.transition_to(AppState.CALL_OUTGOING, "make_call_pause_music"), \
        "Failed to make outgoing call"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.is_in_call(), "Should be in call state"
    logger.info("  ✓ Outgoing call initiated")

    assert sm.transition_to(AppState.CALL_ACTIVE_MUSIC_PAUSED, "call_connected_music_paused"), \
        "Failed to connect call"
    logger.info(f"  State: {sm.get_state_name()}")
    assert sm.has_paused_music_for_call(), "Should have paused music for call"
    logger.info("  ✓ Outgoing call connected")

    # Test 7: Invalid transitions should fail
    logger.info("\n--- Test 7: Invalid Transitions ---")
    current = sm.current_state
    # Try to go directly to IDLE from CALL_ACTIVE_MUSIC_PAUSED (should fail)
    result = sm.transition_to(AppState.IDLE, "invalid_trigger")
    assert not result, "Should reject invalid transition"
    assert sm.current_state == current, "State should not change on invalid transition"
    logger.info("  ✓ Invalid transitions correctly rejected")

    # Test 8: State helper methods
    logger.info("\n--- Test 8: State Helper Methods ---")
    sm.transition_to(AppState.PLAYING_WITH_VOIP, "call_ended_auto_resume")
    assert sm.is_playing_with_voip(), "is_playing_with_voip() should work"
    assert sm.is_music_playing(), "is_music_playing() should work"
    assert not sm.is_music_paused_by_call(), "is_music_paused_by_call() should be False"
    assert not sm.is_in_call(), "is_in_call() should be False"
    logger.info("  ✓ Helper methods work correctly")

    logger.info("\n" + "=" * 60)
    logger.info("✓ ALL TESTS PASSED!")
    logger.info("=" * 60)
    logger.info("\nPhase 1 State Machine:")
    logger.info("  ✓ New states: PLAYING_WITH_VOIP, PAUSED_BY_CALL, CALL_ACTIVE_MUSIC_PAUSED")
    logger.info("  ✓ New transitions: Call interruption flows")
    logger.info("  ✓ Helper methods: State checking utilities")
    logger.info("\nReady for Phase 2: Screen Integration")
    logger.info("")


if __name__ == "__main__":
    try:
        test_state_machine()
        sys.exit(0)
    except AssertionError as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

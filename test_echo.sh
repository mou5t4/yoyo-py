#!/bin/bash
#
# Test VoIP echo service to diagnose one-way audio issue
#
# This script will:
# 1. Kill any existing linphonec processes
# 2. Start linphonec with debug output
# 3. Call the echo test service
# 4. Monitor for audio stream information
#

echo "========================================"
echo "VoIP Echo Test - Audio Diagnostics"
echo "========================================"
echo ""

# Kill existing linphonec
echo "[1/5] Killing existing linphonec processes..."
killall linphonec 2>/dev/null
sleep 2

# Check if linphonec is available
if [ ! -f /usr/bin/linphonec ]; then
    echo "ERROR: linphonec not found at /usr/bin/linphonec"
    exit 1
fi

echo "[2/5] Starting linphonec with debug logging..."
echo ""
echo "When linphonec starts, follow these steps:"
echo "  1. Wait for registration (should see 'Registration successful')"
echo "  2. Type: call sip:echo@sip.linphone.org"
echo "  3. Wait for connection"
echo "  4. SPEAK into the microphone"
echo "  5. Listen - you should hear your voice back"
echo "  6. Type: terminate (to end call)"
echo "  7. Type: quit (to exit)"
echo ""
echo "Look for these key messages in the output:"
echo "  - 'Audio stream running' - indicates audio is being processed"
echo "  - 'RTP' messages - shows network audio packets"
echo "  - 'Starting audio playback' - should see this for incoming audio"
echo ""
read -p "Press ENTER to start linphonec..." dummy

# Start linphonec with increased debug level
/usr/bin/linphonec -d 8

"""
VoIP Manager for YoyoPod using Linphone.

Provides SIP/VoIP calling capability by interfacing with linphonec CLI.
Handles registration, call management, and status monitoring.
"""

import subprocess
import threading
import time
from enum import Enum
from typing import Optional, Callable, List
from dataclasses import dataclass
from loguru import logger


class RegistrationState(Enum):
    """SIP registration states."""
    NONE = "none"
    PROGRESS = "progress"
    OK = "ok"
    CLEARED = "cleared"
    FAILED = "failed"


class CallState(Enum):
    """Call states."""
    IDLE = "idle"
    INCOMING = "incoming"
    OUTGOING = "outgoing_init"
    OUTGOING_PROGRESS = "outgoing_progress"
    OUTGOING_RINGING = "outgoing_ringing"
    OUTGOING_EARLY_MEDIA = "outgoing_early_media"
    CONNECTED = "connected"
    STREAMS_RUNNING = "streams_running"
    PAUSED = "paused"
    PAUSED_BY_REMOTE = "paused_by_remote"
    UPDATED_BY_REMOTE = "updated_by_remote"
    RELEASED = "released"
    ERROR = "error"
    END = "end"


@dataclass
class VoIPConfig:
    """VoIP configuration."""
    sip_server: str = "sip.linphone.org"
    sip_username: str = ""
    sip_password: str = ""
    sip_identity: str = ""  # sip:username@server
    transport: str = "tcp"  # tcp, udp, tls
    stun_server: str = ""
    linphonec_path: str = "/usr/bin/linphonec"


class VoIPManager:
    """
    VoIP Manager using Linphone CLI.

    Manages SIP registration and call handling through linphonec subprocess.
    """

    def __init__(self, config: VoIPConfig) -> None:
        """
        Initialize VoIP manager.

        Args:
            config: VoIP configuration
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.registered = False
        self.registration_state = RegistrationState.NONE
        self.call_state = CallState.IDLE
        self.current_call_id: Optional[str] = None

        # Callbacks
        self.registration_callbacks: List[Callable[[RegistrationState], None]] = []
        self.call_state_callbacks: List[Callable[[CallState], None]] = []

        # Monitor thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_event = threading.Event()

        logger.info(f"VoIPManager initialized (server: {config.sip_server})")

    def start(self) -> bool:
        """
        Start linphonec process and begin monitoring.

        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("VoIP manager already running")
            return True

        try:
            logger.info("Starting linphonec...")

            # Start linphonec in daemon mode with pipe interface
            self.process = subprocess.Popen(
                [self.config.linphonec_path, "-d", "6"],  # -d 6 = debug level
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            self.running = True

            # Start monitor thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_output,
                daemon=True
            )
            self.monitor_thread.start()

            logger.info("Linphonec started successfully")

            # Give it a moment to initialize
            time.sleep(1)

            # Check registration status
            self._send_command("status register")

            return True

        except Exception as e:
            logger.error(f"Failed to start linphonec: {e}")
            self.running = False
            return False

    def stop(self) -> None:
        """Stop linphonec process and monitoring."""
        if not self.running:
            return

        logger.info("Stopping VoIP manager...")

        self.running = False
        self.monitor_event.set()

        # Terminate linphonec
        if self.process:
            try:
                self._send_command("quit")
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception as e:
                logger.error(f"Error stopping linphonec: {e}")
            finally:
                self.process = None

        # Wait for monitor thread
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            self.monitor_thread = None

        logger.info("VoIP manager stopped")

    def _send_command(self, command: str) -> bool:
        """
        Send command to linphonec.

        Args:
            command: Command to send

        Returns:
            True if command sent successfully
        """
        if not self.process or not self.process.stdin:
            logger.error("Cannot send command: linphonec not running")
            return False

        try:
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()
            logger.debug(f"Sent command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            return False

    def _monitor_output(self) -> None:
        """Monitor linphonec output for events."""
        logger.debug("Output monitor started")

        while self.running and self.process:
            try:
                if not self.process.stdout:
                    break

                line = self.process.stdout.readline()
                if not line:
                    if self.process.poll() is not None:
                        logger.warning("Linphonec process terminated")
                        self.running = False
                        break
                    continue

                line = line.strip()
                if line:
                    self._parse_output(line)

            except Exception as e:
                logger.error(f"Error monitoring output: {e}")
                break

        logger.debug("Output monitor stopped")

    def _parse_output(self, line: str) -> None:
        """
        Parse linphonec output line.

        Args:
            line: Output line to parse
        """
        logger.debug(f"Linphone: {line}")

        # Parse registration state
        if "Registration on" in line and "successful" in line:
            self._update_registration_state(RegistrationState.OK)
        elif "Registration on" in line and "failed" in line:
            self._update_registration_state(RegistrationState.FAILED)
        elif "Registration on" in line and "cleared" in line:
            self._update_registration_state(RegistrationState.CLEARED)
        elif "Refreshing" in line and "registration" in line:
            logger.debug("Registration refresh in progress")

        # Parse call state
        if "Call" in line:
            if "incoming" in line.lower():
                self._update_call_state(CallState.INCOMING)
            elif "outgoing" in line.lower():
                self._update_call_state(CallState.OUTGOING)
            elif "connected" in line.lower():
                self._update_call_state(CallState.CONNECTED)
            elif "released" in line.lower() or "ended" in line.lower():
                self._update_call_state(CallState.RELEASED)
                self.current_call_id = None

    def _update_registration_state(self, state: RegistrationState) -> None:
        """
        Update registration state and fire callbacks.

        Args:
            state: New registration state
        """
        if state != self.registration_state:
            old_state = self.registration_state
            self.registration_state = state
            self.registered = (state == RegistrationState.OK)

            logger.info(f"Registration state: {old_state.value} -> {state.value}")

            for callback in self.registration_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in registration callback: {e}")

    def _update_call_state(self, state: CallState) -> None:
        """
        Update call state and fire callbacks.

        Args:
            state: New call state
        """
        if state != self.call_state:
            old_state = self.call_state
            self.call_state = state

            logger.info(f"Call state: {old_state.value} -> {state.value}")

            for callback in self.call_state_callbacks:
                try:
                    callback(state)
                except Exception as e:
                    logger.error(f"Error in call state callback: {e}")

    def make_call(self, sip_address: str) -> bool:
        """
        Initiate outgoing call.

        Args:
            sip_address: SIP address to call (e.g., sip:user@domain)

        Returns:
            True if call initiated successfully
        """
        if not self.registered:
            logger.error("Cannot make call: not registered")
            return False

        logger.info(f"Making call to: {sip_address}")
        return self._send_command(f"call {sip_address}")

    def answer_call(self) -> bool:
        """
        Answer incoming call.

        Returns:
            True if answered successfully
        """
        logger.info("Answering call")
        return self._send_command("answer")

    def hangup(self) -> bool:
        """
        Hangup current call.

        Returns:
            True if hangup command sent successfully
        """
        logger.info("Hanging up call")
        return self._send_command("terminate")

    def get_status(self) -> dict:
        """
        Get current VoIP status.

        Returns:
            Status dictionary
        """
        return {
            "running": self.running,
            "registered": self.registered,
            "registration_state": self.registration_state.value,
            "call_state": self.call_state.value,
            "call_id": self.current_call_id,
            "sip_identity": self.config.sip_identity
        }

    def on_registration_change(self, callback: Callable[[RegistrationState], None]) -> None:
        """
        Register callback for registration state changes.

        Args:
            callback: Function to call on state change
        """
        self.registration_callbacks.append(callback)

    def on_call_state_change(self, callback: Callable[[CallState], None]) -> None:
        """
        Register callback for call state changes.

        Args:
            callback: Function to call on state change
        """
        self.call_state_callbacks.append(callback)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop()
        logger.info("VoIP manager cleaned up")

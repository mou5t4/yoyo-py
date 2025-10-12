"""
Connectivity module for YoyoPod.
Manages 4G/LTE connection, WiFi fallback, network status, and VoIP calling.
"""

from yoyopy.connectivity.voip_manager import (
    VoIPManager,
    VoIPConfig,
    RegistrationState,
    CallState
)

__all__ = [
    'VoIPManager',
    'VoIPConfig',
    'RegistrationState',
    'CallState'
]

"""
data/__init__.py
=================
Makes the data/ directory a Python package.
Exports all public data constants for easy importing.

Example:
    from data import BASE_DICTIONARY, LANGUAGE_MAP, TTS_LANGUAGE_MAP

Author: Yaswin Raj M
Project: Google Prompt War Hackathon — Multilingual Electoral AI
"""

from data.electoral_data import (
    BASE_DICTIONARY,
    LANGUAGE_MAP,
    TTS_LANGUAGE_MAP,
    ELECTION_PHASES,
    SUPPORTED_LANGUAGES,
)

__all__ = [
    "BASE_DICTIONARY",
    "LANGUAGE_MAP",
    "TTS_LANGUAGE_MAP",
    "ELECTION_PHASES",
    "SUPPORTED_LANGUAGES",
]

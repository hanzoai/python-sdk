"""Metastable consensus protocol.

Two-phase finality for multi-agent agreement.

Reference: https://github.com/luxfi/consensus
"""

from .consensus import Consensus, State, Result, run

__all__ = ["Consensus", "State", "Result", "run"]
__version__ = "0.1.0"

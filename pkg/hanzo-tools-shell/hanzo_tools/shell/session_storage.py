"""Session storage for managing shell sessions.

This module provides session management with cleanup capabilities
for shell processes and background tasks.

Usage:
    from hanzo_tools.shell.session_storage import SessionStorage

    # Clean up expired sessions (older than max_age_seconds)
    SessionStorage.cleanup_expired_sessions(max_age_seconds=300)

    # Clear all active sessions
    cleared = SessionStorage.clear_all_sessions()
"""

from __future__ import annotations

import os
import signal
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, ClassVar

from hanzo_tools.shell.base_process import ProcessManager


@dataclass
class SessionInfo:
    """Information about a shell session."""

    session_id: str
    pid: int
    command: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    log_file: Optional[Path] = None


class SessionStorage:
    """Singleton storage for managing shell sessions.

    Provides centralized tracking and cleanup of shell processes
    to prevent resource leaks and orphaned processes.
    """

    _instance: ClassVar[Optional["SessionStorage"]] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()
    _sessions: ClassVar[Dict[str, SessionInfo]] = {}
    _process_manager: ClassVar[Optional[ProcessManager]] = None

    def __new__(cls) -> "SessionStorage":
        """Singleton pattern for session storage."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._process_manager = ProcessManager()
        return cls._instance

    @classmethod
    def add_session(
        cls,
        session_id: str,
        pid: int,
        command: str,
        log_file: Optional[Path] = None,
    ) -> SessionInfo:
        """Add a new session to storage.

        Args:
            session_id: Unique identifier for the session
            pid: Process ID of the session
            command: Command that started the session
            log_file: Optional path to session log file

        Returns:
            SessionInfo for the new session
        """
        with cls._lock:
            session = SessionInfo(
                session_id=session_id,
                pid=pid,
                command=command,
                log_file=log_file,
            )
            cls._sessions[session_id] = session
            return session

    @classmethod
    def remove_session(cls, session_id: str) -> Optional[SessionInfo]:
        """Remove a session from storage.

        Args:
            session_id: Session identifier to remove

        Returns:
            Removed SessionInfo or None if not found
        """
        with cls._lock:
            return cls._sessions.pop(session_id, None)

    @classmethod
    def get_session(cls, session_id: str) -> Optional[SessionInfo]:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionInfo or None if not found
        """
        with cls._lock:
            return cls._sessions.get(session_id)

    @classmethod
    def list_sessions(cls) -> Dict[str, SessionInfo]:
        """List all active sessions.

        Returns:
            Dictionary of session_id -> SessionInfo
        """
        with cls._lock:
            return cls._sessions.copy()

    @classmethod
    def update_activity(cls, session_id: str) -> bool:
        """Update last activity timestamp for a session.

        Args:
            session_id: Session to update

        Returns:
            True if session exists and was updated
        """
        with cls._lock:
            if session_id in cls._sessions:
                cls._sessions[session_id].last_activity = time.time()
                return True
            return False

    @classmethod
    def cleanup_expired_sessions(cls, max_age_seconds: int = 300) -> int:
        """Clean up sessions older than max_age_seconds.

        This method terminates processes for expired sessions and
        removes them from storage.

        Args:
            max_age_seconds: Maximum session age in seconds (default: 5 minutes)

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        expired_ids = []

        with cls._lock:
            for session_id, session in cls._sessions.items():
                age = current_time - session.last_activity
                if age > max_age_seconds:
                    expired_ids.append(session_id)

        cleaned = 0
        for session_id in expired_ids:
            if cls._terminate_session(session_id):
                cleaned += 1

        return cleaned

    @classmethod
    def clear_all_sessions(cls) -> int:
        """Clear all active sessions.

        Terminates all tracked processes and clears storage.

        Returns:
            Number of sessions cleared
        """
        with cls._lock:
            session_ids = list(cls._sessions.keys())

        cleared = 0
        for session_id in session_ids:
            if cls._terminate_session(session_id):
                cleared += 1

        # Also clean up any processes tracked by ProcessManager
        if cls._process_manager:
            for proc_id in list(cls._process_manager.list_processes().keys()):
                proc = cls._process_manager.get_process(proc_id)
                if proc and proc.returncode is None:
                    try:
                        proc.terminate()
                        cleared += 1
                    except Exception:
                        pass

        return cleared

    @classmethod
    def _terminate_session(cls, session_id: str) -> bool:
        """Terminate a session's process and remove from storage.

        Args:
            session_id: Session to terminate

        Returns:
            True if session was terminated successfully
        """
        session = cls.remove_session(session_id)
        if session is None:
            return False

        try:
            # Try to terminate the process gracefully
            os.kill(session.pid, signal.SIGTERM)

            # Give it a moment to terminate
            time.sleep(0.1)

            # Force kill if still running
            try:
                os.kill(session.pid, 0)  # Check if process exists
                os.kill(session.pid, signal.SIGKILL)
            except OSError:
                pass  # Process already terminated

            return True

        except OSError:
            # Process doesn't exist or permission denied
            return True
        except Exception:
            return False

    @classmethod
    def get_stats(cls) -> dict:
        """Get session storage statistics.

        Returns:
            Dictionary with stats about sessions
        """
        with cls._lock:
            sessions = list(cls._sessions.values())

        if not sessions:
            return {
                "total_sessions": 0,
                "oldest_session_age": 0,
                "newest_session_age": 0,
            }

        current_time = time.time()
        ages = [current_time - s.last_activity for s in sessions]

        return {
            "total_sessions": len(sessions),
            "oldest_session_age": max(ages) if ages else 0,
            "newest_session_age": min(ages) if ages else 0,
        }


# Module-level convenience functions
def cleanup_expired_sessions(max_age_seconds: int = 300) -> int:
    """Clean up expired sessions."""
    return SessionStorage.cleanup_expired_sessions(max_age_seconds)


def clear_all_sessions() -> int:
    """Clear all sessions."""
    return SessionStorage.clear_all_sessions()


__all__ = [
    "SessionStorage",
    "SessionInfo",
    "cleanup_expired_sessions",
    "clear_all_sessions",
]

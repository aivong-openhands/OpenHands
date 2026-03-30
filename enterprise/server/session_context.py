"""Session context management using contextvars for automatic session ID logging.

This module provides a way to set session/conversation context that is automatically
injected into all log messages within the request scope. This eliminates the need
to manually pass `extra={'session_id': sid}` to every log call.

Usage:
    # In middleware or at request entry point:
    from server.session_context import session_context

    token = session_context.set(session_id='abc123', user_id='user456')
    try:
        # All logs within this scope will automatically have session_id and user_id
        logger.info('Processing request')  # Will include session_id='abc123', user_id='user456'
    finally:
        session_context.reset(token)

    # Or use the context manager:
    with session_context.scope(session_id='abc123', user_id='user456'):
        logger.info('Processing request')
"""

import logging
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionContextData:
    """Data stored in session context."""

    session_id: str | None = None
    user_id: str | None = None


# Context variable to store session data
_session_context: ContextVar[SessionContextData] = ContextVar(
    'session_context', default=SessionContextData()
)


class SessionContext:
    """Manages session context for logging and request tracking."""

    def set(
        self, session_id: str | None = None, user_id: str | None = None
    ) -> Token[SessionContextData]:
        """Set session context values.

        Args:
            session_id: The session/conversation ID
            user_id: The user ID

        Returns:
            A token that can be used to reset the context
        """
        return _session_context.set(
            SessionContextData(session_id=session_id, user_id=user_id)
        )

    def reset(self, token: Token[SessionContextData]) -> None:
        """Reset session context to previous value.

        Args:
            token: The token returned by set()
        """
        _session_context.reset(token)

    def get(self) -> SessionContextData:
        """Get current session context data."""
        return _session_context.get()

    def get_session_id(self) -> str | None:
        """Get the current session ID."""
        return _session_context.get().session_id

    def get_user_id(self) -> str | None:
        """Get the current user ID."""
        return _session_context.get().user_id

    def scope(self, session_id: str | None = None, user_id: str | None = None):
        """Context manager for setting session context.

        Usage:
            with session_context.scope(session_id='abc123'):
                logger.info('This log will have session_id')
        """
        return _SessionContextScope(self, session_id, user_id)


class _SessionContextScope:
    """Context manager for session context scope."""

    def __init__(
        self,
        context: SessionContext,
        session_id: str | None,
        user_id: str | None,
    ):
        self._context = context
        self._session_id = session_id
        self._user_id = user_id
        self._token: Token[SessionContextData] | None = None

    def __enter__(self) -> 'SessionContext':
        self._token = self._context.set(
            session_id=self._session_id, user_id=self._user_id
        )
        return self._context

    def __exit__(self, *args: Any) -> None:
        if self._token is not None:
            self._context.reset(self._token)


class SessionContextFilter(logging.Filter):
    """Logging filter that injects session context into log records.

    This filter automatically adds session_id and user_id fields to all log
    records when session context has been set.

    Usage:
        logger.addFilter(SessionContextFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add session context to log record.

        Args:
            record: The log record to modify

        Returns:
            True (always allows the record through)
        """
        ctx = _session_context.get()

        # Only set if not already present (allow explicit override via extra={})
        if not hasattr(record, 'session_id') or record.session_id is None:  # type: ignore[attr-defined]
            record.session_id = ctx.session_id  # type: ignore[attr-defined]

        if not hasattr(record, 'user_id') or record.user_id is None:  # type: ignore[attr-defined]
            record.user_id = ctx.user_id  # type: ignore[attr-defined]

        return True


# Global session context instance
session_context = SessionContext()

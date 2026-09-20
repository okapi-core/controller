"""Errors surfaced by okapictl."""


class OkapiCtlError(RuntimeError):
    """An expected, user-actionable controller error."""


class UnsupportedWorkflowError(OkapiCtlError):
    """The command is recognized but not implemented yet."""


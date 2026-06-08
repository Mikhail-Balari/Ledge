"""Exceptions for the Ledge Python SDK core."""


class LedgeSDKError(Exception):
    """Base class for SDK-level errors."""


class InvalidConfidenceError(LedgeSDKError):
    """Raised when a confidence or evidence score is outside [0.0, 1.0]."""


class PolicyValidationError(LedgeSDKError):
    """Raised when a decision policy is invalid."""


class UnsafeUnwrapError(LedgeSDKError):
    """Raised when an uncertain value is unwrapped without an explicit reason."""


class SchemaValidationError(LedgeSDKError):
    """Raised when SDK-level schema validation fails."""

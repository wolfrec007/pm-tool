class NotFoundError(Exception):
    """Resource not found."""

class OverAllocationError(Exception):
    """Assignment would over-allocate the team member."""

class ConflictWithLeaveError(Exception):
    """Assignment conflicts with approved leave."""

class ValidationError(Exception):
    """Business validation failed."""

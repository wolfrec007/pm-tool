"""License tier definitions and limits."""

TIER_LIMITS = {
    "standard": {
        "name": "Standard",
        "max_users": 50,
        "max_team_members": 599,
        "features": {
            "api_access": True,
            "advanced_reports": False,
            "bulk_upload": True,
            "email_notifications": True,
        },
    },
    "enterprise": {
        "name": "Enterprise",
        "max_users": 100,
        "max_team_members": 5000,
        "features": {
            "api_access": True,
            "advanced_reports": True,
            "bulk_upload": True,
            "email_notifications": True,
            "priority_support": True,
        },
    },
}


def get_tier_limits(tier: str) -> dict:
    """Get limits for a license tier."""
    return TIER_LIMITS.get(tier, TIER_LIMITS["standard"])


def check_user_limit(tier: str, current_count: int) -> bool:
    """Check if within user limit for tier. Returns True if allowed."""
    limits = get_tier_limits(tier)
    if limits["max_users"] is None:
        return True  # unlimited
    return current_count < limits["max_users"]


def check_team_member_limit(tier: str, current_count: int) -> bool:
    """Check if within team member limit for tier. Returns True if allowed."""
    limits = get_tier_limits(tier)
    if limits["max_team_members"] is None:
        return True  # unlimited
    return current_count < limits["max_team_members"]


def has_feature(tier: str, feature: str) -> bool:
    """Check if tier has a specific feature."""
    limits = get_tier_limits(tier)
    return limits["features"].get(feature, False)

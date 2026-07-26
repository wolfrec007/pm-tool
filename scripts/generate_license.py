#!/usr/bin/env python3
"""Generate a license key for a customer.

Usage:
    python -m scripts.generate_license --tier standard
    python -m scripts.generate_license --tier enterprise --duration 3m
    python -m scripts.generate_license --tier standard --duration 6m
    python -m scripts.generate_license --tier enterprise --duration 12m
    python -m scripts.generate_license --tier standard --days 30
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.license_service import generate_license_key

# Duration presets
DURATION_MAP = {
    "3m": 90,
    "6m": 180,
    "12m": 365,
}


def main():
    parser = argparse.ArgumentParser(description="Generate a splanly license key")
    parser.add_argument(
        "--tier",
        choices=["standard", "enterprise"],
        required=True,
        help="License tier",
    )
    parser.add_argument(
        "--duration",
        choices=["3m", "6m", "12m"],
        default=None,
        help="License duration (3m, 6m, 12m)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Custom days until expiry (omit for perpetual license)",
    )
    args = parser.parse_args()

    # Calculate expiry
    expires_at = None
    duration_label = "Perpetual"

    if args.duration:
        days = DURATION_MAP[args.duration]
        expires_at = datetime.utcnow() + timedelta(days=days)
        duration_label = f"{args.duration} ({days} days)"
    elif args.days:
        expires_at = datetime.utcnow() + timedelta(days=args.days)
        duration_label = f"{args.days} days"

    # Generate key
    key = generate_license_key(args.tier, expires_at)

    # Get tier limits
    from app.services.license_tiers import get_tier_limits
    limits = get_tier_limits(args.tier)

    # Output
    print("\n" + "=" * 50)
    print("SPLANLY LICENSE KEY")
    print("=" * 50)
    print(f"\nTier:       {args.tier.title()}")
    print(f"Users:      {limits['max_users'] or 'Unlimited'}")
    print(f"Team:       {limits['max_team_members'] or 'Unlimited'}")
    print(f"Duration:   {duration_label}")
    if expires_at:
        print(f"Expires:    {expires_at.strftime('%Y-%m-%d')}")
    print(f"\nKey:        {key}")
    print("\n" + "=" * 50)
    print("\nGive this key to your customer to activate their license.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()

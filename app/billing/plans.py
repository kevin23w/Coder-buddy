"""
Billing plan definitions and feature gates for Coder Buddy SaaS.
"""

# ── Plan feature matrix ───────────────────────────────────────────────────────
PLANS: dict[str, dict] = {
    "free": {
        "display_name":    "Free",
        "price_inr":       0,
        "runs_per_month":  3,
        "max_file_size_kb": 50,
        "email_report":    False,
        "commit_proposal": False,
        "github_pr":       False,
        "api_access":      False,
        "team_members":    1,
        "webhooks":        False,
        "priority_model":  False,
    },
    "pro": {
        "display_name":    "Pro",
        "price_inr":       499,
        "runs_per_month":  50,
        "max_file_size_kb": 500,
        "email_report":    True,
        "commit_proposal": True,
        "github_pr":       True,
        "api_access":      False,
        "team_members":    1,
        "webhooks":        False,
        "priority_model":  True,
    },
    "team": {
        "display_name":    "Team",
        "price_inr":       1499,
        "runs_per_month":  999_999,   # effectively unlimited
        "max_file_size_kb": 2000,
        "email_report":    True,
        "commit_proposal": True,
        "github_pr":       True,
        "api_access":      True,
        "team_members":    5,
        "webhooks":        True,
        "priority_model":  True,
    },
}

# ── Razorpay plan IDs ─────────────────────────────────────────────────────────
# Create these in: Razorpay Dashboard → Subscriptions → Plans
# Then paste the generated plan_XXXXXXXXXXXXXXX IDs below.
RAZORPAY_PLAN_IDS: dict[str, str] = {
    "pro":  "plan_XXXXXXXXXXXXXXX",   # ₹499/month
    "team": "plan_XXXXXXXXXXXXXXX",   # ₹1499/month
}

# Annual pricing (20% discount)
ANNUAL_PRICES_INR: dict[str, int] = {
    "pro":  399 * 12,   # ₹4,788/year
    "team": 1199 * 12,  # ₹14,388/year
}


def get_plan(plan_name: str) -> dict:
    """Return plan config, defaulting to 'free' if unknown."""
    return PLANS.get(plan_name, PLANS["free"])


def check_feature(plan_name: str, feature: str) -> bool:
    """Return True if the given plan has the specified feature enabled."""
    return bool(get_plan(plan_name).get(feature, False))


def get_run_limit(plan_name: str) -> int:
    """Return the monthly run limit for a plan."""
    return get_plan(plan_name)["runs_per_month"]

"""
Notification integrations for Coder Buddy.

Supports:
  - Slack (via Incoming Webhooks)
  - Discord (via Webhooks)
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """Result of sending a notification."""
    success: bool
    platform: str
    error: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Slack
# ─────────────────────────────────────────────────────────────────────────────

def send_slack_notification(
    webhook_url: str,
    repo_path: str,
    success: bool,
    plan: list[str],
    test_output: str,
    commit_message: str,
    pr_url: str = "",
    iterations: int = 0,
) -> NotificationResult:
    """
    Send a rich Slack Block Kit notification via an Incoming Webhook.

    Args:
        webhook_url:    Slack Incoming Webhook URL.
        repo_path:      The analysed repository path.
        success:        Whether tests passed.
        plan:           List of plan steps.
        test_output:    Last few lines of pytest output.
        commit_message: Proposed commit message.
        pr_url:         GitHub PR URL (optional).
        iterations:     Number of fix iterations used.
    """
    try:
        import httpx
    except ImportError:
        return NotificationResult(success=False, platform="slack", error="httpx not installed")

    status_emoji = "✅" if success else "❌"
    status_text  = "All tests passed!" if success else "Tests failed — manual review needed."
    color        = "#3fb950" if success else "#f85149"

    # Truncate test output to avoid Slack's 3000-char block limit
    short_output = "\n".join(test_output.strip().splitlines()[-20:])

    plan_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan[:5]))

    pr_section = (
        [{"type": "section", "text": {"type": "mrkdwn", "text": f"🔗 *Pull Request:* <{pr_url}|View PR #{pr_url.split('/')[-1]}>"}}]
        if pr_url else []
    )

    payload = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"🤖 Coder Buddy — {status_emoji} Fix Complete"},
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Repository:*\n`{repo_path}`"},
                            {"type": "mrkdwn", "text": f"*Status:*\n{status_text}"},
                            {"type": "mrkdwn", "text": f"*Iterations used:*\n{iterations}"},
                            {"type": "mrkdwn", "text": f"*Commit:*\n`{commit_message[:60]}`"},
                        ],
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*📋 Plan:*\n{plan_text}"},
                    },
                    *pr_section,
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🧪 Test Output:*\n```{short_output[:1500]}```",
                        },
                    },
                ],
            }
        ]
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("[slack] Notification sent successfully")
        return NotificationResult(success=True, platform="slack")
    except Exception as e:
        logger.error("[slack] Failed to send notification: %s", e)
        return NotificationResult(success=False, platform="slack", error=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Discord
# ─────────────────────────────────────────────────────────────────────────────

def send_discord_notification(
    webhook_url: str,
    repo_path: str,
    success: bool,
    plan: list[str],
    test_output: str,
    commit_message: str,
    pr_url: str = "",
    iterations: int = 0,
) -> NotificationResult:
    """
    Send a rich Discord Embed notification via a Webhook.

    Args:
        webhook_url:    Discord Webhook URL.
        repo_path:      The analysed repository path.
        success:        Whether tests passed.
        plan:           List of plan steps.
        test_output:    Last few lines of pytest output.
        commit_message: Proposed commit message.
        pr_url:         GitHub PR URL (optional).
        iterations:     Number of fix iterations used.
    """
    try:
        import httpx
    except ImportError:
        return NotificationResult(success=False, platform="discord", error="httpx not installed")

    color       = 0x3FB950 if success else 0xF85149  # green / red
    status_text = "✅ All tests passed!" if success else "❌ Tests failed — review needed."
    short_output = "\n".join(test_output.strip().splitlines()[-15:])
    plan_text    = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan[:5]))

    fields = [
        {"name": "📁 Repository",    "value": f"`{repo_path}`",         "inline": False},
        {"name": "🏁 Status",        "value": status_text,               "inline": True},
        {"name": "🔄 Iterations",    "value": str(iterations),           "inline": True},
        {"name": "📝 Commit Message","value": f"`{commit_message[:80]}`","inline": False},
        {"name": "📋 Plan",          "value": plan_text[:900] or "N/A", "inline": False},
        {
            "name":  "🧪 Test Output",
            "value": f"```\n{short_output[:900]}\n```" if short_output else "No output",
            "inline": False,
        },
    ]

    if pr_url:
        fields.append({"name": "🔗 Pull Request", "value": pr_url, "inline": False})

    payload = {
        "username": "Coder Buddy 🤖",
        "avatar_url": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f916.png",
        "embeds": [
            {
                "title": "🤖 Coder Buddy — Fix Report",
                "color": color,
                "fields": fields,
                "footer": {"text": "Powered by LangGraph × Groq × LLaMA 3.3 70B"},
            }
        ],
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("[discord] Notification sent successfully")
        return NotificationResult(success=True, platform="discord")
    except Exception as e:
        logger.error("[discord] Failed to send notification: %s", e)
        return NotificationResult(success=False, platform="discord", error=str(e))

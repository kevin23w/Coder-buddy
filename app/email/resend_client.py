"""
Transactional email via Resend.com (free tier — 3,000 emails/month).
"""
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def _get_resend():
    try:
        import resend as _resend
        _resend.api_key = settings.RESEND_API_KEY
        return _resend
    except ImportError:
        raise RuntimeError("resend package not installed. Run: pip install resend")


def _from_address() -> str:
    return settings.RESEND_FROM_EMAIL or "noreply@coderbuddy.dev"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Analysis Report (Pro + Team)
# ─────────────────────────────────────────────────────────────────────────────

async def send_analysis_report(user_email: str, result: dict) -> bool:
    """
    Send a formatted code analysis report to the user.
    Only called when the user's plan has email_report = True.
    """
    plan_steps = "".join(
        f"<li style='margin-bottom:6px'>{s}</li>"
        for s in result.get("plan", [])
    )
    test       = result.get("test_result", {})
    passed     = test.get("passed", False)
    status_txt = "✅ All tests passed" if passed else "❌ Tests failed"
    status_col = "#3fb950" if passed else "#f85149"
    commit_msg = result.get("commit_proposal", {}).get("message", "N/A")
    iterations = result.get("iteration", 0)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"/></head>
    <body style="margin:0;padding:0;background:#0d1117;font-family:Inter,Arial,sans-serif;color:#e6edf3;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td align="center" style="padding:40px 20px;">
          <table width="600" cellpadding="0" cellspacing="0" style="background:#161b22;border:1px solid #30363d;border-radius:12px;overflow:hidden;">

            <!-- Header -->
            <tr><td style="background:linear-gradient(135deg,#1c2541,#0d1117);padding:32px 40px;">
              <h1 style="margin:0;font-size:24px;background:linear-gradient(90deg,#58a6ff,#d2a8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                🤖 Coder Buddy
              </h1>
              <p style="margin:8px 0 0;color:#7d8590;font-size:14px;">Your Code Analysis Report</p>
            </td></tr>

            <!-- Status badge -->
            <tr><td style="padding:24px 40px 0;">
              <span style="display:inline-block;background:{status_col}22;border:1px solid {status_col}55;
                color:{status_col};padding:6px 16px;border-radius:20px;font-weight:600;font-size:14px;">
                {status_txt}
              </span>
            </td></tr>

            <!-- Plan -->
            <tr><td style="padding:20px 40px;">
              <h2 style="font-size:16px;color:#e6edf3;margin:0 0 12px;">📋 Action Plan</h2>
              <ol style="margin:0;padding-left:20px;color:#c9d1d9;font-size:14px;line-height:1.6;">
                {plan_steps}
              </ol>
            </td></tr>

            <!-- Commit message -->
            <tr><td style="padding:0 40px 20px;">
              <h2 style="font-size:16px;color:#e6edf3;margin:0 0 10px;">📝 Commit Message</h2>
              <pre style="background:#0d1117;border:1px solid #58a6ff44;border-radius:8px;
                padding:14px;font-family:'Courier New',monospace;font-size:13px;
                color:#58a6ff;margin:0;white-space:pre-wrap;">{commit_msg}</pre>
            </td></tr>

            <!-- Stats -->
            <tr><td style="padding:0 40px 20px;">
              <table width="100%" style="border-collapse:collapse;">
                <tr>
                  <td style="background:#1c2128;border:1px solid #30363d;border-radius:8px;
                    padding:14px;text-align:center;width:50%;">
                    <div style="font-size:24px;font-weight:700;color:#58a6ff;">{iterations}</div>
                    <div style="font-size:12px;color:#7d8590;margin-top:4px;">Iterations Used</div>
                  </td>
                  <td width="16"></td>
                  <td style="background:#1c2128;border:1px solid #30363d;border-radius:8px;
                    padding:14px;text-align:center;width:50%;">
                    <div style="font-size:24px;font-weight:700;color:{status_col};">
                      {'Pass' if passed else 'Fail'}
                    </div>
                    <div style="font-size:12px;color:#7d8590;margin-top:4px;">Test Result</div>
                  </td>
                </tr>
              </table>
            </td></tr>

            <!-- CTA -->
            <tr><td style="padding:0 40px 32px;text-align:center;">
              <a href="{settings.NEXT_PUBLIC_APP_URL}/dashboard"
                style="display:inline-block;background:linear-gradient(135deg,#1f6feb,#388bfd);
                color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;
                font-weight:600;font-size:14px;">
                View Full Report →
              </a>
            </td></tr>

            <!-- Footer -->
            <tr><td style="border-top:1px solid #30363d;padding:20px 40px;text-align:center;">
              <p style="margin:0;font-size:12px;color:#7d8590;">
                Coder Buddy · Powered by LangGraph × Groq × LLaMA 3.3 70B<br/>
                <a href="{settings.NEXT_PUBLIC_APP_URL}/dashboard" style="color:#58a6ff;text-decoration:none;">Manage subscription</a>
              </p>
            </td></tr>

          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """

    return _send(
        to=user_email,
        subject="🤖 Coder Buddy — Your Code Analysis Report",
        html=html,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Welcome Email
# ─────────────────────────────────────────────────────────────────────────────

async def send_welcome_email(user_email: str, name: str = "") -> bool:
    greeting = f"Hi {name}," if name else "Hi there,"
    html = f"""
    <!DOCTYPE html><html><body style="background:#0d1117;font-family:Inter,Arial,sans-serif;color:#e6edf3;padding:40px 20px;">
      <div style="max-width:560px;margin:auto;background:#161b22;border:1px solid #30363d;border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#1c2541,#0d1117);padding:32px 40px;">
          <h1 style="margin:0;font-size:22px;color:#58a6ff;">🤖 Welcome to Coder Buddy!</h1>
        </div>
        <div style="padding:28px 40px;">
          <p>{greeting}</p>
          <p>You're on the <strong>Free plan</strong>. Here's what you can do:</p>
          <ul style="color:#c9d1d9;line-height:2;">
            <li>✅ 3 agent runs per month</li>
            <li>✅ Automatic bug detection</li>
            <li>✅ pytest integration</li>
          </ul>
          <p>Want more? <strong>Upgrade to Pro</strong> for ₹499/month:</p>
          <ul style="color:#c9d1d9;line-height:2;">
            <li>🚀 50 runs/month</li>
            <li>📧 Email reports</li>
            <li>📝 Commit + PR generation</li>
          </ul>
          <div style="text-align:center;margin-top:28px;">
            <a href="{settings.NEXT_PUBLIC_APP_URL}/pricing"
              style="background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;
              text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;">
              View Pricing →
            </a>
          </div>
        </div>
        <div style="border-top:1px solid #30363d;padding:16px 40px;text-align:center;font-size:12px;color:#7d8590;">
          Coder Buddy · <a href="{settings.NEXT_PUBLIC_APP_URL}" style="color:#58a6ff;text-decoration:none;">coderbuddy.dev</a>
        </div>
      </div>
    </body></html>
    """
    return _send(to=user_email, subject="Welcome to Coder Buddy 🤖 — Your AI Software Engineer", html=html)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Payment Confirmation
# ─────────────────────────────────────────────────────────────────────────────

async def send_payment_confirmation(user_email: str, plan: str, amount: int) -> bool:
    plan_label = plan.title()
    html = f"""
    <!DOCTYPE html><html><body style="background:#0d1117;font-family:Inter,Arial,sans-serif;color:#e6edf3;padding:40px 20px;">
      <div style="max-width:560px;margin:auto;background:#161b22;border:1px solid #30363d;border-radius:12px;overflow:hidden;">
        <div style="background:linear-gradient(135deg,#1c2541,#0d1117);padding:32px 40px;">
          <h1 style="margin:0;font-size:22px;color:#3fb950;">✅ Payment Confirmed</h1>
        </div>
        <div style="padding:28px 40px;">
          <p>You are now on the <strong style="color:#58a6ff;">{plan_label} plan</strong>.</p>
          <div style="background:#1c2128;border:1px solid #30363d;border-radius:8px;padding:20px;margin:20px 0;text-align:center;">
            <div style="font-size:32px;font-weight:700;color:#3fb950;">₹{amount}</div>
            <div style="color:#7d8590;font-size:13px;margin-top:4px;">charged per month</div>
          </div>
          <p>What's unlocked on <strong>{plan_label}</strong>:</p>
          {"<ul style='color:#c9d1d9;line-height:2;'><li>50 agent runs/month</li><li>Email reports</li><li>Commit + PR generation</li></ul>" if plan == "pro" else "<ul style='color:#c9d1d9;line-height:2;'><li>Unlimited runs</li><li>5 team members</li><li>API access</li><li>Slack/Discord webhooks</li></ul>"}
          <div style="text-align:center;margin-top:28px;">
            <a href="{settings.NEXT_PUBLIC_APP_URL}/dashboard"
              style="background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;
              text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;">
              Go to Dashboard →
            </a>
          </div>
        </div>
      </div>
    </body></html>
    """
    return _send(to=user_email, subject=f"✅ Payment confirmed — You're on {plan_label} plan | Coder Buddy", html=html)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Subscription Ended
# ─────────────────────────────────────────────────────────────────────────────

async def send_subscription_ended(user_email: str) -> bool:
    html = f"""
    <!DOCTYPE html><html><body style="background:#0d1117;font-family:Inter,Arial,sans-serif;color:#e6edf3;padding:40px 20px;">
      <div style="max-width:560px;margin:auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px 40px;">
        <h1 style="color:#f85149;margin-top:0;">Subscription Ended</h1>
        <p>Your Coder Buddy subscription has ended. Your account has been moved to the <strong>Free plan</strong> (3 runs/month).</p>
        <p>We'd love to have you back!</p>
        <div style="text-align:center;margin-top:28px;">
          <a href="{settings.NEXT_PUBLIC_APP_URL}/pricing"
            style="background:linear-gradient(135deg,#1f6feb,#388bfd);color:#fff;
            text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;">
            Resubscribe →
          </a>
        </div>
      </div>
    </body></html>
    """
    return _send(to=user_email, subject="Your Coder Buddy subscription has ended", html=html)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Payment Failed
# ─────────────────────────────────────────────────────────────────────────────

async def send_payment_failed(user_email: str) -> bool:
    html = f"""
    <!DOCTYPE html><html><body style="background:#0d1117;font-family:Inter,Arial,sans-serif;color:#e6edf3;padding:40px 20px;">
      <div style="max-width:560px;margin:auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px 40px;">
        <h1 style="color:#e3b341;margin-top:0;">⚠️ Payment Failed</h1>
        <p>We couldn't process your payment for Coder Buddy. Please update your payment method to continue enjoying Pro features.</p>
        <div style="text-align:center;margin-top:28px;">
          <a href="{settings.NEXT_PUBLIC_APP_URL}/dashboard"
            style="background:#e3b341;color:#000;text-decoration:none;
            padding:12px 28px;border-radius:8px;font-weight:600;">
            Update Payment Method →
          </a>
        </div>
      </div>
    </body></html>
    """
    return _send(to=user_email, subject="⚠️ Action required — Coder Buddy payment failed", html=html)


# ─────────────────────────────────────────────────────────────────────────────
# Internal send helper
# ─────────────────────────────────────────────────────────────────────────────

def _send(to: str, subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email to %s", to)
        return False
    try:
        resend = _get_resend()
        resend.Emails.send({
            "from":    _from_address(),
            "to":      [to],
            "subject": subject,
            "html":    html,
        })
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False

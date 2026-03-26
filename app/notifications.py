"""
notifications.py — Windows toast notifications for Quietum.
Uses plyer for cross-platform notification support.
Falls back silently if notifications are unavailable.
"""

from app.constants import APP_NAME


def send_notification(title: str, message: str):
    """
    Send a desktop toast notification.
    Fails silently if plyer is not installed or notifications are unsupported.
    """
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name=APP_NAME,
            timeout=8,
        )
    except Exception:
        # Silently ignore — notifications are a nice-to-have
        pass


def send_task_reminder(task_text: str):
    """Send a reminder notification for a specific task."""
    send_notification(
        title=f"⏰ {APP_NAME} Reminder",
        message=task_text[:100],
    )

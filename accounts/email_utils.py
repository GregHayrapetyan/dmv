"""
Utility functions for sending emails asynchronously.
"""
import logging
import threading
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email_async(subject, message, recipient_list, from_email=None):
    """
    Send email asynchronously in a separate thread to avoid blocking the request.
    
    Args:
        subject: Email subject
        message: Email body
        recipient_list: List of recipient email addresses
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    def _send():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {recipient_list}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
    
    # Start email sending in a separate thread
    thread = threading.Thread(target=_send)
    thread.daemon = True  # Thread will not prevent program exit
    thread.start()
    
    logger.info(f"Email queued for sending to {recipient_list}")


def send_verification_email(email, code):
    """Send verification code email asynchronously."""
    send_email_async(
        subject="Verify your email",
        message=f"Your verification code is: {code}",
        recipient_list=[email]
    )


def send_password_reset_email(email, code):
    """Send password reset code email asynchronously."""
    send_email_async(
        subject="Reset password",
        message=f"Your password reset code is: {code}",
        recipient_list=[email]
    )

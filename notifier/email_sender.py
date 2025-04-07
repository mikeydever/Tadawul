"""
Handles sending email notifications using smtplib.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from config import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str, recipient: str) -> bool:
    """
    Sends an email using configured SMTP settings.

    Args:
        subject: The subject line of the email.
        body: The plain text body content of the email.
        recipient: The email address of the recipient.

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    # Check if essential configuration is present
    if not all(
        [
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
            settings.EMAIL_USER,
            settings.EMAIL_PASSWORD,
            recipient, # Ensure recipient is also provided
        ]
    ):
        logger.error(
            "Email configuration incomplete (HOST, PORT, USER, PASSWORD, RECIPIENT). "
            "Cannot send email."
        )
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    # Format 'From' address for better display in email clients
    sender_display_name = settings.EMAIL_SENDER_NAME or settings.EMAIL_USER
    msg["From"] = f"{sender_display_name} <{settings.EMAIL_USER}>"
    msg["To"] = recipient
    msg.set_content(body)

    context = ssl.create_default_context()

    try:
        # Using port 587 typically requires STARTTLS
        if settings.EMAIL_PORT == 587:
            logger.info(f"Connecting to SMTP server {settings.EMAIL_HOST}:{settings.EMAIL_PORT} using STARTTLS...")
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.ehlo() # Can be omitted
                server.starttls(context=context)
                server.ehlo() # Re-identify ourselves over TLS connection
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {recipient}")
        # Using port 465 typically requires SMTP_SSL from the start
        elif settings.EMAIL_PORT == 465:
             logger.info(f"Connecting to SMTP server {settings.EMAIL_HOST}:{settings.EMAIL_PORT} using SSL...")
             with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context) as server:
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)
                logger.info(f"Email sent successfully to {recipient}")
        else:
            # Handle other ports or unencrypted (not recommended)
            logger.warning(f"Unsupported SMTP port configuration: {settings.EMAIL_PORT}. Attempting plain SMTP (unsafe).")
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                # No login for plain SMTP unless server supports it without TLS/SSL
                server.send_message(msg)
                logger.info(f"Email sent (plain) successfully to {recipient}")

        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            f"SMTP Authentication failed for user {settings.EMAIL_USER}. "
            "Check username/password and email provider security settings (e.g., app passwords)."
        )
        return False
    except smtplib.SMTPConnectError:
         logger.error(f"Failed to connect to SMTP server at {settings.EMAIL_HOST}:{settings.EMAIL_PORT}.")
         return False
    except smtplib.SMTPServerDisconnected:
        logger.error("SMTP server disconnected unexpectedly.")
        return False
    except TimeoutError:
         logger.error(f"Connection to SMTP server {settings.EMAIL_HOST} timed out.")
         return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}", exc_info=True)
        return False

# Example usage (optional, for testing during development)
# if __name__ == "__main__":
#     # Ensure you have a .env file with EMAIL_* variables set
#     test_subject = "Test Email from Golden Cross Scanner"
#     test_body = "This is a test email.\nIf you received this, the configuration is likely correct."
#     test_recipient = settings.EMAIL_RECIPIENT # Loaded from .env
#
#     if test_recipient:
#         print(f"Attempting to send test email to: {test_recipient}")
#         success = send_email(test_subject, test_body, test_recipient)
#         if success:
#             print("Test email function executed successfully (check recipient's inbox).")
#         else:
#             print("Test email function failed. Check logs for details.")
#     else:
#         print("EMAIL_RECIPIENT not set in environment variables. Skipping test email.")
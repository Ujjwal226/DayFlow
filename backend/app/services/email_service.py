import email.message
import logging
import smtplib
from abc import ABC, abstractmethod
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("dayflow.email")


class EmailProvider(ABC):
    @abstractmethod
    def send_verification_email(self, to_email: str, display_name: str, verification_url: str) -> None:
        """Send account verification email."""
        pass

    @abstractmethod
    def send_password_reset_email(self, to_email: str, display_name: str, reset_url: str) -> None:
        """Send password reset email."""
        pass

    @abstractmethod
    def send_reminder_email(
        self,
        to_email: str,
        display_name: str,
        title: str,
        description: Optional[str] = None,
        task_title: Optional[str] = None,
        scheduled_at_str: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> None:
        """Send reminder notification email."""
        pass


class DevelopmentEmailProvider(EmailProvider):
    """Console/Terminal development email simulator.
    
    Generates and prints verification, reset, and reminder links clearly to logs/stdout.
    """

    def send_verification_email(self, to_email: str, display_name: str, verification_url: str) -> None:
        logger.info(
            "\n"
            "======================= [DEV EMAIL SIMULATOR] =======================\n"
            "TO: %s <%s>\n"
            "FROM: %s <%s>\n"
            "SUBJECT: Verify your DayFlow account\n"
            "BODY:\n"
            "Hello %s,\n\n"
            "Welcome to DayFlow! Please verify your email by clicking the link below:\n"
            "%s\n\n"
            "(This link expires in %d hours)\n"
            "=====================================================================",
            display_name,
            to_email,
            settings.EMAIL_FROM_NAME,
            settings.EMAIL_FROM,
            display_name,
            verification_url,
            settings.VERIFICATION_TOKEN_EXPIRE_HOURS,
        )

    def send_password_reset_email(self, to_email: str, display_name: str, reset_url: str) -> None:
        logger.info(
            "\n"
            "======================= [DEV EMAIL SIMULATOR] =======================\n"
            "TO: %s <%s>\n"
            "FROM: %s <%s>\n"
            "SUBJECT: Reset your DayFlow password\n"
            "BODY:\n"
            "Hello %s,\n\n"
            "A password reset request was received for your DayFlow account.\n"
            "Click the link below to set a new password:\n"
            "%s\n\n"
            "(This link expires in %d minutes. If you did not request this, ignore this email.)\n"
            "=====================================================================",
            display_name,
            to_email,
            settings.EMAIL_FROM_NAME,
            settings.EMAIL_FROM,
            display_name,
            reset_url,
            settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )

    def send_reminder_email(
        self,
        to_email: str,
        display_name: str,
        title: str,
        description: Optional[str] = None,
        task_title: Optional[str] = None,
        scheduled_at_str: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> None:
        logger.info(
            "\n"
            "======================= [DEV EMAIL SIMULATOR] =======================\n"
            "TO: %s <%s>\n"
            "FROM: %s <%s>\n"
            "MESSAGE-ID: %s\n"
            "SUBJECT: DayFlow Reminder: %s\n"
            "BODY:\n"
            "Hello %s,\n\n"
            "This is a reminder for: %s\n"
            "Description: %s\n"
            "Associated Task: %s\n"
            "Scheduled Time: %s\n\n"
            "— The DayFlow Team\n"
            "=====================================================================",
            display_name,
            to_email,
            settings.EMAIL_FROM_NAME,
            settings.EMAIL_FROM,
            message_id or "(Generated)",
            title,
            display_name,
            title,
            description or "(None)",
            task_title or "(None)",
            scheduled_at_str or "Now",
        )


class SMTPEmailProvider(EmailProvider):
    """Production SMTP Email Provider supporting STARTTLS and SSL."""

    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.use_ssl = settings.SMTP_USE_SSL
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME

        if not self.host:
            raise ValueError("SMTP_HOST must be configured to use SMTPEmailProvider")
        if not self.from_email:
            raise ValueError("EMAIL_FROM must be configured to use SMTPEmailProvider")

    def _send_message(self, to_email: str, subject: str, body: str, message_id: Optional[str] = None) -> None:
        msg = email.message.EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        if message_id:
            msg["Message-ID"] = message_id
        msg.set_content(body)

        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=10) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    server.send_message(msg)
        except Exception as exc:
            # Sanitize error message to ensure password is never exposed in logs/outbox
            err_str = str(exc)
            if self.password and self.password in err_str:
                err_str = err_str.replace(self.password, "******")
            logger.error("SMTP transmission error to %s: %s", to_email, err_str)
            raise RuntimeError(f"SMTP delivery failed: {err_str}") from exc

    def send_verification_email(self, to_email: str, display_name: str, verification_url: str) -> None:
        subject = "Verify your DayFlow account"
        body = (
            f"Hello {display_name},\n\n"
            f"Welcome to DayFlow! Please verify your email by clicking the link below:\n"
            f"{verification_url}\n\n"
            f"(This link expires in {settings.VERIFICATION_TOKEN_EXPIRE_HOURS} hours)\n"
        )
        self._send_message(to_email, subject, body)

    def send_password_reset_email(self, to_email: str, display_name: str, reset_url: str) -> None:
        subject = "Reset your DayFlow password"
        body = (
            f"Hello {display_name},\n\n"
            f"A password reset request was received for your DayFlow account.\n"
            f"Click the link below to set a new password:\n"
            f"{reset_url}\n\n"
            f"(This link expires in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. If you did not request this, ignore this email.)\n"
        )
        self._send_message(to_email, subject, body)

    def send_reminder_email(
        self,
        to_email: str,
        display_name: str,
        title: str,
        description: Optional[str] = None,
        task_title: Optional[str] = None,
        scheduled_at_str: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> None:
        subject = f"DayFlow Reminder: {title}"
        body = (
            f"Hello {display_name},\n\n"
            f"This is a reminder from DayFlow:\n\n"
            f"Title: {title}\n"
            f"Details: {description or 'N/A'}\n"
            f"Linked Task: {task_title or 'N/A'}\n"
            f"Scheduled At: {scheduled_at_str or 'Now'}\n\n"
            f"Log in to DayFlow to view or manage your tasks and reminders.\n\n"
            f"— The DayFlow Team"
        )
        self._send_message(to_email, subject, body, message_id=message_id)


def get_email_provider() -> EmailProvider:
    """Factory creating configured email provider."""
    if settings.EMAIL_PROVIDER == "smtp":
        return SMTPEmailProvider()
    return DevelopmentEmailProvider()

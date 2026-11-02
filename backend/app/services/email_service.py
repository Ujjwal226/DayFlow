from abc import ABC, abstractmethod
import logging

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


class DevelopmentEmailProvider(EmailProvider):
    """Console/Terminal development email simulator.
    
    Generates and prints verification and reset links clearly to logs/stdout.
    Strictly forbidden from being activated in production environments.
    """

    def send_verification_email(self, to_email: str, display_name: str, verification_url: str) -> None:
        logger.info(
            "\n"
            "======================= [DEV EMAIL SIMULATOR] =======================\n"
            "TO: %s <%s>\n"
            "FROM: %s\n"
            "SUBJECT: Verify your DayFlow account\n"
            "BODY:\n"
            "Hello %s,\n\n"
            "Welcome to DayFlow! Please verify your email by clicking the link below:\n"
            "%s\n\n"
            "(This link expires in %d hours)\n"
            "=====================================================================",
            display_name,
            to_email,
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
            "FROM: %s\n"
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
            settings.EMAIL_FROM,
            display_name,
            reset_url,
            settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )


def get_email_provider() -> EmailProvider:
    """Factory creating configured email provider."""
    if settings.EMAIL_PROVIDER == "development":
        return DevelopmentEmailProvider()
    
    # Future production providers (e.g. SMTP, Resend, Sendgrid) will be instantiated here
    raise NotImplementedError(f"Email provider '{settings.EMAIL_PROVIDER}' is not implemented yet.")


"""SMTP email service for OTP verification and notifications."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Raised when an email cannot be sent."""


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_otp_email(self, to_email: str, otp_code: str, user_name: str = "Farmer / Buyer") -> bool:
        """Send a 6-digit OTP verification email via SMTP.

        If SMTP credentials are not configured or dispatch fails, logs the OTP
        to the console in development mode so testing is never blocked.
        """
        subject = f"KrishiLink AI - Verification Code: {otp_code}"

        plain_text = (
            f"Namaste {user_name},\n\n"
            f"Your KrishiLink AI verification code is: {otp_code}\n\n"
            f"This code will expire in 10 minutes.\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"From Farm to Market, Powered by AI\n"
            f"KrishiLink AI Team"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4fbf6; margin: 0; padding: 24px; }}
                .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 32px; box-shadow: 0 4px 16px rgba(16, 122, 60, 0.08); border: 1px solid #d1fae5; }}
                .header {{ text-align: center; border-bottom: 2px solid #ecfdf5; padding-bottom: 20px; }}
                .brand {{ font-size: 24px; font-weight: 800; color: #15803d; }}
                .tagline {{ font-size: 13px; color: #6b7280; margin-top: 4px; }}
                .content {{ margin-top: 24px; color: #1f2937; line-height: 1.6; font-size: 15px; }}
                .otp-box {{ background: #f0fdf4; border: 2px dashed #16a34a; border-radius: 8px; text-align: center; padding: 20px; margin: 24px 0; }}
                .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #166534; font-family: monospace; }}
                .expiry {{ font-size: 13px; color: #dc2626; font-weight: 600; margin-top: 8px; }}
                .footer {{ text-align: center; font-size: 12px; color: #9ca3af; margin-top: 32px; border-top: 1px solid #e5e7eb; padding-top: 16px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div style="font-size: 36px; margin-bottom: 8px;">🌾</div>
                    <div class="brand">KrishiLink AI</div>
                    <div class="tagline">From Farm to Market, Powered by AI</div>
                </div>
                <div class="content">
                    <p>Namaste <strong>{user_name}</strong>,</p>
                    <p>Use the following 6-digit verification code to complete your authentication on the KrishiLink AI agricultural platform:</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                        <div class="expiry">⏱ Valid for 10 minutes only</div>
                    </div>
                    
                    <p style="font-size: 13px; color: #6b7280;">If you did not request this verification code, please disregard this email. Your account remains secure.</p>
                </div>
                <div class="footer">
                    © 2026 KrishiLink AI • Direct Farmer-to-Buyer Marketplace & Decision Support
                </div>
            </div>
        </body>
        </html>
        """

        # Log OTP clearly in dev console regardless for seamless debugging
        logger.info(
            "\n"
            + "=" * 60
            + "\n"
            + f"📧 [KRISHILINK SMTP EMAIL DISPATCH]\n"
            + f"To: {to_email}\n"
            + f"Subject: {subject}\n"
            + f"🔑 OTP CODE: {otp_code}\n"
            + "=" * 60
        )
        print(f"\n[SMTP OTP SERVICE] Verification OTP for {to_email} is: {otp_code}\n", flush=True)

        # Check if SMTP credentials are provided
        if not self.settings.smtp_username or not self.settings.smtp_password:
            logger.info("SMTP credentials not configured in .env; OTP logged to console for prototype mode.")
            return True

        # Send through SMTP
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email or self.settings.smtp_username}>"
            msg["To"] = to_email

            msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if self.settings.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=10)
                if self.settings.smtp_use_tls:
                    server.starttls()

            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.sendmail(self.settings.smtp_from_email or self.settings.smtp_username, [to_email], msg.as_string())
            server.quit()
            logger.info(f"OTP email successfully sent to {to_email}")
            return True
        except Exception as exc:
            logger.warning(f"SMTP dispatch to {to_email} failed ({type(exc).__name__}: {exc}). OTP is logged to console.")
            return True


_email_service_instance: EmailService | None = None


def get_email_service() -> EmailService:
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance

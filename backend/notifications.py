import resend
import logging
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotificationService:
    def __init__(self):
        self.settings = get_settings()
        if self.settings.resend_api_key:
            resend.api_key = self.settings.resend_api_key

    def send_lead_alert(self, lead_data: dict) -> bool:
        """
        Send an email alert for a new lead using Resend API.
        Returns True if sent, False if failed or skipped (no config).
        """
        # 1. Validation: Check if API Key is configured
        if not self.settings.resend_api_key or not self.settings.notification_email:
            logger.warning("⚠️ Resend API Key or Notification Email not found. Email notification SKIPPED. (Check .env)")
            return False

        # 2. Build and Send Email
        try:
            logger.info(f"Sending email via Resend to {self.settings.notification_email}...")
            
            params = {
                "from": f"Atlas-G Protocol <{self.settings.resend_from_email}>",
                "to": [self.settings.notification_email],
                "subject": f"🚀 New Lead: {lead_data.get('name', 'Unknown')}",
                "html": f"""
                <h2>New Contact Form Submission</h2>
                <p><strong>Time:</strong> {lead_data.get('timestamp')}</p>
                <hr>
                <p><strong>Name:</strong> {lead_data.get('name')}</p>
                <p><strong>Email:</strong> {lead_data.get('email')}</p>
                <p><strong>Message:</strong></p>
                <blockquote>{lead_data.get('message')}</blockquote>
                <hr>
                <p><em>ID: {lead_data.get('id')}</em></p>
                """
            }

            email = resend.Emails.send(params)
            
            logger.info(f"✅ Email notification sent! ID: {email.get('id')}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email via Resend: {str(e)}")
            return False

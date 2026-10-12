import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from core.settings import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    """Отправляет email с помощью SMTP."""
    msg = MIMEText(body, _charset='utf-8')
    msg['Subject'] = str(Header(subject, 'utf-8'))
    msg['From'] = settings.email_from
    msg['To'] = to_email

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.email_from, settings.email_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.email_from, settings.email_password)
                server.send_message(msg)

        logger.info('Email отправлен: %s', to_email)
    except smtplib.SMTPException as error:
        logger.error('Ошибка отправки email на %s: %s', to_email, error)
        raise

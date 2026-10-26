import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send the welcome email. Never raises: a mail outage must not block sign-up."""
    if not user.email:
        return False
    name = user.first_name or user.username
    main, _, accent = settings.SITE_NAME.rpartition(" ")
    if not main:
        main, accent = settings.SITE_NAME, ""
    ctx = {"user": user, "name": name, "site_url": settings.SITE_URL, "site_name": settings.SITE_NAME,
           "brand_main": main, "brand_accent": accent}
    subject = f"Welcome to {settings.SITE_NAME}, {name}"
    text_body = render_to_string("emails/welcome.txt", ctx)
    html_body = render_to_string("emails/welcome.html", ctx)
    message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
    message.attach_alternative(html_body, "text/html")
    try:
        message.send()
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Welcome email to %s failed", user.email)
        return False

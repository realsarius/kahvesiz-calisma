import logging
from typing import Dict, Tuple

import requests

from app.core.config import settings


logger = logging.getLogger(__name__)


def _resend_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }


def build_magic_link_url(token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/auth/verify?token={token}"


def build_email_verify_url(token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/auth/email-verify?token={token}"


def render_magic_link_email(token: str) -> Tuple[str, str, str]:
    url = build_magic_link_url(token)
    subject = "Kahvesiz Çalışma giriş bağlantın"
    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937;">
      <h2 style="margin-bottom: 8px;">Kahvesiz Çalışma</h2>
      <p>Hesabına giriş yapmak için aşağıdaki butona tıkla.</p>
      <p>
        <a href="{url}" style="display: inline-block; padding: 10px 16px; background: #0f766e; color: #ffffff; text-decoration: none; border-radius: 8px;">
          Magic Link ile Giriş Yap
        </a>
      </p>
      <p>Bu bağlantı {settings.magic_link_expire_minutes} dakika sonra geçersiz olur.</p>
      <p>Buton çalışmazsa bu adresi kopyalayabilirsin: <br /><code>{url}</code></p>
    </div>
    """.strip()
    text = (
        "Kahvesiz Çalışma giriş bağlantın\n\n"
        "Aşağıdaki bağlantıyı açarak hesabına giriş yapabilirsin:\n"
        f"{url}\n\n"
        f"Bağlantı {settings.magic_link_expire_minutes} dakika içinde geçerlidir."
    )
    return subject, html + "\n\n", text


def render_email_verify_email(token: str) -> Tuple[str, str, str]:
    url = build_email_verify_url(token)
    subject = "Kahvesiz Çalışma email doğrulama"
    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #1f2937;">
      <h2 style="margin-bottom: 8px;">Email doğrulama</h2>
      <p>Hesabını doğrulamak için aşağıdaki bağlantıyı kullan.</p>
      <p><a href="{url}">{url}</a></p>
      <p>Bu bağlantı kısa süre sonra geçersiz olacaktır.</p>
    </div>
    """.strip()
    text = (
        "Kahvesiz Çalışma email doğrulama\n\n"
        f"Doğrulama bağlantısı: {url}"
    )
    return subject, html + "\n\n", text


def send_email_via_resend(
    to_email: str,
    subject: str,
    html: str,
    text: str,
) -> None:
    if not settings.resend_api_key:
        logger.info("RESEND_API_KEY tanımlı değil, email gönderimi atlandı.")
        return

    if not settings.resend_from_email:
        logger.warning("RESEND_FROM_EMAIL boş, email gönderimi atlandı.")
        return

    payload = {
        "from": settings.resend_from_email,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    response = requests.post(
        "https://api.resend.com/emails",
        headers=_resend_headers(),
        json=payload,
        timeout=10,
    )
    if response.status_code >= 400:
        logger.error("Resend email başarısız: status=%s body=%s", response.status_code, response.text)
        response.raise_for_status()

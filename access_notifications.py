"""Authenticated Supabase database webhook for registration notifications."""
import hmac
import json
import os
import re
import urllib.error
import urllib.request
from email.utils import parseaddr
from uuid import UUID


APPROVAL_EMAIL = "chathot000@gmail.com"
MAX_BODY_BYTES = 16384


def handle_access_request(handler):
    """Accept INSERT events from clinic_users, never public browser requests."""
    secret = os.environ.get("ACCESS_REQUEST_WEBHOOK_SECRET", "")
    if len(secret) < 32:
        handler.send_json({"error": "Registration notifications are not configured."}, 503)
        return
    provided = handler.headers.get("Authorization", "").encode("utf-8")
    if not hmac.compare_digest(provided, f"Bearer {secret}".encode("utf-8")):
        handler.send_json({"error": "Unauthorized webhook."}, 401)
        return
    try:
        length = int(handler.headers.get("Content-Length", "0"))
        if not 0 < length <= MAX_BODY_BYTES:
            handler.send_json({"error": "Invalid payload size."}, 413)
            return
        event = json.loads(handler.rfile.read(length))
        if not isinstance(event, dict):
            raise ValueError("Invalid event")
        if (event.get("type"), event.get("schema"), event.get("table")) != (
            "INSERT", "public", "clinic_users"
        ):
            handler.send_json({"ignored": True})
            return
        record = event.get("record")
        if not isinstance(record, dict):
            raise ValueError("Invalid record")
        if record.get("approved") is True:
            handler.send_json({"ignored": True})
            return
        if record.get("approved") is not False:
            raise ValueError("Missing approval status")
        user_id = str(UUID(record.get("id", "")))
        email = record.get("email", "")
        if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Invalid email")
    except (ValueError, TypeError, AttributeError):
        handler.send_json({"error": "Invalid webhook payload."}, 400)
        return

    provider = os.environ.get("REGISTRATION_EMAIL_PROVIDER", "resend").lower()
    if provider not in ("brevo", "resend"):
        handler.send_json({"error": "Unknown email provider."}, 503)
        return
    api_key = os.environ.get("BREVO_API_KEY" if provider == "brevo" else "RESEND_API_KEY", "")
    sender = os.environ.get("REGISTRATION_EMAIL_FROM", "")
    if not api_key or not sender:
        handler.send_json({"error": "Email delivery is not configured."}, 503)
        return
    # The webhook contains profile fields only. Passwords and tokens are never emailed.
    message = {
        "from": sender,
        "to": [APPROVAL_EMAIL],
        "subject": "Denta Atelier — Cerere nouă de acces",
        "text": (
            "Un utilizator nou solicită acces la Denta Atelier.\n\n"
            f"Email: {email}\nID cont: {user_id}\n\n"
            "Pentru aprobare, deschide aplicația Denta Atelier și autentifică-te "
            "cu contul de administrator. Intră la Utilizatori → Vezi și aprobă cererile "
            "și apasă Aprobă lângă acest email.\n\n"
            "Utilizatorul nu poate accesa datele clinicii până la aprobare. "
            "Confirmarea adresei de email este separată de aprobarea accesului."
        ),
    }
    endpoint = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": f"clinic-access/{user_id}",
    }
    if provider == "brevo":
        sender_name, sender_email = parseaddr(sender)
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", sender_email):
            handler.send_json({"error": "Invalid email sender configuration."}, 503)
            return
        endpoint = "https://api.brevo.com/v3/smtp/email"
        headers = {"api-key": api_key}
        message = {
            "sender": {"name": sender_name or "Denta Atelier", "email": sender_email},
            "to": [{"email": APPROVAL_EMAIL}],
            "subject": message["subject"],
            "textContent": message["text"],
        }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(message).encode("utf-8"),
        headers={
            **headers,
            "Content-Type": "application/json",
            "User-Agent": "DentaAtelier/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            result = json.load(response)
        if not isinstance(result, dict) or not result.get("messageId" if provider == "brevo" else "id"):
            raise ValueError("Missing email ID")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        # A failed delivery must remain visible in webhook logs for an operator to retry.
        handler.send_json({"error": "Email delivery failed. Retry this webhook."}, 502)
        return
    handler.send_json({"sent": True})

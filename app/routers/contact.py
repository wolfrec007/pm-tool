"""Contact form router."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.csrf_utils import get_csrf_token, validate_csrf
from app.database import get_db
from app.flash import set_flash
from app.templates_setup import templates

router = APIRouter(tags=["contact"])


@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request):
    """Show contact form."""
    return templates.TemplateResponse(request, "contact.html", {
        "csrf_token": get_csrf_token(request),
        "error": "",
        "success": False,
    })


@router.post("/contact", response_class=HTMLResponse)
async def contact_submit(request: Request, db: Session = Depends(get_db)):
    """Handle contact form submission."""
    form_data = await request.form()
    if not validate_csrf(request, form_data.get("csrf_token")):
        return templates.TemplateResponse(request, "contact.html", {
            "csrf_token": get_csrf_token(request),
            "error": "Invalid form submission. Please try again.",
            "success": False,
        })

    name = form_data.get("name", "").strip()
    email = form_data.get("email", "").strip()
    inquiry_type = form_data.get("inquiry_type", "").strip()
    message = form_data.get("message", "").strip()

    # Validate
    errors = []
    if not name:
        errors.append("Name is required")
    if not email or "@" not in email:
        errors.append("Valid email is required")
    if not inquiry_type:
        errors.append("Please select an inquiry type")
    if not message:
        errors.append("Message is required")

    if errors:
        return templates.TemplateResponse(request, "contact.html", {
            "csrf_token": get_csrf_token(request),
            "error": " / ".join(errors),
            "success": False,
            "name": name,
            "email": email,
            "inquiry_type": inquiry_type,
            "message": message,
        })

    # Send email notification
    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        from app.services.email_service import get_smtp_connection

        # Format inquiry type for display
        inquiry_labels = {
            "license": "License Inquiry",
            "support": "Technical Support",
            "billing": "Billing & Payments",
            "feature": "Feature Request",
            "bug": "Bug Report",
            "partnership": "Partnership",
            "other": "Other",
        }
        inquiry_label = inquiry_labels.get(inquiry_type, inquiry_type)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"splanly Contact: {inquiry_label} - {name}"
        msg["From"] = f"splanly <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = "samarth@skilledca.in"
        msg["Reply-To"] = email

        html = f"""
        <h2>New Contact Form Submission</h2>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f5f5f5;">Name</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f5f5f5;">Email</td>
                <td style="padding: 8px; border: 1px solid #ddd;"><a href="mailto:{email}">{email}</a></td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f5f5f5;">Inquiry Type</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{inquiry_label}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f5f5f5;">Message</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{message}</td>
            </tr>
        </table>
        """

        msg.attach(MIMEText(html, "html"))

        with get_smtp_connection() as server:
            server.send_message(msg)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send contact email: {e}")

    return templates.TemplateResponse(request, "contact.html", {
        "csrf_token": get_csrf_token(request),
        "error": "",
        "success": True,
    })

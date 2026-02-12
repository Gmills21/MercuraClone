"""
Dedicated Email Inbound Route for multi-tenant organizations.
"""

import base64
import hashlib
import hmac
import io
import json
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import EmailStr

from app.config import settings
from app.database_sqlite import (
    add_quote_item, create_inbound_email, create_quote, 
    get_email_by_message_id, get_organization_by_slug, 
    get_user_by_email, update_email_status
)
from app.models import EmailStatus, InboundEmail, Quote, QuoteItem, QuoteStatus, WebhookPayload
from app.organization_service import OrganizationService
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inbound", tags=["email_inbound"])


def verify_sendgrid_signature(payload: bytes, signature: str) -> bool:
    """Verify SendGrid webhook signature."""
    try:
        if not settings.sendgrid_webhook_secret:
            return True  # Skip if secret not set for dev
        expected_signature = base64.b64encode(
            hmac.new(
                settings.sendgrid_webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).digest()
        ).decode()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"SendGrid signature verification error: {e}")
        return False


def verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    """Verify Mailgun webhook signature."""
    try:
        if not settings.mailgun_webhook_secret:
            return True  # Skip if secret not set for dev
        hmac_digest = hmac.new(
            key=settings.mailgun_webhook_secret.encode(),
            msg=f"{timestamp}{token}".encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, hmac_digest)
    except Exception as e:
        logger.error(f"Mailgun signature verification error: {e}")
        return False


def extract_slug_from_recipient(recipient: str) -> Optional[str]:
    """
    Extract organization slug from recipient email.
    Example: requests@acme.mercura.io -> acme
    """
    try:
        # Simple extraction: look for slug between @ and .mercura.io
        if '@' not in recipient:
            return None
        
        domain_part = recipient.split('@')[1]
        if '.mercura.io' in domain_part:
            return domain_part.split('.mercura.io')[0]
        
        # Fallback: if it's just slugs@domain.com, use the subdomain
        if '.' in domain_part:
            parts = domain_part.split('.')
            if len(parts) >= 2:
                return parts[0]
                
        return None
    except Exception as e:
        logger.error(f"Error extracting slug from recipient {recipient}: {e}")
        return None


async def process_dedicated_email(payload: WebhookPayload, org_id: str) -> dict:
    """
    Process email for a specific organization.
    """
    try:
        # 1. Check idempotency
        if payload.message_id:
            existing_email = get_email_by_message_id(payload.message_id)
            if existing_email:
                logger.info(f"Duplicate email skipped: {payload.message_id}")
                return {
                    "status": "skipped",
                    "email_id": existing_email['id'],
                    "message": "Email already processed"
                }

        # 2. Get organization to find owner/default user
        org = OrganizationService.get_organization(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        owner_id = org.owner_user_id

        # 3. Create inbound email record
        email_id = str(uuid.uuid4())
        email_record = {
            "id": email_id,
            "organization_id": org_id,
            "sender_email": payload.sender,
            "recipient_email": payload.recipient,
            "subject_line": payload.subject,
            "body_plain": payload.body_plain,
            "body_html": payload.body_html,
            "received_at": datetime.utcnow().isoformat(),
            "status": "processing",
            "has_attachments": len(payload.attachments) > 0,
            "attachment_count": len(payload.attachments),
            "message_id": payload.message_id,
            "metadata": {}
        }
        
        create_inbound_email(email_record)
        logger.info(f"Created inbound email record: {email_id} for org {org_id}")

        # 4. Extract data
        extraction_results = []
        
        # Process attachments first
        for attachment in payload.attachments:
            try:
                content_type = attachment.get('content-type', '').lower()
                filename = attachment.get('filename', '')
                content = attachment.get('content', '')  # Base64 encoded
                
                logger.info(f"Processing attachment: {filename} ({content_type})")
                
                if 'pdf' in content_type:
                    result = await gemini_service.extract_from_pdf(
                        pdf_base64=content,
                        context=f"Email subject: {payload.subject}"
                    )
                    extraction_results.append(result)
                    
                elif any(ext in filename.lower() for ext in ['.xlsx', '.xls', '.csv']):
                    file_bytes = base64.b64decode(content)
                    if filename.lower().endswith('.csv'):
                        df = pd.read_csv(io.BytesIO(file_bytes))
                    else:
                        df = pd.read_excel(io.BytesIO(file_bytes))
                    
                    spreadsheet_text = df.to_markdown()
                    result = await gemini_service.extract_from_text(
                        text=spreadsheet_text,
                        context=f"Spreadsheet file: {filename}. Email subject: {payload.subject}"
                    )
                    extraction_results.append(result)

                elif any(img_type in content_type for img_type in ['image/png', 'image/jpeg', 'image/jpg']):
                    img_type = 'png' if 'png' in content_type else 'jpg'
                    result = await gemini_service.extract_from_image(
                        image_base64=content,
                        image_type=img_type,
                        context=f"Email subject: {payload.subject}"
                    )
                    extraction_results.append(result)
                    
            except Exception as e:
                logger.error(f"Error processing attachment: {e}")
        
        # Try email body if no results
        if not extraction_results and payload.body_plain:
            result = await gemini_service.extract_from_text(
                text=payload.body_plain,
                context=f"Email subject: {payload.subject}"
            )
            extraction_results.append(result)

        # 5. Create Draft Quote
        all_extracted_items = []
        metadata = {}
        
        for result in extraction_results:
            if result.success and result.line_items:
                all_extracted_items.extend(result.line_items)
                # Capture metadata like deadline from Gemini response if available
                if hasattr(result, 'raw_response'):
                    try:
                        raw_json = json.loads(result.raw_response)
                        if 'metadata' in raw_json:
                            metadata.update(raw_json['metadata'])
                    except:
                        pass

        if all_extracted_items:
            # Create Quote
            quote_id = str(uuid.uuid4())
            token = str(uuid.uuid4())[:12]
            
            subtotal = sum(float(item.get('total_price') or item.get('unit_price', 0) * item.get('quantity', 1)) for item in all_extracted_items)
            
            # Simple customer lookup or create "Unknown Customer"
            # For now, we'll use a placeholder customer or the sender
            from app.database_sqlite import get_customer_by_email, create_customer
            customer = get_customer_by_email(payload.sender, org_id)
            if not customer:
                # Create a minimal customer
                cust_id = str(uuid.uuid4())
                create_customer({
                    "id": cust_id,
                    "organization_id": org_id,
                    "name": payload.sender.split('@')[0],
                    "email": payload.sender,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
                customer_id = cust_id
            else:
                customer_id = customer['id']

            quote_data = {
                "id": quote_id,
                "organization_id": org_id,
                "customer_id": customer_id,
                "status": "draft",
                "subtotal": subtotal,
                "tax_rate": 0,
                "tax_amount": 0,
                "total": subtotal,
                "token": token,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "notes": f"Automatically captured from email: {payload.subject}",
                "metadata": {
                    "source_email_id": email_id,
                    "source_subject": payload.subject,
                    "deadline": metadata.get('deadline')
                }
            }
            
            if create_quote(quote_data):
                for item in all_extracted_items:
                    add_quote_item({
                        "id": str(uuid.uuid4()),
                        "quote_id": quote_id,
                        "description": item.get('description') or item.get('item_name') or "Unknown Item",
                        "sku": item.get('sku'),
                        "quantity": float(item.get('quantity') or 1),
                        "unit_price": float(item.get('unit_price') or 0),
                        "total_price": float(item.get('total_price') or 0),
                    })
                
                update_email_status(email_id, "processed")
                return {
                    "status": "success",
                    "email_id": email_id,
                    "quote_id": quote_id,
                    "items": len(all_extracted_items)
                }

        update_email_status(email_id, "failed", "No data could be extracted")
        return {"status": "failed", "email_id": email_id, "message": "No data extracted"}

    except Exception as e:
        logger.error(f"Error in process_dedicated_email: {e}")
        if 'email_id' in locals():
            update_email_status(email_id, "failed", str(e))
        raise


@router.post("/webhook")
async def email_webhook(
    request: Request,
    x_sendgrid_signature: Optional[str] = Header(None)
):
    """
    Universal webhook for dedicated inbound emails.
    """
    body = await request.body()
    form_data = await request.form()
    
    # SendGrid format
    sender = form_data.get('from')
    recipient = form_data.get('to')
    subject = form_data.get('subject')
    body_plain = form_data.get('text')
    body_html = form_data.get('html')
    message_id = form_data.get('message-id')
    
    if not recipient:
        # Mailgun format
        sender = form_data.get('sender')
        recipient = form_data.get('recipient')
        message_id = form_data.get('Message-Id')
        body_plain = form_data.get('body-plain')
    
    if not recipient:
        raise HTTPException(status_code=400, detail="Missing recipient")

    # Extract organization slug
    slug = extract_slug_from_recipient(recipient)
    if not slug:
        logger.warning(f"Could not extract slug from recipient: {recipient}")
        # Try finding by domain as fallback
        if '@' in recipient:
            domain = recipient.split('@')[1]
            org = OrganizationService.get_organization_by_slug(domain.split('.')[0])
        else:
            org = None
    else:
        org = OrganizationService.get_organization_by_slug(slug)
    
    if not org:
        logger.error(f"Organization not found for slug: {slug} or recipient: {recipient}")
        raise HTTPException(status_code=404, detail=f"Organization not found for {recipient}")

    # Build payload
    payload = WebhookPayload(
        provider="sendgrid" if x_sendgrid_signature else "mailgun",
        sender=sender,
        recipient=recipient,
        subject=subject,
        body_plain=body_plain,
        body_html=body_html,
        attachments=[],
        message_id=message_id
    )
    
    # Parse attachments
    # SendGrid format: attachment1, attachment2...
    attachment_count = int(form_data.get('attachments', '0'))
    for i in range(1, attachment_count + 1):
        attachment_file = form_data.get(f'attachment{i}')
        if attachment_file:
            content = base64.b64encode(await attachment_file.read()).decode()
            payload.attachments.append({
                'filename': attachment_file.filename,
                'content-type': attachment_file.content_type,
                'content': content
            })
    
    # Mailgun format: attachment-1, attachment-2...
    mg_attachment_count = int(form_data.get('attachment-count', '0'))
    for i in range(1, mg_attachment_count + 1):
        attachment_file = form_data.get(f'attachment-{i}')
        if attachment_file:
            content = base64.b64encode(await attachment_file.read()).decode()
            payload.attachments.append({
                'filename': attachment_file.filename,
                'content-type': attachment_file.content_type,
                'content': content
            })

    result = await process_dedicated_email(payload, org.id)
    return result

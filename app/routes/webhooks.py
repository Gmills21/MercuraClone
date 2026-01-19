"""
Email webhook handlers for SendGrid and Mailgun.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from app.models import WebhookPayload, InboundEmail, EmailStatus, Quote, QuoteItem, QuoteStatus
from app.database import db
from app.services.gemini_service import gemini_service
from app.config import settings
import hmac
import hashlib
import base64
import logging
import pandas as pd
import io
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_sendgrid_signature(payload: bytes, signature: str) -> bool:
    """Verify SendGrid webhook signature."""
    try:
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


def verify_mailgun_signature(
    timestamp: str,
    token: str,
    signature: str
) -> bool:
    """Verify Mailgun webhook signature."""
    try:
        hmac_digest = hmac.new(
            key=settings.mailgun_webhook_secret.encode(),
            msg=f"{timestamp}{token}".encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, hmac_digest)
    except Exception as e:
        logger.error(f"Mailgun signature verification error: {e}")
        return False


async def process_email_webhook(payload: WebhookPayload) -> dict:
    """
    Core email processing logic.
    
    Steps:
    1. Validate sender is authorized user
    2. Create inbound email record
    3. Extract data from email body and attachments
    4. Store line items in database
    5. Update email status
    """
    try:
        # Step 1: Check if sender is authorized
        user = await db.get_user_by_email(payload.sender)
        if not user:
            logger.warning(f"Unauthorized sender: {payload.sender}")
            raise HTTPException(
                status_code=403,
                detail=f"Sender {payload.sender} is not authorized"
            )
        
        if not user['is_active']:
            raise HTTPException(
                status_code=403,
                detail="User account is inactive"
            )
        
        # Check quota
        if user['emails_processed_today'] >= user['email_quota_per_day']:
            raise HTTPException(
                status_code=429,
                detail="Daily email quota exceeded"
            )
        
        # Check idempotency
        if payload.message_id:
            existing_email = await db.get_email_by_message_id(payload.message_id)
            if existing_email:
                logger.info(f"Duplicate email skipped: {payload.message_id}")
                return {
                    "status": "skipped",
                    "email_id": existing_email['id'],
                    "message": "Email already processed"
                }
        
        # Step 2: Create inbound email record
        inbound_email = InboundEmail(
            sender_email=payload.sender,
            subject_line=payload.subject,
            received_at=payload.timestamp or datetime.utcnow(),
            status=EmailStatus.PENDING,
            has_attachments=len(payload.attachments) > 0,
            attachment_count=len(payload.attachments),
            user_id=user['id'],
            message_id=payload.message_id
        )
        
        email_id = await db.create_inbound_email(inbound_email)
        logger.info(f"Created inbound email record: {email_id}")
        
        # Update status to processing
        await db.update_email_status(email_id, EmailStatus.PROCESSING)
        
        # Step 3: Extract data
        extraction_results = []
        
        # Process attachments first (higher priority)
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
                    logger.info(f"Processing spreadsheet attachment: {filename}")
                    try:
                        # Decode base64
                        file_bytes = base64.b64decode(content)
                        
                        # Read with Pandas
                        if filename.lower().endswith('.csv'):
                            df = pd.read_csv(io.BytesIO(file_bytes))
                        else:
                            df = pd.read_excel(io.BytesIO(file_bytes))
                        
                        # Convert to text/markdown for Gemini
                        spreadsheet_text = df.to_markdown()
                        
                        # Extract using Gemini text engine
                        result = await gemini_service.extract_from_text(
                            text=spreadsheet_text,
                            context=f"Spreadsheet file: {filename}. Email subject: {payload.subject}"
                        )
                        extraction_results.append(result)
                    except Exception as spreadsheet_err:
                        logger.error(f"Failed to process spreadsheet {filename}: {spreadsheet_err}")

                elif any(img_type in content_type for img_type in ['image/png', 'image/jpeg', 'image/jpg']):
                    # Determine image type
                    img_type = 'png' if 'png' in content_type else 'jpg'
                    result = await gemini_service.extract_from_image(
                        image_base64=content,
                        image_type=img_type,
                        context=f"Email subject: {payload.subject}"
                    )
                    extraction_results.append(result)
                    
            except Exception as e:
                logger.error(f"Error processing attachment {filename}: {e}")
        
        # If no attachments or attachment processing failed, try email body
        if not extraction_results and payload.body_plain:
            logger.info("Processing email body text")
            result = await gemini_service.extract_from_text(
                text=payload.body_plain,
                context=f"Email subject: {payload.subject}"
            )
            extraction_results.append(result)
        
        # Step 4: Store line items and Create Draft Quote
        total_items_created = 0
        all_extracted_items = []
        
        for result in extraction_results:
            if result.success and result.line_items:
                # Add confidence scores to items
                items_with_confidence = [
                    {**item, 'confidence_score': result.confidence_score}
                    for item in result.line_items
                ]
                
                item_ids = await db.create_line_items(email_id, items_with_confidence)
                total_items_created += len(item_ids)
                all_extracted_items.extend(result.line_items)
                logger.info(f"Created {len(item_ids)} line items")

        # Create Draft Quote from extracted items
        if all_extracted_items:
            try:
                # Calculate total
                total_amount = sum(
                    float(item.get('total_price') or 0) 
                    for item in all_extracted_items
                )

                # Create Quote Items
                quote_items = []
                for item in all_extracted_items:
                    quote_items.append(QuoteItem(
                        quote_id="pending", # Will be set by db.create_quote
                        description=item.get('description') or item.get('item_name') or "Unknown Item",
                        sku=item.get('sku'),
                        quantity=int(item.get('quantity') or 1),
                        unit_price=float(item.get('unit_price') or 0.0),
                        total_price=float(item.get('total_price') or 0.0),
                        metadata={"original_extraction": item}
                    ))

                # Create Quote
                # Generate a simple quote number
                quote_number = f"RFQ-{datetime.utcnow().strftime('%Y%m%d')}-{email_id[:8]}"
                
                quote = Quote(
                    user_id=user['id'],
                    quote_number=quote_number,
                    status=QuoteStatus.DRAFT,
                    total_amount=total_amount,
                    items=quote_items,
                    metadata={
                        "source_email_id": email_id, 
                        "source_subject": payload.subject,
                        "source_sender": payload.sender
                    }
                )

                quote_id = await db.create_quote(quote)
                logger.info(f"Created draft quote {quote_id} from email {email_id}")
                
            except Exception as e:
                logger.error(f"Error creating draft quote: {e}")
                # Continue execution to update email status
        
        # Step 5: Update email status
        if total_items_created > 0:
            await db.update_email_status(email_id, EmailStatus.PROCESSED)
            status = "success"
        else:
            await db.update_email_status(
                email_id,
                EmailStatus.FAILED,
                "No data could be extracted from email or attachments"
            )
            status = "failed"
        
        # Increment user's email count
        await db.increment_user_email_count(user['id'])
        
        return {
            "status": status,
            "email_id": email_id,
            "items_extracted": total_items_created,
            "message": f"Processed email from {payload.sender}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email processing error: {e}")
        if 'email_id' in locals():
            await db.update_email_status(
                email_id,
                EmailStatus.FAILED,
                str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inbound-email")
async def inbound_email_webhook(
    request: Request,
    x_sendgrid_signature: Optional[str] = Header(None),
    timestamp: Optional[str] = Header(None),
    token: Optional[str] = Header(None),
    signature: Optional[str] = Header(None)
):
    """
    Universal webhook endpoint for both SendGrid and Mailgun.
    
    The provider is determined by which headers are present.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Determine provider and verify signature
        if x_sendgrid_signature:
            # SendGrid webhook
            if not verify_sendgrid_signature(body, x_sendgrid_signature):
                raise HTTPException(status_code=401, detail="Invalid SendGrid signature")
            
            provider = "sendgrid"
            
        elif timestamp and token and signature:
            # Mailgun webhook
            if not verify_mailgun_signature(timestamp, token, signature):
                raise HTTPException(status_code=401, detail="Invalid Mailgun signature")
            
            provider = "mailgun"
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Missing authentication headers"
            )
        
        # Parse form data
        form_data = await request.form()
        
        # Extract common fields based on provider
        if provider == "sendgrid":
            payload = WebhookPayload(
                provider="sendgrid",
                sender=form_data.get('from'),
                recipient=form_data.get('to'),
                subject=form_data.get('subject'),
                body_plain=form_data.get('text'),
                body_html=form_data.get('html'),
                attachments=[],
                message_id=form_data.get('message-id')
            )
            
            # Parse attachments
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
        
        else:  # mailgun
            payload = WebhookPayload(
                provider="mailgun",
                sender=form_data.get('sender'),
                recipient=form_data.get('recipient'),
                subject=form_data.get('subject'),
                body_plain=form_data.get('body-plain'),
                body_html=form_data.get('body-html'),
                attachments=[],
                message_id=form_data.get('Message-Id')
            )
            
            # Parse attachments
            attachment_count = int(form_data.get('attachment-count', '0'))
            for i in range(1, attachment_count + 1):
                attachment_file = form_data.get(f'attachment-{i}')
                if attachment_file:
                    content = base64.b64encode(await attachment_file.read()).decode()
                    payload.attachments.append({
                        'filename': attachment_file.filename,
                        'content-type': attachment_file.content_type,
                        'content': content
                    })
        
        # Process the email
        result = await process_email_webhook(payload)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook."""
    return {
        "status": "healthy",
        "provider": settings.email_provider,
        "timestamp": datetime.utcnow().isoformat()
    }

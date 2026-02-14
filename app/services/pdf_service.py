"""
PDF Quote Generation Service
Generates professional, branded PDF quotes for customers.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from io import BytesIO
from dataclasses import dataclass
import base64

# Try to import reportlab, but handle gracefully
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation disabled.")

from app.config import settings
from app.database_sqlite import get_quote_with_items, get_organization
from app.errors import (
    AppError,
    ErrorCategory,
    ErrorSeverity,
    MercuraException,
    not_found
)


@dataclass
class PDFConfig:
    """Configuration for PDF quote generation."""
    company_name: str = "Your Company"
    company_logo: Optional[str] = None  # Base64 encoded logo
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    accent_color: str = "#2563eb"  # Blue default
    terms_and_conditions: str = ""


class PDFQuoteService:
    """Service for generating professional PDF quotes."""
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise MercuraException(
                AppError(
                    category=ErrorCategory.INTERNAL_ERROR,
                    code="PDF_LIBRARY_MISSING",
                    message="PDF generation is not available. Required library is not installed.",
                    severity=ErrorSeverity.ERROR,
                    http_status=503,
                    retryable=False,
                    suggested_action="Contact support to enable PDF generation."
                )
            )
    
    def generate_quote_pdf(
        self,
        quote_id: str,
        organization_id: Optional[str] = None,
        config: Optional[PDFConfig] = None
    ) -> bytes:
        """
        Generate a professional PDF quote.
        
        Args:
            quote_id: The quote ID to generate PDF for
            organization_id: Optional org ID for branding
            config: Optional custom PDF configuration
            
        Returns:
            PDF file as bytes
        """
        # Fetch quote data
        quote = get_quote_with_items(quote_id, organization_id)
        if not quote:
            raise MercuraException(not_found("Quote"))
        
        # Get org config for branding
        if organization_id and not config:
            org = get_organization(organization_id)
            if org:
                config = PDFConfig(
                    company_name=org.get('name', 'Your Company'),
                    company_address=org.get('address', ''),
                    company_phone=org.get('phone', ''),
                    company_email=org.get('email', ''),
                    accent_color=org.get('brand_color', '#2563eb'),
                    terms_and_conditions=org.get('terms', '')
                )
        
        if not config:
            config = PDFConfig()
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build content
        story = []
        styles = self._create_styles(config.accent_color)
        
        # Header with company info
        story.extend(self._build_header(quote, config, styles))
        story.append(Spacer(1, 0.3*inch))
        
        # Quote info section
        story.extend(self._build_quote_info(quote, styles))
        story.append(Spacer(1, 0.3*inch))
        
        # Line items table
        story.extend(self._build_line_items(quote, config, styles))
        story.append(Spacer(1, 0.3*inch))
        
        # Totals section
        story.extend(self._build_totals(quote, config, styles))
        story.append(Spacer(1, 0.3*inch))
        
        # Terms and notes
        story.extend(self._build_footer(quote, config, styles))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _create_styles(self, accent_color: str) -> Dict[str, "ParagraphStyle"]:
        """Create paragraph styles for the PDF."""
        styles = getSampleStyleSheet()
        
        # Header style
        styles.add(ParagraphStyle(
            name='CompanyName',
            fontSize=24,
            textColor=colors.HexColor(accent_color),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Quote title
        styles.add(ParagraphStyle(
            name='QuoteTitle',
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Section headers
        styles.add(ParagraphStyle(
            name='SectionHeader',
            fontSize=12,
            textColor=colors.HexColor(accent_color),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Normal text
        styles.add(ParagraphStyle(
            name='NormalText',
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            leading=14
        ))
        
        # Small text
        styles.add(ParagraphStyle(
            name='SmallText',
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),
            leading=12
        ))
        
        # Right aligned
        styles.add(ParagraphStyle(
            name='RightAlign',
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            alignment=TA_RIGHT
        ))
        
        return styles
    
    def _build_header(
        self,
        quote: Dict[str, Any],
        config: PDFConfig,
        styles: Dict[str, "ParagraphStyle"]
    ) -> List[Any]:
        """Build the header section with company info."""
        elements = []
        
        # Company name and quote title side by side
        header_data = [
            [
                Paragraph(f"<b>{config.company_name}</b>", styles['CompanyName']),
                Paragraph("<b>QUOTE</b>", styles['QuoteTitle'])
            ]
        ]
        
        if config.company_address or config.company_phone or config.company_email:
            contact_info = []
            if config.company_address:
                contact_info.append(config.company_address)
            if config.company_phone:
                contact_info.append(f"Tel: {config.company_phone}")
            if config.company_email:
                contact_info.append(f"Email: {config.company_email}")
            
            header_data[0][0] = Paragraph(
                f"<b>{config.company_name}</b><br/><br/>" + 
                "<br/>".join(contact_info),
                styles['CompanyName']
            )
        
        header_table = Table(header_data, colWidths=[4*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Horizontal line
        line_table = Table([['']], colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(config.accent_color)),
        ]))
        elements.append(line_table)
        
        return elements
    
    def _build_quote_info(
        self,
        quote: Dict[str, Any],
        styles: Dict[str, "ParagraphStyle"]
    ) -> List[Any]:
        """Build quote metadata section."""
        elements = []
        
        # Customer info and quote details
        customer = quote.get('customers', {})
        customer_name = customer.get('company_name') or customer.get('name') or 'Customer'
        
        quote_info = [
            ['QUOTE TO:', 'QUOTE DETAILS:'],
            [customer_name, f"Quote #: {quote.get('quote_number', 'N/A')}"],
        ]
        
        # Add customer contact info if available
        customer_details = []
        if customer.get('email'):
            customer_details.append(customer['email'])
        if customer.get('phone'):
            customer_details.append(customer['phone'])
        if customer.get('address'):
            customer_details.append(customer['address'])
        
        if customer_details:
            quote_info[1][0] = customer_name + "<br/>" + "<br/>".join(customer_details)
        
        # Add quote dates
        created_at = quote.get('created_at', '')
        if created_at:
            try:
                date_str = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%B %d, %Y')
                quote_info.append(['', f"Date: {date_str}"])
            except:
                pass
        
        if quote.get('valid_until'):
            try:
                valid_str = datetime.fromisoformat(quote['valid_until'].replace('Z', '+00:00')).strftime('%B %d, %Y')
                quote_info.append(['', f"Valid Until: {valid_str}"])
            except:
                pass
        
        info_table = Table(quote_info, colWidths=[3.25*inch, 3.25*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6b7280')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _build_line_items(
        self,
        quote: Dict[str, Any],
        config: PDFConfig,
        styles: Dict[str, "ParagraphStyle"]
    ) -> List[Any]:
        """Build the line items table."""
        elements = []
        
        # Table header
        table_data = [['Item', 'Description', 'Qty', 'Unit Price', 'Total']]
        
        # Add line items
        items = quote.get('items', [])
        for i, item in enumerate(items, 1):
            description = item.get('description') or item.get('product_name') or 'Item'
            sku = item.get('sku', '')
            if sku:
                description = f"{description}<br/><span color='#6b7280'>(SKU: {sku})</span>"
            
            row = [
                str(i),
                Paragraph(description, styles['NormalText']),
                str(item.get('quantity', 1)),
                f"${float(item.get('unit_price', 0)):,.2f}",
                f"${float(item.get('total_price', 0)):,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        item_table = Table(table_data, colWidths=[0.5*inch, 3.5*inch, 0.75*inch, 1*inch, 1*inch])
        
        # Style the table
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(config.accent_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Qty centered
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Prices right aligned
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ])
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb'))
        
        item_table.setStyle(table_style)
        elements.append(item_table)
        
        return elements
    
    def _build_totals(
        self,
        quote: Dict[str, Any],
        config: PDFConfig,
        styles: Dict[str, "ParagraphStyle"]
    ) -> List[Any]:
        """Build the totals section."""
        elements = []
        
        subtotal = float(quote.get('subtotal', 0))
        tax_amount = float(quote.get('tax_amount', 0))
        total = float(quote.get('total', 0))
        tax_rate = float(quote.get('tax_rate', 0))
        
        totals_data = [
            ['Subtotal:', f"${subtotal:,.2f}"],
        ]
        
        if tax_amount > 0:
            totals_data.append([f"Tax ({tax_rate}%):", f"${tax_amount:,.2f}"])
        
        totals_data.append(['TOTAL:', f"${total:,.2f}"])
        
        totals_table = Table(totals_data, colWidths=[5*inch, 1.5*inch])
        
        # Style totals
        totals_style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        
        # Highlight total row
        totals_style.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor(config.accent_color))
        totals_style.add('TEXTCOLOR', (0, -1), (-1, -1), colors.white)
        totals_style.add('TOPPADDING', (0, -1), (-1, -1), 10)
        totals_style.add('BOTTOMPADDING', (0, -1), (-1, -1), 10)
        
        totals_table.setStyle(totals_style)
        elements.append(totals_table)
        
        return elements
    
    def _build_footer(
        self,
        quote: Dict[str, Any],
        config: PDFConfig,
        styles: Dict[str, "ParagraphStyle"]
    ) -> List[Any]:
        """Build footer with terms and notes."""
        elements = []
        
        # Notes
        if quote.get('notes'):
            elements.append(Paragraph("<b>Notes:</b>", styles['SectionHeader']))
            elements.append(Paragraph(quote['notes'], styles['NormalText']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Terms and conditions
        if config.terms_and_conditions:
            elements.append(Paragraph("<b>Terms & Conditions:</b>", styles['SectionHeader']))
            elements.append(Paragraph(config.terms_and_conditions, styles['SmallText']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Thank you message
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "Thank you for your business!",
            ParagraphStyle(
                name='ThankYou',
                fontSize=11,
                textColor=colors.HexColor('#6b7280'),
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            )
        ))
        
        return elements


# Global instance
pdf_service: Optional[PDFQuoteService] = None
if REPORTLAB_AVAILABLE:
    try:
        pdf_service = PDFQuoteService()
    except Exception as e:
        print(f"Failed to initialize PDF service: {e}")

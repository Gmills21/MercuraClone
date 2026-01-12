"""
Export service for generating CSV, Excel, and Google Sheets exports.
"""

import pandas as pd
from app.database import db
from app.config import settings
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data to various formats."""
    
    def __init__(self):
        """Initialize export service."""
        os.makedirs(settings.export_temp_dir, exist_ok=True)
    
    async def export_to_csv(
        self,
        email_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_metadata: bool = False
    ) -> str:
        """
        Export line items to CSV file.
        
        Returns: Path to generated CSV file
        """
        try:
            # Fetch data
            data = await self._fetch_line_items(
                email_ids, start_date, end_date, user_id
            )
            
            if not data:
                raise ValueError("No data found for export")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean and format data
            df = self._clean_dataframe(df, include_metadata)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"mercura_export_{timestamp}.csv"
            filepath = os.path.join(settings.export_temp_dir, filename)
            
            # Export to CSV
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"CSV export created: {filepath} ({len(df)} rows)")
            
            return filepath
            
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            raise
    
    async def export_to_excel(
        self,
        email_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_metadata: bool = False
    ) -> str:
        """
        Export line items to Excel file.
        
        Returns: Path to generated Excel file
        """
        try:
            # Fetch data
            data = await self._fetch_line_items(
                email_ids, start_date, end_date, user_id
            )
            
            if not data:
                raise ValueError("No data found for export")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean and format data
            df = self._clean_dataframe(df, include_metadata)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"mercura_export_{timestamp}.xlsx"
            filepath = os.path.join(settings.export_temp_dir, filename)
            
            # Export to Excel with formatting
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Data']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#4A90E2',
                    'font_color': 'white',
                    'border': 1
                })
                
                # Format header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column widths
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
            
            logger.info(f"Excel export created: {filepath} ({len(df)} rows)")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Excel export error: {e}")
            raise
    
    async def export_to_google_sheets(
        self,
        sheet_id: str,
        email_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        include_metadata: bool = False
    ) -> dict:
        """
        Export line items to Google Sheets.
        
        Returns: Dictionary with sheet URL and update info
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials
            
            # Fetch data
            data = await self._fetch_line_items(
                email_ids, start_date, end_date, user_id
            )
            
            if not data:
                raise ValueError("No data found for export")
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Clean and format data
            df = self._clean_dataframe(df, include_metadata)
            
            # Authenticate with Google Sheets
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                settings.google_sheets_credentials_path,
                scopes=scopes
            )
            
            client = gspread.authorize(creds)
            
            # Open the sheet
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.get_worksheet(0)  # First worksheet
            
            # Clear existing data
            worksheet.clear()
            
            # Update with new data
            # Convert DataFrame to list of lists
            data_to_write = [df.columns.values.tolist()] + df.values.tolist()
            
            worksheet.update(
                range_name='A1',
                values=data_to_write
            )
            
            # Format header row
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.29, 'green': 0.56, 'blue': 0.89},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            logger.info(f"Google Sheets export completed: {sheet_id} ({len(df)} rows)")
            
            return {
                'sheet_id': sheet_id,
                'sheet_url': sheet.url,
                'rows_updated': len(df),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Google Sheets export error: {e}")
            raise
    
    async def _fetch_line_items(
        self,
        email_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch line items based on filters."""
        if email_ids:
            # Fetch by specific email IDs
            all_items = []
            for email_id in email_ids:
                items = await db.get_line_items_by_email(email_id)
                all_items.extend(items)
            return all_items
        
        elif start_date and end_date:
            # Fetch by date range
            return await db.get_line_items_by_date_range(
                start_date, end_date, user_id
            )
        
        else:
            raise ValueError("Must provide either email_ids or date range")
    
    def _clean_dataframe(
        self,
        df: pd.DataFrame,
        include_metadata: bool
    ) -> pd.DataFrame:
        """Clean and format DataFrame for export."""
        # Select columns to include
        base_columns = [
            'item_name',
            'sku',
            'description',
            'quantity',
            'unit_price',
            'total_price',
            'confidence_score'
        ]
        
        if include_metadata:
            base_columns.extend(['email_id', 'extracted_at', 'metadata'])
        
        # Filter to existing columns
        columns = [col for col in base_columns if col in df.columns]
        df = df[columns]
        
        # Format currency columns
        if 'unit_price' in df.columns:
            df['unit_price'] = df['unit_price'].apply(
                lambda x: f"${x:.2f}" if pd.notnull(x) else ""
            )
        
        if 'total_price' in df.columns:
            df['total_price'] = df['total_price'].apply(
                lambda x: f"${x:.2f}" if pd.notnull(x) else ""
            )
        
        # Format confidence score as percentage
        if 'confidence_score' in df.columns:
            df['confidence_score'] = df['confidence_score'].apply(
                lambda x: f"{x*100:.1f}%" if pd.notnull(x) else ""
            )
        
        # Rename columns to be more user-friendly
        column_names = {
            'item_name': 'Item Name',
            'sku': 'SKU',
            'description': 'Description',
            'quantity': 'Quantity',
            'unit_price': 'Unit Price',
            'total_price': 'Total Price',
            'confidence_score': 'Confidence',
            'email_id': 'Email ID',
            'extracted_at': 'Extracted At',
            'metadata': 'Metadata'
        }
        
        df = df.rename(columns=column_names)
        
        return df


# Global export service instance
export_service = ExportService()

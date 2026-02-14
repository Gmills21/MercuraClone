"""
CSV Import Service
Drag-and-drop import for product catalogs and customer data.
"""

from typing import List, Dict, Any, Optional, Tuple
from io import StringIO
import csv
from dataclasses import dataclass
from app.errors import (
    ValidationException,
    validation_error
)

# Try to import pandas for better CSV handling
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    imported_count: int
    failed_count: int
    errors: List[str]
    warnings: List[str]
    preview: Optional[List[Dict[str, Any]]] = None


class CSVImportService:
    """
    Service for importing data from CSV/Excel files.
    
    Supports:
    - Product catalogs
    - Customer lists
    - Competitor SKU mappings
    - Quote line items
    """
    
    # Column mappings for common variations
    PRODUCT_COLUMNS = {
        'sku': ['sku', 'part_number', 'part no', 'part #', 'item_code', 'item code', 'product_code', 'product id'],
        'name': ['name', 'product_name', 'product name', 'item_name', 'item name', 'description', 'title'],
        'description': ['description', 'desc', 'long_description', 'details'],
        'price': ['price', 'unit_price', 'unit price', 'cost', 'list_price', 'list price', 'msrp'],
        'cost_price': ['cost', 'cost_price', 'cost price', 'wholesale', 'wholesale_price', 'purchase_price'],
        'category': ['category', 'type', 'product_type', 'product type', 'group', 'family'],
        'manufacturer': ['manufacturer', 'brand', 'vendor', 'supplier', 'mfg'],
        'upc': ['upc', 'barcode', 'ean', 'gtin']
    }
    
    CUSTOMER_COLUMNS = {
        'name': ['name', 'company_name', 'company', 'customer_name', 'customer name', 'organization'],
        'email': ['email', 'e-mail', 'email_address', 'email address', 'contact_email'],
        'phone': ['phone', 'phone_number', 'phone number', 'telephone', 'contact_phone', 'tel'],
        'address': ['address', 'street', 'street_address', 'street address'],
        'city': ['city', 'town'],
        'state': ['state', 'province', 'region'],
        'zip': ['zip', 'zipcode', 'zip_code', 'postal', 'postal_code', 'postal code'],
        'country': ['country', 'nation'],
        'contact_name': ['contact_name', 'contact name', 'primary_contact', 'contact person']
    }
    
    COMPETITOR_COLUMNS = {
        'your_sku': ['your_sku', 'our_sku', 'internal_sku', 'sku', 'part_number'],
        'competitor_sku': ['competitor_sku', 'comp_sku', 'their_sku', 'competitor_part', 'competitor_part_number'],
        'competitor_name': ['competitor_name', 'competitor', 'competitor brand', 'brand'],
        'confidence': ['confidence', 'match_confidence', 'score', 'match_score']
    }
    
    def __init__(self):
        self.max_preview_rows = 5
        self.max_import_rows = 10000
    
    def detect_columns(self, headers: List[str], column_map: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Detect which columns map to which fields.
        
        Returns:
            Dict mapping field names to actual column names
        """
        detected = {}
        headers_lower = [h.lower().strip().replace('_', ' ').replace('-', ' ') for h in headers]
        
        for field, possible_names in column_map.items():
            for name in possible_names:
                name_lower = name.lower().strip()
                # Exact match
                if name_lower in headers_lower:
                    idx = headers_lower.index(name_lower)
                    detected[field] = headers[idx]
                    break
                # Substring match
                for i, h in enumerate(headers_lower):
                    if name_lower in h or h in name_lower:
                        detected[field] = headers[i]
                        break
        
        return detected
    
    def parse_csv(
        self,
        file_content: bytes,
        import_type: str = "products",
        delimiter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Parse CSV/Excel file content.
        
        Args:
            file_content: Raw file bytes
            import_type: 'products', 'customers', or 'competitors'
            delimiter: CSV delimiter (auto-detect if None)
            
        Returns:
            Tuple of (rows_data, headers)
        """
        # Try to decode
        try:
            text_content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_content = file_content.decode('latin-1')
            except:
                raise ValidationException(
                    validation_error(
                        field="file",
                        message="Unable to decode file. Please ensure it's a valid CSV or Excel file encoded in UTF-8 or Latin-1."
                    )
                )
        
        # Detect delimiter if not specified
        if not delimiter:
            first_line = text_content.split('\n')[0]
            if '\t' in first_line:
                delimiter = '\t'
            elif ';' in first_line and ',' not in first_line:
                delimiter = ';'
            else:
                delimiter = ','
        
        # Parse CSV
        reader = csv.DictReader(StringIO(text_content), delimiter=delimiter)
        headers = reader.fieldnames or []
        rows = list(reader)
        
        return rows, headers
    
    def preview_import(
        self,
        file_content: bytes,
        import_type: str = "products"
    ) -> Dict[str, Any]:
        """
        Preview an import without actually importing.
        
        Returns:
            Dict with column mapping, sample rows, and validation info
        """
        try:
            rows, headers = self.parse_csv(file_content, import_type)
            
            if not rows:
                return {
                    "success": False,
                    "error": "No data found in file",
                    "headers": headers
                }
            
            # Detect column mapping
            if import_type == "products":
                column_map = self.PRODUCT_COLUMNS
            elif import_type == "customers":
                column_map = self.CUSTOMER_COLUMNS
            elif import_type == "competitors":
                column_map = self.COMPETITOR_COLUMNS
            else:
                column_map = {}
            
            detected = self.detect_columns(headers, column_map)
            
            # Get sample rows
            sample_rows = rows[:self.max_preview_rows]
            
            # Validate sample
            validation_issues = []
            required_fields = list(column_map.keys())[:3]  # First 3 are usually required
            
            for field in required_fields:
                if field not in detected:
                    validation_issues.append(f"Could not detect '{field}' column")
            
            return {
                "success": True,
                "headers": headers,
                "detected_columns": detected,
                "sample_rows": sample_rows,
                "total_rows": len(rows),
                "validation_issues": validation_issues,
                "ready_to_import": len(validation_issues) == 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_products(
        self,
        file_content: bytes,
        organization_id: str,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> ImportResult:
        """
        Import products from CSV.
        
        Args:
            file_content: Raw CSV bytes
            organization_id: Organization to import into
            column_mapping: Optional override of detected columns
            
        Returns:
            ImportResult with counts and errors
        """
        from app.database_sqlite import create_product
        
        errors = []
        warnings = []
        imported = 0
        failed = 0
        
        try:
            rows, headers = self.parse_csv(file_content, "products")
            
            if not rows:
                return ImportResult(
                    success=False,
                    imported_count=0,
                    failed_count=0,
                    errors=["No data found in file"],
                    warnings=[]
                )
            
            # Detect or use provided column mapping
            if column_mapping:
                detected = column_mapping
            else:
                detected = self.detect_columns(headers, self.PRODUCT_COLUMNS)
            
            # Check required fields
            if 'sku' not in detected or 'name' not in detected:
                missing = []
                if 'sku' not in detected:
                    missing.append("SKU")
                if 'name' not in detected:
                    missing.append("Name")
                return ImportResult(
                    success=False,
                    imported_count=0,
                    failed_count=len(rows),
                    errors=[f"Required columns not found: {', '.join(missing)}. Found: {headers}"],
                    warnings=[]
                )
            
            sku_col = detected['sku']
            name_col = detected['name']
            
            # Import each row
            for i, row in enumerate(rows[:self.max_import_rows], 1):
                try:
                    sku = row.get(sku_col, '').strip()
                    name = row.get(name_col, '').strip()
                    
                    if not sku or not name:
                        warnings.append(f"Row {i}: Missing SKU or name, skipped")
                        failed += 1
                        continue
                    
                    # Build product data
                    product_data = {
                        'sku': sku,
                        'name': name,
                        'organization_id': organization_id
                    }
                    
                    # Optional fields
                    if 'description' in detected:
                        product_data['description'] = row.get(detected['description'], '')
                    if 'price' in detected:
                        try:
                            price_str = row.get(detected['price'], '0').replace('$', '').replace(',', '')
                            product_data['price'] = float(price_str)
                        except:
                            pass
                    if 'cost_price' in detected:
                        try:
                            cost_str = row.get(detected['cost_price'], '0').replace('$', '').replace(',', '')
                            product_data['cost_price'] = float(cost_str)
                        except:
                            pass
                    if 'category' in detected:
                        product_data['category'] = row.get(detected['category'], '')
                    if 'manufacturer' in detected:
                        product_data['manufacturer'] = row.get(detected['manufacturer'], '')
                    
                    # Create product
                    create_product(product_data)
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
                    failed += 1
            
            if len(rows) > self.max_import_rows:
                warnings.append(f"Import limited to {self.max_import_rows} rows. {len(rows) - self.max_import_rows} rows were skipped.")
            
            return ImportResult(
                success=imported > 0,
                imported_count=imported,
                failed_count=failed,
                errors=errors,
                warnings=warnings
            )
            
        except ValidationException:
            raise
        except Exception as e:
            return ImportResult(
                success=False,
                imported_count=0,
                failed_count=0,
                errors=[str(e)],
                warnings=[]
            )
    
    def import_customers(
        self,
        file_content: bytes,
        organization_id: str,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> ImportResult:
        """Import customers from CSV."""
        from app.database_sqlite import create_customer
        
        errors = []
        imported = 0
        failed = 0
        
        try:
            rows, headers = self.parse_csv(file_content, "customers")
            
            if not rows:
                return ImportResult(False, 0, 0, ["No data found"], [])
            
            detected = column_mapping or self.detect_columns(headers, self.CUSTOMER_COLUMNS)
            
            if 'name' not in detected:
                return ImportResult(
                    False, 0, len(rows),
                    [f"Name column not found. Available: {headers}"],
                    []
                )
            
            name_col = detected['name']
            
            for i, row in enumerate(rows[:self.max_import_rows], 1):
                try:
                    name = row.get(name_col, '').strip()
                    if not name:
                        failed += 1
                        continue
                    
                    customer_data = {
                        'name': name,
                        'organization_id': organization_id
                    }
                    
                    if 'email' in detected:
                        customer_data['email'] = row.get(detected['email'], '')
                    if 'phone' in detected:
                        customer_data['phone'] = row.get(detected['phone'], '')
                    if 'address' in detected:
                        customer_data['address'] = row.get(detected['address'], '')
                    
                    create_customer(customer_data)
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {i}: {str(e)}")
                    failed += 1
            
            return ImportResult(
                success=imported > 0,
                imported_count=imported,
                failed_count=failed,
                errors=errors,
                warnings=[]
            )
            
        except ValidationException:
            raise
        except Exception as e:
            return ImportResult(False, 0, 0, [str(e)], [])


# Global instance
import_service = CSVImportService()

"""
ERP Export module - CSV formats for major ERP systems.
Universal integration without API subscriptions.
"""

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.database_sqlite import get_quote_with_items, list_quotes, get_customer_by_id


class ERPExporter:
    """Export quotes/orders to various ERP formats."""
    
    def __init__(self):
        self.supported_formats = ["sap", "netsuite", "quickbooks", "generic"]
    
    def export_quote(self, quote_id: str, format_type: str = "generic") -> Dict[str, Any]:
        """Export a single quote to ERP format."""
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"error": "Quote not found"}
        
        customer = get_customer_by_id(quote["customer_id"])
        
        if format_type == "sap":
            return self._format_sap(quote, customer)
        elif format_type == "netsuite":
            return self._format_netsuite(quote, customer)
        elif format_type == "quickbooks":
            return self._format_quickbooks(quote, customer)
        else:
            return self._format_generic(quote, customer)
    
    def export_quotes_batch(self, quote_ids: List[str], format_type: str = "generic") -> str:
        """Export multiple quotes to CSV."""
        output = io.StringIO()
        writer = None
        
        for quote_id in quote_ids:
            result = self.export_quote(quote_id, format_type)
            if "error" in result:
                continue
            
            if writer is None:
                writer = csv.DictWriter(output, fieldnames=result.keys())
                writer.writeheader()
            
            writer.writerow(result)
        
        return output.getvalue()
    
    def _format_sap(self, quote: Dict, customer: Optional[Dict]) -> Dict[str, Any]:
        """Format for SAP ERP."""
        items = quote.get("items", [])
        
        # SAP uses specific field codes
        return {
            "Document_Type": "QU",  # Quotation
            "Sales_Org": "1000",
            "Distribution_Channel": "10",
            "Division": "00",
            "Sold_To_Party": customer.get("id", "")[:10] if customer else "",
            "Ship_To_Party": customer.get("id", "")[:10] if customer else "",
            "Customer_Reference": quote.get("token", "")[:20],
            "Document_Date": quote.get("created_at", "")[:10],
            "Valid_From": quote.get("created_at", "")[:10],
            "Valid_To": quote.get("expires_at", "")[:10] if quote.get("expires_at") else "",
            "Item_Number": "10",
            "Material_Code": items[0].get("sku", "") if items else "",
            "Quantity": items[0].get("quantity", 0) if items else 0,
            "Unit": "EA",
            "Net_Price": items[0].get("unit_price", 0) if items else 0,
            "Currency": "USD",
            "Tax_Code": "TX",
            "Header_Text": quote.get("notes", "")[:132],
        }
    
    def _format_netsuite(self, quote: Dict, customer: Optional[Dict]) -> Dict[str, Any]:
        """Format for NetSuite."""
        items = quote.get("items", [])
        
        return {
            "Transaction_Type": "Estimate",
            "Entity": customer.get("name", "") if customer else "",
            "External_ID": quote.get("token", ""),
            "Transaction_Date": quote.get("created_at", "")[:10],
            "Due_Date": quote.get("expires_at", "")[:10] if quote.get("expires_at") else "",
            "Memo": quote.get("notes", ""),
            "Item": items[0].get("sku", "") if items else "",
            "Quantity": items[0].get("quantity", 0) if items else 0,
            "Rate": items[0].get("unit_price", 0) if items else 0,
            "Amount": items[0].get("total_price", 0) if items else 0,
            "Tax_Code": quote.get("tax_rate", 0),
            "Total_Amount": quote.get("total", 0),
            "Status": quote.get("status", ""),
        }
    
    def _format_quickbooks(self, quote: Dict, customer: Optional[Dict]) -> Dict[str, Any]:
        """Format for QuickBooks Online/Desktop."""
        items = quote.get("items", [])
        
        return {
            "Transaction_Type": "Estimate",
            "Customer": customer.get("name", "") if customer else "",
            "Email": customer.get("email", "") if customer else "",
            "Estimate_Number": quote.get("token", ""),
            "Estimate_Date": quote.get("created_at", "")[:10],
            "Expiration_Date": quote.get("expires_at", "")[:10] if quote.get("expires_at") else "",
            "Product_Service": items[0].get("product_name", "") if items else "",
            "SKU": items[0].get("sku", "") if items else "",
            "Description": items[0].get("description", "") if items else "",
            "Quantity": items[0].get("quantity", 0) if items else 0,
            "Rate": items[0].get("unit_price", 0) if items else 0,
            "Amount": items[0].get("total_price", 0) if items else 0,
            "Tax_Amount": quote.get("tax_amount", 0),
            "Total": quote.get("total", 0),
            "Message_on_Estimate": quote.get("notes", ""),
        }
    
    def _format_generic(self, quote: Dict, customer: Optional[Dict]) -> Dict[str, Any]:
        """Universal format - works with any ERP."""
        items = quote.get("items", [])
        
        # Get first item or empty defaults
        first_item = items[0] if items else {}
        
        return {
            "Quote_ID": quote.get("id", ""),
            "Quote_Token": quote.get("token", ""),
            "Quote_Date": quote.get("created_at", ""),
            "Expiry_Date": quote.get("expires_at", ""),
            "Customer_ID": quote.get("customer_id", ""),
            "Customer_Name": customer.get("name", "") if customer else "",
            "Customer_Email": customer.get("email", "") if customer else "",
            "Customer_Company": customer.get("company", "") if customer else "",
            "Line_Item_SKU": first_item.get("sku", ""),
            "Line_Item_Name": first_item.get("product_name", ""),
            "Line_Item_Description": first_item.get("description", ""),
            "Quantity": first_item.get("quantity", 0),
            "Unit_Price": first_item.get("unit_price", 0),
            "Line_Total": first_item.get("total_price", 0),
            "Subtotal": quote.get("subtotal", 0),
            "Tax_Rate": quote.get("tax_rate", 0),
            "Tax_Amount": quote.get("tax_amount", 0),
            "Total": quote.get("total", 0),
            "Currency": "USD",
            "Status": quote.get("status", ""),
            "Notes": quote.get("notes", ""),
        }
    
    def export_all_line_items(self, quote_id: str, format_type: str = "generic") -> str:
        """Export all line items as separate rows."""
        quote = get_quote_with_items(quote_id)
        if not quote:
            return "error: Quote not found"
        
        customer = get_customer_by_id(quote["customer_id"])
        items = quote.get("items", [])
        
        output = io.StringIO()
        
        if format_type == "sap":
            # SAP format - one row per item
            fieldnames = [
                "Document_Type", "Sales_Org", "Distribution_Channel", "Division",
                "Sold_To_Party", "Document_Date", "Item_Number", "Material_Code",
                "Quantity", "Unit", "Net_Price", "Currency"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, item in enumerate(items, 1):
                writer.writerow({
                    "Document_Type": "QU",
                    "Sales_Org": "1000",
                    "Distribution_Channel": "10",
                    "Division": "00",
                    "Sold_To_Party": customer.get("id", "")[:10] if customer else "",
                    "Document_Date": quote.get("created_at", "")[:10],
                    "Item_Number": str(idx * 10),
                    "Material_Code": item.get("sku", ""),
                    "Quantity": item.get("quantity", 0),
                    "Unit": "EA",
                    "Net_Price": item.get("unit_price", 0),
                    "Currency": "USD",
                })
        
        elif format_type == "quickbooks":
            # QuickBooks format
            fieldnames = [
                "Customer", "Estimate_Number", "Estimate_Date", "Product_Service",
                "Description", "Quantity", "Rate", "Amount", "Total"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                writer.writerow({
                    "Customer": customer.get("name", "") if customer else "",
                    "Estimate_Number": quote.get("token", ""),
                    "Estimate_Date": quote.get("created_at", "")[:10],
                    "Product_Service": item.get("product_name", ""),
                    "Description": item.get("description", ""),
                    "Quantity": item.get("quantity", 0),
                    "Rate": item.get("unit_price", 0),
                    "Amount": item.get("total_price", 0),
                    "Total": quote.get("total", 0),
                })
        
        else:
            # Generic format - one row per item
            fieldnames = [
                "Quote_ID", "Quote_Date", "Customer_Name", "Line_Number",
                "SKU", "Product_Name", "Description", "Quantity", "Unit_Price",
                "Line_Total", "Quote_Total", "Currency"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for idx, item in enumerate(items, 1):
                writer.writerow({
                    "Quote_ID": quote.get("id", ""),
                    "Quote_Date": quote.get("created_at", ""),
                    "Customer_Name": customer.get("name", "") if customer else "",
                    "Line_Number": idx,
                    "SKU": item.get("sku", ""),
                    "Product_Name": item.get("product_name", ""),
                    "Description": item.get("description", ""),
                    "Quantity": item.get("quantity", 0),
                    "Unit_Price": item.get("unit_price", 0),
                    "Line_Total": item.get("total_price", 0),
                    "Quote_Total": quote.get("total", 0),
                    "Currency": "USD",
                })
        
        return output.getvalue()


# Singleton instance
_erp_exporter: Optional[ERPExporter] = None

def get_erp_exporter() -> ERPExporter:
    """Get or create ERP exporter singleton."""
    global _erp_exporter
    if _erp_exporter is None:
        _erp_exporter = ERPExporter()
    return _erp_exporter

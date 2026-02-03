"""
Industry-specific templates for OpenMercura.
HVAC, Electrical, Building Materials, etc.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class IndustryTemplate:
    id: str
    name: str
    description: str
    category: str
    default_products: List[Dict[str, Any]]
    common_skus: List[str]
    tax_rate: float
    currency: str


# HVAC Industry Template
HVAC_TEMPLATE = IndustryTemplate(
    id="hvac",
    name="HVAC Distribution",
    description="Heating, Ventilation, and Air Conditioning parts and equipment",
    category="HVAC",
    default_products=[
        {"sku": "AC-COND-3T", "name": "3 Ton Air Conditioner Condenser", "price": 1200.00, "category": "AC Units"},
        {"sku": "AC-COND-5T", "name": "5 Ton Air Conditioner Condenser", "price": 1800.00, "category": "AC Units"},
        {"sku": "FURN-80-60", "name": "80% AFUE 60K BTU Furnace", "price": 850.00, "category": "Furnaces"},
        {"sku": "FURN-80-80", "name": "80% AFUE 80K BTU Furnace", "price": 1100.00, "category": "Furnaces"},
        {"sku": "FURN-96-60", "name": "96% AFUE 60K BTU Furnace", "price": 1200.00, "category": "Furnaces"},
        {"sku": "COIL-3T", "name": "3 Ton Evaporator Coil", "price": 450.00, "category": "Coils"},
        {"sku": "COIL-5T", "name": "5 Ton Evaporator Coil", "price": 650.00, "category": "Coils"},
        {"sku": "THERM-WIFI", "name": "WiFi Smart Thermostat", "price": 199.00, "category": "Thermostats"},
        {"sku": "THERM-PRO", "name": "Professional Programmable Thermostat", "price": 89.00, "category": "Thermostats"},
        {"sku": "DUCT-8x10", "name": "8\"x10\" Ductwork 25ft", "price": 75.00, "category": "Ductwork"},
        {"sku": "DUCT-10x12", "name": "10\"x12\" Ductwork 25ft", "price": 95.00, "category": "Ductwork"},
        {"sku": "FILTER-16x25", "name": "16x25x1 Air Filter (Case of 12)", "price": 45.00, "category": "Filters"},
        {"sku": "FILTER-20x25", "name": "20x25x1 Air Filter (Case of 12)", "price": 55.00, "category": "Filters"},
        {"sku": "REFR-R410A", "name": "R-410A Refrigerant 25lb", "price": 180.00, "category": "Refrigerant"},
        {"sku": "CAP-45-5", "name": "45+5 MFD Capacitor", "price": 12.00, "category": "Electrical"},
        {"sku": "CONT-2P-30", "name": "2 Pole 30A Contactor", "price": 18.00, "category": "Electrical"},
    ],
    common_skus=["AC-COND-", "FURN-", "COIL-", "THERM-", "DUCT-", "FILTER-"],
    tax_rate=8.5,
    currency="USD"
)


# Electrical Industry Template
ELECTRICAL_TEMPLATE = IndustryTemplate(
    id="electrical",
    name="Electrical Supplies",
    description="Electrical components, wire, and equipment",
    category="Electrical",
    default_products=[
        {"sku": "WIRE-12-THHN", "name": "12 AWG THHN Wire (500ft)", "price": 125.00, "category": "Wire"},
        {"sku": "WIRE-10-THHN", "name": "10 AWG THHN Wire (500ft)", "price": 185.00, "category": "Wire"},
        {"sku": "WIRE-14-ROMEX", "name": "14/2 Romex Wire (250ft)", "price": 85.00, "category": "Wire"},
        {"sku": "WIRE-12-ROMEX", "name": "12/2 Romex Wire (250ft)", "price": 115.00, "category": "Wire"},
        {"sku": "BREAK-20-SP", "name": "20A Single Pole Breaker", "price": 8.50, "category": "Breakers"},
        {"sku": "BREAK-30-SP", "name": "30A Single Pole Breaker", "price": 9.50, "category": "Breakers"},
        {"sku": "BREAK-50-DP", "name": "50A Double Pole Breaker", "price": 18.00, "category": "Breakers"},
        {"sku": "PANEL-200", "name": "200A Main Breaker Panel", "price": 185.00, "category": "Panels"},
        {"sku": "PANEL-100", "name": "100A Main Breaker Panel", "price": 145.00, "category": "Panels"},
        {"sku": "SWITCH-SINGLE", "name": "Single Pole Switch (10pk)", "price": 12.00, "category": "Switches"},
        {"sku": "SWITCH-3WAY", "name": "3-Way Switch (10pk)", "price": 18.00, "category": "Switches"},
        {"sku": "OUTLET-15A", "name": "15A Duplex Outlet (10pk)", "price": 14.00, "category": "Outlets"},
        {"sku": "OUTLET-20A", "name": "20A Duplex Outlet (10pk)", "price": 18.00, "category": "Outlets"},
        {"sku": "GFI-15A", "name": "15A GFCI Outlet", "price": 16.00, "category": "GFCI"},
        {"sku": "GFI-20A", "name": "20A GFCI Outlet", "price": 22.00, "category": "GFCI"},
        {"sku": "CONDUIT-1-EMT", "name": "1\" EMT Conduit 10ft", "price": 12.50, "category": "Conduit"},
    ],
    common_skus=["WIRE-", "BREAK-", "PANEL-", "SWITCH-", "OUTLET-", "GFI-"],
    tax_rate=7.0,
    currency="USD"
)


# Building Materials Template
BUILDING_MATERIALS_TEMPLATE = IndustryTemplate(
    id="building",
    name="Building Materials",
    description="Lumber, concrete, drywall, and construction supplies",
    category="Building Materials",
    default_products=[
        {"sku": "LUM-2x4-8", "name": "2x4x8 SPF Stud", "price": 4.25, "category": "Lumber"},
        {"sku": "LUM-2x6-8", "name": "2x6x8 SPF Stud", "price": 6.50, "category": "Lumber"},
        {"sku": "LUM-2x4-10", "name": "2x4x10 SPF Stud", "price": 5.75, "category": "Lumber"},
        {"sku": "PLY-34-4x8", "name": "3/4\" Plywood 4x8", "price": 45.00, "category": "Plywood"},
        {"sku": "PLY-12-4x8", "name": "1/2\" Plywood 4x8", "price": 32.00, "category": "Plywood"},
        {"sku": "DRYW-12-4x8", "name": "1/2\" Drywall 4x8", "price": 12.50, "category": "Drywall"},
        {"sku": "DRYW-58-4x8", "name": "5/8\" Drywall 4x8", "price": 15.00, "category": "Drywall"},
        {"sku": "INSUL-R13", "name": "R-13 Fiberglass Insulation", "price": 28.00, "category": "Insulation"},
        {"sku": "INSUL-R19", "name": "R-19 Fiberglass Insulation", "price": 38.00, "category": "Insulation"},
        {"sku": "CONC-80", "name": "80lb Concrete Mix", "price": 5.50, "category": "Concrete"},
        {"sku": "MORTAR-60", "name": "60lb Mortar Mix", "price": 6.50, "category": "Concrete"},
        {"sku": "REBAR-10", "name": "#10 Rebar 20ft", "price": 18.00, "category": "Rebar"},
        {"sku": "REBAR-8", "name": "#8 Rebar 20ft", "price": 14.00, "category": "Rebar"},
        {"sku": "FAST-NAIL-16D", "name": "16D Common Nails (50lb)", "price": 45.00, "category": "Fasteners"},
        {"sku": "FAST-SCREW-2", "name": "#2 Phillips Deck Screws (5lb)", "price": 22.00, "category": "Fasteners"},
    ],
    common_skus=["LUM-", "PLY-", "DRYW-", "INSUL-", "CONC-", "REBAR-"],
    tax_rate=6.5,
    currency="USD"
)


# Template registry
INDUSTRY_TEMPLATES = {
    "hvac": HVAC_TEMPLATE,
    "electrical": ELECTRICAL_TEMPLATE,
    "building": BUILDING_MATERIALS_TEMPLATE,
}


def get_template(template_id: str) -> Optional[IndustryTemplate]:
    """Get template by ID."""
    return INDUSTRY_TEMPLATES.get(template_id)


def list_templates() -> List[Dict[str, str]]:
    """List all available templates."""
    return [
        {"id": t.id, "name": t.name, "description": t.description, "category": t.category}
        for t in INDUSTRY_TEMPLATES.values()
    ]


def apply_template(template_id: str, user_id: str) -> Dict[str, Any]:
    """Apply template - create all default products."""
    from app.database_sqlite import create_product
    from datetime import datetime
    import uuid
    
    template = get_template(template_id)
    if not template:
        return {"success": False, "error": "Template not found"}
    
    created = 0
    skipped = 0
    
    for product_data in template.default_products:
        now = datetime.utcnow().isoformat()
        product = {
            "id": str(uuid.uuid4()),
            "sku": product_data["sku"],
            "name": product_data["name"],
            "description": f"{template.name} - {product_data['category']}",
            "price": product_data["price"],
            "cost": product_data["price"] * 0.6,  # 40% margin default
            "category": product_data["category"],
            "competitor_sku": None,
            "created_at": now,
            "updated_at": now
        }
        
        if create_product(product):
            created += 1
        else:
            skipped += 1
    
    return {
        "success": True,
        "template": template.name,
        "created": created,
        "skipped": skipped,
        "tax_rate": template.tax_rate,
        "currency": template.currency
    }

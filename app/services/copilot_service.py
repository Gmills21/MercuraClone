"""
AI Copilot Service - The Industrial Subject Matter Expert
Integrates extraction engine, RAG, and product intelligence for quote assistance
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from loguru import logger

from app.database_sqlite import get_quote_with_items, list_products


class CopilotCommand:
    """Represents a parsed natural language command"""
    def __init__(self, raw_text: str, intent: str, entities: Dict[str, Any]):
        self.raw_text = raw_text
        self.intent = intent
        self.entities = entities


class CopilotService:
    """
    AI Copilot for quote verification and optimization.
    
    Provides:
    - Natural language command parsing
    - Semantic product search
    - Alternative product suggestions
    - Quote analysis and recommendations
    - Context-aware assistance
    """
    
    def __init__(self):
        from app.services.extraction_engine import extraction_engine
        from app.services.rag_service import rag_service
        
        self.extraction_engine = extraction_engine
        self.rag_service = rag_service
        logger.info("Copilot service initialized")
    
    async def process_command(
        self,
        command: str,
        quote_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language command from the user.
        
        Examples:
        - "Change Sanpress to Mapress stainless steel"
        - "Find alternatives for item 3"
        - "What's the lead time on XT-400 valves?"
        - "Show me similar past quotes"
        """
        # Parse the command intent
        parsed = self._parse_command(command)
        
        # Execute based on intent
        if parsed.intent == "replace_product":
            return await self._handle_replace_product(parsed, quote_id, context)
        elif parsed.intent == "find_alternatives":
            return await self._handle_find_alternatives(parsed, quote_id, context)
        elif parsed.intent == "ask_question":
            return await self._handle_question(parsed, quote_id, context)
        elif parsed.intent == "show_history":
            return await self._handle_show_history(parsed, quote_id, context)
        elif parsed.intent == "optimize_margin":
            return await self._handle_optimize_margin(parsed, quote_id, context)
        else:
            return {
                "success": False,
                "message": "I didn't understand that command. Try:\n• 'Change [product] to [alternative]'\n• 'Find alternatives for item [number]'\n• 'What's the lead time on [product]?'",
                "suggestions": [
                    "Change Sanpress to Mapress",
                    "Find alternatives for item 3",
                    "Show similar past quotes",
                    "Optimize for better margins"
                ]
            }
    
    def _parse_command(self, command: str) -> CopilotCommand:
        """Parse natural language command into structured intent"""
        command_lower = command.lower()
        
        # Replace/change product
        if any(word in command_lower for word in ["change", "replace", "swap", "switch"]):
            return self._parse_replace_command(command)
        
        # Find alternatives
        if any(word in command_lower for word in ["alternative", "similar", "options", "instead"]):
            return self._parse_alternatives_command(command)
        
        # Question/query
        if any(word in command_lower for word in ["what", "how", "when", "lead time", "price", "cost", "available"]):
            return CopilotCommand(
                raw_text=command,
                intent="ask_question",
                entities={"question": command}
            )
        
        # History/similar quotes
        if any(word in command_lower for word in ["history", "past", "similar", "previous", "before"]):
            return CopilotCommand(
                raw_text=command,
                intent="show_history",
                entities={}
            )
        
        # Optimization
        if any(word in command_lower for word in ["optimize", "better margin", "improve", "cheaper", "boost"]):
            return CopilotCommand(
                raw_text=command,
                intent="optimize_margin",
                entities={}
            )
        
        # Default
        return CopilotCommand(
            raw_text=command,
            intent="unknown",
            entities={}
        )
    
    def _parse_replace_command(self, command: str) -> CopilotCommand:
        """Parse product replacement commands"""
        # Pattern: "Change X to Y" or "Replace X with Y"
        import re
        
        patterns = [
            r"(?:change|replace|swap)\s+(.+?)\s+(?:to|with|for)\s+(.+)",
            r"(?:change|replace|swap)\s+item\s+(\d+)\s+(?:to|with|for)\s+(.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return CopilotCommand(
                    raw_text=command,
                    intent="replace_product",
                    entities={
                        "from_product": match.group(1).strip(),
                        "to_product": match.group(2).strip(),
                        "item_index": int(match.group(1)) - 1 if match.group(1).isdigit() else None
                    }
                )
        
        return CopilotCommand(raw_text=command, intent="unknown", entities={})
    
    def _parse_alternatives_command(self, command: str) -> CopilotCommand:
        """Parse find alternatives commands"""
        import re
        
        # Pattern: "Find alternatives for X" or "What are options for item Y"
        patterns = [
            r"(?:find|show|get)\s+alternatives?\s+(?:for|to)\s+(?:item\s+)?(\d+|.+)",
            r"(?:what are|show me)\s+(?:the\s+)?alternatives?\s+(?:for|to)\s+(?:item\s+)?(\d+|.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                return CopilotCommand(
                    raw_text=command,
                    intent="find_alternatives",
                    entities={
                        "item_index": int(target) - 1 if target.isdigit() else None,
                        "product_name": target if not target.isdigit() else None
                    }
                )
        
        return CopilotCommand(raw_text=command, intent="unknown", entities={})
    
    async def _handle_replace_product(
        self,
        command: CopilotCommand,
        quote_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle product replacement requests"""
        from_product = command.entities.get("from_product")
        to_product = command.entities.get("to_product")
        item_index = command.entities.get("item_index")
        
        if not quote_id:
            return {
                "success": False,
                "message": "Please open a quote first to make changes."
            }
        
        # Get current quote
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"success": False, "message": "Quote not found."}
        
        items = quote.get("items", [])
        
        # Find the item to replace
        target_item = None
        target_index = None
        
        if item_index is not None and 0 <= item_index < len(items):
            target_item = items[item_index]
            target_index = item_index
        elif from_product:
            # Search by name/description
            for i, item in enumerate(items):
                desc = item.get("description", "").lower()
                name = item.get("product_name", "").lower()
                if from_product.lower() in desc or from_product.lower() in name:
                    target_item = item
                    target_index = i
                    break
        
        if not target_item:
            return {
                "success": False,
                "message": f"Could not find '{from_product}' in this quote. Please check the item name or use the item number (e.g., 'item 3')."
            }
        
        # Search for replacement product
        search_results = await self._search_products(to_product)
        
        if not search_results:
            return {
                "success": False,
                "message": f"Could not find product matching '{to_product}' in the catalog."
            }
        
        best_match = search_results[0]
        
        return {
            "success": True,
            "action": "replace_product",
            "message": f"Found replacement for '{target_item.get('description', target_item.get('product_name'))}'",
            "changes": {
                "item_index": target_index,
                "old_item": target_item,
                "new_item": {
                    "product_id": best_match.get("id"),
                    "product_name": best_match.get("name"),
                    "sku": best_match.get("sku"),
                    "description": best_match.get("description"),
                    "unit_price": best_match.get("price", 0),
                    "quantity": target_item.get("quantity", 1)
                },
                "margin_impact": self._calculate_margin_impact(target_item, best_match)
            },
            "alternatives": search_results[1:4] if len(search_results) > 1 else []
        }
    
    async def _handle_find_alternatives(
        self,
        command: CopilotCommand,
        quote_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle find alternatives requests"""
        item_index = command.entities.get("item_index")
        product_name = command.entities.get("product_name")
        
        if not quote_id:
            return {
                "success": False,
                "message": "Please open a quote first to find alternatives."
            }
        
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"success": False, "message": "Quote not found."}
        
        items = quote.get("items", [])
        
        # Determine target item
        target_item = None
        if item_index is not None and 0 <= item_index < len(items):
            target_item = items[item_index]
        elif product_name:
            # Search by name
            for item in items:
                if product_name.lower() in item.get("description", "").lower():
                    target_item = item
                    break
        
        if not target_item:
            return {
                "success": False,
                "message": "Could not find the specified item. Use item numbers like 'item 3'."
            }
        
        # Search for alternatives using the item name/description
        search_query = target_item.get("description") or target_item.get("product_name", "")
        alternatives = await self._search_products(search_query, limit=5)
        
        # Filter out the current item and sort by margin potential
        current_sku = target_item.get("sku", "").lower()
        alternatives = [
            alt for alt in alternatives 
            if alt.get("sku", "").lower() != current_sku
        ]
        
        # Calculate margin for each alternative
        for alt in alternatives:
            alt["margin_potential"] = self._calculate_margin_potential(alt)
        
        # Sort by margin potential
        alternatives.sort(key=lambda x: x.get("margin_potential", 0), reverse=True)
        
        return {
            "success": True,
            "action": "show_alternatives",
            "message": f"Found {len(alternatives)} alternatives for '{search_query[:50]}...'",
            "target_item": target_item,
            "target_index": item_index,
            "alternatives": alternatives[:4]
        }
    
    async def _handle_question(
        self,
        command: CopilotCommand,
        quote_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle knowledge base questions using RAG"""
        question = command.entities.get("question", "")
        
        # Use RAG to answer the question
        rag_response = await self.rag_service.chat_with_data(question, context_window=3)
        
        return {
            "success": True,
            "action": "answer_question",
            "message": rag_response.get("answer", "I don't have information about that."),
            "confidence": rag_response.get("confidence", 0),
            "sources": rag_response.get("sources", [])
        }
    
    async def _handle_show_history(
        self,
        command: CopilotCommand,
        quote_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Show similar past quotes"""
        if not quote_id:
            return {
                "success": False,
                "message": "Please open a quote first to see similar history."
            }
        
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"success": False, "message": "Quote not found."}
        
        # Search for similar quotes using customer name and products
        customer_name = quote.get("customer_name", "")
        items = quote.get("items", [])
        
        # Build search query from items
        product_names = [item.get("product_name", "") for item in items[:3]]
        search_query = f"{customer_name} {' '.join(product_names)}"
        
        similar_quotes = await self.rag_service.search(
            f"Quote for {search_query}",
            top_k=5,
            threshold=0.3
        )
        
        return {
            "success": True,
            "action": "show_history",
            "message": f"Found {len(similar_quotes)} similar past quotes",
            "similar_quotes": [
                {
                    "id": r.document.metadata.get("quote_id"),
                    "content": r.document.content[:200],
                    "score": round(r.score, 3)
                }
                for r in similar_quotes
            ]
        }
    
    async def _handle_optimize_margin(
        self,
        command: CopilotCommand,
        quote_id: Optional[str],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Optimize quote for better margins"""
        if not quote_id:
            return {
                "success": False,
                "message": "Please open a quote first to optimize."
            }
        
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"success": False, "message": "Quote not found."}
        
        items = quote.get("items", [])
        optimizations = []
        
        for i, item in enumerate(items):
            # Search for alternatives with better margins
            search_query = item.get("description") or item.get("product_name", "")
            alternatives = await self._search_products(search_query, limit=3)
            
            # Filter for better margins
            current_price = item.get("unit_price", 0)
            current_cost = item.get("cost_price", current_price * 0.7)
            current_margin = ((current_price - current_cost) / current_price * 100) if current_price > 0 else 0
            
            for alt in alternatives:
                alt_price = alt.get("price", 0)
                alt_cost = alt.get("cost_price", alt_price * 0.7)
                alt_margin = ((alt_price - alt_cost) / alt_price * 100) if alt_price > 0 else 0
                
                if alt_margin > current_margin + 5:  # At least 5% better margin
                    optimizations.append({
                        "item_index": i,
                        "current_item": item,
                        "alternative": alt,
                        "margin_gain": alt_margin - current_margin,
                        "potential_profit_increase": (alt_margin - current_margin) / 100 * current_price * item.get("quantity", 1)
                    })
                    break
        
        # Sort by profit increase
        optimizations.sort(key=lambda x: x.get("potential_profit_increase", 0), reverse=True)
        
        total_potential = sum(opt.get("potential_profit_increase", 0) for opt in optimizations)
        
        return {
            "success": True,
            "action": "optimize_margin",
            "message": f"Found {len(optimizations)} optimization opportunities",
            "potential_profit_increase": round(total_potential, 2),
            "optimizations": optimizations[:5]
        }
    
    async def _search_products(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search products using RAG"""
        results = await self.rag_service.search(query, top_k=limit, threshold=0.3)
        
        # Convert to product format
        products = []
        for r in results:
            if r.document.metadata.get("type") == "product":
                products.append({
                    "id": r.document.metadata.get("product_id"),
                    "name": r.document.metadata.get("name") or self._extract_name(r.document.content),
                    "sku": r.document.metadata.get("sku"),
                    "description": r.document.content[:500],
                    "price": r.document.metadata.get("price", 0),
                    "cost_price": r.document.metadata.get("cost_price", 0),
                    "score": round(r.score, 3)
                })
        
        return products
    
    def _extract_name(self, content: str) -> str:
        """Extract product name from RAG content"""
        import re
        match = re.search(r"Product:\s*(.+?)\.", content)
        return match.group(1).strip() if match else "Unknown Product"
    
    def _calculate_margin_impact(self, old_item: Dict, new_item: Dict) -> Dict[str, float]:
        """Calculate margin impact of a product change"""
        old_price = old_item.get("unit_price", 0)
        old_cost = old_item.get("cost_price", old_price * 0.7)
        old_margin = ((old_price - old_cost) / old_price * 100) if old_price > 0 else 0
        
        new_price = new_item.get("price", 0)
        new_cost = new_item.get("cost_price", new_price * 0.7)
        new_margin = ((new_price - new_cost) / new_price * 100) if new_price > 0 else 0
        
        quantity = old_item.get("quantity", 1)
        
        return {
            "old_margin_percent": round(old_margin, 1),
            "new_margin_percent": round(new_margin, 1),
            "margin_change": round(new_margin - old_margin, 1),
            "profit_change_per_unit": round((new_price - new_cost) - (old_price - old_cost), 2),
            "total_profit_impact": round(((new_price - new_cost) - (old_price - old_cost)) * quantity, 2)
        }
    
    def _calculate_margin_potential(self, product: Dict) -> float:
        """Calculate margin potential for ranking"""
        price = product.get("price", 0)
        cost = product.get("cost_price", price * 0.7)
        if price > 0:
            return ((price - cost) / price * 100)
        return 0
    
    async def analyze_quote(self, quote_id: str) -> Dict[str, Any]:
        """Perform full analysis on a quote"""
        quote = get_quote_with_items(quote_id)
        if not quote:
            return {"success": False, "message": "Quote not found"}
        
        items = quote.get("items", [])
        
        # Calculate overall stats
        total_items = len(items)
        items_with_products = sum(1 for item in items if item.get("product_id"))
        
        # Check for margin opportunities
        low_margin_items = []
        for i, item in enumerate(items):
            price = item.get("unit_price", 0)
            cost = item.get("cost_price", price * 0.7)
            margin = ((price - cost) / price * 100) if price > 0 else 0
            if margin < 20:
                low_margin_items.append({
                    "index": i,
                    "item": item,
                    "margin": round(margin, 1)
                })
        
        return {
            "success": True,
            "quote_id": quote_id,
            "summary": {
                "total_items": total_items,
                "catalog_matches": items_with_products,
                "match_rate": round(items_with_products / total_items * 100, 1) if total_items > 0 else 0,
                "low_margin_items": len(low_margin_items)
            },
            "recommendations": [
                f"{len(low_margin_items)} items have margins below 20%" if low_margin_items else "All items have healthy margins",
                f"Catalog match rate: {round(items_with_products / total_items * 100, 1)}%" if total_items > 0 else "No items to analyze"
            ],
            "low_margin_items": low_margin_items[:3]
        }


# Global instance
copilot_service = CopilotService()

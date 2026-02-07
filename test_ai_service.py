"""
Test script for MultiProviderAIService
Run this to verify your API keys are working
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_service():
    """Test the multi-provider AI service."""
    from app.ai_provider_service import get_ai_service, ProviderType
    
    print("=" * 60)
    print("OpenMercura Multi-Provider AI Service Test")
    print("=" * 60)
    
    # Initialize service
    service = get_ai_service()
    
    # Check loaded keys
    print("\n📊 API Key Configuration:")
    print("-" * 40)
    stats = service.get_stats()
    
    gemini_keys = [k for k in stats["keys"] if k["provider"] == "gemini"]
    openrouter_keys = [k for k in stats["keys"] if k["provider"] == "openrouter"]
    
    print(f"Total API Keys: {len(stats['keys'])}")
    print(f"  - Gemini keys: {len(gemini_keys)}")
    print(f"  - OpenRouter keys: {len(openrouter_keys)}")
    
    if not stats["keys"]:
        print("\n❌ No API keys configured!")
        print("Please add your API keys to the .env file")
        return
    
    # Health check
    print("\n🏥 Health Check:")
    print("-" * 40)
    health = await service.health_check()
    
    for provider, status in health.items():
        icon = "✅" if status["available"] else "❌"
        print(f"{icon} {provider}: {status['status']}")
    
    # Test chat completion with each provider
    print("\n💬 Testing Chat Completion:")
    print("-" * 40)
    
    test_message = "Say 'Hello from OpenMercura!' and nothing else."
    
    for provider_type in [ProviderType.GEMINI, ProviderType.OPENROUTER]:
        provider_name = provider_type.value
        print(f"\n🔄 Testing {provider_name}...")
        
        try:
            result = await service.chat_completion(
                messages=[{"role": "user", "content": test_message}],
                temperature=0.1,
                preferred_provider=provider_type,
                fallback_providers=False  # Don't fallback for this test
            )
            
            if "error" in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                content = result["choices"][0]["message"]["content"]
                used_provider = result.get("provider", "unknown")
                model = result.get("model", "unknown")
                print(f"   ✅ Success!")
                print(f"      Provider: {used_provider}")
                print(f"      Model: {model}")
                print(f"      Response: {content[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Test structured data extraction
    print("\n📋 Testing Structured Data Extraction:")
    print("-" * 40)
    
    test_text = """
    Quote Request from ABC Manufacturing
    Contact: john.doe@abcmanufacturing.com
    Phone: (555) 123-4567
    
    Items needed:
    - 50x Ball Valve DN50
    - 25x Pressure Gauge 0-100 PSI
    - 10x Butterfly Valve DN100
    
    Delivery needed by: 2026-03-15
    Ship to: 123 Industrial Way, Manufacturing City, MC 12345
    """
    
    schema = {
        "customer_name": "string",
        "contact_email": "string",
        "contact_phone": "string",
        "line_items": [
            {
                "item_name": "string",
                "quantity": "number"
            }
        ],
        "delivery_date": "string"
    }
    
    try:
        result = await service.extract_structured_data(
            text=test_text,
            schema=schema,
            instructions="Extract RFQ information from this text."
        )
        
        if result["success"]:
            print("   ✅ Extraction successful!")
            print(f"      Provider used: {result.get('provider', 'unknown')}")
            print(f"      Model used: {result.get('model', 'unknown')}")
            print(f"      Data: {result['data']}")
        else:
            print(f"   ❌ Extraction failed: {result.get('error')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Final stats
    print("\n📈 Final Statistics:")
    print("-" * 40)
    final_stats = service.get_stats()
    print(f"Total requests: {final_stats['total_requests']}")
    print(f"Failed requests: {final_stats['failed_requests']}")
    print(f"Success rate: {final_stats['success_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_service())
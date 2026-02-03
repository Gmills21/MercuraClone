import asyncio
import sys
import os
from pathlib import Path

# Set env var
os.environ['KNOWLEDGE_BASE_ENABLED'] = 'true'

sys.path.insert(0, 'C:/Users/graha/MercuraClone')

async def test_kb():
    print("=" * 70)
    print("KNOWLEDGE BASE - FINAL TEST")
    print("=" * 70)
    
    from app.services.knowledge_base_service import get_knowledge_base_service
    
    kb = get_knowledge_base_service()
    
    print(f"\nKB Available: {kb.is_available()}")
    
    if not kb.is_available():
        print("\nChecking dependencies...")
        try:
            import chromadb
            print(f"  ChromaDB: {chromadb.__version__}")
        except Exception as e:
            print(f"  ChromaDB: ERROR - {e}")
        
        try:
            import sentence_transformers
            print("  Sentence-Transformers: OK")
        except Exception as e:
            print(f"  Sentence-Transformers: ERROR - {e}")
        
        return
    
    print("\n✓ Knowledge Base is ready!")
    
    # Test files
    test_files = [
        ("C:/Users/graha/MercuraClone/test_materials/Battery.pdf", "manual"),
        ("C:/Users/graha/MercuraClone/test_materials/NPC-Nitra-Pneumatic-Cylinders.pdf", "catalog"),
    ]
    
    print("\n" + "=" * 70)
    print("INGESTING TEST FILES")
    print("=" * 70)
    
    for file_path, doc_type in test_files:
        file = Path(file_path)
        print(f"\n{file.name}")
        print("-" * 50)
        
        if not file.exists():
            print("  ERROR: File not found")
            continue
        
        size_mb = file.stat().st_size / 1024 / 1024
        print(f"  Size: {size_mb:.2f} MB")
        
        try:
            result = await kb.ingest_document(
                str(file),
                doc_type=doc_type,
                metadata={'test': True, 'doc_name': file.name}
            )
            
            if 'error' in result:
                print(f"  Status: FAILED")
                print(f"  Error: {result['error']}")
            else:
                print(f"  Status: SUCCESS")
                print(f"  Pages: {result.get('pages_processed', 0)}")
                print(f"  Chunks: {result.get('chunks_created', 0)}")
        
        except Exception as e:
            print(f"  Status: ERROR - {e}")
    
    # Check stats
    stats = kb.get_stats()
    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE STATS")
    print("=" * 70)
    print(f"  Total Documents: {stats.get('document_count', 0)}")
    print(f"  DB Path: {stats.get('db_path', 'N/A')}")
    print(f"  AI Enhanced: {stats.get('ai_enhanced', False)}")
    
    # Test query if we have documents
    if stats.get('document_count', 0) > 0:
        print("\n" + "=" * 70)
        print("TESTING QUERIES")
        print("=" * 70)
        
        queries = [
            "What is Contractor Foreman?",
            "What pressure rating for NITRA cylinders?",
        ]
        
        for query in queries:
            print(f"\nQ: {query}")
            try:
                result = await kb.query(query, use_ai=False)
                print(f"  A: {result.answer[:200]}...")
                print(f"  Confidence: {result.confidence:.2f}")
                print(f"  Time: {result.query_time_ms}ms")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_kb())

import os
import sys

os.environ['KNOWLEDGE_BASE_ENABLED'] = 'true'
sys.path.insert(0, 'C:/Users/graha/MercuraClone')

from app.services.knowledge_base_service import get_knowledge_base_service

kb = get_knowledge_base_service()

print("=" * 60)
print("LISTING ALL KB DOCUMENTS")
print("=" * 60)

# Get all documents
try:
    results = kb.collection.get()
    
    sources = {}
    for i, metadata in enumerate(results['metadatas']):
        source = metadata.get('source', 'unknown')
        if source not in sources:
            sources[source] = 0
        sources[source] += 1
    
    print(f"\nTotal chunks in KB: {len(results['ids'])}")
    print("\nDocuments by source:")
    for source, count in sorted(sources.items()):
        print(f"  {source}: {count} chunks")
        
except Exception as e:
    print(f"Error: {e}")

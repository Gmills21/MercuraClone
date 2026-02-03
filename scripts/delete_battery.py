import os
import sys

os.environ['KNOWLEDGE_BASE_ENABLED'] = 'true'
sys.path.insert(0, 'C:/Users/graha/MercuraClone')

from app.services.knowledge_base_service import get_knowledge_base_service

kb = get_knowledge_base_service()

print("=" * 60)
print("DELETING BATTERY.PDF (CONTRACTOR FOREMAN) DATA")
print("=" * 60)

# Find all chunks with Battery.pdf in source
results = kb.collection.get(
    where={"source": {"$contains": "Battery.pdf"}}
)

print(f"\nFound {len(results['ids'])} chunks from Battery.pdf")

if results['ids']:
    # Delete them
    kb.collection.delete(ids=results['ids'])
    print(f"Deleted {len(results['ids'])} chunks")
else:
    print("No chunks found to delete")

# Verify
results_after = kb.collection.get(
    where={"source": {"$contains": "Battery.pdf"}}
)

print(f"\nAfter deletion: {len(results_after['ids'])} chunks remain")

# Show remaining docs
all_results = kb.collection.get()
sources = {}
for metadata in all_results['metadatas']:
    source = metadata.get('source', 'unknown')
    sources[source] = sources.get(source, 0) + 1

print("\nRemaining documents in KB:")
for source, count in sorted(sources.items()):
    print(f"  {source}: {count} chunks")

print("\n✓ Contractor Foreman data removed from KB")

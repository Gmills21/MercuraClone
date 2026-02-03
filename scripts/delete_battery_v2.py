import os
import sys

os.environ['KNOWLEDGE_BASE_ENABLED'] = 'true'
sys.path.insert(0, 'C:/Users/graha/MercuraClone')

from app.services.knowledge_base_service import get_knowledge_base_service

kb = get_knowledge_base_service()

print("=" * 60)
print("DELETING BATTERY.PDF (CONTRACTOR FOREMAN) DATA")
print("=" * 60)

# Get all chunks
all_results = kb.collection.get()
print(f"\nTotal chunks: {len(all_results['ids'])}")

# Find Battery.pdf chunks
battery_ids = []
for i, metadata in enumerate(all_results['metadatas']):
    if 'Battery.pdf' in metadata.get('source', ''):
        battery_ids.append(all_results['ids'][i])

print(f"Found {len(battery_ids)} chunks from Battery.pdf")

if battery_ids:
    # Delete in batches
    batch_size = 100
    for i in range(0, len(battery_ids), batch_size):
        batch = battery_ids[i:i+batch_size]
        kb.collection.delete(ids=batch)
        print(f"  Deleted batch {i//batch_size + 1}: {len(batch)} chunks")
    
    print(f"\n✓ Deleted all {len(battery_ids)} Battery.pdf chunks")
else:
    print("No Battery.pdf chunks found")

# Verify final state
final_results = kb.collection.get()
print(f"\nFinal KB state:")
print(f"  Total chunks: {len(final_results['ids'])}")

# Show remaining docs
sources = {}
for metadata in final_results['metadatas']:
    source = metadata.get('source', 'unknown')
    sources[source] = sources.get(source, 0) + 1

print("\nRemaining documents:")
for source, count in sorted(sources.items()):
    print(f"  {source}: {count} chunks")

print("\n✓ Knowledge Base cleaned up - Contractor Foreman data removed")

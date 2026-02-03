import os
import sys

os.environ['KNOWLEDGE_BASE_ENABLED'] = 'true'
sys.path.insert(0, 'C:/Users/graha/MercuraClone')

from app.services.knowledge_base_service import get_knowledge_base_service

kb = get_knowledge_base_service()

print("=" * 60)
print("CLEANING UP KNOWLEDGE BASE")
print("=" * 60)

stats = kb.get_stats()
print(f"\nBefore cleanup:")
print(f"  Documents: {stats.get('document_count', 0)}")

# Delete Battery.pdf document (Contractor Foreman)
# The document ID is based on file path hash
import hashlib
doc_id = hashlib.md5("C:\\Users\\graha\\MercuraClone\\test_materials\\Battery.pdf".encode()).hexdigest()[:12]

print(f"\nDeleting document: Battery.pdf (ID: {doc_id})")
result = kb.delete_document(doc_id)
print(f"  Result: {'Success' if result else 'Not found'}")

# Check stats again
stats = kb.get_stats()
print(f"\nAfter cleanup:")
print(f"  Documents: {stats.get('document_count', 0)}")

print("\n" + "=" * 60)
print("KB Status: Contractor Foreman data removed")
print("=" * 60)

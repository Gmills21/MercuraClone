import shutil
import os

# Copy app folder
src = r'C:\Users\graha\.openclaw\workspace\MercuraClone\app'
dst = r'C:\Users\graha\MercuraClone\app'

# Ensure destination exists
os.makedirs(dst, exist_ok=True)

# Copy specific new files
files_to_copy = [
    'alert_service.py',
    'business_impact_service.py', 
    'customer_intelligence_service.py',
    'empty_states_service.py',
    'image_extraction_service.py',
    'onboarding_service.py',
    'quickbooks_service.py',
    'config.py',
    'main.py'
]

for f in files_to_copy:
    src_file = os.path.join(src, f)
    dst_file = os.path.join(dst, f)
    if os.path.exists(src_file):
        try:
            shutil.copy2(src_file, dst_file)
            print(f'Copied: {f}')
        except Exception as e:
            print(f'Failed {f}: {e}')

# Copy routes
routes_src = os.path.join(src, 'routes')
routes_dst = os.path.join(dst, 'routes')
os.makedirs(routes_dst, exist_ok=True)

route_files = ['alerts.py', 'impact.py', 'image_extract.py', 'intelligence.py', 'onboarding.py', 'quickbooks.py']
for f in route_files:
    src_file = os.path.join(routes_src, f)
    dst_file = os.path.join(routes_dst, f)
    if os.path.exists(src_file):
        try:
            shutil.copy2(src_file, dst_file)
            print(f'Copied routes/{f}')
        except Exception as e:
            print(f'Failed routes/{f}: {e}')

print('Done copying backend files')

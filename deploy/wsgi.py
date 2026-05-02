import sys
path = '/home/YOUR_USERNAME/caviar-crm'
if path not in sys.path:
    sys.path.insert(0, path)

from backend.app import create_app
application = create_app('production')

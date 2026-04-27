import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'newProject.settings')
django.setup()

# Simple ASGI application without WebSocket routing
application = get_asgi_application()
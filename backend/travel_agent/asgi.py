"""
ASGI config for AI Travel Agent project.
Handles both HTTP and WebSocket connections.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'travel_agent.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import WebSocket routing and JWT middleware after Django setup
from apps.notifications.routing import websocket_urlpatterns
from travel_agent.channelsmiddleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    # HTTP requests
    "http": django_asgi_app,

    # WebSocket connections with JWT auth
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

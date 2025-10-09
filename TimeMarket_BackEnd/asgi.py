"""
ASGI config for TimeMarket_BackEnd project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

# Django 설정 먼저 로드
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TimeMarket_BackEnd.settings")
django.setup()

# Django ASGI 애플리케이션 먼저 생성
django_asgi_app = get_asgi_application()

# 이후에 channels 관련 import
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.middleware import JWTAuthMiddleware
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

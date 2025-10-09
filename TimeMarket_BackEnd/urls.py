# project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/wallet/', include('wallet.urls')),
    path('api/', include('users.urls')),
    path('api/map/', include('map.urls')),
    path('api/time-posts/', include('posts.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/push/', include('push_notice.urls')),  # 추가
]

from django.conf import settings
from django.conf.urls.static import static


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
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
    path('api/trades/', include('chat.urls')),  # 거래 히스토리용 추가 경로
    path('api/push/', include('push_notice.urls')),
    path('api/reviews/', include('review.urls')),  # 리뷰 API
]

from django.conf import settings
from django.conf.urls.static import static


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
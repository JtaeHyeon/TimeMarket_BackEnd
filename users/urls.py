# baskduf/timemarket_backend/TimeMarket_BackEnd-af582882d1bc775a5de6f36633ddc9966161e2e3/users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("auth/signup/", views.SignUpView.as_view(), name="auth-signup"),
    path("auth/login/", views.TokenObtainPairView.as_view(), name="auth-login"),
    path("users/me/", views.UserMeView.as_view(), name="user-me"),
    path("users/<int:user_id>/", views.UserDetailView.as_view(), name="user-detail"),
    # ▼▼▼▼▼ [추가] 비밀번호 변경 URL ▼▼▼▼▼
    path("users/change-password/", views.ChangePasswordView.as_view(), name="change-password"),
]
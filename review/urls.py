from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReviewListView.as_view(), name='review-list'),
    path('create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('user/<int:user_id>/', views.UserReviewListView.as_view(), name='user-review-list'),
]


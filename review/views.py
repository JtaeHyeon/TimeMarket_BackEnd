from rest_framework import generics, permissions
from .models import Review
from .serializers import ReviewSerializer, CreateReviewSerializer


class ReviewListView(generics.ListAPIView):
    """리뷰 목록 조회"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ReviewCreateView(generics.CreateAPIView):
    """리뷰 생성"""
    serializer_class = CreateReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({'request': self.request})
        return ctx


class ReviewDetailView(generics.RetrieveDestroyAPIView):
    """리뷰 상세 조회 및 삭제"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def delete(self, request, *args, **kwargs):
        review = self.get_object()
        if request.user != review.author and not request.user.is_staff:
            from rest_framework.response import Response
            from rest_framework import status
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)


class UserReviewListView(generics.ListAPIView):
    """특정 사용자가 받은 리뷰 목록"""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Review.objects.filter(target_id=user_id)


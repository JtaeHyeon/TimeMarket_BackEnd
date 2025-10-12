from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from .models import TimePost
from .serializers import TimePostSerializer
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    # 위도, 경도 라디안으로 변환
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # 지구 반지름 (km)
    return c * r

class NearbyTimePostList(APIView):
    def get(self, request):
        lat = float(request.query_params.get('lat', 0))
        lng = float(request.query_params.get('lng', 0))
        post_type = request.query_params.get('type', None)

        posts = TimePost.objects.all()

        if post_type:
            posts = posts.filter(type=post_type)

        posts = sorted(
            posts,
            key=lambda post: haversine(lat, lng, post.latitude or 0, post.longitude or 0)
        )

        serializer = TimePostSerializer(posts[:30], many=True, context={'request': request})  # context 추가
        return Response(serializer.data)

class TimePostCreate(generics.CreateAPIView):
    queryset = TimePost.objects.all()
    serializer_class = TimePostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TimePostDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = TimePost.objects.all()
    serializer_class = TimePostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != self.get_object().user:
            raise PermissionDenied("수정 권한이 없습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.user:
            raise PermissionDenied("삭제 권한이 없습니다.")
        instance.delete()

class BoardTimePostList(generics.ListAPIView):
    queryset = TimePost.objects.all().order_by('-created_at')
    serializer_class = TimePostSerializer

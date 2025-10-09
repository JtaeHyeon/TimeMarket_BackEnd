# users/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import SignUpSerializer, UserSerializer, CustomTokenObtainPairSerializer, PasswordChangeSerializer

User = get_user_model()

# 회원가입
class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]

# 로그인 (JWT 발급)
class TokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# 내 정보 가져오기 & 수정
class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

# 다른 유저 정보 조회
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'user_id'

# ▼▼▼▼▼ [수정] POST 요청을 처리하도록 View 변경 ▼▼▼▼▼
class ChangePasswordView(generics.GenericAPIView):
    """
    비밀번호 변경
    """
    serializer_class = PasswordChangeSerializer
    model = User
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # 새 비밀번호로 변경
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            return Response({"detail": "비밀번호가 성공적으로 변경되었습니다."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# ▲▲▲▲▲ [수정] POST 요청을 처리하도록 View 변경 ▲▲▲▲▲
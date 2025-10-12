# baskduf/timemarket_backend/TimeMarket_BackEnd-af582882d1bc775a5de6f36633ddc9966161e2e3/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# 회원가입용
class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'nickname', 'email', 'password', 'profile_image']  # profile_image 추가

    def create(self, validated_data):
        profile_image = validated_data.pop('profile_image', None)  # 프로필 이미지 꺼내기(없으면 None)
        user = User.objects.create_user(
            nickname=validated_data["nickname"],
            email=validated_data.get("email"),
            password=validated_data["password"]
        )
        if profile_image:
            user.profile_image = profile_image
            user.save()
        return user


# 사용자 정보 조회 및 수정용
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nickname', 'email', 'profile_image', 'average_rating', 'rating_count']
        read_only_fields = ['id', 'average_rating', 'rating_count']

    def to_representation(self, instance):
        """응답 시 profile_image를 전체 URL로 변환"""
        data = super().to_representation(instance)
        if instance.profile_image:
            request = self.context.get('request')
            if request:
                # HTTP 요청이 있으면 전체 URL 생성
                data['profile_image'] = request.build_absolute_uri(instance.profile_image.url)
            else:
                # WebSocket 등 request가 없는 경우 상대 URL 반환
                from django.conf import settings
                data['profile_image'] = f"{settings.MEDIA_URL}{instance.profile_image}"
        else:
            data['profile_image'] = None
        return data


# ▼▼▼▼▼ [추가] 비밀번호 변경 Serializer ▼▼▼▼▼
class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("현재 비밀번호가 일치하지 않습니다.")
        return value


# ▲▲▲▲▲ [추가] 비밀번호 변경 Serializer ▲▲▲▲▲


# 로그인용 (JWT 커스터마이징 가능)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # username_field를 nickname으로 설정
    username_field = 'nickname'

    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            'nickname': self.user.nickname,
            'email': self.user.email,
        })
        return data
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
class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    average_rating = serializers.ReadOnlyField()
    rating_count = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'email', 'profile_image', 'average_rating', 'rating_count']

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None


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
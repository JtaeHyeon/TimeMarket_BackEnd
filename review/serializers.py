from rest_framework import serializers
from .models import Review
from chat.models import TradeRequest
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile_image', 'average_rating', 'rating_count']


class ReviewSerializer(serializers.ModelSerializer):
    author = SimpleUserSerializer(read_only=True)
    target = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'trade', 'author', 'target', 'rating', 'content', 'created_at']


class CreateReviewSerializer(serializers.ModelSerializer):
    trade = serializers.PrimaryKeyRelatedField(queryset=TradeRequest.objects.all())

    class Meta:
        model = Review
        fields = ['trade', 'rating', 'content']

    def validate_rating(self, value):
        # rating은 0.5 단위 (예: 0.5, 1.0, 1.5 ... 5.0)
        try:
            multiplied = float(value) * 2
        except Exception:
            raise serializers.ValidationError("유효한 평점을 입력하세요.")
        if abs(round(multiplied) - multiplied) > 1e-6:
            raise serializers.ValidationError("평점은 0.5 단위여야 합니다.")
        if value < 0.5 or value > 5.0:
            raise serializers.ValidationError("평점은 0.5 이상 5.0 이하이어야 합니다.")
        return value

    def validate(self, attrs):
        trade = attrs.get('trade')
        request = self.context['request']
        user = request.user

        # 거래가 완료된 거래인지 확인
        if trade.status != 'completed':
            raise serializers.ValidationError("리뷰는 완료된 거래에 대해서만 작성할 수 있습니다.")

        # 작성자가 거래 참여자인지 확인
        if not (trade.requester == user or trade.receiver == user):
            raise serializers.ValidationError("해당 거래에 참여하지 않은 사용자는 리뷰를 작성할 수 없습니다.")

        # 같은 거래에 이미 작성한 리뷰가 있는지 확인
        existing = Review.objects.filter(trade=trade, author=user).exists()
        if existing:
            raise serializers.ValidationError("이미 이 거래에 대해 리뷰를 작성했습니다.")

        return attrs

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        trade = validated_data['trade']

        # target은 작성자의 상대방
        if trade.requester == user:
            target = trade.receiver
        else:
            target = trade.requester

        review = Review.objects.create(
            trade=trade,
            author=user,
            target=target,
            rating=validated_data['rating'],
            content=validated_data.get('content', '')
        )
        return review


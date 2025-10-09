from rest_framework import serializers
from .models import ChatMessage, Room, TradeRequest
from users.models import User
from posts.models import TimePost
from users.serializers import UserSerializer

# TimePost 정보를 위한 간단한 시리얼라이저 (순환 import 방지)
class SimpleTimePostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TimePost
        fields = ['id', 'title', 'description', 'type', 'latitude', 'longitude', 'created_at', 'price', 'user']

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'receiver', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp', 'sender', 'receiver', 'room']

# ✅ 1. 기본 채팅방 정보를 위한 RoomSerializer를 다시 정의합니다.
#    MatchRequestView와 ChatRoomDetailView에서 사용됩니다.
class RoomSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    post = SimpleTimePostSerializer(read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'post', 'users', 'created_at']
    

# ✅ 2. 채팅방 '목록'에 필요한 상세 정보를 담는 ChatRoomListSerializer는 그대로 유지합니다.
#    MyChatsView에서 사용됩니다.
class ChatRoomListSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    post = SimpleTimePostSerializer(read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'post', 'other_user', 'last_message', 'created_at']

    def get_other_user(self, obj):
        user = self.context['request'].user
        other_user = obj.users.exclude(id=user.id).first()
        return UserSerializer(other_user, context=self.context).data if other_user else None

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        return ChatMessageSerializer(last_msg, context=self.context).data if last_msg else None


class TradeRequestSerializer(serializers.ModelSerializer):
    requester = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    post = SimpleTimePostSerializer(read_only=True)
    
    class Meta:
        model = TradeRequest
        fields = [
            'id', 'room', 'post', 'requester', 'receiver',
            'proposed_price', 'proposed_hours', 'message',
            'status', 'requester_accepted', 'receiver_accepted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status']


class TradeRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeRequest
        fields = ['proposed_price', 'proposed_hours', 'message']
        
    def validate_proposed_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("제안 가격은 0보다 커야 합니다.")
        return value
    
    def validate_proposed_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("제안 시간은 0보다 커야 합니다.")
        return value
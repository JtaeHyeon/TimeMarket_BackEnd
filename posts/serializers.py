from rest_framework import serializers
from .models import TimePost
from users.serializers import UserSerializer
from django.utils import timezone
from datetime import datetime
import math


class TimePostSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    # UI 친화적인 추가 필드들
    distance = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()
    type_display = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()
    is_urgent = serializers.SerializerMethodField()
    
    class Meta:
        model = TimePost
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user']
    
    def get_distance(self, obj):
        """사용자 위치로부터의 거리 계산 (km 단위)"""
        request = self.context.get('request')
        if not request:
            return None
            
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')
        
        if not (user_lat and user_lng and obj.latitude and obj.longitude):
            return None
            
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            
            # Haversine 공식으로 거리 계산
            lat1, lon1, lat2, lon2 = map(math.radians, [user_lat, user_lng, obj.latitude, obj.longitude])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371 * c  # 지구 반지름 (km)
            
            if distance < 1:
                return f"{int(distance * 1000)}m"
            else:
                return f"{distance:.1f}km"
        except:
            return None
    
    def get_time_ago(self, obj):
        """게시물 작성 시간을 상대적 시간으로 표시"""
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days}일 전"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}시간 전"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}분 전"
        else:
            return "방금 전"
    
    def get_formatted_price(self, obj):
        """가격을 포맷팅하여 표시"""
        if obj.price == 0:
            return "무료"
        elif obj.price >= 10000:
            return f"{obj.price // 10000}만원"
        elif obj.price >= 1000:
            return f"{obj.price // 1000}천원"
        else:
            return f"{obj.price:,}원"
    
    def get_type_display(self, obj):
        """게시물 타입을 한글로 표시"""
        return obj.get_type_display()
    
    def get_status_color(self, obj):
        """게시물 타입에 따른 상태 색상"""
        colors = {
            'sale': '#4CAF50',  # 초록색 (시간 판매)
            'request': '#2196F3'  # 파란색 (구인)
        }
        return colors.get(obj.type, '#757575')
    
    def get_is_urgent(self, obj):
        """긴급 게시물 여부 (1시간 이내 작성된 게시물)"""
        now = timezone.now()
        diff = now - obj.created_at
        return diff.total_seconds() < 3600  # 1시간 = 3600초


class TimePostCreateSerializer(serializers.ModelSerializer):
    """게시물 생성용 시리얼라이저 (간소화된 필드)"""
    class Meta:
        model = TimePost
        fields = ['title', 'description', 'type', 'latitude', 'longitude', 'price']
        
    def validate_price(self, value):
        """가격 유효성 검사"""
        if value < 0:
            raise serializers.ValidationError("가격은 0 이상이어야 합니다.")
        return value

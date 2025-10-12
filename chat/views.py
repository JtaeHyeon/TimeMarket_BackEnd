from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Room, ChatMessage, TradeRequest
from .serializers import (
    RoomSerializer, ChatMessageSerializer, ChatRoomListSerializer,
    TradeRequestSerializer, TradeRequestCreateSerializer
)
from users.models import User
from posts.models import TimePost
from django.http import Http404
from push_notice.services import send_push_to_user


class MatchRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        post_id = request.data.get('post_id')

        try:
            post = TimePost.objects.get(id=post_id)
        except TimePost.DoesNotExist:
            raise Http404("TimePost with the given ID does not exist.")

        # ✅ 'post.author'를 올바른 필드 이름인 'post.user'로 수정했습니다.
        receiver = post.user
        
        # 자신의 게시글에는 채팅을 시작할 수 없음
        if receiver == request.user:
            return Response(
                {"error": "자신의 게시글에는 채팅을 시작할 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 해당 게시글에 대해 나와 상대방이 이미 참여하고 있는 채팅방이 있는지 확인
        existing_room = Room.objects.prefetch_related('users', 'post__user').filter(
            post=post,
            users=request.user
        ).filter(users=receiver).first()
        if existing_room:
            serializer = RoomSerializer(existing_room, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        room = Room.objects.create(post=post)
        room.users.add(request.user, receiver)
        
        # ManyToMany 관계를 포함해서 room을 다시 가져옴
        room = Room.objects.prefetch_related('users', 'post__user').get(id=room.id)

        try:
            title = f"{request.user.nickname}와 새로운 채팅방"
            body = f"게시글: {post.title}"
            data = {"type": "room_created", "room_id": str(room.id), "post_id": str(post.id)}
            send_push_to_user(receiver, title, body, data)
        except Exception:
            pass

        # context를 명시적으로 전달
        serializer = RoomSerializer(room, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyChatsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRoomListSerializer

    def get_queryset(self):
        return Room.objects.filter(users=self.request.user).select_related('post__user').prefetch_related('users', 'messages')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class ChatRoomDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Room.objects.select_related('post__user').prefetch_related('users')
    serializer_class = RoomSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'room_id'
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class ChatMessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        return ChatMessage.objects.filter(room__id=room_id).order_by('timestamp')

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        room = Room.objects.get(id=room_id)
        receiver = room.users.exclude(id=self.request.user.id).first()

        if not receiver:
            raise serializers.ValidationError("상대방을 찾을 수 없습니다.")

        serializer.save(
            room=room,
            sender=self.request.user,
            receiver=receiver
        )


class TradeRequestListView(generics.ListAPIView):
    """채팅방의 거래 요청 목록 조회"""
    permission_classes = [IsAuthenticated]
    serializer_class = TradeRequestSerializer

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        # 사용자가 참여한 채팅방의 거래 요청만 조회
        return TradeRequest.objects.filter(
            room__id=room_id,
            room__users=self.request.user
        ).order_by('-created_at')


class TradeRequestCreateView(generics.CreateAPIView):
    """거래 요청 생성 (REST API용 - WebSocket 대신 사용 가능)"""
    permission_classes = [IsAuthenticated]
    serializer_class = TradeRequestCreateSerializer

    def perform_create(self, serializer):
        room_id = self.kwargs['room_id']
        try:
            room = Room.objects.select_related('post__user').get(id=room_id)
        except Room.DoesNotExist:
            raise serializers.ValidationError("채팅방을 찾을 수 없습니다.")
        
        # 사용자가 이 채팅방에 참여하고 있는지 확인
        if not room.users.filter(id=self.request.user.id).exists():
            raise serializers.ValidationError("이 채팅방에 접근할 권한이 없습니다.")
        
        # ✅ 검증: 자신의 게시글에는 거래 요청을 할 수 없음
        if room.post.user.id == self.request.user.id:
            post_type_display = room.post.get_type_display()
            raise serializers.ValidationError(f"자신의 {post_type_display}에는 거래 요청을 할 수 없습니다.")
        
        receiver = room.users.exclude(id=self.request.user.id).first()

        if not receiver:
            raise serializers.ValidationError("상대방을 찾을 수 없습니다.")

        serializer.save(
            room=room,
            post=room.post,
            requester=self.request.user,
            receiver=receiver
        )


class TradeRequestDetailView(generics.RetrieveUpdateAPIView):
    """거래 요청 상세 조회 및 수정"""
    permission_classes = [IsAuthenticated]
    serializer_class = TradeRequestSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'trade_id'

    def get_queryset(self):
        return TradeRequest.objects.filter(
            room__users=self.request.user
        )

    def perform_update(self, serializer):
        from django.db import transaction
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        with transaction.atomic():
            # 🔒 락을 걸어서 거래 요청 조회
            trade_request = TradeRequest.objects.select_for_update().select_related(
                'post__user', 'requester', 'receiver'
            ).get(id=self.kwargs['trade_id'])
            
            # ✅ 이미 처리된 거래는 수정 불가
            if trade_request.status in ['completed', 'rejected', 'cancelled']:
                raise serializers.ValidationError(f"이미 처리된 거래는 수정할 수 없습니다 (상태: {trade_request.get_status_display()})")
            
            # 사용자가 요청자인지 수신자인지 확인
            if trade_request.requester == self.request.user:
                # 요청자는 자신의 수락 상태만 변경 가능
                if 'requester_accepted' in self.request.data:
                    serializer.save(requester_accepted=self.request.data['requester_accepted'])
            elif trade_request.receiver == self.request.user:
                # 수신자는 자신의 수락 상태만 변경 가능
                if 'receiver_accepted' in self.request.data:
                    serializer.save(receiver_accepted=self.request.data['receiver_accepted'])
            else:
                raise serializers.ValidationError("이 거래 요청에 대한 권한이 없습니다.")
            
            # 거래 완료 확인 (객체를 새로고침하고 확인)
            trade_request.refresh_from_db()
            
            # 양쪽 모두 수락했는지 확인하고 거래 처리
            if trade_request.requester_accepted and trade_request.receiver_accepted and trade_request.status == 'pending':
                try:
                    # ✅ 모델의 process_trade 메서드를 사용하여 거래 처리
                    trade_request.process_trade()
                except DjangoValidationError as e:
                    # Django ValidationError를 DRF ValidationError로 변환
                    raise serializers.ValidationError(str(e))


class TradeHistoryView(generics.ListAPIView):
    """사용자의 전체 거래 히스토리 조회"""
    permission_classes = [IsAuthenticated]
    serializer_class = TradeRequestSerializer

    def get_queryset(self):
        # 사용자가 참여한 모든 채팅방의 거래 요청을 조회
        return TradeRequest.objects.filter(
            room__users=self.request.user
        ).select_related(
            'room', 'post', 'post__user', 'requester', 'receiver'
        ).order_by('-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
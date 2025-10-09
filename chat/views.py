from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Room, ChatMessage
from .serializers import RoomSerializer, ChatMessageSerializer, ChatRoomListSerializer
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

        # 나와 상대방이 이미 참여하고 있는 채팅방이 있는지 확인
        existing_room = Room.objects.prefetch_related('users', 'post__user').filter(users=request.user).filter(users=receiver).first()
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
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, ChatMessage, TradeRequest
from users.models import User
from posts.models import TimePost
from asgiref.sync import sync_to_async
# ✅ serializers를 import하여 데이터 형식을 통일합니다.
from .serializers import ChatMessageSerializer, TradeRequestSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"🔌 WebSocket 연결 시도: {self.scope}")
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']
        
        print(f"📍 방 이름: {self.room_name}, 사용자: {self.user}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"✅ WebSocket 연결 수락됨")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'chat')  # 기본값은 채팅
        
        if message_type == 'chat':
            await self.handle_chat_message(data)
        elif message_type == 'trade_request':
            await self.handle_trade_request(data)
        elif message_type == 'trade_response':
            await self.handle_trade_response(data)
    
    async def handle_chat_message(self, data):
        """기존 채팅 메시지 처리"""
        message = data['message']

        receiver = await self.get_receiver()

        if not receiver:
            print("🚨 상대방을 찾을 수 없어 메시지를 저장하지 않습니다.")
            return

        # ✅ DB에 메시지를 저장하고, 저장된 객체를 받아옵니다.
        new_message_obj = await self.save_message(
            self.room_name,
            self.user,
            receiver,
            message
        )

        # ✅ Serializer를 사용해 new_message_obj를 JSON으로 변환합니다.
        #    이렇게 하면 모든 데이터 타입(id는 int, 나머지는 string 등)이 정확해집니다.
        serialized_message = await self.serialize_message(new_message_obj)

        # 그룹 전체로 직렬화된 메시지 데이터를 전송합니다.
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': serialized_message  # ✅ 직렬화된 데이터를 전송
            }
        )
    
    async def handle_trade_request(self, data):
        """거래 요청 처리"""
        try:
            receiver = await self.get_receiver()
            room = await self.get_room()
            
            if not receiver or not room:
                await self.send_error("상대방 또는 채팅방을 찾을 수 없습니다.")
                return
            
            # 거래 요청 생성
            trade_request = await self.create_trade_request(
                room=room,
                requester=self.user,
                receiver=receiver,
                proposed_price=data['proposed_price'],
                proposed_hours=data['proposed_hours'],
                message=data.get('message', '')
            )
            
            # 거래 요청 직렬화
            serialized_trade = await self.serialize_trade_request(trade_request)
            
            # 그룹에 거래 요청 알림
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'trade_request_notification',
                    'trade_request': serialized_trade
                }
            )
            
        except Exception as e:
            await self.send_error(f"거래 요청 처리 중 오류가 발생했습니다: {str(e)}")
    
    async def handle_trade_response(self, data):
        """거래 응답 처리 (수락/거절)"""
        try:
            trade_request_id = data['trade_request_id']
            response = data['response']  # 'accept' 또는 'reject'
            
            trade_request = await self.get_trade_request(trade_request_id)
            
            if not trade_request:
                await self.send_error("거래 요청을 찾을 수 없습니다.")
                return
            
            # 사용자 권한 확인 및 응답 처리
            updated_trade = await self.update_trade_response(trade_request, self.user, response)
            
            if not updated_trade:
                await self.send_error("이 거래 요청에 대한 권한이 없습니다.")
                return
            
            # 거래 상태 업데이트 알림
            serialized_trade = await self.serialize_trade_request(updated_trade)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'trade_status_update',
                    'trade_request': serialized_trade,
                    'is_completed': updated_trade.status == 'completed'
                }
            )
            
        except Exception as e:
            await self.send_error(f"거래 응답 처리 중 오류가 발생했습니다: {str(e)}")

    async def chat_message(self, event):
        # ✅ 받은 데이터를 그대로 클라이언트에게 전송합니다.
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'data': event['message']
        }))
    
    async def trade_request_notification(self, event):
        """거래 요청 알림"""
        await self.send(text_data=json.dumps({
            'type': 'trade_request',
            'data': event['trade_request']
        }))
    
    async def trade_status_update(self, event):
        """거래 상태 업데이트 알림"""
        await self.send(text_data=json.dumps({
            'type': 'trade_status_update',
            'data': event['trade_request'],
            'is_completed': event['is_completed']
        }))
    
    async def send_error(self, message):
        """에러 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    @sync_to_async
    def save_message(self, room_id, sender, receiver, message):
        room = Room.objects.get(id=int(room_id))
        # ✅ create()는 생성된 객체를 반환합니다.
        return ChatMessage.objects.create(room=room, sender=sender, receiver=receiver, message=message)

    @sync_to_async
    def get_receiver(self):
        room = Room.objects.get(id=int(self.room_name))
        receiver = room.users.exclude(id=self.user.id).first()
        return receiver

    # ✅ 메시지 객체를 직렬화하는 헬퍼 함수 추가
    @sync_to_async
    def serialize_message(self, message_obj):
        return ChatMessageSerializer(message_obj).data
    
    @sync_to_async
    def get_room(self):
        """현재 채팅방 객체 가져오기"""
        try:
            return Room.objects.get(id=int(self.room_name))
        except Room.DoesNotExist:
            return None
    
    @sync_to_async
    def create_trade_request(self, room, requester, receiver, proposed_price, proposed_hours, message):
        """거래 요청 생성"""
        return TradeRequest.objects.create(
            room=room,
            post=room.post,
            requester=requester,
            receiver=receiver,
            proposed_price=proposed_price,
            proposed_hours=proposed_hours,
            message=message
        )
    
    @sync_to_async
    def get_trade_request(self, trade_request_id):
        """거래 요청 가져오기"""
        try:
            return TradeRequest.objects.get(id=trade_request_id)
        except TradeRequest.DoesNotExist:
            return None
    
    @sync_to_async
    def save_trade_request(self, trade_request):
        """거래 요청 저장"""
        trade_request.save()
        return trade_request
    
    @sync_to_async
    def update_trade_response(self, trade_request, user, response):
        """거래 응답 업데이트 및 완료 확인"""
        # 사용자가 요청자인지 수신자인지 확인
        if trade_request.requester.id == user.id:
            trade_request.requester_accepted = (response == 'accept')
        elif trade_request.receiver.id == user.id:
            trade_request.receiver_accepted = (response == 'accept')
        else:
            return None  # 권한 없음
        
        # 거절인 경우 상태를 바로 거절로 변경
        if response == 'reject':
            trade_request.status = 'rejected'
        # 양쪽 모두 수락했는지 확인하고 상태 업데이트
        elif trade_request.requester_accepted and trade_request.receiver_accepted and trade_request.status == 'pending':
            trade_request.status = 'completed'
        
        trade_request.save()
        return trade_request
    
    @sync_to_async
    def serialize_trade_request(self, trade_request):
        """거래 요청 직렬화"""
        return TradeRequestSerializer(trade_request).data
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, ChatMessage, TradeRequest
from users.models import User
from posts.models import TimePost
from wallet.models import Wallet, Transaction
from asgiref.sync import sync_to_async
from django.db import transaction
# ✅ serializers를 import하여 데이터 형식을 통일합니다.
from .serializers import ChatMessageSerializer, TradeRequestSerializer
from rest_framework import serializers as rest_serializers
import logging

logger = logging.getLogger(__name__)


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
            
            logger.info(f"[WebSocket 거래 요청 생성]")
            logger.info(f"  - 요청자(self.user): {self.user.nickname}")
            logger.info(f"  - 수신자(receiver): {receiver.nickname if receiver else 'None'}")
            logger.info(f"  - 채팅방: {room.id if room else 'None'}")
            logger.info(f"  - 게시글 작성자: {room.post.user.nickname if room and room.post else 'None'}")
            
            if not receiver or not room:
                await self.send_error("상대방 또는 채팅방을 찾을 수 없습니다.")
                return
            
            # ✅ 검증: 자신의 게시글에는 거래 요청을 할 수 없음
            if room.post.user.id == self.user.id:
                post_type_display = "판매글" if room.post.type == 'sale' else "구인글"
                error_msg = f"자신의 {post_type_display}에는 거래 요청을 할 수 없습니다."
                logger.warning(f"  - ❌ {error_msg}")
                await self.send_error(error_msg)
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
            
            logger.info(f"  - 생성된 거래 요청 ID: {trade_request.id}")
            logger.info(f"  - 저장된 requester: {trade_request.requester.nickname}")
            logger.info(f"  - 저장된 receiver: {trade_request.receiver.nickname}")
            
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
            logger.error(f"  - ❌ 거래 요청 처리 실패: {str(e)}", exc_info=True)
            await self.send_error(f"거래 요청 처리 중 오류가 발생했습니다: {str(e)}")
    
    async def handle_trade_response(self, data):
        """거래 응답 처리 (수락/거절)"""
        try:
            trade_request_id = data['trade_request_id']
            response = data['response']  # 'accept' 또는 'reject'
            
            # 거래 요청이 존재하는지만 확인
            trade_exists = await self.check_trade_exists(trade_request_id)
            
            if not trade_exists:
                await self.send_error("거래 요청을 찾을 수 없습니다.")
                return
            
            # ID만 전달하여 처리
            updated_trade = await self.update_trade_response_by_id(trade_request_id, self.user.id, response)
            
            if not updated_trade:
                await self.send_error("이 거래 요청에 대한 권한이 없습니다.")
                return
            
            # 거래 상태 업데이트 알림
            serialized_trade = await self.serialize_trade_request_by_id(trade_request_id)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'trade_status_update',
                    'trade_request': serialized_trade,
                    'is_completed': serialized_trade['status'] == 'completed'
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
        room = Room.objects.prefetch_related('users').get(id=int(self.room_name))
        receiver = room.users.exclude(id=self.user.id).first()
        return receiver

    def _create_fake_request(self):
        """WebSocket에서 사용할 가짜 request 객체 생성"""
        class FakeRequest:
            def __init__(self, scope):
                self.scope = scope
            
            def build_absolute_uri(self, path):
                # WebSocket scope에서 host 정보 가져오기
                headers = dict(self.scope.get('headers', []))
                host = headers.get(b'host', b'localhost:8000').decode('utf-8')
                scheme = 'https' if self.scope.get('scheme') == 'wss' else 'http'
                return f"{scheme}://{host}{path}"
        
        return FakeRequest(self.scope)
    
    # ✅ 메시지 객체를 직렬화하는 헬퍼 함수 추가
    @sync_to_async
    def serialize_message(self, message_obj):
        fake_request = self._create_fake_request()
        return ChatMessageSerializer(message_obj, context={'request': fake_request}).data
    
    @sync_to_async
    def get_room(self):
        """현재 채팅방 객체 가져오기"""
        try:
            return Room.objects.select_related('post__user').get(id=int(self.room_name))
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
    def check_trade_exists(self, trade_request_id):
        """거래 요청 존재 여부 확인"""
        return TradeRequest.objects.filter(id=trade_request_id).exists()
    
    async def update_trade_response_by_id(self, trade_request_id, user_id, response):
        """거래 응답 업데이트 및 완료 확인 (ID 기반)"""
        logger.info(f"[WebSocket 거래 응답] Trade #{trade_request_id} by user #{user_id}")
        logger.info(f"  - 응답: {response}")
        
        # ID만 전달하여 sync 함수에서 다시 조회
        # 성공 여부만 리턴 (True/False/None)
        result = await self._update_trade_response_sync(trade_request_id, user_id, response)
        return result
    
    @sync_to_async
    def serialize_trade_request_by_id(self, trade_request_id):
        """거래 요청 직렬화 (ID 기반)"""
        trade_request = TradeRequest.objects.select_related('post__user', 'requester', 'receiver').get(id=trade_request_id)
        fake_request = self._create_fake_request()
        return TradeRequestSerializer(trade_request, context={'request': fake_request}).data
    
    @sync_to_async
    def _update_trade_response_sync(self, trade_request_id, user_id, response):
        """거래 응답 업데이트 및 처리 (모든 동기 로직을 하나로 통합)"""
        
        # 🔒 트랜잭션 전체를 atomic으로 감싸서 동시성 문제 방지
        with transaction.atomic():
            # 🔒 TradeRequest에 락을 걸어 중복 처리 방지
            trade_request = TradeRequest.objects.select_for_update().select_related(
                'post__user', 'requester', 'receiver'
            ).get(id=trade_request_id)
            
            user = User.objects.get(id=user_id)
            
            # ✅ 이미 처리된 거래는 재처리하지 않음
            if trade_request.status in ['completed', 'rejected', 'cancelled']:
                logger.warning(f"[거래 응답 거부] Trade #{trade_request_id} - 이미 처리된 거래 (상태: {trade_request.status})")
                return False
            
            # 사용자가 요청자인지 수신자인지 확인
            if trade_request.requester.id == user.id:
                trade_request.requester_accepted = (response == 'accept')
                logger.info(f"  - 요청자({user.nickname})가 {'수락' if response == 'accept' else '거절'}")
            elif trade_request.receiver.id == user.id:
                trade_request.receiver_accepted = (response == 'accept')
                logger.info(f"  - 수신자({user.nickname})가 {'수락' if response == 'accept' else '거절'}")
            else:
                logger.warning(f"  - ❌ 권한 없음")
                return None  # 권한 없음
            
            trade_request.save()
            
            # 거절인 경우 상태를 바로 거절로 변경
            if response == 'reject':
                trade_request.status = 'rejected'
                trade_request.save()
                logger.info(f"  - 거래 거절됨")
                return True
            
            # 양쪽 모두 수락했는지 확인
            if not (trade_request.requester_accepted and trade_request.receiver_accepted):
                logger.info(f"  - 한쪽만 수락함. 대기 중...")
                return True
            
            # 🎉 양쪽 모두 수락! 거래 처리 시작
            logger.info(f"  - 🎉 양쪽 모두 수락! 거래 처리 시작")
            
            try:
                post = trade_request.post
                requester = trade_request.requester
                receiver = trade_request.receiver
                proposed_hours = trade_request.proposed_hours
                
                logger.info(f"[거래 처리 시작] Trade #{trade_request.id}")
                logger.info(f"  - 게시글 ID: {post.id}")
                logger.info(f"  - 게시글 타입: {post.type} ({post.get_type_display()})")
                logger.info(f"  - 게시글 작성자: {post.user.nickname}")
                logger.info(f"  - 거래 요청자: {requester.nickname}")
                logger.info(f"  - 거래 수신자: {receiver.nickname}")
                logger.info(f"  - 거래 시간: {proposed_hours}시간")
                
                # ✅ 게시글 타입에 따라 역할 구분 및 검증
                if post.type == 'sale':
                    # 판매 글: 게시글 작성자가 판매자, 거래 요청자가 구매자
                    seller = post.user
                    buyer = requester
                    
                    # ✅ 검증: 구매자는 판매자가 아니어야 함
                    if buyer.id == seller.id:
                        logger.error(f"  - ❌ 검증 실패: 자신의 판매글은 구매할 수 없음")
                        trade_request.status = 'rejected'
                        trade_request.save()
                        raise rest_serializers.ValidationError("자신의 판매글은 구매할 수 없습니다.")
                    
                    payer = buyer      # 구매자가 지불
                    payee = seller     # 판매자가 받음
                    
                    logger.info(f"  - [판매 타입] 구매자({payer.nickname})가 판매자({payee.nickname})에게 {proposed_hours}시간 지불")
                    
                elif post.type == 'request':
                    # 구인 글: 게시글 작성자가 구인자(고용주), 거래 요청자가 지원자(일꾼)
                    employer = post.user
                    worker = requester
                    
                    # ✅ 검증: 지원자는 구인자가 아니어야 함
                    if worker.id == employer.id:
                        logger.error(f"  - ❌ 검증 실패: 자신의 구인글에는 지원할 수 없음")
                        trade_request.status = 'rejected'
                        trade_request.save()
                        raise rest_serializers.ValidationError("자신의 구인글에는 지원할 수 없습니다.")
                    
                    payer = employer   # 구인자가 지불
                    payee = worker     # 지원자가 받음
                    
                    logger.info(f"  - [구인 타입] 구인자({payer.nickname})가 지원자({payee.nickname})에게 {proposed_hours}시간 지불")
                    
                else:
                    logger.error(f"  - ❌ 알 수 없는 게시글 타입: {post.type}")
                    trade_request.status = 'rejected'
                    trade_request.save()
                    raise rest_serializers.ValidationError(f"알 수 없는 게시글 타입: {post.type}")
                
                # 🔒 지갑에 락을 걸어 동시성 문제 방지
                # 지갑이 없으면 생성
                payer_wallet, _ = Wallet.objects.get_or_create(user=payer)
                payee_wallet, _ = Wallet.objects.get_or_create(user=payee)
                
                # 다시 락을 걸어서 조회 (생성 후에도 락 필요)
                payer_wallet = Wallet.objects.select_for_update().get(id=payer_wallet.id)
                payee_wallet = Wallet.objects.select_for_update().get(id=payee_wallet.id)
                
                logger.info(f"  - 거래 전 잔액:")
                logger.info(f"    * {payer.nickname} (지불자): {payer_wallet.balance}시간")
                logger.info(f"    * {payee.nickname} (수령자): {payee_wallet.balance}시간")
                
                # ✅ 잔액 확인
                if payer_wallet.balance < proposed_hours:
                    logger.warning(f"  - ❌ 잔액 부족!")
                    logger.warning(f"    * {payer.nickname}님의 잔액: {payer_wallet.balance}시간")
                    logger.warning(f"    * 필요 금액: {proposed_hours}시간")
                    logger.warning(f"    * 부족 금액: {proposed_hours - payer_wallet.balance}시간")
                    
                    trade_request.status = 'rejected'
                    trade_request.save()
                    
                    raise rest_serializers.ValidationError(
                        f"{payer.nickname}님의 잔액이 부족하여 거래가 거절되었습니다. "
                        f"필요: {proposed_hours}시간, 현재 잔액: {payer_wallet.balance}시간"
                    )
                
                logger.info(f"  - ✅ 잔액 충분! 거래 실행 중...")
                
                # 💰 거래 실행
                payer_wallet.balance -= proposed_hours
                payee_wallet.balance += proposed_hours
                
                payer_wallet.save()
                payee_wallet.save()
                
                logger.info(f"  - 거래 후 잔액:")
                logger.info(f"    * {payer.nickname}: {payer_wallet.balance}시간 (변경: -{proposed_hours})")
                logger.info(f"    * {payee.nickname}: {payee_wallet.balance}시간 (변경: +{proposed_hours})")
                
                # 📝 거래 내역 기록
                transaction_note_payer = (
                    f"[{post.get_type_display()}] 거래 #{trade_request.id}: "
                    f"{payee.nickname}님에게 {proposed_hours}시간 지불 (게시글: {post.title})"
                )
                transaction_note_payee = (
                    f"[{post.get_type_display()}] 거래 #{trade_request.id}: "
                    f"{payer.nickname}님으로부터 {proposed_hours}시간 받음 (게시글: {post.title})"
                )
                
                Transaction.objects.create(
                    wallet=payer_wallet,
                    transaction_type='withdraw',
                    amount=proposed_hours,
                    note=transaction_note_payer
                )
                
                Transaction.objects.create(
                    wallet=payee_wallet,
                    transaction_type='deposit',
                    amount=proposed_hours,
                    note=transaction_note_payee
                )
                
                logger.info(f"  - 거래 내역 기록 완료")
                
                # ✅ 거래 완료 상태로 변경
                trade_request.status = 'completed'
                trade_request.save()
                
                logger.info(f"[거래 완료] Trade #{trade_request.id} ✅")
                logger.info(f"  - 상태: completed")
                logger.info(f"  - 거래 타입: {post.get_type_display()}")
                logger.info(f"  - {payer.nickname} → {payee.nickname}: {proposed_hours}시간")
                
                return True
                
            except rest_serializers.ValidationError as e:
                # 검증 오류는 그대로 전달
                logger.error(f"  - ❌ 검증 오류: {str(e)}")
                raise
            except Exception as e:
                # 기타 오류 처리
                logger.error(f"  - ❌ 거래 처리 실패: {str(e)}", exc_info=True)
                trade_request.refresh_from_db()
                if trade_request.status not in ['rejected', 'completed']:
                    trade_request.status = 'rejected'
                    trade_request.save()
                raise rest_serializers.ValidationError(f"거래 처리 중 오류가 발생했습니다: {str(e)}")
    
    @sync_to_async
    def serialize_trade_request(self, trade_request):
        """거래 요청 직렬화"""
        fake_request = self._create_fake_request()
        return TradeRequestSerializer(trade_request, context={'request': fake_request}).data
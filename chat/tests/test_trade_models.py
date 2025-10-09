from django.test import TestCase
from django.contrib.auth import get_user_model
from chat.models import Room, TradeRequest
from posts.models import TimePost

User = get_user_model()


class TradeRequestModelTest(TestCase):
    def setUp(self):
        """테스트용 데이터 설정"""
        # 사용자 생성
        self.user1 = User.objects.create_user(
            nickname='test',
            email='test@gmail.com',
            password='test'
        )
        self.user2 = User.objects.create_user(
            nickname='admin',
            email='admin@gmail.com',
            password='admin'
        )
        
        # 게시글 생성
        self.post = TimePost.objects.create(
            user=self.user1,
            title='컴퓨터 수리 도움',
            description='컴퓨터 수리 도와드립니다',
            type='sale',
            price=10000
        )
        
        # 채팅방 생성
        self.room = Room.objects.create(post=self.post)
        self.room.users.add(self.user1, self.user2)

    def test_create_trade_request(self):
        """거래 요청 생성 테스트"""
        trade_request = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5,
            message='도움 요청드립니다'
        )
        
        self.assertEqual(trade_request.status, 'pending')
        self.assertFalse(trade_request.requester_accepted)
        self.assertFalse(trade_request.receiver_accepted)
        self.assertEqual(trade_request.proposed_price, 15000)
        self.assertEqual(trade_request.proposed_hours, 2.5)

    def test_trade_completion_both_accept(self):
        """양쪽 모두 수락시 거래 완료 테스트"""
        trade_request = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5
        )
        
        # 양쪽 모두 수락
        trade_request.requester_accepted = True
        trade_request.receiver_accepted = True
        
        # 완료 확인
        is_completed = trade_request.check_completion()
        
        self.assertTrue(is_completed)
        self.assertEqual(trade_request.status, 'completed')

    def test_trade_not_completed_partial_accept(self):
        """한쪽만 수락시 거래 미완료 테스트"""
        trade_request = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5
        )
        
        # 한쪽만 수락
        trade_request.requester_accepted = True
        trade_request.receiver_accepted = False
        
        # 완료 확인
        is_completed = trade_request.check_completion()
        
        self.assertFalse(is_completed)
        self.assertEqual(trade_request.status, 'pending')

    def test_trade_request_string_representation(self):
        """거래 요청 문자열 표현 테스트"""
        trade_request = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5
        )
        
        expected_str = f"거래요청 {trade_request.id}: {self.user2} -> {self.user1}"
        self.assertEqual(str(trade_request), expected_str)

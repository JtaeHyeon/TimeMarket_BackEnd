from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from chat.models import Room, TradeRequest
from posts.models import TimePost

User = get_user_model()


class TradeRequestViewTest(TestCase):
    def setUp(self):
        """테스트용 데이터 설정"""
        self.client = APIClient()
        
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
        
        # JWT 토큰 생성
        self.token1 = RefreshToken.for_user(self.user1).access_token
        self.token2 = RefreshToken.for_user(self.user2).access_token

    def authenticate_user1(self):
        """사용자1로 인증"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token1}')

    def authenticate_user2(self):
        """사용자2로 인증"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token2}')

    def test_create_trade_request(self):
        """거래 요청 생성 테스트"""
        self.authenticate_user2()
        
        url = reverse('trade-create', kwargs={'room_id': self.room.id})
        data = {
            'proposed_price': 15000,
            'proposed_hours': 2.5,
            'message': '도움 요청드립니다'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TradeRequest.objects.count(), 1)
        
        trade_request = TradeRequest.objects.first()
        self.assertEqual(trade_request.requester, self.user2)
        self.assertEqual(trade_request.receiver, self.user1)
        self.assertEqual(trade_request.proposed_price, 15000)

    def test_list_trade_requests(self):
        """거래 요청 목록 조회 테스트"""
        # 거래 요청 생성
        TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5
        )
        
        self.authenticate_user1()
        
        url = reverse('trade-list', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['proposed_price'], '15000.00')

    def test_update_trade_request_accept(self):
        """거래 요청 수락 테스트"""
        trade_request = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user2,
            receiver=self.user1,
            proposed_price=15000,
            proposed_hours=2.5
        )
        
        self.authenticate_user1()  # 수신자로 인증
        
        url = reverse('trade-detail', kwargs={'trade_id': trade_request.id})
        data = {'receiver_accepted': True}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        trade_request.refresh_from_db()
        self.assertTrue(trade_request.receiver_accepted)

    def test_unauthorized_access(self):
        """인증되지 않은 접근 테스트"""
        url = reverse('trade-list', kwargs={'room_id': self.room.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_room_access(self):
        """잘못된 채팅방 접근 테스트"""
        # 다른 사용자 생성
        other_user = User.objects.create_user(
            nickname='other',
            email='other@gmail.com',
            password='other'
        )
        other_token = RefreshToken.for_user(other_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        
        url = reverse('trade-create', kwargs={'room_id': self.room.id})
        data = {
            'proposed_price': 15000,
            'proposed_hours': 2.5
        }
        
        response = self.client.post(url, data, format='json')
        
        # 채팅방에 속하지 않은 사용자는 거래 요청을 생성할 수 없음
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

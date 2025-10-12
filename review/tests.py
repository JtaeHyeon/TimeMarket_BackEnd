from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from chat.models import Room, TradeRequest
from posts.models import TimePost
from review.models import Review
from decimal import Decimal

User = get_user_model()


class ReviewValidationTest(TestCase):
    def setUp(self):
        # 테스트 유저 생성
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            nickname='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            nickname='user2',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            email='user3@test.com',
            nickname='user3',
            password='testpass123'
        )

        # TimePost 생성 (실제 필드명 사용)
        self.post = TimePost.objects.create(
            user=self.user1,
            title='테스트 포스트',
            description='테스트 내용',
            type='sale',
            price=10000
        )

        # Room 생성
        self.room = Room.objects.create(post=self.post)
        self.room.users.add(self.user1, self.user2)

        # 완료된 거래 생성
        self.completed_trade = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user1,
            receiver=self.user2,
            proposed_price=10000,
            proposed_hours=5,
            status='completed'
        )

        # 완료되지 않은 거래 생성
        self.pending_trade = TradeRequest.objects.create(
            room=self.room,
            post=self.post,
            requester=self.user1,
            receiver=self.user2,
            proposed_price=10000,
            proposed_hours=5,
            status='pending'
        )

        self.client = APIClient()

    def test_completed_trade_only(self):
        """❌ 완료되지 않은 거래에는 작성 불가"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post('/api/reviews/create/', {
            'trade': self.pending_trade.id,
            'rating': 4.5,
            'content': '좋았습니다'
        })

        print(f"\n[TEST 1] 완료되지 않은 거래 리뷰 작성: {response.status_code}")
        print(f"응답: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('완료된 거래', str(response.data))

    def test_participant_only(self):
        """❌ 거래 참여자가 아니면 작성 불가"""
        self.client.force_authenticate(user=self.user3)

        response = self.client.post('/api/reviews/create/', {
            'trade': self.completed_trade.id,
            'rating': 4.5,
            'content': '좋았습니다'
        })

        print(f"\n[TEST 2] 거래 참여자 아닌 사용자 리뷰 작성: {response.status_code}")
        print(f"응답: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('참여하지 않은', str(response.data))

    def test_duplicate_review(self):
        """❌ 같은 거래에 대해 중복 작성 불가"""
        self.client.force_authenticate(user=self.user1)

        # 첫 번째 리뷰 작성
        response1 = self.client.post('/api/reviews/create/', {
            'trade': self.completed_trade.id,
            'rating': 4.5,
            'content': '첫 번째 리뷰'
        })

        print(f"\n[TEST 3-1] 첫 번째 리뷰 작성: {response1.status_code}")
        print(f"응답: {response1.data}")

        # 두 번째 리뷰 작성 시도
        response2 = self.client.post('/api/reviews/create/', {
            'trade': self.completed_trade.id,
            'rating': 5.0,
            'content': '두 번째 리뷰'
        })

        print(f"\n[TEST 3-2] 중복 리뷰 작성 시도: {response2.status_code}")
        print(f"응답: {response2.data}")

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('이미', str(response2.data))

    def test_zero_rating_not_allowed(self):
        """❌ 별점 0점은 제출 불가"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post('/api/reviews/create/', {
            'trade': self.completed_trade.id,
            'rating': 0,
            'content': '별점 0점'
        })

        print(f"\n[TEST 4] 별점 0점 제출: {response.status_code}")
        print(f"응답: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rating_half_unit_only(self):
        """✅ 별점은 0.5 단위로만 가능"""
        self.client.force_authenticate(user=self.user2)

        # 0.5 단위 테스트
        valid_ratings = [0.5, 1.0, 1.5]
        invalid_ratings = [0.3, 1.2]

        print(f"\n[TEST 5-1] 유효한 별점 테스트")
        for rating in valid_ratings:
            # 새로운 거래 생성
            trade = TradeRequest.objects.create(
                room=self.room,
                post=self.post,
                requester=self.user1,
                receiver=self.user2,
                proposed_price=10000,
                proposed_hours=5,
                status='completed'
            )

            response = self.client.post('/api/reviews/create/', {
                'trade': trade.id,
                'rating': rating,
                'content': f'{rating}점'
            })
            print(f"  별점 {rating}: {response.status_code}")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        print(f"\n[TEST 5-2] 유효하지 않은 별점 테스트")
        for rating in invalid_ratings:
            # 새로운 거래 생성
            trade = TradeRequest.objects.create(
                room=self.room,
                post=self.post,
                requester=self.user1,
                receiver=self.user2,
                proposed_price=10000,
                proposed_hours=5,
                status='completed'
            )

            response = self.client.post('/api/reviews/create/', {
                'trade': trade.id,
                'rating': rating,
                'content': f'{rating}점'
            })
            print(f"  별점 {rating}: {response.status_code}")
            print(f"  응답: {response.data}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

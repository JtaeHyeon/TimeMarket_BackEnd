"""
게시글별 채팅 기능 테스트
수정된 채팅 시스템이 게시글별로 올바르게 작동하는지 확인합니다.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from chat.models import Room, ChatMessage
from posts.models import TimePost

User = get_user_model()

class PostSpecificChatTest(TestCase):
    def setUp(self):
        """테스트 데이터 설정"""
        # 테스트 사용자 생성
        self.user1 = User.objects.create_user(
            email='user1@test.com',
            password='testpass123',
            nickname='사용자1'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@test.com',
            password='testpass123',
            nickname='사용자2'
        )
        
        # 테스트 게시글 2개 생성 (user1이 작성)
        self.post1 = TimePost.objects.create(
            user=self.user1,
            title='시간 판매 게시글 1',
            description='첫 번째 게시글입니다',
            type='sale',
            price=10000
        )
        
        self.post2 = TimePost.objects.create(
            user=self.user1,
            title='시간 판매 게시글 2', 
            description='두 번째 게시글입니다',
            type='sale',
            price=15000
        )
        
        self.client = APIClient()
    
    def test_different_posts_create_different_rooms(self):
        """서로 다른 게시글에 대해 서로 다른 채팅방이 생성되는지 테스트"""
        self.client.force_authenticate(user=self.user2)
        
        # 첫 번째 게시글에 대한 채팅방 생성
        response1 = self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        room1_data = response1.json()
        room1_id = room1_data['id']
        
        # 두 번째 게시글에 대한 채팅방 생성
        response2 = self.client.post('/api/chat/match/request/', {'post_id': self.post2.id})
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        room2_data = response2.json()
        room2_id = room2_data['id']
        
        # 두 채팅방이 서로 다른지 확인
        self.assertNotEqual(room1_id, room2_id, "서로 다른 게시글에 대해 같은 채팅방이 생성되었습니다")
        
        # 각 채팅방이 올바른 게시글과 연결되어 있는지 확인
        self.assertEqual(room1_data['post']['id'], self.post1.id)
        self.assertEqual(room2_data['post']['id'], self.post2.id)
        
        print(f"✅ 테스트 통과: 서로 다른 게시글에 대해 서로 다른 채팅방 생성됨")
        print(f"   - 게시글 {self.post1.id} → 채팅방 {room1_id}")
        print(f"   - 게시글 {self.post2.id} → 채팅방 {room2_id}")
    
    def test_same_post_returns_existing_room(self):
        """같은 게시글에 대한 중복 요청 시 기존 채팅방을 반환하는지 테스트"""
        self.client.force_authenticate(user=self.user2)
        
        # 첫 번째 요청으로 채팅방 생성
        response1 = self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        room1_id = response1.json()['id']
        
        # 같은 게시글에 대한 두 번째 요청
        response2 = self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)  # 기존 방 반환은 200
        room2_id = response2.json()['id']
        
        # 같은 채팅방이 반환되는지 확인
        self.assertEqual(room1_id, room2_id, "같은 게시글에 대해 새로운 채팅방이 생성되었습니다")
        
        print(f"✅ 테스트 통과: 같은 게시글에 대한 중복 요청 시 기존 채팅방 반환됨 (Room {room1_id})")
    
    def test_own_post_chat_blocked(self):
        """자신의 게시글에 채팅 시도 시 차단되는지 테스트"""
        self.client.force_authenticate(user=self.user1)  # 게시글 작성자로 인증
        
        # 자신의 게시글에 채팅 시도
        response = self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        error_data = response.json()
        self.assertIn('error', error_data)
        self.assertIn('자신의 게시글', error_data['error'])
        
        print(f"✅ 테스트 통과: 자신의 게시글에 채팅 시도 시 차단됨 - {error_data['error']}")
    
    def test_room_contains_correct_post_info(self):
        """생성된 채팅방이 올바른 게시글 정보를 포함하는지 테스트"""
        self.client.force_authenticate(user=self.user2)
        
        response = self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        room_data = response.json()
        post_data = room_data['post']
        
        # 게시글 정보가 올바르게 포함되어 있는지 확인
        self.assertEqual(post_data['id'], self.post1.id)
        self.assertEqual(post_data['title'], self.post1.title)
        self.assertEqual(post_data['description'], self.post1.description)
        self.assertEqual(post_data['type'], self.post1.type)
        self.assertEqual(post_data['price'], self.post1.price)
        
        # 참여자 정보 확인
        users = room_data['users']
        user_nicknames = [user['nickname'] for user in users]
        self.assertIn(self.user1.nickname, user_nicknames)
        self.assertIn(self.user2.nickname, user_nicknames)
        
        print(f"✅ 테스트 통과: 채팅방이 올바른 게시글 정보를 포함함")
        print(f"   - 게시글: {post_data['title']} (ID: {post_data['id']})")
        print(f"   - 참여자: {user_nicknames}")
    
    def test_database_room_structure(self):
        """데이터베이스에서 Room 객체가 올바르게 생성되는지 테스트"""
        self.client.force_authenticate(user=self.user2)
        
        # 두 개의 서로 다른 게시글에 대한 채팅방 생성
        self.client.post('/api/chat/match/request/', {'post_id': self.post1.id})
        self.client.post('/api/chat/match/request/', {'post_id': self.post2.id})
        
        # 데이터베이스에서 Room 객체 확인
        rooms = Room.objects.all()
        self.assertEqual(rooms.count(), 2, "예상과 다른 수의 채팅방이 생성되었습니다")
        
        # 각 채팅방이 올바른 게시글과 연결되어 있는지 확인
        post_ids = [room.post.id for room in rooms]
        self.assertIn(self.post1.id, post_ids)
        self.assertIn(self.post2.id, post_ids)
        
        # 각 채팅방에 올바른 사용자들이 참여하고 있는지 확인
        for room in rooms:
            users_in_room = list(room.users.all())
            self.assertEqual(len(users_in_room), 2)
            self.assertIn(self.user1, users_in_room)
            self.assertIn(self.user2, users_in_room)
        
        print(f"✅ 테스트 통과: 데이터베이스에서 Room 객체가 올바르게 생성됨")
        for room in rooms:
            users_in_room = [u.nickname for u in room.users.all()]
            print(f"   - Room {room.id}: 게시글 '{room.post.title}' (ID: {room.post.id})")
            print(f"     참여자: {users_in_room}")

#!/usr/bin/env python
"""
테스트용 사용자 계정 생성 스크립트
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TimeMarket_BackEnd.settings')
django.setup()

from django.contrib.auth import get_user_model
from posts.models import TimePost
from chat.models import Room

User = get_user_model()

def create_test_users():
    """테스트용 사용자 계정 생성"""
    
    # 기존 사용자 삭제 (있다면)
    User.objects.filter(nickname__in=['test', 'admin']).delete()
    
    # 사용자1 생성
    user1 = User.objects.create_user(
        nickname='test',
        email='test@gmail.com',
        password='test'
    )
    print(f"✅ 사용자1 생성: {user1.nickname} ({user1.email})")
    
    # 사용자2 생성
    user2 = User.objects.create_user(
        nickname='admin',
        email='admin@gmail.com',
        password='admin'
    )
    print(f"✅ 사용자2 생성: {user2.nickname} ({user2.email})")
    
    # 테스트용 게시글 생성
    post1 = TimePost.objects.create(
        user=user1,
        title='컴퓨터 수리 도움',
        description='컴퓨터 수리 도와드립니다. 시간당 10,000원',
        type='sale',
        price=10000,
        latitude=37.5665,
        longitude=126.9780
    )
    print(f"✅ 게시글1 생성: {post1.title} (ID: {post1.id})")
    
    post2 = TimePost.objects.create(
        user=user2,
        title='영어 과외 구함',
        description='영어 과외 선생님을 구합니다',
        type='request',
        price=20000,
        latitude=37.5665,
        longitude=126.9780
    )
    print(f"✅ 게시글2 생성: {post2.title} (ID: {post2.id})")
    
    # 테스트용 채팅방 생성
    room = Room.objects.create(post=post1)
    room.users.add(user1, user2)
    print(f"✅ 채팅방 생성: Room ID {room.id}")
    
    print("\n🎉 테스트 데이터 생성 완료!")
    print(f"📋 사용자1: {user1.nickname} / {user1.email} / test")
    print(f"📋 사용자2: {user2.nickname} / {user2.email} / admin")
    print(f"📋 게시글1 ID: {post1.id}")
    print(f"📋 게시글2 ID: {post2.id}")
    print(f"📋 채팅방 ID: {room.id}")

if __name__ == '__main__':
    create_test_users()

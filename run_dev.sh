#!/bin/bash

# TimeMarket 개발 서버 (Django runserver with WebSocket support)

echo "🚀 TimeMarket 개발 서버를 시작합니다... (자동 리로드)"

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
echo "📦 가상환경을 활성화합니다..."
source venv/bin/activate

# 마이그레이션 확인 및 적용
echo "🗄️  데이터베이스 마이그레이션을 확인합니다..."
python manage.py makemigrations
python manage.py migrate

echo "📍 WebSocket 지원이 활성화됩니다."
echo "🌐 서버 주소: http://localhost:8000"
echo "🔌 WebSocket 주소: ws://localhost:8000/ws/chat/{room_id}/"
echo "🔄 자동 리로드가 활성화되었습니다."
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo ""

# Django runserver (Channels가 설치되어 있으면 WebSocket도 지원)
python manage.py runserver 0.0.0.0:8000

#!/bin/bash

# TimeMarket ASGI 서버 실행 스크립트

echo "🚀 TimeMarket ASGI 서버를 시작합니다..."

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
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo ""

# Daphne로 ASGI 서버 실행
echo "⚠️  Daphne는 자동 리로드를 지원하지 않습니다."
echo "📝 코드 변경 시 수동으로 서버를 재시작해주세요."
daphne -b 0.0.0.0 -p 8000 TimeMarket_BackEnd.asgi:application

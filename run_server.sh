#!/bin/bash

# TimeMarket 백엔드 서버 실행 스크립트

echo "🚀 TimeMarket 백엔드 서버를 시작합니다..."

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
echo "📦 가상환경을 활성화합니다..."
source venv/bin/activate

# 마이그레이션 확인 및 적용
echo "🗄️  데이터베이스 마이그레이션을 확인합니다..."
python manage.py makemigrations
python manage.py migrate

# 개발 서버 실행
echo "🌐 개발 서버를 시작합니다..."
echo "   - 로컬 접속: http://127.0.0.1:8000/"
echo "   - 관리자 페이지: http://127.0.0.1:8000/admin/"
echo "   - 관리자 계정: 닉네임='관리자', 비밀번호='admin123!'"
echo ""
echo "서버를 중지하려면 Ctrl+C를 누르세요."
echo ""

python manage.py runserver

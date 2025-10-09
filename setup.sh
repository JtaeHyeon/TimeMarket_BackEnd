#!/bin/bash

# TimeMarket 백엔드 초기 설정 스크립트

echo "🔧 TimeMarket 백엔드 초기 설정을 시작합니다..."

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# Python 가상환경 생성
echo "📦 Python 가상환경을 생성합니다..."
python3 -m venv venv

# 가상환경 활성화
echo "📦 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치
echo "📚 의존성 패키지를 설치합니다..."
pip install -r requirements.txt

# 데이터베이스 마이그레이션
echo "🗄️  데이터베이스 마이그레이션을 실행합니다..."
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성
echo "👤 관리자 계정을 생성합니다..."
python create_superuser.py

echo ""
echo "✅ 초기 설정이 완료되었습니다!"
echo ""
echo "🚀 서버를 실행하려면 다음 명령어를 사용하세요:"
echo "   ./run_server.sh"
echo ""
echo "또는 수동으로 실행:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"

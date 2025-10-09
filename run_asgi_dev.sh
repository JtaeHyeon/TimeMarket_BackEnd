#!/bin/bash

# TimeMarket ASGI 개발 서버 (자동 리로드)

echo "🚀 TimeMarket ASGI 개발 서버를 시작합니다... (자동 리로드)"

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# 가상환경 활성화
echo "📦 가상환경을 활성화합니다..."
source venv/bin/activate

# watchdog 설치 확인
if ! python -c "import watchdog" 2>/dev/null; then
    echo "📦 watchdog를 설치합니다..."
    pip install watchdog
fi

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

# Python 스크립트로 자동 리로드 구현
python -c "
import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.restart_server()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.html', '.css', '.js')):
            print(f'🔄 파일 변경 감지: {event.src_path}')
            self.restart_server()
    
    def restart_server(self):
        if self.process:
            print('🛑 서버를 중지합니다...')
            self.process.terminate()
            self.process.wait()
        
        print('🚀 서버를 재시작합니다...')
        self.process = subprocess.Popen([
            'daphne', '-b', '0.0.0.0', '-p', '8000', 
            'TimeMarket_BackEnd.asgi:application'
        ])

if __name__ == '__main__':
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, '.', recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\\n🛑 서버를 종료합니다...')
        if event_handler.process:
            event_handler.process.terminate()
        observer.stop()
    observer.join()
"

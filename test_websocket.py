#!/usr/bin/env python
"""
WebSocket 거래 시스템 테스트 클라이언트
"""
import asyncio
import websockets
import json
import sys

async def test_websocket_trade():
    """WebSocket을 통한 거래 시스템 테스트"""
    
    # JWT 토큰 (실제 로그인에서 받은 토큰 사용)
    user1_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5OTk5NTUzLCJpYXQiOjE3NTk5OTU5NTMsImp0aSI6IjMwNzNhMTk5YmMzOTQ3ZTZiZTJjMjEwOGRiZjg0NGMyIiwidXNlcl9pZCI6IjQifQ.V44-LsajaKBdRamX0wLRMRtzbfCJe5M6vh5oKMK-R70"
    user2_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5OTk5NTYyLCJpYXQiOjE3NTk5OTU5NjIsImp0aSI6ImYxZGI0ZjZiMDQwMzRkZTdiZWZmOGQ2YmRmYTU0OTk2IiwidXNlcl9pZCI6IjUifQ.RlDgZlVU5nv6jJtPjzcSO95IDBeOiFXi7nDIkVBe-TA"
    
    room_id = 3
    
    try:
        print("🔌 WebSocket 연결 테스트 시작...")
        
        # 사용자1 WebSocket 연결
        uri1 = f"ws://localhost:8000/ws/chat/{room_id}/?token={user1_token}"
        print(f"📡 사용자1 연결 시도: {uri1}")
        
        async with websockets.connect(uri1) as websocket1:
            print("✅ 사용자1 WebSocket 연결 성공!")
            
            # 사용자2 WebSocket 연결
            uri2 = f"ws://localhost:8000/ws/chat/{room_id}/?token={user2_token}"
            print(f"📡 사용자2 연결 시도: {uri2}")
            
            async with websockets.connect(uri2) as websocket2:
                print("✅ 사용자2 WebSocket 연결 성공!")
                
                # 1. 사용자2가 거래 요청 전송
                trade_request = {
                    "type": "trade_request",
                    "proposed_price": 25000,
                    "proposed_hours": 4.0,
                    "message": "WebSocket을 통한 거래 요청입니다"
                }
                
                print("📤 사용자2가 거래 요청 전송...")
                await websocket2.send(json.dumps(trade_request))
                
                # 2. 양쪽에서 메시지 수신 대기
                print("📥 메시지 수신 대기...")
                
                # 사용자1이 거래 요청 수신
                response1 = await websocket1.recv()
                data1 = json.loads(response1)
                print(f"👤 사용자1 수신: {data1}")
                
                # 사용자2도 확인 메시지 수신
                response2 = await websocket2.recv()
                data2 = json.loads(response2)
                print(f"👤 사용자2 수신: {data2}")
                
                # 거래 요청 ID 추출
                if data1.get('type') == 'trade_request':
                    trade_request_id = data1['data']['id']
                    print(f"🆔 거래 요청 ID: {trade_request_id}")
                    
                    # 3. 사용자1이 거래 수락
                    trade_accept = {
                        "type": "trade_response",
                        "trade_request_id": trade_request_id,
                        "response": "accept",
                        "message": "거래를 수락합니다!"
                    }
                    
                    print("✅ 사용자1이 거래 수락...")
                    await websocket1.send(json.dumps(trade_accept))
                    
                    # 상태 업데이트 메시지 수신
                    update1 = await websocket1.recv()
                    update2 = await websocket2.recv()
                    
                    print(f"📊 상태 업데이트1: {json.loads(update1)}")
                    print(f"📊 상태 업데이트2: {json.loads(update2)}")
                    
                    # 4. 사용자2도 거래 수락 (거래 완료)
                    trade_accept2 = {
                        "type": "trade_response",
                        "trade_request_id": trade_request_id,
                        "response": "accept",
                        "message": "저도 수락합니다!"
                    }
                    
                    print("✅ 사용자2도 거래 수락...")
                    await websocket2.send(json.dumps(trade_accept2))
                    
                    # 최종 상태 업데이트 메시지 수신
                    final1 = await websocket1.recv()
                    final2 = await websocket2.recv()
                    
                    print(f"🎉 최종 상태1: {json.loads(final1)}")
                    print(f"🎉 최종 상태2: {json.loads(final2)}")
                    
                    final_data = json.loads(final1)
                    if final_data.get('is_completed'):
                        print("🎊 거래가 성공적으로 완료되었습니다!")
                    else:
                        print("⚠️ 거래가 아직 완료되지 않았습니다.")
                
                print("✨ WebSocket 거래 테스트 완료!")
                
    except Exception as e:
        print(f"❌ WebSocket 테스트 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 WebSocket 거래 시스템 테스트 시작")
    result = asyncio.run(test_websocket_trade())
    
    if result:
        print("✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 테스트 실패!")
        sys.exit(1)

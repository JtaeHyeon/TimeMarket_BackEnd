# 거래 시스템 프론트엔드 연동 가이드

## 📋 개요

TimeMarket 백엔드의 실시간 거래 시스템을 프론트엔드에서 구현하기 위한 가이드입니다.

## 🔌 WebSocket 연결

### 연결 정보
- **URL**: `ws://[서버주소]/ws/chat/{room_id}/?token={jwt_access_token}`
- **인증**: URL 파라미터로 JWT access token 전달
- **프로토콜**: WebSocket

### 연결 예시
```javascript
const roomId = 3;
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const wsUrl = `ws://localhost:8000/ws/chat/${roomId}/?token=${token}`;
const websocket = new WebSocket(wsUrl);

// 또는 HTTPS 환경에서는
const wsUrl = `wss://yourdomain.com/ws/chat/${roomId}/?token=${token}`;
```

## 📤 전송 메시지 형식

### 1. 채팅 메시지
```json
{
    "type": "chat",
    "message": "안녕하세요"
}
```

### 2. 거래 요청
```json
{
    "type": "trade_request",
    "proposed_price": 15000,
    "proposed_hours": 2.5,
    "message": "컴퓨터 수리 도움 요청드립니다"
}
```

### 3. 거래 응답 (수락/거절)
```json
{
    "type": "trade_response",
    "trade_request_id": 123,
    "response": "accept",
    "message": "좋습니다. 거래하겠습니다."
}
```

**response 값:**
- `"accept"`: 수락
- `"reject"`: 거절

## 📥 수신 메시지 형식

### 1. 채팅 메시지
```json
{
    "type": "chat_message",
    "data": {
        "id": 1,
        "sender": {
            "id": 4,
            "nickname": "test",
            "email": "test@gmail.com",
            "profile_image": null
        },
        "receiver": {
            "id": 5,
            "nickname": "admin",
            "email": "admin@gmail.com",
            "profile_image": null
        },
        "message": "안녕하세요",
        "timestamp": "2025-10-09T07:46:15.322411Z"
    }
}
```

### 2. 거래 요청 알림
```json
{
    "type": "trade_request",
    "data": {
        "id": 123,
        "room": 3,
        "post": {
            "id": 2,
            "title": "컴퓨터 수리 도움",
            "description": "컴퓨터 수리 도와드립니다",
            "type": "sale",
            "price": 10000,
            "user": {
                "id": 4,
                "nickname": "test",
                "email": "test@gmail.com"
            }
        },
        "requester": {
            "id": 5,
            "nickname": "admin",
            "email": "admin@gmail.com",
            "profile_image": null
        },
        "receiver": {
            "id": 4,
            "nickname": "test",
            "email": "test@gmail.com",
            "profile_image": null
        },
        "proposed_price": "15000.00",
        "proposed_hours": "2.50",
        "message": "컴퓨터 수리 도움 요청드립니다",
        "status": "pending",
        "requester_accepted": false,
        "receiver_accepted": false,
        "created_at": "2025-10-09T07:46:15.322411Z",
        "updated_at": "2025-10-09T07:46:15.322438Z"
    }
}
```

### 3. 거래 상태 업데이트
```json
{
    "type": "trade_status_update",
    "data": {
        "id": 123,
        "room": 3,
        "post": {
            "id": 2,
            "title": "컴퓨터 수리 도움",
            "description": "컴퓨터 수리 도와드립니다. 시간당 10,000원",
            "type": "sale",
            "latitude": 37.5665,
            "longitude": 126.978,
            "created_at": "2025-10-09T07:44:58.638161Z",
            "price": 10000,
            "user": {
                "id": 4,
                "nickname": "test",
                "email": "test@gmail.com",
                "profile_image": null
            }
        },
        "requester": {
            "id": 5,
            "nickname": "admin",
            "email": "admin@gmail.com",
            "profile_image": null
        },
        "receiver": {
            "id": 4,
            "nickname": "test",
            "email": "test@gmail.com",
            "profile_image": null
        },
        "proposed_price": "15000.00",
        "proposed_hours": "2.50",
        "message": "컴퓨터 수리 도움 요청드립니다",
        "status": "completed",
        "requester_accepted": true,
        "receiver_accepted": true,
        "created_at": "2025-10-09T07:46:15.322411Z",
        "updated_at": "2025-10-09T07:46:47.440377Z"
    },
    "is_completed": true
}
```

**status 값:**
- `"pending"`: 대기중 (기본값)
- `"rejected"`: 거절됨 (한쪽이라도 거절시)
- `"completed"`: 완료됨 (양쪽 모두 수락시)
- `"cancelled"`: 취소됨

### 4. 에러 메시지
```json
{
    "type": "error",
    "message": "거래 요청 처리 중 오류가 발생했습니다"
}
```

## 🌐 REST API 엔드포인트

### 1. 거래 요청 목록 조회
```http
GET /api/chat/match/chat/{room_id}/trades/
Authorization: Bearer {jwt_token}
```

**응답 예시:**
```json
[
    {
        "id": 1,
        "room": 3,
        "post": {
            "id": 2,
            "title": "컴퓨터 수리 도움",
            "description": "컴퓨터 수리 도와드립니다. 시간당 10,000원",
            "type": "sale",
            "latitude": 37.5665,
            "longitude": 126.978,
            "created_at": "2025-10-09T07:44:58.638161Z",
            "price": 10000,
            "user": {
                "id": 4,
                "nickname": "test",
                "email": "test@gmail.com",
                "profile_image": null
            }
        },
        "requester": {
            "id": 5,
            "nickname": "admin",
            "email": "admin@gmail.com",
            "profile_image": null
        },
        "receiver": {
            "id": 4,
            "nickname": "test",
            "email": "test@gmail.com",
            "profile_image": null
        },
        "proposed_price": "15000.00",
        "proposed_hours": "2.50",
        "message": "컴퓨터 수리 도움 요청드립니다",
        "status": "pending",
        "requester_accepted": false,
        "receiver_accepted": false,
        "created_at": "2025-10-09T07:46:15.322411Z",
        "updated_at": "2025-10-09T07:46:15.322438Z"
    }
]
```

### 2. 거래 요청 생성
```http
POST /api/chat/match/chat/{room_id}/trades/create/
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
    "proposed_price": 15000,
    "proposed_hours": 2.5,
    "message": "도움 요청드립니다"
}
```

### 3. 거래 요청 상세 조회/수정
```http
GET /api/chat/match/trades/{trade_id}/
PATCH /api/chat/match/trades/{trade_id}/
Authorization: Bearer {jwt_token}
```

**PATCH 요청 예시:**
```json
{
    "requester_accepted": true
}
```
또는
```json
{
    "receiver_accepted": false
}
```

## 🔄 거래 플로우

### 1. 거래 요청 과정
1. **사용자A**가 `trade_request` 메시지 전송
2. **사용자A, B** 모두 `trade_request` 타입 메시지 수신
3. 거래 요청이 채팅창에 표시됨

### 2. 거래 응답 과정
1. **사용자B**가 `trade_response` 메시지 전송 (`"accept"` 또는 `"reject"`)
2. **사용자A, B** 모두 `trade_status_update` 타입 메시지 수신
3. 거래 상태가 업데이트됨

### 3. 거래 완료 조건
- **양쪽 모두 수락**: `requester_accepted: true` && `receiver_accepted: true`
- **한쪽이라도 거절**: 즉시 `status: "rejected"`로 변경

## 💡 구현 팁

### 1. WebSocket 연결 관리
```javascript
class TradeWebSocket {
    constructor(roomId, token) {
        this.roomId = roomId;
        this.token = token;
        this.ws = null;
        this.messageHandlers = new Map();
    }

    connect() {
        const wsUrl = `ws://localhost:8000/ws/chat/${this.roomId}/?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const handler = this.messageHandlers.get(data.type);
            if (handler) handler(data);
        };
    }

    on(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }

    sendTradeRequest(price, hours, message) {
        this.ws.send(JSON.stringify({
            type: 'trade_request',
            proposed_price: price,
            proposed_hours: hours,
            message: message
        }));
    }

    sendTradeResponse(tradeId, response) {
        this.ws.send(JSON.stringify({
            type: 'trade_response',
            trade_request_id: tradeId,
            response: response
        }));
    }
}
```

### 2. 상태 관리
```javascript
// React 예시
const [tradeRequests, setTradeRequests] = useState([]);
const [messages, setMessages] = useState([]);

// 거래 요청 수신 시
ws.on('trade_request', (data) => {
    setTradeRequests(prev => [...prev, data.data]);
    setMessages(prev => [...prev, {
        type: 'trade_request',
        data: data.data
    }]);
});

// 거래 상태 업데이트 시
ws.on('trade_status_update', (data) => {
    setTradeRequests(prev => 
        prev.map(req => 
            req.id === data.data.id 
                ? { ...req, ...data.data }
                : req
        )
    );
});
```

### 3. UI 컴포넌트 구조
```
ChatRoom
├── MessageList
│   ├── ChatMessage
│   └── TradeRequestMessage
├── TradeRequestForm
└── MessageInput
```

## 🚨 주의사항

1. **토큰 만료**: JWT 토큰이 만료되면 WebSocket 연결이 끊어집니다.
2. **권한 확인**: 채팅방에 참여하지 않은 사용자는 거래 요청을 생성할 수 없습니다.
3. **중복 요청**: 동일한 거래 요청에 대해 여러 번 응답하지 않도록 UI에서 제어해야 합니다.
4. **연결 재시도**: WebSocket 연결이 끊어졌을 때 자동 재연결 로직을 구현하세요.
5. **ASGI 서버**: WebSocket 기능을 사용하려면 ASGI 서버(Daphne, Uvicorn 등)가 필요합니다.
6. **데이터 타입**: 
   - `proposed_price`와 `proposed_hours`는 숫자로 전송하지만 문자열로 수신됩니다.
   - `room` 필드는 정수 ID입니다.
7. **상태 변경**: 거래 상태는 서버에서 자동으로 관리되며, 클라이언트에서 직접 변경할 수 없습니다.

## 📞 문의사항

구현 중 문제가 발생하거나 추가 기능이 필요한 경우 백엔드 팀에 문의해주세요.

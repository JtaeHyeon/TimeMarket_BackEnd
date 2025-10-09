# 거래 목록 API 가이드

## 📋 API 개요

특정 채팅방의 거래 요청 목록을 조회하는 API입니다.

### 기본 정보
- **엔드포인트**: `GET /api/chat/match/chat/{room_id}/trades/`
- **인증**: JWT Bearer Token 필수
- **권한**: 해당 채팅방에 참여한 사용자만 접근 가능

---

## 🔗 요청 방법

### HTTP 요청
```http
GET /api/chat/match/chat/3/trades/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### JavaScript 예시
```javascript
const getRoomTrades = async (roomId) => {
  try {
    const response = await fetch(`/api/chat/match/chat/${roomId}/trades/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const trades = await response.json();
    return trades;
  } catch (error) {
    console.error('거래 목록 조회 실패:', error);
    throw error;
  }
};
```

---

## 📤 응답 형식

### 성공 응답 (200 OK)
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
    "updated_at": "2025-10-09T07:46:15.322411Z"
  },
  {
    "id": 2,
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
    "proposed_price": "12000.00",
    "proposed_hours": "1.00",
    "message": "1시간만 도와주세요",
    "status": "completed",
    "requester_accepted": true,
    "receiver_accepted": true,
    "created_at": "2025-10-09T06:30:10.123456Z",
    "updated_at": "2025-10-09T06:45:22.654321Z"
  }
]
```

### 에러 응답

#### 401 Unauthorized - 인증 실패
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden - 권한 없음
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 404 Not Found - 채팅방 없음
```json
{
  "detail": "Not found."
}
```

---

## 📊 응답 데이터 구조

### TradeRequest 객체
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | integer | 거래 요청 고유 ID |
| `room` | integer | 채팅방 ID |
| `post` | object | 관련 게시글 정보 |
| `requester` | object | 거래 요청자 정보 |
| `receiver` | object | 거래 수신자 정보 |
| `proposed_price` | string | 제안 가격 (Decimal) |
| `proposed_hours` | string | 제안 시간 (Decimal) |
| `message` | string/null | 거래 요청 메시지 (선택사항) |
| `status` | string | 거래 상태 |
| `requester_accepted` | boolean | 요청자 수락 여부 |
| `receiver_accepted` | boolean | 수신자 수락 여부 |
| `created_at` | string | 생성일시 (ISO 8601) |
| `updated_at` | string | 수정일시 (ISO 8601) |

### Post 객체 (SimpleTimePostSerializer)
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | integer | 게시글 ID |
| `title` | string | 게시글 제목 |
| `description` | string | 게시글 내용 |
| `type` | string | 게시글 타입 ("sale" 또는 "request") |
| `latitude` | float | 위도 |
| `longitude` | float | 경도 |
| `created_at` | string | 생성일시 |
| `price` | integer | 시간당 가격 |
| `user` | object | 게시글 작성자 정보 |

### User 객체 (UserSerializer)
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | integer | 사용자 ID |
| `nickname` | string | 닉네임 |
| `email` | string | 이메일 |
| `profile_image` | string/null | 프로필 이미지 절대 URL (없으면 null) |

---

## 🔄 거래 상태 (Status)

| 상태값 | 한글명 | 설명 |
|--------|--------|------|
| `pending` | 대기중 | 기본 상태, 아직 처리되지 않음 |
| `accepted` | 수락됨 | 한쪽이 수락한 상태 |
| `rejected` | 거절됨 | 한쪽이라도 거절한 상태 |
| `completed` | 완료됨 | 양쪽 모두 수락하여 거래 성사 |
| `cancelled` | 취소됨 | 거래가 취소된 상태 |

---

## 💡 프론트엔드 구현 팁

### 1. 거래 상태별 UI 처리
```javascript
const getStatusDisplay = (trade) => {
  const statusMap = {
    'pending': { text: '대기중', color: '#FFA500', icon: '⏳' },
    'accepted': { text: '수락됨', color: '#32CD32', icon: '✅' },
    'rejected': { text: '거절됨', color: '#FF6B6B', icon: '❌' },
    'completed': { text: '완료됨', color: '#4CAF50', icon: '🎉' },
    'cancelled': { text: '취소됨', color: '#9E9E9E', icon: '🚫' }
  };
  
  return statusMap[trade.status] || statusMap['pending'];
};
```

### 2. 거래 목록 정렬 및 필터링
```javascript
const processTrades = (trades) => {
  // 최신순 정렬 (API에서 이미 정렬되어 오지만 확실히)
  const sortedTrades = trades.sort((a, b) => 
    new Date(b.created_at) - new Date(a.created_at)
  );
  
  // 상태별 분류
  const groupedTrades = {
    pending: sortedTrades.filter(t => t.status === 'pending'),
    completed: sortedTrades.filter(t => t.status === 'completed'),
    others: sortedTrades.filter(t => !['pending', 'completed'].includes(t.status))
  };
  
  return groupedTrades;
};
```

### 3. 가격 및 시간 포맷팅
```javascript
const formatPrice = (price) => {
  return new Intl.NumberFormat('ko-KR').format(price) + '원';
};

const formatHours = (hours) => {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return m > 0 ? `${h}시간 ${m}분` : `${h}시간`;
};
```

### 4. 에러 처리
```javascript
const handleApiError = (error, response) => {
  if (response?.status === 401) {
    // 토큰 만료 - 로그인 페이지로 리다이렉트
    localStorage.removeItem('access_token');
    window.location.href = '/login';
  } else if (response?.status === 403) {
    alert('해당 채팅방에 접근할 권한이 없습니다.');
  } else if (response?.status === 404) {
    alert('채팅방을 찾을 수 없습니다.');
  } else {
    alert('거래 목록을 불러오는 중 오류가 발생했습니다.');
  }
};
```

---

## 🔄 실시간 업데이트

거래 상태가 변경될 때는 WebSocket을 통해 실시간으로 업데이트됩니다. 
WebSocket 메시지 타입 `trade_status_update`를 수신하여 목록을 갱신하세요.

```javascript
// WebSocket 메시지 처리 예시
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'trade_status_update') {
    // 거래 목록 다시 조회 또는 해당 항목만 업데이트
    updateTradeInList(data.data);
  }
};
```

---

## 📝 주의사항

1. **권한 확인**: 해당 채팅방에 참여한 사용자만 거래 목록을 조회할 수 있습니다.
2. **정렬**: 거래 요청은 생성일시 역순으로 정렬되어 반환됩니다.
3. **실시간성**: 목록 조회는 현재 시점의 스냅샷이므로, 실시간 업데이트는 WebSocket을 활용하세요.
4. **토큰 관리**: JWT 토큰 만료 시 적절한 에러 처리를 구현하세요.

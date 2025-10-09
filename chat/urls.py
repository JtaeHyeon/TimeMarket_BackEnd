from django.urls import path
from . import views

urlpatterns = [
    # 채팅 관련
    path('match/request/', views.MatchRequestView.as_view(), name='match-request'), #채팅방 생성
    path('match/my-chats/', views.MyChatsView.as_view(), name='my-chats'), #내 채팅방 목록
    path('match/chat/<int:room_id>/', views.ChatRoomDetailView.as_view(), name='chat-room-detail'), #채팅방 상세
    path('match/chat/<int:room_id>/messages/', views.ChatMessageListCreateView.as_view(), name='chat-messages'), #채팅 메시지 목록(읽기 전용)
    
    # 거래 관련
    path('match/chat/<int:room_id>/trades/', views.TradeRequestListView.as_view(), name='trade-list'), #거래 요청 목록
    path('match/chat/<int:room_id>/trades/create/', views.TradeRequestCreateView.as_view(), name='trade-create'), #거래 요청 생성
    path('match/trades/<int:trade_id>/', views.TradeRequestDetailView.as_view(), name='trade-detail'), #거래 요청 상세/수정
]

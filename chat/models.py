from django.db import models
from posts.models import TimePost
from users.models import User

class Room(models.Model):
    post = models.ForeignKey(TimePost, on_delete=models.CASCADE, null=True, blank=True, related_name="rooms")
    users = models.ManyToManyField(User, related_name="chat_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.id}"


class ChatMessage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.message[:20]}"


class TradeRequest(models.Model):
    TRADE_STATUS_CHOICES = [
        ('pending', '대기중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
        ('completed', '완료됨'),
        ('cancelled', '취소됨'),
    ]
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='trade_requests')
    post = models.ForeignKey(TimePost, on_delete=models.CASCADE)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_trade_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_trade_requests')
    
    # 거래 조건
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    proposed_hours = models.DecimalField(max_digits=5, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    
    # 상태 관리
    status = models.CharField(max_length=20, choices=TRADE_STATUS_CHOICES, default='pending')
    requester_accepted = models.BooleanField(default=False)
    receiver_accepted = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"거래요청 {self.id}: {self.requester} -> {self.receiver}"

    def check_completion(self):
        """양쪽 모두 수락했는지 확인하고 상태 업데이트"""
        if self.requester_accepted and self.receiver_accepted and self.status == 'pending':
            self.status = 'completed'
            self.save()
            return True
        return False


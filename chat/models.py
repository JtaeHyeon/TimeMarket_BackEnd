from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from posts.models import TimePost
from users.models import User
import logging

logger = logging.getLogger(__name__)


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
    proposed_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[
            MinValueValidator(0.01, message="제안 가격은 0.01원 이상이어야 합니다."),
            MaxValueValidator(99999999.99, message="제안 가격은 99,999,999.99원을 초과할 수 없습니다.")
        ]
    )
    proposed_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[
            MinValueValidator(0.01, message="제안 시간은 0.01시간 이상이어야 합니다."),
            MaxValueValidator(999.99, message="제안 시간은 999.99시간을 초과할 수 없습니다.")
        ]
    )
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
    
    def process_trade(self):
        """
        거래 처리 메서드 - 양쪽 모두 수락했을 때 실제 거래 실행
        Returns: True if successful, raises ValidationError otherwise
        """
        from wallet.models import Wallet, Transaction
        
        # ✅ 이미 처리된 거래는 재처리하지 않음
        if self.status in ['completed', 'rejected', 'cancelled']:
            logger.warning(f"[거래 처리 거부] Trade #{self.id} - 이미 처리된 거래 (상태: {self.status})")
            raise ValidationError(f"이미 처리된 거래입니다 (상태: {self.get_status_display()})")
        
        # 양쪽 모두 수락했는지 확인
        if not (self.requester_accepted and self.receiver_accepted):
            raise ValidationError("양쪽 모두 수락해야 거래를 진행할 수 있습니다.")
        
        logger.info(f"[거래 처리 시작] Trade #{self.id}")
        
        post = self.post
        requester = self.requester
        proposed_hours = self.proposed_hours
        
        logger.info(f"  - 게시글 타입: {post.type} ({post.get_type_display()})")
        logger.info(f"  - 게시글 작성자: {post.user.nickname}")
        logger.info(f"  - 거래 요청자: {requester.nickname}")
        logger.info(f"  - 거래 시간: {proposed_hours}시간")
        
        # ✅ 게시글 타입에 따라 역할 구분 및 검증
        if post.type == 'sale':
            # 판매 글: 게시글 작성자가 판매자, 거래 요청자가 구매자
            seller = post.user
            buyer = requester
            
            if buyer.id == seller.id:
                logger.error(f"  - ❌ 검증 실패: 자신의 판매글은 구매할 수 없음")
                self.status = 'rejected'
                self.save()
                raise ValidationError("자신의 판매글은 구매할 수 없습니다.")
            
            payer = buyer      # 구매자가 지불
            payee = seller     # 판매자가 받음
            
            logger.info(f"  - [판매 타입] 구매자({payer.nickname})가 판매자({payee.nickname})에게 {proposed_hours}시간 지불")
            
        elif post.type == 'request':
            # 구인 글: 게시글 작성자가 구인자(고용주), 거래 요청자가 지원자(일꾼)
            employer = post.user
            worker = requester
            
            if worker.id == employer.id:
                logger.error(f"  - ❌ 검증 실패: 자신의 구인글에는 지원할 수 없음")
                self.status = 'rejected'
                self.save()
                raise ValidationError("자신의 구인글에는 지원할 수 없습니다.")
            
            payer = employer   # 구인자가 지불
            payee = worker     # 지원자가 받음
            
            logger.info(f"  - [구인 타입] 구인자({payer.nickname})가 지원자({payee.nickname})에게 {proposed_hours}시간 지불")
            
        else:
            logger.error(f"  - ❌ 알 수 없는 게시글 타입: {post.type}")
            self.status = 'rejected'
            self.save()
            raise ValidationError(f"알 수 없는 게시글 타입: {post.type}")
        
        # 🔒 트랜잭션으로 거래 처리
        try:
            with transaction.atomic():
                # 지갑 조회 또는 생성 후 락 걸기
                payer_wallet, _ = Wallet.objects.get_or_create(user=payer)
                payee_wallet, _ = Wallet.objects.get_or_create(user=payee)
                
                # 락을 걸어서 다시 조회
                payer_wallet = Wallet.objects.select_for_update().get(id=payer_wallet.id)
                payee_wallet = Wallet.objects.select_for_update().get(id=payee_wallet.id)
                
                logger.info(f"  - 거래 전 잔액:")
                logger.info(f"    * {payer.nickname} (지불자): {payer_wallet.balance}시간")
                logger.info(f"    * {payee.nickname} (수령자): {payee_wallet.balance}시간")
                
                # ✅ 잔액 확인
                if payer_wallet.balance < proposed_hours:
                    logger.warning(f"  - ❌ 잔액 부족!")
                    logger.warning(f"    * {payer.nickname}님의 잔액: {payer_wallet.balance}시간")
                    logger.warning(f"    * 필요 금액: {proposed_hours}시간")
                    
                    self.status = 'rejected'
                    self.save()
                    
                    raise ValidationError(
                        f"{payer.nickname}님의 잔액이 부족하여 거래가 거절되었습니다. "
                        f"필요: {proposed_hours}시간, 현재 잔액: {payer_wallet.balance}시간"
                    )
                
                logger.info(f"  - ✅ 잔액 충분! 거래 실행 중...")
                
                # 💰 거래 실행
                payer_wallet.balance -= proposed_hours
                payee_wallet.balance += proposed_hours
                
                payer_wallet.save()
                payee_wallet.save()
                
                logger.info(f"  - 거래 후 잔액:")
                logger.info(f"    * {payer.nickname}: {payer_wallet.balance}시간 (변경: -{proposed_hours})")
                logger.info(f"    * {payee.nickname}: {payee_wallet.balance}시간 (변경: +{proposed_hours})")
                
                # 📝 거래 내역 기록
                transaction_note_payer = (
                    f"[{post.get_type_display()}] 거래 #{self.id}: "
                    f"{payee.nickname}님에게 {proposed_hours}시간 지불 (게시글: {post.title})"
                )
                transaction_note_payee = (
                    f"[{post.get_type_display()}] 거래 #{self.id}: "
                    f"{payer.nickname}님으로부터 {proposed_hours}시간 받음 (게시글: {post.title})"
                )
                
                Transaction.objects.create(
                    wallet=payer_wallet,
                    transaction_type='withdraw',
                    amount=proposed_hours,
                    note=transaction_note_payer
                )
                
                Transaction.objects.create(
                    wallet=payee_wallet,
                    transaction_type='deposit',
                    amount=proposed_hours,
                    note=transaction_note_payee
                )
                
                logger.info(f"  - 거래 내역 기록 완료")
                
                # ✅ 거래 완료 상태로 변경
                self.status = 'completed'
                self.save()
                
                logger.info(f"[거래 완료] Trade #{self.id} ✅")
                logger.info(f"  - 거래 타입: {post.get_type_display()}")
                logger.info(f"  - {payer.nickname} → {payee.nickname}: {proposed_hours}시간")
                
                return True
                
        except ValidationError:
            # ValidationError는 그대로 전달
            raise
        except Exception as e:
            # 기타 오류 처리
            logger.error(f"  - ❌ 거래 처리 실패: {str(e)}", exc_info=True)
            self.refresh_from_db()
            if self.status not in ['rejected', 'completed']:
                self.status = 'rejected'
                self.save()
            raise ValidationError(f"거래 처리 중 오류가 발생했습니다: {str(e)}")


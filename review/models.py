from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
from users.models import User
from chat.models import TradeRequest


class Review(models.Model):
    trade = models.ForeignKey(TradeRequest, on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='written_reviews')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal('0.5')),
            MaxValueValidator(Decimal('5.0')),
        ]
    )
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (('trade', 'author'),)
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.id} - {self.author} -> {self.target} : {self.rating}"

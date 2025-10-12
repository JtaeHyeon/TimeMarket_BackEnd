# users/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=30, unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'nickname'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.email

    @property
    def average_rating(self):
        """받은 리뷰의 평균 평점을 실시간으로 계산합니다."""
        try:
            from django.apps import apps
            Review = apps.get_model('review', 'Review')
            reviews = Review.objects.filter(target=self)
            count = reviews.count()
            if count == 0:
                return 0.00

            from decimal import Decimal
            total = Decimal('0')
            for r in reviews:
                total += Decimal(str(r.rating))
            avg = (total / count).quantize(Decimal('0.01'))
            return float(avg)
        except Exception:
            return 0.00

    @property
    def rating_count(self):
        """받은 리뷰의 개수를 실시간으로 계산합니다."""
        try:
            from django.apps import apps
            Review = apps.get_model('review', 'Review')
            return Review.objects.filter(target=self).count()
        except Exception:
            return 0

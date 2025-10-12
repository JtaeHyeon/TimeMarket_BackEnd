from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'trade', 'author', 'target', 'rating', 'created_at')
    search_fields = ('author__nickname', 'target__nickname', 'trade__id')
    list_filter = ('rating', 'created_at')
    readonly_fields = ('created_at',)


from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'amount', 'category', 'user', 'is_flagged')
    list_filter = ('category', 'is_flagged', 'is_recurring', 'date')
    search_fields = ('description', 'merchant', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('id', 'created_at', 'updated_at')

from django.contrib import admin
from .models import CreditCardStatement


@admin.register(CreditCardStatement)
class CreditCardStatementAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_name', 'status', 'transaction_count', 'uploaded_at')
    list_filter = ('status', 'bank_name', 'uploaded_at')
    search_fields = ('user__email', 'original_filename')
    readonly_fields = ('id', 'uploaded_at', 'processed_at')

from django.contrib import admin
from .models import Account, AccountBalanceSnapshot


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'user',
        'account_type',
        'institution',
        'last_four',
        'is_active',
        'created_at',
    ]
    list_filter = ['account_type', 'institution', 'is_active', 'created_at']
    search_fields = ['name', 'institution', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'name', 'account_type')
        }),
        ('Details', {
            'fields': ('institution', 'last_four', 'color')
        }),
        ('Balance', {
            'fields': ('initial_balance', 'credit_limit')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(AccountBalanceSnapshot)
class AccountBalanceSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'account',
        'balance',
        'as_of_date',
        'source',
        'created_at',
    ]
    list_filter = ['source', 'as_of_date', 'created_at']
    search_fields = ['account__name', 'account__user__email', 'notes']
    ordering = ['-as_of_date', '-created_at']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['account', 'statement']

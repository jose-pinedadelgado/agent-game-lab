from django.contrib import admin
from .models import BudgetCategory, SpendingAlert


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'monthly_limit', 'color', 'is_active')
    list_filter = ('is_active', 'user')
    search_fields = ('name', 'user__email')


@admin.register(SpendingAlert)
class SpendingAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'user', 'category', 'is_read', 'created_at')
    list_filter = ('alert_type', 'is_read', 'is_dismissed')
    search_fields = ('message', 'user__email')

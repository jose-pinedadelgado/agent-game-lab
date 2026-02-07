from django.contrib import admin
from .models import CategoryAssignment


@admin.register(CategoryAssignment)
class CategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_description',
        'category_name',
        'source',
        'ai_confidence',
        'user',
        'created_at',
    ]
    list_filter = ['source', 'category_name', 'created_at']
    search_fields = ['transaction_description', 'transaction_merchant', 'category_name']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

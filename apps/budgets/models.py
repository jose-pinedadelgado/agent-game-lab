import uuid
from django.db import models
from django.conf import settings


class BudgetCategory(models.Model):
    """Spending category with monthly budget limit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, default='#3B82F6')
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'name']
        verbose_name_plural = 'Budget Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (${self.monthly_limit})"

    @classmethod
    def create_defaults_for_user(cls, user):
        """Create default categories for a new user."""
        defaults = [
            {'name': 'Groceries', 'monthly_limit': 500, 'color': '#10B981'},
            {'name': 'Dining', 'monthly_limit': 300, 'color': '#F59E0B'},
            {'name': 'Transportation', 'monthly_limit': 200, 'color': '#3B82F6'},
            {'name': 'Entertainment', 'monthly_limit': 150, 'color': '#8B5CF6'},
            {'name': 'Shopping', 'monthly_limit': 250, 'color': '#EC4899'},
            {'name': 'Utilities', 'monthly_limit': 200, 'color': '#6B7280'},
            {'name': 'Other', 'monthly_limit': 500, 'color': '#9CA3AF'},
        ]
        for default in defaults:
            cls.objects.get_or_create(user=user, name=default['name'], defaults=default)


class SpendingAlert(models.Model):
    """Notification for spending events."""

    class AlertType(models.TextChoices):
        APPROACHING = 'approaching', 'Approaching Limit'
        OVER_BUDGET = 'over_budget', 'Over Budget'
        LARGE_TRANSACTION = 'large_transaction', 'Large Transaction'
        UNUSUAL = 'unusual', 'Unusual Spending'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    message = models.TextField()
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.created_at.strftime('%Y-%m-%d')}"

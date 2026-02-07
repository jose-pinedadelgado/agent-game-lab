import uuid
from django.db import models
from django.conf import settings


class Transaction(models.Model):
    """Represents a single credit card transaction."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    statement = models.ForeignKey(
        'statements.CreditCardStatement',
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True
    )
    category = models.ForeignKey(
        'budgets.BudgetCategory',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )

    # Core fields
    date = models.DateField(db_index=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    transaction_number = models.CharField(max_length=32, blank=True)

    # AI fields
    ai_category_suggestion = models.CharField(max_length=100, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    user_confirmed = models.BooleanField(default=False)

    # User fields
    is_recurring = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'merchant']),
        ]

    def __str__(self):
        return f"{self.date} - {self.description[:30]} - ${self.amount}"

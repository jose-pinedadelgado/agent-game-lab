import uuid
from django.db import models
from django.conf import settings


class CategoryAssignment(models.Model):
    """Records every category assignment for future model training."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.CASCADE,
        related_name='category_assignments'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # What was assigned
    category_name = models.CharField(max_length=100)  # Denormalized for training export
    category = models.ForeignKey(
        'budgets.BudgetCategory',
        on_delete=models.SET_NULL,
        null=True
    )

    # Source of assignment
    class Source(models.TextChoices):
        AI_PREDICTION = 'ai', 'AI Prediction'
        USER_CORRECTION = 'user', 'User Correction'
        USER_INITIAL = 'user_initial', 'User Initial Selection'

    source = models.CharField(max_length=20, choices=Source.choices)

    # AI metadata (if AI-assigned)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_model_version = models.CharField(max_length=50, blank=True)

    # Transaction context for training (denormalized)
    transaction_description = models.CharField(max_length=255)
    transaction_merchant = models.CharField(max_length=255, blank=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'category_name']),
            models.Index(fields=['transaction_description']),
        ]

    def __str__(self):
        return f"{self.transaction_description[:30]} -> {self.category_name} ({self.source})"

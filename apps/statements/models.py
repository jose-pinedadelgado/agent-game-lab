import uuid
from django.db import models
from django.conf import settings


class CreditCardStatement(models.Model):
    """Represents an uploaded credit card statement PDF."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    class Bank(models.TextChoices):
        AMEX = 'amex', 'American Express'
        CHASE = 'chase', 'Chase'
        WELLS_FARGO = 'wells_fargo', 'Wells Fargo'
        BOA = 'boa', 'Bank of America'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    statement_file = models.FileField(upload_to='statements/%Y/%m/')
    original_filename = models.CharField(max_length=255, blank=True)
    bank_name = models.CharField(max_length=20, choices=Bank.choices, default=Bank.OTHER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    transaction_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_bank_name_display()} - {self.uploaded_at.strftime('%Y-%m-%d')}"

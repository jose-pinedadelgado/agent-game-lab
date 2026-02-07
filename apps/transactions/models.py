import uuid
from django.db import models
from django.conf import settings

from apps.budgets.models import SpendingType, CSPBucket


class TransactionType(models.TextChoices):
    """Type of transaction for balance calculations."""
    PURCHASE = 'purchase', 'Purchase'
    PAYMENT = 'payment', 'Payment'
    TRANSFER = 'transfer', 'Transfer'
    REFUND = 'refund', 'Refund'
    DEPOSIT = 'deposit', 'Deposit'
    WITHDRAWAL = 'withdrawal', 'Withdrawal'
    FEE = 'fee', 'Fee'
    INTEREST = 'interest', 'Interest'


class TransactionStatus(models.TextChoices):
    """Status of a transaction (pending, posted, cleared)."""
    PENDING = 'pending', 'Pending'
    POSTED = 'posted', 'Posted'
    CLEARED = 'cleared', 'Cleared'


class Transaction(models.Model):
    """Represents a single financial transaction."""

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

    # Account link
    account = models.ForeignKey(
        'accounts_financial.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    # Transaction type and status
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.PURCHASE
    )
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.POSTED
    )

    # Transfer linking (self-referential for transfer pairs)
    transfer_pair = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_transfer'
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

    # Secondary categorization overrides (override category defaults)
    spending_type_override = models.CharField(
        max_length=10,
        choices=SpendingType.choices,
        null=True,
        blank=True,
        help_text="Override the category's default spending type"
    )
    csp_bucket_override = models.CharField(
        max_length=15,
        choices=CSPBucket.choices,
        null=True,
        blank=True,
        help_text="Override the category's default CSP bucket"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'merchant']),
            models.Index(fields=['account', 'date']),
            models.Index(fields=['account', 'status']),
        ]

    def __str__(self):
        return f"{self.date} - {self.description[:30]} - ${self.amount}"

    @property
    def is_pending(self):
        """Returns True if transaction is pending."""
        return self.status == TransactionStatus.PENDING

    @property
    def is_transfer(self):
        """Returns True if this is a transfer transaction."""
        return self.transaction_type == TransactionType.TRANSFER or self.transfer_pair is not None

    @property
    def spending_type(self):
        """Return override if set, otherwise category default."""
        if self.spending_type_override:
            return self.spending_type_override
        if self.category and self.category.default_spending_type:
            return self.category.default_spending_type
        return None

    @property
    def csp_bucket(self):
        """Return override if set, otherwise category default."""
        if self.csp_bucket_override:
            return self.csp_bucket_override
        if self.category and self.category.default_csp_bucket:
            return self.category.default_csp_bucket
        return None

    def get_spending_type_display_effective(self):
        """Get display label for effective spending type."""
        value = self.spending_type
        if value:
            return SpendingType(value).label
        return None

    def get_csp_bucket_display_effective(self):
        """Get display label for effective CSP bucket."""
        value = self.csp_bucket
        if value:
            return CSPBucket(value).label
        return None

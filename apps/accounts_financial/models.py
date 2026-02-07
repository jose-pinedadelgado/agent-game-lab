import uuid
from django.conf import settings
from django.db import models


class Account(models.Model):
    """Represents a financial account (checking, savings, credit card, etc.)."""

    class AccountType(models.TextChoices):
        CHECKING = 'checking', 'Checking'
        SAVINGS = 'savings', 'Savings'
        CREDIT_CARD = 'credit_card', 'Credit Card'
        INVESTMENT = 'investment', 'Investment'
        LOAN = 'loan', 'Loan'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='financial_accounts'
    )
    name = models.CharField(max_length=100)  # e.g., "Chase Sapphire"
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CHECKING
    )
    institution = models.CharField(max_length=100, blank=True)  # e.g., "Chase"
    last_four = models.CharField(max_length=4, blank=True)  # Last 4 digits
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    is_active = models.BooleanField(default=True)
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Credit limit for credit cards"
    )
    initial_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Starting balance when account was added"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Financial Account'
        verbose_name_plural = 'Financial Accounts'

    def __str__(self):
        if self.last_four:
            return f"{self.name} (****{self.last_four})"
        return self.name

    @property
    def is_liability(self):
        """Returns True if this account represents a liability (debt)."""
        return self.account_type in [self.AccountType.CREDIT_CARD, self.AccountType.LOAN]

    @property
    def is_asset(self):
        """Returns True if this account represents an asset."""
        return not self.is_liability


class AccountBalanceSnapshot(models.Model):
    """Records a balance at a specific point in time for reconciliation."""

    class Source(models.TextChoices):
        STATEMENT = 'statement', 'Statement'
        MANUAL = 'manual', 'Manual Entry'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='snapshots'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    as_of_date = models.DateField()
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL
    )
    statement = models.ForeignKey(
        'statements.CreditCardStatement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='balance_snapshots'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-as_of_date', '-created_at']
        verbose_name = 'Balance Snapshot'
        verbose_name_plural = 'Balance Snapshots'

    def __str__(self):
        return f"{self.account.name}: ${self.balance} as of {self.as_of_date}"

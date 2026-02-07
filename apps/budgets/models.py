import uuid
from django.db import models
from django.conf import settings


class SpendingType(models.TextChoices):
    """Classification for Wants vs Needs budgeting."""
    NEED = 'need', 'Need'
    WANT = 'want', 'Want'
    SAVINGS = 'savings', 'Savings'


class CSPBucket(models.TextChoices):
    """Ramit Sethi's Conscious Spending Plan buckets."""
    FIXED = 'fixed', 'Fixed Costs (50-60%)'
    INVESTMENTS = 'investments', 'Investments (10%+)'
    SAVINGS = 'savings', 'Savings Goals (5-15%+)'
    GUILT_FREE = 'guilt_free', 'Guilt-Free Spending (20-35%)'


class BudgetSection(models.TextChoices):
    """Section within expenses tab (fixed vs variable)."""
    FIXED = 'fixed', 'Fixed Expenses'
    VARIABLE = 'variable', 'Variable Expenses'


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

    # Section within expenses tab
    section = models.CharField(
        max_length=10,
        choices=BudgetSection.choices,
        default=BudgetSection.VARIABLE,
        help_text="Whether this is a fixed or variable expense"
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="For bills with regular due dates"
    )
    due_day = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Day of month this bill is due (1-31)"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying within section"
    )

    # Secondary categorization defaults
    default_spending_type = models.CharField(
        max_length=10,
        choices=SpendingType.choices,
        null=True,
        blank=True,
        help_text="Default spending type for transactions in this category"
    )
    default_csp_bucket = models.CharField(
        max_length=15,
        choices=CSPBucket.choices,
        null=True,
        blank=True,
        help_text="Default Conscious Spending Plan bucket"
    )

    class Meta:
        unique_together = ['user', 'name']
        verbose_name_plural = 'Budget Categories'
        ordering = ['section', 'display_order', 'name']

    def __str__(self):
        return f"{self.name} (${self.monthly_limit})"

    @classmethod
    def create_defaults_for_user(cls, user):
        """Create default categories for a new user."""
        defaults = [
            # Fixed expenses
            {
                'name': 'Utilities', 'monthly_limit': 200, 'color': '#6B7280',
                'section': BudgetSection.FIXED, 'is_recurring': True,
                'default_spending_type': SpendingType.NEED, 'default_csp_bucket': CSPBucket.FIXED
            },
            # Variable expenses
            {
                'name': 'Groceries', 'monthly_limit': 500, 'color': '#10B981',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': SpendingType.NEED, 'default_csp_bucket': CSPBucket.FIXED
            },
            {
                'name': 'Dining', 'monthly_limit': 300, 'color': '#F59E0B',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': SpendingType.WANT, 'default_csp_bucket': CSPBucket.GUILT_FREE
            },
            {
                'name': 'Transportation', 'monthly_limit': 200, 'color': '#3B82F6',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': SpendingType.NEED, 'default_csp_bucket': CSPBucket.FIXED
            },
            {
                'name': 'Entertainment', 'monthly_limit': 150, 'color': '#8B5CF6',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': SpendingType.WANT, 'default_csp_bucket': CSPBucket.GUILT_FREE
            },
            {
                'name': 'Shopping', 'monthly_limit': 250, 'color': '#EC4899',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': SpendingType.WANT, 'default_csp_bucket': CSPBucket.GUILT_FREE
            },
            {
                'name': 'Other', 'monthly_limit': 500, 'color': '#9CA3AF',
                'section': BudgetSection.VARIABLE,
                'default_spending_type': None, 'default_csp_bucket': None
            },
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


class DebtPayoffStrategy(models.TextChoices):
    """Strategy for paying off multiple debts."""
    AVALANCHE = 'avalanche', 'Avalanche (Highest Interest First)'
    SNOWBALL = 'snowball', 'Snowball (Smallest Balance First)'


class Debt(models.Model):
    """Tracks debt for payoff planning."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    linked_account = models.OneToOneField(
        'accounts_financial.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_debt',
        help_text="Optional link to financial account"
    )
    name = models.CharField(max_length=100)
    original_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Balance when debt tracking started"
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Current remaining balance"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual percentage rate (APR)"
    )
    minimum_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum monthly payment required"
    )
    extra_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Additional monthly payment beyond minimum"
    )
    target_payoff_date = models.DateField(
        null=True,
        blank=True,
        help_text="Goal date to pay off this debt"
    )
    color = models.CharField(max_length=7, default='#EF4444')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-interest_rate', 'current_balance']
        verbose_name_plural = 'Debts'

    def __str__(self):
        return f"{self.name} (${self.current_balance})"

    @property
    def total_monthly_payment(self):
        """Total payment amount (minimum + extra)."""
        return self.minimum_payment + self.extra_payment

    @property
    def paid_off_amount(self):
        """Amount paid off so far."""
        return self.original_balance - self.current_balance

    @property
    def payoff_percentage(self):
        """Percentage of debt paid off."""
        if self.original_balance == 0:
            return 100
        return float(self.paid_off_amount / self.original_balance * 100)

    @property
    def is_paid_off(self):
        """True if debt is fully paid."""
        return self.current_balance <= 0


class DebtPayment(models.Model):
    """Records a payment toward a debt."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Remaining balance after this payment"
    )
    linked_transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='debt_payments'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.debt.name}: ${self.amount} on {self.payment_date}"


class GoalType(models.TextChoices):
    """Type of savings goal."""
    EMERGENCY_FUND = 'emergency', 'Emergency Fund'
    RETIREMENT = 'retirement', 'Retirement'
    INVESTMENT = 'investment', 'Investment'
    VACATION = 'vacation', 'Vacation'
    CAR = 'car', 'Car'
    HOUSE = 'house', 'House Down Payment'
    WEDDING = 'wedding', 'Wedding'
    EDUCATION = 'education', 'Education'
    OTHER = 'other', 'Other'


class SavingsGoal(models.Model):
    """Tracks progress toward a savings or investment goal."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    linked_account = models.ForeignKey(
        'accounts_financial.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_goals',
        help_text="Optional link to financial account"
    )
    name = models.CharField(max_length=100)
    goal_type = models.CharField(
        max_length=20,
        choices=GoalType.choices,
        default=GoalType.OTHER
    )
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Target amount to save"
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Current amount saved"
    )
    target_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target date to reach goal"
    )
    monthly_contribution = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Planned monthly contribution"
    )
    is_retirement = models.BooleanField(
        default=False,
        help_text="Whether this is a retirement account (401k, IRA)"
    )
    employer_match_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Employer 401k match percentage"
    )
    color = models.CharField(max_length=7, default='#10B981')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['goal_type', 'name']
        verbose_name = 'Savings Goal'
        verbose_name_plural = 'Savings Goals'

    def __str__(self):
        return f"{self.name} (${self.current_amount}/${self.target_amount})"

    @property
    def progress_percentage(self):
        """Percentage of goal achieved."""
        if self.target_amount == 0:
            return 100
        return min(100, float(self.current_amount / self.target_amount * 100))

    @property
    def remaining_amount(self):
        """Amount still needed to reach goal."""
        return max(0, self.target_amount - self.current_amount)

    @property
    def is_complete(self):
        """True if goal has been reached."""
        return self.current_amount >= self.target_amount

    @property
    def is_investment_type(self):
        """True if this is an investment or retirement goal."""
        return self.goal_type in [GoalType.RETIREMENT, GoalType.INVESTMENT] or self.is_retirement


class SavingsContribution(models.Model):
    """Records a contribution toward a savings goal."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    contribution_date = models.DateField()
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Goal balance after this contribution"
    )
    linked_transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='savings_contributions'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-contribution_date', '-created_at']

    def __str__(self):
        return f"{self.goal.name}: ${self.amount} on {self.contribution_date}"

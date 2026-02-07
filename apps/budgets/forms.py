from django import forms
from decimal import Decimal
from .models import (
    BudgetCategory, BudgetSection, SpendingType, CSPBucket,
    Debt, SavingsGoal, GoalType, DebtPayment, SavingsContribution
)


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating/editing budget categories."""

    class Meta:
        model = BudgetCategory
        fields = [
            'name', 'monthly_limit', 'color', 'section',
            'is_recurring', 'due_day',
            'default_spending_type', 'default_csp_bucket'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'due_day': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '31'}),
            'default_spending_type': forms.Select(attrs={'class': 'form-select'}),
            'default_csp_bucket': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'section': 'Expense Type',
            'is_recurring': 'Recurring Bill',
            'due_day': 'Due Day of Month',
            'default_spending_type': 'Default Spending Type',
            'default_csp_bucket': 'Default CSP Bucket',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Add empty choice to spending type/CSP fields
        self.fields['default_spending_type'].choices = [('', '-- None --')] + list(SpendingType.choices)
        self.fields['default_csp_bucket'].choices = [('', '-- None --')] + list(CSPBucket.choices)

        # Hide fields if user hasn't enabled the features
        if user:
            if not user.enable_wants_needs:
                self.fields['default_spending_type'].widget = forms.HiddenInput()
            if not user.enable_conscious_spending:
                self.fields['default_csp_bucket'].widget = forms.HiddenInput()

    def clean_due_day(self):
        """Validate due_day is between 1 and 31."""
        due_day = self.cleaned_data.get('due_day')
        if due_day is not None and (due_day < 1 or due_day > 31):
            raise forms.ValidationError("Due day must be between 1 and 31.")
        return due_day


class DebtForm(forms.ModelForm):
    """Form for creating/editing debts."""

    class Meta:
        model = Debt
        fields = [
            'name', 'original_balance', 'current_balance', 'interest_rate',
            'minimum_payment', 'extra_payment', 'target_payoff_date',
            'linked_account', 'color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Chase Visa'}),
            'original_balance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'current_balance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
            'minimum_payment': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'extra_payment': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'target_payoff_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'linked_account': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }
        labels = {
            'interest_rate': 'Interest Rate (APR %)',
            'extra_payment': 'Extra Monthly Payment',
            'target_payoff_date': 'Target Payoff Date',
            'linked_account': 'Link to Account',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Filter linked_account to user's accounts
        if user:
            from apps.accounts_financial.models import Account
            self.fields['linked_account'].queryset = Account.objects.filter(
                user=user,
                is_active=True,
                account_type__in=[Account.AccountType.CREDIT_CARD, Account.AccountType.LOAN]
            )
            self.fields['linked_account'].empty_label = "-- Not linked --"

    def clean(self):
        cleaned_data = super().clean()
        original = cleaned_data.get('original_balance')
        current = cleaned_data.get('current_balance')

        if original and current and current > original:
            self.add_error('current_balance', 'Current balance cannot exceed original balance.')

        return cleaned_data


class DebtPaymentForm(forms.ModelForm):
    """Form for recording debt payments."""

    class Meta:
        model = DebtPayment
        fields = ['amount', 'payment_date', 'linked_transaction', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'linked_transaction': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'linked_transaction': 'Link to Transaction',
        }

    def __init__(self, *args, debt=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.debt = debt

        # Filter transactions to user's payment transactions
        if user:
            from apps.transactions.models import Transaction, TransactionType
            self.fields['linked_transaction'].queryset = Transaction.objects.filter(
                user=user,
                transaction_type=TransactionType.PAYMENT
            ).order_by('-date')[:50]
            self.fields['linked_transaction'].empty_label = "-- Not linked --"


class SavingsGoalForm(forms.ModelForm):
    """Form for creating/editing savings goals."""

    class Meta:
        model = SavingsGoal
        fields = [
            'name', 'goal_type', 'target_amount', 'current_amount',
            'target_date', 'monthly_contribution',
            'is_retirement', 'employer_match_percent',
            'linked_account', 'color'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Emergency Fund'}),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'current_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monthly_contribution': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'is_retirement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'employer_match_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.1'}),
            'linked_account': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }
        labels = {
            'goal_type': 'Goal Type',
            'target_amount': 'Target Amount ($)',
            'current_amount': 'Current Amount ($)',
            'target_date': 'Target Date',
            'monthly_contribution': 'Planned Monthly Contribution',
            'is_retirement': 'Retirement Account (401k, IRA)',
            'employer_match_percent': 'Employer Match (%)',
            'linked_account': 'Link to Account',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Filter linked_account to user's accounts
        if user:
            from apps.accounts_financial.models import Account
            self.fields['linked_account'].queryset = Account.objects.filter(
                user=user,
                is_active=True
            )
            self.fields['linked_account'].empty_label = "-- Not linked --"


class SavingsContributionForm(forms.ModelForm):
    """Form for recording contributions to savings goals."""

    class Meta:
        model = SavingsContribution
        fields = ['amount', 'contribution_date', 'linked_transaction', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.01', 'step': '0.01'}),
            'contribution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'linked_transaction': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'linked_transaction': 'Link to Transaction',
        }

    def __init__(self, *args, goal=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.goal = goal

        # Filter transactions to user's deposit/transfer transactions
        if user:
            from apps.transactions.models import Transaction, TransactionType
            self.fields['linked_transaction'].queryset = Transaction.objects.filter(
                user=user,
                transaction_type__in=[TransactionType.DEPOSIT, TransactionType.TRANSFER]
            ).order_by('-date')[:50]
            self.fields['linked_transaction'].empty_label = "-- Not linked --"

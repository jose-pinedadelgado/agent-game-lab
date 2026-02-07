from django import forms
from decimal import Decimal
from .models import Account, AccountBalanceSnapshot


class AccountForm(forms.ModelForm):
    """Form for creating and editing financial accounts."""

    class Meta:
        model = Account
        fields = [
            'name',
            'account_type',
            'institution',
            'last_four',
            'color',
            'credit_limit',
            'initial_balance',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Chase Sapphire Preferred'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Chase, Bank of America'
            }),
            'last_four': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1234',
                'maxlength': '4'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control form-control-color',
                'type': 'color'
            }),
            'credit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'initial_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institution'].required = False
        self.fields['last_four'].required = False
        self.fields['credit_limit'].required = False

    def clean_last_four(self):
        value = self.cleaned_data.get('last_four', '')
        if value and (not value.isdigit() or len(value) != 4):
            raise forms.ValidationError('Last four digits must be exactly 4 numbers')
        return value


class BalanceSnapshotForm(forms.ModelForm):
    """Form for recording a balance snapshot."""

    class Meta:
        model = AccountBalanceSnapshot
        fields = ['balance', 'as_of_date', 'notes']
        widgets = {
            'balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'as_of_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional notes about this balance...'
            }),
        }


class TransferForm(forms.Form):
    """Form for creating a transfer between accounts."""

    from_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='From Account'
    )
    to_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='To Account'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description...'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        accounts = Account.objects.filter(user=user, is_active=True)
        self.fields['from_account'].queryset = accounts
        self.fields['to_account'].queryset = accounts

    def clean(self):
        cleaned_data = super().clean()
        from_account = cleaned_data.get('from_account')
        to_account = cleaned_data.get('to_account')

        if from_account and to_account and from_account == to_account:
            raise forms.ValidationError('Cannot transfer to the same account')

        return cleaned_data


class CCPaymentForm(forms.Form):
    """Form for creating a credit card payment."""

    from_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Pay From'
    )
    cc_account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Credit Card'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description...'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # From account should be debit accounts
        debit_accounts = Account.objects.filter(
            user=user,
            is_active=True,
            account_type__in=[
                Account.AccountType.CHECKING,
                Account.AccountType.SAVINGS,
            ]
        )
        # To account should be credit cards
        cc_accounts = Account.objects.filter(
            user=user,
            is_active=True,
            account_type=Account.AccountType.CREDIT_CARD
        )
        self.fields['from_account'].queryset = debit_accounts
        self.fields['cc_account'].queryset = cc_accounts

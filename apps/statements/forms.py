from django import forms
from .models import CreditCardStatement
from apps.accounts_financial.models import Account


class StatementUploadForm(forms.ModelForm):
    """Form for uploading credit card statements (PDF or CSV)."""

    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Link this statement to an existing account, or leave blank to auto-create one.'
    )
    create_balance_snapshot = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Import ending balance as snapshot',
        help_text='Record the statement ending balance for reconciliation.'
    )

    class Meta:
        model = CreditCardStatement
        fields = ['statement_file', 'bank_name', 'account']
        widgets = {
            'bank_name': forms.Select(attrs={'class': 'form-select'}),
            'statement_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.csv'
            }),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(
                user=user,
                is_active=True
            ).order_by('name')

    def clean_statement_file(self):
        file = self.cleaned_data.get('statement_file')
        if file:
            # Check file extension
            name_lower = file.name.lower()
            if not (name_lower.endswith('.pdf') or name_lower.endswith('.csv')):
                raise forms.ValidationError('Only PDF and CSV files are allowed.')
            # Check file size (10 MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 10 MB.')
        return file

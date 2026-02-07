from django import forms
from .models import CreditCardStatement


class StatementUploadForm(forms.ModelForm):
    """Form for uploading credit card statements (PDF or CSV)."""

    class Meta:
        model = CreditCardStatement
        fields = ['statement_file', 'bank_name']
        widgets = {
            'bank_name': forms.Select(attrs={'class': 'form-select'}),
            'statement_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.csv'
            }),
        }

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

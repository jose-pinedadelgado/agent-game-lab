from django import forms
from .models import User


class ProfileSettingsForm(forms.ModelForm):
    """Form for user profile and budgeting settings."""

    class Meta:
        model = User
        fields = ['monthly_income', 'enable_wants_needs', 'enable_conscious_spending']
        widgets = {
            'monthly_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'e.g., 5000.00'
            }),
            'enable_wants_needs': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'enable_conscious_spending': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'monthly_income': 'Monthly Income',
            'enable_wants_needs': 'Enable Wants vs Needs tracking',
            'enable_conscious_spending': 'Enable Conscious Spending Plan',
        }
        help_texts = {
            'monthly_income': 'Used to calculate CSP percentages',
            'enable_wants_needs': 'Categorize spending as Need, Want, or Savings',
            'enable_conscious_spending': 'Track spending against Ramit Sethi\'s 4-bucket system',
        }

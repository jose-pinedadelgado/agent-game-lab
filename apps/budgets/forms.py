from django import forms
from .models import BudgetCategory, SpendingType, CSPBucket


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating/editing budget categories."""

    class Meta:
        model = BudgetCategory
        fields = ['name', 'monthly_limit', 'color', 'default_spending_type', 'default_csp_bucket']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'default_spending_type': forms.Select(attrs={'class': 'form-select'}),
            'default_csp_bucket': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
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

from django import forms
from .models import BudgetCategory


class BudgetCategoryForm(forms.ModelForm):
    """Form for creating/editing budget categories."""

    class Meta:
        model = BudgetCategory
        fields = ['name', 'monthly_limit', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'monthly_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
        }

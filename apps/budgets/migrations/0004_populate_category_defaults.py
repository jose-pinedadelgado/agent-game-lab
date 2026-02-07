"""
Data migration to set default spending types and CSP buckets for existing categories.
"""
from django.db import migrations


# Category name -> (spending_type, csp_bucket)
CATEGORY_DEFAULTS = {
    'Groceries': ('need', 'fixed'),
    'Dining': ('want', 'guilt_free'),
    'Transportation': ('need', 'fixed'),
    'Entertainment': ('want', 'guilt_free'),
    'Shopping': ('want', 'guilt_free'),
    'Utilities': ('need', 'fixed'),
    # 'Other' intentionally left out - no defaults
}


def populate_defaults(apps, schema_editor):
    """Set default spending type and CSP bucket for existing categories."""
    BudgetCategory = apps.get_model('budgets', 'BudgetCategory')

    for name, (spending_type, csp_bucket) in CATEGORY_DEFAULTS.items():
        BudgetCategory.objects.filter(
            name__iexact=name,
            default_spending_type__isnull=True,
            default_csp_bucket__isnull=True
        ).update(
            default_spending_type=spending_type,
            default_csp_bucket=csp_bucket
        )


def reverse_defaults(apps, schema_editor):
    """Clear defaults (reverse migration)."""
    BudgetCategory = apps.get_model('budgets', 'BudgetCategory')

    for name in CATEGORY_DEFAULTS.keys():
        BudgetCategory.objects.filter(name__iexact=name).update(
            default_spending_type=None,
            default_csp_bucket=None
        )


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0003_secondary_categorization'),
    ]

    operations = [
        migrations.RunPython(populate_defaults, reverse_defaults),
    ]

# Generated migration to set default sections for existing categories

from django.db import migrations


def set_category_sections(apps, schema_editor):
    """Set appropriate sections for existing budget categories."""
    BudgetCategory = apps.get_model('budgets', 'BudgetCategory')

    # Categories that are typically fixed expenses
    fixed_category_names = [
        'Utilities', 'Rent', 'Mortgage', 'Insurance', 'Internet',
        'Phone', 'Cable', 'Subscriptions', 'Car Payment', 'Student Loans',
        'Child Care', 'Gym Membership', 'Streaming Services'
    ]

    for category in BudgetCategory.objects.all():
        if any(name.lower() in category.name.lower() for name in fixed_category_names):
            category.section = 'fixed'
        else:
            category.section = 'variable'
        category.save()


def reverse_sections(apps, schema_editor):
    """Reverse - set all to variable."""
    BudgetCategory = apps.get_model('budgets', 'BudgetCategory')
    BudgetCategory.objects.all().update(section='variable')


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0005_add_budget_tabs_models'),
    ]

    operations = [
        migrations.RunPython(set_category_sections, reverse_sections),
    ]

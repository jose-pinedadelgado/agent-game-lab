from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.models import User
from .models import BudgetCategory


@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    """Create default budget categories when a new user is created."""
    if created:
        BudgetCategory.create_defaults_for_user(instance)

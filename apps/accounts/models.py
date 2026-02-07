import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with UUID primary key and email as username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    preferred_currency = models.CharField(max_length=3, default='USD')
    timezone = models.CharField(max_length=50, default='America/Los_Angeles')

    # Budgeting features
    monthly_income = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Monthly income for budget calculations"
    )
    enable_wants_needs = models.BooleanField(
        default=False,
        help_text="Enable Wants vs Needs tracking"
    )
    enable_conscious_spending = models.BooleanField(
        default=False,
        help_text="Enable Conscious Spending Plan tracking"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

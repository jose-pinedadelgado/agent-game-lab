"""
Pytest configuration and fixtures for Bamboo Money tests.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a client with an authenticated user."""
    client.login(email='test@example.com', password='testpass123')
    return client

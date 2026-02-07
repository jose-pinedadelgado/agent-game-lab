"""
URL configuration for Bamboo Money project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.analytics.urls')),  # Dashboard is home
    path('statements/', include('apps.statements.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('budgets/', include('apps.budgets.urls')),
    path('advisor/', include('apps.advisor.urls')),
    path('profile/', include('apps.accounts.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

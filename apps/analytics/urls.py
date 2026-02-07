from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('trends/', views.trends, name='trends'),
    path('api/spending-by-category/', views.api_spending_by_category, name='api_spending_by_category'),
    path('api/monthly-trends/', views.api_monthly_trends, name='api_monthly_trends'),
]

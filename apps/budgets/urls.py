from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    path('', views.manage_categories, name='manage'),
    path('create/', views.create_category, name='create'),
    path('<uuid:pk>/edit/', views.edit_category, name='edit'),
    path('<uuid:pk>/delete/', views.delete_category, name='delete'),
    path('alerts/', views.alerts, name='alerts'),
]

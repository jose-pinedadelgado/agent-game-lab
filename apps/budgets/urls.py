from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    # Overview (redirects to expenses)
    path('', views.budget_overview, name='overview'),

    # Expenses Tab
    path('expenses/', views.expenses_tab, name='expenses'),
    path('expenses/category/create/', views.create_category, name='create_category'),
    path('expenses/category/<uuid:pk>/edit/', views.edit_category, name='edit_category'),
    path('expenses/category/<uuid:pk>/delete/', views.delete_category, name='delete_category'),

    # Debt Tab
    path('debt/', views.debt_tab, name='debt'),
    path('debt/add/', views.add_debt, name='add_debt'),
    path('debt/<uuid:pk>/', views.debt_detail, name='debt_detail'),
    path('debt/<uuid:pk>/edit/', views.edit_debt, name='edit_debt'),
    path('debt/<uuid:pk>/delete/', views.delete_debt, name='delete_debt'),
    path('debt/<uuid:pk>/payment/', views.record_debt_payment, name='debt_payment'),
    path('debt/toggle-strategy/', views.toggle_debt_strategy, name='toggle_debt_strategy'),

    # Savings Tab
    path('savings/', views.savings_tab, name='savings'),
    path('savings/goal/create/', views.create_savings_goal, name='create_goal'),
    path('savings/goal/<uuid:pk>/', views.savings_goal_detail, name='goal_detail'),
    path('savings/goal/<uuid:pk>/edit/', views.edit_savings_goal, name='edit_goal'),
    path('savings/goal/<uuid:pk>/delete/', views.delete_savings_goal, name='delete_goal'),
    path('savings/goal/<uuid:pk>/contribute/', views.record_contribution, name='contribute'),

    # Legacy routes (redirect to new structure)
    path('manage/', views.manage_categories, name='manage'),
    path('create/', views.create_category, name='create'),
    path('<uuid:pk>/edit/', views.edit_category, name='edit'),
    path('<uuid:pk>/delete/', views.delete_category, name='delete'),

    # Alerts
    path('alerts/', views.alerts, name='alerts'),
]

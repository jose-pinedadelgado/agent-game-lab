from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='list'),
    path('<uuid:pk>/', views.transaction_detail, name='detail'),
    path('<uuid:pk>/update-category/', views.update_category, name='update_category'),
    path('<uuid:pk>/update-spending/', views.update_spending_override, name='update_spending'),
]

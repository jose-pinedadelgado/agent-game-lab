from django.urls import path
from . import views

app_name = 'accounts_financial'

urlpatterns = [
    path('', views.account_list, name='list'),
    path('create/', views.create_account, name='create'),
    path('<uuid:pk>/', views.account_detail, name='detail'),
    path('<uuid:pk>/edit/', views.edit_account, name='edit'),
    path('<uuid:pk>/delete/', views.delete_account, name='delete'),
    path('<uuid:pk>/add-balance/', views.add_balance_snapshot, name='add_balance'),
    path('<uuid:pk>/balance-history/', views.balance_history_api, name='balance_history_api'),
    path('transfer/', views.create_transfer, name='create_transfer'),
    path('cc-payment/', views.create_cc_payment, name='create_cc_payment'),
    path('transaction/<uuid:pk>/mark-posted/', views.mark_transaction_posted, name='mark_posted'),
]

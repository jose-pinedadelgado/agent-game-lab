from django.urls import path
from . import views

app_name = 'statements'

urlpatterns = [
    path('upload/', views.upload_statement, name='upload'),
    path('history/', views.statement_history, name='history'),
    path('<uuid:pk>/delete/', views.delete_statement, name='delete'),
]

from django.urls import path
from . import views

app_name = 'cashie'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('new/', views.new_session, name='new_session'),
    path('session/<uuid:session_id>/', views.chat_view, name='session'),
    path('send/', views.send_message, name='send_message'),
]

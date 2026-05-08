from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('cancel-reset/', views.cancel_password_reset, name='cancel_reset'),
]
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('book/<int:field_id>/', views.book_field, name='book_field'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('join-team/<int:team_id>/', views.join_team, name='join_team'),
    path('manage-team/<int:team_id>/', views.manage_join_requests, name='manage_join_requests'),
]

from django.urls import path
from . import views

app_name = 'fields'

urlpatterns = [
    path('', views.fields, name='fields'),
    path('search/', views.advanced_search, name='advanced_search'),
    path('search/basic/', views.search_fields, name='search_fields'),
    path('<int:field_id>/', views.field_detail, name='field_detail'),
    path('add/', views.add_field, name='add_field'),
    path('manage/', views.manage_fields, name='manage_fields'),
    path('<int:field_id>/edit/', views.edit_field, name='edit_field'),
    path('<int:field_id>/time-slots/', views.manage_time_slots, name='manage_time_slots'),
    path('<int:field_id>/review/', views.add_review, name='add_review'),
    path('review/image/<int:image_id>/delete/', views.delete_review_image, name='delete_review_image'),
    path('<int:field_id>/delete/', views.delete_field, name='delete_field'),
    path('<int:field_id>/review/delete/', views.delete_review, name='delete_review'),
]
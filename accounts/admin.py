from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'age', 'gender', 'is_field_owner', 'mobile']
    list_filter = ['gender', 'is_field_owner']
    search_fields = ['user__username', 'user__email', 'mobile']
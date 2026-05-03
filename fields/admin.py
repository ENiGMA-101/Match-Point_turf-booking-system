from django.contrib import admin
from .models import Field, FieldTimeSlot, Review, ReviewImage


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'field_type', 'location', 'availability_type', 'cost_per_hour', 'is_active']
    list_filter = ['field_type', 'availability_type', 'is_women_only', 'is_active']
    search_fields = ['name', 'location', 'owner__username']


@admin.register(FieldTimeSlot)
class FieldTimeSlotAdmin(admin.ModelAdmin):
    list_display = ['field', 'start_time', 'end_time', 'is_available']
    list_filter = ['is_available']


class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    fields = ['image', 'caption']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'field', 'rating', 'experience_title', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__username', 'field__name', 'experience_title']
    inlines = [ReviewImageInline]


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['review__user__username', 'review__field__name', 'caption']
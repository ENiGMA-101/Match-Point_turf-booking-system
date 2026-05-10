from django.contrib import admin
from .models import Booking, TeamFormation, JoinRequest, Payment

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'field', 'booking_date', 'status', 'total_cost', 'created_at']
    list_filter = ['status', 'booking_date', 'field__field_type']
    search_fields = ['user__username', 'field__name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'booking_date'

    def total_cost(self, obj):
        return f"${obj.total_cost}"
    total_cost.short_description = 'Total Cost'


@admin.register(TeamFormation)
class TeamFormationAdmin(admin.ModelAdmin):
    list_display = ['booking', 'looking_for_players', 'required_players', 'skill_level', 'created_at']
    list_filter = ['looking_for_players', 'skill_level']
    search_fields = ['booking__user__username', 'booking__field__name']


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'team_formation', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'team_formation__booking__field__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'payment_method', 'amount', 'status', 'transaction_id', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['booking__user__username', 'transaction_id', 'mobile_number']
    readonly_fields = ['transaction_id', 'created_at']

    def amount(self, obj):
        return f"${obj.amount}"
    amount.short_description = 'Amount'
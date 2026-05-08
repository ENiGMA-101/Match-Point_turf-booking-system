from django.db import models
from django.contrib.auth.models import User
from fields.models import Field, FieldTimeSlot
from decimal import Decimal


class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(FieldTimeSlot, on_delete=models.CASCADE)
    booking_date = models.DateField()
    players_count = models.PositiveIntegerField()
    special_requirements = models.TextField(blank=True)
    emergency_contact_visible = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_cost(self):
        if self.field.availability_type == 'Free':
            return Decimal('0.00')
        return self.field.get_90min_cost()

    def __str__(self):
        return f"{self.user.username} - {self.field.name} - {self.booking_date}"

    class Meta:
        app_label = 'bookings'

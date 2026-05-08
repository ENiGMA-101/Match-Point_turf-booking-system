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


class TeamFormation(models.Model):
    SKILL_LEVELS = (
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='team_formation')
    looking_for_players = models.BooleanField(default=False)
    required_players = models.PositiveIntegerField(default=1)
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVELS, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Team for {self.booking}"

    class Meta:
        app_label = 'bookings'


class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    )

    team_formation = models.ForeignKey(TeamFormation, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} wants to join {self.team_formation.booking}"

    class Meta:
        app_label = 'bookings'


class Payment(models.Model):
    PAYMENT_METHODS = (
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('upay', 'Upay'),
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    mobile_number = models.CharField(max_length=15)
    transaction_id = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.booking} - {self.transaction_id}"

    class Meta:
        app_label = 'bookings'

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Field(models.Model):
    def __str__(self):
        return self.name

    FIELD_TYPES = (
        ('Cricket', 'Cricket'),
        ('Football', 'Football'),
        ('Tennis', 'Tennis'),
        ('Basketball', 'Basketball'),
    )

    AVAILABILITY = (
        ('Free', 'Free'),
        ('Paid', 'Paid'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    location = models.CharField(max_length=300)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    availability_type = models.CharField(max_length=10, choices=AVAILABILITY)
    description = models.TextField(max_length=1000)
    image = models.ImageField(upload_to='fields/', blank=True, null=True)
    is_women_only = models.BooleanField(default=False)
    capacity = models.PositiveIntegerField()
    amenities = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_90min_cost(self):
        """Get cost for 90 minutes (1.5 hours)"""
        if self.availability_type == 'Free':
            return Decimal('0.00')
        return self.cost_per_hour * Decimal('1.5')

    def get_formatted_90min_cost(self):
        """Get formatted cost for display"""
        cost = self.get_90min_cost()
        return f"${cost:.2f}"


class FieldTimeSlot(models.Model):
    def __str__(self):
        return f"{self.field.name} - {self.start_time} to {self.end_time}"

    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)


class Review(models.Model):
    def __str__(self):
        return f"{self.user.username} - {self.field.name}"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(max_length=1000, blank=True)
    experience_title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'field')


class ReviewImage(models.Model):
    def __str__(self):
        return f"{self.review.user.username} - {self.review.field.name} - Image {self.id}"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

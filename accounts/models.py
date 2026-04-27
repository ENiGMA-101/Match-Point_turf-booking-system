from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField(null=True, blank=True, default=18)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=[('Male', 'Male'), ('Female', 'Female')], 
        blank=True, 
        null=True,
        default='Male'
    )
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    is_field_owner = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def save(self, *args, **kwargs):
        if self.age is None:
            self.age = 18
        if not self.gender:
            self.gender = 'Male'
        super().save(*args, **kwargs)
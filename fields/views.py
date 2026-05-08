from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count, Min, Max
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date, time, timedelta, datetime
from decimal import Decimal
from .forms import FieldForm, ReviewForm
from .models import Field, FieldTimeSlot, Review, ReviewImage
from datetime import date
from bookings.models import TeamFormation, Booking
from accounts.models import UserProfile

def home(request):
    recent_fields = Field.objects.filter(is_active=True).order_by('-created_at')[:6]
    context = {
        'recent_fields': recent_fields,
    }
    return render(request, "home.html", context)


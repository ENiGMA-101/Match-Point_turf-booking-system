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


def fields(request):
    fields_list = Field.objects.filter(is_active=True)

    field_type = request.GET.get('field_type')
    availability = request.GET.get('availability')
    women_only = request.GET.get('women_only')
    location = request.GET.get('location')

    if field_type and field_type != 'All':
        fields_list = fields_list.filter(field_type=field_type)
    if availability and availability != 'All':
        fields_list = fields_list.filter(availability_type=availability)
    if women_only == 'on':
        fields_list = fields_list.filter(is_women_only=True)
    if location:
        fields_list = fields_list.filter(location__icontains=location)

    context = {
        'fields': fields_list,
        'field_types': Field.FIELD_TYPES,
        'availability_types': Field.AVAILABILITY,
        'today': date.today(),
    }
    return render(request, 'fields/fields.html', context)

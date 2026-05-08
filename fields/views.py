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

@login_required
def delete_field(request, field_id):
    field = get_object_or_404(Field, id=field_id, owner=request.user)
    if request.method == 'POST':
        field.delete()
        messages.success(request, 'Field deleted successfully.')
        return redirect('fields:manage_fields')
    return render(request, 'fields/confirm_delete_field.html', {'field': field})

@login_required
def delete_review(request, field_id):
    field = get_object_or_404(Field, id=field_id)
    review = Review.objects.filter(user=request.user, field=field).first()
    if not review:
        messages.info(request, 'No review to delete.')
        return redirect('fields:field_detail', field_id=field.id)

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('fields:field_detail', field_id=field.id)

    return render(request, 'fields/confirm_delete_review.html', {'field': field})

def advanced_search(request):
    fields_list = Field.objects.filter(is_active=True)

    field_type = request.GET.get('field_type')
    availability = request.GET.get('availability')
    location = request.GET.get('location')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')
    amenities = request.GET.get('amenities')
    capacity = request.GET.get('capacity')
    women_only = request.GET.get('women_only')

    available_date = request.GET.get('available_date')
    available_time = request.GET.get('available_time')

    if field_type and field_type != 'All':
        fields_list = fields_list.filter(field_type=field_type)

    if availability and availability != 'All':
        fields_list = fields_list.filter(availability_type=availability)

    if location:
        fields_list = fields_list.filter(location__icontains=location)

    if min_price:
        try:
            fields_list = fields_list.filter(cost_per_hour__gte=Decimal(min_price))
        except:
            pass

    if max_price:
        try:
            fields_list = fields_list.filter(cost_per_hour__lte=Decimal(max_price))
        except:
            pass

    if min_rating:
        try:
            fields_list = fields_list.annotate(
                avg_rating=Avg('review__rating')
            ).filter(avg_rating__gte=float(min_rating))
        except:
            pass

    if amenities:
        fields_list = fields_list.filter(amenities__icontains=amenities)

    if capacity:
        try:
            fields_list = fields_list.filter(capacity__gte=int(capacity))
        except:
            pass

    if women_only == 'on':
        fields_list = fields_list.filter(is_women_only=True)

    if available_date and available_time:
        try:
            check_date = datetime.strptime(available_date, '%Y-%m-%d').date()
            check_time = datetime.strptime(available_time, '%H:%M').time()


            matching_slots = FieldTimeSlot.objects.filter(
                start_time__lte=check_time,
                end_time__gt=check_time,
                is_available=True
            )

            booked_slots = Booking.objects.filter(
                booking_date=check_date,
                time_slot__in=matching_slots,
                status__in=['Confirmed', 'Pending']
            ).values_list('time_slot_id', 'field_id')

            booked_field_slot_pairs = set(booked_slots)
            available_fields = []

            for field in fields_list:
                field_slots = matching_slots.filter(field=field)
                has_available_slot = False

                for slot in field_slots:
                    if (slot.id, field.id) not in booked_field_slot_pairs:
                        has_available_slot = True
                        break

                if has_available_slot:
                    available_fields.append(field.id)

            fields_list = fields_list.filter(id__in=available_fields)

        except ValueError:
            pass

    sort_by = request.GET.get('sort_by', 'name')
    if sort_by == 'price_low':
        fields_list = fields_list.order_by('cost_per_hour')
    elif sort_by == 'price_high':
        fields_list = fields_list.order_by('-cost_per_hour')
    elif sort_by == 'rating':
        fields_list = fields_list.annotate(
            avg_rating=Avg('review__rating')
        ).order_by('-avg_rating')
    elif sort_by == 'newest':
        fields_list = fields_list.order_by('-created_at')
    else:
        fields_list = fields_list.order_by('name')

    price_range = Field.objects.filter(is_active=True).aggregate(
        min_price=Min('cost_per_hour'),
        max_price=Max('cost_per_hour')
    )

    context = {
        'fields': fields_list,
        'field_types': Field.FIELD_TYPES,
        'availability_types': Field.AVAILABILITY,
        'price_range': price_range,
        'current_filters': request.GET,
        'today': date.today(),
    }
    return render(request, 'fields/advanced_search.html', context)


def field_detail(request, field_id):
    field = get_object_or_404(Field, id=field_id, is_active=True)
    time_slots = FieldTimeSlot.objects.filter(field=field, is_available=True)
    reviews = Review.objects.filter(field=field).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    today = date.today()
    available_dates = []

    for i in range(8):
        check_date = today + timedelta(days=i)

        booked_slots = set()
        try:
            bookings = Booking.objects.filter(
                field=field,
                booking_date=check_date,
                status__in=['Confirmed', 'Pending']
            ).values_list('time_slot_id', flat=True)
            booked_slots.update(bookings)
        except ImportError:
            pass

        total_slots = time_slots.count()
        available_slots = total_slots - len(booked_slots)

        available_dates.append({
            'date': check_date,
            'available_slots': available_slots,
            'total_slots': total_slots,
            'is_fully_booked': available_slots == 0
        })

    team_formations = []
    try:
        team_formations = TeamFormation.objects.filter(
            booking__field=field,
            looking_for_players=True,
            booking__booking_date__gte=date.today(),
            booking__status='Confirmed'
        )
    except ImportError:
        pass

    context = {
        'field': field,
        'time_slots': time_slots,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'team_formations': team_formations,
        'available_dates': available_dates,
        'today': today,
    }
    return render(request, 'fields/field_detail.html', context)


@login_required
def manage_fields(request):
    user_profile, created = request.user.userprofile, False
    try:
        user_profile = request.user.userprofile
    except:
        
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'age': 18,
                'gender': 'Male',
                'is_field_owner': False
            }
        )

    if not user_profile.is_field_owner:
        messages.error(request, "You need to be a field owner to access this page.")
        return redirect('accounts:user_profile')

    owned_fields = Field.objects.filter(owner=request.user)
    return render(request, 'fields/manage_fields.html', {'owned_fields': owned_fields})

@login_required
def add_field(request):
    try:
        user_profile = request.user.userprofile
    except:
        user_profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'age': 18,
                'gender': 'Male',
                'is_field_owner': False
            }
        )

    if not user_profile.is_field_owner:
        messages.error(request, "You need to be a field owner to add fields.")
        return redirect('accounts:user_profile')

    if request.method == 'POST':
        field_form = FieldForm(request.POST, request.FILES)

        if field_form.is_valid():
            field = field_form.save(commit=False)
            field.owner = request.user
            field.save()

            create_default_time_slots(field)

            messages.success(request, "Field added successfully with time slots!")
            return redirect('fields:manage_fields')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        field_form = FieldForm()

    return render(request, 'fields/add_field.html', {'field_form': field_form})

def create_default_time_slots(field):
    time_slots = [
        (time(6, 0), time(7, 30)),  # 6:00 AM - 7:30 AM
        (time(7, 30), time(9, 0)),  # 7:30 AM - 9:00 AM
        (time(9, 0), time(10, 30)),  # 9:00 AM - 10:30 AM
        (time(10, 30), time(12, 0)),  # 10:30 AM - 12:00 PM
        (time(12, 0), time(13, 30)),  # 12:00 PM - 1:30 PM
        (time(13, 30), time(15, 0)),  # 1:30 PM - 3:00 PM
        (time(15, 0), time(16, 30)),  # 3:00 PM - 4:30 PM
        (time(16, 30), time(18, 0)),  # 4:30 PM - 6:00 PM
        (time(18, 0), time(19, 30)),  # 6:00 PM - 7:30 PM
        (time(19, 30), time(21, 0)),  # 7:30 PM - 9:00 PM
        (time(21, 0), time(22, 30)),  # 9:00 PM - 10:30 PM
    ]

    for start_time, end_time in time_slots:
        FieldTimeSlot.objects.create(
            field=field,
            start_time=start_time,
            end_time=end_time,
            is_available=True
        )

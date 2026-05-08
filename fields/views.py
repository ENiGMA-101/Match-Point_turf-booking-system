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

@login_required
def delete_field(request, field_id):
    field = get_object_or_404(Field, id=field_id, owner=request.user)
    if request.method == 'POST':
        field.delete()
        messages.success(request, 'Field deleted successfully.')
        return redirect('fields:manage_fields')
    return render(request, 'fields/confirm_delete_field.html', {'field': field})

@login_required
def add_review(request, field_id):
    field = get_object_or_404(Field, id=field_id)

    try:
        has_booking = Booking.objects.filter(
            user=request.user,
            field=field,
            status__in=['Confirmed', 'Completed'] 
        ).exists()

        user_booking = Booking.objects.filter(
            user=request.user,
            field=field
        ).first()

        user_booking_status = user_booking.status if user_booking else None

    except ImportError:
        has_booking = True 
        user_booking_status = None

    if not has_booking:
        if user_booking_status:
            if user_booking_status == 'Pending':
                messages.warning(request,
                                 "Your booking is still pending approval. You can review this field once your booking is confirmed.")
            elif user_booking_status == 'Cancelled':
                messages.info(request, "Your booking was cancelled. To review this field, please make a new booking.")
            else:
                messages.info(request,
                              f"Your booking status is '{user_booking_status}'. You can review once your booking is confirmed or completed.")
        else:
            messages.info(request,
                          "To review this field, please book it first. You can review after your booking is confirmed.")

        return redirect('fields:field_detail', field_id=field_id)

    existing_review = Review.objects.filter(user=request.user, field=field).first()

    if request.method == 'POST':
        review_form = ReviewForm(request.POST, instance=existing_review)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.field = field
            review.save()

            uploaded_files = request.FILES.getlist('review_images')
            image_captions = request.POST.getlist('image_captions')

            if existing_review:
                ReviewImage.objects.filter(review=review).delete()

            for i, uploaded_file in enumerate(uploaded_files[:5]):
                caption = image_captions[i] if i < len(image_captions) else ''
                ReviewImage.objects.create(
                    review=review,
                    image=uploaded_file,
                    caption=caption
                )

            if existing_review:
                messages.success(request, "Review updated successfully!")
            else:
                messages.success(request, "Review added successfully!")

            return redirect('fields:field_detail', field_id=field_id)
        else:
            messages.error(request, "Please fix the errors in the form.")
    else:
        review_form = ReviewForm(instance=existing_review)

    existing_images = []
    if existing_review:
        existing_images = ReviewImage.objects.filter(review=existing_review)

    context = {
        'field': field,
        'review_form': review_form,
        'existing_review': existing_review,
        'existing_images': existing_images,
        'user_booking_status': user_booking_status,
    }
    return render(request, 'fields/add_review.html', context)


@login_required
def delete_review_image(request, image_id):
    image = get_object_or_404(ReviewImage, id=image_id)

    if image.review.user != request.user:
        messages.error(request, "You can only delete your own review images.")
        return redirect('fields:field_detail', field_id=image.review.field.id)

    field_id = image.review.field.id
    image.delete()
    messages.success(request, "Image deleted successfully!")

    return redirect('fields:add_review', field_id=field_id)

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

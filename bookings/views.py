from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import date, timedelta
from fields.models import Field, FieldTimeSlot
from .models import Booking, TeamFormation, JoinRequest, Payment
from .forms import BookingForm, TeamFormationForm
from .payment_service import payment_service


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def book_field(request, field_id):
    field = get_object_or_404(Field, id=field_id, is_active=True)
    today = date.today()
    max_date = today + timedelta(days=7)
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))

    try:
        selected_date = timezone.datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today

    time_slots = FieldTimeSlot.objects.filter(field=field, is_available=True)
    booked_slots = Booking.objects.filter(
        field=field,
        booking_date=selected_date,
        status__in=['Confirmed', 'Pending']
    ).values_list('time_slot_id', flat=True)

    time_slots_with_status = []
    for slot in time_slots:
        time_slots_with_status.append({
            'slot': slot,
            'is_booked': slot.id in booked_slots
        })

    if request.method == 'POST':
        booking_form = BookingForm(request.POST)
        team_form = TeamFormationForm(request.POST)

        if booking_form.is_valid():
            slot_id = request.POST.get('time_slot')
            if slot_id and int(slot_id) in booked_slots:
                messages.error(request, "This time slot is no longer available.")
                return redirect('bookings:book_field', field_id=field_id)

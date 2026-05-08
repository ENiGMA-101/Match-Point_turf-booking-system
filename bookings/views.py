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

            booking = booking_form.save(commit=False)
            booking.user = request.user
            booking.field = field
            booking.save()

            # Handle team formation
            if team_form.is_valid() and team_form.cleaned_data.get('looking_for_players'):
                team_formation = team_form.save(commit=False)
                team_formation.booking = booking
                team_formation.save()

            # Redirect to payment or confirmation
            if field.availability_type == 'Paid':
                return redirect('bookings:process_payment', booking_id=booking.id)
            else:
                booking.status = 'Confirmed'
                booking.save()
                messages.success(request, "Free field booked successfully!")
                return redirect('bookings:booking_detail', booking_id=booking.id)
    else:
        booking_form = BookingForm()
        team_form = TeamFormationForm()

    context = {
        'field': field,
        'booking_form': booking_form,
        'team_form': team_form,
        'time_slots_with_status': time_slots_with_status,
        'selected_date': selected_date,
        'today': today,
        'max_date': max_date,
    }
    return render(request, 'bookings/book_field.html', context)


@login_required
def process_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.field.availability_type == 'Free':
        messages.info(request, "This is a free field, no payment required.")
        return redirect('bookings:booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        mobile = request.POST.get('mobile')
        pin = request.POST.get('pin')

        result = payment_service.process_payment(booking, payment_method, mobile, pin)

        if result['success']:
            messages.success(request, "Payment completed successfully!")
            context = {
                'booking': booking,
                'transaction_id': result['transaction_id'],
                'payment_method': result['payment_method'],
                'amount': result['amount']
            }
            return render(request, 'bookings/payment_success.html', context)
        else:
            messages.error(request, result['message'])

    return render(request, 'bookings/process_payment.html', {'booking': booking})


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status == 'Confirmed':
        booking.status = 'Cancelled'
        booking.save()
        messages.success(request, "Booking cancelled successfully!")
    else:
        messages.error(request, "Cannot cancel this booking.")

    return redirect('bookings:my_bookings')


@login_required
def join_team(request, team_id):
    team_formation = get_object_or_404(TeamFormation, id=team_id)

    if request.method == 'POST':
        message = request.POST.get('message', '')

        # Check if already requested
        existing_request = JoinRequest.objects.filter(
            team_formation=team_formation,
            user=request.user
        ).first()

        if existing_request:
            messages.info(request, "You have already sent a join request for this team.")
        else:
            JoinRequest.objects.create(
                team_formation=team_formation,
                user=request.user,
                message=message
            )
            messages.success(request, "Join request sent successfully!")

        return redirect('fields:field_detail', field_id=team_formation.booking.field.id)

    return render(request, 'bookings/join_team.html', {'team_formation': team_formation})


@login_required
def manage_join_requests(request, team_id):
    team_formation = get_object_or_404(TeamFormation, id=team_id, booking__user=request.user)
    join_requests = JoinRequest.objects.filter(team_formation=team_formation, status='Pending')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        join_request = get_object_or_404(JoinRequest, id=request_id, team_formation=team_formation)

        if action == 'accept':
            join_request.status = 'Accepted'
            join_request.save()
            messages.success(request, f"{join_request.user.username} has been accepted to your team!")
        elif action == 'reject':
            join_request.status = 'Rejected'
            join_request.save()
            messages.info(request, f"{join_request.user.username}'s request has been rejected.")

        return redirect('bookings:manage_join_requests', team_id=team_id)

    context = {
        'team_formation': team_formation,
        'join_requests': join_requests,
    }
    return render(request, 'bookings/manage_join_requests.html', context)

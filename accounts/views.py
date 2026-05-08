from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import UserProfile
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm, ForgotPasswordForm, ResetPasswordForm

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            profile = profile_form.save(commit=False)
            profile.user = user
            
            if not profile.age:
                profile.age = 18
            if not profile.gender:
                profile.gender = 'Male'
                
            profile.save()
            
            messages.success(request, 'Account created successfully! You can now sign in.')
            return redirect('accounts:login')
        else:
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'accounts/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def user_login(request):
    if request.user.is_authenticated:
        messages.info(request, f'You are already logged in as {request.user.username}.')
        return redirect('accounts:user_profile')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is disabled. Please contact support.')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'accounts/login.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        try:
            profile = user.userprofile
            if getattr(profile, 'profile_picture', None):
                profile.profile_picture.delete(save=False)
        except Exception:
            pass

        logout(request)
        user.delete()
        messages.success(request, 'Your account has been deleted.')
        return redirect('home')

    return render(request, 'accounts/confirm_delete_account.html')


def user_logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Goodbye {username}! You have been signed out successfully.')
    return redirect('home')

@login_required
def user_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'age': 18,
            'gender': 'Male',
            'mobile': '',
            'address': '',
            'emergency_contact': '',
            'is_field_owner': False
        }
    )
    
    if request.method == 'POST':
        if 'delete_account' in request.POST:
            username = request.user.username
            request.user.delete()
            messages.success(request, f'Account {username} deleted successfully.')
            return redirect('home')
        
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            
            profile = profile_form.save(commit=False)
            if not profile.age:
                profile.age = 18
            if not profile.gender:
                profile.gender = 'Male'
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:user_profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    bookings = []
    try:
        from bookings.models import Booking
        bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    except ImportError:
        pass
    owned_fields = []
    if user_profile.is_field_owner:
        try:
            from fields.models import Field
            owned_fields = Field.objects.filter(owner=request.user)
        except ImportError:
            pass
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
        'bookings': bookings,
        'owned_fields': owned_fields,
        'today': timezone.now().date(),
    }
    
    return render(request, 'accounts/user_profile.html', context)

def forgot_password(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in. You can change your password in your profile.')
        return redirect('accounts:user_profile')
    
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            
            request.session['reset_username'] = username
            request.session['reset_timestamp'] = timezone.now().isoformat()
            
            messages.success(request, f'Account found! You can now set a new password for {username}.')
            return redirect('accounts:reset_password')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})

def reset_password(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('accounts:user_profile')
    
    username = request.session.get('reset_username')
    reset_time = request.session.get('reset_timestamp')
    
    if not username or not reset_time:
        messages.error(request, 'Session expired. Please start the password recovery process again.')
        return redirect('accounts:forgot_password')
    
    try:
        reset_timestamp = timezone.datetime.fromisoformat(reset_time.replace('Z', '+00:00'))
        if timezone.now() - reset_timestamp > timezone.timedelta(minutes=15):
            request.session.pop('reset_username', None)
            request.session.pop('reset_timestamp', None)
            messages.error(request, 'Password reset session expired. Please try again.')
            return redirect('accounts:forgot_password')
    except:
        messages.error(request, 'Invalid session. Please start over.')
        return redirect('accounts:forgot_password')
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'User account not found.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            
            user.set_password(new_password)
            user.save()
            
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'age': 18,
                    'gender': 'Male',
                    'mobile': '',
                    'address': '',
                    'emergency_contact': '',
                    'is_field_owner': False
                }
            )
            
            request.session.pop('reset_username', None)
            request.session.pop('reset_timestamp', None)
            
            messages.success(request, 'Password updated successfully! You can now sign in with your new password.')
            return redirect('accounts:login')
    else:
        form = ResetPasswordForm(initial={
            'username': username,
            'email': user.email
        })
    
    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'user': user
    })

def cancel_password_reset(request):
    request.session.pop('reset_username', None)
    request.session.pop('reset_timestamp', None)
    messages.info(request, 'Password reset cancelled.')
    return redirect('accounts:login')
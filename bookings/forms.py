from django import forms
from .models import Booking, TeamFormation


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['booking_date', 'time_slot', 'players_count', 'special_requirements', 'emergency_contact_visible']
        widgets = {
            'booking_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'players_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requirements...'
            }),
            'emergency_contact_visible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TeamFormationForm(forms.ModelForm):
    class Meta:
        model = TeamFormation
        fields = ['looking_for_players', 'required_players', 'skill_level', 'description']
        widgets = {
            'looking_for_players': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'required_players': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'skill_level': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe your team and what you are looking for...'
            }),
        }

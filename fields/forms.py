from django import forms
from .models import Field, FieldTimeSlot, Review, ReviewImage


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ['name', 'field_type', 'location', 'cost_per_hour', 'availability_type',
                 'description', 'image', 'is_women_only', 'capacity', 'amenities']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'availability_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'amenities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

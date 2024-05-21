from django import forms
from .models import CheckInOut, Profile, InOut

class CheckInOutForm(forms.ModelForm):
    class Meta:
        model = CheckInOut
        fields = ['plate_number', 'vehicle_type', 'check_in_time', 'check_out_time']
        widgets = {
            'check_in_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'check_out_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['birth_date', 'gender', 'address', 'hometown', 'job_position']
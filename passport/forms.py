from django import forms
from .models import PassportRequest

class PassportRequestForm(forms.ModelForm):
    class Meta:
        model = PassportRequest
        fields = ['full_name','email', 'phone_number', 'cccd', 'address', 'gender', 'current_passport_number']

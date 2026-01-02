from django import forms
from .models import Order, NukeRequest, PollinationRequest, BeeRemovalRequest, CallbackRequest


class OrderForm(forms.ModelForm):
    """Form for placing honey orders"""
    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'address', 'city', 'state', 'zip_code',
            'product', 'quantity', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions or notes (optional)'}),
        }


class NukeRequestForm(forms.ModelForm):
    """Form for submitting nuc (bee starter kit) requests"""
    class Meta:
        model = NukeRequest
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'address', 'city', 'state', 'zip_code',
            'quantity', 'experience_level', 'preferred_pickup_date', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'preferred_pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your beekeeping experience and any questions you have'}),
        }


class PollinationRequestForm(forms.ModelForm):
    """Form for submitting pollination service requests"""
    class Meta:
        model = PollinationRequest
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'property_address', 'city', 'state', 'zip_code',
            'crop_type', 'crop_type_other', 'acreage', 'num_hives_requested',
            'preferred_start_date', 'duration_weeks', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address where pollination is needed'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FL', 'value': 'FL'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'crop_type': forms.Select(attrs={'class': 'form-control'}),
            'crop_type_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify crop type'}),
            'acreage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0.1, 'step': 0.1, 'placeholder': 'Acres'}),
            'num_hives_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Leave blank if unsure'}),
            'preferred_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your pollination needs, any specific requirements, or questions'}),
        }


class BeeRemovalRequestForm(forms.ModelForm):
    """Form for submitting bee removal/relocation requests"""
    class Meta:
        model = BeeRemovalRequest
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'property_address', 'city', 'state', 'zip_code', 'property_type',
            'bee_location', 'bee_location_other', 'how_long_present',
            'estimated_size', 'height_from_ground', 'urgency',
            'has_been_sprayed', 'can_send_photo', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Address where bees are located'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FL', 'value': 'FL'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'bee_location': forms.Select(attrs={'class': 'form-control'}),
            'bee_location_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please describe location'}),
            'how_long_present': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Just noticed today, 1 week, Several months'}),
            'estimated_size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., softball size, basketball size'}),
            'height_from_ground': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 6 feet, ground level'}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'has_been_sprayed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_send_photo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Any additional information that might help us assess the situation'}),
        }


class CallbackRequestForm(forms.ModelForm):
    """Simple form for requesting a callback"""
    class Meta:
        model = CallbackRequest
        fields = ['name', 'phone', 'email', 'interest', 'best_time', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 123-4567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com (optional)'}),
            'interest': forms.Select(attrs={'class': 'form-control'}),
            'best_time': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mornings, After 5pm, Weekends'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any details you\'d like to share (optional)'}),
        }

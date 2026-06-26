import re

from django import forms
from django.core.exceptions import ValidationError

from .models import BeeRemovalRequest, CallbackRequest, NukeRequest, Order, PollinationRequest, Product


def _normalize_phone(value):
    """Accept any common US phone format, return (XXX) XXX-XXXX."""
    digits = re.sub(r'\D', '', value)
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise ValidationError(
            'Please enter a valid 10-digit US phone number, e.g. (850) 555-1234.'
        )
    return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'


class ContactValidationMixin:
    """Shared phone normalization and email lowercasing for all contact forms."""

    def clean_phone(self):
        return _normalize_phone(self.cleaned_data.get('phone', ''))

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


MAX_SELF_SERVE_QUANTITY = 24


class OrderForm(ContactValidationMixin, forms.ModelForm):
    """Form for placing honey orders"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer products that are currently for sale; this stays in sync as
        # the catalog changes (retired items have in_stock=False).
        self.fields['product'].queryset = Product.objects.filter(in_stock=True)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity > MAX_SELF_SERVE_QUANTITY:
            raise ValidationError(
                f'For orders of more than {MAX_SELF_SERVE_QUANTITY} jars, please request a '
                f'callback so we can arrange bulk pricing and delivery.'
            )
        return quantity

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'address', 'city', 'state', 'zip_code',
            'product', 'quantity', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(850) 555-1234', 'autocomplete': 'tel'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123 Main St', 'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'autocomplete': 'address-level1'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code', 'autocomplete': 'postal-code', 'maxlength': 10}),
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': MAX_SELF_SERVE_QUANTITY, 'value': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any special instructions or notes (optional)'}),
        }


class NukeRequestForm(ContactValidationMixin, forms.ModelForm):
    """Form for submitting nuc (bee starter kit) requests"""
    class Meta:
        model = NukeRequest
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'prefer_callback',
            'address', 'city', 'state', 'zip_code',
            'quantity', 'experience_level', 'preferred_pickup_date', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(850) 555-1234', 'autocomplete': 'tel'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123 Main St', 'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State', 'autocomplete': 'address-level1'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code', 'autocomplete': 'postal-code', 'maxlength': 10}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'preferred_pickup_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your beekeeping experience and any questions you have'}),
        }


class PollinationRequestForm(ContactValidationMixin, forms.ModelForm):
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
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(850) 555-1234', 'autocomplete': 'tel'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address where pollination is needed', 'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FL', 'value': 'FL', 'autocomplete': 'address-level1'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'crop_type': forms.Select(attrs={'class': 'form-control'}),
            'crop_type_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Please specify crop type'}),
            'acreage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0.1, 'step': 0.1, 'placeholder': 'Acres'}),
            'num_hives_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Leave blank if unsure'}),
            'preferred_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your pollination needs, any specific requirements, or questions'}),
        }


class BeeRemovalRequestForm(ContactValidationMixin, forms.ModelForm):
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
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your.email@example.com', 'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(850) 555-1234', 'autocomplete': 'tel'}),
            'prefer_callback': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'property_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address where bees are located', 'autocomplete': 'street-address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'autocomplete': 'address-level2'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FL', 'value': 'FL', 'autocomplete': 'address-level1'}),
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


class CallbackRequestForm(ContactValidationMixin, forms.ModelForm):
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

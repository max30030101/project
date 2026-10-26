from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "phone", "address_line", "city", "state", "pincode"]
        labels = {"address_line": "Address", "pincode": "PIN code"}

from django import forms

from .models import Order, Product, ReturnRequest


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "stock", "image", "image_url", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["full_name", "phone", "address", "payment_method"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class ReturnForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ["reason"]
        widgets = {"reason": forms.Textarea(attrs={"rows": 3, "placeholder": "Why do you want to return this item?"})}


class CommissionForm(forms.Form):
    commission_rate = forms.DecimalField(min_value=0, max_value=100, decimal_places=2)

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import SellerProfile, User


class RegisterForm(UserCreationForm):
    ROLE_CHOICES = [(User.CUSTOMER, "Customer - I want to buy"), (User.SELLER, "Seller - I want to sell")]
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial=User.CUSTOMER)
    store_name = forms.CharField(max_length=100, required=False, label="Store name (sellers only)")
    store_description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False,
                                        label="About your store (sellers only)")

    class Meta:
        model = User
        fields = ("username", "email", "phone", "role", "password1", "password2")

    def clean(self):
        data = super().clean()
        if data.get("role") == User.SELLER and not data.get("store_name"):
            self.add_error("store_name", "Store name is required for sellers.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
            if user.role == User.SELLER:
                SellerProfile.objects.create(
                    user=user,
                    store_name=self.cleaned_data["store_name"],
                    description=self.cleaned_data.get("store_description", ""),
                )
        return user

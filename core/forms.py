from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    """
    Custom signup form with Bengali labels.
    Inherits from Django's UserCreationForm (username + password1 + password2).
    """
    email = forms.EmailField(
        required=True,
        label="ইমেইল",
        widget=forms.EmailInput(attrs={
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "you@example.com",
        }),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ইউজারনেম"
        self.fields["username"].widget.attrs.update({
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "যেমন: rahim",
        })
        self.fields["password1"].label = "পাসওয়ার্ড"
        self.fields["password1"].widget.attrs.update({
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
        })
        self.fields["password2"].label = "পাসওয়ার্ড নিশ্চিত করো"
        self.fields["password2"].widget.attrs.update({
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
        })


class LoginForm(AuthenticationForm):
    """
    Custom login form with Tailwind styling and Bengali labels.
    """
    username = forms.CharField(
        label="ইউজারনেম",
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "তোমার ইউজারনেম",
        }),
    )
    password = forms.CharField(
        label="পাসওয়ার্ড",
        widget=forms.PasswordInput(attrs={
            "class": "w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500",
            "placeholder": "তোমার পাসওয়ার্ড",
        }),
    )
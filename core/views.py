from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import SignupForm, LoginForm
from .models import ChatSession


def home(request):
    """
    Landing page. If the user is logged in, show their sessions.
    Otherwise show the welcome page.
    """
    sessions = []
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(user=request.user)[:10]

    return render(request, "core/home.html", {"sessions": sessions})


def signup_view(request):
    """
    Handle user registration. On success, log the user in and redirect home.
    """
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"স্বাগতম, {user.username}! অ্যাকাউন্ট তৈরি হয়েছে।")
            return redirect("core:home")
    else:
        form = SignupForm()

    return render(request, "core/signup.html", {"form": form})


def login_view(request):
    """
    Handle user login. Uses Django's AuthenticationForm.
    """
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"স্বাগতম, {user.username}!")
            return redirect("core:home")
    else:
        form = LoginForm(request)

    return render(request, "core/login.html", {"form": form})


def logout_view(request):
    """
    Log the user out and redirect home.
    """
    logout(request)
    messages.info(request, "তুমি logout করেছ।")
    return redirect("core:home")


@login_required
def dashboard_view(request):
    """
    A protected page — only for logged-in users.
    Shows all sessions of the user.
    """
    sessions = ChatSession.objects.filter(user=request.user)
    return render(request, "core/dashboard.html", {"sessions": sessions})
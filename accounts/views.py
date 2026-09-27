from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        if not user.is_active:
            form.add_error(
                None,
                "Your account is inactive. Please contact an administrator.",
            )
        else:
            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.get_full_name() or user.username}.",
            )

            return redirect(
                request.GET.get("next") or "dashboard:index"
            )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username

        logout(request)

        messages.success(
            request,
            f"Goodbye, {username}. You have been logged out successfully.",
        )

    return redirect("accounts:login")
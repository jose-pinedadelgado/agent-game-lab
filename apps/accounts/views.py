from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import ProfileSettingsForm


@login_required
def profile(request):
    """User profile page with budgeting settings."""
    if request.method == 'POST':
        form = ProfileSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully.')
            return redirect('accounts:profile')
    else:
        form = ProfileSettingsForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

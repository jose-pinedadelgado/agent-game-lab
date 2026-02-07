from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

from .models import BudgetCategory, SpendingAlert
from .forms import BudgetCategoryForm
from apps.transactions.models import Transaction


@login_required
def manage_categories(request):
    """Display and manage budget categories with spending progress."""
    categories = BudgetCategory.objects.filter(user=request.user, is_active=True)

    # Calculate current month spending for each category
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    category_data = []
    for category in categories:
        spent = Transaction.objects.filter(
            user=request.user,
            category=category,
            date__gte=month_start.date()
        ).aggregate(total=Sum('amount'))['total'] or 0

        percentage = (float(spent) / float(category.monthly_limit) * 100) if category.monthly_limit else 0

        category_data.append({
            'category': category,
            'spent': spent,
            'remaining': category.monthly_limit - spent,
            'percentage': min(percentage, 100),
            'over_budget': percentage > 100,
            'status_class': 'success' if percentage < 80 else ('warning' if percentage < 100 else 'danger'),
        })

    return render(request, 'budgets/manage.html', {
        'category_data': category_data,
        'month_name': now.strftime('%B %Y')
    })


@login_required
def create_category(request):
    """Create a new budget category."""
    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST, user=request.user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully.')
            return redirect('budgets:manage')
    else:
        form = BudgetCategoryForm(user=request.user)

    return render(request, 'budgets/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'user': request.user,
    })


@login_required
def edit_category(request, pk):
    """Edit an existing budget category."""
    category = get_object_or_404(BudgetCategory, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BudgetCategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
            return redirect('budgets:manage')
    else:
        form = BudgetCategoryForm(instance=category, user=request.user)

    return render(request, 'budgets/category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'user': request.user,
    })


@login_required
def delete_category(request, pk):
    """Delete a budget category (moves transactions to 'Other')."""
    category = get_object_or_404(BudgetCategory, pk=pk, user=request.user)

    # Prevent deleting 'Other' category
    if category.name == 'Other':
        messages.error(request, 'Cannot delete the "Other" category.')
        return redirect('budgets:manage')

    if request.method == 'POST':
        # Move transactions to 'Other'
        other_category, _ = BudgetCategory.objects.get_or_create(
            user=request.user,
            name='Other',
            defaults={'monthly_limit': 500, 'color': '#9CA3AF'}
        )
        Transaction.objects.filter(category=category).update(category=other_category)

        category.delete()
        messages.success(request, f'Category deleted. Transactions moved to "Other".')
        return redirect('budgets:manage')

    return render(request, 'budgets/confirm_delete.html', {'category': category})


@login_required
def alerts(request):
    """Display spending alerts."""
    alerts = SpendingAlert.objects.filter(user=request.user, is_dismissed=False)

    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        action = request.POST.get('action')

        if alert_id:
            alert = get_object_or_404(SpendingAlert, pk=alert_id, user=request.user)
            if action == 'read':
                alert.is_read = True
                alert.save()
            elif action == 'dismiss':
                alert.is_dismissed = True
                alert.save()

    return render(request, 'budgets/alerts.html', {'alerts': alerts})

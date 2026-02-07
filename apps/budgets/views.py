from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime
from decimal import Decimal

from .models import (
    BudgetCategory, BudgetSection, SpendingAlert,
    Debt, DebtPayment, SavingsGoal, SavingsContribution, GoalType
)
from .forms import (
    BudgetCategoryForm, DebtForm, DebtPaymentForm,
    SavingsGoalForm, SavingsContributionForm
)
from apps.transactions.models import Transaction


def _get_category_spending(user, categories):
    """Calculate current month spending for categories."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    category_data = []
    for category in categories:
        spent = Transaction.objects.filter(
            user=user,
            category=category,
            date__gte=month_start.date()
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        percentage = (float(spent) / float(category.monthly_limit) * 100) if category.monthly_limit else 0

        category_data.append({
            'category': category,
            'spent': spent,
            'remaining': category.monthly_limit - spent,
            'percentage': min(percentage, 100),
            'over_budget': percentage > 100,
            'status_class': 'success' if percentage < 80 else ('warning' if percentage < 100 else 'danger'),
        })

    return category_data


# ==============================================================================
# BUDGET OVERVIEW (redirects to expenses)
# ==============================================================================

@login_required
def budget_overview(request):
    """Redirect to expenses tab."""
    return redirect('budgets:expenses')


# ==============================================================================
# EXPENSES TAB
# ==============================================================================

@login_required
def expenses_tab(request):
    """Display expenses tab with fixed and variable sections."""
    fixed_categories = BudgetCategory.objects.filter(
        user=request.user, is_active=True, section=BudgetSection.FIXED
    ).order_by('display_order', 'name')

    variable_categories = BudgetCategory.objects.filter(
        user=request.user, is_active=True, section=BudgetSection.VARIABLE
    ).order_by('display_order', 'name')

    fixed_data = _get_category_spending(request.user, fixed_categories)
    variable_data = _get_category_spending(request.user, variable_categories)

    # Calculate totals
    fixed_total = sum(c.monthly_limit for c in fixed_categories)
    variable_total = sum(c.monthly_limit for c in variable_categories)
    total_budget = fixed_total + variable_total
    total_spent = sum(item['spent'] for item in fixed_data + variable_data)
    total_remaining = total_budget - total_spent

    now = timezone.now()

    return render(request, 'budgets/expenses/tab.html', {
        'active_tab': 'expenses',
        'fixed_categories': fixed_data,
        'variable_categories': variable_data,
        'fixed_total': fixed_total,
        'variable_total': variable_total,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'month_name': now.strftime('%B %Y'),
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
            return redirect('budgets:expenses')
    else:
        form = BudgetCategoryForm(user=request.user)

    return render(request, 'budgets/expenses/category_form.html', {
        'form': form,
        'title': 'Create Category',
        'user': request.user,
        'active_tab': 'expenses',
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
            return redirect('budgets:expenses')
    else:
        form = BudgetCategoryForm(instance=category, user=request.user)

    return render(request, 'budgets/expenses/category_form.html', {
        'form': form,
        'category': category,
        'title': 'Edit Category',
        'user': request.user,
        'active_tab': 'expenses',
    })


@login_required
def delete_category(request, pk):
    """Delete a budget category (moves transactions to 'Other')."""
    category = get_object_or_404(BudgetCategory, pk=pk, user=request.user)

    # Prevent deleting 'Other' category
    if category.name == 'Other':
        messages.error(request, 'Cannot delete the "Other" category.')
        return redirect('budgets:expenses')

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
        return redirect('budgets:expenses')

    return render(request, 'budgets/expenses/confirm_delete.html', {
        'category': category,
        'active_tab': 'expenses',
    })


# ==============================================================================
# DEBT TAB
# ==============================================================================

@login_required
def debt_tab(request):
    """Display debt payoff tab."""
    debts = Debt.objects.filter(user=request.user, is_active=True)

    # Order by user's strategy
    strategy = request.user.debt_payoff_strategy
    if strategy == 'avalanche':
        debts = debts.order_by('-interest_rate', 'current_balance')
    else:  # snowball
        debts = debts.order_by('current_balance', '-interest_rate')

    # Calculate totals
    total_debt = sum(d.current_balance for d in debts)
    total_original = sum(d.original_balance for d in debts)
    total_paid = total_original - total_debt
    total_minimum = sum(d.minimum_payment for d in debts)
    total_extra = sum(d.extra_payment for d in debts)

    return render(request, 'budgets/debt/tab.html', {
        'active_tab': 'debt',
        'debts': debts,
        'strategy': strategy,
        'total_debt': total_debt,
        'total_original': total_original,
        'total_paid': total_paid,
        'total_minimum': total_minimum,
        'total_extra': total_extra,
        'overall_percentage': (float(total_paid) / float(total_original) * 100) if total_original else 0,
    })


@login_required
def add_debt(request):
    """Add a new debt."""
    if request.method == 'POST':
        form = DebtForm(request.POST, user=request.user)
        if form.is_valid():
            debt = form.save(commit=False)
            debt.user = request.user
            debt.save()
            messages.success(request, f'Debt "{debt.name}" added successfully.')
            return redirect('budgets:debt')
    else:
        form = DebtForm(user=request.user)

    return render(request, 'budgets/debt/form.html', {
        'form': form,
        'title': 'Add Debt',
        'active_tab': 'debt',
    })


@login_required
def edit_debt(request, pk):
    """Edit an existing debt."""
    debt = get_object_or_404(Debt, pk=pk, user=request.user)

    if request.method == 'POST':
        form = DebtForm(request.POST, instance=debt, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Debt "{debt.name}" updated successfully.')
            return redirect('budgets:debt')
    else:
        form = DebtForm(instance=debt, user=request.user)

    return render(request, 'budgets/debt/form.html', {
        'form': form,
        'debt': debt,
        'title': 'Edit Debt',
        'active_tab': 'debt',
    })


@login_required
def debt_detail(request, pk):
    """View debt details and payment history."""
    debt = get_object_or_404(Debt, pk=pk, user=request.user)
    payments = debt.payments.all()[:20]

    return render(request, 'budgets/debt/detail.html', {
        'debt': debt,
        'payments': payments,
        'active_tab': 'debt',
    })


@login_required
def record_debt_payment(request, pk):
    """Record a payment toward a debt."""
    debt = get_object_or_404(Debt, pk=pk, user=request.user)

    if request.method == 'POST':
        form = DebtPaymentForm(request.POST, debt=debt, user=request.user)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.debt = debt

            # Update debt balance
            debt.current_balance = max(Decimal('0'), debt.current_balance - payment.amount)
            payment.balance_after = debt.current_balance
            debt.save()
            payment.save()

            messages.success(request, f'Payment of ${payment.amount} recorded.')
            return redirect('budgets:debt_detail', pk=debt.pk)
    else:
        from datetime import date
        form = DebtPaymentForm(
            debt=debt,
            user=request.user,
            initial={'payment_date': date.today(), 'amount': debt.total_monthly_payment}
        )

    return render(request, 'budgets/debt/payment_form.html', {
        'form': form,
        'debt': debt,
        'active_tab': 'debt',
    })


@login_required
def delete_debt(request, pk):
    """Delete a debt."""
    debt = get_object_or_404(Debt, pk=pk, user=request.user)

    if request.method == 'POST':
        name = debt.name
        debt.delete()
        messages.success(request, f'Debt "{name}" deleted.')
        return redirect('budgets:debt')

    return render(request, 'budgets/debt/confirm_delete.html', {
        'debt': debt,
        'active_tab': 'debt',
    })


@login_required
def toggle_debt_strategy(request):
    """Toggle between avalanche and snowball strategies."""
    if request.method == 'POST':
        user = request.user
        if user.debt_payoff_strategy == 'avalanche':
            user.debt_payoff_strategy = 'snowball'
        else:
            user.debt_payoff_strategy = 'avalanche'
        user.save()
        messages.info(request, f'Switched to {user.get_debt_payoff_strategy_display()} strategy.')
    return redirect('budgets:debt')


# ==============================================================================
# SAVINGS TAB
# ==============================================================================

@login_required
def savings_tab(request):
    """Display savings and investments tab."""
    goals = SavingsGoal.objects.filter(user=request.user, is_active=True)

    # Separate into sections
    retirement_goals = [g for g in goals if g.is_retirement or g.goal_type == GoalType.RETIREMENT]
    investment_goals = [g for g in goals if g.goal_type == GoalType.INVESTMENT and not g.is_retirement]
    general_goals = [g for g in goals if g.goal_type not in [GoalType.RETIREMENT, GoalType.INVESTMENT] and not g.is_retirement]

    # Calculate totals
    total_saved = sum(g.current_amount for g in goals)
    total_target = sum(g.target_amount for g in goals)
    monthly_contributions = sum(g.monthly_contribution for g in goals)

    return render(request, 'budgets/savings/tab.html', {
        'active_tab': 'savings',
        'retirement_goals': retirement_goals,
        'investment_goals': investment_goals,
        'general_goals': general_goals,
        'total_saved': total_saved,
        'total_target': total_target,
        'monthly_contributions': monthly_contributions,
        'overall_percentage': (float(total_saved) / float(total_target) * 100) if total_target else 0,
    })


@login_required
def create_savings_goal(request):
    """Create a new savings goal."""
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, user=request.user)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, f'Goal "{goal.name}" created successfully.')
            return redirect('budgets:savings')
    else:
        form = SavingsGoalForm(user=request.user)

    return render(request, 'budgets/savings/goal_form.html', {
        'form': form,
        'title': 'Create Goal',
        'active_tab': 'savings',
    })


@login_required
def edit_savings_goal(request, pk):
    """Edit an existing savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SavingsGoalForm(request.POST, instance=goal, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Goal "{goal.name}" updated successfully.')
            return redirect('budgets:savings')
    else:
        form = SavingsGoalForm(instance=goal, user=request.user)

    return render(request, 'budgets/savings/goal_form.html', {
        'form': form,
        'goal': goal,
        'title': 'Edit Goal',
        'active_tab': 'savings',
    })


@login_required
def savings_goal_detail(request, pk):
    """View goal details and contribution history."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)
    contributions = goal.contributions.all()[:20]

    return render(request, 'budgets/savings/goal_detail.html', {
        'goal': goal,
        'contributions': contributions,
        'active_tab': 'savings',
    })


@login_required
def record_contribution(request, pk):
    """Record a contribution to a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SavingsContributionForm(request.POST, goal=goal, user=request.user)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal

            # Update goal balance
            goal.current_amount = goal.current_amount + contribution.amount
            contribution.balance_after = goal.current_amount
            goal.save()
            contribution.save()

            messages.success(request, f'Contribution of ${contribution.amount} recorded.')
            return redirect('budgets:goal_detail', pk=goal.pk)
    else:
        from datetime import date
        form = SavingsContributionForm(
            goal=goal,
            user=request.user,
            initial={'contribution_date': date.today(), 'amount': goal.monthly_contribution}
        )

    return render(request, 'budgets/savings/contribution_form.html', {
        'form': form,
        'goal': goal,
        'active_tab': 'savings',
    })


@login_required
def delete_savings_goal(request, pk):
    """Delete a savings goal."""
    goal = get_object_or_404(SavingsGoal, pk=pk, user=request.user)

    if request.method == 'POST':
        name = goal.name
        goal.delete()
        messages.success(request, f'Goal "{name}" deleted.')
        return redirect('budgets:savings')

    return render(request, 'budgets/savings/confirm_delete.html', {
        'goal': goal,
        'active_tab': 'savings',
    })


# ==============================================================================
# LEGACY SUPPORT - keep manage_categories working
# ==============================================================================

@login_required
def manage_categories(request):
    """Legacy view - redirects to expenses tab."""
    return redirect('budgets:expenses')


# ==============================================================================
# ALERTS
# ==============================================================================

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

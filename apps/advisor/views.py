from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta

from apps.transactions.models import Transaction
from apps.budgets.models import BudgetCategory


@login_required
def insights(request):
    """AI-powered spending insights page."""
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Current month transactions
    current_month_txns = Transaction.objects.filter(
        user=request.user,
        date__gte=month_start.date()
    )

    # Last month transactions
    last_month_txns = Transaction.objects.filter(
        user=request.user,
        date__gte=last_month_start.date(),
        date__lt=month_start.date()
    )

    # Generate basic insights
    insights = []

    # 1. Month-over-month comparison
    current_total = current_month_txns.aggregate(total=Sum('amount'))['total'] or 0
    last_total = last_month_txns.aggregate(total=Sum('amount'))['total'] or 0

    if last_total > 0:
        change_pct = ((float(current_total) - float(last_total)) / float(last_total)) * 100
        if change_pct > 10:
            insights.append({
                'type': 'warning',
                'icon': 'trending-up',
                'title': 'Spending Increase',
                'message': f'Your spending is up {abs(change_pct):.0f}% compared to last month. Consider reviewing your recent purchases.',
            })
        elif change_pct < -10:
            insights.append({
                'type': 'success',
                'icon': 'trending-down',
                'title': 'Great Progress!',
                'message': f'Your spending is down {abs(change_pct):.0f}% compared to last month. Keep up the good work!',
            })

    # 2. Top spending category
    top_category = current_month_txns.values(
        'category__name'
    ).annotate(total=Sum('amount')).order_by('-total').first()

    if top_category and top_category['category__name']:
        insights.append({
            'type': 'info',
            'icon': 'pie-chart',
            'title': 'Top Spending Category',
            'message': f'You\'ve spent the most on {top_category["category__name"]} this month (${top_category["total"]:.2f}).',
        })

    # 3. Large transactions
    large_txns = current_month_txns.filter(amount__gte=100).count()
    if large_txns > 0:
        insights.append({
            'type': 'info',
            'icon': 'alert-circle',
            'title': 'Large Transactions',
            'message': f'You have {large_txns} transaction(s) over $100 this month.',
        })

    # 4. Budget status
    categories = BudgetCategory.objects.filter(user=request.user, is_active=True)
    over_budget_count = 0
    for category in categories:
        spent = current_month_txns.filter(category=category).aggregate(total=Sum('amount'))['total'] or 0
        if float(spent) > float(category.monthly_limit):
            over_budget_count += 1

    if over_budget_count > 0:
        insights.append({
            'type': 'danger',
            'icon': 'alert-triangle',
            'title': 'Budget Alert',
            'message': f'You are over budget in {over_budget_count} category(ies). Review your spending to get back on track.',
        })
    elif categories.exists():
        insights.append({
            'type': 'success',
            'icon': 'check-circle',
            'title': 'On Track',
            'message': 'You\'re staying within your budget limits. Great job!',
        })

    # 5. Average transaction
    avg_amount = current_month_txns.aggregate(avg=Avg('amount'))['avg']
    if avg_amount:
        insights.append({
            'type': 'info',
            'icon': 'credit-card',
            'title': 'Average Transaction',
            'message': f'Your average transaction this month is ${avg_amount:.2f}.',
        })

    context = {
        'insights': insights,
        'current_total': current_total,
        'last_total': last_total,
        'month_name': now.strftime('%B %Y'),
    }

    return render(request, 'advisor/insights.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import calendar

from apps.transactions.models import Transaction
from apps.budgets.models import BudgetCategory, SpendingAlert
from apps.statements.models import CreditCardStatement


@login_required
def dashboard(request):
    """Main dashboard with spending overview."""
    now = timezone.now()

    # Get month/year from query params, default to current
    try:
        selected_year = int(request.GET.get('year', now.year))
        selected_month = int(request.GET.get('month', now.month))
        # Validate ranges
        if not (1 <= selected_month <= 12):
            selected_month = now.month
        if not (2020 <= selected_year <= now.year + 1):
            selected_year = now.year
    except (ValueError, TypeError):
        selected_year = now.year
        selected_month = now.month

    # Calculate month date range
    month_start = timezone.datetime(selected_year, selected_month, 1).date()
    _, last_day = calendar.monthrange(selected_year, selected_month)
    month_end = timezone.datetime(selected_year, selected_month, last_day).date()

    # Get selected month transactions
    transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=month_end
    )

    # Get available months for the selector (months that have transactions)
    available_months = Transaction.objects.filter(
        user=request.user
    ).annotate(
        month=TruncMonth('date')
    ).values('month').distinct().order_by('-month')
    available_months = [m['month'] for m in available_months if m['month']]

    # Summary metrics
    total_spent = transactions.aggregate(total=Sum('amount'))['total'] or 0
    transaction_count = transactions.count()

    # Top category
    top_category = transactions.values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total').first()

    # Spending by category for chart
    spending_by_category = list(transactions.values(
        'category__name', 'category__color'
    ).annotate(total=Sum('amount')).order_by('-total'))

    # Recent transactions for selected month
    recent_transactions = Transaction.objects.filter(
        user=request.user,
        date__gte=month_start,
        date__lte=month_end
    ).select_related('category')[:5]

    # Budget categories with progress
    categories = BudgetCategory.objects.filter(user=request.user, is_active=True)
    category_progress = []
    total_budget = 0
    total_category_spent = 0

    for category in categories:
        spent = transactions.filter(category=category).aggregate(total=Sum('amount'))['total'] or 0
        percentage = (float(spent) / float(category.monthly_limit) * 100) if category.monthly_limit else 0
        total_budget += float(category.monthly_limit)
        total_category_spent += float(spent)

        category_progress.append({
            'category': category,
            'spent': spent,
            'percentage': min(percentage, 100),
            'status_class': 'success' if percentage < 80 else ('warning' if percentage < 100 else 'danger'),
        })

    # Budget health (percentage of total budget remaining)
    budget_health = 100 - (total_category_spent / total_budget * 100) if total_budget else 100

    # Unread alerts count
    unread_alerts = SpendingAlert.objects.filter(
        user=request.user, is_read=False, is_dismissed=False
    ).count()

    # Build month/year options for selector
    current_year = now.year
    years = list(range(current_year - 5, current_year + 1))
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    context = {
        'total_spent': total_spent,
        'transaction_count': transaction_count,
        'top_category': top_category,
        'budget_health': max(0, budget_health),
        'spending_by_category': spending_by_category,
        'recent_transactions': recent_transactions,
        'category_progress': category_progress,
        'month_name': f'{calendar.month_name[selected_month]} {selected_year}',
        'unread_alerts': unread_alerts,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'years': years,
        'months': months,
        'available_months': available_months,
    }

    return render(request, 'analytics/dashboard.html', context)


@login_required
def trends(request):
    """Spending trends over time."""
    return render(request, 'analytics/trends.html')


@login_required
def api_spending_by_category(request):
    """API endpoint for spending by category chart data."""
    now = timezone.now()
    month_start = now.replace(day=1)

    data = Transaction.objects.filter(
        user=request.user,
        date__gte=month_start.date()
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')

    return JsonResponse({
        'labels': [d['category__name'] or 'Uncategorized' for d in data],
        'values': [float(d['total']) for d in data],
        'colors': [d['category__color'] or '#9CA3AF' for d in data],
    })


@login_required
def api_monthly_trends(request):
    """API endpoint for monthly spending trends."""
    six_months_ago = timezone.now() - timedelta(days=180)

    data = Transaction.objects.filter(
        user=request.user,
        date__gte=six_months_ago.date()
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    return JsonResponse({
        'labels': [d['month'].strftime('%b %Y') for d in data],
        'values': [float(d['total']) for d in data],
        'counts': [d['count'] for d in data],
    })

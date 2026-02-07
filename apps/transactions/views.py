from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import Transaction, TransactionStatus
from apps.budgets.models import BudgetCategory, SpendingType, CSPBucket
from apps.accounts_financial.models import Account


@login_required
def transaction_list(request):
    """Display paginated list of user transactions with filters."""
    transactions = Transaction.objects.filter(user=request.user).select_related(
        'category', 'statement', 'account', 'transfer_pair__account'
    )

    # Apply filters
    category_id = request.GET.get('category')
    if category_id:
        transactions = transactions.filter(category_id=category_id)

    account_id = request.GET.get('account')
    if account_id:
        transactions = transactions.filter(account_id=account_id)

    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)

    search = request.GET.get('search')
    if search:
        transactions = transactions.filter(description__icontains=search)

    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = BudgetCategory.objects.filter(user=request.user)
    accounts = Account.objects.filter(user=request.user, is_active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'accounts': accounts,
        'current_category': category_id,
        'current_account': account_id,
        'current_status': status,
        'search': search or '',
        'status_choices': TransactionStatus.choices,
    }

    # Return partial for HTMX requests
    if request.htmx:
        return render(request, 'transactions/partials/_transaction_list.html', context)

    return render(request, 'transactions/list.html', context)


@login_required
def transaction_detail(request, pk):
    """Display single transaction details."""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    categories = BudgetCategory.objects.filter(user=request.user)
    return render(request, 'transactions/detail.html', {
        'transaction': transaction,
        'categories': categories,
        'spending_types': SpendingType.choices,
        'csp_buckets': CSPBucket.choices,
        'enable_wants_needs': request.user.enable_wants_needs,
        'enable_conscious_spending': request.user.enable_conscious_spending,
    })


@login_required
def update_category(request, pk):
    """Update transaction category (HTMX endpoint)."""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    old_category = transaction.category

    if request.method == 'POST':
        category_id = request.POST.get('category')
        if category_id:
            category = get_object_or_404(BudgetCategory, pk=category_id, user=request.user)
            transaction.category = category
            transaction.user_confirmed = True
            transaction.save()

            # Record user correction for training if category changed
            if old_category != category:
                from apps.categorization.models import CategoryAssignment
                CategoryAssignment.objects.create(
                    transaction=transaction,
                    user=request.user,
                    category_name=category.name,
                    category=category,
                    source=CategoryAssignment.Source.USER_CORRECTION,
                    transaction_description=transaction.description,
                    transaction_merchant=transaction.merchant,
                    transaction_amount=transaction.amount,
                )

    categories = BudgetCategory.objects.filter(user=request.user)

    return render(request, 'transactions/partials/_category_select.html', {
        'transaction': transaction,
        'categories': categories
    })


@login_required
def update_spending_override(request, pk):
    """Update transaction spending type or CSP bucket override (HTMX endpoint)."""
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        # Update spending type override
        if 'spending_type' in request.POST:
            value = request.POST.get('spending_type')
            transaction.spending_type_override = value if value else None
            transaction.save(update_fields=['spending_type_override', 'updated_at'])

        # Update CSP bucket override
        if 'csp_bucket' in request.POST:
            value = request.POST.get('csp_bucket')
            transaction.csp_bucket_override = value if value else None
            transaction.save(update_fields=['csp_bucket_override', 'updated_at'])

    return render(request, 'transactions/partials/_spending_overrides.html', {
        'transaction': transaction,
        'spending_types': SpendingType.choices,
        'csp_buckets': CSPBucket.choices,
        'enable_wants_needs': request.user.enable_wants_needs,
        'enable_conscious_spending': request.user.enable_conscious_spending,
    })

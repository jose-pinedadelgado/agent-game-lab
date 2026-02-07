import json
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Max

from .models import Account, AccountBalanceSnapshot
from .forms import AccountForm, BalanceSnapshotForm, TransferForm, CCPaymentForm
from .services import AccountBalanceService, TransferService
from apps.transactions.models import Transaction, TransactionStatus


@login_required
def account_list(request):
    """Display all accounts with net worth summary."""
    accounts = Account.objects.filter(user=request.user).annotate(
        transaction_count=Count('transactions'),
        last_transaction_date=Max('transactions__date')
    )

    balance_service = AccountBalanceService()

    # Calculate balances for each account
    account_data = []
    for account in accounts:
        current_balance = balance_service.get_current_balance(account)
        posted_balance = balance_service.get_posted_balance(account)

        account_data.append({
            'account': account,
            'current_balance': current_balance,
            'posted_balance': posted_balance,
            'has_pending': current_balance != posted_balance,
        })

    # Calculate net worth summary
    net_worth_summary = balance_service.get_net_worth_summary(request.user)

    # Split into active and inactive
    active_accounts = [a for a in account_data if a['account'].is_active]
    inactive_accounts = [a for a in account_data if not a['account'].is_active]

    context = {
        'active_accounts': active_accounts,
        'inactive_accounts': inactive_accounts,
        'net_worth_summary': net_worth_summary,
        'show_inactive': request.GET.get('show_inactive', 'false') == 'true',
    }
    return render(request, 'accounts_financial/list.html', context)


@login_required
def account_detail(request, pk):
    """Display single account with transactions and balance chart."""
    account = get_object_or_404(Account, pk=pk, user=request.user)
    balance_service = AccountBalanceService()

    # Get current balances
    current_balance = balance_service.get_current_balance(account)
    posted_balance = balance_service.get_posted_balance(account)

    # Get transactions for this account
    transactions = Transaction.objects.filter(
        account=account
    ).select_related('category', 'transfer_pair__account').order_by('-date', '-created_at')[:50]

    # Get balance history for chart (last 30 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    balance_history = balance_service.get_balance_history_optimized(
        account, start_date, end_date
    )

    # Calculate spending this month
    first_of_month = date.today().replace(day=1)
    month_transactions = Transaction.objects.filter(
        account=account,
        date__gte=first_of_month,
        transaction_type__in=['purchase', 'withdrawal', 'fee']
    )
    month_spending = sum(t.amount for t in month_transactions)

    # Get recent snapshots
    snapshots = AccountBalanceSnapshot.objects.filter(account=account)[:5]

    context = {
        'account': account,
        'current_balance': current_balance,
        'posted_balance': posted_balance,
        'has_pending': current_balance != posted_balance,
        'transactions': transactions,
        'balance_history_json': json.dumps(balance_history),
        'month_spending': month_spending,
        'transaction_count': transactions.count(),
        'snapshots': snapshots,
    }
    return render(request, 'accounts_financial/detail.html', context)


@login_required
def create_account(request):
    """Create a new financial account."""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            messages.success(request, f'Account "{account.name}" created successfully.')
            return redirect('accounts_financial:detail', pk=account.pk)
    else:
        form = AccountForm()

    context = {
        'form': form,
        'title': 'Create Account',
        'submit_text': 'Create Account',
    }
    return render(request, 'accounts_financial/form.html', context)


@login_required
def edit_account(request, pk):
    """Edit an existing account."""
    account = get_object_or_404(Account, pk=pk, user=request.user)

    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'Account "{account.name}" updated successfully.')
            return redirect('accounts_financial:detail', pk=account.pk)
    else:
        form = AccountForm(instance=account)

    context = {
        'form': form,
        'account': account,
        'title': f'Edit {account.name}',
        'submit_text': 'Save Changes',
    }
    return render(request, 'accounts_financial/form.html', context)


@login_required
def delete_account(request, pk):
    """Delete an account."""
    account = get_object_or_404(Account, pk=pk, user=request.user)

    if request.method == 'POST':
        name = account.name
        account.delete()
        messages.success(request, f'Account "{name}" deleted successfully.')
        return redirect('accounts_financial:list')

    # Get count of related items
    transaction_count = Transaction.objects.filter(account=account).count()
    statement_count = account.statements.count()

    context = {
        'account': account,
        'transaction_count': transaction_count,
        'statement_count': statement_count,
    }
    return render(request, 'accounts_financial/delete.html', context)


@login_required
def add_balance_snapshot(request, pk):
    """Add a manual balance snapshot for reconciliation."""
    account = get_object_or_404(Account, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BalanceSnapshotForm(request.POST)
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.account = account
            snapshot.source = AccountBalanceSnapshot.Source.MANUAL
            snapshot.save()

            # Check for discrepancy
            balance_service = AccountBalanceService()
            reconciliation = balance_service.reconcile_with_snapshot(account, snapshot)

            if reconciliation['is_reconciled']:
                messages.success(request, 'Balance snapshot recorded. Account is reconciled.')
            else:
                discrepancy = reconciliation['discrepancy']
                messages.warning(
                    request,
                    f'Balance snapshot recorded. Discrepancy of ${abs(discrepancy):.2f} detected.'
                )

            return redirect('accounts_financial:detail', pk=account.pk)
    else:
        form = BalanceSnapshotForm(initial={'as_of_date': date.today()})

    # Get current calculated balance
    balance_service = AccountBalanceService()
    current_balance = balance_service.get_current_balance(account)

    context = {
        'form': form,
        'account': account,
        'current_balance': current_balance,
    }
    return render(request, 'accounts_financial/add_balance.html', context)


@login_required
def create_transfer(request):
    """Create a transfer between accounts."""
    if request.method == 'POST':
        form = TransferForm(request.user, request.POST)
        if form.is_valid():
            transfer_service = TransferService()
            from_txn, to_txn = transfer_service.create_transfer(
                from_account=form.cleaned_data['from_account'],
                to_account=form.cleaned_data['to_account'],
                amount=form.cleaned_data['amount'],
                transfer_date=form.cleaned_data['date'],
                description=form.cleaned_data.get('description', ''),
            )
            messages.success(request, 'Transfer created successfully.')
            return redirect('accounts_financial:detail', pk=from_txn.account.pk)
    else:
        form = TransferForm(request.user, initial={'date': date.today()})

    context = {
        'form': form,
        'title': 'Create Transfer',
    }
    return render(request, 'accounts_financial/transfer_form.html', context)


@login_required
def create_cc_payment(request):
    """Create a credit card payment."""
    if request.method == 'POST':
        form = CCPaymentForm(request.user, request.POST)
        if form.is_valid():
            transfer_service = TransferService()
            from_txn, cc_txn = transfer_service.create_cc_payment(
                from_account=form.cleaned_data['from_account'],
                cc_account=form.cleaned_data['cc_account'],
                amount=form.cleaned_data['amount'],
                payment_date=form.cleaned_data['date'],
                description=form.cleaned_data.get('description', ''),
            )
            messages.success(request, 'Credit card payment recorded.')
            return redirect('accounts_financial:detail', pk=form.cleaned_data['cc_account'].pk)
    else:
        form = CCPaymentForm(request.user, initial={'date': date.today()})

    context = {
        'form': form,
        'title': 'Credit Card Payment',
    }
    return render(request, 'accounts_financial/cc_payment_form.html', context)


@login_required
def mark_transaction_posted(request, pk):
    """Mark a pending transaction as posted."""
    transaction = get_object_or_404(Transaction, pk=pk, account__user=request.user)

    if request.method == 'POST':
        transaction.status = TransactionStatus.POSTED
        transaction.save()
        messages.success(request, 'Transaction marked as posted.')

        if transaction.account:
            return redirect('accounts_financial:detail', pk=transaction.account.pk)

    return redirect('transactions:list')


@login_required
def balance_history_api(request, pk):
    """API endpoint for balance history chart data."""
    account = get_object_or_404(Account, pk=pk, user=request.user)

    days = int(request.GET.get('days', 30))
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    balance_service = AccountBalanceService()
    history = balance_service.get_balance_history_optimized(account, start_date, end_date)

    return JsonResponse({'data': history})

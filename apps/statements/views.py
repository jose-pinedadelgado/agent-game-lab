from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import CreditCardStatement
from .forms import StatementUploadForm
from .services.parser import StatementParser
from apps.accounts_financial.models import Account, AccountBalanceSnapshot


@login_required
def upload_statement(request):
    """Handle PDF statement upload."""
    if request.method == 'POST':
        form = StatementUploadForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            statement = form.save(commit=False)
            statement.user = request.user
            statement.original_filename = request.FILES['statement_file'].name

            # Handle account linking
            account = form.cleaned_data.get('account')
            if account:
                statement.account = account
            else:
                # Auto-create account based on bank_name if none selected
                account = auto_create_account_for_statement(request.user, statement.bank_name)
                statement.account = account

            statement.save()

            # Process the statement synchronously for MVP
            # In production, use background task queue
            try:
                process_statement(statement, form.cleaned_data.get('create_balance_snapshot', False))
                messages.success(
                    request,
                    f'Statement processed successfully! {statement.transaction_count} transactions imported.'
                )
            except Exception as e:
                statement.status = CreditCardStatement.Status.FAILED
                statement.error_message = str(e)
                statement.save()
                messages.error(request, f'Error processing statement: {str(e)}')

            return redirect('statements:history')
    else:
        form = StatementUploadForm(request.user)

    return render(request, 'statements/upload.html', {'form': form})


def auto_create_account_for_statement(user, bank_name):
    """Auto-create a credit card account based on bank name."""
    bank_display = dict(CreditCardStatement.Bank.choices).get(bank_name, 'Unknown Bank')

    # Check if an account already exists for this bank
    existing = Account.objects.filter(
        user=user,
        institution__iexact=bank_display,
        account_type=Account.AccountType.CREDIT_CARD,
    ).first()

    if existing:
        return existing

    # Create a new account
    return Account.objects.create(
        user=user,
        name=f"{bank_display} Credit Card",
        account_type=Account.AccountType.CREDIT_CARD,
        institution=bank_display,
        color='#3B82F6',
    )


@login_required
def statement_history(request):
    """Display user's uploaded statements."""
    statements = CreditCardStatement.objects.filter(user=request.user)
    return render(request, 'statements/history.html', {'statements': statements})


@login_required
def delete_statement(request, pk):
    """Delete a statement and its transactions."""
    statement = get_object_or_404(CreditCardStatement, pk=pk, user=request.user)
    if request.method == 'POST':
        statement.delete()
        messages.success(request, 'Statement deleted successfully.')
        return redirect('statements:history')
    return render(request, 'statements/confirm_delete.html', {'statement': statement})


def process_statement(statement, create_balance_snapshot=False):
    """Process an uploaded statement and extract transactions."""
    from apps.transactions.models import Transaction, TransactionType
    from apps.budgets.models import BudgetCategory
    from apps.categorization.services.llm_categorizer import LLMCategorizer
    from apps.categorization.services.base import TransactionData
    from apps.categorization.models import CategoryAssignment

    statement.status = CreditCardStatement.Status.PROCESSING
    statement.save()

    try:
        # Parse PDF
        parser = StatementParser(bank=statement.bank_name)
        extracted = parser.parse(statement.statement_file.path)

        if not extracted:
            raise ValueError('No transactions found in the statement.')

        # Get or create default "Other" category
        default_category, _ = BudgetCategory.objects.get_or_create(
            user=statement.user,
            name='Other',
            defaults={'monthly_limit': 500, 'color': '#9CA3AF'}
        )

        # Get user's valid categories for AI prediction
        user_categories = list(BudgetCategory.objects.filter(
            user=statement.user
        ).values_list('name', flat=True))

        # Get user's past categorization history for context
        user_history = list(CategoryAssignment.objects.filter(
            user=statement.user,
            source__in=[CategoryAssignment.Source.USER_CORRECTION, CategoryAssignment.Source.USER_INITIAL]
        ).values('transaction_description', 'category_name')[:100])

        # Prepare transaction data for categorization
        txn_data = [
            TransactionData(
                description=t.description,
                amount=t.amount,
                merchant=t.merchant or ""
            ) for t in extracted
        ]

        # Get AI predictions
        categorizer = LLMCategorizer()
        predictions = categorizer.categorize_batch(txn_data, user_categories, user_history)

        # Build a lookup for categories by name
        categories_by_name = {
            cat.name: cat for cat in BudgetCategory.objects.filter(user=statement.user)
        }

        # Create transactions with AI predictions
        transactions = []
        for t, pred in zip(extracted, predictions):
            # Find matching category or fall back to default
            category = categories_by_name.get(pred.category_name, default_category)

            transactions.append(Transaction(
                user=statement.user,
                statement=statement,
                account=statement.account,  # Link to financial account
                category=category,
                date=t.date,
                description=t.description,
                amount=t.amount,
                merchant=t.merchant or '',
                transaction_number=t.transaction_number or '',
                transaction_type=TransactionType.PURCHASE,  # Default for CC statements
                ai_category_suggestion=pred.category_name,
                ai_confidence=pred.confidence,
                user_confirmed=False,
            ))

        Transaction.objects.bulk_create(transactions)

        # Record AI predictions for future training
        assignments = []
        for txn, pred in zip(transactions, predictions):
            assignments.append(CategoryAssignment(
                transaction=txn,
                user=statement.user,
                category_name=pred.category_name,
                category=txn.category,
                source=CategoryAssignment.Source.AI_PREDICTION,
                ai_confidence=pred.confidence,
                ai_model_version=categorizer.model_version,
                transaction_description=txn.description,
                transaction_merchant=txn.merchant,
                transaction_amount=txn.amount,
            ))
        CategoryAssignment.objects.bulk_create(assignments)

        # Update statement
        statement.status = CreditCardStatement.Status.COMPLETED
        statement.transaction_count = len(transactions)
        statement.processed_at = timezone.now()
        if extracted:
            dates = [t.date for t in extracted if t.date]
            if dates:
                statement.period_start = min(dates)
                statement.period_end = max(dates)
        statement.save()

        # Create balance snapshot if requested and we have an account
        if create_balance_snapshot and statement.account and statement.period_end:
            # Calculate total from transactions as ending balance
            total_balance = sum(t.amount for t in extracted)
            AccountBalanceSnapshot.objects.create(
                account=statement.account,
                balance=total_balance,
                as_of_date=statement.period_end,
                source=AccountBalanceSnapshot.Source.STATEMENT,
                statement=statement,
                notes=f"Imported from {statement.original_filename}"
            )

    except Exception as e:
        statement.status = CreditCardStatement.Status.FAILED
        statement.error_message = str(e)
        statement.save()
        raise

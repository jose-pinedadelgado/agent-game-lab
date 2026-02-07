from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import CreditCardStatement
from .forms import StatementUploadForm
from .services.parser import StatementParser


@login_required
def upload_statement(request):
    """Handle PDF statement upload."""
    if request.method == 'POST':
        form = StatementUploadForm(request.POST, request.FILES)
        if form.is_valid():
            statement = form.save(commit=False)
            statement.user = request.user
            statement.original_filename = request.FILES['statement_file'].name
            statement.save()

            # Process the statement synchronously for MVP
            # In production, use background task queue
            try:
                process_statement(statement)
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
        form = StatementUploadForm()

    return render(request, 'statements/upload.html', {'form': form})


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


def process_statement(statement):
    """Process an uploaded statement and extract transactions."""
    from apps.transactions.models import Transaction
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
                category=category,
                date=t.date,
                description=t.description,
                amount=t.amount,
                merchant=t.merchant or '',
                transaction_number=t.transaction_number or '',
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

    except Exception as e:
        statement.status = CreditCardStatement.Status.FAILED
        statement.error_message = str(e)
        statement.save()
        raise

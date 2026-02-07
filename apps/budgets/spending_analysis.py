"""
Spending analysis helpers for Wants/Needs and Conscious Spending Plan breakdowns.
"""
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass

from django.db.models import Sum

from apps.transactions.models import Transaction
from .models import SpendingType, CSPBucket


@dataclass
class SpendingBreakdown:
    """Breakdown of spending by category."""
    label: str
    amount: Decimal
    percentage: float
    color: str


@dataclass
class CSPBreakdownItem:
    """Single bucket in Conscious Spending Plan breakdown."""
    label: str
    amount: Decimal
    percentage: float
    target_min: float
    target_max: float
    is_on_target: bool
    color: str


# Colors for spending types
SPENDING_TYPE_COLORS = {
    SpendingType.NEED: '#3B82F6',      # Blue
    SpendingType.WANT: '#F59E0B',       # Amber
    SpendingType.SAVINGS: '#10B981',    # Green
}

# Colors for CSP buckets
CSP_BUCKET_COLORS = {
    CSPBucket.FIXED: '#3B82F6',        # Blue
    CSPBucket.INVESTMENTS: '#10B981',   # Green
    CSPBucket.SAVINGS: '#8B5CF6',       # Purple
    CSPBucket.GUILT_FREE: '#F59E0B',    # Amber
}

# CSP target percentages (min, max)
CSP_TARGETS = {
    CSPBucket.FIXED: (50, 60),
    CSPBucket.INVESTMENTS: (10, 100),  # 10%+ means no upper limit
    CSPBucket.SAVINGS: (5, 15),
    CSPBucket.GUILT_FREE: (20, 35),
}


def calculate_wants_needs_breakdown(
    transactions: List[Transaction],
) -> Dict[str, SpendingBreakdown]:
    """
    Calculate spending breakdown by Wants/Needs/Savings.

    Returns dict with keys 'need', 'want', 'savings' containing SpendingBreakdown.
    """
    totals = {
        SpendingType.NEED: Decimal('0'),
        SpendingType.WANT: Decimal('0'),
        SpendingType.SAVINGS: Decimal('0'),
    }
    uncategorized = Decimal('0')

    for txn in transactions:
        spending_type = txn.spending_type
        if spending_type and spending_type in totals:
            totals[spending_type] += txn.amount
        else:
            uncategorized += txn.amount

    grand_total = sum(totals.values()) + uncategorized

    results = {}
    for spending_type, amount in totals.items():
        percentage = float(amount / grand_total * 100) if grand_total else 0
        results[spending_type] = SpendingBreakdown(
            label=SpendingType(spending_type).label,
            amount=amount,
            percentage=round(percentage, 1),
            color=SPENDING_TYPE_COLORS[spending_type],
        )

    # Add uncategorized if any
    if uncategorized > 0:
        percentage = float(uncategorized / grand_total * 100) if grand_total else 0
        results['uncategorized'] = SpendingBreakdown(
            label='Uncategorized',
            amount=uncategorized,
            percentage=round(percentage, 1),
            color='#9CA3AF',
        )

    return results


def calculate_csp_breakdown(
    transactions: List[Transaction],
    monthly_income: Optional[Decimal] = None,
) -> Dict[str, CSPBreakdownItem]:
    """
    Calculate Conscious Spending Plan breakdown.

    Returns dict with keys for each CSP bucket containing CSPBreakdownItem.
    """
    totals = {
        CSPBucket.FIXED: Decimal('0'),
        CSPBucket.INVESTMENTS: Decimal('0'),
        CSPBucket.SAVINGS: Decimal('0'),
        CSPBucket.GUILT_FREE: Decimal('0'),
    }
    uncategorized = Decimal('0')

    for txn in transactions:
        csp_bucket = txn.csp_bucket
        if csp_bucket and csp_bucket in totals:
            totals[csp_bucket] += txn.amount
        else:
            uncategorized += txn.amount

    grand_total = sum(totals.values()) + uncategorized

    # Use income for percentage calculation if provided, otherwise use total spending
    base_for_percentage = monthly_income if monthly_income else grand_total

    results = {}
    for bucket, amount in totals.items():
        if base_for_percentage:
            percentage = float(amount / base_for_percentage * 100)
        else:
            percentage = 0

        target_min, target_max = CSP_TARGETS[bucket]

        # Check if on target
        if bucket == CSPBucket.INVESTMENTS:
            # 10%+ means at or above minimum
            is_on_target = percentage >= target_min
        elif bucket == CSPBucket.SAVINGS:
            # 5-15%+ means at least minimum, upper is a suggestion
            is_on_target = percentage >= target_min
        else:
            is_on_target = target_min <= percentage <= target_max

        results[bucket] = CSPBreakdownItem(
            label=CSPBucket(bucket).label,
            amount=amount,
            percentage=round(percentage, 1),
            target_min=target_min,
            target_max=target_max,
            is_on_target=is_on_target,
            color=CSP_BUCKET_COLORS[bucket],
        )

    return results


def get_spending_summary(
    user,
    transactions,
) -> dict:
    """
    Get complete spending summary for dashboard display.

    Returns dict with:
    - wants_needs: breakdown if enabled
    - csp: breakdown if enabled
    - total_spent: sum of all transactions
    - monthly_income: user's income (if set)
    """
    transactions_list = list(transactions)
    total_spent = sum(t.amount for t in transactions_list)

    result = {
        'total_spent': total_spent,
        'monthly_income': user.monthly_income,
        'wants_needs': None,
        'csp': None,
    }

    if user.enable_wants_needs:
        result['wants_needs'] = calculate_wants_needs_breakdown(transactions_list)

    if user.enable_conscious_spending:
        result['csp'] = calculate_csp_breakdown(
            transactions_list,
            user.monthly_income
        )

    return result

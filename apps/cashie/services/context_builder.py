"""
Builds financial context from user data for Cashie LLM consumption.
"""
from decimal import Decimal
from typing import Dict, List, Any
from datetime import date

from django.db.models import Sum
from django.utils import timezone

from apps.transactions.models import Transaction
from apps.budgets.models import BudgetCategory, SpendingAlert


class ContextBuilder:
    """Builds financial context for the LLM from user data."""

    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
        self.month_start = self.today.replace(day=1)

    def build_context(self) -> Dict[str, Any]:
        """Build complete financial context for the user."""
        return {
            'user_preferences': self._get_user_preferences(),
            'current_month_spending': self._get_current_month_spending(),
            'budget_status': self._get_budget_status(),
            'recent_transactions': self._get_recent_transactions(),
            'unread_alerts': self._get_unread_alerts(),
            'summary_stats': self._get_summary_stats(),
        }

    def build_context_string(self) -> str:
        """Build context as a formatted string for the system prompt."""
        context = self.build_context()
        parts = []

        # User preferences
        prefs = context['user_preferences']
        parts.append("USER PROFILE:")
        parts.append(f"- Currency: {prefs['currency']}")
        if prefs['monthly_income']:
            parts.append(f"- Monthly Income: ${prefs['monthly_income']:.2f}")
        if prefs['wants_needs_enabled']:
            parts.append("- Wants vs Needs tracking: Enabled")
        if prefs['csp_enabled']:
            parts.append("- Conscious Spending Plan: Enabled")
        parts.append("")

        # Current month spending
        spending = context['current_month_spending']
        parts.append(f"CURRENT MONTH SPENDING ({self.today.strftime('%B %Y')}):")
        if spending:
            total = sum(item['spent'] for item in spending)
            parts.append(f"- Total spent: ${total:.2f}")
            for item in spending:
                parts.append(f"- {item['category']}: ${item['spent']:.2f}")
        else:
            parts.append("- No transactions this month")
        parts.append("")

        # Budget status
        budgets = context['budget_status']
        if budgets:
            parts.append("BUDGET STATUS:")
            for b in budgets:
                pct = (b['spent'] / b['limit'] * 100) if b['limit'] else 0
                status = "OVER" if b['spent'] > b['limit'] else f"{pct:.0f}%"
                parts.append(f"- {b['category']}: ${b['spent']:.2f} / ${b['limit']:.2f} ({status})")
            parts.append("")

        # Recent transactions
        txns = context['recent_transactions']
        if txns:
            parts.append("RECENT TRANSACTIONS (last 20):")
            for t in txns[:20]:
                cat = t.get('category', 'Uncategorized')
                parts.append(f"- {t['date']}: {t['description'][:40]} - ${t['amount']:.2f} [{cat}]")
            parts.append("")

        # Unread alerts
        alerts = context['unread_alerts']
        if alerts:
            parts.append(f"UNREAD ALERTS ({len(alerts)}):")
            for a in alerts[:5]:
                parts.append(f"- {a['type']}: {a['message'][:60]}")
            parts.append("")

        # Summary stats
        stats = context['summary_stats']
        parts.append("SUMMARY STATISTICS:")
        parts.append(f"- Total transactions this month: {stats['transaction_count']}")
        parts.append(f"- Active budget categories: {stats['category_count']}")
        if stats['largest_transaction']:
            parts.append(f"- Largest transaction: ${stats['largest_transaction']:.2f}")
        if stats['avg_transaction']:
            parts.append(f"- Average transaction: ${stats['avg_transaction']:.2f}")

        return "\n".join(parts)

    def _get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences and settings."""
        return {
            'currency': self.user.preferred_currency,
            'monthly_income': self.user.monthly_income,
            'wants_needs_enabled': self.user.enable_wants_needs,
            'csp_enabled': self.user.enable_conscious_spending,
        }

    def _get_current_month_spending(self) -> List[Dict[str, Any]]:
        """Get spending by category for current month."""
        spending = Transaction.objects.filter(
            user=self.user,
            date__gte=self.month_start
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        return [
            {
                'category': item['category__name'] or 'Uncategorized',
                'spent': item['total'] or Decimal('0'),
            }
            for item in spending
        ]

    def _get_budget_status(self) -> List[Dict[str, Any]]:
        """Get budget limit vs spent for each category."""
        categories = BudgetCategory.objects.filter(
            user=self.user,
            is_active=True
        )

        result = []
        for category in categories:
            spent = Transaction.objects.filter(
                user=self.user,
                category=category,
                date__gte=self.month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            result.append({
                'category': category.name,
                'limit': category.monthly_limit,
                'spent': spent,
                'remaining': category.monthly_limit - spent,
            })

        return sorted(result, key=lambda x: x['spent'], reverse=True)

    def _get_recent_transactions(self) -> List[Dict[str, Any]]:
        """Get the 20 most recent transactions."""
        transactions = Transaction.objects.filter(
            user=self.user
        ).select_related('category').order_by('-date', '-created_at')[:20]

        return [
            {
                'date': txn.date.isoformat(),
                'description': txn.description,
                'amount': txn.amount,
                'category': txn.category.name if txn.category else None,
                'merchant': txn.merchant,
            }
            for txn in transactions
        ]

    def _get_unread_alerts(self) -> List[Dict[str, Any]]:
        """Get unread spending alerts."""
        alerts = SpendingAlert.objects.filter(
            user=self.user,
            is_read=False,
            is_dismissed=False
        )[:10]

        return [
            {
                'type': alert.get_alert_type_display(),
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
            }
            for alert in alerts
        ]

    def _get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        month_txns = Transaction.objects.filter(
            user=self.user,
            date__gte=self.month_start
        )

        count = month_txns.count()
        aggregates = month_txns.aggregate(
            total=Sum('amount'),
        )

        category_count = BudgetCategory.objects.filter(
            user=self.user,
            is_active=True
        ).count()

        largest = month_txns.order_by('-amount').first()
        avg = (aggregates['total'] / count) if count and aggregates['total'] else None

        return {
            'transaction_count': count,
            'category_count': category_count,
            'total_spent': aggregates['total'] or Decimal('0'),
            'largest_transaction': largest.amount if largest else None,
            'avg_transaction': avg,
        }

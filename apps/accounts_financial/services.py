from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from django.db.models import Sum, Q

from apps.transactions.models import Transaction, TransactionType, TransactionStatus
from .models import Account, AccountBalanceSnapshot


class AccountBalanceService:
    """Service for calculating and managing account balances."""

    # Transaction types that decrease balance for asset accounts
    ASSET_DECREASE_TYPES = [
        TransactionType.PURCHASE,
        TransactionType.WITHDRAWAL,
        TransactionType.FEE,
        TransactionType.PAYMENT,  # Payment to CC
    ]

    # Transaction types that increase balance for asset accounts
    ASSET_INCREASE_TYPES = [
        TransactionType.DEPOSIT,
        TransactionType.REFUND,
    ]

    # Transaction types that increase debt for liability accounts
    LIABILITY_INCREASE_TYPES = [
        TransactionType.PURCHASE,
        TransactionType.FEE,
        TransactionType.INTEREST,
    ]

    # Transaction types that decrease debt for liability accounts
    LIABILITY_DECREASE_TYPES = [
        TransactionType.PAYMENT,
        TransactionType.REFUND,
    ]

    def get_current_balance(self, account: Account, include_pending: bool = True) -> Decimal:
        """
        Calculate current account balance including all transactions.

        Args:
            account: The account to calculate balance for
            include_pending: If True, include pending transactions (Available Balance)
                           If False, only posted/cleared (Posted Balance)

        Returns:
            Current balance as Decimal
        """
        return self._calculate_balance(
            account,
            as_of_date=None,
            include_pending=include_pending
        )

    def get_posted_balance(self, account: Account) -> Decimal:
        """Get balance from only posted/cleared transactions."""
        return self.get_current_balance(account, include_pending=False)

    def get_balance_as_of(self, account: Account, as_of_date: date) -> Decimal:
        """
        Calculate account balance as of a specific date.

        Args:
            account: The account to calculate balance for
            as_of_date: Calculate balance up to and including this date

        Returns:
            Balance as of the specified date
        """
        return self._calculate_balance(
            account,
            as_of_date=as_of_date,
            include_pending=True
        )

    def _calculate_balance(
        self,
        account: Account,
        as_of_date: Optional[date] = None,
        include_pending: bool = True
    ) -> Decimal:
        """
        Core balance calculation logic.

        For asset accounts (checking, savings, investment):
            balance = initial_balance + deposits/refunds - purchases/withdrawals/fees/payments

        For liability accounts (credit card, loan):
            balance = initial_balance + purchases/fees/interest - payments/refunds
            (Positive balance = debt owed)
        """
        balance = account.initial_balance

        # Build base query
        txn_query = Transaction.objects.filter(account=account)

        # Filter by date if specified
        if as_of_date:
            txn_query = txn_query.filter(date__lte=as_of_date)

        # Filter by status if not including pending
        if not include_pending:
            txn_query = txn_query.exclude(status=TransactionStatus.PENDING)

        if account.is_asset:
            # Asset account: deposits increase, purchases decrease
            increases = txn_query.filter(
                transaction_type__in=self.ASSET_INCREASE_TYPES
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            decreases = txn_query.filter(
                transaction_type__in=self.ASSET_DECREASE_TYPES
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # Handle transfers
            # Outbound transfers (this is the source account)
            outbound_transfers = txn_query.filter(
                transaction_type=TransactionType.TRANSFER,
                transfer_pair__isnull=False
            ).exclude(
                transfer_pair__account=account  # Exclude self-transfers
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # For assets: amount is stored as positive, decreases are subtracted
            balance = balance + increases - decreases - outbound_transfers

            # Inbound transfers (check linked transactions that point to different account)
            inbound_query = Transaction.objects.filter(
                transfer_pair__account=account
            )
            if as_of_date:
                inbound_query = inbound_query.filter(date__lte=as_of_date)
            if not include_pending:
                inbound_query = inbound_query.exclude(status=TransactionStatus.PENDING)

            inbound_transfers = inbound_query.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            balance = balance + inbound_transfers

        else:
            # Liability account: purchases increase debt, payments decrease
            increases = txn_query.filter(
                transaction_type__in=self.LIABILITY_INCREASE_TYPES
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            decreases = txn_query.filter(
                transaction_type__in=self.LIABILITY_DECREASE_TYPES
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            # For liabilities: positive balance = debt
            balance = balance + increases - decreases

        return balance

    def get_balance_history(
        self,
        account: Account,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Get daily balance history for charting.

        Args:
            account: The account to get history for
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of dicts with 'date' and 'balance' keys
        """
        history = []
        current_date = start_date

        while current_date <= end_date:
            balance = self.get_balance_as_of(account, current_date)
            history.append({
                'date': current_date.isoformat(),
                'balance': float(balance)
            })
            current_date += timedelta(days=1)

        return history

    def get_balance_history_optimized(
        self,
        account: Account,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Optimized balance history that only calculates on transaction dates.

        Returns list of dicts with 'date' and 'balance' for each day in range,
        but only recalculates when transactions occur.
        """
        # Get starting balance (day before start_date)
        day_before = start_date - timedelta(days=1)
        running_balance = self.get_balance_as_of(account, day_before)

        # Get all transactions in date range
        transactions = Transaction.objects.filter(
            account=account,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date', 'created_at')

        # Build a map of date -> net change
        date_changes = {}
        for txn in transactions:
            if txn.date not in date_changes:
                date_changes[txn.date] = Decimal('0')

            change = self._get_transaction_effect(account, txn)
            date_changes[txn.date] += change

        # Generate daily history
        history = []
        current_date = start_date

        while current_date <= end_date:
            if current_date in date_changes:
                running_balance += date_changes[current_date]

            history.append({
                'date': current_date.isoformat(),
                'balance': float(running_balance)
            })
            current_date += timedelta(days=1)

        return history

    def _get_transaction_effect(self, account: Account, txn: Transaction) -> Decimal:
        """Calculate the effect of a single transaction on account balance."""
        amount = txn.amount

        if account.is_asset:
            if txn.transaction_type in self.ASSET_INCREASE_TYPES:
                return amount
            elif txn.transaction_type in self.ASSET_DECREASE_TYPES:
                return -amount
            elif txn.transaction_type == TransactionType.TRANSFER:
                # Outbound transfer
                return -amount
        else:
            # Liability account
            if txn.transaction_type in self.LIABILITY_INCREASE_TYPES:
                return amount
            elif txn.transaction_type in self.LIABILITY_DECREASE_TYPES:
                return -amount

        return Decimal('0')

    def reconcile_with_snapshot(
        self,
        account: Account,
        snapshot: AccountBalanceSnapshot
    ) -> Dict:
        """
        Compare calculated balance with a recorded snapshot.

        Args:
            account: The account to reconcile
            snapshot: The balance snapshot to compare against

        Returns:
            Dict with reconciliation details
        """
        calculated = self.get_balance_as_of(account, snapshot.as_of_date)
        recorded = snapshot.balance
        discrepancy = calculated - recorded

        return {
            'as_of_date': snapshot.as_of_date,
            'calculated_balance': calculated,
            'recorded_balance': recorded,
            'discrepancy': discrepancy,
            'is_reconciled': discrepancy == Decimal('0'),
            'snapshot_source': snapshot.source,
        }

    def get_net_worth_summary(self, user) -> Dict:
        """
        Calculate net worth summary for a user.

        Returns:
            Dict with total_assets, total_liabilities, net_worth
        """
        accounts = Account.objects.filter(user=user, is_active=True)

        total_assets = Decimal('0')
        total_liabilities = Decimal('0')

        for account in accounts:
            balance = self.get_current_balance(account)
            if account.is_asset:
                total_assets += balance
            else:
                total_liabilities += balance

        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'net_worth': total_assets - total_liabilities,
        }


class TransferService:
    """Service for managing transfers between accounts."""

    def create_transfer(
        self,
        from_account: Account,
        to_account: Account,
        amount: Decimal,
        transfer_date: date,
        description: str = ""
    ) -> Tuple[Transaction, Transaction]:
        """
        Create a transfer between two accounts.

        Creates two linked transactions:
        - One outflow from source account
        - One inflow to destination account

        Args:
            from_account: Source account
            to_account: Destination account
            amount: Transfer amount (positive)
            transfer_date: Date of transfer
            description: Optional description

        Returns:
            Tuple of (from_transaction, to_transaction)
        """
        if from_account.user != to_account.user:
            raise ValueError("Cannot transfer between accounts of different users")

        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        # Create outflow transaction
        from_txn = Transaction.objects.create(
            user=from_account.user,
            account=from_account,
            date=transfer_date,
            description=description or f"Transfer to {to_account.name}",
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.POSTED,
        )

        # Create inflow transaction
        to_txn = Transaction.objects.create(
            user=to_account.user,
            account=to_account,
            date=transfer_date,
            description=description or f"Transfer from {from_account.name}",
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            status=TransactionStatus.POSTED,
        )

        # Link the transactions
        from_txn.transfer_pair = to_txn
        from_txn.save()
        to_txn.transfer_pair = from_txn
        to_txn.save()

        return from_txn, to_txn

    def create_cc_payment(
        self,
        from_account: Account,
        cc_account: Account,
        amount: Decimal,
        payment_date: date,
        description: str = ""
    ) -> Tuple[Transaction, Transaction]:
        """
        Create a credit card payment from a debit account.

        Args:
            from_account: Source checking/savings account
            cc_account: Credit card account receiving payment
            amount: Payment amount
            payment_date: Date of payment
            description: Optional description

        Returns:
            Tuple of (payment_from_txn, payment_to_cc_txn)
        """
        if cc_account.account_type != Account.AccountType.CREDIT_CARD:
            raise ValueError("Destination must be a credit card account")

        if from_account.user != cc_account.user:
            raise ValueError("Cannot pay CC from different user's account")

        if amount <= 0:
            raise ValueError("Payment amount must be positive")

        # Create payment outflow from debit account
        from_txn = Transaction.objects.create(
            user=from_account.user,
            account=from_account,
            date=payment_date,
            description=description or f"Payment to {cc_account.name}",
            amount=amount,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.POSTED,
        )

        # Create payment inflow to credit card (reduces debt)
        cc_txn = Transaction.objects.create(
            user=cc_account.user,
            account=cc_account,
            date=payment_date,
            description=description or f"Payment from {from_account.name}",
            amount=amount,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.POSTED,
        )

        # Link the transactions
        from_txn.transfer_pair = cc_txn
        from_txn.save()
        cc_txn.transfer_pair = from_txn
        cc_txn.save()

        return from_txn, cc_txn

    def link_existing_transactions(
        self,
        txn1: Transaction,
        txn2: Transaction
    ) -> None:
        """
        Link two existing transactions as a transfer pair.

        Args:
            txn1: First transaction
            txn2: Second transaction
        """
        if txn1.transfer_pair or txn2.transfer_pair:
            raise ValueError("One or both transactions already have a transfer pair")

        txn1.transfer_pair = txn2
        txn1.transaction_type = TransactionType.TRANSFER
        txn1.save()

        txn2.transfer_pair = txn1
        txn2.transaction_type = TransactionType.TRANSFER
        txn2.save()

    def unlink_transfer(self, transaction: Transaction) -> None:
        """
        Unlink a transfer pair.

        Args:
            transaction: Either transaction in the pair
        """
        if not transaction.transfer_pair:
            return

        paired = transaction.transfer_pair

        transaction.transfer_pair = None
        transaction.save()

        paired.transfer_pair = None
        paired.save()

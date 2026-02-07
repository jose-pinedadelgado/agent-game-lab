from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal


@dataclass
class CategoryPrediction:
    """Result of a categorization prediction."""
    category_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: Optional[str] = None


@dataclass
class TransactionData:
    """Input data for categorization."""
    description: str
    amount: Decimal
    merchant: str = ""
    date: Optional[str] = None


class BaseCategorizer(ABC):
    """Abstract base class for categorization strategies."""

    @abstractmethod
    def categorize(
        self,
        transaction: TransactionData,
        valid_categories: List[str],
        user_history: Optional[List[dict]] = None
    ) -> CategoryPrediction:
        """Predict category for a single transaction."""
        pass

    @abstractmethod
    def categorize_batch(
        self,
        transactions: List[TransactionData],
        valid_categories: List[str],
        user_history: Optional[List[dict]] = None
    ) -> List[CategoryPrediction]:
        """Predict categories for multiple transactions."""
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        """Return identifier for this categorizer version."""
        pass

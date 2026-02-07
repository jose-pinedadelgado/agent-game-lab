"""
LLM-based transaction categorizer using OpenAI GPT-4o.
Includes user history as few-shot examples for personalized predictions.
"""
import json
import logging
from typing import List, Optional

from django.conf import settings

from .base import BaseCategorizer, CategoryPrediction, TransactionData

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial transaction categorizer. Your job is to assign spending categories to transactions based on their descriptions.

RULES:
1. You MUST only use categories from the provided list of valid categories
2. Learn from the user's past categorization examples - they show personal preferences
3. Be consistent - similar transactions should get the same category
4. When uncertain, use "Other" if it's a valid category
5. Confidence should be 0.0-1.0 where 1.0 means you're certain

Common category mappings (adjust based on user's actual categories):
- Grocery stores, supermarkets → Groceries
- Restaurants, cafes, fast food → Dining
- Gas stations, uber, lyft, parking → Transportation
- Movies, streaming, games → Entertainment
- Retail stores, Amazon → Shopping
- Electric, water, internet, phone → Utilities"""

SYSTEM_PROMPT_WITH_SECONDARY = """You are a financial transaction categorizer. Your job is to assign spending categories AND spending types to transactions.

RULES:
1. You MUST only use categories from the provided list of valid categories
2. Learn from the user's past categorization examples - they show personal preferences
3. Be consistent - similar transactions should get the same category
4. When uncertain, use "Other" if it's a valid category
5. Confidence should be 0.0-1.0 where 1.0 means you're certain

Common category mappings (adjust based on user's actual categories):
- Grocery stores, supermarkets → Groceries
- Restaurants, cafes, fast food → Dining
- Gas stations, uber, lyft, parking → Transportation
- Movies, streaming, games → Entertainment
- Retail stores, Amazon → Shopping
- Electric, water, internet, phone → Utilities

SPENDING TYPE RULES (Wants vs Needs):
- need: Essential expenses (groceries, rent, utilities, insurance, basic transportation, healthcare)
- want: Non-essential expenses (dining out, entertainment, luxury items, hobbies)
- savings: Money set aside (retirement contributions, savings deposits, investments)

CSP BUCKET RULES (Conscious Spending Plan):
- fixed: Fixed recurring costs (rent, mortgage, utilities, insurance, groceries, minimum debt payments)
- investments: Long-term wealth building (401k, IRA, brokerage deposits, index funds)
- savings: Short/medium-term goals (emergency fund, vacation fund, down payment savings)
- guilt_free: Discretionary spending (dining, entertainment, shopping, hobbies, subscriptions)"""


class LLMCategorizer(BaseCategorizer):
    """OpenAI-based categorizer using GPT-4o."""

    MODEL_VERSION = "llm-gpt4o-v2"  # Updated version for secondary categorization

    def __init__(self):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '')
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    def categorize(
        self,
        transaction: TransactionData,
        valid_categories: List[str],
        user_history: Optional[List[dict]] = None,
        include_spending_type: bool = False,
        include_csp_bucket: bool = False,
    ) -> CategoryPrediction:
        """Predict category for a single transaction."""
        results = self.categorize_batch(
            [transaction],
            valid_categories,
            user_history,
            include_spending_type,
            include_csp_bucket,
        )
        return results[0]

    def categorize_batch(
        self,
        transactions: List[TransactionData],
        valid_categories: List[str],
        user_history: Optional[List[dict]] = None,
        include_spending_type: bool = False,
        include_csp_bucket: bool = False,
    ) -> List[CategoryPrediction]:
        """Predict categories for multiple transactions."""
        if not transactions:
            return []

        if not self.client:
            logger.warning("OpenAI client not available, returning 'Other' for all")
            return [CategoryPrediction("Other", 0.0) for _ in transactions]

        if not valid_categories:
            logger.warning("No valid categories provided")
            return [CategoryPrediction("Other", 0.0) for _ in transactions]

        try:
            use_secondary = include_spending_type or include_csp_bucket
            prompt = self._build_prompt(
                transactions,
                valid_categories,
                user_history,
                include_spending_type,
                include_csp_bucket,
            )
            system_prompt = SYSTEM_PROMPT_WITH_SECONDARY if use_secondary else SYSTEM_PROMPT

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return self._parse_response(
                response,
                transactions,
                valid_categories,
                include_spending_type,
                include_csp_bucket,
            )

        except Exception as e:
            logger.error(f"LLM categorization failed: {e}")
            return [CategoryPrediction("Other", 0.0) for _ in transactions]

    def _build_prompt(
        self,
        transactions: List[TransactionData],
        valid_categories: List[str],
        user_history: Optional[List[dict]] = None,
        include_spending_type: bool = False,
        include_csp_bucket: bool = False,
    ) -> str:
        """Build prompt with categories, examples, and transactions."""
        parts = []

        # Valid categories
        parts.append("VALID CATEGORIES (you must ONLY use these):")
        for cat in valid_categories:
            parts.append(f"- {cat}")
        parts.append("")

        # Spending type options
        if include_spending_type:
            parts.append("VALID SPENDING TYPES:")
            parts.append("- need (essential expenses)")
            parts.append("- want (non-essential expenses)")
            parts.append("- savings (money set aside)")
            parts.append("")

        # CSP bucket options
        if include_csp_bucket:
            parts.append("VALID CSP BUCKETS:")
            parts.append("- fixed (fixed recurring costs: 50-60% of income)")
            parts.append("- investments (long-term wealth: 10%+ of income)")
            parts.append("- savings (short/medium-term goals: 5-15% of income)")
            parts.append("- guilt_free (discretionary spending: 20-35% of income)")
            parts.append("")

        # User history as few-shot examples
        if user_history:
            parts.append("USER'S PAST CATEGORIZATIONS (learn from these preferences):")
            # Group by category and limit examples
            examples_by_category = {}
            for item in user_history:
                cat = item.get('category_name', '')
                desc = item.get('transaction_description', '')
                if cat and desc:
                    if cat not in examples_by_category:
                        examples_by_category[cat] = []
                    if len(examples_by_category[cat]) < 5:  # Max 5 per category
                        examples_by_category[cat].append(desc)

            for cat, descriptions in examples_by_category.items():
                for desc in descriptions:
                    parts.append(f'- "{desc}" → {cat}')
            parts.append("")

        # Transactions to categorize
        parts.append("TRANSACTIONS TO CATEGORIZE:")
        for i, t in enumerate(transactions):
            merchant_info = f" (merchant: {t.merchant})" if t.merchant else ""
            parts.append(f'{i + 1}. "{t.description}"{merchant_info} - ${t.amount}')
        parts.append("")

        # Output format
        if include_spending_type or include_csp_bucket:
            prediction_fields = [
                '"index": 1',
                '"category": "CategoryName"',
                '"confidence": 0.95',
            ]
            if include_spending_type:
                prediction_fields.append('"spending_type": "need"')
            if include_csp_bucket:
                prediction_fields.append('"csp_bucket": "fixed"')

            example_pred = "{" + ", ".join(prediction_fields) + "}"
            parts.append(f"""Return a JSON object with this exact structure:
{{
    "predictions": [
        {example_pred}
    ]
}}

Each prediction must have:
- index: The transaction number (1-based)
- category: MUST be one of the valid categories listed above
- confidence: 0.0 to 1.0""")
            if include_spending_type:
                parts.append("- spending_type: MUST be one of: need, want, savings")
            if include_csp_bucket:
                parts.append("- csp_bucket: MUST be one of: fixed, investments, savings, guilt_free")
        else:
            parts.append("""Return a JSON object with this exact structure:
{
    "predictions": [
        {"index": 1, "category": "CategoryName", "confidence": 0.95},
        {"index": 2, "category": "CategoryName", "confidence": 0.80}
    ]
}

Each prediction must have:
- index: The transaction number (1-based)
- category: MUST be one of the valid categories listed above
- confidence: 0.0 to 1.0""")

        return "\n".join(parts)

    def _parse_response(
        self,
        response,
        transactions: List[TransactionData],
        valid_categories: List[str],
        include_spending_type: bool = False,
        include_csp_bucket: bool = False,
    ) -> List[CategoryPrediction]:
        """Parse OpenAI response into CategoryPrediction list."""
        default_category = "Other" if "Other" in valid_categories else valid_categories[0]

        valid_spending_types = {'need', 'want', 'savings'}
        valid_csp_buckets = {'fixed', 'investments', 'savings', 'guilt_free'}

        try:
            content = response.choices[0].message.content
            data = json.loads(content)

            if not isinstance(data, dict) or 'predictions' not in data:
                logger.warning("Response missing 'predictions' key")
                return [CategoryPrediction(default_category, 0.0) for _ in transactions]

            # Build results indexed by position
            results = [CategoryPrediction(default_category, 0.0) for _ in transactions]

            for pred in data['predictions']:
                try:
                    idx = int(pred.get('index', 0)) - 1  # Convert to 0-based
                    if 0 <= idx < len(transactions):
                        category = pred.get('category', default_category)
                        confidence = float(pred.get('confidence', 0.0))

                        # Validate category is in valid list
                        if category not in valid_categories:
                            # Try case-insensitive match
                            category_lower = category.lower()
                            matched = False
                            for valid_cat in valid_categories:
                                if valid_cat.lower() == category_lower:
                                    category = valid_cat
                                    matched = True
                                    break
                            if not matched:
                                category = default_category
                                confidence = 0.0

                        # Clamp confidence
                        confidence = max(0.0, min(1.0, confidence))

                        # Parse spending type
                        spending_type = None
                        if include_spending_type:
                            st = pred.get('spending_type', '').lower()
                            if st in valid_spending_types:
                                spending_type = st

                        # Parse CSP bucket
                        csp_bucket = None
                        if include_csp_bucket:
                            cb = pred.get('csp_bucket', '').lower()
                            if cb in valid_csp_buckets:
                                csp_bucket = cb

                        results[idx] = CategoryPrediction(
                            category,
                            confidence,
                            spending_type=spending_type,
                            csp_bucket=csp_bucket,
                        )
                except (ValueError, TypeError, KeyError) as e:
                    logger.debug(f"Error parsing prediction: {pred} - {e}")
                    continue

            return results

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return [CategoryPrediction(default_category, 0.0) for _ in transactions]

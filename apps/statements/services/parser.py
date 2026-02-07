"""
Multi-strategy PDF parser for credit card statements.
Fallback chain: pdfplumber -> PyPDF2 -> OpenAI (AI extraction)
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
import re
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTransaction:
    """Represents a transaction extracted from a statement."""
    date: date
    description: str
    amount: Decimal
    transaction_number: Optional[str] = None
    merchant: Optional[str] = None


class StatementParser:
    """
    Multi-strategy PDF parser with fallback chain.
    Primary: Regex-based extraction
    Fallback: OpenAI GPT-4 for intelligent extraction
    """

    def __init__(self, bank: str = 'other'):
        self.bank = bank

    def parse(self, file_path: str) -> List[ExtractedTransaction]:
        """Try each extraction strategy until one succeeds."""
        # First extract text from PDF
        text = self._extract_text(file_path)
        if not text:
            logger.warning("Could not extract text from PDF")
            return []

        # Try regex-based parsing first
        transactions = self._parse_transactions(text)

        # If regex found many transactions, use them
        if transactions and len(transactions) >= 5:
            logger.info(f"Regex extracted {len(transactions)} transactions")
            return transactions

        # Try OpenAI for better extraction (handles various formats intelligently)
        logger.info(f"Regex found {len(transactions)} transactions, trying OpenAI for better results...")
        ai_transactions = self._extract_with_openai(text)
        if ai_transactions:
            logger.info(f"OpenAI extracted {len(ai_transactions)} transactions")
            return ai_transactions

        # Return whatever regex found (even if few)
        return transactions

    def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF using multiple strategies."""
        # Try pdfplumber first (best for structured PDFs)
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            if text_parts:
                return '\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            if text_parts:
                return '\n'.join(text_parts)
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")

        return ""

    def _extract_with_openai(self, text: str) -> List[ExtractedTransaction]:
        """Use OpenAI GPT-4 to extract transactions from statement text."""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            logger.warning("No OpenAI API key configured")
            return []

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            # Truncate text to avoid token limits
            truncated_text = text[:12000]

            prompt = f"""Extract all financial transactions from this bank/credit card statement text.
Return ONLY a valid JSON object with this exact structure:
{{
    "transactions": [
        {{
            "date": "YYYY-MM-DD",
            "description": "Transaction description or merchant name",
            "amount": 123.45
        }}
    ]
}}

RULES:
1. Include ALL transactions (deposits, withdrawals, purchases, payments, transfers)
2. Dates must be in YYYY-MM-DD format (use current year if year not specified)
3. Amounts must be positive numbers
4. For withdrawals/debits, the amount is still positive (we track the type in description)
5. Clean up descriptions - remove extra spaces and formatting artifacts
6. Skip headers, footers, balance summaries, and non-transaction lines
7. If you cannot determine a date, skip that transaction

Statement Text:
{truncated_text}
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a financial document parser. Extract transactions accurately and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )

            raw_content = response.choices[0].message.content

            # Clean the response to extract JSON
            cleaned_content = self._clean_json_response(raw_content)
            data = json.loads(cleaned_content)

            if not isinstance(data, dict) or 'transactions' not in data:
                logger.warning("OpenAI response missing 'transactions' key")
                return []

            # Convert to ExtractedTransaction objects
            transactions = []
            for t in data['transactions']:
                try:
                    trans_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    amount = Decimal(str(t['amount']))
                    description = str(t['description']).strip()

                    if amount > 0 and description:
                        transactions.append(ExtractedTransaction(
                            date=trans_date,
                            description=description,
                            amount=amount,
                            merchant=self._extract_merchant(description)
                        ))
                except (ValueError, KeyError, TypeError) as e:
                    logger.debug(f"Skipping invalid transaction: {t} - {e}")
                    continue

            return transactions

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return []

    def _clean_json_response(self, content: str) -> str:
        """Clean OpenAI response to extract valid JSON."""
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith('```'):
            lines = content.split('\n')
            # Remove first and last lines (```json and ```)
            lines = [l for l in lines if not l.strip().startswith('```')]
            content = '\n'.join(lines)

        # Find JSON object boundaries
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            content = content[start:end + 1]

        return content

    def _parse_transactions(self, text: str) -> List[ExtractedTransaction]:
        """Parse transactions from extracted text based on bank type."""
        if self.bank == 'amex':
            return self._parse_amex(text)
        elif self.bank == 'chase':
            return self._parse_chase(text)
        else:
            return self._parse_generic(text)

    def _parse_amex(self, text: str) -> List[ExtractedTransaction]:
        """Parse American Express statement format."""
        transactions = []

        # Multiple AMEX patterns
        patterns = [
            # Pattern: MM/DD/YY* MERCHANT NAME AMOUNT (with optional asterisk for online)
            r'(\d{2}/\d{2}/\d{2})\*?\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            # Pattern: MM/DD/YY MERCHANT CITY STATE $AMOUNT
            r'(\d{2}/\d{2}/\d{2})\s+(.+?)\s+[A-Z]{2}\s+\$?([\d,]+\.\d{2})',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                try:
                    date_str, description, amount_str = match.groups()
                    trans_date = datetime.strptime(date_str, '%m/%d/%y').date()
                    amount = Decimal(amount_str.replace(',', ''))

                    merchant = self._extract_merchant(description)

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description.strip(),
                        amount=amount,
                        merchant=merchant
                    ))
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse line: {match.group(0)} - {e}")
                    continue

        return self._deduplicate(transactions)

    def _parse_chase(self, text: str) -> List[ExtractedTransaction]:
        """Parse Chase statement format."""
        transactions = []

        # Chase pattern: MM/DD MERCHANT AMOUNT
        pattern = r'(\d{2}/\d{2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})'

        current_year = datetime.now().year

        for match in re.finditer(pattern, text):
            try:
                date_str, description, amount_str = match.groups()
                trans_date = datetime.strptime(f"{date_str}/{current_year}", '%m/%d/%Y').date()
                amount = Decimal(amount_str.replace('$', '').replace(',', '').replace('-', ''))

                merchant = self._extract_merchant(description)

                transactions.append(ExtractedTransaction(
                    date=trans_date,
                    description=description.strip(),
                    amount=amount,
                    merchant=merchant
                ))
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse line: {match.group(0)} - {e}")
                continue

        return self._deduplicate(transactions)

    def _parse_generic(self, text: str) -> List[ExtractedTransaction]:
        """Generic parser that tries multiple patterns."""
        transactions = []

        # Patterns to skip (balances, summaries, headers)
        skip_patterns = [
            r'balance\s*(forward)?',
            r'ending\s*balance',
            r'beginning\s*balance',
            r'total\s+',
            r'subtotal',
            r'dividends?\s+paid',
            r'annual\s+percentage',
            r'minimum\s+balance',
        ]
        skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)

        # Multiple patterns for different statement formats
        patterns = [
            # Credit union style: MM/DD Transaction Type Description Amount- Balance
            r'^(\d{2}/\d{2})\s+(Withdrawal|Deposit|Debit Card|ACH|Transfer)\s+(.+?)\s+([\d,]+\.\d{2})-?\s+[\d,]+\.\d{2}',
            # MM/DD/YYYY or MM/DD/YY followed by description and amount
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            # YYYY-MM-DD format
            r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
        ]

        date_formats = ['%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%m/%d']
        current_year = datetime.now().year

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    groups = match.groups()

                    # Handle different pattern group counts
                    if len(groups) == 4:
                        # Credit union pattern with transaction type
                        date_str, trans_type, description, amount_str = groups
                        description = f"{trans_type} {description}"
                    else:
                        date_str, description, amount_str = groups

                    # Skip balance/summary lines
                    if skip_regex.search(description):
                        continue

                    # Try each date format
                    trans_date = None
                    for fmt in date_formats:
                        try:
                            trans_date = datetime.strptime(date_str, fmt).date()
                            # If year is missing or default, use current year
                            if trans_date.year == 1900 or (fmt == '%m/%d'):
                                trans_date = trans_date.replace(year=current_year)
                            break
                        except ValueError:
                            continue

                    if trans_date is None:
                        continue

                    # Fix future dates (use previous year if date is in future)
                    if trans_date > date.today():
                        trans_date = trans_date.replace(year=current_year - 1)

                    amount = Decimal(amount_str.replace(',', '').replace('-', ''))
                    if amount <= 0:
                        continue

                    merchant = self._extract_merchant(description)

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description.strip(),
                        amount=amount,
                        merchant=merchant
                    ))
                except (ValueError, IndexError):
                    continue

        return self._deduplicate(transactions)

    def _deduplicate(self, transactions: List[ExtractedTransaction]) -> List[ExtractedTransaction]:
        """Remove duplicate transactions."""
        seen = set()
        unique = []
        for t in transactions:
            key = (t.date, t.description, t.amount)
            if key not in seen:
                seen.add(key)
                unique.append(t)
        return unique

    def _extract_merchant(self, description: str) -> str:
        """Extract merchant name from transaction description."""
        description = description.strip()

        # Remove location info (state codes at end)
        description = re.sub(r'\s+[A-Z]{2}\s*$', '', description)

        # Remove reference numbers
        description = re.sub(r'\s*#?\d{6,}$', '', description)

        # Take first part before common separators
        for sep in [' - ', ' * ', '  ']:
            if sep in description:
                description = description.split(sep)[0]
                break

        return description.strip()[:100]

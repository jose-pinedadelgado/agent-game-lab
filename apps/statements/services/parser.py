"""
Multi-format statement parser for credit card and bank statements.
Supports: PDF (multiple bank formats) and CSV (Chase export format)
Fallback chain: Format-specific parsing -> Generic parsing -> OpenAI extraction
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Tuple
from decimal import Decimal, InvalidOperation
import re
import csv
import json
import logging
import io
from pathlib import Path
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
    category_hint: Optional[str] = None  # Category from CSV if available
    transaction_type: Optional[str] = None  # Sale, Payment, Return, etc.


class StatementParser:
    """
    Multi-format statement parser with bank-specific strategies.
    Supports PDF and CSV files with fallback to OpenAI extraction.
    """

    def __init__(self, bank: str = 'other'):
        self.bank = bank.lower() if bank else 'other'

    def parse(self, file_path: str) -> List[ExtractedTransaction]:
        """Parse a statement file and extract transactions."""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.csv':
            return self._parse_csv(file_path)
        elif extension == '.pdf':
            return self._parse_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return []

    def _parse_csv(self, file_path: str) -> List[ExtractedTransaction]:
        """Parse CSV statement exports (primarily Chase format)."""
        transactions = []

        try:
            # Try different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error("Could not decode CSV file with any known encoding")
                return []

            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]

            # Detect format based on headers
            if 'transaction date' in headers and 'description' in headers:
                transactions = self._parse_chase_csv(reader)
            elif 'date' in headers and 'description' in headers:
                transactions = self._parse_generic_csv(reader)
            else:
                logger.warning(f"Unknown CSV format. Headers: {headers}")
                transactions = self._parse_generic_csv(reader)

            logger.info(f"CSV extracted {len(transactions)} transactions")
            return transactions

        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            return []

    def _parse_chase_csv(self, reader: csv.DictReader) -> List[ExtractedTransaction]:
        """Parse Chase credit card CSV export format."""
        transactions = []

        for row in reader:
            try:
                # Get date (Transaction Date preferred, fall back to Post Date)
                date_str = row.get('Transaction Date', '') or row.get('Post Date', '')
                if not date_str:
                    continue

                # Parse date (MM/DD/YYYY format)
                trans_date = self._parse_date(date_str)
                if not trans_date:
                    continue

                # Get description
                description = row.get('Description', '').strip()
                if not description:
                    continue

                # Get amount (negative = purchase, positive = payment/credit)
                amount_str = row.get('Amount', '0').strip()
                try:
                    amount = Decimal(amount_str.replace(',', ''))
                    # Convert to absolute value (we store all as positive)
                    amount = abs(amount)
                except (InvalidOperation, ValueError):
                    continue

                if amount <= 0:
                    continue

                # Get optional fields
                category = row.get('Category', '').strip() or None
                trans_type = row.get('Type', '').strip() or None
                merchant = self._extract_merchant(description)

                transactions.append(ExtractedTransaction(
                    date=trans_date,
                    description=description,
                    amount=amount,
                    merchant=merchant,
                    category_hint=category,
                    transaction_type=trans_type,
                ))

            except Exception as e:
                logger.debug(f"Skipping CSV row: {e}")
                continue

        return transactions

    def _parse_generic_csv(self, reader: csv.DictReader) -> List[ExtractedTransaction]:
        """Parse generic CSV format with flexible column detection."""
        transactions = []

        for row in reader:
            try:
                # Try to find date column
                date_str = None
                for key in ['date', 'transaction date', 'post date', 'trans date']:
                    if key in [k.lower() for k in row.keys()]:
                        for k, v in row.items():
                            if k.lower() == key and v:
                                date_str = v
                                break
                    if date_str:
                        break

                if not date_str:
                    continue

                trans_date = self._parse_date(date_str)
                if not trans_date:
                    continue

                # Try to find description column
                description = None
                for key in ['description', 'merchant', 'payee', 'name', 'memo']:
                    for k, v in row.items():
                        if k.lower() == key and v:
                            description = v.strip()
                            break
                    if description:
                        break

                if not description:
                    continue

                # Try to find amount column
                amount = None
                for key in ['amount', 'debit', 'credit', 'value']:
                    for k, v in row.items():
                        if k.lower() == key and v:
                            try:
                                amount = abs(Decimal(v.replace(',', '').replace('$', '').replace('-', '')))
                                break
                            except (InvalidOperation, ValueError):
                                continue
                    if amount:
                        break

                if not amount or amount <= 0:
                    continue

                transactions.append(ExtractedTransaction(
                    date=trans_date,
                    description=description,
                    amount=amount,
                    merchant=self._extract_merchant(description),
                ))

            except Exception as e:
                logger.debug(f"Skipping CSV row: {e}")
                continue

        return transactions

    def _parse_pdf(self, file_path: str) -> List[ExtractedTransaction]:
        """Parse PDF statement with bank-specific and generic strategies."""
        # Extract text from PDF
        text = self._extract_text(file_path)
        if not text:
            logger.warning("Could not extract text from PDF")
            return []

        # Try bank-specific parser first
        transactions = []
        if self.bank == 'chase':
            transactions = self._parse_chase_pdf(text)
        elif self.bank == 'amex':
            transactions = self._parse_amex_pdf(text)
        elif self.bank in ('wells_fargo', 'wellsfargo'):
            transactions = self._parse_wells_fargo_pdf(text)
        elif self.bank == 'boa':
            transactions = self._parse_boa_pdf(text)

        # If bank-specific found enough, use those
        if len(transactions) >= 3:
            logger.info(f"{self.bank} parser extracted {len(transactions)} transactions")
            return transactions

        # Try auto-detecting bank from content
        detected_bank = self._detect_bank(text)
        if detected_bank and detected_bank != self.bank:
            logger.info(f"Auto-detected bank: {detected_bank}")
            if detected_bank == 'chase':
                transactions = self._parse_chase_pdf(text)
            elif detected_bank == 'wells_fargo':
                transactions = self._parse_wells_fargo_pdf(text)
            elif detected_bank == 'amex':
                transactions = self._parse_amex_pdf(text)
            elif detected_bank == 'schoolfirst':
                transactions = self._parse_credit_union_pdf(text)

            if len(transactions) >= 3:
                logger.info(f"Auto-detected {detected_bank} extracted {len(transactions)} transactions")
                return transactions

        # Try generic parser
        generic_transactions = self._parse_generic_pdf(text)
        if len(generic_transactions) > len(transactions):
            transactions = generic_transactions

        # If still not enough, try OpenAI
        if len(transactions) < 3:
            logger.info(f"Regex found {len(transactions)} transactions, trying OpenAI...")
            ai_transactions = self._extract_with_openai(text)
            if len(ai_transactions) > len(transactions):
                logger.info(f"OpenAI extracted {len(ai_transactions)} transactions")
                return ai_transactions

        logger.info(f"Final extraction: {len(transactions)} transactions")
        return transactions

    def _detect_bank(self, text: str) -> Optional[str]:
        """Auto-detect bank from statement text content."""
        text_lower = text.lower()

        if 'chase.com' in text_lower or 'jpmorgan chase' in text_lower:
            return 'chase'
        elif 'wells fargo' in text_lower or 'wellsfargo.com' in text_lower:
            return 'wells_fargo'
        elif 'american express' in text_lower or 'amex' in text_lower:
            return 'amex'
        elif 'bank of america' in text_lower or 'bankofamerica.com' in text_lower:
            return 'boa'
        elif 'schoolsfirst' in text_lower or 'schoolfirst' in text_lower:
            return 'schoolfirst'

        return None

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

    def _parse_chase_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Parse Chase credit card PDF statement."""
        transactions = []

        # Chase format: MM/DD MERCHANT_NAME LOCATION STATE AMOUNT
        # Example: 12/07 Amazon.com*5S9VO0HA3 Amzn.com/bill WA 14.97
        patterns = [
            # Standard format: MM/DD Description Amount (at end of line or before next date)
            r'(\d{1,2}/\d{1,2})\s+(.+?)\s+(-?[\d,]+\.\d{2})(?:\s*$|\s+(?=\d{1,2}/\d{1,2}))',
            # Format with state code before amount
            r'(\d{1,2}/\d{1,2})\s+(.+?)\s+[A-Z]{2}\s+(-?[\d,]+\.\d{2})',
            # Format: MM/DD Description ending with amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+(\d+\.\d{2})\s*$',
        ]

        current_year = datetime.now().year

        # Look for statement date to determine year
        year_match = re.search(r'(\d{1,2}/\d{1,2}/(\d{2,4}))', text)
        if year_match:
            year_str = year_match.group(2)
            if len(year_str) == 2:
                current_year = 2000 + int(year_str)
            else:
                current_year = int(year_str)

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    date_str, description, amount_str = match.groups()

                    # Skip non-transaction lines
                    if self._is_skip_line(description):
                        continue

                    # Parse date
                    trans_date = self._parse_date(f"{date_str}/{current_year}")
                    if not trans_date:
                        continue

                    # Handle future dates (statement from previous year)
                    if trans_date > date.today():
                        trans_date = trans_date.replace(year=trans_date.year - 1)

                    # Parse amount
                    amount = Decimal(amount_str.replace(',', '').replace('-', ''))
                    if amount <= 0:
                        continue

                    # Clean description
                    description = self._clean_description(description)
                    if not description or len(description) < 3:
                        continue

                    merchant = self._extract_merchant(description)

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description,
                        amount=amount,
                        merchant=merchant,
                    ))

                except Exception as e:
                    logger.debug(f"Chase parse error: {e}")
                    continue

        return self._deduplicate(transactions)

    def _parse_wells_fargo_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Parse Wells Fargo PDF statement."""
        transactions = []

        # Wells Fargo format: M/D Description Amount Balance
        # Example: 7/1 Zelle From Jose Pineda Delgado on 07/01 Ref # SFC0Jfi0Jvun 440.00 2,387.25
        # The key is that there are TWO amounts at the end: the transaction amount and the balance
        # We need to capture only the first amount (transaction) not the balance

        # Pattern: Date Description Amount Balance (capture the first amount only)
        pattern = r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s*$'

        current_year = datetime.now().year

        for match in re.finditer(pattern, text, re.MULTILINE):
            try:
                date_str, description, amount_str, balance_str = match.groups()

                if self._is_skip_line(description):
                    continue

                trans_date = self._parse_date(f"{date_str}/{current_year}")
                if not trans_date:
                    continue

                if trans_date > date.today():
                    trans_date = trans_date.replace(year=trans_date.year - 1)

                # Use the first amount (transaction), not the second (balance)
                amount = Decimal(amount_str.replace(',', ''))
                if amount <= 0:
                    continue

                description = self._clean_description(description)
                if not description:
                    continue

                transactions.append(ExtractedTransaction(
                    date=trans_date,
                    description=description,
                    amount=amount,
                    merchant=self._extract_merchant(description),
                ))

            except Exception as e:
                logger.debug(f"Wells Fargo parse error: {e}")
                continue

        return self._deduplicate(transactions)

    def _parse_amex_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Parse American Express PDF statement."""
        transactions = []

        patterns = [
            # MM/DD/YY* MERCHANT AMOUNT
            r'(\d{2}/\d{2}/\d{2})\*?\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            # MM/DD/YY MERCHANT CITY STATE AMOUNT
            r'(\d{2}/\d{2}/\d{2})\s+(.+?)\s+[A-Z]{2}\s+\$?([\d,]+\.\d{2})',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                try:
                    date_str, description, amount_str = match.groups()

                    if self._is_skip_line(description):
                        continue

                    trans_date = datetime.strptime(date_str, '%m/%d/%y').date()
                    amount = Decimal(amount_str.replace(',', ''))

                    if amount <= 0:
                        continue

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description.strip(),
                        amount=amount,
                        merchant=self._extract_merchant(description),
                    ))

                except Exception as e:
                    logger.debug(f"AMEX parse error: {e}")
                    continue

        return self._deduplicate(transactions)

    def _parse_boa_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Parse Bank of America PDF statement."""
        transactions = []

        # BoA can be in Spanish, try both patterns
        patterns = [
            r'(\d{2}/\d{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            r'(\d{2}/\d{2}/\d{2,4})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
        ]

        current_year = datetime.now().year

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    groups = match.groups()
                    date_str = groups[0]
                    description = groups[1]
                    amount_str = groups[2]

                    if self._is_skip_line(description):
                        continue

                    trans_date = self._parse_date(date_str)
                    if not trans_date:
                        continue

                    amount = Decimal(amount_str.replace(',', ''))
                    if amount <= 0:
                        continue

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description.strip(),
                        amount=amount,
                        merchant=self._extract_merchant(description),
                    ))

                except Exception as e:
                    logger.debug(f"BoA parse error: {e}")
                    continue

        return self._deduplicate(transactions)

    def _parse_credit_union_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Parse credit union PDF statements (SchoolFirst, etc.)."""
        transactions = []

        # Credit union format: MM/DD Transaction Type Description Amount Balance
        patterns = [
            # With transaction type
            r'(\d{2}/\d{2})\s+(Deposit|Withdrawal|Debit Card|ACH|Transfer)\s+(.+?)\s+([\d,]+\.\d{2})-?\s+[\d,]+\.\d{2}',
            # Generic format
            r'(\d{2}/\d{2})\s+(.+?)\s+([\d,]+\.\d{2})-?\s+[\d,]+\.\d{2}',
        ]

        current_year = datetime.now().year

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    groups = match.groups()

                    if len(groups) == 4:
                        date_str, trans_type, description, amount_str = groups
                        description = f"{trans_type} {description}"
                    else:
                        date_str, description, amount_str = groups

                    if self._is_skip_line(description):
                        continue

                    trans_date = self._parse_date(f"{date_str}/{current_year}")
                    if not trans_date:
                        continue

                    if trans_date > date.today():
                        trans_date = trans_date.replace(year=trans_date.year - 1)

                    amount = Decimal(amount_str.replace(',', '').replace('-', ''))
                    if amount <= 0:
                        continue

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description.strip(),
                        amount=amount,
                        merchant=self._extract_merchant(description),
                    ))

                except Exception as e:
                    logger.debug(f"Credit union parse error: {e}")
                    continue

        return self._deduplicate(transactions)

    def _parse_generic_pdf(self, text: str) -> List[ExtractedTransaction]:
        """Generic PDF parser that tries multiple patterns."""
        transactions = []

        # Multiple patterns for different formats
        patterns = [
            # MM/DD/YYYY or MM/DD/YY format
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            # YYYY-MM-DD format
            r'(\d{4}-\d{2}-\d{2})\s+(.+?)\s+\$?([\d,]+\.\d{2})',
            # MM/DD format with amount
            r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})',
        ]

        current_year = datetime.now().year

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                try:
                    date_str, description, amount_str = match.groups()

                    if self._is_skip_line(description):
                        continue

                    trans_date = self._parse_date(date_str)
                    if not trans_date:
                        continue

                    if trans_date > date.today():
                        trans_date = trans_date.replace(year=trans_date.year - 1)

                    amount = Decimal(amount_str.replace(',', '').replace('-', ''))
                    if amount <= 0:
                        continue

                    description = self._clean_description(description)
                    if not description or len(description) < 3:
                        continue

                    transactions.append(ExtractedTransaction(
                        date=trans_date,
                        description=description,
                        amount=amount,
                        merchant=self._extract_merchant(description),
                    ))

                except Exception as e:
                    logger.debug(f"Generic parse error: {e}")
                    continue

        return self._deduplicate(transactions)

    def _extract_with_openai(self, text: str) -> List[ExtractedTransaction]:
        """Use OpenAI GPT-4 to extract transactions from statement text."""
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if not api_key:
            logger.warning("No OpenAI API key configured")
            return []

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            # Truncate text but try to keep transaction sections
            truncated_text = text[:15000]

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
2. Dates must be in YYYY-MM-DD format (infer year from context or use current year)
3. Amounts must be positive numbers (absolute values)
4. Clean up descriptions - remove extra spaces, phone numbers, and formatting artifacts
5. Skip headers, footers, balance summaries, interest rate info, and non-transaction lines
6. If a transaction has both a date and an amount, include it
7. For multi-line transactions, combine the description into one line

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
            cleaned_content = self._clean_json_response(raw_content)
            data = json.loads(cleaned_content)

            if not isinstance(data, dict) or 'transactions' not in data:
                logger.warning("OpenAI response missing 'transactions' key")
                return []

            transactions = []
            for t in data['transactions']:
                try:
                    trans_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                    amount = Decimal(str(abs(float(t['amount']))))
                    description = str(t['description']).strip()

                    if amount > 0 and description:
                        transactions.append(ExtractedTransaction(
                            date=trans_date,
                            description=description,
                            amount=amount,
                            merchant=self._extract_merchant(description)
                        ))
                except Exception as e:
                    logger.debug(f"Skipping invalid AI transaction: {t} - {e}")
                    continue

            return transactions

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return []

    def _clean_json_response(self, content: str) -> str:
        """Clean OpenAI response to extract valid JSON."""
        content = content.strip()
        if content.startswith('```'):
            lines = content.split('\n')
            lines = [l for l in lines if not l.strip().startswith('```')]
            content = '\n'.join(lines)

        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            content = content[start:end + 1]

        return content

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in various formats."""
        if not date_str:
            return None

        date_str = date_str.strip()
        current_year = datetime.now().year

        formats = [
            '%m/%d/%Y',
            '%m/%d/%y',
            '%Y-%m-%d',
            '%m/%d',
            '%m-%d-%Y',
            '%m-%d-%y',
            '%d/%m/%Y',
            '%d/%m/%y',
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt).date()
                # If year is 1900 (from %m/%d format), use current year
                if parsed.year == 1900:
                    parsed = parsed.replace(year=current_year)
                return parsed
            except ValueError:
                continue

        return None

    def _is_skip_line(self, description: str) -> bool:
        """Check if a line should be skipped (not a transaction)."""
        if not description:
            return True

        skip_patterns = [
            r'^balance\s*(forward)?$',
            r'^ending\s*balance',
            r'^beginning\s*balance',
            r'^total\s+',
            r'^subtotal',
            r'^dividends?\s+paid',
            r'^annual\s+percentage',
            r'^minimum\s+balance',
            r'^statement\s+period',
            r'^account\s+number',
            r'^page\s+\d+',
            r'^credit\s+limit',
            r'^available\s+credit',
            r'^interest\s+rate',
            r'^apr\s*$',
            r'^fees?\s+charged',
            r'^interest\s+charged',
            r'^new\s+balance',
            r'^previous\s+balance',
            r'^payment\s+due',
            r'^\d+\s+days\s+in',
            r'^date\s+of$',
            r'^transaction$',
            r'^merchant\s+name',
            r'^\$\s*amount$',
        ]

        desc_lower = description.lower().strip()
        for pattern in skip_patterns:
            if re.match(pattern, desc_lower):
                return True

        # Skip if too short
        if len(description.strip()) < 3:
            return True

        return False

    def _clean_description(self, description: str) -> str:
        """Clean up transaction description."""
        if not description:
            return ""

        # Remove phone numbers
        description = re.sub(r'\s*\d{3}[-.]?\d{3}[-.]?\d{4}\s*', ' ', description)

        # Remove extra whitespace
        description = ' '.join(description.split())

        # Remove trailing state codes if they're alone
        description = re.sub(r'\s+[A-Z]{2}\s*$', '', description)

        # Remove common noise
        description = re.sub(r'\s*https?://\S+', '', description)

        return description.strip()

    def _extract_merchant(self, description: str) -> str:
        """Extract merchant name from transaction description."""
        description = description.strip()

        # Remove location info (state codes at end)
        description = re.sub(r'\s+[A-Z]{2}\s*$', '', description)

        # Remove phone numbers
        description = re.sub(r'\s*\d{3}[-.]?\d{3}[-.]?\d{4}', '', description)

        # Remove reference numbers
        description = re.sub(r'\s*#?\d{6,}$', '', description)

        # Remove common suffixes
        description = re.sub(r'\s+(Amzn\.com/bill|g\.co/helppay#).*$', '', description, flags=re.IGNORECASE)

        # Take first part before common separators
        for sep in [' - ', ' * ', '  ', ' Ref #']:
            if sep in description:
                description = description.split(sep)[0]
                break

        return description.strip()[:100]

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

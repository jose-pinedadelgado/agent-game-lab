# Bamboo Money - System Design

## Document Information

| Field | Value |
|-------|-------|
| Project | Bamboo Money |
| Version | 1.0.0 |
| Status | Draft |
| Created | January 23, 2025 |

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           BAMBOO MONEY                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Browser   │    │   Mobile    │    │    API      │              │
│  │   Client    │    │   Browser   │    │   Client    │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                      │
│         └──────────────────┴──────────────────┘                      │
│                            │                                         │
│                            ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     DJANGO APPLICATION                       │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │    │
│  │  │Accounts │ │Statements│ │Transact.│ │ Budgets │ │Analytics│ │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │    │
│  │                          │                                   │    │
│  │  ┌───────────────────────┴───────────────────────────────┐  │    │
│  │  │                    SERVICES LAYER                      │  │    │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │    │
│  │  │  │PDF Parser│  │Categorizer│  │AI Advisor│            │  │    │
│  │  │  └──────────┘  └──────────┘  └──────────┘            │  │    │
│  │  └───────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│         ┌──────────────────┼──────────────────┐                     │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ PostgreSQL  │    │   OpenAI    │    │   Redis     │              │
│  │  Database   │    │    API      │    │   Cache     │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Django Templates + HTMX | Server-rendered UI with dynamic updates |
| **CSS Framework** | Bootstrap 5 | Responsive layout and components |
| **Charts** | Chart.js | Interactive data visualization |
| **Interactivity** | Alpine.js | Lightweight JavaScript framework |
| **Backend** | Django 5.2 | Web framework |
| **Database** | PostgreSQL 15 | Primary data store |
| **Cache** | Redis | Session storage, caching |
| **Task Queue** | Django Q2 | Background PDF processing |
| **AI/ML** | OpenAI API | Transaction parsing, categorization |
| **AI Agents** | CrewAI | Financial advisor agents |
| **Auth** | Django AllAuth | Authentication with social login |
| **PDF Processing** | pdfplumber, PyPDF2, pytesseract | Multi-strategy extraction |

---

## 2. Project Structure

```
bamboo_money/
├── manage.py                      # Django CLI
├── pyproject.toml                 # Dependencies (UV)
├── .env                           # Environment variables
├── .env.example                   # Template for .env
├── .gitignore
├── README.md
│
├── config/                        # Django project configuration
│   ├── __init__.py
│   ├── settings.py                # Main settings
│   ├── urls.py                    # Root URL configuration
│   ├── wsgi.py                    # WSGI entry point
│   └── asgi.py                    # ASGI entry point
│
├── apps/                          # Django applications
│   │
│   ├── accounts/                  # User management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # User model
│   │   ├── views.py               # Profile, settings
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/
│   │       └── accounts/
│   │           ├── profile.html
│   │           └── settings.html
│   │
│   ├── statements/                # PDF upload & processing
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # CreditCardStatement
│   │   ├── views.py               # Upload, history
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py          # Multi-strategy PDF parser
│   │   │   ├── extractors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── amex.py        # AMEX-specific patterns
│   │   │   │   ├── chase.py       # Chase patterns
│   │   │   │   └── generic.py     # Fallback patterns
│   │   │   └── ocr.py             # OCR utilities
│   │   ├── tasks.py               # Background processing tasks
│   │   └── templates/
│   │       └── statements/
│   │           ├── upload.html
│   │           └── history.html
│   │
│   ├── transactions/              # Transaction management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # Transaction
│   │   ├── views.py               # List, detail, edit
│   │   ├── urls.py
│   │   ├── filters.py             # Django-filter definitions
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── categorizer.py     # AI categorization
│   │   └── templates/
│   │       └── transactions/
│   │           ├── list.html
│   │           ├── detail.html
│   │           └── partials/
│   │               ├── _transaction_row.html
│   │               └── _category_select.html
│   │
│   ├── budgets/                   # Budget management
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # BudgetCategory, SpendingAlert
│   │   ├── views.py               # CRUD, alerts
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── signals.py             # Alert creation signals
│   │   └── templates/
│   │       └── budgets/
│   │           ├── manage.html
│   │           ├── alerts.html
│   │           └── partials/
│   │               ├── _category_card.html
│   │               └── _progress_bar.html
│   │
│   ├── analytics/                 # Dashboards & reports
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py               # Dashboard, trends, reports
│   │   ├── urls.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── aggregations.py    # Data aggregation queries
│   │   │   └── charts.py          # Chart data preparation
│   │   └── templates/
│   │       └── analytics/
│   │           ├── dashboard.html
│   │           ├── trends.html
│   │           └── partials/
│   │               ├── _spending_chart.html
│   │               └── _summary_cards.html
│   │
│   └── advisor/                   # AI advisor
│       ├── __init__.py
│       ├── apps.py
│       ├── views.py               # Insights, recommendations
│       ├── urls.py
│       ├── crews/
│       │   ├── __init__.py
│       │   ├── financial_advisor.py
│       │   └── config/
│       │       ├── agents.yaml
│       │       └── tasks.yaml
│       └── templates/
│           └── advisor/
│               ├── insights.html
│               └── chat.html
│
├── templates/                     # Global templates
│   ├── base.html                  # Master layout
│   ├── includes/
│   │   ├── _navbar.html
│   │   ├── _sidebar.html
│   │   ├── _footer.html
│   │   ├── _messages.html         # Flash messages
│   │   └── _pagination.html
│   ├── components/
│   │   ├── _card.html
│   │   ├── _modal.html
│   │   ├── _loading.html
│   │   └── _empty_state.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/                        # Static assets
│   ├── css/
│   │   ├── main.css               # Custom styles
│   │   └── components/
│   │       ├── cards.css
│   │       └── charts.css
│   ├── js/
│   │   ├── main.js                # Global JavaScript
│   │   ├── charts.js              # Chart initialization
│   │   └── htmx-config.js         # HTMX configuration
│   └── images/
│       ├── logo.svg
│       └── icons/
│
├── media/                         # User uploads
│   └── statements/                # PDF files (by year/month)
│
└── tests/                         # Test suite
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures
    ├── test_accounts.py
    ├── test_statements.py
    ├── test_transactions.py
    ├── test_budgets.py
    ├── test_analytics.py
    └── test_advisor.py
```

---

## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐
│      User       │       │  CreditCardStatement │
├─────────────────┤       ├─────────────────────┤
│ id (UUID) [PK]  │──┐    │ id (UUID) [PK]      │
│ email           │  │    │ user_id [FK]        │◄──┐
│ password        │  │    │ statement_file      │   │
│ first_name      │  ├───►│ bank_name           │   │
│ last_name       │  │    │ status              │   │
│ preferred_curr  │  │    │ uploaded_at         │   │
│ created_at      │  │    │ period_start        │   │
└─────────────────┘  │    │ period_end          │   │
                     │    └─────────────────────┘   │
                     │                              │
                     │    ┌─────────────────────┐   │
                     │    │    Transaction      │   │
                     │    ├─────────────────────┤   │
                     │    │ id (UUID) [PK]      │   │
                     ├───►│ user_id [FK]        │   │
                     │    │ statement_id [FK]   │───┘
                     │    │ category_id [FK]    │───┐
                     │    │ date                │   │
                     │    │ description         │   │
                     │    │ amount              │   │
                     │    │ merchant            │   │
                     │    │ is_recurring        │   │
                     │    │ is_flagged          │   │
                     │    │ notes               │   │
                     │    └─────────────────────┘   │
                     │                              │
                     │    ┌─────────────────────┐   │
                     │    │   BudgetCategory    │   │
                     │    ├─────────────────────┤   │
                     ├───►│ id (UUID) [PK]      │◄──┘
                     │    │ user_id [FK]        │
                     │    │ name                │
                     │    │ monthly_limit       │
                     │    │ color               │
                     │    │ icon                │
                     │    │ is_active           │
                     │    └─────────────────────┘
                     │
                     │    ┌─────────────────────┐
                     │    │   SpendingAlert     │
                     │    ├─────────────────────┤
                     └───►│ id (UUID) [PK]      │
                          │ user_id [FK]        │
                          │ alert_type          │
                          │ message             │
                          │ transaction_id [FK] │
                          │ category_id [FK]    │
                          │ is_read             │
                          │ created_at          │
                          └─────────────────────┘
```

### 3.2 Model Definitions

```python
# apps/accounts/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    preferred_currency = models.CharField(max_length=3, default='USD')
    timezone = models.CharField(max_length=50, default='America/Los_Angeles')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

```python
# apps/statements/models.py
import uuid
from django.db import models
from django.conf import settings

class CreditCardStatement(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    class Bank(models.TextChoices):
        AMEX = 'amex', 'American Express'
        CHASE = 'chase', 'Chase'
        WELLS_FARGO = 'wells_fargo', 'Wells Fargo'
        BOA = 'boa', 'Bank of America'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    statement_file = models.FileField(upload_to='statements/%Y/%m/')
    bank_name = models.CharField(max_length=20, choices=Bank.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    transaction_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']
```

```python
# apps/transactions/models.py
import uuid
from django.db import models
from django.conf import settings

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    statement = models.ForeignKey(
        'statements.CreditCardStatement',
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True
    )
    category = models.ForeignKey(
        'budgets.BudgetCategory',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )

    date = models.DateField(db_index=True)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    merchant = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    transaction_number = models.CharField(max_length=32, blank=True)

    # AI fields
    ai_category_suggestion = models.CharField(max_length=100, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)

    # User fields
    is_recurring = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'merchant']),
        ]
```

```python
# apps/budgets/models.py
import uuid
from django.db import models
from django.conf import settings

class BudgetCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=7, default='#3B82F6')
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'name']
        verbose_name_plural = 'Budget Categories'
        ordering = ['name']


class SpendingAlert(models.Model):
    class AlertType(models.TextChoices):
        APPROACHING = 'approaching', 'Approaching Limit'
        OVER_BUDGET = 'over_budget', 'Over Budget'
        LARGE_TRANSACTION = 'large_transaction', 'Large Transaction'
        UNUSUAL = 'unusual', 'Unusual Spending'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    message = models.TextField()
    transaction = models.ForeignKey(
        'transactions.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.ForeignKey(
        BudgetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

---

## 4. Service Layer Architecture

### 4.1 PDF Parser Service

```python
# apps/statements/services/parser.py
from dataclasses import dataclass
from typing import List, Optional, Protocol
from enum import Enum

class ParsingStrategy(Enum):
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"
    OCR = "ocr"
    AI = "ai"

@dataclass
class ExtractedTransaction:
    date: str
    description: str
    amount: float
    transaction_number: Optional[str] = None
    merchant: Optional[str] = None

class PDFExtractor(Protocol):
    """Protocol for PDF extraction strategies"""
    def extract(self, file_path: str) -> List[ExtractedTransaction]:
        ...

class StatementParser:
    """
    Multi-strategy PDF parser with fallback chain:
    1. pdfplumber (best for structured PDFs)
    2. PyPDF2 (fallback text extraction)
    3. OCR (for image-based PDFs)
    4. OpenAI (AI extraction as last resort)
    """

    def __init__(self, bank: str = 'generic'):
        self.bank = bank
        self.strategies = self._build_strategy_chain()

    def parse(self, file_path: str) -> List[ExtractedTransaction]:
        """Try each strategy until one succeeds"""
        for strategy in self.strategies:
            try:
                transactions = strategy.extract(file_path)
                if transactions and len(transactions) >= 3:
                    return transactions
            except Exception:
                continue
        return []

    def _build_strategy_chain(self) -> List[PDFExtractor]:
        from .extractors import (
            PdfPlumberExtractor,
            PyPDF2Extractor,
            OCRExtractor,
            AIExtractor
        )
        return [
            PdfPlumberExtractor(self.bank),
            PyPDF2Extractor(self.bank),
            OCRExtractor(self.bank),
            AIExtractor()
        ]
```

### 4.2 Categorization Service

```python
# apps/transactions/services/categorizer.py
from typing import List, Dict
from openai import OpenAI
from django.conf import settings
import json

class TransactionCategorizer:
    """AI-powered transaction categorization"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def categorize_batch(
        self,
        transactions: List[Dict],
        categories: List[str]
    ) -> List[Dict]:
        """
        Categorize multiple transactions in a single API call.
        Returns list with category and confidence for each transaction.
        """
        prompt = self._build_prompt(transactions, categories)

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        return json.loads(response.choices[0].message.content)['results']

    def _system_prompt(self) -> str:
        return """You are a financial transaction categorizer.
        Analyze each transaction and assign the most appropriate category.
        Return confidence scores between 0 and 1."""

    def _build_prompt(self, transactions: List[Dict], categories: List[str]) -> str:
        return f"""
        Categories: {', '.join(categories)}

        Transactions to categorize:
        {json.dumps(transactions, indent=2)}

        Return JSON: {{"results": [{{"index": 0, "category": "...", "confidence": 0.95}}]}}
        """
```

### 4.3 Analytics Service

```python
# apps/analytics/services/aggregations.py
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta

class SpendingAnalytics:
    """Aggregate spending data for dashboards and reports"""

    def __init__(self, user):
        self.user = user

    def get_dashboard_summary(self) -> dict:
        """Get key metrics for dashboard cards"""
        from apps.transactions.models import Transaction

        now = datetime.now()
        month_start = now.replace(day=1)

        qs = Transaction.objects.filter(
            user=self.user,
            date__gte=month_start
        )

        return {
            'total_spent': qs.aggregate(total=Sum('amount'))['total'] or 0,
            'transaction_count': qs.count(),
            'daily_average': qs.aggregate(avg=Avg('amount'))['avg'] or 0,
            'top_category': self._get_top_category(qs),
        }

    def get_spending_by_category(self, months: int = 1) -> list:
        """Get spending breakdown by category"""
        from apps.transactions.models import Transaction

        start_date = datetime.now() - timedelta(days=months * 30)

        return list(
            Transaction.objects.filter(
                user=self.user,
                date__gte=start_date
            ).values(
                'category__name',
                'category__color'
            ).annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')
        )

    def get_monthly_trends(self, months: int = 6) -> list:
        """Get monthly spending totals for trend chart"""
        from apps.transactions.models import Transaction

        start_date = datetime.now() - timedelta(days=months * 30)

        return list(
            Transaction.objects.filter(
                user=self.user,
                date__gte=start_date
            ).annotate(
                month=TruncMonth('date')
            ).values('month').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('month')
        )
```

---

## 5. URL Structure

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('apps.analytics.urls')),  # Dashboard is home
    path('statements/', include('apps.statements.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('budgets/', include('apps.budgets.urls')),
    path('advisor/', include('apps.advisor.urls')),
    path('profile/', include('apps.accounts.urls')),
]
```

### URL Map

| URL | View | Description |
|-----|------|-------------|
| `/` | `analytics:dashboard` | Main dashboard |
| `/statements/upload/` | `statements:upload` | Upload PDF |
| `/statements/history/` | `statements:history` | Upload history |
| `/transactions/` | `transactions:list` | Transaction list |
| `/transactions/<id>/` | `transactions:detail` | Single transaction |
| `/budgets/` | `budgets:manage` | Category management |
| `/budgets/alerts/` | `budgets:alerts` | Spending alerts |
| `/advisor/` | `advisor:insights` | AI insights |
| `/advisor/chat/` | `advisor:chat` | Chat interface |
| `/profile/` | `accounts:profile` | User profile |
| `/profile/settings/` | `accounts:settings` | Account settings |

---

## 6. Frontend Architecture

### 6.1 Template Hierarchy

```
base.html
├── includes/_navbar.html
├── includes/_sidebar.html
├── includes/_messages.html
└── {% block content %}
    │
    ├── analytics/dashboard.html
    │   ├── partials/_summary_cards.html
    │   ├── partials/_spending_chart.html
    │   └── partials/_recent_transactions.html
    │
    ├── statements/upload.html
    │   └── partials/_upload_form.html
    │
    ├── transactions/list.html
    │   ├── partials/_filter_form.html
    │   └── partials/_transaction_row.html (HTMX)
    │
    └── budgets/manage.html
        ├── partials/_category_card.html
        └── partials/_progress_bar.html
```

### 6.2 HTMX Integration Pattern

```html
<!-- Example: Category quick-edit -->
<div id="category-{{ category.id }}">
    <select
        hx-post="{% url 'transactions:update_category' transaction.id %}"
        hx-target="#category-{{ category.id }}"
        hx-swap="outerHTML"
        name="category">
        {% for cat in categories %}
            <option value="{{ cat.id }}" {% if cat == transaction.category %}selected{% endif %}>
                {{ cat.name }}
            </option>
        {% endfor %}
    </select>
</div>
```

### 6.3 Chart.js Configuration

```javascript
// static/js/charts.js
function createSpendingPieChart(elementId, data) {
    const ctx = document.getElementById(elementId);
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: data.colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `$${ctx.parsed.toFixed(2)}`
                    }
                }
            }
        }
    });
}
```

---

## 7. Background Task Processing

### 7.1 Task Queue Architecture

```python
# apps/statements/tasks.py
from django_q.tasks import async_task
from django.core.mail import send_mail

def process_statement(statement_id: str):
    """
    Background task to process uploaded PDF statement.
    Called after file upload to avoid blocking the request.
    """
    from apps.statements.models import CreditCardStatement
    from apps.statements.services.parser import StatementParser
    from apps.transactions.models import Transaction
    from apps.transactions.services.categorizer import TransactionCategorizer

    statement = CreditCardStatement.objects.get(id=statement_id)
    statement.status = 'processing'
    statement.save()

    try:
        # 1. Parse PDF
        parser = StatementParser(bank=statement.bank_name)
        extracted = parser.parse(statement.statement_file.path)

        # 2. Create transaction objects
        transactions = [
            Transaction(
                user=statement.user,
                statement=statement,
                date=t.date,
                description=t.description,
                amount=t.amount,
                merchant=t.merchant or '',
                transaction_number=t.transaction_number or ''
            )
            for t in extracted
        ]

        # 3. Bulk create
        Transaction.objects.bulk_create(transactions)

        # 4. Categorize
        categorizer = TransactionCategorizer()
        categories = list(
            statement.user.budgetcategory_set.values_list('name', flat=True)
        )
        # ... categorization logic

        # 5. Update status
        statement.status = 'completed'
        statement.transaction_count = len(transactions)
        statement.save()

    except Exception as e:
        statement.status = 'failed'
        statement.error_message = str(e)
        statement.save()


# Usage in view:
def upload_statement(request):
    # ... save statement ...
    async_task('apps.statements.tasks.process_statement', str(statement.id))
    return redirect('statements:history')
```

---

## 8. API Design (Optional REST API)

### 8.1 Endpoints

```python
# apps/api/urls.py (if adding REST API later)
urlpatterns = [
    path('transactions/', TransactionListAPI.as_view()),
    path('transactions/<uuid:id>/', TransactionDetailAPI.as_view()),
    path('categories/', CategoryListAPI.as_view()),
    path('dashboard/', DashboardAPI.as_view()),
    path('insights/', InsightsAPI.as_view()),
]
```

### 8.2 Response Formats

```json
// GET /api/dashboard/
{
    "summary": {
        "total_spent": 2345.67,
        "transaction_count": 42,
        "budget_health": 0.78
    },
    "spending_by_category": [
        {"name": "Dining", "amount": 456.78, "color": "#F59E0B"},
        {"name": "Groceries", "amount": 234.56, "color": "#10B981"}
    ],
    "recent_transactions": [
        {"id": "uuid", "date": "2025-01-20", "merchant": "...", "amount": 45.67}
    ]
}
```

---

## 9. Security Design

### 9.1 Authentication Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│  User   │────►│  Login  │────►│ AllAuth │────►│ Session │
│         │     │  Form   │     │  Verify │     │ Created │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
              ┌─────────────┐                  ┌─────────────┐
              │   Email/    │                  │   Google    │
              │  Password   │                  │   OAuth     │
              └─────────────┘                  └─────────────┘
```

### 9.2 Security Checklist

- [x] API keys in environment variables
- [x] CSRF protection enabled
- [x] Secure session cookies
- [x] Password hashing (bcrypt)
- [x] SQL injection prevention (ORM)
- [x] XSS prevention (template escaping)
- [x] File upload validation
- [ ] Rate limiting on AI endpoints
- [ ] Input sanitization

---

## 10. Deployment Architecture

### 10.1 Production Stack

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX                                │
│                    (Reverse Proxy + SSL)                     │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│        Gunicorn         │    │      Static Files       │
│    (WSGI Application)   │    │      (WhiteNoise)       │
└─────────────────────────┘    └─────────────────────────┘
              │
              ▼
┌─────────────────────────┐
│         Django          │
│      Application        │
└─────────────────────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌───────────┐    ┌───────────┐
│PostgreSQL │    │   Redis   │
│ Database  │    │   Cache   │
└───────────┘    └───────────┘
```

### 10.2 Environment Variables

```bash
# .env.example
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:pass@host:5432/bamboo_money
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# AllAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

---

## 11. Testing Strategy

### 11.1 Test Categories

| Type | Coverage Target | Framework |
|------|-----------------|-----------|
| Unit Tests | 80% | pytest |
| Integration Tests | Key flows | pytest-django |
| Property Tests | Edge cases | Hypothesis |
| E2E Tests | Critical paths | Playwright |

### 11.2 Test Examples

```python
# tests/test_statements.py
import pytest
from apps.statements.services.parser import StatementParser

class TestPDFParser:
    def test_amex_extraction(self, amex_pdf_fixture):
        parser = StatementParser(bank='amex')
        transactions = parser.parse(amex_pdf_fixture)

        assert len(transactions) > 0
        assert all(t.amount > 0 for t in transactions)
        assert all(t.date for t in transactions)

    @pytest.mark.parametrize("bank", ['amex', 'chase', 'wells_fargo'])
    def test_supported_banks(self, bank, sample_pdf):
        parser = StatementParser(bank=bank)
        # Should not raise
        parser.parse(sample_pdf)
```

---

## 12. Performance Considerations

### 12.1 Database Optimization

```python
# Indexes already defined in models
# Additional query optimizations:

# Use select_related for FK joins
Transaction.objects.select_related('category', 'statement')

# Use prefetch_related for reverse FK
User.objects.prefetch_related('transaction_set', 'budgetcategory_set')

# Aggregate queries for dashboard
Transaction.objects.filter(...).aggregate(
    total=Sum('amount'),
    count=Count('id')
)
```

### 12.2 Caching Strategy

```python
# Cache expensive AI results
from django.core.cache import cache

def get_spending_insights(user_id: str) -> dict:
    cache_key = f"insights:{user_id}"
    insights = cache.get(cache_key)

    if not insights:
        insights = generate_insights(user_id)  # Expensive AI call
        cache.set(cache_key, insights, timeout=3600)  # 1 hour

    return insights
```

---

## 13. Future Extensibility

### 13.1 Planned Features (Post-MVP)

1. **Bank Account Linking** - Plaid integration for automatic imports
2. **Investment Tracking** - Portfolio management
3. **Bill Reminders** - Upcoming payment notifications
4. **Multi-Currency** - Support for international users
5. **Mobile App** - React Native or Flutter client
6. **Data Export** - PDF reports, tax summaries

### 13.2 Extension Points

- Service layer for swappable implementations
- Abstract base classes for extractors
- Plugin system for new bank parsers
- Webhook support for external integrations

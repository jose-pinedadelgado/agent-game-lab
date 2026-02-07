# Bamboo Money - Integration Plan

## Overview

**Bamboo Money** is a unified personal finance application that consolidates the best features from three existing prototype projects into a single, production-ready Django application.

**Goal:** Create a comprehensive personal finance tool that helps users track spending, analyze transactions, and receive AI-powered financial advice.

---

## Source Projects Analysis

### 1. budget_app2 (Primary Reference)

**Location:** `research_projects/budget_app2`
**Status:** Most mature, actively developed (Dec 2024 - Jan 2025)

#### What It Was Doing
- **Dual Interface Architecture**: Streamlit prototype (chatbot + dashboard) alongside Django backend
- **Comprehensive Data Models**: 5 models (User, CreditCardStatement, BudgetCategory, Transaction, SpendingAlert)
- **AI-Powered Analysis**: OpenAI GPT-4 integration for transaction parsing and financial insights
- **PDF Processing Pipeline**: PyPDF2 + Tesseract OCR fallback for statement extraction
- **Interactive Dashboard**: Plotly visualizations with spending breakdowns
- **Chatbot Interface**: Pattern-matched responses for financial queries
- **Specification-Driven Development**: .kiro specs with requirements, design, and tasks

#### Wins to Extract
| Feature | Value | Priority |
|---------|-------|----------|
| Django models (5 complete) | Production-ready schema | P0 |
| PDF + OCR extraction | Handles image-based PDFs | P0 |
| OpenAI transaction parsing | Intelligent data extraction | P0 |
| Streamlit chatbot component | Rapid prototyping reference | P1 |
| Financial dashboard design | UX patterns | P1 |
| .kiro specification format | Documentation standard | P2 |

#### Technical Debt to Avoid
- Hardcoded OpenAI API key in views.py
- Incomplete Django templates (referenced but not present)
- Dual architecture complexity (Streamlit + Django)

---

### 2. budget_app (Secondary Reference)

**Location:** `research_projects/budget_app`
**Status:** Functional prototype (May 2025)

#### What It Was Doing
- **PDF Parsing with pdfplumber**: More reliable text extraction for structured PDFs
- **Regex Pattern Matching**: AMEX-specific transaction extraction
- **Working HTML Templates**: Complete upload, analysis, and dashboard pages
- **Session-Based Analysis Storage**: Stores AI results in Django sessions
- **Chart.js Visualizations**: Category and monthly spending charts

#### Wins to Extract
| Feature | Value | Priority |
|---------|-------|----------|
| pdfplumber integration | Better structured PDF parsing | P0 |
| AMEX regex pattern | Proven transaction extraction | P0 |
| upload.html template | Complete file upload UI | P0 |
| analysis_result.html | Analysis display template | P0 |
| analytics_dashboard.html | Chart.js integration | P1 |
| Bulk transaction creation | Efficient DB operations | P1 |

#### Technical Debt to Avoid
- Hardcoded OpenAI API key
- CSRF exemptions on endpoints
- Hardcoded demo data in dashboard

---

### 3. bamboo-budget (Tertiary Reference)

**Location:** `research_projects/bamboo-budget`
**Status:** Early development (May 2025)

#### What It Was Doing
- **Django AllAuth Integration**: Social login (Google, Facebook)
- **CrewAI Agent Structure**: Multi-agent AI framework for financial advice
- **Clean Project Scaffolding**: Proper Django app organization
- **Authentication Flow**: Login/logout redirects configured
- **View Stubs**: Home, add_transaction, transaction_list, monthly_report

#### Wins to Extract
| Feature | Value | Priority |
|---------|-------|----------|
| AllAuth configuration | Social login ready | P1 |
| CrewAI pyproject.toml | Agent dependencies | P1 |
| Site ID configuration | Multi-site support | P2 |
| View structure | Clean URL routing | P1 |

#### Technical Debt to Avoid
- Incomplete views (just render stubs)
- No actual data models
- Empty templates

---

## Integration Strategy

### Phase 1: Foundation (Day 1)

**Objective:** Create project structure and core configuration

```
bamboo_money/
├── manage.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
│
├── config/                    # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/             # From bamboo-budget AllAuth
│   ├── statements/           # PDF upload & parsing
│   ├── transactions/         # Transaction management
│   ├── budgets/              # Categories & limits
│   ├── analytics/            # Reports & dashboards
│   └── advisor/              # AI recommendations
│
├── templates/                 # From budget_app
├── static/
└── tests/
```

**Source Mapping:**
- Project structure → bamboo-budget (clean scaffolding)
- Settings base → bamboo-budget (AllAuth config)
- Dependencies → Merge all three pyproject.toml files

---

### Phase 2: Data Layer (Day 1-2)

**Objective:** Implement unified data models

**Source:** Primarily budget_app2 with enhancements

```python
# Models to create:
1. User (accounts) - Custom user with UUID, from budget_app2
2. CreditCardStatement (statements) - PDF metadata, from budget_app2
3. Transaction (transactions) - Core transaction data, merged
4. BudgetCategory (budgets) - Spending categories, from budget_app2
5. SpendingAlert (budgets) - Notifications, from budget_app2
6. MonthlyReport (analytics) - New, aggregated data
```

**Enhancements over originals:**
- Add `is_recurring` flag to Transaction
- Add `processing_status` to CreditCardStatement
- Add `icon` field to BudgetCategory
- Create proper indexes for query performance

---

### Phase 3: PDF Processing (Day 2-3)

**Objective:** Merge PDF parsing strategies

**Multi-Strategy Parser:**
```
1. Try pdfplumber (from budget_app) - Best for structured PDFs
   ↓ (if fails)
2. Try PyPDF2 (from budget_app2) - Fallback text extraction
   ↓ (if fails)
3. Try OCR (from budget_app2) - For image-based PDFs
   ↓ (if fails)
4. Use OpenAI (from budget_app2) - AI extraction as last resort
```

**Regex Patterns to Include:**
- AMEX pattern (from budget_app)
- Chase pattern (new)
- Wells Fargo pattern (new)
- Generic fallback pattern

---

### Phase 4: AI Integration (Day 3-4)

**Objective:** Implement intelligent features

**From budget_app/budget_app2:**
- Transaction categorization via OpenAI
- Spending analysis and insights
- Financial recommendations

**From bamboo-budget (new implementation):**
- CrewAI financial advisor agent
- Budget optimization crew
- Anomaly detection agent

**AI Features:**
1. Auto-categorize transactions on import
2. Generate monthly spending reports
3. Provide personalized savings recommendations
4. Detect unusual spending patterns
5. Answer natural language financial queries

---

### Phase 5: User Interface (Day 4-5)

**Objective:** Build complete frontend

**Templates from budget_app:**
- `upload.html` → `statements/upload.html`
- `analysis_result.html` → `analytics/analysis.html`
- `analytics_dashboard.html` → `analytics/dashboard.html`

**New Templates:**
- `base.html` - Master layout with navigation
- `accounts/login.html` - AllAuth customization
- `transactions/list.html` - Transaction browser
- `budgets/manage.html` - Category management
- `advisor/chat.html` - AI advisor interface

**Frontend Stack:**
- Bootstrap 5 (responsive layout)
- Chart.js (visualizations)
- HTMX (dynamic updates without full page reload)
- Alpine.js (lightweight interactivity)

---

### Phase 6: Authentication (Day 5)

**Objective:** Implement secure user management

**From bamboo-budget:**
- Django AllAuth configuration
- Google OAuth provider
- Email verification flow

**Enhancements:**
- Add "Remember me" functionality
- Implement password reset flow
- Add account deletion option
- Session timeout for security

---

### Phase 7: Testing & Polish (Day 6-7)

**Objective:** Ensure quality and reliability

**Test Categories:**
1. Unit tests for models
2. Integration tests for PDF parsing
3. API tests for views
4. Property-based tests (Hypothesis) for edge cases

**Polish Items:**
- Error handling and user feedback
- Loading states for AI operations
- Mobile-responsive layout
- Accessibility compliance

---

## Feature Mapping Matrix

| Feature | budget_app2 | budget_app | bamboo-budget | Bamboo Money |
|---------|-------------|------------|---------------|--------------|
| User Auth | Basic | None | AllAuth | AllAuth + enhanced |
| PDF Upload | PyPDF2 | pdfplumber | None | Both + OCR |
| Transaction Model | Full | Basic | None | Full + enhanced |
| AI Categorization | GPT-4 | GPT-3.5 | CrewAI ready | GPT-4 + CrewAI |
| Dashboard | Streamlit | Chart.js | Stub | Chart.js + Plotly |
| Budgets | Model only | None | None | Full UI |
| Alerts | Model only | None | None | Full system |
| Social Login | None | None | Configured | Working |

---

## Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| PDF parsing failures | Multi-strategy fallback chain |
| AI API rate limits | Implement caching and queuing |
| Data migration issues | Create rollback scripts |
| Performance at scale | Add database indexes early |

### Security Risks

| Risk | Mitigation |
|------|------------|
| API key exposure | Use environment variables only |
| CSRF attacks | Remove all @csrf_exempt decorators |
| File upload attacks | Validate file types and sizes |
| Session hijacking | Use secure session settings |

---

## Success Metrics

### Functional Requirements
- [ ] Users can upload PDF statements from 3+ banks
- [ ] Transactions are automatically categorized with >80% accuracy
- [ ] Dashboard shows spending breakdown by category
- [ ] AI advisor provides personalized recommendations
- [ ] Users can set and track budget limits

### Non-Functional Requirements
- [ ] Page load time < 2 seconds
- [ ] PDF processing < 30 seconds for 10-page statement
- [ ] Mobile-responsive design
- [ ] WCAG 2.1 AA accessibility compliance

---

## Post-Integration Actions

1. **Archive source projects:**
   - `budget_app` → `[ARCHIVED]budget_app`
   - `budget_app2` → `[ARCHIVED]budget_app2`
   - `bamboo-budget` → `[ARCHIVED]bamboo-budget`

2. **Update documentation:**
   - Update master `summary.md`
   - Create Bamboo Money README
   - Document API endpoints

3. **Future roadmap:**
   - Bank account linking (Plaid integration)
   - Investment tracking
   - Bill reminders
   - Multi-currency support

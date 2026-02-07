# Bamboo Money - Requirements Specification

## Document Information

| Field | Value |
|-------|-------|
| Project | Bamboo Money |
| Version | 1.0.0 |
| Status | Draft |
| Created | January 23, 2025 |

---

## 1. Introduction

### 1.1 Purpose

Bamboo Money is a personal finance management application that helps users:
- Track credit card spending through statement uploads
- Automatically categorize transactions using AI
- Set and monitor budgets by category
- Receive personalized financial advice

### 1.2 Scope

This document defines the functional and non-functional requirements for the initial release (MVP) of Bamboo Money.

### 1.3 Definitions

| Term | Definition |
|------|------------|
| Statement | A credit card statement PDF uploaded by the user |
| Transaction | A single charge or credit on a credit card |
| Category | A user-defined spending bucket (e.g., Groceries, Dining) |
| Budget | A monthly spending limit for a category |
| Alert | A notification triggered by spending patterns |

---

## 2. User Requirements

### 2.1 User Personas

#### Primary: Budget-Conscious Professional
- Age: 25-45
- Tech-savvy but time-constrained
- Has 1-3 credit cards
- Wants to understand spending without manual tracking
- Values automated insights over manual data entry

#### Secondary: Financial Planner
- Age: 30-55
- Actively manages household finances
- Multiple accounts and cards
- Wants detailed reports and trend analysis
- Willing to categorize and review transactions

### 2.2 User Stories

#### Authentication (AUTH)

| ID | Story | Priority |
|----|-------|----------|
| AUTH-01 | As a user, I want to create an account with my email so I can access my data securely | P0 |
| AUTH-02 | As a user, I want to log in with Google so I don't need another password | P1 |
| AUTH-03 | As a user, I want to reset my password via email if I forget it | P1 |
| AUTH-04 | As a user, I want to log out from all devices for security | P2 |

#### Statement Upload (STMT)

| ID | Story | Priority |
|----|-------|----------|
| STMT-01 | As a user, I want to upload a PDF credit card statement so my transactions are imported | P0 |
| STMT-02 | As a user, I want to see upload progress so I know the system is working | P1 |
| STMT-03 | As a user, I want to select my bank/card type so parsing is more accurate | P1 |
| STMT-04 | As a user, I want to view my upload history so I can track what's been imported | P2 |
| STMT-05 | As a user, I want to delete an uploaded statement and its transactions | P2 |

#### Transaction Management (TXN)

| ID | Story | Priority |
|----|-------|----------|
| TXN-01 | As a user, I want to view all my transactions in a list so I can review my spending | P0 |
| TXN-02 | As a user, I want transactions auto-categorized so I don't have to do it manually | P0 |
| TXN-03 | As a user, I want to filter transactions by date, category, or amount | P1 |
| TXN-04 | As a user, I want to search transactions by merchant name or description | P1 |
| TXN-05 | As a user, I want to change a transaction's category if the AI got it wrong | P1 |
| TXN-06 | As a user, I want to flag transactions for review later | P2 |
| TXN-07 | As a user, I want to add notes to transactions for context | P2 |
| TXN-08 | As a user, I want to mark transactions as recurring | P2 |

#### Budget Management (BDG)

| ID | Story | Priority |
|----|-------|----------|
| BDG-01 | As a user, I want to create spending categories with monthly limits | P0 |
| BDG-02 | As a user, I want to see how much I've spent vs. my budget for each category | P0 |
| BDG-03 | As a user, I want to edit or delete categories | P1 |
| BDG-04 | As a user, I want to assign colors to categories for visual distinction | P1 |
| BDG-05 | As a user, I want to receive alerts when I'm approaching or exceeding a budget | P1 |
| BDG-06 | As a user, I want to see budget progress as a visual bar or chart | P1 |

#### Analytics & Reporting (RPT)

| ID | Story | Priority |
|----|-------|----------|
| RPT-01 | As a user, I want to see a dashboard with my spending overview | P0 |
| RPT-02 | As a user, I want to see spending breakdown by category (pie/bar chart) | P0 |
| RPT-03 | As a user, I want to see monthly spending trends over time | P1 |
| RPT-04 | As a user, I want to see my top merchants by spending | P1 |
| RPT-05 | As a user, I want to compare this month to previous months | P2 |
| RPT-06 | As a user, I want to export my transactions to CSV | P2 |

#### AI Advisor (ADV)

| ID | Story | Priority |
|----|-------|----------|
| ADV-01 | As a user, I want AI-generated insights about my spending patterns | P1 |
| ADV-02 | As a user, I want personalized recommendations to save money | P1 |
| ADV-03 | As a user, I want to ask questions about my finances in natural language | P2 |
| ADV-04 | As a user, I want alerts about unusual spending patterns | P2 |

---

## 3. Functional Requirements

### 3.1 Authentication Module

#### FR-AUTH-01: User Registration
- **Description:** Users can create an account with email and password
- **Input:** Email, password, password confirmation
- **Validation:**
  - Email must be valid format and unique
  - Password minimum 8 characters with 1 number and 1 special character
  - Passwords must match
- **Output:** Account created, verification email sent
- **Acceptance Criteria:**
  - [ ] Registration form validates all fields
  - [ ] Duplicate email shows appropriate error
  - [ ] Verification email sent within 30 seconds
  - [ ] User cannot log in until email verified

#### FR-AUTH-02: Social Login (Google)
- **Description:** Users can authenticate via Google OAuth
- **Flow:**
  1. User clicks "Sign in with Google"
  2. Redirect to Google consent screen
  3. User grants permission
  4. Return to app with authenticated session
- **Acceptance Criteria:**
  - [ ] Google button visible on login page
  - [ ] New users auto-created on first Google login
  - [ ] Existing email users linked to Google account
  - [ ] Profile picture imported from Google

#### FR-AUTH-03: Session Management
- **Description:** Secure session handling
- **Requirements:**
  - Sessions expire after 24 hours of inactivity
  - "Remember me" extends to 30 days
  - Sessions invalidated on password change
- **Acceptance Criteria:**
  - [ ] Inactive users logged out automatically
  - [ ] Remember me persists across browser close
  - [ ] Password change logs out other sessions

---

### 3.2 Statement Processing Module

#### FR-STMT-01: PDF Upload
- **Description:** Users can upload credit card statement PDFs
- **Input:** PDF file (max 10MB), bank selection
- **Supported Banks:**
  - American Express
  - Chase
  - Wells Fargo
  - Bank of America
  - Generic (fallback)
- **Processing Steps:**
  1. Validate file type and size
  2. Store file securely
  3. Extract text (pdfplumber → PyPDF2 → OCR → AI)
  4. Parse transactions using bank-specific patterns
  5. Auto-categorize transactions
  6. Save to database
- **Acceptance Criteria:**
  - [ ] Only PDF files accepted
  - [ ] Files over 10MB rejected with message
  - [ ] Progress indicator shown during processing
  - [ ] Success message shows transaction count
  - [ ] Errors display user-friendly message

#### FR-STMT-02: Transaction Extraction
- **Description:** Extract transaction data from statement text
- **Output per transaction:**
  - Date (required)
  - Description/Merchant (required)
  - Amount (required)
  - Transaction ID (optional)
  - Location (optional)
- **Acceptance Criteria:**
  - [ ] 90%+ transactions extracted from supported banks
  - [ ] Amounts correctly parsed (handle $, commas, negatives)
  - [ ] Dates normalized to YYYY-MM-DD
  - [ ] Non-transactions filtered (balances, fees info)

#### FR-STMT-03: AI-Powered Extraction Fallback
- **Description:** Use OpenAI when regex parsing fails
- **Trigger:** Less than 5 transactions found via regex
- **Acceptance Criteria:**
  - [ ] AI extraction produces valid transaction objects
  - [ ] Processing completes within 60 seconds
  - [ ] Partial results saved if AI call fails

---

### 3.3 Transaction Module

#### FR-TXN-01: Transaction List
- **Description:** Display paginated list of user transactions
- **Features:**
  - Pagination (25 per page)
  - Sort by date (default), amount, merchant
  - Filter by: date range, category, amount range
  - Search by merchant/description
- **Display per transaction:**
  - Date
  - Merchant/Description
  - Amount (color-coded: red expense, green credit)
  - Category (with color indicator)
  - Statement source
- **Acceptance Criteria:**
  - [ ] Transactions load within 1 second
  - [ ] Filters apply without page reload (HTMX)
  - [ ] Search is case-insensitive
  - [ ] Empty state shown when no transactions

#### FR-TXN-02: Auto-Categorization
- **Description:** AI assigns categories to new transactions
- **Process:**
  1. Batch transactions by statement
  2. Send to OpenAI with user's category list
  3. Store suggested category with confidence score
  4. Auto-apply if confidence > 0.8
- **Acceptance Criteria:**
  - [ ] 80%+ transactions correctly categorized
  - [ ] Low-confidence items flagged for review
  - [ ] User corrections improve future suggestions

#### FR-TXN-03: Manual Category Override
- **Description:** Users can change transaction category
- **Input:** Transaction ID, new category ID
- **Acceptance Criteria:**
  - [ ] Dropdown shows all user categories
  - [ ] Change saves without page reload
  - [ ] Change reflected in dashboard immediately

---

### 3.4 Budget Module

#### FR-BDG-01: Category Management
- **Description:** CRUD operations for spending categories
- **Fields:**
  - Name (required, unique per user)
  - Monthly limit (required, positive decimal)
  - Color (hex code, default provided)
  - Icon (optional, from predefined set)
- **Default Categories (created on signup):**
  - Groceries (#10B981)
  - Dining (#F59E0B)
  - Transportation (#3B82F6)
  - Entertainment (#8B5CF6)
  - Shopping (#EC4899)
  - Utilities (#6B7280)
  - Other (#9CA3AF)
- **Acceptance Criteria:**
  - [ ] User can create custom categories
  - [ ] User can edit category name, limit, color
  - [ ] Deleting category moves transactions to "Other"
  - [ ] Cannot delete "Other" category

#### FR-BDG-02: Budget Tracking
- **Description:** Track spending against budget limits
- **Calculations:**
  - Current month spending per category
  - Percentage of budget used
  - Days remaining in month
  - Projected month-end spending
- **Display:**
  - Progress bar per category
  - Green (<80%), Yellow (80-100%), Red (>100%)
- **Acceptance Criteria:**
  - [ ] Spending updates in real-time after import
  - [ ] Progress bars visually accurate
  - [ ] Projections based on daily average

#### FR-BDG-03: Spending Alerts
- **Description:** Notify users of budget events
- **Alert Types:**
  - `approaching_limit`: 80% of budget reached
  - `over_budget`: 100% of budget exceeded
  - `large_transaction`: Single transaction > $100
  - `unusual_spending`: 50% above category average
- **Delivery:** In-app notification center
- **Acceptance Criteria:**
  - [ ] Alerts created automatically on trigger
  - [ ] User can dismiss/mark as read
  - [ ] Alert count shown in navigation

---

### 3.5 Analytics Module

#### FR-RPT-01: Dashboard Overview
- **Description:** Main financial summary page
- **Components:**
  1. **Summary Cards:**
     - Total spending (current month)
     - Transaction count
     - Top category
     - Budget health (% under budget)
  2. **Spending by Category:** Pie or donut chart
  3. **Recent Transactions:** Last 5 transactions
  4. **Budget Status:** All categories with progress bars
- **Acceptance Criteria:**
  - [ ] Dashboard loads within 2 seconds
  - [ ] Charts are interactive (hover for details)
  - [ ] Responsive on mobile devices

#### FR-RPT-02: Spending Trends
- **Description:** Historical spending analysis
- **Charts:**
  - Monthly spending (bar chart, last 6 months)
  - Category trends (line chart)
  - Day-of-week patterns (bar chart)
- **Acceptance Criteria:**
  - [ ] Charts render correctly with partial data
  - [ ] User can select date range
  - [ ] Export chart as image

#### FR-RPT-03: Merchant Analysis
- **Description:** Top merchants by spending
- **Display:**
  - Ranked list of top 10 merchants
  - Total spent per merchant
  - Transaction count per merchant
  - Trend indicator (up/down from last month)
- **Acceptance Criteria:**
  - [ ] Merchants grouped by normalized name
  - [ ] Click merchant to see transactions

---

### 3.6 AI Advisor Module

#### FR-ADV-01: Spending Insights
- **Description:** AI-generated analysis of spending patterns
- **Insights Generated:**
  - Highest spending category and comparison to average
  - Unusual transactions flagged
  - Recurring payments identified
  - Savings opportunities
- **Trigger:** Generated weekly or on-demand
- **Acceptance Criteria:**
  - [ ] Insights are specific to user's data
  - [ ] Plain language, actionable recommendations
  - [ ] Updates reflect recent transactions

#### FR-ADV-02: Financial Recommendations
- **Description:** Personalized advice using CrewAI agents
- **Agent Roles:**
  - Analyst: Reviews spending patterns
  - Advisor: Generates recommendations
- **Output:** 3-5 specific, actionable recommendations
- **Acceptance Criteria:**
  - [ ] Recommendations are relevant and realistic
  - [ ] User can request new recommendations
  - [ ] Processing completes within 30 seconds

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Page load time | < 2 seconds | Time to interactive |
| PDF processing | < 30 seconds | For 10-page statement |
| API response time | < 500ms | 95th percentile |
| Database queries | < 100ms | Average query time |
| Concurrent users | 100 | Without degradation |

### 4.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Password storage | bcrypt with salt |
| API keys | Environment variables only |
| HTTPS | Required for all connections |
| CSRF protection | Django middleware enabled |
| XSS prevention | Template auto-escaping |
| File uploads | Type validation, size limits |
| Session security | HttpOnly, Secure cookies |

### 4.3 Reliability

| Requirement | Target |
|-------------|--------|
| Uptime | 99.5% |
| Data backup | Daily automated backups |
| Error handling | Graceful degradation |
| Logging | All errors logged with context |

### 4.4 Usability

| Requirement | Implementation |
|-------------|----------------|
| Responsive design | Mobile-first, works on all devices |
| Accessibility | WCAG 2.1 AA compliance |
| Browser support | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| Error messages | User-friendly, actionable |
| Loading states | Visual feedback for all async operations |

### 4.5 Maintainability

| Requirement | Implementation |
|-------------|----------------|
| Code style | Black + Ruff formatting |
| Documentation | Docstrings on all public functions |
| Test coverage | Minimum 80% |
| Dependency management | UV with locked versions |

---

## 5. Constraints

### 5.1 Technical Constraints
- Must use Django 5.x framework
- Must use PostgreSQL for production (SQLite for development)
- Must support Python 3.11+
- OpenAI API for AI features (no local models)

### 5.2 Business Constraints
- MVP must be completable in 7 days
- No third-party paid services beyond OpenAI
- No bank account linking in MVP (PDF upload only)

### 5.3 Regulatory Constraints
- No storage of full credit card numbers
- User data deletion on request (GDPR compliance)
- Clear privacy policy required

---

## 6. Acceptance Criteria Summary

### MVP Checklist

#### Must Have (P0)
- [ ] User registration and login
- [ ] PDF statement upload (AMEX, Chase)
- [ ] Transaction extraction and display
- [ ] Auto-categorization
- [ ] Basic dashboard with spending by category
- [ ] Budget categories with limits

#### Should Have (P1)
- [ ] Google social login
- [ ] Budget alerts
- [ ] Spending trends charts
- [ ] AI-generated insights
- [ ] Transaction search and filter
- [ ] Mobile-responsive design

#### Nice to Have (P2)
- [ ] Transaction notes and flags
- [ ] CSV export
- [ ] Natural language queries
- [ ] Multiple bank support
- [ ] Recurring transaction detection

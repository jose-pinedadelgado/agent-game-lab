# Bamboo Money

A personal finance management application that helps you track credit card spending, categorize transactions, and gain AI-powered insights into your finances.

## Features

- **PDF Statement Upload**: Upload credit card statements from major banks (AMEX, Chase, Wells Fargo, Bank of America)
- **Automatic Transaction Extraction**: Intelligent parsing of PDF statements to extract transactions
- **Smart Categorization**: Transactions are automatically assigned to budget categories
- **Budget Management**: Set monthly spending limits for each category and track progress
- **Dashboard Analytics**: Visualize spending patterns with interactive charts
- **AI Insights**: Get personalized recommendations based on your spending habits
- **Spending Alerts**: Receive notifications when approaching or exceeding budget limits

## Tech Stack

- **Backend**: Django 5.2
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Django AllAuth with Google OAuth support
- **PDF Processing**: pdfplumber, PyPDF2
- **Frontend**: Bootstrap 5, Chart.js, HTMX
- **AI/ML**: OpenAI API (for advanced features)

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [UV](https://docs.astral.sh/uv/) package manager

### Installation

1. **Navigate to the project directory**:
   ```bash
   cd bamboo_money
   ```

2. **Create virtual environment and install dependencies with UV**:
   ```bash
   # Create venv and install all dependencies in one command
   uv sync
   ```

3. **Set up environment variables**:
   ```bash
   # Copy the example file (Windows)
   copy .env.example .env

   # Or on macOS/Linux
   cp .env.example .env

   # Edit .env and add your settings:
   # - SECRET_KEY: Generate a new Django secret key
   # - OPENAI_API_KEY: Your OpenAI API key (optional, for AI features)
   ```

4. **Run database migrations**:
   ```bash
   uv run python manage.py migrate
   ```

5. **Create a superuser** (admin account):
   ```bash
   uv run python manage.py createsuperuser
   ```

6. **Start the development server**:
   ```bash
   uv run python manage.py runserver
   ```

7. **Open your browser** and go to: http://127.0.0.1:8000

## Usage Guide

### 1. Create an Account

- Click "Sign Up" in the navigation bar
- Enter your email and create a password
- Default budget categories will be created automatically

### 2. Upload a Statement

- Go to "Upload Statement" in the sidebar
- Select your bank/card issuer from the dropdown
- Upload your PDF credit card statement
- The system will extract and categorize transactions automatically

### 3. Review Transactions

- Go to "Transactions" to see all imported transactions
- Use filters to search by date, category, or keyword
- Click on a transaction to see details
- Change categories using the dropdown (changes save automatically via HTMX)

### 4. Manage Budgets

- Go to "Budgets" to see your spending progress
- Each category shows how much you've spent vs. your limit
- Click "Add Category" to create new budget categories
- Edit or delete categories as needed

### 5. View Insights

- Go to "Insights" for AI-generated spending analysis
- See month-over-month comparisons
- Get personalized recommendations

### 6. Monitor Alerts

- Click the bell icon in the navigation bar
- View alerts for:
  - Approaching budget limits (80%)
  - Exceeded budgets
  - Large transactions

## Project Structure

```
bamboo_money/
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/          # User management
│   ├── statements/        # PDF upload & parsing
│   ├── transactions/      # Transaction management
│   ├── budgets/           # Categories & alerts
│   ├── analytics/         # Dashboard & charts
│   └── advisor/           # AI insights
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── media/                 # User uploads
└── tests/                 # Test suite
```

## Supported Banks

The PDF parser includes specific patterns for:
- American Express (AMEX)
- Chase
- Wells Fargo
- Bank of America
- Generic (fallback for other banks)

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format with black
black .

# Lint with ruff
ruff check .
```

### Database Reset

```bash
# Delete SQLite database and re-run migrations
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Enable debug mode (True/False) | No (default: True) |
| `DATABASE_URL` | Database connection string | No (default: SQLite) |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | No |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | No |

## Roadmap

- [ ] AI-powered transaction categorization
- [ ] Natural language financial queries
- [ ] Bank account linking (Plaid integration)
- [ ] Recurring transaction detection
- [ ] CSV export
- [ ] Mobile app

## License

This project is for personal use. All rights reserved.

---

Built with Django and AI

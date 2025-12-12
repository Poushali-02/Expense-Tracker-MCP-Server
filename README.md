# Expense Tracker MCP Server

A comprehensive personal finance management system built with FastMCP (Model Context Protocol) for Claude Desktop integration. This server provides secure, authenticated transaction tracking with advanced analytics and reporting capabilities.

## Features

- 🔐 **Secure Authentication**: JWT-based user authentication with password hashing
- 💰 **Dual Transaction Types**: Track both expenses and income (credits)
- 📊 **Advanced Analytics**: Category breakdowns, date filtering, and financial summaries
- 🔄 **Recurring Transactions**: Support for daily, weekly, monthly, and yearly frequencies
- 🏷️ **Flexible Categorization**: 25+ predefined categories with custom tags
- 📅 **Date Range Filtering**: Analyze transactions by custom time periods
- 📈 **Financial Reports**: Monthly reports, balance calculations, and spending insights
- 🔒 **User Isolation**: Each user sees only their own data
- ⚡ **FastMCP Integration**: Seamless Claude Desktop integration

## Quick Start

### Prerequisites
- Python 3.13+
- PostgreSQL 15+
- Claude Desktop (for MCP integration)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/expense-tracker-mcp.git
   cd expense-tracker-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database:**
   ```sql
   CREATE DATABASE expense_tracker;
   ```

4. **Configure environment variables:**
   Create a `.env` file:
   ```env
   DB_HOST=localhost
   DB_NAME=expense_tracker
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_PORT=5432
   SECRET_KEY=your_secret_key_here
   TOKEN_EXPIRY_HOURS=24
   ```

5. **Initialize database:**
   ```bash
   python Database/init_db.py
   ```

6. **Run the MCP server:**
   ```bash
   python main.py
   ```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": ["/path/to/expense-tracker-mcp/main.py"],
      "env": {
        "PYTHONPATH": "/path/to/expense-tracker-mcp"
      }
    }
  }
}
```

## Authentication

### User Registration
```python
# Register a new user
register_user(
    username="your_username",
    email="your_email@example.com",
    password="SecurePass123!",
    full_name="Your Full Name"
)
```

### User Login
```python
# Login and get JWT token
result = login_user(
    username="your_username",
    password="SecurePass123!"
)
# Returns: {"token": "eyJ...", "user_id": "uuid", "expires_at": "timestamp"}
```

### Using Authenticated Tools
All transaction tools require a valid JWT token:
```python
# Example: Add a transaction
addTransaction(
    token="your_jwt_token_here",
    amount=50.00,
    category="groceries",
    transaction_type="expense",
    payment_method="credit_card"
)
```

## Transaction Management

### Transaction Types
- **expense**: Money spent (debits)
- **credit**: Money received (income/credits)

### Status Values
- **completed**: Transaction finalized
- **pending**: Transaction in progress
- **cancelled**: Transaction cancelled

### Frequency Options
- **none**: One-time transaction
- **daily**: Repeats every day
- **weekly**: Repeats every week
- **monthly**: Repeats every month
- **yearly**: Repeats every year

### Supported Categories
- Housing & Maintenance (rent, utilities, repairs)
- Transportation (fuel, public transport, car maintenance)
- Groceries & Food (groceries, dining out, restaurants)
- Health & Fitness (healthcare, gym, sports)
- Entertainment & Leisure (movies, games, hobbies)
- Education & Self-Development (courses, books, training)
- Insurance (health, car, home insurance)
- Investment & Financial (investments, savings, banking fees)
- Essential Services (internet, phone, subscriptions)
- And 15+ more categories...

## API Reference

### Authentication Tools

#### register_user
Creates a new user account with secure password hashing.
- **Parameters:** username, email, password, full_name
- **Returns:** Success status with user details
- **Password Requirements:** Min 8 chars, uppercase, lowercase, digit

#### login_user
Authenticates user and returns JWT token.
- **Parameters:** username, password
- **Returns:** JWT token, user_id, expiry timestamp
- **Token Validity:** 24 hours

#### verify_token
Validates JWT token expiry and signature.
- **Parameters:** token
- **Returns:** Token validity status

#### change_password
Updates user password with old password verification.
- **Parameters:** user_id, old_password, new_password
- **Returns:** Success status

### Transaction Management Tools

#### addTransaction
Creates a new transaction with automatic timestamping.
- **Parameters:** token, amount, category, transaction_type, payment_method, status, frequency, transaction_date, tags, notes
- **Auto-Features:** UUID generation, created_at timestamp
- **Required:** token, amount, category, transaction_type

#### get_all_transactions
Retrieves all user transactions.
- **Parameters:** token
- **Returns:** Complete transaction list with full details
- **Sorting:** Newest first (descending date order)

#### updateTransaction
Modifies existing transaction (partial updates supported).
- **Parameters:** token, transaction_id, and any fields to update
- **Auto-Features:** Updates "updated_at" timestamp
- **Flexibility:** Only provide fields to modify

#### delete_transaction
Permanently removes a transaction.
- **Parameters:** token, transaction_id
- **Returns:** Status and confirmation message
- **Warning:** This operation cannot be undone

### Transaction Retrieval & Analysis Tools

#### get_selected_transactions
Retrieves transactions within date range.
- **Parameters:** token, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
- **Returns:** Filtered transaction list
- **Sorting:** Newest first

#### get_total_transactions
Calculates total amount with optional filters.
- **Parameters:** token, optional start_date, end_date, category
- **Returns:** Total amount, breakdown by transaction type
- **Filtering:** Date range and/or category

#### get_top_transaction_categories
Identifies top 5 highest individual transactions.
- **Returns:** Separate lists for expenses and credits
- **Use Case:** Identify major spending patterns

### Financial Summary & Analysis Tools

#### get_summary
Comprehensive financial analysis with advanced filtering.
- **Parameters:** token, optional filters (type, category, tags, payment_method, status, frequency, date range)
- **Returns:** Transaction list + detailed statistics
- **Statistics:** Total amount, count, average, category breakdown

#### balance
Calculates net financial position.
- **Returns:** Total credits, total expenses, net balance
- **Use Case:** Quick financial health check

#### monthly_report
Generates detailed report for specific month/year.
- **Parameters:** token, year (YYYY), month (1-12)
- **Returns:** Separate expense/credit lists + summary statistics
- **Use Case:** Monthly financial review

## 4. Financial Summary & Analysis Tools

#### get_summary
Comprehensive financial analysis with advanced filtering.
- **Parameters:** token, optional filters (type, category, tags, payment_method, status, frequency, date range)
- **Returns:** Transaction list + detailed statistics
- **Statistics:** Total amount, count, average, category breakdown

#### balance
Calculates net financial position.
- **Returns:** Total credits, total expenses, net balance
- **Use Case:** Quick financial health check

#### monthly_report
Generates detailed report for specific month/year.
- **Parameters:** token, year (YYYY), month (1-12)
- **Returns:** Separate expense/credit lists + summary statistics
- **Use Case:** Monthly financial review

## Example Usage

### Basic Transaction Workflow

```python
# 1. Register user
register_user("johndoe", "john@example.com", "SecurePass123!", "John Doe")

# 2. Login to get token
login_result = login_user("johndoe", "SecurePass123!")
token = login_result["token"]

# 3. Add transactions
addTransaction(token, 25.50, "groceries", "expense", "credit_card", "completed", "none")
addTransaction(token, 1500.00, "salary", "credit", "bank_transfer", "completed", "monthly")

# 4. Get balance
balance_result = balance(token)
# Returns: {"total_credits": 1500.00, "total_expenses": 25.50, "net_balance": 1474.50}

# 5. Get monthly report
monthly_report(token, 2024, 12)
```

### Advanced Filtering

```python
# Get transactions for specific date range
get_selected_transactions(token, "2024-12-01", "2024-12-31")

# Get total for specific category
get_total_transactions(token, category="groceries")

# Get comprehensive summary with filters
get_summary(token, transaction_type="expense", category="food", start_date="2024-12-01")
```

## Security Features

- **Password Hashing:** bcrypt with salt rounds
- **JWT Authentication:** Secure token-based access
- **User Isolation:** Database-level user data separation
- **Token Expiry:** 24-hour token validity
- **Password Requirements:** Strong password validation
- **Input Validation:** Comprehensive parameter validation

## Database Schema

### Users Table
- user_id (UUID, Primary Key)
- username (VARCHAR, Unique)
- full_name (VARCHAR)
- email (VARCHAR, Unique)
- password_hash (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- active (BOOLEAN)

### Transactions Table
- user_id (UUID, Foreign Key)
- transaction_id (UUID, Primary Key)
- transaction_type (VARCHAR: expense/credit)
- transaction_date (DATE)
- amount (DECIMAL)
- category (VARCHAR)
- tags (VARCHAR)
- notes (VARCHAR)
- payment_method (VARCHAR)
- status (VARCHAR: completed/pending/cancelled)
- frequency (VARCHAR: none/daily/weekly/monthly/yearly)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

## Dependencies

- fastmcp>=2.13.3
- psycopg2-binary>=2.9.9
- bcrypt>=4.0.0
- pyjwt>=2.8.0
- python-dotenv>=1.0.0

## Development

### Running Tests
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_auth.py
```

### Code Quality
```bash
# Run linting
python -m flake8

# Run type checking
python -m mypy
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions or issues:
- Open an issue on GitHub
- Check the documentation in this README
- Review the code comments for implementation details

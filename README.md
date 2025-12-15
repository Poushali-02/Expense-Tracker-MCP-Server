# Transaction Tracker MCP Server

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

## LOCAL INSTALLATION GUIDE
IF YOU WANT TO USE THIS SERVER LOCALLY, CLONE THIS REPOSITORY AND SET IT UP AS SHOWN.

#### Prerequisites
- Python 3.13+
- uv
- PostgreSQL 15+
- Claude Desktop (for MCP integration)

#### Installation

Make sure you have uv installed in your system. This system was built using uv.
To install uv use -

   ```bash
   pip install uv
   ```

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Poushali-02/Expense-Tracker-MCP-Server.git
   cd Expense-Tracker-MCP-Server
   ```

2. **Install dependencies:**
   ```bash
   uv venv
   .venv\Scripts\activate # windows
   source .venv/bin/activate # macOs / Linux

   uv pip install -r requirements.txt
   ```

3. **Check and run the MCP server:**
   ```bash
   uv run fastmcp dev main.py  # this gives the mcp inspector tool to check all the functions
   uv run fastmcp run main.py  # this runs the server
   ```

### Claude Desktop Configuration

Since you have uv installed, running this command will add the server to your Claude Desktop:
```bash
uv run fastmcp install claude-desktop main.py
```
Or manually add it to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "Expense Tracker MCP Server": {
      "command": "uv",
      "args": [
        "--directory",
        "absolute\\path\\to\\ExpenseTrackerMCP",
        "run",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "main.py"
      ],
      "env": {},
      "transport": "stdio",
      "type": null,
      "cwd": null,
      "timeout": null,
      "description": null,
      "icon": null,
      "authentication": null
    }
  }
}
```

**How to access claude_desktop_config.json:**
1. Open Claude Desktop
2. Click your profile (bottom right) → Settings
3. Click "Developer" in the sidebar
4. Click "Edit Config" to open the JSON file in your editor


## REMOTE SERVER SETUP GUIDE

THIS SERVER HAS BEEN DEPLOYED USING [fastmcp cloud](https://fastmcp.cloud) 
FOR SETTING UP SEE THIS PART.

### CLAUDE PRO USERS: INSTALLATION GUIDE

If you have Claude Pro account, things are very easy.

- Just go to settings (from your Profile name)
- Click on Connectors
- Click on "Add custom Connector"
- On the popup add a name (e.g: "Transaction Tracker")
- On the URL section add this url - https://transaction-tracker.fastmcp.app/mcp
- Restart Claude

### CLAUDE FREE USERS

If you are a Claude Free Plan user (like me). Follow these steps

1. Open Claude Developer Settings

- Open Claude Desktop
- Click your profile (bottom right) → Settings
- Click "Developer" in the sidebar
- Click "Edit Config" to open the JSON file in your editor

2. Add this json to the file:

```json
{
  "mcpServers": {
    "Transaction Tracker": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://transaction-tracker.fastmcp.app/mcp"
      ]
    }
  }
}
```

# FEATURES

## Authentication

### User Registration
Use the Claude client to register with `register_user` tool (username, password, email, full_name).

### User Login
Use the Claude client with `login_user` tool (username, password) to get your JWT token.


### Using Authenticated Tools
Here is the list of tools available right now for this server.

#### Authentication & User Management
1. **register_user** ✅ - Registers new user
2. **login_user** ✅ - Authentication
3. **verify_token** ✅ - Token validation
4. **change_password** ✅ - Password change

#### Transaction Management
5. **addTransaction** ✅ - Adds transactions to database for user
6. **get_all_transactions** ✅ - Retrieves all transactions
7. **updateTransaction** ✅ - Updates transactions
8. **delete_transaction** ✅ - Deletes transactions

#### Transaction Retrieval & Analysis
9. **get_selected_transactions** ✅ - Retrieves transactions for date range (example: 2025-12-10 to 2025-12-15)
10. **get_total_transactions** ✅ - Calculates total transactions for a category
11. **get_top_transaction_categories** ✅ - Identifies top 5 expenses and credits

#### Financial Summary & Analysis
12. **get_summary** ✅ - Generates comprehensive analysis with category breakdown
13. **getBalance** ✅ - Calculates net balance
14. **monthly_report** ✅ - Generates monthly report with summary statistics (example: December 2025)


## Transaction Management

#### Transaction Types
- **expense**: Money spent (debits)
- **credit**: Money received (income/credits)

#### Status Values
- **completed**: Transaction finalized
- **pending**: Transaction in progress
- **cancelled**: Transaction cancelled

#### Frequency Options
- **none**: One-time transaction
- **daily**: Repeats every day
- **weekly**: Repeats every week
- **monthly**: Repeats every month
- **yearly**: Repeats every year

#### Supported Categories
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

## Security Features

- **Password Hashing:** bcrypt with salt rounds
- **JWT Authentication:** Secure token-based access
- **User Isolation:** Database-level user data separation
- **Token Expiry:** 24-hour token validity
- **Password Requirements:** Strong password validation
- **Input Validation:** Comprehensive parameter validation

## Dependencies

- fastmcp>=2.13.3
- asyncpg>=0.31.0
- bcrypt>=4.0.0
- pyjwt>=2.8.0
- python-dotenv>=1.0.0

## Support

For questions or issues:
- Open an issue on GitHub
- Check the documentation in this README
- Review the code comments for implementation details
- Please don't judge
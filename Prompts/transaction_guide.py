def transaction_guide():
    return """When adding a transaction, you MUST use only the following valid values:

## Categories (use expense://categories resource for full list):
- food, electronics, transport, emi_loans, shopping, entertainment
- housing, utilities, health, education, personal_care, travel
- gifts_donations, investments, insurance, taxes, subscriptions, miscellaneous

## Tags/Subcategories:
Each category has specific tags. Query expense://category/{category_name} to get valid tags.
Example: expense://category/food returns: groceries, dining_out, coffee_tea, snacks, etc.

## Status (REQUIRED - pick one):
- pending: Transaction not yet completed
- completed: Transaction finished
- cancelled: Transaction was cancelled

## Payment Methods (REQUIRED - pick one):
- cash, card, upi, bank, wallet, cheque, other

## Frequency (optional):
- none: One-time transaction (default)
- daily, weekly, monthly, yearly: Recurring transaction

## Transaction Type (REQUIRED):
- expense: Money going out (debit)
- credit: Money coming in (income)

## Date Format:
- Use YYYY-MM-DD format (e.g., 2025-12-17)

IMPORTANT: Always validate user input against these values before calling add_transaction or bulk_add_transactions tools."""

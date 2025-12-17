def validate():
    return  """QUICK REFERENCE - Valid Transaction Values:

┌─────────────────┬──────────────────────────────────────────────────┐
│ Field           │ Valid Values                                      │
├─────────────────┼──────────────────────────────────────────────────┤
│ transaction_type│ expense, credit                                   │
│ status          │ pending, completed, cancelled                     │
│ payment_method  │ cash, card, upi, bank, wallet, cheque, other     │
│ frequency       │ none, daily, weekly, monthly, yearly              │
│ date format     │ YYYY-MM-DD (e.g., 2025-12-17)                    │
└─────────────────┴──────────────────────────────────────────────────┘

CATEGORIES: food, electronics, transport, emi_loans, shopping, 
entertainment, housing, utilities, health, education, personal_care, 
travel, gifts_donations, investments, insurance, taxes, subscriptions, miscellaneous

For subcategories/tags, use: expense://category/{category_name}

Example: User says "Add coffee expense 150 rupees"
→ category: food
→ tags: coffee_tea (from expense://category/food)
→ transaction_type: expense
→ status: completed (default for past expenses)
→ payment_method: Ask user or default to 'cash'"""

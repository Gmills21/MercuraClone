# Mercura Clone - Sales Quote System

This project now includes a Sales Representative User Interface and Quote Generation capabilities.

## Prerequisites

1.  **Backend**: Python 3.9+, Supabase Account.
2.  **Frontend**: Node.js 18+.

## Setup & Running

### 1. Database Setup
To create the necessary tables, copy the `SUPABASE_SCHEMA` string from `app/models.py` (lines ~122+) and run it in your Supabase SQL Editor.

### 2. Backend (API)
The backend now includes routes for Quotes, Customers, and Products.

```bash
# Activate virtual environment
.\.venv\Scripts\Activate

# Install dependencies (if any new ones, though standard fastapi/supabase used)
pip install -r requirements.txt

# Seed Data (Optional - creates User, Customers, Products, Quotes)
$env:PYTHONPATH="."
python scripts/seed_data.py

# Run Server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend (Sales UI)
The new frontend is located in the `frontend/` directory.

```bash
cd frontend

# Install dependencies
npm install

# Run Development Server
npm run dev
```

Visit `http://localhost:5173` to access the Sales Dashboard.

## Features Added

-   **Dashboard**: Overview of revenue, quotes, and quick actions.
-   **Quote Builder**: Search products, add to quote, calculate totals.
-   **Quote Management**: List quotes, track status (Draft, Pending Approval, etc).
-   **Customers**: Basic customer list.
-   **Product Search**: Search catalog by Name or SKU.

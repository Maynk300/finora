export interface Category {
  id: number;
  name: string;
  description: string;
  type: 'income' | 'expense' | 'both';
  created_at: string;
}

export interface Transaction {
  id: number;
  user: number;
  amount: string;
  transaction_type: 'income' | 'expense';
  category: number;
  category_name: string;
  description: string;
  transaction_date: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  amount: number;
  transaction_type: 'income' | 'expense';
  category: number;
  description?: string;
  transaction_date: string;
}

export interface TransactionUpdate extends Partial<TransactionCreate> {}

export interface Budget {
  id: number;
  user: number;
  category: number;
  category_name: string;
  amount: string;
  spent: string;
  month: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetCreate {
  category: number;
  amount: number;
  month: string;
}

export interface BudgetUpdate extends Partial<BudgetCreate> {}

export interface DashboardStats {
  total_income: string;
  total_expenses: string;
  net_savings: string;
  budget_used_percentage: number;
}

export interface ApiError {
  detail?: string;
  [key: string]: unknown;
}
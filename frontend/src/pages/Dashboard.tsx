import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { transactionService, budgetService } from '../services'
import type { Transaction, Budget } from '../services/types'

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [txns, bdgts] = await Promise.all([
        transactionService.getAll({ ordering: '-transaction_date,-created_at' }),
        budgetService.getAll(),
      ])
      setTransactions(txns)
      setBudgets(bdgts)
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const totalIncome = transactions
    .filter(t => t.transaction_type === 'income')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
  const totalExpenses = transactions
    .filter(t => t.transaction_type === 'expense')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
  const netSavings = totalIncome - totalExpenses

  const currentMonth = new Date().toISOString().slice(0, 7)
  const currentBudgets = budgets.filter(b => b.month.startsWith(currentMonth))
  const totalBudgeted = currentBudgets.reduce((sum, b) => sum + parseFloat(b.amount), 0)
  const totalSpent = currentBudgets.reduce((sum, b) => sum + parseFloat(b.spent), 0)
  const budgetUsedPercentage = totalBudgeted > 0 ? Math.round((totalSpent / totalBudgeted) * 100) : 0

  const recentTransactions = transactions.slice(0, 5)

  const stats = [
    { name: 'Total Income', value: `$${totalIncome.toFixed(2)}`, change: '+12.5%', trend: 'up' as const, icon: '💰' },
    { name: 'Total Expenses', value: `$${totalExpenses.toFixed(2)}`, change: '-8.2%', trend: 'down' as const, icon: '💸' },
    { name: 'Net Savings', value: `$${netSavings.toFixed(2)}`, change: '+22.1%', trend: 'up' as const, icon: '📈' },
    { name: 'Budget Used', value: `${budgetUsedPercentage}%`, change: budgetUsedPercentage <= 75 ? 'On track' : 'Over budget', trend: budgetUsedPercentage <= 75 ? 'up' as const : 'down' as const, icon: '🎯' },
  ]

  if (loading && transactions.length === 0) {
    return (
      <div className="space-y-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" aria-label="Loading..." />
          <p className="mt-2 text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">Welcome back! Here's an overview of your finances.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{stat.value}</p>
                <p className={`mt-2 text-sm ${stat.trend === 'up' ? 'text-green-600' : stat.trend === 'down' ? 'text-red-600' : 'text-gray-500'}`}>
                  {stat.change}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-2xl">
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
          <Link to="/transactions" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View all →
          </Link>
        </div>
        <div className="divide-y divide-gray-200">
          {recentTransactions.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No transactions yet</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by adding a new transaction.</p>
              <Link
                to="/transactions"
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                Add Transaction
              </Link>
            </div>
          ) : (
            recentTransactions.map((txn) => (
              <div key={txn.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-lg">
                    {txn.transaction_type === 'income' ? '📥' : '📤'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{txn.description}</p>
                    <p className="text-sm text-gray-500">{txn.category_name} • {txn.transaction_date}</p>
                  </div>
                </div>
                <span className={`font-semibold ${txn.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                  {txn.transaction_type === 'income' ? '+' : '-'}${parseFloat(txn.amount).toFixed(2)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Overview</h3>
          <div className="space-y-4">
            {currentBudgets.length === 0 ? (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h4 className="mt-2 text-sm font-medium text-gray-900">No budgets set</h4>
                <p className="mt-1 text-sm text-gray-500">Create budgets to track spending.</p>
                <Link
                  to="/budgets"
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
                >
                  Set Budget
                </Link>
              </div>
            ) : (
              currentBudgets.map((budget) => {
                const percentage = parseFloat(budget.amount) > 0 ? (parseFloat(budget.spent) / parseFloat(budget.amount)) * 100 : 0
                const getColor = (p: number) => {
                  if (p >= 90) return 'bg-red-600'
                  if (p >= 75) return 'bg-yellow-500'
                  return 'bg-blue-600'
                }
                return (
                  <div key={budget.id}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium">{budget.category_name}</span>
                      <span className="text-gray-500">${parseFloat(budget.spent).toFixed(2)} / ${parseFloat(budget.amount).toFixed(2)}</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${getColor(percentage)}`}
                        style={{ width: `${Math.min(percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link
              to="/transactions"
              className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-lg">➕</div>
              <div>
                <p className="font-medium text-gray-900">Add Transaction</p>
                <p className="text-sm text-gray-500">Record income or expense</p>
              </div>
            </Link>
            <Link
              to="/budgets"
              className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-lg">🎯</div>
              <div>
                <p className="font-medium text-gray-900">Set Budget</p>
                <p className="text-sm text-gray-500">Create or update budgets</p>
              </div>
            </Link>
            <Link
              to="/ai-assistant"
              className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 text-lg">🤖</div>
              <div>
                <p className="font-medium text-gray-900">AI Assistant</p>
                <p className="text-sm text-gray-500">Get financial insights</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
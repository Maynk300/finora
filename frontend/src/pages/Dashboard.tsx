import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { transactionService, budgetService } from '../services'
import type { Transaction, Budget } from '../services/types'

const statIcons = {
  income: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  expenses: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2h2m-4-4h.01M17 21h-10a2 2 0 01-2-2V5a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2z" />
    </svg>
  ),
  savings: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  budget: (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
}

const statConfigs = [
  { key: 'income', name: 'Total Income', trend: 'up', color: 'success', gradient: 'gradient-success' },
  { key: 'expenses', name: 'Total Expenses', trend: 'down', color: 'danger', gradient: 'gradient-danger' },
  { key: 'savings', name: 'Net Savings', trend: 'up', color: 'primary', gradient: 'gradient-primary' },
  { key: 'budget', name: 'Budget Used', trend: 'neutral', color: 'warning', gradient: 'gradient-warning' },
] as const

type StatKey = typeof statConfigs[number]['key']

interface StatCardProps {
  key: StatKey
  name: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  gradient: string
  delay: number
}

function StatCard({ key, name, value, change, trend, icon, gradient, delay }: StatCardProps) {
  const trendColors = {
    up: 'text-success',
    down: 'text-danger',
    neutral: 'text-warning',
  }

  return (
    <div
      key={key}
      className={`stat-card animate-slide-up gradient-surface`}
      style={{ animationDelay: `${delay * 100}ms` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-secondary">{name}</p>
          <p className="mt-1 text-2xl font-bold text-text-primary">{value}</p>
          <p className={`mt-2 text-sm font-medium ${trendColors[trend]}`}>
            {trend === 'up' && <span className="inline-flex items-center gap-1"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>{change}</span>}
            {trend === 'down' && <span className="inline-flex items-center gap-1"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>{change}</span>}
            {trend === 'neutral' && change}
          </p>
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${gradient} text-white shadow-lg`}>
          {icon}
        </div>
      </div>
      <div className="mt-4 h-1.5 bg-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${trend === 'up' ? 'bg-success' : trend === 'down' ? 'bg-danger' : 'bg-warning'}`}
          style={{ width: trend === 'up' ? '85%' : trend === 'down' ? '45%' : '65%' }}
        />
      </div>
    </div>
  )
}

function BudgetProgressBar({ budget }: { budget: Budget }) {
  const percentage = parseFloat(budget.amount) > 0 ? (parseFloat(budget.spent) / parseFloat(budget.amount)) * 100 : 0
  const clamped = Math.min(percentage, 100)
  const isOver = percentage >= 100
  const isWarning = percentage >= 75 && percentage < 100

  const getColorClass = () => {
    if (isOver) return 'bg-danger'
    if (isWarning) return 'bg-warning'
    return 'bg-success'
  }

  const getGlowClass = () => {
    if (isOver) return 'animate-pulse-glow-danger'
    if (isWarning) return 'animate-pulse-glow-warning'
    return 'animate-pulse-glow-success'
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-surface border border-border flex items-center justify-center">
            <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <p className="font-medium text-text-primary">{budget.category_name}</p>
            <p className="text-sm text-text-secondary">${parseFloat(budget.spent).toFixed(2)} / ${parseFloat(budget.amount).toFixed(2)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`font-semibold text-sm ${isOver ? 'text-danger' : isWarning ? 'text-warning' : 'text-success'}`}>
            {clamped.toFixed(0)}%
          </span>
          <span className="text-sm text-text-muted">${(parseFloat(budget.amount) - parseFloat(budget.spent)).toFixed(2)} left</span>
        </div>
      </div>
      <div className="h-2.5 bg-border rounded-full overflow-hidden">
        <div
          className={`${getColorClass()} h-full rounded-full ${getGlowClass()} transition-all duration-1000 ease-out`}
          style={{ width: `${clamped}%` }}
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${budget.category_name} budget usage`}
        />
      </div>
    </div>
  )
}

function QuickActionCard({ icon, title, description, href }: { icon: React.ReactNode; title: string; description: string; href: string }) {
  return (
    <Link
      to={href}
      className="card p-4 flex items-center gap-3 group"
    >
      <div className="w-12 h-12 rounded-xl bg-primary-light text-primary flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <div>
        <p className="font-medium text-text-primary">{title}</p>
        <p className="text-sm text-text-secondary">{description}</p>
      </div>
      <div className="ml-auto text-primary group-hover:translate-x-1 transition-transform duration-200">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
        </svg>
      </div>
    </Link>
  )
}

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

  if (loading && transactions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-rotate mb-4" />
        <p className="text-text-secondary">Loading dashboard...</p>
      </div>
    )
  }

  const stats: Array<{ key: StatKey; name: string; value: string; change: string; trend: 'up' | 'down' | 'neutral'; icon: React.ReactNode; gradient: string }> = [
    { key: 'income', name: 'Total Income', value: `$${totalIncome.toFixed(2)}`, change: '+12.5%', trend: 'up', icon: statIcons.income, gradient: 'gradient-success' },
    { key: 'expenses', name: 'Total Expenses', value: `$${totalExpenses.toFixed(2)}`, change: '-8.2%', trend: 'down', icon: statIcons.expenses, gradient: 'gradient-danger' },
    { key: 'savings', name: 'Net Savings', value: `$${netSavings.toFixed(2)}`, change: '+22.1%', trend: 'up', icon: statIcons.savings, gradient: 'gradient-primary' },
    { key: 'budget', name: 'Budget Used', value: `${budgetUsedPercentage}%`, change: budgetUsedPercentage <= 75 ? 'On track' : 'Over budget', trend: budgetUsedPercentage <= 75 ? 'up' : 'down', icon: statIcons.budget, gradient: budgetUsedPercentage <= 75 ? 'gradient-success' : 'gradient-warning' },
  ]

  return (
    <div className="space-y-8">
      <div className="page-header animate-slide-up">
        <h1>Dashboard</h1>
        <p>Welcome back! Here's an overview of your finances.</p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => {
          const { key: statKey, ...rest } = stat
          return <StatCard key={statKey} delay={index} {...rest} />
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="card-elevated">
            <div className="p-6 border-b border-border flex justify-between items-center">
              <h2 className="text-lg font-semibold text-text-primary">Recent Transactions</h2>
              <Link to="/transactions" className="text-sm font-medium text-primary hover:text-primary-hover transition-colors flex items-center gap-1">
                View all
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
            </div>
            <div className="divide-y divide-border">
              {recentTransactions.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-border flex items-center justify-center">
                    <svg className="w-8 h-8 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-medium text-text-primary">No transactions yet</h3>
                  <p className="mt-1 text-sm text-text-secondary">Get started by adding a new transaction.</p>
                  <Link
                    to="/transactions"
                    className="mt-4 inline-flex items-center gap-2 btn-primary"
                  >
                    Add Transaction
                  </Link>
                </div>
              ) : (
                recentTransactions.map((txn) => (
                  <div key={txn.id} className="p-4 flex items-center justify-between table-row group">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        txn.transaction_type === 'income' ? 'bg-success-light text-success' : 'bg-danger-light text-danger'
                      } group-hover:scale-110 transition-transform duration-300`}>
                        {txn.transaction_type === 'income' ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-text-primary">{txn.description}</p>
                        <p className="text-sm text-text-secondary flex items-center gap-2">
                          <span className="badge badge-primary">{txn.category_name}</span>
                          <span>•</span>
                          <span>{txn.transaction_date}</span>
                        </p>
                      </div>
                    </div>
                    <span className={`font-semibold ${txn.transaction_type === 'income' ? 'text-success' : 'text-danger'}`}>
                      {txn.transaction_type === 'income' ? '+' : '-'}${parseFloat(txn.amount).toFixed(2)}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6 animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="card-elevated">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                <svg className="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Budget Overview
              </h3>
            </div>
            <div className="p-6 space-y-4">
              {currentBudgets.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-warning-light flex items-center justify-center">
                    <svg className="w-8 h-8 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h4 className="text-sm font-medium text-text-primary">No budgets set</h4>
                  <p className="mt-1 text-sm text-text-secondary">Create budgets to track spending.</p>
                  <Link
                    to="/budgets"
                    className="mt-4 inline-flex items-center gap-2 btn-primary"
                  >
                    Set Budget
                  </Link>
                </div>
              ) : (
                currentBudgets.map((budget) => (
                  <BudgetProgressBar key={budget.id} budget={budget} />
                ))
              )}
            </div>
          </div>

          <div className="card-elevated">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Quick Actions
              </h3>
            </div>
            <div className="p-6 space-y-3">
              <QuickActionCard
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                }
                title="Add Transaction"
                description="Record income or expense"
                href="/transactions"
              />
              <QuickActionCard
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
                title="Set Budget"
                description="Create or update budgets"
                href="/budgets"
              />
              <QuickActionCard
                icon={
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                }
                title="AI Assistant"
                description="Get financial insights"
                href="/ai-assistant"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
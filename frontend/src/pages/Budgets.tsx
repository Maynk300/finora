import { useState, useEffect, useCallback } from 'react'
import { budgetService, categoryService } from '../services'
import type { Budget, Category, BudgetCreate, BudgetUpdate } from '../services/types'

function BudgetProgressBar({ budget, index }: { budget: Budget; index: number }) {
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
    <div className="card p-4 animate-slide-up" style={{ animationDelay: `${index * 80}ms` }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 flex-1 min-w-0">
          <div className="w-12 h-12 rounded-xl bg-surface border border-border flex items-center justify-center">
            <svg className="w-6 h-6 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="font-medium text-text-primary truncate">{budget.category_name}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`badge ${isOver ? 'badge-danger' : isWarning ? 'badge-warning' : 'badge-success'}`}>
                {isOver ? 'Over Budget' : isWarning ? 'Warning' : 'On Track'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 ml-4">
          <span className={`font-semibold ${isOver ? 'text-danger' : isWarning ? 'text-warning' : 'text-success'}`}>
            {Math.round(clamped)}%
          </span>
          <span className="font-medium text-text-primary">
            ${(parseFloat(budget.amount) - parseFloat(budget.spent)).toFixed(2)}
          </span>
        </div>
      </div>
      <div className="mt-3 h-3 bg-border rounded-full overflow-hidden">
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
      <div className="mt-3 flex justify-between text-sm text-text-secondary">
        <span>Spent: ${parseFloat(budget.spent).toFixed(2)}</span>
        <span>Budget: ${parseFloat(budget.amount).toFixed(2)}</span>
        <span>Left: ${(parseFloat(budget.amount) - parseFloat(budget.spent)).toFixed(2)}</span>
      </div>
    </div>
  )
}

function QuickStat({ label, value, color = 'text-primary' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-secondary">{label}</span>
      <span className={`font-medium ${color}`}>{value}</span>
    </div>
  )
}

function BudgetSummaryCard({ totalBudgeted, totalSpent, remaining }: { totalBudgeted: number; totalSpent: number; remaining: number }) {
  return (
    <div className="card-elevated p-6 sticky top-24 animate-slide-up" style={{ animationDelay: '200ms' }}>
      <div className="flex items-center gap-2 mb-6">
        <div className="w-10 h-10 rounded-xl gradient-warning flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-text-primary">Budget Summary</h3>
      </div>
      <div className="space-y-4">
        <div className="flex justify-between">
          <span className="text-text-secondary">Total Budgeted</span>
          <span className="font-semibold text-text-primary">${totalBudgeted.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Total Spent</span>
          <span className="font-semibold text-danger">${totalSpent.toFixed(2)}</span>
        </div>
        <div className="pt-4 border-t border-border">
          <div className="flex justify-between mb-1">
            <span className="text-text-secondary">Remaining</span>
            <span className={`font-semibold ${remaining >= 0 ? 'text-success' : 'text-danger'}`}>
              ${remaining.toFixed(2)}
            </span>
          </div>
          <div className="h-3 bg-border rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${remaining >= 0 ? 'bg-success' : 'bg-danger'}`}
              style={{ width: `${totalBudgeted > 0 ? Math.min((totalSpent / totalBudgeted) * 100, 100) : 0}%` }}
            />
          </div>
          <p className="mt-1 text-sm text-text-secondary text-right">
            {totalBudgeted > 0 ? Math.round((totalSpent / totalBudgeted) * 100) : 0}% used
          </p>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-border">
        <h4 className="text-sm font-medium text-text-primary mb-4">Quick Stats</h4>
        <div className="space-y-3 text-sm">
          <QuickStat label="Budgets Set" value="0" />
          <QuickStat label="Over Budget" value="0" color="danger" />
          <QuickStat label="On Track" value="0" color="success" />
          <QuickStat label="Warning" value="0" color="warning" />
        </div>
      </div>
    </div>
  )
}

function EmptyState({ title, description, action }: { title: string; description: string; action: React.ReactNode }) {
  return (
    <div className="text-center py-16">
      <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-border flex items-center justify-center">
        <svg className="w-10 h-10 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-lg font-medium text-text-primary">{title}</h3>
      <p className="mt-2 text-text-secondary">{description}</p>
      <div className="mt-6">{action}</div>
    </div>
  )
}

export default function Budgets() {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedMonth, setSelectedMonth] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [showModal, setShowModal] = useState(false)
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const fetchBudgets = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await budgetService.getAll(selectedMonth)
      setBudgets(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load budgets')
    } finally {
      setLoading(false)
    }
  }, [selectedMonth])

  const fetchCategories = useCallback(async () => {
    try {
      const data = await categoryService.getAll()
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }, [])

  useEffect(() => {
    fetchBudgets()
    fetchCategories()
  }, [fetchBudgets, fetchCategories])

  const handleCreate = async (data: BudgetCreate) => {
    setFormError(null)
    try {
      await budgetService.create(data)
      setShowModal(false)
      setEditingBudget(null)
      fetchBudgets()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create budget')
    }
  }

  const handleUpdate = async (id: number, data: BudgetUpdate) => {
    setFormError(null)
    try {
      await budgetService.update(id, data)
      setShowModal(false)
      setEditingBudget(null)
      fetchBudgets()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update budget')
    }
  }

  const openAddModal = () => {
    setEditingBudget(null)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingBudget(null)
    setFormError(null)
  }

  const validateForm = (formData: FormData): { isValid: boolean; category: number; amount: number; month: string } | null => {
    const categoryStr = formData.get('category') as string
    const amountStr = formData.get('amount') as string
    const monthStr = formData.get('month') as string

    if (!categoryStr) {
      setFormError('Please select a category')
      return null
    }

    const category = parseInt(categoryStr, 10)
    if (isNaN(category)) {
      setFormError('Invalid category')
      return null
    }

    const trimmedAmount = amountStr.trim()
    if (!trimmedAmount) {
      setFormError('Please enter a budget amount')
      return null
    }

    const amount = parseFloat(trimmedAmount)
    if (isNaN(amount) || amount <= 0) {
      setFormError('Please enter a valid positive amount')
      return null
    }

    if (!monthStr) {
      setFormError('Please select a month')
      return null
    }

    const month = `${monthStr}-01`

    return { isValid: true, category, amount, month }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget as HTMLFormElement
    const formData = new FormData(form)

    const validated = validateForm(formData)
    if (!validated) return

    if (editingBudget) {
      const data: BudgetUpdate = {
        category: validated.category,
        amount: validated.amount,
        month: validated.month,
      }
      handleUpdate(editingBudget.id, data)
    } else {
      const data: BudgetCreate = {
        category: validated.category,
        amount: validated.amount,
        month: validated.month,
      }
      handleCreate(data)
    }
  }

  const currentBudgets = budgets
  const totalBudgeted = currentBudgets.reduce((sum, b) => sum + parseFloat(b.amount), 0)
  const totalSpent = currentBudgets.reduce((sum, b) => sum + parseFloat(b.spent), 0)
  const remaining = totalBudgeted - totalSpent

  const monthOptions = Array.from({ length: 12 }, (_, i) => {
    const date = new Date()
    date.setMonth(date.getMonth() - i)
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    return {
      value,
      label: date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' }),
    }
  })

  return (
    <div className="space-y-6">
      <div className="page-header animate-slide-up">
        <h1>Budgets</h1>
        <p>Track your spending against budget limits</p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="flex items-center gap-4">
          <label htmlFor="month-select" className="text-sm font-medium text-text-secondary">Month:</label>
          <select
            id="month-select"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="input w-auto"
          >
            {monthOptions.map((month) => (
              <option key={month.value} value={month.value}>{month.label}</option>
            ))}
          </select>
          <button
            onClick={openAddModal}
            disabled={loading}
            className="btn-primary"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Budget
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-danger-light border border-danger/20 text-danger px-4 py-3 rounded-xl animate-slide-down" role="alert">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <div className="card-elevated">
            <div className="p-6 border-b border-border">
              <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Budget Overview - {new Date(selectedMonth + '-01').toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}
              </h2>
            </div>
            <div className="divide-y divide-border">
              {loading && budgets.length === 0 ? (
                <div className="p-12 text-center">
                  <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-rotate mx-auto mb-4" />
                  <p className="text-text-secondary">Loading budgets...</p>
                </div>
              ) : currentBudgets.length === 0 ? (
                <EmptyState
                  title="No budgets set"
                  description="Create your first budget to start tracking your spending against limits."
                  action={
                    <button onClick={openAddModal} className="btn-primary">
                      Create Budget
                    </button>
                  }
                />
              ) : (
                currentBudgets.map((budget, index) => (
                  <BudgetProgressBar key={budget.id} budget={budget} index={index} />
                ))
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <BudgetSummaryCard
            totalBudgeted={totalBudgeted}
            totalSpent={totalSpent}
            remaining={remaining}
          />
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto animate-fade-in" role="dialog" aria-modal="true" aria-labelledby="budget-modal-title">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in" onClick={closeModal} />
            <div className="relative w-full max-w-md bg-surface rounded-2xl shadow-xl p-6 modal-content">
              <h2 id="budget-modal-title" className="text-xl font-semibold text-text-primary mb-6">
                {editingBudget ? 'Edit Budget' : 'Add Budget'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                {formError && (
                  <div className="bg-danger-light border border-danger/20 text-danger px-4 py-3 rounded-xl text-sm animate-slide-down" role="alert">
                    {formError}
                  </div>
                )}
                <div>
                  <label htmlFor="budget-category" className="block text-sm font-medium text-text-secondary mb-1">Category</label>
                  <select
                    id="budget-category"
                    name="category"
                    defaultValue={editingBudget?.category.toString() || ''}
                    disabled={!!editingBudget}
                    className="input"
                    required
                  >
                    <option value="">Select category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id.toString()}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="budget-amount" className="block text-sm font-medium text-text-secondary mb-1">Budget Amount</label>
                  <input
                    type="number"
                    id="budget-amount"
                    name="amount"
                    step="0.01"
                    min="0.01"
                    defaultValue={editingBudget?.amount || ''}
                    required
                    className="input"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label htmlFor="budget-month" className="block text-sm font-medium text-text-secondary mb-1">Month</label>
                  <input
                    type="month"
                    id="budget-month"
                    name="month"
                    defaultValue={editingBudget?.month || selectedMonth}
                    disabled={!!editingBudget}
                    required
                    className="input"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
                  <button type="submit" className="btn-primary">
                    {editingBudget ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
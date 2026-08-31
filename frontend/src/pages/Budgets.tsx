import { useState, useEffect, useCallback } from 'react'
import { budgetService, categoryService } from '../services'
import type { Budget, Category, BudgetCreate, BudgetUpdate } from '../services/types'

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

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this budget?')) return
    setError(null)
    try {
      await budgetService.delete(id)
      fetchBudgets()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete budget')
    }
  }

  const handleEdit = (budget: Budget) => {
    setEditingBudget(budget)
    setShowModal(true)
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

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 75) return 'bg-yellow-500'
    return 'bg-green-500'
  }

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Budgets</h1>
          <p className="mt-1 text-gray-600">Track your spending against budget limits</p>
        </div>
        <div className="flex items-center gap-4">
          <label htmlFor="month-select" className="text-sm font-medium text-gray-700">Month:</label>
          <select
            id="month-select"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {monthOptions.map((month) => (
              <option key={month.value} value={month.value}>{month.label}</option>
            ))}
          </select>
          <button
            onClick={openAddModal}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Budget
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Budget Overview - {new Date(selectedMonth + '-01').toLocaleDateString('en-US', { year: 'numeric', month: 'long' })}
              </h2>
            </div>
            <div className="divide-y divide-gray-200">
              {loading && budgets.length === 0 ? (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" aria-label="Loading..." />
                  <p className="mt-2 text-gray-500">Loading budgets...</p>
                </div>
              ) : currentBudgets.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No budgets set</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first budget to start tracking.</p>
                </div>
              ) : (
                currentBudgets.map((budget) => {
                  const percentage = parseFloat(budget.amount) > 0 ? (parseFloat(budget.spent) / parseFloat(budget.amount)) * 100 : 0
                  return (
                    <div key={budget.id} className="px-6 py-4 hover:bg-gray-50 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-lg">📊</div>
                        <div className="min-w-0">
                          <p className="font-medium text-gray-900 truncate">{budget.category_name}</p>
                          <p className="text-sm text-gray-500">${parseFloat(budget.spent).toFixed(2)} / ${parseFloat(budget.amount).toFixed(2)} spent</p>
                        </div>
                        <div className="flex-1 max-w-xs ml-4">
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${getProgressColor(percentage)}`}
                              style={{ width: `${Math.min(percentage, 100)}%` }}
                            />
                          </div>
                          <p className="mt-1 text-xs text-gray-500 text-right">{Math.round(percentage)}% used</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold ${parseFloat(budget.spent) > parseFloat(budget.amount) ? 'text-red-600' : 'text-gray-900'}`}>
                          ${(parseFloat(budget.amount) - parseFloat(budget.spent)).toFixed(2)} left
                        </span>
                        <button onClick={() => handleEdit(budget)} className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors" aria-label="Edit budget">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </button>
                        <button onClick={() => handleDelete(budget.id)} className="p-1.5 text-gray-400 hover:text-red-600 transition-colors" aria-label="Delete budget">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-24">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Total Budgeted</span>
                  <span className="font-semibold text-gray-900">${totalBudgeted.toFixed(2)}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Total Spent</span>
                  <span className="font-semibold text-red-600">${totalSpent.toFixed(2)}</span>
                </div>
              </div>
              <div className="pt-4 border-t border-gray-200">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Remaining</span>
                  <span className={`font-semibold ${remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${remaining.toFixed(2)}
                  </span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
                  <div
                    className={`h-full rounded-full transition-all ${getProgressColor(totalBudgeted > 0 ? (totalSpent / totalBudgeted) * 100 : 0)}`}
                    style={{ width: `${totalBudgeted > 0 ? Math.min((totalSpent / totalBudgeted) * 100, 100) : 0}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Budgets Set</span>
                  <span className="font-medium text-gray-900">{currentBudgets.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Over Budget</span>
                  <span className="font-medium text-red-600">{currentBudgets.filter(b => parseFloat(b.spent) > parseFloat(b.amount)).length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">On Track</span>
                  <span className="font-medium text-green-600">{currentBudgets.filter(b => parseFloat(b.spent) <= parseFloat(b.amount) * 0.75).length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Warning</span>
                  <span className="font-medium text-yellow-600">{currentBudgets.filter(b => parseFloat(b.spent) > parseFloat(b.amount) * 0.75 && parseFloat(b.spent) <= parseFloat(b.amount)).length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="budget-modal-title">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={closeModal} />
            <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl p-6">
              <h2 id="budget-modal-title" className="text-xl font-semibold text-gray-900 mb-6">
                {editingBudget ? 'Edit Budget' : 'Add Budget'}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                {formError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm" role="alert">
                    {formError}
                  </div>
                )}
                <div>
                  <label htmlFor="budget-category" className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    id="budget-category"
                    name="category"
                    defaultValue={editingBudget?.category.toString() || ''}
                    disabled={!!editingBudget}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id.toString()}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="budget-amount" className="block text-sm font-medium text-gray-700 mb-1">Budget Amount</label>
                  <input
                    type="number"
                    id="budget-amount"
                    name="amount"
                    step="0.01"
                    min="0.01"
                    defaultValue={editingBudget?.amount || ''}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label htmlFor="budget-month" className="block text-sm font-medium text-gray-700 mb-1">Month</label>
                  <input
                    type="month"
                    id="budget-month"
                    name="month"
                    defaultValue={editingBudget?.month || selectedMonth}
                    disabled={!!editingBudget}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button type="button" onClick={closeModal} className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">Cancel</button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
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
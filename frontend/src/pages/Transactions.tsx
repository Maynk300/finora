import { useState, useEffect, useCallback } from 'react'
import { transactionService, categoryService } from '../services'
import type { Transaction, Category, TransactionCreate, TransactionUpdate } from '../services/types'

interface TransactionFormData {
  transaction_type: 'income' | 'expense'
  amount: string
  category: string
  description: string
  transaction_date: string
}

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'income' | 'expense'>('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formError, setFormError] = useState<string | null>(null)

  const [formData, setFormData] = useState<TransactionFormData>({
    transaction_type: 'expense',
    amount: '',
    category: '',
    description: '',
    transaction_date: new Date().toISOString().split('T')[0],
  })

  const fetchTransactions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        search: searchTerm || undefined,
        type: typeFilter !== 'all' ? typeFilter : undefined,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        ordering: '-transaction_date,-created_at',
      }

      const data = await transactionService.getAll(params)
      setTransactions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [searchTerm, typeFilter, categoryFilter])

  const fetchCategories = useCallback(async () => {
    try {
      const data = await categoryService.getAll()
      console.log('[DEBUG] fetchCategories response:', data)
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }, [])

  const filteredCategories = categories.filter((cat) => {
    const formType = formData.transaction_type
    console.log('[DEBUG] Category:', cat.name, 'type:', cat.type, 'formType:', formType)
    if (!formType) return true
    if (cat.type === 'both') return true
    return cat.type === formType
  })
  console.log('[DEBUG] filteredCategories:', filteredCategories.map(c => c.name), 'formData.transaction_type:', formData.transaction_type)

  const resetForm = useCallback(() => {
    setFormData({
      transaction_type: 'expense',
      amount: '',
      category: '',
      description: '',
      transaction_date: new Date().toISOString().split('T')[0],
    })
  }, [])

  const handleOpenAddModal = () => {
    resetForm()
    setEditingTransaction(null)
    setShowModal(true)
  }

  const handleOpenEditModal = (transaction: Transaction) => {
    setFormData({
      transaction_type: transaction.transaction_type,
      amount: transaction.amount,
      category: transaction.category.toString(),
      description: transaction.description,
      transaction_date: transaction.transaction_date,
    })
    setEditingTransaction(transaction)
    setShowModal(true)
  }

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    console.log('[DEBUG] handleFormChange:', name, value)
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    try {
      if (editingTransaction) {
        const data: TransactionUpdate = {
          transaction_type: formData.transaction_type as 'income' | 'expense',
          amount: parseFloat(formData.amount as string),
          category: parseInt(formData.category as string),
          description: formData.description || '',
          transaction_date: formData.transaction_date as string,
        }
        await handleUpdate(editingTransaction.id, data)
      } else {
        const data: TransactionCreate = {
          transaction_type: formData.transaction_type as 'income' | 'expense',
          amount: parseFloat(formData.amount as string),
          category: parseInt(formData.category as string),
          description: formData.description || '',
          transaction_date: formData.transaction_date as string,
        }
        await handleCreate(data)
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save transaction')
    }
  }

  useEffect(() => {
    fetchTransactions()
    fetchCategories()
  }, [fetchTransactions, fetchCategories])

  const handleCreate = async (data: TransactionCreate) => {
    setFormError(null)
    try {
      await transactionService.create(data)
      setShowModal(false)
      setEditingTransaction(null)
      fetchTransactions()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create transaction')
    }
  }

  const handleUpdate = async (id: number, data: TransactionUpdate) => {
    setFormError(null)
    try {
      await transactionService.update(id, data)
      setShowModal(false)
      setEditingTransaction(null)
      fetchTransactions()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update transaction')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this transaction?')) return
    setError(null)
    try {
      await transactionService.delete(id)
      fetchTransactions()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete transaction')
    }
  }

  const handleEdit = (transaction: Transaction) => {
    handleOpenEditModal(transaction)
  }

  const openAddModal = () => {
    handleOpenAddModal()
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingTransaction(null)
    setFormError(null)
  }

  const filteredTransactions = transactions.filter((txn) => {
    const matchesSearch = txn.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      txn.category_name.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = typeFilter === 'all' || txn.transaction_type === typeFilter
    const matchesCategory = categoryFilter === 'all' || txn.category_name === categoryFilter
    return matchesSearch && matchesType && matchesCategory
  })

  const totalIncome = transactions
    .filter(t => t.transaction_type === 'income')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)
  const totalExpenses = transactions
    .filter(t => t.transaction_type === 'expense')
    .reduce((sum, t) => sum + parseFloat(t.amount), 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <p className="mt-1 text-gray-600">Manage your income and expenses</p>
        </div>
        <button
          onClick={openAddModal}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Transaction
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value as 'all' | 'income' | 'expense')}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.name}>{cat.name}</option>
            ))}
          </select>
        </div>

        <div className="flex justify-between text-sm text-gray-500 mb-4">
          <span>Showing {filteredTransactions.length} of {transactions.length} transactions</span>
          <div className="flex gap-4">
            <span className="text-green-600 font-medium">Income: +${totalIncome.toFixed(2)}</span>
            <span className="text-red-600 font-medium">Expenses: -${totalExpenses.toFixed(2)}</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          {loading && transactions.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" aria-label="Loading..." />
              <p className="mt-2 text-gray-500">Loading transactions...</p>
            </div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="pb-3 font-semibold text-gray-900">Date</th>
                  <th className="pb-3 font-semibold text-gray-900">Description</th>
                  <th className="pb-3 font-semibold text-gray-900">Category</th>
                  <th className="pb-3 font-semibold text-gray-900">Type</th>
                  <th className="pb-3 font-semibold text-gray-900 text-right">Amount</th>
                  <th className="pb-3 font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredTransactions.map((txn) => (
                  <tr key={txn.id} className="hover:bg-gray-50">
                    <td className="py-4 text-gray-900">{txn.transaction_date}</td>
                    <td className="py-4 font-medium text-gray-900">{txn.description}</td>
                    <td className="py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                        {txn.category_name}
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        txn.transaction_type === 'income' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {txn.transaction_type === 'income' ? 'Income' : 'Expense'}
                      </span>
                    </td>
                    <td className="py-4 text-right font-medium">
                      <span className={txn.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}>
                        {txn.transaction_type === 'income' ? '+' : '-'}${parseFloat(txn.amount).toFixed(2)}
                      </span>
                    </td>
                    <td className="py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEdit(txn)}
                          className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
                          aria-label="Edit transaction"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDelete(txn.id)}
                          className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                          aria-label="Delete transaction"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {filteredTransactions.length === 0 && !loading && (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No transactions found</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by adding a new transaction.</p>
              <button
                onClick={openAddModal}
                className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                Add Transaction
              </button>
            </div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={closeModal} />
            <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl p-6">
              <h2 id="modal-title" className="text-xl font-semibold text-gray-900 mb-6">
                {editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
              </h2>
              <form onSubmit={handleFormSubmit} className="space-y-4">
                {formError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm" role="alert">
                    {formError}
                  </div>
                )}
                <div>
                  <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    id="type"
                    name="transaction_type"
                    value={formData.transaction_type}
                    onChange={handleFormChange}
                    disabled={!!editingTransaction}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                  <input
                    type="number"
                    id="amount"
                    name="amount"
                    step="0.01"
                    min="0.01"
                    value={formData.amount}
                    onChange={handleFormChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    id="category"
                    name="category"
                    value={formData.category}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select category</option>
                    {filteredCategories.map((cat) => (
                      <option key={cat.id} value={cat.id.toString()}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter description"
                  />
                </div>
                <div>
                  <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input
                    type="date"
                    id="date"
                    name="date"
                    value={formData.transaction_date}
                    onChange={handleFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    {editingTransaction ? 'Update' : 'Save'}
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
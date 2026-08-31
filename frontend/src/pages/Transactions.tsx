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

function TransactionTypeBadge({ type }: { type: 'income' | 'expense' }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
      type === 'income' ? 'bg-success-light text-success' : 'bg-danger-light text-danger'
    }`}>
      {type === 'income' ? (
        <>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Income
        </>
      ) : (
        <>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Expense
        </>
      )}
    </span>
  )
}

function CategoryBadge({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-primary-light text-primary">
      {name}
    </span>
  )
}

function ActionButton({ onClick, children, color = 'text-text-secondary', hoverColor = 'text-text-primary', ariaLabel }: { onClick: () => void; children: React.ReactNode; color?: string; hoverColor?: string; ariaLabel: string }) {
  return (
    <button
      onClick={onClick}
      className={`icon-btn ${color} hover:${hoverColor} group`}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  )
}

function EmptyState({ icon, title, description, action }: { icon: React.ReactNode; title: string; description: string; action: React.ReactNode }) {
  return (
    <div className="text-center py-16">
      <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-border flex items-center justify-center">
        <div className="w-10 h-10 text-text-muted">{icon}</div>
      </div>
      <h3 className="text-lg font-medium text-text-primary">{title}</h3>
      <p className="mt-2 text-text-secondary">{description}</p>
      <div className="mt-6">{action}</div>
    </div>
  )
}

function TransactionRow({ txn, onEdit, onDelete }: { txn: Transaction; onEdit: () => void; onDelete: () => void }) {
  return (
    <tr key={txn.id} className="table-row animate-fade-in">
      <td className="py-4 px-6 text-text-secondary whitespace-nowrap">{txn.transaction_date}</td>
      <td className="py-4 px-6 font-medium text-text-primary">{txn.description}</td>
      <td className="py-4 px-6">
        <CategoryBadge name={txn.category_name} />
      </td>
      <td className="py-4 px-6">
        <TransactionTypeBadge type={txn.transaction_type} />
      </td>
      <td className="py-4 px-6 text-right font-medium">
        <span className={txn.transaction_type === 'income' ? 'text-success' : 'text-danger'}>
          {txn.transaction_type === 'income' ? '+' : '-'}${parseFloat(txn.amount).toFixed(2)}
        </span>
      </td>
      <td className="py-4 px-6">
        <div className="flex items-center justify-end gap-2">
          <ActionButton
            onClick={onEdit}
            ariaLabel="Edit transaction"
            children={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            }
          />
          <ActionButton
            onClick={onDelete}
            color="text-danger"
            hoverColor="text-danger"
            ariaLabel="Delete transaction"
            children={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            }
          />
        </div>
      </td>
    </tr>
  )
}

function TransactionForm({ formData, onChange, onSubmit, editingTransaction, closeModal, filteredCategories, formError, loading }: {
  formData: TransactionFormData
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void
  onSubmit: (e: React.FormEvent) => void
  editingTransaction: Transaction | null
  closeModal: () => void
  filteredCategories: Category[]
  formError: string | null
  loading: boolean
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4 animate-slide-up">
      {formError && (
        <div className="bg-danger-light border border-danger/20 text-danger px-4 py-3 rounded-xl text-sm animate-slide-down" role="alert">
          {formError}
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="type" className="block text-sm font-medium text-text-secondary mb-1">Type</label>
          <select
            id="type"
            name="transaction_type"
            value={formData.transaction_type}
            onChange={onChange}
            disabled={!!editingTransaction}
            className="input"
          >
            <option value="expense">Expense</option>
            <option value="income">Income</option>
          </select>
        </div>
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-text-secondary mb-1">Amount</label>
          <input
            type="number"
            id="amount"
            name="amount"
            step="0.01"
            min="0.01"
            value={formData.amount}
            onChange={onChange}
            required
            className="input"
            placeholder="0.00"
          />
        </div>
      </div>
      <div>
        <label htmlFor="category" className="block text-sm font-medium text-text-secondary mb-1">Category</label>
        <select
          id="category"
          name="category"
          value={formData.category}
          onChange={onChange}
          className="input"
          required
        >
          <option value="">Select category</option>
          {filteredCategories.map((cat) => (
            <option key={cat.id} value={cat.id.toString()}>{cat.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-text-secondary mb-1">Description</label>
        <input
          type="text"
          id="description"
          name="description"
          value={formData.description}
          onChange={onChange}
          className="input"
          placeholder="Enter description"
        />
      </div>
      <div>
        <label htmlFor="date" className="block text-sm font-medium text-text-secondary mb-1">Date</label>
        <input
          type="date"
          id="date"
          name="date"
          value={formData.transaction_date}
          onChange={onChange}
          className="input"
        />
      </div>
      <div className="flex justify-end gap-3 pt-4">
        <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
        <button type="submit" disabled={loading} className="btn-primary">
          {editingTransaction ? 'Update' : 'Save'}
        </button>
      </div>
    </form>
  )
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
      setCategories(data)
    } catch (err) {
      console.error('Failed to load categories:', err)
    }
  }, [])

  const filteredCategories = categories.filter((cat) => {
    const formType = formData.transaction_type
    if (!formType) return true
    if (cat.type === 'both') return true
    return cat.type === formType
  })

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
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    try {
      if (editingTransaction) {
        const data: TransactionUpdate = {
          transaction_type: formData.transaction_type as 'income' | 'expense',
          amount: parseFloat(formData.amount),
          category: parseInt(formData.category),
          description: formData.description || '',
          transaction_date: formData.transaction_date,
        }
        await handleUpdate(editingTransaction.id, data)
      } else {
        const data: TransactionCreate = {
          transaction_type: formData.transaction_type as 'income' | 'expense',
          amount: parseFloat(formData.amount),
          category: parseInt(formData.category),
          description: formData.description || '',
          transaction_date: formData.transaction_date,
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
      <div className="page-header animate-slide-up">
        <h1>Transactions</h1>
        <p>Manage your income and expenses</p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Transactions</h1>
          <p className="mt-1 text-text-secondary">Manage your income and expenses</p>
        </div>
        <button
          onClick={openAddModal}
          disabled={loading}
          className="btn-primary"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Transaction
        </button>
      </div>

      {error && (
        <div className="bg-danger-light border border-danger/20 text-danger px-4 py-3 rounded-xl animate-slide-down" role="alert">
          {error}
        </div>
      )}

      <div className="card-elevated animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="relative">
              <input
                type="text"
                placeholder="Search transactions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as 'all' | 'income' | 'expense')}
              className="input"
            >
              <option value="all">All Types</option>
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.name}>{cat.name}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-between items-center mb-6">
            <span className="text-sm text-text-secondary">Showing {filteredTransactions.length} of {transactions.length} transactions</span>
            <div className="flex gap-4">
              <span className="flex items-center gap-1 text-success font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                +${totalIncome.toFixed(2)}
              </span>
              <span className="flex items-center gap-1 text-danger font-medium">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                -${totalExpenses.toFixed(2)}
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            {loading && transactions.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-rotate mx-auto mb-4" />
                <p className="text-text-secondary">Loading transactions...</p>
              </div>
            ) : (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border">
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider">Date</th>
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider">Description</th>
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider">Category</th>
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider">Type</th>
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider text-right">Amount</th>
                    <th className="pb-3 px-6 font-semibold text-text-secondary text-sm uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredTransactions.map((txn) => (
                    <TransactionRow key={txn.id} txn={txn} onEdit={() => handleEdit(txn)} onDelete={() => handleDelete(txn.id)} />
                  ))}
                </tbody>
              </table>
            )}

            {filteredTransactions.length === 0 && !loading && (
              <EmptyState
                icon={
                  <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
                title="No transactions found"
                description="Get started by adding a new transaction."
                action={
                  <button onClick={openAddModal} className="btn-primary">
                    Add Transaction
                  </button>
                }
              />
            )}
          </div>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto animate-fade-in" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in" onClick={closeModal} />
            <div className="relative w-full max-w-md bg-surface rounded-2xl shadow-xl p-6 modal-content">
              <h2 id="modal-title" className="text-xl font-semibold text-text-primary mb-6">
                {editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
              </h2>
              <TransactionForm
                formData={formData}
                onChange={handleFormChange}
                onSubmit={handleFormSubmit}
                editingTransaction={editingTransaction}
                closeModal={closeModal}
                filteredCategories={filteredCategories}
                formError={formError}
                loading={loading}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
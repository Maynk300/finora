import { api } from './api';
import type { Transaction, TransactionCreate, TransactionUpdate } from './types';

export const transactionService = {
  async getAll(params?: {
    search?: string;
    type?: 'income' | 'expense' | 'all';
    category?: string;
    ordering?: string;
  }): Promise<Transaction[]> {
    const searchParams = new URLSearchParams();
    if (params?.search) searchParams.set('search', params.search);
    if (params?.type && params.type !== 'all') searchParams.set('transaction_type', params.type);
    if (params?.category) searchParams.set('category', params.category);
    if (params?.ordering) searchParams.set('ordering', params.ordering);

    const queryString = searchParams.toString();
    const endpoint = `/transactions/${queryString ? `?${queryString}` : ''}`;

    const response = await api.get<{ results: Transaction[] }>(endpoint);
    return response.results ?? response;
  },

  async getById(id: number): Promise<Transaction> {
    return api.get<Transaction>(`/transactions/${id}/`);
  },

  async create(data: TransactionCreate): Promise<Transaction> {
    return api.post<Transaction>('/transactions/', data);
  },

  async update(id: number, data: TransactionUpdate): Promise<Transaction> {
    return api.patch<Transaction>(`/transactions/${id}/`, data);
  },

  async delete(id: number): Promise<void> {
    return api.delete<void>(`/transactions/${id}/`);
  },
};
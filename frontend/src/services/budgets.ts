import { api } from './api';
import type { Budget, BudgetCreate, BudgetUpdate } from './types';

export const budgetService = {
  async getAll(month?: string): Promise<Budget[]> {
    const searchParams = new URLSearchParams();
    if (month) searchParams.set('month', month);

    const queryString = searchParams.toString();
    const endpoint = `/budgets/${queryString ? `?${queryString}` : ''}`;

    const response = await api.get<{ results: Budget[] }>(endpoint);
    return response.results ?? response;
  },

  async getById(id: number): Promise<Budget> {
    return api.get<Budget>(`/budgets/${id}/`);
  },

  async create(data: BudgetCreate): Promise<Budget> {
    return api.post<Budget>('/budgets/', data);
  },

  async update(id: number, data: BudgetUpdate): Promise<Budget> {
    return api.patch<Budget>(`/budgets/${id}/`, data);
  },

  async delete(id: number): Promise<void> {
    return api.delete<void>(`/budgets/${id}/`);
  },
};